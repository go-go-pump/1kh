"""
INTENT Loop - Decision making and path selection.

This Temporal workflow handles:
1. Receiving hypotheses from IMAGINATION
2. Detecting conflicts between hypotheses (resource contention)
3. Deciding which paths to pursue and in what ORDER
4. Observing outcomes and adapting
5. Pruning approaches that aren't working
6. Escalating to human when confidence is low or conflicts need resolution

This is where strategic decisions are made.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from temporal.activities.foundation import read_oracle
    from core.resources import detect_hypothesis_conflicts, suggest_execution_order


@workflow.defn
class IntentLoopWorkflow:
    """
    The INTENT loop makes strategic decisions.

    Input:
        project_path: Path to the 1KH project
        hypotheses: Evaluated hypotheses from IMAGINATION

    Output:
        Selected paths to pursue, or escalation request
    """

    def __init__(self):
        self.selected_paths = []
        self.execution_order = []  # Ordered list of hypothesis IDs
        self.conflicts = {}  # Detected resource conflicts
        self.status = "initializing"
        self.escalation_pending = False
        self.escalation_reason = None

    @workflow.run
    async def run(
        self,
        project_path: str,
        hypotheses: list[dict],
        confidence_threshold: float = 0.6,
    ) -> dict:
        """
        Execute the intent loop.

        1. Review hypotheses from IMAGINATION
        2. Apply decision criteria
        3. Select paths to pursue OR escalate to human
        """
        self.status = "reviewing_hypotheses"

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
        )

        # Load Oracle to check against values
        oracle = await workflow.execute_activity(
            read_oracle,
            project_path,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # Filter hypotheses that violate Oracle
        valid_hypotheses = []
        for hyp in hypotheses:
            evaluation = hyp.get("last_evaluation", {})
            if evaluation.get("violates_oracle", False):
                workflow.logger.warning(
                    f"Rejecting hypothesis {hyp.get('id')} - violates Oracle"
                )
                continue
            valid_hypotheses.append(hyp)

        workflow.logger.info(
            f"Reviewing {len(valid_hypotheses)} valid hypotheses "
            f"(filtered {len(hypotheses) - len(valid_hypotheses)} Oracle violations)"
        )

        # Detect resource conflicts between hypotheses
        self.status = "detecting_conflicts"
        self.conflicts = detect_hypothesis_conflicts(valid_hypotheses)

        if self.conflicts:
            workflow.logger.info(
                f"Detected conflicts between {len(self.conflicts)} hypotheses"
            )
            # Annotate hypotheses with conflict info
            for hyp in valid_hypotheses:
                hyp_id = hyp.get("id")
                if hyp_id in self.conflicts:
                    hyp["_conflicts"] = self.conflicts[hyp_id]
                    hyp["_has_conflicts"] = True

        # Decision logic
        self.status = "making_decisions"

        high_confidence = [
            h for h in valid_hypotheses
            if h.get("estimated_confidence", 0) >= confidence_threshold
        ]

        if not high_confidence:
            # No confident paths - escalate to human
            self.status = "escalating"
            self.escalation_pending = True
            self.escalation_reason = (
                f"No hypotheses meet confidence threshold ({confidence_threshold}). "
                f"Best option: {valid_hypotheses[0].get('description', 'unknown') if valid_hypotheses else 'none'} "
                f"at {valid_hypotheses[0].get('estimated_confidence', 0):.0%} confidence."
                if valid_hypotheses else "No valid hypotheses generated."
            )

            return {
                "status": "escalation_needed",
                "reason": self.escalation_reason,
                "hypotheses": valid_hypotheses[:5],  # Show top 5 for human review
                "selected_paths": [],
            }

        # Select top paths (could be more sophisticated)
        # For now, take up to 3 highest confidence paths
        self.selected_paths = high_confidence[:3]

        # Determine execution order to avoid conflicts
        self.execution_order = suggest_execution_order(
            self.selected_paths,
            self.conflicts,
        )

        # Check if selected paths have unresolvable conflicts
        # (i.e., multiple paths that MUST modify the same resource)
        conflicting_selected = []
        for path in self.selected_paths:
            path_id = path.get("id")
            if path_id in self.conflicts:
                for conflict in self.conflicts[path_id]:
                    if conflict["with"] in [p.get("id") for p in self.selected_paths]:
                        conflicting_selected.append({
                            "path1": path_id,
                            "path2": conflict["with"],
                            "resources": conflict["resources"],
                        })

        if conflicting_selected:
            # Escalate for human decision on which path to prioritize
            self.status = "escalating"
            self.escalation_pending = True
            self.escalation_reason = (
                f"Selected paths have resource conflicts that require human decision. "
                f"Conflicts: {conflicting_selected}"
            )
            return {
                "status": "conflict_escalation",
                "reason": self.escalation_reason,
                "conflicts": conflicting_selected,
                "selected_paths": self.selected_paths,
                "suggested_order": self.execution_order,
            }

        self.status = "complete"

        return {
            "status": "paths_selected",
            "selected_paths": self.selected_paths,
            "execution_order": self.execution_order,
            "conflicts_detected": self.conflicts,
            "rejected_count": len(valid_hypotheses) - len(self.selected_paths),
            "next_step": "work_loop",
        }

    @workflow.query
    def get_status(self) -> str:
        """Query the current status."""
        return self.status

    @workflow.query
    def get_selected_paths(self) -> list:
        """Query the selected paths."""
        return self.selected_paths

    @workflow.query
    def get_escalation(self) -> dict:
        """Query if there's a pending escalation."""
        return {
            "pending": self.escalation_pending,
            "reason": self.escalation_reason,
        }

    @workflow.query
    def get_conflicts(self) -> dict:
        """Query detected conflicts between hypotheses."""
        return self.conflicts

    @workflow.query
    def get_execution_order(self) -> list:
        """Query the suggested execution order."""
        return self.execution_order

    @workflow.signal
    def human_decision(self, decision: dict):
        """
        Signal from human with their decision.

        decision = {
            "action": "approve" | "reject" | "modify",
            "selected_hypothesis_ids": ["hyp-001", ...],
            "feedback": "optional guidance"
        }
        """
        workflow.logger.info(f"Received human decision: {decision.get('action')}")
        self.escalation_pending = False

    @workflow.signal
    def abort_path(self, hypothesis_id: str, reason: str):
        """Signal to abort a selected path."""
        self.selected_paths = [
            p for p in self.selected_paths
            if p.get("id") != hypothesis_id
        ]
        workflow.logger.info(f"Aborted path {hypothesis_id}: {reason}")
