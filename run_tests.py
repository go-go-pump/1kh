#!/usr/bin/env python3
"""
Simple test runner for Layer 2a tests.

This bypasses pytest to work in environments with limited Python stdlib.
"""
import sys
import os
import tempfile
import shutil
import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Track results
passed = 0
failed = 0
errors = []


def temp_project():
    """Create temporary project directory."""
    path = Path(tempfile.mkdtemp())
    (path / ".1kh").mkdir(parents=True, exist_ok=True)
    return path


def cleanup_project(path):
    """Clean up temporary project."""
    try:
        shutil.rmtree(path)
    except Exception:
        pass


def run_test(name, test_func):
    """Run a single test."""
    global passed, failed, errors
    proj = temp_project()
    try:
        test_func(proj)
        passed += 1
        print(f"  ✓ {name}")
    except AssertionError as e:
        failed += 1
        errors.append((name, str(e)))
        print(f"  ✗ {name}: {e}")
    except Exception as e:
        failed += 1
        errors.append((name, traceback.format_exc()))
        print(f"  ✗ {name}: {type(e).__name__}: {e}")
    finally:
        cleanup_project(proj)


# =============================================================================
# Dashboard Tests
# =============================================================================

def test_event_creation(proj):
    """Test Event creation and serialization."""
    from core.dashboard import Event, EventType

    event = Event.create(
        event_type=EventType.REVENUE,
        value=99.99,
        metadata={"source": "stripe"},
    )

    assert event.event_id.startswith("evt-")
    assert event.event_type == EventType.REVENUE
    assert event.value == 99.99
    assert event.metadata["source"] == "stripe"


def test_event_serialization(proj):
    """Test Event roundtrip serialization."""
    from core.dashboard import Event, EventType

    original = Event.create(
        event_type=EventType.SIGNUP,
        value=1,
        metadata={"email": "test@example.com"},
        hypothesis_id="hyp-001",
    )

    as_dict = original.to_dict()
    restored = Event.from_dict(as_dict)

    assert restored.event_id == original.event_id
    assert restored.event_type == original.event_type
    assert restored.value == original.value
    assert restored.hypothesis_id == original.hypothesis_id


def test_event_log_append_read(proj):
    """Test EventLog append and read."""
    from core.dashboard import EventLog, Event, EventType

    log = EventLog(proj)
    event = Event.create(EventType.REVENUE, value=100.0)
    log.append(event)

    events = log.read_all()
    assert len(events) == 1
    assert events[0].value == 100.0


def test_event_log_multiple(proj):
    """Test multiple events."""
    from core.dashboard import EventLog, Event, EventType

    log = EventLog(proj)
    events = [
        Event.create(EventType.REVENUE, value=10.0),
        Event.create(EventType.SIGNUP, value=1),
        Event.create(EventType.PAGE_VIEW, value=1),
    ]
    log.append_many(events)

    all_events = log.read_all()
    assert len(all_events) == 3


def test_dashboard_log_event(proj):
    """Test Dashboard log_event."""
    from core.dashboard import Dashboard, EventType

    dashboard = Dashboard(proj)
    dashboard.log_event(EventType.REVENUE, value=100)
    dashboard.log_event(EventType.SIGNUP, value=1)

    assert dashboard.event_log.count() == 2


def test_dashboard_compute_state(proj):
    """Test Dashboard state computation."""
    from core.dashboard import Dashboard, EventType

    dashboard = Dashboard(proj)
    dashboard.set_north_star("$1M ARR", target_value=1000000)

    dashboard.log_event(EventType.REVENUE, value=1000)
    dashboard.log_event(EventType.SIGNUP, value=1)
    dashboard.log_event(EventType.SIGNUP, value=1)

    state = dashboard.compute_state()

    assert state.north_star.current_value == 1000
    assert state.metrics_lifetime["revenue"] == 1000
    assert state.metrics_lifetime["signups"] == 2


def test_north_star_progress(proj):
    """Test North Star progress calculation."""
    from core.dashboard import NorthStarProgress

    ns = NorthStarProgress(
        objective="$1M ARR",
        target_value=1000000,
        current_value=100000,
    )

    assert ns.progress_pct == 10.0


def test_aggregation_sum(proj):
    """Test aggregate_sum function."""
    from core.dashboard import Event, EventType, aggregate_sum

    events = [
        Event.create(EventType.REVENUE, value=100),
        Event.create(EventType.REVENUE, value=50),
        Event.create(EventType.SIGNUP, value=1),
    ]

    total = aggregate_sum(events, EventType.REVENUE)
    assert total == 150


