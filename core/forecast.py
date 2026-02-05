"""
Forecast Engine - Business simulation without real execution.

This module enables users to simulate their business trajectory:
- Preview journey, estimate costs/timeline, identify risks
- Run Monte Carlo simulations with different human behaviors
- Replay past forecasts with different inputs

Modes:
    | Mode     | Flag          | Claude    | Human      | Use Case                    |
    |----------|---------------|-----------|------------|-----------------------------|
    | Mock     | --mock        | Mocked    | Mocked     | Fast testing, no tokens     |
    | Live     | (default)     | Real API  | Simulated  | First run, captures trace   |
    | Replay   | --replay <id> | Cached    | Configurable | Re-run with different inputs |
    | Scenario | --runs N      | Cached    | Randomized | Monte Carlo distribution    |

Configurable Variables:
    - human_quality: perfect, good, mediocre, poor
    - human_delay_hours: 1, 4, 24, 72, 168
    - market_response: optimistic, realistic, pessimistic
    - execution_variance: 0.0 - 1.0
    - chaos_level: none, low, medium, high
    - human_selection: optimal, random, worst
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any

logger = logging.getLogger("1kh.forecast")


# =============================================================================
# Forecast Variables (Configurable Parameters)
# =============================================================================

@dataclass
class ForecastVariables:
    """Configurable simulation parameters."""
    # Human behavior
    human_quality: str = "good"  # perfect, good, mediocre, poor
    human_delay_hours: int = 4   # 1, 4, 24, 72, 168
    human_selection: str = "optimal"  # optimal, random, worst

    # Market conditions
    market_response: str = "realistic"  # optimistic, realistic, pessimistic

    # Execution
    execution_variance: float = 0.0  # 0.0 - 1.0
    chaos_level: str = "none"  # none, low, medium, high

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ForecastVariables":
        return cls(**data)

    def get_human_approve_rate(self) -> float:
        """Convert human_quality to approval rate."""
        rates = {
            "perfect": 1.0,
            "good": 0.9,
            "mediocre": 0.7,
            "poor": 0.5,
        }
        return rates.get(self.human_quality, 0.9)

    def get_market_multiplier(self) -> float:
        """Convert market_response to metric multiplier."""
        multipliers = {
            "optimistic": 1.3,
            "realistic": 1.0,
            "pessimistic": 0.7,
        }
        return multipliers.get(self.market_response, 1.0)

    def get_chaos_failure_rate(self) -> float:
        """Convert chaos_level to additional failure rate."""
        rates = {
            "none": 0.0,
            "low": 0.1,
            "medium": 0.2,
            "high": 0.4,
        }
        return rates.get(self.chaos_level, 0.0)


# =============================================================================
# Forecast Manifest (Trace Metadata)
# =============================================================================

@dataclass
class ForecastManifest:
    """Metadata for a forecast trace."""
    trace_id: str
    created_at: str
    mode: str  # "mock", "live", "replay"
    variables: dict
    foundation_hash: str  # Hash of foundation docs for drift detection
    foundation_files: dict[str, str]  # filename -> hash
    cycles_completed: int = 0
    outcome: Optional[dict] = None
    parent_trace_id: Optional[str] = None  # For replays

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ForecastManifest":
        return cls(**data)

    @classmethod
    def create(
        cls,
        mode: str,
        variables: ForecastVariables,
        foundation_hash: str,
        foundation_files: dict[str, str],
        parent_trace_id: Optional[str] = None,
    ) -> "ForecastManifest":
        """Create a new manifest."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        trace_id = f"trace_{timestamp}"
        return cls(
            trace_id=trace_id,
            created_at=datetime.utcnow().isoformat(),
            mode=mode,
            variables=variables.to_dict(),
            foundation_hash=foundation_hash,
            foundation_files=foundation_files,
            parent_trace_id=parent_trace_id,
        )


# =============================================================================
# Forecast Outcome (Final Results)
# =============================================================================

@dataclass
class ForecastOutcome:
    """Final results of a forecast run."""
    target_reached: bool
    cycles_completed: int
    final_revenue: float
    target_revenue: float
    time_estimate: str  # "4-6 months"
    estimated_api_cost: float
    human_decisions_required: int
    risk_level: str  # "low", "medium", "high"
    success_rate: float  # 0.0 - 1.0
    progress_pct: float
    total_hypotheses: int = 0
    total_tasks: int = 0
    total_failures: int = 0
    simulated_days: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ForecastOutcome":
        return cls(**data)


