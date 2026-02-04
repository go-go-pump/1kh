"""
Mock Execution Layer for testing.

Simulates task execution with realistic outcomes:
- Generates fake but plausible results
- Updates dashboard with metric events
- Can simulate success, failure, and partial completion
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Callable
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.dashboard import Dashboard, EventType


@dataclass
class ExecutionOutcome:
    """Result of mock execution."""
    success: bool
    result_text: str
    duration_seconds: float
    cost_dollars: float
    metrics_delta: dict[str, float] = field(default_factory=dict)
    files_created: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class MetricProgression:
    """Configuration for how metrics progress over time."""
    base_revenue_per_task: float = 100.0
    base_signups_per_task: float = 10.0
    base_page_views_per_task: float = 100.0
    conversion_rate: float = 0.02  # 2% of signups convert
    growth_multiplier: float = 1.1  # Each success grows 10%
    failure_rate: float = 0.2  # 20% of tasks fail
    noise: float = 0.3  # ±30% random variation


class MockExecutor:
    """
    Simulates task execution with configurable outcomes.

    Usage:
        executor = MockExecutor(project_path)
        executor.configure(
            success_rate=0.8,
            revenue_per_task=100,
        )
        outcome = executor.execute(task, hypothesis)
    """

    def __init__(
        self,
        project_path: Path,
        dashboard: Dashboard = None,
        progression: MetricProgression = None,
        seed: int = None,
    ):
        self.project_path = project_path
        self.dashboard = dashboard or Dashboard(project_path)
        self.progression = progression or MetricProgression()
        self.rng = random.Random(seed)  # Seeded for reproducibility
        self.execution_count = 0
        self.successes = 0

    def execute(
        self,
        task: dict,
        hypothesis: dict = None,
    ) -> ExecutionOutcome:
        """
        Execute a task (simulated).

        Returns ExecutionOutcome and logs events to dashboard.
        """
        self.execution_count += 1
        task_id = task.get("id", f"task-{self.execution_count}")
        hypothesis_id = task.get("hypothesis_id") or (hypothesis.get("id") if hypothesis else None)
        task_type = task.get("task_type", "build")

        # Log task started
        self.dashboard.log_event(
            EventType.TASK_STARTED,
            task_id=task_id,
            hypothesis_id=hypothesis_id,
            metadata={"task_type": task_type},
        )

        # Determine success/failure
        success = self.rng.random() > self.progression.failure_rate

        # Simulate duration (30s to 5min)
        duration = self.rng.uniform(30, 300)

        # Simulate cost ($0.01 to $0.50)
        cost = self.rng.uniform(0.01, 0.50)

        if success:
            self.successes += 1
            outcome = self._generate_success_outcome(
                task, hypothesis_id, task_id, duration, cost
            )
        else:
            outcome = self._generate_failure_outcome(
                task, hypothesis_id, task_id, duration, cost
            )

        return outcome

    def _generate_success_outcome(
        self,
        task: dict,
        hypothesis_id: str,
        task_id: str,
        duration: float,
        cost: float,
    ) -> ExecutionOutcome:
        """Generate a successful execution outcome."""
        task_type = task.get("task_type", "build")

        # Apply growth multiplier based on past successes
        multiplier = self.progression.growth_multiplier ** (self.successes - 1)

        # Calculate metrics with noise
        noise = 1 + self.rng.uniform(-self.progression.noise, self.progression.noise)

        metrics = {}

        if task_type in ("build", "deploy"):
            # Build tasks generate signups and page views
            signups = int(self.progression.base_signups_per_task * multiplier * noise)
            page_views = int(self.progression.base_page_views_per_task * multiplier * noise)
            conversions = int(signups * self.progression.conversion_rate)
            revenue = conversions * self.progression.base_revenue_per_task * noise

            metrics = {
                "signups": signups,
                "page_views": page_views,
                "conversions": conversions,
                "revenue": revenue,
            }

            # Log metric events
            self.dashboard.log_event(EventType.SIGNUP, value=signups, task_id=task_id, hypothesis_id=hypothesis_id)
            self.dashboard.log_event(EventType.PAGE_VIEW, value=page_views, task_id=task_id, hypothesis_id=hypothesis_id)
            self.dashboard.log_event(EventType.CONVERSION, value=conversions, task_id=task_id, hypothesis_id=hypothesis_id)
            self.dashboard.log_event(EventType.REVENUE, value=revenue, task_id=task_id, hypothesis_id=hypothesis_id)

        # Log task completed
        self.dashboard.log_event(
            EventType.TASK_COMPLETED,
            task_id=task_id,
            hypothesis_id=hypothesis_id,
            metadata={"metrics": metrics},
        )

        return ExecutionOutcome(
            success=True,
            result_text=f"Task {task_id} completed successfully. Generated {metrics.get('signups', 0)} signups.",
            duration_seconds=duration,
            cost_dollars=cost,
            metrics_delta=metrics,
            files_created=self._generate_fake_files(task),
        )

    def _generate_failure_outcome(
        self,
        task: dict,
        hypothesis_id: str,
        task_id: str,
        duration: float,
        cost: float,
    ) -> ExecutionOutcome:
        """Generate a failed execution outcome."""
        # Pick a random failure reason
        failure_reasons = [
            "API rate limit exceeded",
            "Dependency not available",
            "Build failed due to syntax error",
            "Timeout waiting for external service",
            "Permission denied",
            "Resource constraint exceeded",
        ]
        reason = self.rng.choice(failure_reasons)

        # Log task failed
        self.dashboard.log_event(
            EventType.TASK_FAILED,
            task_id=task_id,
            hypothesis_id=hypothesis_id,
            metadata={"error": reason},
        )

        return ExecutionOutcome(
            success=False,
            result_text=f"Task {task_id} failed: {reason}",
            duration_seconds=duration,
            cost_dollars=cost,
            metrics_delta={},
            errors=[reason],
        )

    def _generate_fake_files(self, task: dict) -> list[str]:
        """Generate fake file paths based on task."""
        task_type = task.get("task_type", "build")
        description = task.get("description", "").lower()

        files = []

        if "landing" in description:
            files.extend(["src/pages/landing.html", "src/styles/landing.css"])
        elif "auth" in description:
            files.extend(["src/auth/login.py", "src/auth/session.py"])
        elif "api" in description:
            files.extend(["src/api/routes.py", "src/api/handlers.py"])
        elif "payment" in description:
            files.extend(["src/payments/stripe.py", "src/payments/checkout.py"])
        else:
            files.append(f"src/{task_type}/output.py")

        return files


class ScenarioExecutor(MockExecutor):
    """
    Mock executor with predefined scenarios.

    Useful for deterministic testing of specific paths.

    Demo scenarios (set via scenario parameter):
      - missing-payment: Simulate no payment component
      - stalled: Metrics plateau after initial growth
      - pivot-needed: Repeated failures
      - vendor-choice: Needs vendor decision
    """

    def __init__(self, project_path: Path, dashboard: Dashboard = None, scenario: str = None):
        super().__init__(project_path, dashboard)
        self.scenario_queue: list[dict] = []
        self.demo_scenario = scenario  # For demo mode scenarios
        self._scenario_cycle = 0  # Track which cycle we're in

    def queue_outcome(
        self,
        success: bool,
        metrics: dict = None,
        error: str = None,
    ):
        """Queue a specific outcome for the next execution."""
        self.scenario_queue.append({
            "success": success,
            "metrics": metrics or {},
            "error": error,
        })

    def queue_scenario(self, scenario: str):
        """
        Queue a predefined scenario.

        Scenarios:
        - "success_small": Small metrics gain
        - "success_large": Large metrics gain (breakthrough)
        - "success_viral": Exponential growth
        - "partial_success": Some metrics, some issues
        - "failure_transient": Temporary failure, can retry
        - "failure_permanent": Permanent failure, abandon
        - "blocked" / "blocked_human": Needs human intervention
        """
        scenarios = {
            "success_small": {
                "success": True,
                "metrics": {"signups": 10, "revenue": 50},
            },
            "success_large": {
                "success": True,
                "metrics": {"signups": 100, "revenue": 500},
            },
            "success_viral": {
                "success": True,
                "metrics": {"signups": 1000, "revenue": 5000},
            },
            "partial_success": {
                "success": True,
                "metrics": {"signups": 25, "revenue": 150},
                "warning": "Partial completion - some subtasks pending",
            },
            "failure_transient": {
                "success": False,
                "error": "Timeout - can retry",
            },
            "failure_permanent": {
                "success": False,
                "error": "Service discontinued - abandon hypothesis",
            },
            "blocked": {
                "success": False,
                "error": "Requires human approval",
            },
            "blocked_human": {
                "success": False,
                "error": "Requires human approval",
            },
        }

        if scenario in scenarios:
            self.scenario_queue.append(scenarios[scenario])
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

    def execute(self, task: dict, hypothesis: dict = None) -> ExecutionOutcome:
        """Execute using queued scenario if available."""
        if self.scenario_queue:
            scenario = self.scenario_queue.pop(0)
            return self._execute_scenario(task, hypothesis, scenario)
        else:
            # Fall back to random
            return super().execute(task, hypothesis)

    def _execute_scenario(
        self,
        task: dict,
        hypothesis: dict,
        scenario: dict,
    ) -> ExecutionOutcome:
        """Execute a specific scenario."""
        self.execution_count += 1
        task_id = task.get("id", f"task-{self.execution_count}")
        hypothesis_id = task.get("hypothesis_id") or (hypothesis.get("id") if hypothesis else None)

        # Log start
        self.dashboard.log_event(
            EventType.TASK_STARTED,
            task_id=task_id,
            hypothesis_id=hypothesis_id,
        )

        if scenario["success"]:
            self.successes += 1
            metrics = scenario.get("metrics", {})

            # Log metrics
            for metric_type, value in metrics.items():
                event_type = getattr(EventType, metric_type.upper(), EventType.CUSTOM)
                self.dashboard.log_event(
                    event_type,
                    value=value,
                    task_id=task_id,
                    hypothesis_id=hypothesis_id,
                )

            self.dashboard.log_event(
                EventType.TASK_COMPLETED,
                task_id=task_id,
                hypothesis_id=hypothesis_id,
            )

            return ExecutionOutcome(
                success=True,
                result_text=f"Task {task_id} completed",
                duration_seconds=60,
                cost_dollars=0.10,
                metrics_delta=metrics,
            )
        else:
            error = scenario.get("error", "Unknown error")

            self.dashboard.log_event(
                EventType.TASK_FAILED,
                task_id=task_id,
                hypothesis_id=hypothesis_id,
                metadata={"error": error},
            )

            return ExecutionOutcome(
                success=False,
                result_text=f"Task {task_id} failed: {error}",
                duration_seconds=30,
                cost_dollars=0.05,
                errors=[error],
            )


class ProgressionSimulator:
    """
    Simulates progression toward North Star over multiple cycles.

    Useful for demos showing $0 → $1M in fast-forward.
    """

    def __init__(
        self,
        project_path: Path,
        north_star_target: float = 1000000,
        cycles_to_reach: int = 50,
    ):
        self.project_path = project_path
        self.dashboard = Dashboard(project_path)
        self.dashboard.set_north_star("$1M ARR", target_value=north_star_target)
        self.target = north_star_target
        self.cycles_to_reach = cycles_to_reach

        # Calculate growth needed per cycle (exponential)
        # If we want to reach target in N cycles, each cycle multiplies by target^(1/N)
        self.growth_rate = (north_star_target / 100) ** (1 / cycles_to_reach)

        self.current_revenue = 0
        self.current_cycle = 0

    def simulate_cycle(self) -> dict:
        """
        Simulate one cycle of the system.

        Returns summary of what happened.
        """
        self.current_cycle += 1

        # Log cycle start
        self.dashboard.log_event(
            EventType.CYCLE_STARTED,
            metadata={"cycle": self.current_cycle},
        )

        # Generate hypothesis
        hyp_id = f"hyp-cycle-{self.current_cycle:03d}"
        self.dashboard.log_event(
            EventType.HYPOTHESIS_CREATED,
            hypothesis_id=hyp_id,
        )
        self.dashboard.log_event(
            EventType.HYPOTHESIS_ACCEPTED,
            hypothesis_id=hyp_id,
        )

        # Create and execute task
        task_id = f"task-cycle-{self.current_cycle:03d}"
        self.dashboard.log_event(
            EventType.TASK_CREATED,
            task_id=task_id,
            hypothesis_id=hyp_id,
        )
        self.dashboard.log_event(
            EventType.TASK_STARTED,
            task_id=task_id,
            hypothesis_id=hyp_id,
        )

        # Calculate revenue for this cycle
        if self.current_revenue == 0:
            revenue_this_cycle = 100  # Starting point
        else:
            revenue_this_cycle = self.current_revenue * (self.growth_rate - 1)

        # Add some noise
        revenue_this_cycle *= random.uniform(0.8, 1.2)
        revenue_this_cycle = max(10, revenue_this_cycle)  # Minimum $10

        self.current_revenue += revenue_this_cycle

        # Log metrics
        signups = int(revenue_this_cycle / 10)  # Rough ratio
        self.dashboard.log_event(EventType.SIGNUP, value=signups, task_id=task_id, hypothesis_id=hyp_id)
        self.dashboard.log_event(EventType.REVENUE, value=revenue_this_cycle, task_id=task_id, hypothesis_id=hyp_id)

        # Complete task and hypothesis
        self.dashboard.log_event(EventType.TASK_COMPLETED, task_id=task_id, hypothesis_id=hyp_id)
        self.dashboard.log_event(EventType.HYPOTHESIS_VALIDATED, hypothesis_id=hyp_id)

        # Log cycle end
        self.dashboard.log_event(
            EventType.CYCLE_COMPLETED,
            metadata={"cycle": self.current_cycle},
        )

        # Return summary
        state = self.dashboard.compute_state()
        return {
            "cycle": self.current_cycle,
            "revenue_this_cycle": revenue_this_cycle,
            "total_revenue": self.current_revenue,
            "progress_pct": state.north_star.progress_pct,
            "reached_target": self.current_revenue >= self.target,
        }

    def run_to_completion(self, max_cycles: int = 100) -> list[dict]:
        """Run cycles until target reached or max cycles."""
        history = []
        while self.current_revenue < self.target and self.current_cycle < max_cycles:
            summary = self.simulate_cycle()
            history.append(summary)
            if summary["reached_target"]:
                break
        return history
