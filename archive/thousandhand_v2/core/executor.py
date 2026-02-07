"""
Task Executor - Executes tasks using Claude.

This is the real executor used in local and cloud modes.
For demo mode, use tests/mocks/execution.py instead.

IMPORTANT: In local mode, we use Claude for PLANNING but return
realistic mock metrics. Actual metrics would come from real execution
(e.g., deploying code, running campaigns) which we can't do yet.

METRICS ARE BASED ON SYSTEM STATE:
- No payment system = NO revenue (literally)
- No channel = minimal signups (organic only)
- Full system = realistic growth
"""
from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from core.dashboard import Dashboard, EventType
from core.conversation import ConversationManager
from core.runner import ExecutionResult
from core.system_state import SystemStateManager, ComponentStatus

logger = logging.getLogger("1kh.executor")


class ClaudeExecutor:
    """
    Executes tasks using Claude API for planning.

    In local mode:
    - Claude generates the execution PLAN
    - Metrics are simulated realistically (not parsed from Claude's estimates)

    In production:
    - Claude plans + orchestrates real execution
    - Metrics come from actual results
    """

    def __init__(
        self,
        project_path: Path,
        dashboard: Dashboard,
        conversation_manager: ConversationManager,
        claude_client: Any = None,
        simulate_metrics: bool = True,  # Use realistic mock metrics
        system_state: SystemStateManager = None,
    ):
        self.project_path = Path(project_path)
        self.dashboard = dashboard
        self.conversation_manager = conversation_manager
        self.claude_client = claude_client or self._get_client()
        self.simulate_metrics = simulate_metrics
        self.system_state = system_state or SystemStateManager(project_path)

        self.execution_count = 0

    def _get_client(self):
        """Get Claude client (lazy load)."""
        import anthropic
        return anthropic.Anthropic()

    def execute(self, task: dict, hypothesis: dict = None) -> ExecutionResult:
        """
        Execute a task and return result.

        Uses Claude to generate a plan, then:
        - In local mode: Returns simulated realistic metrics
        - In production: Would execute the plan and track real metrics
        """
        start_time = time.time()
        task_id = task.get("id", f"task-{self.execution_count}")
        hypothesis_id = hypothesis.get("id") if hypothesis else None

        self.execution_count += 1

        logger.info(f"Executing task {task_id}: {task.get('description', 'Unknown')}")

        try:
            # Get Claude to plan the execution
            result = self._execute_with_claude(task, hypothesis)

            duration = time.time() - start_time

            if result["success"]:
                # Use simulated metrics in local mode (not Claude's estimates)
                if self.simulate_metrics:
                    metrics = self._generate_realistic_metrics(task, hypothesis)
                else:
                    metrics = result.get("metrics", {})

                return ExecutionResult(
                    success=True,
                    task_id=task_id,
                    hypothesis_id=hypothesis_id,
                    result_text=result.get("output", "Task completed"),
                    duration_seconds=duration,
                    metrics_delta=metrics,
                    errors=[],
                )
            else:
                return ExecutionResult(
                    success=False,
                    task_id=task_id,
                    hypothesis_id=hypothesis_id,
                    result_text=result.get("error", "Task failed"),
                    duration_seconds=duration,
                    metrics_delta={},
                    errors=[result.get("error", "Unknown error")],
                )

        except Exception as e:
            logger.error(f"Task {task_id} failed with exception: {e}")
            return ExecutionResult(
                success=False,
                task_id=task_id,
                hypothesis_id=hypothesis_id,
                result_text=str(e),
                duration_seconds=time.time() - start_time,
                errors=[str(e)],
            )

    def _execute_with_claude(self, task: dict, hypothesis: dict) -> dict:
        """Execute task by sending to Claude for planning."""
        task_desc = task.get("description", "Unknown task")
        hyp_desc = hypothesis.get("description", "Unknown hypothesis") if hypothesis else "N/A"

        prompt = f"""You are the WORK loop of ThousandHand, an autonomous business-building system.

TASK: {task_desc}

HYPOTHESIS: {hyp_desc}

Please create an execution plan for this task:

1. Break it into 3-5 concrete steps
2. Identify what tools/resources are needed
3. Note any dependencies or blockers
4. Estimate time to complete

Format your response as:

PLAN:
1. [First step - be specific]
2. [Second step]
3. [Third step]
...

RESOURCES NEEDED:
- [tool/resource 1]
- [tool/resource 2]

BLOCKERS: [any dependencies or things that could block progress]

ESTIMATED TIME: [hours/days]

Note: Focus on the PLAN. Metrics will be tracked separately after execution.
"""

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            output = response.content[0].text

            return {
                "success": True,
                "output": output,
            }

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _generate_realistic_metrics(self, task: dict, hypothesis: dict) -> dict:
        """
        Generate realistic metrics for local/dev mode.

        These are NOT Claude's estimates - they're simulated results
        that represent what might happen if the task was actually executed.

        CRITICAL: Metrics depend on system state!
        - No payment system = NO revenue
        - No channel = minimal signups
        """
        # Check system state - this determines what's POSSIBLE
        state = self.system_state.load()
        can_generate_revenue, blockers = state.can_generate_revenue()
        has_channel = state.is_component_live("channel")
        has_payment = state.is_component_live("payment")

        task_type = task.get("task_type", "build")
        description = task.get("description", "").lower()

        # Update system state based on task (infer what was built)
        self.system_state.auto_update_from_task(task, success=True)

        # =====================================================================
        # REVENUE: Only possible if payment system is live
        # =====================================================================
        if not has_payment:
            # Literally cannot make money without payment system
            revenue = 0
        elif any(word in description for word in ["pricing", "payment", "checkout", "premium"]):
            # Payment/pricing tasks when system is ready
            revenue = random.randint(50, 300)
        elif any(word in description for word in ["marketing", "campaign", "social", "content"]):
            # Marketing tasks can drive sales if payment exists
            revenue = random.randint(10, 100) if has_channel else random.randint(0, 20)
        elif any(word in description for word in ["referral", "viral", "partnership"]):
            revenue = random.randint(20, 150)
        elif any(word in description for word in ["onboarding", "retention", "engagement"]):
            revenue = random.randint(10, 100)
        else:
            # Default: small revenue if system is complete
            revenue = random.randint(10, 75) if has_channel else random.randint(0, 20)

        # =====================================================================
        # SIGNUPS: Possible but limited without channel
        # =====================================================================
        if not has_channel:
            # Organic only - very limited
            signups = random.randint(0, 3)
        elif any(word in description for word in ["marketing", "campaign", "social", "content"]):
            signups = random.randint(10, 50)
        elif any(word in description for word in ["referral", "viral", "partnership"]):
            signups = random.randint(15, 75)
        elif any(word in description for word in ["youtube", "blog", "seo", "ads"]):
            signups = random.randint(20, 100)
        else:
            signups = random.randint(5, 25)

        # =====================================================================
        # Variance: Not every task succeeds equally
        # =====================================================================
        roll = random.random()
        if roll > 0.8:
            # Exceptional - 2-3x results
            multiplier = random.uniform(2.0, 3.0)
        elif roll < 0.2:
            # Poor results - 0.2-0.5x
            multiplier = random.uniform(0.2, 0.5)
        else:
            # Normal - slight variance
            multiplier = random.uniform(0.8, 1.2)

        final_signups = int(signups * multiplier)
        final_revenue = int(revenue * multiplier)

        # Log what's happening for transparency
        if not has_payment and revenue == 0:
            logger.debug(f"Revenue = $0 (no payment system live)")
        if not has_channel and signups < 5:
            logger.debug(f"Low signups (no marketing channel live)")

        return {
            "signups": final_signups,
            "revenue": final_revenue,
        }


class DryRunExecutor:
    """
    Executor for dry-run mode - logs what would happen but doesn't execute.
    """

    def __init__(self, console=None):
        self.console = console
        self.execution_count = 0

    def execute(self, task: dict, hypothesis: dict = None) -> ExecutionResult:
        """Log what would be executed without actually doing it."""
        task_id = task.get("id", f"task-{self.execution_count}")
        self.execution_count += 1

        if self.console:
            from rich.panel import Panel
            self.console.print(Panel(
                f"[bold]Would execute:[/bold]\n\n"
                f"Task: {task.get('description', 'Unknown')}\n"
                f"Hypothesis: {hypothesis.get('description', 'N/A') if hypothesis else 'N/A'}",
                title=f"[DRY RUN] {task_id}",
                border_style="dim",
            ))
        else:
            print(f"[DRY RUN] Would execute: {task.get('description', 'Unknown')}")

        return ExecutionResult(
            success=True,
            task_id=task_id,
            hypothesis_id=hypothesis.get("id") if hypothesis else None,
            result_text="Dry run - not executed",
            metrics_delta={},
        )