# =============================================================================
# Trace Manager
# =============================================================================

class TraceManager:
    """
    Manages forecast traces on disk.

    Trace Structure:
        .1kh/forecasts/
        ├── trace_20260205_143000/
        │   ├── manifest.json
        │   ├── foundation_snapshot/
        │   │   ├── oracle.md
        │   │   ├── north-star.md
        │   │   └── context.md
        │   ├── claude_cache/
        │   │   ├── index.json
        │   │   └── cycle_001_imagination_001.json
        │   ├── human_decisions/
        │   ├── events.jsonl
        │   └── outcome.json
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.forecasts_dir = self.project_path / ".1kh" / "forecasts"
        self.forecasts_dir.mkdir(parents=True, exist_ok=True)

    def create_trace(
        self,
        mode: str,
        variables: ForecastVariables,
        parent_trace_id: Optional[str] = None,
    ) -> Path:
        """
        Create a new forecast trace.

        Returns: Path to trace directory
        """
        # Compute foundation hash
        foundation_hash, foundation_files = self._hash_foundation()

        # Create manifest
        manifest = ForecastManifest.create(
            mode=mode,
            variables=variables,
            foundation_hash=foundation_hash,
            foundation_files=foundation_files,
            parent_trace_id=parent_trace_id,
        )

        # Create trace directory
        trace_dir = self.forecasts_dir / manifest.trace_id
        trace_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (trace_dir / "claude_cache").mkdir(exist_ok=True)
        (trace_dir / "human_decisions").mkdir(exist_ok=True)
        (trace_dir / "foundation_snapshot").mkdir(exist_ok=True)

        # Snapshot foundation docs
        self._snapshot_foundation(trace_dir / "foundation_snapshot")

        # Write manifest
        manifest_path = trace_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2))

        logger.info(f"Created forecast trace: {manifest.trace_id}")
        return trace_dir

    def get_trace(self, trace_id: str) -> Optional[Path]:
        """Get trace directory by ID."""
        trace_dir = self.forecasts_dir / trace_id
        if trace_dir.exists():
            return trace_dir
        return None

    def get_manifest(self, trace_id: str) -> Optional[ForecastManifest]:
        """Get manifest for a trace."""
        trace_dir = self.get_trace(trace_id)
        if not trace_dir:
            return None

        manifest_path = trace_dir / "manifest.json"
        if not manifest_path.exists():
            return None

        try:
            data = json.loads(manifest_path.read_text())
            return ForecastManifest.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to load manifest: {e}")
            return None

    def update_manifest(self, trace_id: str, updates: dict):
        """Update manifest fields."""
        trace_dir = self.get_trace(trace_id)
        if not trace_dir:
            return

        manifest_path = trace_dir / "manifest.json"
        if not manifest_path.exists():
            return

        data = json.loads(manifest_path.read_text())
        data.update(updates)
        manifest_path.write_text(json.dumps(data, indent=2))

    def save_outcome(self, trace_id: str, outcome: ForecastOutcome):
        """Save outcome to trace."""
        trace_dir = self.get_trace(trace_id)
        if not trace_dir:
            return

        outcome_path = trace_dir / "outcome.json"
        outcome_path.write_text(json.dumps(outcome.to_dict(), indent=2))

        # Also update manifest
        self.update_manifest(trace_id, {
            "outcome": outcome.to_dict(),
            "cycles_completed": outcome.cycles_completed,
        })

    def list_traces(self) -> list[dict]:
        """List all traces with summary info."""
        traces = []
        for trace_dir in sorted(self.forecasts_dir.iterdir(), reverse=True):
            if not trace_dir.is_dir():
                continue

            manifest = self.get_manifest(trace_dir.name)
            if not manifest:
                continue

            # Get outcome if available
            outcome_path = trace_dir / "outcome.json"
            outcome = None
            if outcome_path.exists():
                try:
                    outcome = json.loads(outcome_path.read_text())
                except json.JSONDecodeError:
                    pass

            traces.append({
                "trace_id": manifest.trace_id,
                "created_at": manifest.created_at,
                "mode": manifest.mode,
                "cycles_completed": manifest.cycles_completed,
                "outcome": outcome,
                "variables": manifest.variables,
            })

        return traces

    def check_foundation_drift(self, trace_id: str) -> list[str]:
        """
        Check if foundation has changed since trace was created.

        Returns: List of changed files (empty if no drift)
        """
        manifest = self.get_manifest(trace_id)
        if not manifest:
            return ["manifest_not_found"]

        current_hash, current_files = self._hash_foundation()

        changed = []
        for filename, old_hash in manifest.foundation_files.items():
            new_hash = current_files.get(filename, "missing")
            if old_hash != new_hash:
                changed.append(filename)

        # Check for new files
        for filename in current_files:
            if filename not in manifest.foundation_files:
                changed.append(f"{filename} (new)")

        return changed

    def delete_trace(self, trace_id: str) -> bool:
        """Delete a trace."""
        trace_dir = self.get_trace(trace_id)
        if trace_dir and trace_dir.exists():
            shutil.rmtree(trace_dir)
            logger.info(f"Deleted trace: {trace_id}")
            return True
        return False

    def _hash_foundation(self) -> tuple[str, dict[str, str]]:
        """Compute hash of foundation documents."""
        foundation_dir = self.project_path / "foundation"
        files_to_hash = ["oracle.md", "north-star.md", "context.md"]

        file_hashes = {}
        combined = ""

        for filename in files_to_hash:
            filepath = foundation_dir / filename
            if filepath.exists():
                content = filepath.read_text()
                file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                file_hashes[filename] = file_hash
                combined += file_hash

        overall_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]
        return overall_hash, file_hashes

    def _snapshot_foundation(self, snapshot_dir: Path):
        """Copy foundation docs to snapshot directory."""
        foundation_dir = self.project_path / "foundation"
        files_to_copy = ["oracle.md", "north-star.md", "context.md"]

        for filename in files_to_copy:
            src = foundation_dir / filename
            if src.exists():
                dst = snapshot_dir / filename
                shutil.copy2(src, dst)


# =============================================================================
# Simulated Human Responder
# =============================================================================

class SimulatedHumanResponder:
    """
    Simulates human responses based on ForecastVariables.

    Used in forecast mode to simulate human decisions without prompts.
    """

    def __init__(self, variables: ForecastVariables, seed: int = None):
        self.variables = variables
        self.rng = random.Random(seed)
        self.decisions_made = 0
        self.decisions_log: list[dict] = []

    def request_decision(
        self,
        escalation_type: str,
        summary: str,
        options: list[str],
        context: dict,
    ) -> dict:
        """Simulate a human decision."""
        self.decisions_made += 1

        # Determine action based on human_quality
        approve_rate = self.variables.get_human_approve_rate()

        if self.rng.random() < approve_rate:
            # Select option based on human_selection
            if self.variables.human_selection == "optimal":
                action = options[0] if options else "approve"
            elif self.variables.human_selection == "worst":
                action = options[-1] if options else "reject"
            else:  # random
                action = self.rng.choice(options) if options else "approve"
        else:
            action = "reject"

        decision = {"action": action, "feedback": f"Simulated: {action}"}

        # Log the decision
        self.decisions_log.append({
            "decision_number": self.decisions_made,
            "escalation_type": escalation_type,
            "summary": summary[:100],
            "options": options,
            "result": decision,
        })

        return decision

    def request_approval(self, summary: str, details: dict) -> bool:
        """Simulate approval request."""
        self.decisions_made += 1
        approve_rate = self.variables.get_human_approve_rate()
        approved = self.rng.random() < approve_rate

        self.decisions_log.append({
            "decision_number": self.decisions_made,
            "escalation_type": "approval_request",
            "summary": summary[:100],
            "result": {"approved": approved},
        })

        return approved

    def save_decisions(self, output_dir: Path):
        """Save decisions log to file."""
        output_path = output_dir / "decisions.json"
        output_path.write_text(json.dumps(self.decisions_log, indent=2))


# =============================================================================
# Simulated Executor
# =============================================================================

class SimulatedExecutor:
    """
    Executor that simulates task outcomes based on ForecastVariables.

    Applies market conditions and chaos to outcomes.
    """

    def __init__(
        self,
        project_path: Path,
        dashboard: Any,
        variables: ForecastVariables,
        seed: int = None,
    ):
        self.project_path = project_path
        self.dashboard = dashboard
        self.variables = variables
        self.rng = random.Random(seed)
        self.execution_count = 0
        self.successes = 0

    def execute(self, task: dict, hypothesis: dict = None):
        """Execute task with simulated outcomes."""
        from core.runner import ExecutionResult
        from core.dashboard import EventType

        self.execution_count += 1
        task_id = task.get("id", f"task-{self.execution_count}")
        hypothesis_id = hypothesis.get("id") if hypothesis else None

        # Log start
        self.dashboard.log_event(
            EventType.TASK_STARTED,
            task_id=task_id,
            hypothesis_id=hypothesis_id,
        )

        # Determine success/failure
        base_failure_rate = 0.15
        chaos_failure = self.variables.get_chaos_failure_rate()
        variance_failure = self.variables.execution_variance * 0.2
        total_failure_rate = base_failure_rate + chaos_failure + variance_failure

        success = self.rng.random() > total_failure_rate

        if success:
            self.successes += 1
            return self._generate_success(task, task_id, hypothesis_id)
        else:
            return self._generate_failure(task, task_id, hypothesis_id)

    def _generate_success(self, task: dict, task_id: str, hypothesis_id: str):
        """Generate successful outcome."""
        from core.runner import ExecutionResult
        from core.dashboard import EventType

        # Base metrics with market multiplier
        multiplier = self.variables.get_market_multiplier()
        growth_mult = 1.1 ** (self.successes - 1)  # Growth over time

        base_signups = 10 * multiplier * growth_mult
        base_revenue = 100 * multiplier * growth_mult

        # Add noise
        noise = 1 + self.rng.uniform(-0.3, 0.3)
        signups = int(base_signups * noise)
        revenue = base_revenue * noise

        # Log metrics
        self.dashboard.log_event(EventType.SIGNUP, value=signups, task_id=task_id, hypothesis_id=hypothesis_id)
        self.dashboard.log_event(EventType.REVENUE, value=revenue, task_id=task_id, hypothesis_id=hypothesis_id)
        self.dashboard.log_event(EventType.TASK_COMPLETED, task_id=task_id, hypothesis_id=hypothesis_id)

        return ExecutionResult(
            success=True,
            task_id=task_id,
            hypothesis_id=hypothesis_id,
            result_text=f"Task {task_id} completed",
            duration_seconds=60,
            metrics_delta={"signups": signups, "revenue": revenue},
        )

    def _generate_failure(self, task: dict, task_id: str, hypothesis_id: str):
        """Generate failure outcome."""
        from core.runner import ExecutionResult
        from core.dashboard import EventType

        errors = [
            "Timeout exceeded",
            "Dependency unavailable",
            "Resource constraint",
            "Permission denied",
        ]
        error = self.rng.choice(errors)

        self.dashboard.log_event(
            EventType.TASK_FAILED,
            task_id=task_id,
            hypothesis_id=hypothesis_id,
            metadata={"error": error},
        )

        return ExecutionResult(
            success=False,
            task_id=task_id,
            hypothesis_id=hypothesis_id,
            result_text=f"Task {task_id} failed: {error}",
            errors=[error],
            needs_human=False,
        )


# =============================================================================
# Forecast Runner
# =============================================================================

class ForecastRunner:
    """
    Runs forecast simulations.

    Uses CycleRunner internally via composition, not inheritance.
    Operates silently (no interactive output) for fast batch processing.
    """

    def __init__(
        self,
        project_path: Path,
        mode: str,  # "mock", "live", "replay"
        variables: ForecastVariables,
        max_cycles: int = 50,
        trace_id: Optional[str] = None,  # For replay mode
        seed: int = None,
        on_cycle_complete: Optional[Callable[[int, dict], None]] = None,
    ):
        self.project_path = Path(project_path)
        self.mode = mode
        self.variables = variables
        self.max_cycles = max_cycles
        self.trace_id = trace_id
        self.seed = seed or random.randint(0, 1000000)
        self.on_cycle_complete = on_cycle_complete

        # Initialize trace manager
        self.trace_manager = TraceManager(project_path)

        # State
        self.trace_dir: Optional[Path] = None
        self.human_responder: Optional[SimulatedHumanResponder] = None
        self.api_cost_estimate = 0.0

    async def run(self) -> ForecastOutcome:
        """
        Run the forecast simulation.

        Returns: ForecastOutcome with final results
        """
        from core.runner import CycleRunner, RunnerConfig, RunnerMode, Dependencies
        from core.dashboard import Dashboard
        from core.claude_cache import CachedClaudeClient, CacheMode, ClaudeCache

        # Create or load trace
        if self.mode == "replay" and self.trace_id:
            self.trace_dir = self.trace_manager.get_trace(self.trace_id)
            if not self.trace_dir:
                raise ValueError(f"Trace not found: {self.trace_id}")

            # Check for foundation drift
            drift = self.trace_manager.check_foundation_drift(self.trace_id)
            if drift:
                logger.warning(f"Foundation drift detected: {drift}")
        else:
            self.trace_dir = self.trace_manager.create_trace(
                mode=self.mode,
                variables=self.variables,
            )
            self.trace_id = self.trace_dir.name

        # Set up components based on mode
        dashboard = Dashboard(self.project_path)
        dashboard.event_log.log_file = self.trace_dir / "events.jsonl"  # Write to trace
        dashboard.set_north_star("$1M ARR", target_value=1_000_000)

        # Create simulated human responder
        self.human_responder = SimulatedHumanResponder(self.variables, seed=self.seed)

        # Set up Claude client based on mode
        if self.mode == "mock":
            cache_mode = CacheMode.MOCK
            claude_client = CachedClaudeClient(
                cache_dir=self.trace_dir / "claude_cache",
                mode=cache_mode,
            )
        elif self.mode == "live":
            cache_mode = CacheMode.CAPTURE
            claude_client = CachedClaudeClient(
                cache_dir=self.trace_dir / "claude_cache",
                mode=cache_mode,
            )
        else:  # replay
            cache_mode = CacheMode.REPLAY
            claude_client = CachedClaudeClient(
                cache_dir=self.trace_dir / "claude_cache",
                mode=cache_mode,
            )

        # Create executor
        executor = SimulatedExecutor(
            project_path=self.project_path,
            dashboard=dashboard,
            variables=self.variables,
            seed=self.seed,
        )

        # Create runner config
        config = RunnerConfig(
            mode=RunnerMode.DEMO,  # Use demo mode for mock behavior
            project_path=self.project_path,
            max_cycles=self.max_cycles,
            demo_speed=100,  # Fast
            demo_delay_base=0,  # No delays
        )

        # Create dependencies
        deps = Dependencies(
            claude_client=claude_client,
            human_responder=self.human_responder,
            executor=executor,
            dashboard=dashboard,
        )

        # Create and run the cycle runner
        runner = CycleRunner(config, deps)
        runner.clear_run_state()  # Start fresh

        # Run cycles
        summary = await runner.run()

        # Calculate API cost estimate
        self.api_cost_estimate = claude_client.get_usage_stats().get("estimated_cost", 0.0)

        # Build outcome
        outcome = self._build_outcome(summary, runner)

        # Save outcome
        self.trace_manager.save_outcome(self.trace_id, outcome)

        # Save human decisions
        if self.human_responder:
            self.human_responder.save_decisions(self.trace_dir / "human_decisions")

        return outcome

    def _build_outcome(self, summary: dict, runner) -> ForecastOutcome:
        """Build ForecastOutcome from runner summary."""
        # Determine risk level
        success_rate = summary.get("success_rate", 0.5)
        if success_rate >= 0.8:
            risk_level = "low"
        elif success_rate >= 0.6:
            risk_level = "medium"
        else:
            risk_level = "high"

        # Time estimate based on cycles and days_per_cycle
        simulated_days = summary.get("simulated_days", 0)
        months = simulated_days / 30
        if months < 2:
            time_estimate = f"{int(simulated_days / 7)}-{int(simulated_days / 7) + 2} weeks"
        elif months < 12:
            time_estimate = f"{int(months)}-{int(months) + 2} months"
        else:
            time_estimate = f"{int(months / 12)}-{int(months / 12) + 1} years"

        return ForecastOutcome(
            target_reached=summary.get("target_reached", False),
            cycles_completed=summary.get("cycles_completed", 0),
            final_revenue=summary.get("final_revenue", 0),
            target_revenue=summary.get("target_revenue", 1_000_000),
            time_estimate=time_estimate,
            estimated_api_cost=self.api_cost_estimate,
            human_decisions_required=self.human_responder.decisions_made if self.human_responder else 0,
            risk_level=risk_level,
            success_rate=success_rate,
            progress_pct=summary.get("progress_pct", 0),
            total_hypotheses=summary.get("hypotheses_total", 0),
            total_tasks=summary.get("tasks_total", 0),
            total_failures=summary.get("failures", 0),
            simulated_days=simulated_days,
        )


# =============================================================================
# Scenario Runner (Monte Carlo)
# =============================================================================

class ScenarioRunner:
    """
    Runs multiple simulations with randomization for Monte Carlo analysis.

    Aggregates results to show distribution of outcomes.
    """

    def __init__(
        self,
        project_path: Path,
        variables: ForecastVariables,
        num_runs: int = 100,
        max_cycles: int = 50,
        trace_id: Optional[str] = None,  # Use cached responses from this trace
        on_run_complete: Optional[Callable[[int, ForecastOutcome], None]] = None,
    ):
        self.project_path = Path(project_path)
        self.variables = variables
        self.num_runs = num_runs
        self.max_cycles = max_cycles
        self.trace_id = trace_id
        self.on_run_complete = on_run_complete

    async def run(self) -> dict:
        """
        Run multiple simulations.

        Returns: Aggregated statistics
        """
        outcomes: list[ForecastOutcome] = []

        for i in range(self.num_runs):
            seed = random.randint(0, 1000000)

            # Randomize some variables for Monte Carlo
            varied_vars = ForecastVariables(
                human_quality=random.choice(["perfect", "good", "mediocre"]),
                human_delay_hours=random.choice([1, 4, 24]),
                human_selection=random.choice(["optimal", "random"]),
                market_response=random.choice(["optimistic", "realistic", "pessimistic"]),
                execution_variance=random.uniform(0, 0.3),
                chaos_level=random.choice(["none", "low"]),
            )

            runner = ForecastRunner(
                project_path=self.project_path,
                mode="mock" if not self.trace_id else "replay",
                variables=varied_vars,
                max_cycles=self.max_cycles,
                trace_id=self.trace_id,
                seed=seed,
            )

            try:
                outcome = await runner.run()
                outcomes.append(outcome)

                if self.on_run_complete:
                    self.on_run_complete(i + 1, outcome)
            except Exception as e:
                logger.warning(f"Run {i+1} failed: {e}")

        return self._aggregate_results(outcomes)

    def _aggregate_results(self, outcomes: list[ForecastOutcome]) -> dict:
        """Aggregate results from all runs."""
        if not outcomes:
            return {"error": "No successful runs"}

        # Success rate
        successes = sum(1 for o in outcomes if o.target_reached)
        success_rate = successes / len(outcomes)

        # Cycles distribution
        cycles = [o.cycles_completed for o in outcomes]
        avg_cycles = sum(cycles) / len(cycles)
        min_cycles = min(cycles)
        max_cycles = max(cycles)

        # Revenue distribution
        revenues = [o.final_revenue for o in outcomes]
        avg_revenue = sum(revenues) / len(revenues)

        # Time estimate (mode/median)
        times = [o.simulated_days for o in outcomes]
        median_days = sorted(times)[len(times) // 2]

        return {
            "num_runs": len(outcomes),
            "success_rate": success_rate,
            "successes": successes,
            "failures": len(outcomes) - successes,
            "cycles": {
                "average": avg_cycles,
                "min": min_cycles,
                "max": max_cycles,
            },
            "revenue": {
                "average": avg_revenue,
                "min": min(revenues),
                "max": max(revenues),
            },
            "time": {
                "median_days": median_days,
                "estimate": f"{int(median_days / 30)}-{int(median_days / 30) + 2} months",
            },
            "risk_distribution": {
                "low": sum(1 for o in outcomes if o.risk_level == "low"),
                "medium": sum(1 for o in outcomes if o.risk_level == "medium"),
                "high": sum(1 for o in outcomes if o.risk_level == "high"),
            },
        }