def test_aggregation_count(proj):
    """Test aggregate_count function."""
    from core.dashboard import Event, EventType, aggregate_count

    events = [
        Event.create(EventType.SIGNUP, value=1),
        Event.create(EventType.SIGNUP, value=1),
        Event.create(EventType.REVENUE, value=100),
    ]

    count = aggregate_count(events, EventType.SIGNUP)
    assert count == 2


# =============================================================================
# Mock Execution Tests
# =============================================================================

def test_mock_executor_success(proj):
    """Test MockExecutor with success scenario."""
    from core.dashboard import Dashboard
    from tests.mocks.execution import MockExecutor

    dashboard = Dashboard(proj)
    executor = MockExecutor(proj, dashboard, success_rate=1.0)

    task = {"id": "task-001", "task_type": "build"}
    hypothesis = {"id": "hyp-001"}

    outcome = executor.execute(task, hypothesis)
    assert outcome.success is True


def test_mock_executor_failure(proj):
    """Test MockExecutor with failure scenario."""
    from core.dashboard import Dashboard
    from tests.mocks.execution import MockExecutor

    dashboard = Dashboard(proj)
    executor = MockExecutor(proj, dashboard, success_rate=0.0)

    task = {"id": "task-001", "task_type": "build"}
    hypothesis = {"id": "hyp-001"}

    outcome = executor.execute(task, hypothesis)
    assert outcome.success is False


def test_scenario_executor(proj):
    """Test ScenarioExecutor with queued scenarios."""
    from core.dashboard import Dashboard
    from tests.mocks.execution import ScenarioExecutor

    dashboard = Dashboard(proj)
    executor = ScenarioExecutor(proj, dashboard)

    executor.queue_scenario("success_large")

    task = {"id": "task-001", "task_type": "build"}
    outcome = executor.execute(task)

    assert outcome.success is True
    assert outcome.metrics_delta.get("revenue", 0) > 0


def test_scenario_failure(proj):
    """Test ScenarioExecutor with failure scenario."""
    from core.dashboard import Dashboard
    from tests.mocks.execution import ScenarioExecutor

    dashboard = Dashboard(proj)
    executor = ScenarioExecutor(proj, dashboard)

    executor.queue_scenario("failure_transient")

    task = {"id": "task-001", "task_type": "build"}
    outcome = executor.execute(task)

    assert outcome.success is False
    assert len(outcome.errors) > 0


# =============================================================================
# Mock Human Tests
# =============================================================================

def test_mock_human_simple_approve(proj):
    """Test MockHumanSimple with always_approve pattern."""
    from tests.mocks.human import (
        MockHumanSimple,
        Escalation,
        EscalationType
    )

    human = MockHumanSimple(patterns={"approval_request": "always_approve"})

    escalation = Escalation(
        id="esc-001",
        type=EscalationType.APPROVAL_REQUEST,
        summary="Deploy to production?",
    )

    response = human.respond(escalation)
    assert response.action == "approve"


def test_mock_human_simple_reject(proj):
    """Test MockHumanSimple with always_reject pattern."""
    from tests.mocks.human import (
        MockHumanSimple,
        Escalation,
        EscalationType
    )

    human = MockHumanSimple(patterns={"approval_request": "always_reject"})

    escalation = Escalation(
        id="esc-001",
        type=EscalationType.APPROVAL_REQUEST,
        summary="Spend $500 on ads?",
    )

    response = human.respond(escalation)
    assert response.action == "reject"


def test_mock_human_conflict_resolution(proj):
    """Test MockHumanSimple with conflict resolution."""
    from tests.mocks.human import (
        MockHumanSimple,
        Escalation,
        EscalationType
    )

    human = MockHumanSimple(patterns={"conflict_resolution": "prioritize_first"})

    escalation = Escalation(
        id="esc-001",
        type=EscalationType.CONFLICT_RESOLUTION,
        summary="hyp-001 and hyp-002 conflict",
        options=["hyp-001", "hyp-002"],
    )

    response = human.respond(escalation)
    assert response.action == "select"
    assert "hyp-001" in (response.feedback or "")


def test_escalation_manager(proj):
    """Test EscalationManager creates and processes escalations."""
    from core.dashboard import Dashboard
    from tests.mocks.human import (
        MockHumanSimple,
        EscalationManager,
        EscalationType,
    )

    dashboard = Dashboard(proj)
    human = MockHumanSimple()
    manager = EscalationManager(proj, human=human, dashboard=dashboard)

    manager.create_escalation(
        type=EscalationType.APPROVAL_REQUEST,
        summary="Test escalation",
    )

    assert manager.get_pending_count() == 1

    responses = manager.process_pending()
    assert len(responses) == 1
    assert manager.get_pending_count() == 0


# =============================================================================
# Resource Conflict Tests
# =============================================================================

