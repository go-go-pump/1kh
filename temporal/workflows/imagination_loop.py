"""
IMAGINATION Loop - Generate and evaluate hypotheses.

This Temporal workflow handles:
1. Reading the foundation documents (Oracle, North Star, Context)
2. Generating hypothesis candidates using Claude
3. Estimating confidence/feasibility for each
4. Recommending paths or escalating to human for decision

Triggers:
- First run after ceremony (seeds exist but no hypotheses evaluated)
- INTENT requests new hypotheses
- Human provides new Seeds
- Periodic refresh (re-evaluate existing hypotheses)
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activity stubs - these get executed by the worker
with workflow.unsafe.imports_passed_through():
    from temporal.activities.foundation import (
        read_oracle,
        read_north_star,
        read_context,
        read_seeds,
    )
    from temporal.activities.imagination import (
        generate_hypotheses,
        estimate_confidence,
    )


@workflow.defn
class ImaginationLoopWorkflow:
    """
    The IMAGINATION loop generates and evaluates hypotheses.

    Input:
        project_path: Path to the 1KH project

    Output:
        List of evaluated hypotheses with confidence scores
    """

    def __init__(self):
        self.hypotheses = []
        self.status = "initializing"

    @workflow.run
    async def run(self, project_path: str, max_hypotheses: int = 10) -> dict:
        """
        Execute the imagination loop.

        1. Load foundation documents
        2. Generate hypotheses from seeds + context
        3. Evaluate each hypothesis
        4. Return ranked hypotheses for INTENT to decide on
        """
        self.status = "loading_foundation"

        # Configure retry policy for activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
        )

        # Step 1: Load foundation documents
        oracle = await workflow.execute_activity(
            read_oracle,
            project_path,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        north_star = await workflow.execute_activity(
            read_north_star,
            project_path,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        context = await workflow.execute_activity(
            read_context,
            project_path,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        seeds = await workflow.execute_activity(
            read_seeds,
            project_path,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        workflow.logger.info(
            f"Loaded foundation: {len(oracle.get('values', []))} values, "
            f"{len(north_star.get('objectives', []))} objectives, "
            f"{len(seeds)} seeds"
        )

        # Step 2: Generate hypotheses
        self.status = "generating_hypotheses"

        new_hypotheses = await workflow.execute_activity(
            generate_hypotheses,
            args=[project_path, oracle, north_star, context, self.hypotheses, max_hypotheses],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
            heartbeat_timeout=timedelta(minutes=2),
        )

        workflow.logger.info(f"Generated {len(new_hypotheses)} new hypotheses")

        # Step 3: Evaluate each hypothesis
        self.status = "evaluating_hypotheses"

        evaluated = []
        for hyp in new_hypotheses:
            updated = await workflow.execute_activity(
                estimate_confidence,
                args=[project_path, hyp, oracle, context],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
                heartbeat_timeout=timedelta(minutes=1),
            )
            evaluated.append(updated)

        # Sort by confidence
        evaluated.sort(
            key=lambda h: h.get("estimated_confidence", 0),
            reverse=True
        )

        self.hypotheses = evaluated
        self.status = "complete"

        # Return results for INTENT loop
        return {
            "status": "complete",
            "hypotheses": evaluated,
            "oracle_values": oracle.get("values", []),
            "objectives": north_star.get("objectives", []),
            "top_hypothesis": evaluated[0] if evaluated else None,
        }

    @workflow.query
    def get_status(self) -> str:
        """Query the current status of the imagination loop."""
        return self.status

    @workflow.query
    def get_hypotheses(self) -> list:
        """Query the current list of hypotheses."""
        return self.hypotheses

    @workflow.signal
    def add_seed(self, seed: dict):
        """Signal to add a new seed for consideration."""
        # This would trigger re-evaluation
        workflow.logger.info(f"Received new seed: {seed.get('description', 'unknown')}")
