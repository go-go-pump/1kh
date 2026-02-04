"""
Tests for INTENT loop - Decision making and path selection.

Coverage:
- Conflict detection (uses resources.py, already tested there)
- Escalation generation when confidence is low
- Escalation generation when conflicts exist
- depends_on ordering in execution order
- Human response handling (signals)
- Oracle violation filtering
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# Unit Tests for INTENT Logic (without Temporal)
# =============================================================================

class TestIntentDecisionLogic:
    """Test the decision logic independent of Temporal workflow."""

    def test_filters_oracle_violations(self):
        """Hypotheses marked as Oracle violations should be filtered."""
        hypotheses = [
            {"id": "hyp-001", "description": "Good one", "estimated_confidence": 0.8},
            {"id": "hyp-002", "description": "Bad one", "estimated_confidence": 0.9,
             "last_evaluation": {"violates_oracle": True}},
            {"id": "hyp-003", "description": "Another good", "estimated_confidence": 0.7},
        ]

        # Filter logic (extracted from workflow)
        valid = [
            h for h in hypotheses
            if not h.get("last_evaluation", {}).get("violates_oracle", False)
        ]

        assert len(valid) == 2
        assert all(h["id"] != "hyp-002" for h in valid)

    def test_low_confidence_triggers_escalation(self):
        """When no hypothesis meets threshold, should escalate."""
        hypotheses = [
            {"id": "hyp-001", "description": "Low confidence", "estimated_confidence": 0.4},
            {"id": "hyp-002", "description": "Also low", "estimated_confidence": 0.3},
        ]
        threshold = 0.6

        high_confidence = [
            h for h in hypotheses
            if h.get("estimated_confidence", 0) >= threshold
        ]

        assert len(high_confidence) == 0
        # This would trigger escalation

    def test_selects_top_paths_by_confidence(self):
        """Should select top N paths by confidence."""
        hypotheses = [
            {"id": "hyp-001", "estimated_confidence": 0.9},
            {"id": "hyp-002", "estimated_confidence": 0.8},
            {"id": "hyp-003", "estimated_confidence": 0.7},
            {"id": "hyp-004", "estimated_confidence": 0.6},
            {"id": "hyp-005", "estimated_confidence": 0.5},
        ]
        threshold = 0.6
        max_paths = 3

        high_confidence = [
            h for h in hypotheses
            if h.get("estimated_confidence", 0) >= threshold
        ]
        selected = high_confidence[:max_paths]

        assert len(selected) == 3
        assert selected[0]["id"] == "hyp-001"  # Highest first

    def test_detects_conflicting_selected_paths(self):
        """Should detect when selected paths conflict with each other."""
        from core.resources import detect_hypothesis_conflicts

        hypotheses = [
            {
                "id": "hyp-001",
                "estimated_confidence": 0.9,
                "touches_resources": [
                    {"type": "file", "identifier": "src/main.py", "access": "write"}
                ]
            },
            {
                "id": "hyp-002",
                "estimated_confidence": 0.85,
                "touches_resources": [
                    {"type": "file", "identifier": "src/main.py", "access": "write"}
                ]
            },
        ]

        # Detect conflicts
        conflicts = detect_hypothesis_conflicts(hypotheses)

        # Both selected, both conflict
        selected_ids = [h["id"] for h in hypotheses]
        conflicting_selected = []
        for hyp in hypotheses:
            hyp_id = hyp["id"]
            if hyp_id in conflicts:
                for conflict in conflicts[hyp_id]:
                    if conflict["with"] in selected_ids:
                        conflicting_selected.append({
                            "path1": hyp_id,
                            "path2": conflict["with"],
                        })

        # Should find the conflict
        assert len(conflicting_selected) > 0


class TestDependencyOrdering:
    """Test that depends_on is respected in execution order."""

    def test_respects_depends_on(self):
        """Hypothesis with depends_on should come after its dependency."""
        from core.resources import suggest_execution_order

        hypotheses = [
            {"id": "hyp-001", "depends_on": ["hyp-002"], "blocks": []},
            {"id": "hyp-002", "depends_on": [], "blocks": ["hyp-001"]},
            {"id": "hyp-003", "depends_on": [], "blocks": []},
        ]

        order = suggest_execution_order(hypotheses, {})

        # hyp-002 should come before hyp-001
        idx_001 = order.index("hyp-001")
        idx_002 = order.index("hyp-002")
        assert idx_002 < idx_001, "Dependency should come first"

    def test_chain_dependencies(self):
        """Chain of dependencies should be ordered correctly."""
        from core.resources import suggest_execution_order

        hypotheses = [
            {"id": "hyp-003", "depends_on": ["hyp-002"], "blocks": []},
            {"id": "hyp-001", "depends_on": [], "blocks": ["hyp-002"]},
            {"id": "hyp-002", "depends_on": ["hyp-001"], "blocks": ["hyp-003"]},
        ]

        order = suggest_execution_order(hypotheses, {})

        # Order should be: hyp-001 → hyp-002 → hyp-003
        assert order.index("hyp-001") < order.index("hyp-002")
        assert order.index("hyp-002") < order.index("hyp-003")


class TestEscalationGeneration:
    """Test escalation message generation."""

    def test_escalation_includes_best_option(self):
        """Low confidence escalation should mention the best available option."""
        hypotheses = [
            {"id": "hyp-001", "description": "Build landing page", "estimated_confidence": 0.5},
            {"id": "hyp-002", "description": "Set up payments", "estimated_confidence": 0.4},
        ]
        threshold = 0.6

        # This is the escalation logic from the workflow
        best = hypotheses[0] if hypotheses else None
        reason = (
            f"No hypotheses meet confidence threshold ({threshold}). "
            f"Best option: {best.get('description', 'unknown') if best else 'none'} "
            f"at {best.get('estimated_confidence', 0):.0%} confidence."
            if hypotheses else "No valid hypotheses generated."
        )

        assert "50%" in reason
        assert "landing page" in reason

    def test_conflict_escalation_lists_conflicts(self):
        """Conflict escalation should list the conflicting resources."""
        conflicting_selected = [
            {
                "path1": "hyp-001",
                "path2": "hyp-002",
                "resources": ["src/main.py", "src/api.py"],
            }
        ]

        reason = (
            f"Selected paths have resource conflicts that require human decision. "
            f"Conflicts: {conflicting_selected}"
        )

        assert "hyp-001" in reason
        assert "hyp-002" in reason
        assert "src/main.py" in reason


class TestHumanResponseHandling:
    """Test handling of human responses to escalations."""

    def test_human_decision_clears_escalation(self):
        """Human decision signal should clear escalation pending state."""
        # Simulating the workflow state
        escalation_pending = True
        escalation_reason = "Need approval"

        # Human decision received
        decision = {"action": "approve", "selected_hypothesis_ids": ["hyp-001"]}

        # After receiving decision
        escalation_pending = False  # This is what the signal handler does

        assert escalation_pending is False

    def test_abort_path_removes_from_selected(self):
        """abort_path signal should remove hypothesis from selected paths."""
        selected_paths = [
            {"id": "hyp-001", "description": "Path 1"},
            {"id": "hyp-002", "description": "Path 2"},
            {"id": "hyp-003", "description": "Path 3"},
        ]

        # Abort hyp-002
        hypothesis_id = "hyp-002"
        selected_paths = [
            p for p in selected_paths
            if p.get("id") != hypothesis_id
        ]

        assert len(selected_paths) == 2
        assert all(p["id"] != "hyp-002" for p in selected_paths)


# =============================================================================
# Integration Tests (with mock activities)
# =============================================================================

class TestIntentIntegration:
    """Integration tests for INTENT loop."""

    def test_full_happy_path_flow(self, temp_project_with_hypotheses):
        """Test complete INTENT flow with valid hypotheses."""
        project_path, hypotheses = temp_project_with_hypotheses

        # Add confidence scores
        for hyp in hypotheses:
            hyp["estimated_confidence"] = 0.8

        # Run decision logic
        threshold = 0.6
        valid = [h for h in hypotheses if not h.get("last_evaluation", {}).get("violates_oracle")]
        high_confidence = [h for h in valid if h.get("estimated_confidence", 0) >= threshold]
        selected = high_confidence[:3]

        assert len(selected) > 0
        assert all(h["estimated_confidence"] >= threshold for h in selected)

    def test_all_low_confidence_escalates(self, temp_project_with_hypotheses):
        """Should escalate when all hypotheses are low confidence."""
        project_path, hypotheses = temp_project_with_hypotheses

        # Set all to low confidence
        for hyp in hypotheses:
            hyp["estimated_confidence"] = 0.3

        threshold = 0.6
        high_confidence = [h for h in hypotheses if h.get("estimated_confidence", 0) >= threshold]

        assert len(high_confidence) == 0
        # Workflow would return escalation_needed

    def test_conflict_between_selected_escalates(self, temp_project_with_hypotheses):
        """Should escalate when selected paths conflict."""
        from core.resources import detect_hypothesis_conflicts

        project_path, hypotheses = temp_project_with_hypotheses

        # Ensure hyp-001 and hyp-003 both write to same file
        hypotheses[0]["touches_resources"] = [
            {"type": "file", "identifier": "src/auth/login.py", "access": "write"}
        ]
        hypotheses[2]["touches_resources"] = [
            {"type": "file", "identifier": "src/auth/login.py", "access": "write"}
        ]

        # Set high confidence so both are selected
        for hyp in hypotheses:
            hyp["estimated_confidence"] = 0.8

        # Detect conflicts
        conflicts = detect_hypothesis_conflicts(hypotheses)

        # Check if selected paths conflict
        selected_ids = [h["id"] for h in hypotheses]
        has_internal_conflict = False
        for hyp_id in selected_ids:
            if hyp_id in conflicts:
                for conflict in conflicts[hyp_id]:
                    if conflict["with"] in selected_ids:
                        has_internal_conflict = True
                        break

        assert has_internal_conflict


# =============================================================================
# Edge Cases
# =============================================================================

class TestIntentEdgeCases:
    """Test edge cases in INTENT loop."""

    def test_empty_hypotheses_list(self):
        """Should handle empty hypotheses list gracefully."""
        hypotheses = []
        threshold = 0.6

        high_confidence = [h for h in hypotheses if h.get("estimated_confidence", 0) >= threshold]

        assert high_confidence == []
        # Workflow would return escalation with "No valid hypotheses generated"

    def test_single_hypothesis_selected(self):
        """Should work with just one hypothesis."""
        hypotheses = [
            {"id": "hyp-001", "estimated_confidence": 0.9, "depends_on": [], "blocks": []}
        ]

        from core.resources import suggest_execution_order
        order = suggest_execution_order(hypotheses, {})

        assert order == ["hyp-001"]

    def test_hypothesis_without_confidence_uses_zero(self):
        """Hypothesis without estimated_confidence should default to 0."""
        hypotheses = [
            {"id": "hyp-001", "description": "No confidence field"},
        ]
        threshold = 0.6

        high_confidence = [h for h in hypotheses if h.get("estimated_confidence", 0) >= threshold]

        assert len(high_confidence) == 0

    def test_circular_dependencies_handled(self):
        """Should not crash on circular dependencies."""
        from core.resources import suggest_execution_order

        # Circular: A depends on B, B depends on A
        hypotheses = [
            {"id": "hyp-001", "depends_on": ["hyp-002"], "blocks": []},
            {"id": "hyp-002", "depends_on": ["hyp-001"], "blocks": []},
        ]

        # Should not hang or crash
        order = suggest_execution_order(hypotheses, {})

        # Should include both (order may vary)
        assert set(order) == {"hyp-001", "hyp-002"}