def test_no_conflict_different_files(proj):
    """Test no conflict when hypotheses touch different files."""
    from core.resources import detect_hypothesis_conflicts

    hypotheses = [
        {
            "id": "hyp-001",
            "touches_resources": [
                {"type": "file", "identifier": "src/a.py", "access": "write"}
            ]
        },
        {
            "id": "hyp-002",
            "touches_resources": [
                {"type": "file", "identifier": "src/b.py", "access": "write"}
            ]
        },
    ]

    conflicts = detect_hypothesis_conflicts(hypotheses)
    assert len(conflicts) == 0


def test_conflict_same_file(proj):
    """Test conflict when hypotheses touch same file."""
    from core.resources import detect_hypothesis_conflicts

    hypotheses = [
        {
            "id": "hyp-001",
            "touches_resources": [
                {"type": "file", "identifier": "src/shared.py", "access": "write"}
            ]
        },
        {
            "id": "hyp-002",
            "touches_resources": [
                {"type": "file", "identifier": "src/shared.py", "access": "write"}
            ]
        },
    ]

    conflicts = detect_hypothesis_conflicts(hypotheses)
    assert len(conflicts) > 0


def test_no_conflict_read_operations(proj):
    """Test no conflict for read-only operations."""
    from core.resources import detect_hypothesis_conflicts

    hypotheses = [
        {
            "id": "hyp-001",
            "touches_resources": [
                {"type": "file", "identifier": "src/shared.py", "access": "read"}
            ]
        },
        {
            "id": "hyp-002",
            "touches_resources": [
                {"type": "file", "identifier": "src/shared.py", "access": "read"}
            ]
        },
    ]

    conflicts = detect_hypothesis_conflicts(hypotheses)
    assert len(conflicts) == 0


# =============================================================================
# Progression Simulator Tests
# =============================================================================

def test_progression_simulator(proj):
    """Test ProgressionSimulator runs cycles."""
    from tests.mocks.execution import ProgressionSimulator

    simulator = ProgressionSimulator(
        proj,
        north_star_target=10000,
        cycles_to_reach=20,
    )

    history = []
    for _ in range(3):
        result = simulator.simulate_cycle()
        history.append(result)

    assert len(history) == 3
    # Revenue should accumulate
    assert history[2]["total_revenue"] > history[0]["total_revenue"]


def test_progression_to_target(proj):
    """Test ProgressionSimulator reaches target."""
    from tests.mocks.execution import ProgressionSimulator

    simulator = ProgressionSimulator(
        proj,
        north_star_target=1000,  # Low target
        cycles_to_reach=10,
    )

    history = simulator.run_to_completion(max_cycles=50)

    assert history[-1]["reached_target"] is True


# =============================================================================
# Main Runner
# =============================================================================

def main():
    print("\n" + "=" * 60)
    print("  ThousandHand (1KH) - Layer 2a Test Suite")
    print("=" * 60)

    # Dashboard Tests
    print("\n📊 Dashboard Tests")
    run_test("Event creation", test_event_creation)
    run_test("Event serialization", test_event_serialization)
    run_test("Event log append/read", test_event_log_append_read)
    run_test("Event log multiple events", test_event_log_multiple)
    run_test("Dashboard log_event", test_dashboard_log_event)
    run_test("Dashboard compute_state", test_dashboard_compute_state)
    run_test("North Star progress", test_north_star_progress)
    run_test("Aggregation sum", test_aggregation_sum)
    run_test("Aggregation count", test_aggregation_count)

    # Mock Execution Tests
    print("\n🔧 Mock Execution Tests")
    run_test("Mock executor success", test_mock_executor_success)
    run_test("Mock executor failure", test_mock_executor_failure)
    run_test("Scenario executor", test_scenario_executor)
    run_test("Scenario failure", test_scenario_failure)

    # Mock Human Tests
    print("\n👤 Mock Human Tests")
    run_test("Mock human approve", test_mock_human_simple_approve)
    run_test("Mock human reject", test_mock_human_simple_reject)
    run_test("Mock human conflict resolution", test_mock_human_conflict_resolution)
    run_test("Escalation manager", test_escalation_manager)

    # Resource Conflict Tests
    print("\n🔒 Resource Conflict Tests")
    run_test("No conflict different files", test_no_conflict_different_files)
    run_test("Conflict same file", test_conflict_same_file)
    run_test("No conflict read operations", test_no_conflict_read_operations)

    # Progression Tests
    print("\n📈 Progression Tests")
    run_test("Progression simulator", test_progression_simulator)
    run_test("Progression to target", test_progression_to_target)

    # Summary
    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if errors:
        print("\nErrors:")
        for name, err in errors:
            print(f"\n  {name}:")
            for line in err.split("\n")[:5]:
                print(f"    {line}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
