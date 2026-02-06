"""
Cycle Runner - Shared orchestration for demo/local modes.

This module provides the Python-loop orchestration that's used for:
- Demo mode (all mocks)
- Local mode (real Claude, no Temporal)

Temporal workflows call the same activities but handle orchestration differently.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    EXECUTION MODES                          │
    ├─────────────────────────────────────────────────────────────┤
    │  Mode      │ Orchestrator     │ Claude    │ Human           │
    ├─────────────────────────────────────────────────────────────┤
    │  --demo    │ CycleRunner      │ Mock      │ Mock            │
    │  --local   │ CycleRunner      │ Real      │ CLI prompts     │
    │  --cloud   │ Temporal         │ Real      │ Webhooks/UI     │
    └─────────────────────────────────────────────────────────────┘

The key insight: Activities are identical across all modes.
Only the orchestrator and injected dependencies change.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any, Protocol
import asyncio

logger = logging.getLogger("1kh.runner")


# =============================================================================
# Protocols for Dependency Injection
# =============================================================================

class ClaudeClientProtocol(Protocol):
    """Protocol for Claude API client (real or mock)."""

    def messages_create(
        self,
        model: str,
        max_tokens: int,
        messages: list[dict],
        **kwargs,
    ) -> Any:
        """Create a message completion."""
        ...


class HumanResponderProtocol(Protocol):
    """Protocol for human interaction (mock, CLI, or webhook)."""

    def request_decision(
        self,
        escalation_type: str,
        summary: str,
        options: list[str],
        context: dict,
    ) -> dict:
        """Request a decision from human. Returns {action, feedback}."""
        ...

    def request_approval(
        self,
        summary: str,
        details: dict,
    ) -> bool:
        """Request approval for an action."""
        ...


class ExecutorProtocol(Protocol):
    """Protocol for task execution (mock or real)."""

    def execute(
        self,
        task: dict,
        hypothesis: dict,
    ) -> "ExecutionResult":
        """Execute a task and return result."""
        ...


# =============================================================================
# Execution Result
# =============================================================================

@dataclass
class ExecutionResult:
    """Result of executing a task."""
    success: bool
    task_id: str
    hypothesis_id: Optional[str] = None
    result_text: str = ""
    duration_seconds: float = 0
    metrics_delta: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    needs_human: bool = False
    human_prompt: Optional[str] = None


# =============================================================================
# Runner Configuration
# =============================================================================

class RunnerMode(str, Enum):
    DEMO = "demo"      # All mocked
    LOCAL = "local"    # Real Claude, CLI human
    # CLOUD mode uses Temporal, not this runner


@dataclass
class RunnerConfig:
    """Configuration for the cycle runner."""
    mode: RunnerMode
    project_path: Path

    # Thresholds
    approval_threshold: float = 0.65
    escalation_threshold: float = 0.40

    # Limits
    max_cycles: int = 100
    max_hypotheses_per_cycle: int = 5
    max_tasks_per_cycle: int = 3

    # Demo-specific
    demo_speed: float = 1.0
    demo_delay_base: float = 0.5

    # North Star
    north_star_target: float = 1_000_000
    north_star_name: str = "$1M ARR"

    # Time simulation (how many days per cycle)
    days_per_cycle: int = 3  # Default: each cycle represents 3 days of work

    # Callbacks for UI
    on_cycle_start: Optional[Callable[[int], None]] = None
    on_cycle_end: Optional[Callable[[int, dict], None]] = None
    on_hypothesis_generated: Optional[Callable[[dict], None]] = None
    on_task_executed: Optional[Callable[[dict, ExecutionResult], None]] = None
    on_escalation: Optional[Callable[[str, dict], None]] = None
    on_progress_update: Optional[Callable[[float, float], None]] = None

    # Vendor selection callback (for two-level hypotheses)
    on_vendor_selection_needed: Optional[Callable[[str, list[dict]], str]] = None

    # Pivot decision callback (when REFLECTION recommends pivot)
    on_pivot_decision_needed: Optional[Callable[[dict], str]] = None

    # Phase callbacks (for loading indicators)
    on_phase_start: Optional[Callable[[str], None]] = None  # "imagination", "intent", "work", "execution"
    on_phase_end: Optional[Callable[[str], None]] = None

    # Report generation
    generate_reports: bool = True
    on_report_generated: Optional[Callable[[Path], None]] = None


# =============================================================================
# Dependency Container
# =============================================================================

@dataclass
class Dependencies:
    """Container for injected dependencies."""
    claude_client: Any  # ClaudeClientProtocol
    human_responder: Any  # HumanResponderProtocol
    executor: Any  # ExecutorProtocol
    dashboard: Any  # Dashboard
    conversation_manager: Optional[Any] = None  # ConversationManager


# =============================================================================
# Cycle Runner
# =============================================================================

class CycleRunner:
    """
    Orchestrates the Four Loops cycle using Python async.

    Used for demo and local modes. Temporal handles cloud mode.
    """

    def __init__(
        self,
        config: RunnerConfig,
        deps: Dependencies,
    ):
        self.config = config
        self.deps = deps

        # State - load from persisted state if available
        run_state = self._load_run_state()
        self.cycle_count = run_state.get("last_cycle", 0)
        self.hypotheses_total = run_state.get("hypotheses_total", 0)
        self.tasks_total = run_state.get("tasks_total", 0)
        self.escalations_total = run_state.get("escalations_total", 0)
        self.failures = run_state.get("failures", 0)
        self.target_reached = False

        # Cached foundation docs (loaded once, reused)
        self._oracle: dict = {}
        self._north_star: dict = {}
        self._context: dict = {}
        self._foundation_loaded = False

        # History for analysis
        self.cycle_history: list[dict] = []

        # Hypothesis manager for two-level hypotheses and vendor selection
        self._hypothesis_manager = None  # Initialized lazily after foundation loads

    def _load_run_state(self) -> dict:
        """Load persisted run state if available."""
        import json
        state_path = self.config.project_path / ".1kh" / "state" / "run_state.json"
        if state_path.exists():
            try:
                return json.loads(state_path.read_text())
            except Exception:
                pass
        return {}

    def _save_run_state(self):
        """Persist run state for resume capability."""
        import json
        from datetime import datetime

        state_dir = self.config.project_path / ".1kh" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Calculate simulated time
        simulated_days = self.cycle_count * self.config.days_per_cycle

        state = {
            "last_cycle": self.cycle_count,
            "hypotheses_total": self.hypotheses_total,
            "tasks_total": self.tasks_total,
            "escalations_total": self.escalations_total,
            "failures": self.failures,
            "last_run_at": datetime.utcnow().isoformat(),
            "target_reached": self.target_reached,
            "simulated_days": simulated_days,
            "days_per_cycle": self.config.days_per_cycle,
        }

        state_path = state_dir / "run_state.json"
        state_path.write_text(json.dumps(state, indent=2))

    def clear_run_state(self):
        """Clear persisted run state (called on --fresh)."""
        state_path = self.config.project_path / ".1kh" / "state" / "run_state.json"
        if state_path.exists():
            state_path.unlink()
        # Reset in-memory state
        self.cycle_count = 0
        self.hypotheses_total = 0
        self.tasks_total = 0
        self.escalations_total = 0
        self.failures = 0
        self.target_reached = False

    async def run(self) -> dict:
        """
        Run cycles until target reached or max cycles.

        Returns summary dict with statistics.
        """
        logger.info(f"Starting cycle runner in {self.config.mode.value} mode, resuming from cycle {self.cycle_count}")

        # Set up North Star
        self.deps.dashboard.set_north_star(
            self.config.north_star_name,
            target_value=self.config.north_star_target,
        )

        while self.cycle_count < self.config.max_cycles and not self.target_reached:
            self.cycle_count += 1

            if self.config.on_cycle_start:
                self.config.on_cycle_start(self.cycle_count)

            cycle_result = await self._run_single_cycle()
            self.cycle_history.append(cycle_result)

            if self.config.on_cycle_end:
                self.config.on_cycle_end(self.cycle_count, cycle_result)

            # Save state after each cycle (for resume capability)
            self._save_run_state()

            # Check if pivot was confirmed - stop to let user update foundation
            if cycle_result.get("stop_after_cycle"):
                logger.info("Stopping after cycle due to pivot decision")
                summary = self._build_summary()
                summary["pivot_required"] = True
                summary["pivot_updates"] = cycle_result.get("pivot_updates", {})
                return summary

            # Check progress
            state = self.deps.dashboard.compute_state()
            progress = state.north_star.progress_pct

            if self.config.on_progress_update:
                self.config.on_progress_update(
                    state.north_star.current_value,
                    self.config.north_star_target,
                )

            if progress >= 100:
                self.target_reached = True
                self._save_run_state()
                logger.info("North Star target reached!")

        return self._build_summary()

    async def _run_single_cycle(self) -> dict:
        """Run a single REFLECTION → IMAGINATION → INTENT → WORK → EXECUTION cycle."""
        cycle_result = {
            "cycle": self.cycle_count,
            "hypotheses_generated": 0,
            "hypotheses_approved": 0,
            "hypotheses_escalated": 0,
            "tasks_executed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "revenue_delta": 0,
            "signups_delta": 0,
        }

        # Track hypotheses and tasks for report
        all_hypotheses = []
        all_tasks = []

        # =====================================================
        # REFLECTION: Analyze system state and get guidance
        # =====================================================
        reflection_result = None
        if self.config.on_phase_start:
            self.config.on_phase_start("reflection")

        try:
            reflection_result = self._run_reflection()

            # Check if reflection triggered a pivot that requires stopping
            if reflection_result and reflection_result.get("stop_after_cycle"):
                cycle_result["stop_after_cycle"] = True
                cycle_result["pivot_updates"] = reflection_result.get("pivot_updates", {})

        except Exception as e:
            logger.warning(f"Reflection failed: {e}")

        if self.config.on_phase_end:
            self.config.on_phase_end("reflection")

        # =====================================================
        # IMAGINATION: Generate hypotheses (informed by reflection)
        # =====================================================
        if self.config.on_phase_start:
            self.config.on_phase_start("imagination")

        hypotheses = await self._imagination_phase(reflection_result)

        if self.config.on_phase_end:
            self.config.on_phase_end("imagination")

        cycle_result["hypotheses_generated"] = len(hypotheses)
        self.hypotheses_total += len(hypotheses)
        all_hypotheses = hypotheses

        for hyp in hypotheses:
            if self.config.on_hypothesis_generated:
                self.config.on_hypothesis_generated(hyp)

        # =====================================================
        # INTENT: Evaluate and decide
        # =====================================================
        if self.config.on_phase_start:
            self.config.on_phase_start("intent")

        approved, escalated = await self._intent_phase(hypotheses)

        if self.config.on_phase_end:
            self.config.on_phase_end("intent")

        cycle_result["hypotheses_approved"] = len(approved)
        cycle_result["hypotheses_escalated"] = len(escalated)
        self.escalations_total += len(escalated)

        # Handle escalations
        for hyp in escalated:
            if self.config.on_escalation:
                self.config.on_escalation("approval_needed", {"hypothesis": hyp})

            # Get human decision
            decision = self.deps.human_responder.request_approval(
                summary=f"Approve hypothesis: {hyp.get('description', 'Unknown')}?",
                details=hyp,
            )

            if decision:
                approved.append(hyp)
                cycle_result["hypotheses_approved"] += 1

        # =====================================================
        # WORK: Create and execute tasks
        # =====================================================
        if approved:
            if self.config.on_phase_start:
                self.config.on_phase_start("work")

            tasks = await self._work_phase(approved)

            if self.config.on_phase_end:
                self.config.on_phase_end("work")

            cycle_result["tasks_executed"] = len(tasks)
            self.tasks_total += len(tasks)

            # =====================================================
            # EXECUTION: Execute tasks and track metrics
            # =====================================================
            if self.config.on_phase_start:
                self.config.on_phase_start("execution")

            for task, hyp in tasks:
                result = await self._execution_phase(task, hyp)

                # Track for report
                all_tasks.append({
                    **task,
                    "result": result.metrics_delta,
                    "success": result.success,
                })

                if self.config.on_task_executed:
                    self.config.on_task_executed(task, result)

                if result.success:
                    cycle_result["tasks_succeeded"] += 1
                    cycle_result["revenue_delta"] += result.metrics_delta.get("revenue", 0)
                    cycle_result["signups_delta"] += result.metrics_delta.get("signups", 0)
                else:
                    cycle_result["tasks_failed"] += 1
                    self.failures += 1

            if self.config.on_phase_end:
                self.config.on_phase_end("execution")

        # =====================================================
        # Generate HTML Report
        # =====================================================
        if self.config.generate_reports:
            self._generate_cycle_report(cycle_result, all_hypotheses, all_tasks)

        return cycle_result

    def _generate_cycle_report(self, cycle_result: dict, hypotheses: list, tasks: list):
        """Generate HTML report for this cycle."""
        try:
            from core.report import ReportGenerator
            from core.reflection import ReflectionEngine

            # Run reflection for this cycle
            engine = ReflectionEngine(self.config.project_path, dashboard=self.deps.dashboard)
            reflection = engine.reflect(cycle_number=self.cycle_count)

            # Get current state
            state = self.deps.dashboard.compute_state()

            # Generate report
            generator = ReportGenerator(self.config.project_path)
            report_path = generator.generate(
                cycle_number=self.cycle_count,
                cycle_result=cycle_result,
                reflection_result=reflection.to_dict(),
                hypotheses=hypotheses,
                tasks=tasks,
                north_star_name=self.config.north_star_name,
                north_star_target=self.config.north_star_target,
                north_star_current=state.north_star.current_value,
            )

            logger.info(f"Generated cycle {self.cycle_count} report: {report_path}")

            if self.config.on_report_generated:
                self.config.on_report_generated(report_path)

        except Exception as e:
            # Log the full error for debugging
            logger.error(f"Failed to generate cycle report for cycle {self.cycle_count}: {e}", exc_info=True)

    def _run_reflection(self) -> dict:
        """Run reflection analysis to guide the next cycle."""
        # Demo mode: return mock reflection based on scenario
        if self.config.mode == RunnerMode.DEMO:
            return self._mock_reflection()

        from core.reflection import ReflectionEngine

        engine = ReflectionEngine(self.config.project_path, dashboard=self.deps.dashboard)
        result = engine.reflect(cycle_number=self.cycle_count)

        # Cache the result for reporting
        self._last_reflection = result

        return result.to_dict()

    def _mock_reflection(self) -> dict:
        """Generate mock reflection for demo mode, respecting scenario."""
        scenario = getattr(self, '_demo_scenario', None)

        # Base reflection
        result = {
            "cycle": self.cycle_count,
            "completeness": {
                "can_generate_revenue": True,
                "components_present": ["product", "channel", "payment", "fulfillment"],
                "blockers": [],
            },
            "trajectory": {
                "trend": "positive",
                "velocity": "steady",
            },
            "recommendations": [],
        }

        # Scenario: missing-payment - AUGMENT recommendation
        if scenario == "missing-payment":
            result["completeness"] = {
                "can_generate_revenue": False,
                "components_present": ["product", "channel"],
                "blockers": ["No payment system - cannot process customer payments"],
            }
            result["recommendations"] = [{
                "type": "augment",
                "title": "Add Payment Processing",
                "priority": "critical",
                "component": "payment",
                "suggested_hypotheses": [{
                    "description": "Integrate payment processing to enable revenue"
                }],
            }]

        # Scenario: stalled - OPTIMIZE recommendation
        elif scenario == "stalled" and self.cycle_count >= 3:
            result["trajectory"] = {
                "trend": "plateau",
                "velocity": "stalled",
                "stall_cycles": 2,
            }
            result["recommendations"] = [{
                "type": "optimize",
                "title": "Conversion Rate Optimization",
                "priority": "high",
                "component": "channel",
                "suggested_hypotheses": [{
                    "description": "A/B test landing page to improve conversion"
                }],
            }]

        # Scenario: pivot-needed - PIVOT recommendation (asks human!)
        elif scenario == "pivot-needed" and self.cycle_count >= 2:
            result["trajectory"] = {
                "trend": "negative",
                "velocity": "declining",
                "consecutive_failures": 3,
            }
            result["recommendations"] = [{
                "type": "pivot",
                "title": "Strategy Pivot Required",
                "priority": "critical",
                "reason": "Repeated failures indicate current approach is not working",
                "needs_human_decision": True,
            }]

            # Call pivot decision callback if available
            if self.config.on_pivot_decision_needed:
                pivot_result = self.config.on_pivot_decision_needed({
                    "failure_rate": 0.7,
                    "consecutive_failures": 3,
                    "current_strategy": "Content marketing + SEO",
                })
                result["pivot_decision"] = pivot_result

                # If user confirmed a pivot, we need to stop after this cycle
                if isinstance(pivot_result, dict):
                    if pivot_result.get("action") == "update_foundation_and_restart":
                        result["stop_after_cycle"] = True
                        result["pivot_updates"] = pivot_result.get("updates", {})

        return result

    async def _imagination_phase(self, reflection_result: dict = None) -> list[dict]:
        """Generate hypotheses using Claude (or mock), informed by reflection."""
        from core.dashboard import EventType

        # Load foundation docs (cached after first load)
        if not self._foundation_loaded:
            self._oracle = await self._load_foundation("oracle")
            self._north_star = await self._load_foundation("north_star")
            self._context = await self._load_foundation("context")
            self._foundation_loaded = True

        # Initialize hypothesis manager for vendor selection (only if callback exists)
        if self._hypothesis_manager is None and self.config.on_vendor_selection_needed:
            from core.hypothesis import HypothesisManager
            self._hypothesis_manager = HypothesisManager(
                project_path=self.config.project_path,
                ask_user_callback=self.config.on_vendor_selection_needed,
            )

        # Get current dashboard state for context
        state = self.deps.dashboard.compute_state()

        # Generate hypotheses with reflection guidance
        hypotheses = await self._call_imagination_activity(
            oracle=self._oracle,
            north_star=self._north_star,
            context=self._context,
            dashboard_state=state,
            reflection=reflection_result,  # Pass reflection to guide hypothesis generation
        )

        # Log to dashboard
        for hyp in hypotheses:
            self.deps.dashboard.log_event(
                EventType.HYPOTHESIS_CREATED,
                metadata={"id": hyp.get("id"), "desc": hyp.get("description", "")[:50]},
            )

        return hypotheses

    async def _intent_phase(self, hypotheses: list[dict]) -> tuple[list[dict], list[dict]]:
        """Evaluate hypotheses and decide which to pursue."""
        from core.dashboard import EventType

        approved = []
        escalated = []

        for hyp in hypotheses:
            # Calculate combined score
            feasibility = hyp.get("feasibility", 0)
            alignment = hyp.get("north_star_alignment", 0)
            score = feasibility * 0.4 + alignment * 0.6

            hyp["_combined_score"] = score

            if score >= self.config.approval_threshold:
                # Check if this hypothesis needs vendor/implementation selection
                # This implements the two-level hypothesis system:
                # Level 1 (CAPABILITY): What we want to achieve (approved here)
                # Level 2 (IMPLEMENTATION): How we'll achieve it (selected via callback)
                needs_vendor = (
                    hyp.get("needs_vendor_decision") or  # Explicit flag (demo mode)
                    (self._hypothesis_manager and self._hypothesis_manager.needs_implementation_decision(hyp))
                )

                if needs_vendor and self._hypothesis_manager:
                    # This hypothesis needs a vendor/technology choice
                    selection = self._hypothesis_manager.select_implementation(hyp)

                    if selection:
                        # Create implementation-specific hypothesis
                        impl_hyp = self._hypothesis_manager.create_implementation_hypothesis(hyp, selection)

                        # Replace capability hypothesis with implementation hypothesis
                        # (Keep the capability for records, use implementation for work)
                        hyp["implementation"] = impl_hyp
                        hyp["selected_vendor"] = selection.selected_vendor
                        hyp["vendor_source"] = selection.source

                approved.append(hyp)
                self.deps.dashboard.log_event(
                    EventType.HYPOTHESIS_ACCEPTED,
                    metadata={"id": hyp.get("id")},
                )
            elif score >= self.config.escalation_threshold:
                escalated.append(hyp)
            else:
                self.deps.dashboard.log_event(
                    EventType.HYPOTHESIS_REJECTED,
                    metadata={"id": hyp.get("id"), "reason": "score_too_low"},
                )

        return approved, escalated

    async def _work_phase(self, approved: list[dict]) -> list[tuple[dict, dict]]:
        """Create tasks from approved hypotheses."""
        from core.dashboard import EventType

        tasks = []

        for hyp in approved[:self.config.max_tasks_per_cycle]:
            task = await self._call_work_activity(hyp)

            self.deps.dashboard.log_event(
                EventType.TASK_CREATED,
                task_id=task.get("id"),
                hypothesis_id=hyp.get("id"),
            )

            tasks.append((task, hyp))

        return tasks

    async def _execution_phase(self, task: dict, hypothesis: dict) -> ExecutionResult:
        """Execute a task and log results."""
        from core.dashboard import EventType

        # Execute using injected executor
        result = self.deps.executor.execute(task, hypothesis)

        if result.success:
            self.deps.dashboard.log_event(
                EventType.TASK_COMPLETED,
                task_id=task.get("id"),
            )

            # Log metrics
            if result.metrics_delta.get("revenue"):
                self.deps.dashboard.log_event(
                    EventType.REVENUE,
                    value=result.metrics_delta["revenue"],
                    task_id=task.get("id"),
                )
            if result.metrics_delta.get("signups"):
                self.deps.dashboard.log_event(
                    EventType.SIGNUP,
                    value=result.metrics_delta["signups"],
                    task_id=task.get("id"),
                )
        else:
            self.deps.dashboard.log_event(
                EventType.TASK_FAILED,
                task_id=task.get("id"),
                metadata={"errors": result.errors},
            )

        return result

    async def _load_foundation(self, doc_type: str) -> dict:
        """Load foundation document."""
        # In real mode, this reads files. In demo, returns mock data.
        if self.config.mode == RunnerMode.DEMO:
            return self._mock_foundation(doc_type)

        from temporal.activities.foundation import (
            read_oracle,
            read_north_star,
            read_context,
        )

        project_path = str(self.config.project_path)

        if doc_type == "oracle":
            return await read_oracle(project_path)
        elif doc_type == "north_star":
            return await read_north_star(project_path)
        elif doc_type == "context":
            return await read_context(project_path)

        return {}

    def _mock_foundation(self, doc_type: str) -> dict:
        """Return mock foundation data for demo mode."""
        if doc_type == "oracle":
            return {
                "values": ["Customer-first", "Move fast", "Data-driven"],
                "never_do": ["Spam users", "Mislead customers"],
                "always_do": ["Test before deploy", "Measure outcomes"],
            }
        elif doc_type == "north_star":
            return {
                "objectives": [
                    "Reach $1M ARR",
                    "Acquire 10,000 customers",
                    "Achieve 90% retention",
                ],
                "success_metrics": ["MRR", "Customer count", "Churn rate"],
            }
        elif doc_type == "context":
            return {
                "constraints": ["$50k budget", "3 month timeline"],
                "resources": ["2 developers", "1 marketer"],
            }
        return {}

    async def _call_imagination_activity(
        self,
        oracle: dict,
        north_star: dict,
        context: dict,
        dashboard_state: Any,
        reflection: dict = None,
    ) -> list[dict]:
        """Call imagination activity (real or mock), informed by reflection."""
        if self.config.mode == RunnerMode.DEMO:
            return self._mock_imagination(reflection)

        from temporal.activities.imagination import generate_hypotheses

        return await generate_hypotheses(
            project_path=str(self.config.project_path),
            oracle=oracle,
            north_star=north_star,
            context=context,
            existing_hypotheses=[],
            max_new=self.config.max_hypotheses_per_cycle,
            reflection=reflection,  # Pass reflection to guide generation
        )

    def _mock_imagination(self, reflection: dict = None) -> list[dict]:
        """Generate mock hypotheses for demo mode, guided by reflection and foundation."""
        import random

        # Check for demo scenario
        scenario = getattr(self, '_demo_scenario', None)

        # Check for foundation context (used by forecast mode for grounded simulation)
        foundation = getattr(self, '_foundation', None)
        if foundation:
            # Use foundation-aware hypothesis generation
            return foundation.get_mock_hypotheses(
                cycle=self.cycle_count,
                max_count=self.config.max_hypotheses_per_cycle,
            )

        # Handle vendor-choice scenario: Generate hypothesis that needs vendor decision
        if scenario == "vendor-choice" and self.cycle_count == 1:
            return [{
                "id": f"hyp-{self.cycle_count:03d}-PAY",
                "description": "Enable payment processing for customer transactions",
                "feasibility": 0.90,
                "north_star_alignment": 0.99,
                "estimated_effort": "medium",
                "category": "payment",  # This triggers vendor selection
                "priority": "critical",
                "needs_vendor_decision": True,  # Explicit flag
            }]

        # Handle missing-payment scenario: First cycle returns no payment component
        if scenario == "missing-payment" and self.cycle_count == 1:
            return [{
                "id": f"hyp-{self.cycle_count:03d}-CHN",
                "description": "Launch landing page with SEO optimization",
                "feasibility": 0.85,
                "north_star_alignment": 0.70,
                "estimated_effort": "medium",
                "category": "channel",
            }]

        # Default descriptions for product/optimization work
        default_descriptions = [
            "Implement email marketing automation",
            "Add social proof to landing page",
            "Create referral program",
            "Optimize checkout flow",
            "Launch content marketing campaign",
            "Build partnership integrations",
            "Improve onboarding experience",
            "Add premium tier pricing",
            "Implement A/B testing framework",
            "Create customer feedback loop",
        ]

        # CRITICAL: Check if reflection says we're missing key components
        # and prioritize those hypotheses
        priority_hypotheses = []

        if reflection:
            completeness = reflection.get("completeness", {})
            can_generate = completeness.get("can_generate_revenue", True)
            blockers = completeness.get("blockers", [])
            recommendations = reflection.get("recommendations", [])

            # If we can't generate revenue, prioritize fixing that
            if not can_generate:
                for blocker in blockers:
                    if "payment" in blocker.lower():
                        priority_hypotheses.append({
                            "id": f"hyp-{self.cycle_count:03d}-PAY",
                            "description": "Integrate Stripe payment processing to enable customer transactions and revenue generation",
                            "feasibility": 0.85,
                            "north_star_alignment": 0.99,  # Critical for revenue!
                            "estimated_effort": "medium",
                            "category": "payment",
                            "priority": "critical",
                        })
                    if "channel" in blocker.lower() or "find you" in blocker.lower():
                        priority_hypotheses.append({
                            "id": f"hyp-{self.cycle_count:03d}-CHN",
                            "description": "Launch landing page with SEO and social sharing to acquire customers",
                            "feasibility": 0.80,
                            "north_star_alignment": 0.95,
                            "estimated_effort": "medium",
                            "category": "channel",
                            "priority": "critical",
                        })
                    if "product" in blocker.lower():
                        priority_hypotheses.append({
                            "id": f"hyp-{self.cycle_count:03d}-PRD",
                            "description": "Build and deploy MVP product to production",
                            "feasibility": 0.70,
                            "north_star_alignment": 0.98,
                            "estimated_effort": "large",
                            "category": "product",
                            "priority": "critical",
                        })

            # Also add hypotheses from recommendations
            for rec in recommendations:
                if rec.get("type") in ["augment", "optimize"]:
                    for hyp in rec.get("suggested_hypotheses", []):
                        priority_hypotheses.append({
                            "id": f"hyp-{self.cycle_count:03d}-REC",
                            "description": hyp.get("description", rec.get("title", "Implement recommendation")),
                            "feasibility": 0.75,
                            "north_star_alignment": 0.90,
                            "estimated_effort": "medium",
                            "category": rec.get("component", "general"),
                            "priority": "high",
                        })

        # If we have priority hypotheses, return those first
        if priority_hypotheses:
            # Add some regular hypotheses too
            num_regular = max(0, self.config.max_hypotheses_per_cycle - len(priority_hypotheses))
            regular = []
            for i in range(min(num_regular, 2)):
                regular.append({
                    "id": f"hyp-{self.cycle_count:03d}-{i+1}",
                    "description": random.choice(default_descriptions),
                    "feasibility": random.uniform(0.5, 0.85),
                    "north_star_alignment": random.uniform(0.5, 0.80),  # Lower than priority
                    "estimated_effort": random.choice(["small", "medium"]),
                    "priority": "normal",
                })
            return priority_hypotheses + regular

        # Default behavior if no reflection or no issues
        num = random.randint(2, self.config.max_hypotheses_per_cycle)
        hypotheses = []

        for i in range(num):
            hyp = {
                "id": f"hyp-{self.cycle_count:03d}-{i+1}",
                "description": random.choice(default_descriptions),
                "feasibility": random.uniform(0.5, 0.95),
                "north_star_alignment": random.uniform(0.6, 0.98),
                "estimated_effort": random.choice(["small", "medium", "large"]),
            }
            hypotheses.append(hyp)

        return hypotheses

    async def _call_work_activity(self, hypothesis: dict) -> dict:
        """Call work activity to create task (real or mock)."""
        if self.config.mode == RunnerMode.DEMO:
            return self._mock_task(hypothesis)

        from temporal.activities.work import create_task

        return await create_task(
            project_path=str(self.config.project_path),
            hypothesis=hypothesis,
            oracle=self._oracle,
            context=self._context,
        )

    def _mock_task(self, hypothesis: dict) -> dict:
        """Create mock task for demo mode."""
        return {
            "id": f"task-{self.cycle_count:03d}-{hypothesis['id'].split('-')[-1]}",
            "hypothesis_id": hypothesis["id"],
            "description": f"Execute: {hypothesis['description'][:40]}",
            "task_type": "build",
        }

    def _build_summary(self) -> dict:
        """Build final summary of the run."""
        state = self.deps.dashboard.compute_state()

        # Calculate simulated time
        simulated_days = self.cycle_count * self.config.days_per_cycle
        weeks = simulated_days // 7
        days = simulated_days % 7

        if weeks > 0:
            time_estimate = f"{weeks} week{'s' if weeks != 1 else ''}"
            if days > 0:
                time_estimate += f" {days} day{'s' if days != 1 else ''}"
        else:
            time_estimate = f"{days} day{'s' if days != 1 else ''}"

        return {
            "target_reached": self.target_reached,
            "cycles_completed": self.cycle_count,
            "hypotheses_total": self.hypotheses_total,
            "tasks_total": self.tasks_total,
            "escalations_total": self.escalations_total,
            "failures": self.failures,
            "final_revenue": state.north_star.current_value,
            "target_revenue": self.config.north_star_target,
            "progress_pct": state.north_star.progress_pct,
            "metrics": state.metrics_lifetime,
            "success_rate": (self.tasks_total - self.failures) / max(self.tasks_total, 1),
            # Time simulation
            "simulated_days": simulated_days,
            "time_estimate": time_estimate,
            "days_per_cycle": self.config.days_per_cycle,
        }


# =============================================================================
# Human Responders
# =============================================================================

class MockHumanResponder:
    """Mock human that always approves."""

    def __init__(self, approve_rate: float = 1.0):
        self.approve_rate = approve_rate

    def request_decision(
        self,
        escalation_type: str,
        summary: str,
        options: list[str],
        context: dict,
    ) -> dict:
        import random
        if random.random() < self.approve_rate:
            return {"action": "approve", "feedback": "Approved"}
        return {"action": "reject", "feedback": "Rejected"}

    def request_approval(self, summary: str, details: dict) -> bool:
        import random
        return random.random() < self.approve_rate


class CLIHumanResponder:
    """Human responder via CLI prompts."""

    def __init__(self, console=None):
        self.console = console

    def request_decision(
        self,
        escalation_type: str,
        summary: str,
        options: list[str],
        context: dict,
    ) -> dict:
        from rich.prompt import Prompt
        from rich.panel import Panel

        if self.console:
            self.console.print()
            self.console.print(Panel(
                f"[bold]{escalation_type.upper()}[/bold]\n\n{summary}",
                title="Human Decision Required",
                border_style="yellow",
            ))

            if options:
                self.console.print("Options:")
                for i, opt in enumerate(options, 1):
                    self.console.print(f"  {i}. {opt}")

            action = Prompt.ask(
                "Your decision",
                choices=options + ["skip"] if options else ["approve", "reject", "skip"],
                default="approve" if not options else options[0],
            )

            feedback = Prompt.ask("Feedback (optional)", default="")

            return {"action": action, "feedback": feedback or None}

        # Fallback to input()
        print(f"\n=== {escalation_type.upper()} ===")
        print(summary)
        action = input("Action [approve/reject/skip]: ").strip() or "approve"
        return {"action": action, "feedback": None}

    def request_approval(self, summary: str, details: dict) -> bool:
        from rich.prompt import Confirm
        from rich.panel import Panel

        if self.console:
            self.console.print()
            self.console.print(Panel(
                f"{summary}\n\n[dim]Details: {details.get('description', 'N/A')}[/dim]",
                title="Approval Required",
                border_style="yellow",
            ))
            return Confirm.ask("Approve?", default=True)

        # Fallback
        print(f"\n=== APPROVAL REQUIRED ===")
        print(summary)
        response = input("Approve? [Y/n]: ").strip().lower()
        return response != "n"


# =============================================================================
# Factory Functions
# =============================================================================

def create_demo_runner(
    project_path: Path,
    speed: float = 1.0,
    max_cycles: int = 100,
    include_chaos: bool = False,
    on_cycle_start: Callable = None,
    on_cycle_end: Callable = None,
    on_progress_update: Callable = None,
    on_phase_start: Callable = None,
    on_phase_end: Callable = None,
    on_vendor_selection_needed: Callable = None,
    on_pivot_decision_needed: Callable = None,
    scenario: str = None,
) -> CycleRunner:
    """
    Create a runner configured for demo mode.

    Scenarios:
      - missing-payment: Start without payment component (triggers AUGMENT)
      - stalled: Metrics plateau after initial growth (triggers OPTIMIZE)
      - pivot-needed: Repeated failures (triggers PIVOT - asks human)
      - vendor-choice: Hypothesis needs vendor decision (asks human)
    """
    from core.dashboard import Dashboard
    from tests.mocks.execution import ScenarioExecutor
    from tests.mocks.claude_client import MockAnthropicClient

    dashboard = Dashboard(project_path)

    config = RunnerConfig(
        mode=RunnerMode.DEMO,
        project_path=project_path,
        max_cycles=max_cycles,
        demo_speed=speed,
        demo_delay_base=0.5 / speed,
        on_cycle_start=on_cycle_start,
        on_cycle_end=on_cycle_end,
        on_progress_update=on_progress_update,
        on_phase_start=on_phase_start,
        on_phase_end=on_phase_end,
        on_vendor_selection_needed=on_vendor_selection_needed,
        on_pivot_decision_needed=on_pivot_decision_needed,
    )

    deps = Dependencies(
        claude_client=MockAnthropicClient(),
        human_responder=MockHumanResponder(approve_rate=0.9 if include_chaos else 1.0),
        executor=ScenarioExecutor(project_path, dashboard, scenario=scenario),
        dashboard=dashboard,
    )

    runner = CycleRunner(config, deps)
    runner._demo_scenario = scenario  # Store for mock imagination to use
    return runner


def create_local_runner(
    project_path: Path,
    console=None,
    on_cycle_start: Callable = None,
    on_cycle_end: Callable = None,
    on_progress_update: Callable = None,
    on_hypothesis_generated: Callable = None,
    on_task_executed: Callable = None,
    on_phase_start: Callable = None,
    on_phase_end: Callable = None,
    on_report_generated: Callable = None,
    on_vendor_selection_needed: Callable = None,
    generate_reports: bool = True,
) -> CycleRunner:
    """Create a runner configured for local mode (real Claude, CLI human)."""
    import os
    from core.dashboard import Dashboard
    from core.conversation import ConversationManager
    import anthropic

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Try loading from project .env
        env_path = Path(project_path) / ".1kh" / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break

    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. Set it in environment or in .1kh/.env"
        )

    # Ensure API key is in environment so activities can find it
    os.environ["ANTHROPIC_API_KEY"] = api_key

    dashboard = Dashboard(project_path)
    conv_manager = ConversationManager(project_path)

    config = RunnerConfig(
        mode=RunnerMode.LOCAL,
        project_path=project_path,
        on_cycle_start=on_cycle_start,
        on_cycle_end=on_cycle_end,
        on_progress_update=on_progress_update,
        on_hypothesis_generated=on_hypothesis_generated,
        on_task_executed=on_task_executed,
        on_phase_start=on_phase_start,
        on_phase_end=on_phase_end,
        on_report_generated=on_report_generated,
        on_vendor_selection_needed=on_vendor_selection_needed,
        generate_reports=generate_reports,
    )

    # Real executor that uses Claude
    from core.executor import ClaudeExecutor

    # Create Claude client with explicit API key
    claude_client = anthropic.Anthropic(api_key=api_key)

    deps = Dependencies(
        claude_client=claude_client,
        human_responder=CLIHumanResponder(console=console),
        executor=ClaudeExecutor(project_path, dashboard, conv_manager, claude_client=claude_client),
        dashboard=dashboard,
        conversation_manager=conv_manager,
    )

    return CycleRunner(config, deps)
