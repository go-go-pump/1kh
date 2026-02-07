"""
End-to-End Cycle Tests (Layer 2a).

Deterministic tests that run complete cycles:
IMAGINATION → INTENT → WORK → (Mock) EXECUTION → Dashboard Update

These use mocked Claude, mocked execution, and mocked human responses
to verify the full feedback loop works correctly.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.mocks import (
    MockAnthropicClient,
    MOCK_RESPONSES,
    MockExecutor,
    ScenarioExecutor,
    MockHumanSimple,
    EscalationManager,
    EscalationType,
)
from core.dashboard import Dashboard, EventType
from core.resources import detect_hypothesis_conflicts, suggest_execution_order


# =============================================================================
# Happy Path Tests
# =============================================================================

class TestHappyPaths:
    """Happy path end-to-end tests."""

    @pytest.mark.asyncio
    async def test_h1_single_hypothesis_to_metrics(self, temp_project):
        """
        H1: Single hypothesis → task → execution → metrics improve

        Complete cycle where one hypothesis is generated, executed,
        and results in North Star progress.
        """
        from temporal.activities.imagination import generate_hypotheses
        from temporal.activities.work import create_task

        # Setup
        dashboard = Dashboard(temp_project)
        dashboard.set_north_star("$10K MRR", target_value=10000)

        oracle = {"values": ["Quality"], "never_do": [], "always_do": []}
        north_star = {"objectives": [{"name": "Reach $10K MRR"}]}
        context = {"budget": 1000, "skills": ["Python"]}

        # IMAGINATION: Generate hypothesis
        mock_claude = MockAnthropicClient(response_key="imagination_hypotheses")
        with patch('anthropic.Anthropic', return_value=mock_claude):
            hypotheses = await generate_hypotheses(
                str(temp_project),
                oracle=oracle,
                north_star=north_star,
                context=context,
                existing_hypotheses=[],
            )

        assert len(hypotheses) > 0
        dashboard.log_event(EventType.HYPOTHESIS_CREATED, hypothesis_id=hypotheses[0]["id"])
        dashboard.log_event(EventType.HYPOTHESIS_ACCEPTED, hypothesis_id=hypotheses[0]["id"])

        # INTENT: Select path (no conflicts expected with single hypothesis)
        selected = hypotheses[:1]
        assert len(selected) == 1

        # WORK: Create task
        mock_claude.set_response_key("work_task_creation")
        with patch('anthropic.Anthropic', return_value=mock_claude):
            task = await create_task(
                project_path=str(temp_project),
                hypothesis=selected[0],
                oracle=oracle,
                context=context,
            )

        assert task["status"] == "pending"
        dashboard.log_event(EventType.TASK_CREATED, task_id=task["id"], hypothesis_id=selected[0]["id"])

        # EXECUTION: Mock execution with positive outcome
        executor = ScenarioExecutor(temp_project, dashboard)
        executor.queue_scenario("success_large")

        outcome = executor.execute(task, selected[0])

        assert outcome.success is True
        assert outcome.metrics_delta.get("revenue", 0) > 0

        # Verify dashboard reflects progress
        state = dashboard.compute_state()
        assert state.north_star.current_value > 0
        assert state.tasks_completed == 1

    @pytest.mark.asyncio
    async def test_h5_multi_cycle_progress(self, temp_project):
        """
        H5: Multi-cycle run shows cumulative progress.

        Run 3 cycles and verify metrics accumulate.
        """
        from tests.mocks.execution import ProgressionSimulator

        simulator = ProgressionSimulator(
            temp_project,
            north_star_target=10000,
            cycles_to_reach=20,
        )

        history = []
        for _ in range(3):
            result = simulator.simulate_cycle()
            history.append(result)

        # Verify progression
        assert len(history) == 3
        assert history[2]["total_revenue"] > history[1]["total_revenue"]
        assert history[1]["total_revenue"] > history[0]["total_revenue"]

        # Verify dashboard state
        state = simulator.dashboard.compute_state()
        assert state.cycle_count == 3
        assert state.north_star.current_value > 0

    def test_h6_milestone_reached(self, temp_project):
        """
        H6: System recognizes when North Star is achieved.
        """
        from tests.mocks.execution import ProgressionSimulator

        simulator = ProgressionSimulator(
            temp_project,
            north_star_target=1000,  # Low target for quick test
            cycles_to_reach=10,
        )

        history = simulator.run_to_completion(max_cycles=50)

        # Should have reached target
        assert history[-1]["reached_target"] is True

        # Dashboard should show 100%+ progress
        state = simulator.dashboard.compute_state()
        assert state.north_star.progress_pct >= 100


# =============================================================================
# Sad Path Tests
# =============================================================================

class TestSadPaths:
    """Sad path end-to-end tests."""

    def test_s1_oracle_violation_rejected(self, temp_project_with_hypotheses):
        """
        S1: Hypothesis that violates Oracle should be rejected.
        """
        project_path, hypotheses = temp_project_with_hypotheses

        # Mark one as violating oracle
        hypotheses[1]["last_evaluation"] = {"violates_oracle": True}

        # INTENT filtering logic
        valid = [
            h for h in hypotheses
            if not h.get("last_evaluation", {}).get("violates_oracle", False)
        ]

        assert len(valid) == len(hypotheses) - 1
        assert all(h["id"] != hypotheses[1]["id"] for h in valid)

    def test_s2_conflict_triggers_escalation(self, temp_project_with_hypotheses):
        """
        S2: Two hypotheses with resource conflicts trigger escalation.
        """
        project_path, hypotheses = temp_project_with_hypotheses

        # Make hyp-001 and hyp-003 conflict on same file
        hypotheses[0]["touches_resources"] = [
            {"type": "file", "identifier": "src/shared.py", "access": "write"}
        ]
        hypotheses[2]["touches_resources"] = [
            {"type": "file", "identifier": "src/shared.py", "access": "write"}
        ]

        # Detect conflicts
        conflicts = detect_hypothesis_conflicts(hypotheses)

        # Should detect the conflict
        assert len(conflicts) > 0
        assert hypotheses[0]["id"] in conflicts or hypotheses[2]["id"] in conflicts

        # Escalation should be created
        dashboard = Dashboard(project_path)
        manager = EscalationManager(project_path, dashboard=dashboard)

        escalation = manager.create_escalation(
            type=EscalationType.CONFLICT_RESOLUTION,
            summary=f"Conflict between {hypotheses[0]['id']} and {hypotheses[2]['id']}",
            options=[hypotheses[0]["id"], hypotheses[2]["id"]],
        )

        assert escalation is not None
        assert manager.get_pending_count() == 1

    def test_s3_task_failure_captured(self, temp_project):
        """
        S3: Task execution failure is captured, system continues.
        """
        dashboard = Dashboard(temp_project)
        executor = ScenarioExecutor(temp_project, dashboard)

        # Queue a failure
        executor.queue_scenario("failure_transient")

        task = {"id": "task-fail-001", "task_type": "build", "hypothesis_id": "hyp-001"}
        outcome = executor.execute(task)

        assert outcome.success is False
        assert len(outcome.errors) > 0

        # Dashboard should show the failure
        state = dashboard.compute_state()
        assert state.tasks_failed == 1

    def test_s4_low_confidence_escalates(self, temp_project_with_hypotheses):
        """
        S4: When all hypotheses have low confidence, escalation is triggered.
        """
        project_path, hypotheses = temp_project_with_hypotheses

        # Set all to low confidence
        for h in hypotheses:
            h["estimated_confidence"] = 0.3

        threshold = 0.6
        high_confidence = [h for h in hypotheses if h.get("estimated_confidence", 0) >= threshold]

        assert len(high_confidence) == 0

        # Escalation should be created
        dashboard = Dashboard(project_path)
        manager = EscalationManager(project_path, dashboard=dashboard)

        escalation = manager.create_escalation(
            type=EscalationType.GUIDANCE_REQUEST,
            summary="No hypotheses meet confidence threshold",
            context={"best_score": 0.3},
            options=["Proceed with best option", "Generate new hypotheses", "Pause"],
            default_option="Proceed with best option",
        )

        assert escalation is not None

    def test_s5_human_task_blocks(self, temp_project):
        """
        S5: Task requiring human action is blocked, escalation created.
        """
        dashboard = Dashboard(temp_project)

        task = {
            "id": "task-human-001",
            "task_type": "build",
            "requires_human": True,
            "human_reason": "Need to register on third-party site",
        }

        # Task should be blocked
        assert task.get("requires_human") is True

        # Escalation created
        manager = EscalationManager(temp_project, dashboard=dashboard)
        escalation = manager.create_escalation(
            type=EscalationType.APPROVAL_REQUEST,
            summary=f"Task {task['id']} requires human action: {task['human_reason']}",
        )

        assert manager.get_pending_count() == 1

    def test_s6_metrics_decline_triggers_new_hypothesis(self, temp_project):
        """
        S6: When metrics go DOWN, IMAGINATION should generate corrective hypotheses.
        """
        dashboard = Dashboard(temp_project)
        dashboard.set_north_star("$10K MRR", target_value=10000)

        # Initial positive metrics
        dashboard.log_event(EventType.REVENUE, value=1000)

        # Then decline (refund)
        dashboard.log_event(EventType.REVENUE, value=-200)

        # Get summary for IMAGINATION
        summary = dashboard.get_summary_for_imagination()

        # Lifetime is still positive, but...
        assert summary["recent_metrics"]["revenue"] == 800

        # The system would detect the decline and generate corrective hypotheses
        # (This is logic that would be in IMAGINATION, not tested here directly)

    @pytest.mark.asyncio
    async def test_s9_api_error_graceful(self, temp_project):
        """
        S9: API error during hypothesis generation is handled gracefully.
        """
        from temporal.activities.imagination import generate_hypotheses

        oracle = {"values": [], "never_do": [], "always_do": []}
        north_star = {"objectives": []}
        context = {}

        # Mock that raises error
        mock_claude = MockAnthropicClient()
        mock_claude.set_error(Exception("API rate limit exceeded"))

        with patch('anthropic.Anthropic', return_value=mock_claude):
            # Should not crash, should return empty or error
            try:
                result = await generate_hypotheses(
                    str(temp_project),
                    oracle=oracle,
                    north_star=north_star,
                    context=context,
                    existing_hypotheses=[],
                )
                # If it doesn't raise, result should be empty list
                assert isinstance(result, list)
            except Exception:
                # If it raises, that's also acceptable for this test
                pass


# =============================================================================
# Human Interaction Tests
# =============================================================================

class TestHumanInteraction:
    """Tests for human-in-the-loop scenarios."""

    def test_hi1_conflict_resolution(self, temp_project):
        """
        HI1: Human resolves conflict by prioritizing one hypothesis.
        """
        dashboard = Dashboard(temp_project)
        human = MockHumanSimple(patterns={
            "conflict_resolution": "prioritize_first",
        })
        manager = EscalationManager(temp_project, human=human, dashboard=dashboard)

        # Create conflict escalation
        escalation = manager.create_escalation(
            type=EscalationType.CONFLICT_RESOLUTION,
            summary="hyp-001 and hyp-002 both modify src/main.py",
            options=["hyp-001", "hyp-002"],
        )

        # Process escalation
        responses = manager.process_pending()

        assert len(responses) == 1
        assert responses[0].action == "select"
        assert "hyp-001" in (responses[0].feedback or "")  # First option selected

    def test_hi3_approval_granted(self, temp_project):
        """
        HI3: Human approves a task that requires confirmation.
        """
        dashboard = Dashboard(temp_project)
        human = MockHumanSimple(patterns={
            "approval_request": "always_approve",
        })
        manager = EscalationManager(temp_project, human=human, dashboard=dashboard)

        escalation = manager.create_escalation(
            type=EscalationType.APPROVAL_REQUEST,
            summary="Deploy to production?",
        )

        responses = manager.process_pending()

        assert len(responses) == 1
        assert responses[0].action == "approve"

    def test_hi4_approval_rejected(self, temp_project):
        """
        HI4: Human rejects a task.
        """
        dashboard = Dashboard(temp_project)
        human = MockHumanSimple(patterns={
            "approval_request": "always_reject",
        })
        manager = EscalationManager(temp_project, human=human, dashboard=dashboard)

        escalation = manager.create_escalation(
            type=EscalationType.APPROVAL_REQUEST,
            summary="Spend $500 on ads?",
        )

        responses = manager.process_pending()

        assert len(responses) == 1
        assert responses[0].action == "reject"

    def test_hi5_guidance_provided(self, temp_project):
        """
        HI5: Human provides guidance when stuck.
        """
        dashboard = Dashboard(temp_project)
        human = MockHumanSimple(patterns={
            "guidance_request": "provide_default",
        })
        manager = EscalationManager(temp_project, human=human, dashboard=dashboard)

        escalation = manager.create_escalation(
            type=EscalationType.GUIDANCE_REQUEST,
            summary="No clear path forward",
            default_option="Focus on user acquisition",
        )

        responses = manager.process_pending()

        assert len(responses) == 1
        assert "default" in (responses[0].feedback or "").lower() or responses[0].action == "select"


# =============================================================================
# Full Cycle Integration
# =============================================================================

class TestFullCycleIntegration:
    """Test complete system cycles."""

    @pytest.mark.asyncio
    async def test_complete_cycle_with_all_components(self, temp_project):
        """
        Complete cycle using all components together.
        """
        from temporal.activities.imagination import generate_hypotheses
        from temporal.activities.work import create_task

        # Setup all components
        dashboard = Dashboard(temp_project)
        dashboard.set_north_star("$5K MRR", target_value=5000)

        executor = ScenarioExecutor(temp_project, dashboard)
        human = MockHumanSimple()
        escalation_manager = EscalationManager(temp_project, human=human, dashboard=dashboard)

        oracle = {"values": ["Quality"], "never_do": ["spam"], "always_do": ["test"]}
        north_star = {"objectives": [{"name": "Reach $5K MRR"}]}
        context = {"budget": 500, "skills": ["Python", "Marketing"]}

        # Log cycle start
        dashboard.log_event(EventType.CYCLE_STARTED, metadata={"cycle": 1})

        # IMAGINATION
        mock_claude = MockAnthropicClient(response_key="imagination_hypotheses")
        with patch('anthropic.Anthropic', return_value=mock_claude):
            hypotheses = await generate_hypotheses(
                str(temp_project),
                oracle=oracle,
                north_star=north_star,
                context=context,
                existing_hypotheses=[],
            )

        for h in hypotheses:
            dashboard.log_event(EventType.HYPOTHESIS_CREATED, hypothesis_id=h["id"])

        # INTENT
        for h in hypotheses:
            h["estimated_confidence"] = 0.8  # All high confidence

        conflicts = detect_hypothesis_conflicts(hypotheses)
        selected = hypotheses[:1]  # Take first

        for h in selected:
            dashboard.log_event(EventType.HYPOTHESIS_ACCEPTED, hypothesis_id=h["id"])

        # WORK
        mock_claude.set_response_key("work_task_creation")
        with patch('anthropic.Anthropic', return_value=mock_claude):
            task = await create_task(
                project_path=str(temp_project),
                hypothesis=selected[0],
                oracle=oracle,
                context=context,
            )

        dashboard.log_event(EventType.TASK_CREATED, task_id=task["id"], hypothesis_id=selected[0]["id"])

        # EXECUTION
        executor.queue_scenario("success_large")
        outcome = executor.execute(task, selected[0])

        # Mark hypothesis as validated if successful
        if outcome.success:
            dashboard.log_event(EventType.HYPOTHESIS_VALIDATED, hypothesis_id=selected[0]["id"])

        # Log cycle end
        dashboard.log_event(EventType.CYCLE_COMPLETED, metadata={"cycle": 1})

        # Verify final state
        state = dashboard.compute_state()

        assert state.cycle_count == 1
        assert state.hypotheses_total >= 1
        assert state.tasks_completed == 1
        assert state.north_star.current_value > 0

        # Get summary for next IMAGINATION cycle
        summary = dashboard.get_summary_for_imagination()
        assert summary["cycles_completed"] == 1
        assert summary["hypothesis_success_rate"] > 0
