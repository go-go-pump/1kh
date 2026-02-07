"""
Tests for Dashboard and Event Log.

Coverage:
- Event creation and serialization
- Event log append and read operations
- Aggregation functions (sum, count, by time)
- Dashboard state computation
- North Star progress tracking
- Metrics filtering by time
"""
import pytest
from pathlib import Path
from datetime import datetime, timedelta
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.dashboard import (
    Event,
    EventType,
    EventLog,
    Dashboard,
    DashboardState,
    NorthStarProgress,
    aggregate_sum,
    aggregate_count,
    aggregate_by_time,
)


# =============================================================================
# Event Tests
# =============================================================================

class TestEvent:
    """Test Event dataclass."""

    def test_create_event(self):
        """Should create event with factory method."""
        event = Event.create(
            event_type=EventType.REVENUE,
            value=99.99,
            metadata={"source": "stripe"},
        )

        assert event.event_id.startswith("evt-")
        assert event.event_type == EventType.REVENUE
        assert event.value == 99.99
        assert event.metadata["source"] == "stripe"

    def test_event_serialization_roundtrip(self):
        """Event should serialize and deserialize correctly."""
        original = Event.create(
            event_type=EventType.SIGNUP,
            value=1,
            metadata={"email": "test@example.com"},
            hypothesis_id="hyp-001",
            task_id="task-001",
        )

        as_dict = original.to_dict()
        restored = Event.from_dict(as_dict)

        assert restored.event_id == original.event_id
        assert restored.event_type == original.event_type
        assert restored.value == original.value
        assert restored.metadata == original.metadata
        assert restored.hypothesis_id == original.hypothesis_id

    def test_event_source_defaults_to_system(self):
        """Source should default to 'system'."""
        event = Event.create(event_type=EventType.TASK_COMPLETED, value=1)
        assert event.source == "system"


# =============================================================================
# Event Log Tests
# =============================================================================

class TestEventLog:
    """Test EventLog append-only storage."""

    def test_append_and_read(self, temp_project):
        """Should append event and read it back."""
        log = EventLog(temp_project)

        event = Event.create(EventType.REVENUE, value=100.0)
        log.append(event)

        events = log.read_all()
        assert len(events) == 1
        assert events[0].value == 100.0

    def test_append_many(self, temp_project):
        """Should append multiple events efficiently."""
        log = EventLog(temp_project)

        events = [
            Event.create(EventType.REVENUE, value=10.0),
            Event.create(EventType.SIGNUP, value=1),
            Event.create(EventType.PAGE_VIEW, value=1),
        ]
        log.append_many(events)

        all_events = log.read_all()
        assert len(all_events) == 3

    def test_read_since(self, temp_project):
        """Should filter events by timestamp."""
        log = EventLog(temp_project)

        # Create events with different timestamps
        old_event = Event.create(EventType.REVENUE, value=50.0)
        old_event.timestamp = datetime.utcnow() - timedelta(hours=48)

        new_event = Event.create(EventType.REVENUE, value=100.0)

        log.append(old_event)
        log.append(new_event)

        # Read since 24h ago
        since = datetime.utcnow() - timedelta(hours=24)
        recent = log.read_since(since)

        assert len(recent) == 1
        assert recent[0].value == 100.0

    def test_read_by_type(self, temp_project):
        """Should filter events by type."""
        log = EventLog(temp_project)

        log.append(Event.create(EventType.REVENUE, value=100))
        log.append(Event.create(EventType.SIGNUP, value=1))
        log.append(Event.create(EventType.REVENUE, value=50))

        revenue_events = log.read_by_type(EventType.REVENUE)
        assert len(revenue_events) == 2

    def test_read_by_hypothesis(self, temp_project):
        """Should filter events by hypothesis ID."""
        log = EventLog(temp_project)

        log.append(Event.create(EventType.TASK_COMPLETED, hypothesis_id="hyp-001"))
        log.append(Event.create(EventType.TASK_COMPLETED, hypothesis_id="hyp-002"))
        log.append(Event.create(EventType.TASK_FAILED, hypothesis_id="hyp-001"))

        hyp_events = log.read_by_hypothesis("hyp-001")
        assert len(hyp_events) == 2

    def test_clear(self, temp_project):
        """Should clear all events."""
        log = EventLog(temp_project)

        log.append(Event.create(EventType.REVENUE, value=100))
        log.append(Event.create(EventType.SIGNUP, value=1))

        log.clear()

        assert log.count() == 0

    def test_handles_malformed_lines(self, temp_project):
        """Should skip malformed JSON lines gracefully."""
        log = EventLog(temp_project)

        # Write a valid event
        log.append(Event.create(EventType.REVENUE, value=100))

        # Manually append malformed line
        with open(log.log_file, "a") as f:
            f.write("not valid json\n")

        # Write another valid event
        log.append(Event.create(EventType.SIGNUP, value=1))

        # Should read 2 valid events, skip the bad one
        events = log.read_all()
        assert len(events) == 2


# =============================================================================
# Aggregation Tests
# =============================================================================

class TestAggregation:
    """Test aggregation functions."""

    def test_aggregate_sum(self):
        """Should sum values for event type."""
        events = [
            Event.create(EventType.REVENUE, value=100),
            Event.create(EventType.REVENUE, value=50),
            Event.create(EventType.SIGNUP, value=1),  # Different type
        ]

        total = aggregate_sum(events, EventType.REVENUE)
        assert total == 150

    def test_aggregate_count(self):
        """Should count events of type."""
        events = [
            Event.create(EventType.SIGNUP, value=1),
            Event.create(EventType.SIGNUP, value=1),
            Event.create(EventType.REVENUE, value=100),
        ]

        count = aggregate_count(events, EventType.SIGNUP)
        assert count == 2

    def test_aggregate_by_time_daily(self):
        """Should aggregate by day."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        events = [
            Event.create(EventType.REVENUE, value=100),
            Event.create(EventType.REVENUE, value=50),
        ]
        events[1].timestamp = yesterday

        by_day = aggregate_by_time(events, EventType.REVENUE, "daily")

        # Should have 2 days
        assert len(by_day) == 2
        # Today should have 100
        today_key = now.strftime("%Y-%m-%d")
        assert by_day[today_key] == 100


# =============================================================================
# Dashboard Tests
# =============================================================================

class TestDashboard:
    """Test Dashboard manager."""

    def test_log_event(self, temp_project):
        """Should log events through dashboard."""
        dashboard = Dashboard(temp_project)

        dashboard.log_event(EventType.REVENUE, value=100)
        dashboard.log_event(EventType.SIGNUP, value=1)

        assert dashboard.event_log.count() == 2

    def test_compute_state(self, temp_project):
        """Should compute dashboard state from events."""
        dashboard = Dashboard(temp_project)
        dashboard.set_north_star("$1M ARR", target_value=1000000)

        # Log some events
        dashboard.log_event(EventType.REVENUE, value=1000)
        dashboard.log_event(EventType.SIGNUP, value=1)
        dashboard.log_event(EventType.SIGNUP, value=1)
        dashboard.log_event(EventType.TASK_COMPLETED, value=1)

        state = dashboard.compute_state()

        assert state.north_star.current_value == 1000
        assert state.north_star.progress_pct == 0.1  # 1000/1000000 * 100
        assert state.metrics_lifetime["revenue"] == 1000
        assert state.metrics_lifetime["signups"] == 2
        assert state.tasks_completed == 1

    def test_state_saved_to_file(self, temp_project):
        """Dashboard state should be saved to JSON file."""
        dashboard = Dashboard(temp_project)
        dashboard.set_north_star("$1M ARR", target_value=1000000)
        dashboard.log_event(EventType.REVENUE, value=5000)

        state = dashboard.compute_state()

        # Check file exists and is valid JSON
        assert dashboard.state_file.exists()
        data = json.loads(dashboard.state_file.read_text())
        assert data["north_star"]["current_value"] == 5000

    def test_get_summary_for_imagination(self, temp_project):
        """Should provide summary suitable for IMAGINATION."""
        dashboard = Dashboard(temp_project)
        dashboard.set_north_star("$1M ARR", target_value=1000000)

        dashboard.log_event(EventType.REVENUE, value=10000)
        dashboard.log_event(EventType.HYPOTHESIS_CREATED, value=1)
        dashboard.log_event(EventType.HYPOTHESIS_VALIDATED, value=1)

        summary = dashboard.get_summary_for_imagination()

        assert summary["north_star"]["objective"] == "$1M ARR"
        assert summary["north_star"]["progress_pct"] == 1.0  # 10000/1M * 100
        assert summary["hypothesis_success_rate"] == 1.0


class TestNorthStarProgress:
    """Test North Star progress tracking."""

    def test_progress_calculation(self):
        """Should calculate progress percentage."""
        ns = NorthStarProgress(
            objective="$1M ARR",
            target_value=1000000,
            current_value=100000,
        )

        assert ns.progress_pct == 10.0

    def test_zero_target_handled(self):
        """Should handle zero target gracefully."""
        ns = NorthStarProgress(
            objective="Test",
            target_value=0,
            current_value=100,
        )

        assert ns.progress_pct == 0

    def test_on_track_without_deadline(self):
        """Without deadline, always on track."""
        ns = NorthStarProgress(
            objective="Test",
            target_value=1000,
            current_value=1,
            deadline=None,
        )

        assert ns.on_track is True


# =============================================================================
# Integration Tests
# =============================================================================

class TestDashboardIntegration:
    """Integration tests for dashboard flow."""

    def test_full_cycle_tracking(self, temp_project):
        """Should track a full cycle from start to finish."""
        dashboard = Dashboard(temp_project)
        dashboard.set_north_star("$100K MRR", target_value=100000)

        # Start cycle
        dashboard.log_event(EventType.CYCLE_STARTED, metadata={"cycle": 1})

        # Create hypothesis
        dashboard.log_event(
            EventType.HYPOTHESIS_CREATED,
            hypothesis_id="hyp-001",
            metadata={"description": "Build landing page"},
        )

        # Create task
        dashboard.log_event(
            EventType.TASK_CREATED,
            task_id="task-001",
            hypothesis_id="hyp-001",
        )

        # Task completes
        dashboard.log_event(
            EventType.TASK_COMPLETED,
            task_id="task-001",
            hypothesis_id="hyp-001",
        )

        # Metrics improve
        dashboard.log_event(EventType.SIGNUP, value=47)
        dashboard.log_event(EventType.REVENUE, value=1000)

        # End cycle
        dashboard.log_event(EventType.CYCLE_COMPLETED, metadata={"cycle": 1})

        # Check state
        state = dashboard.compute_state()

        assert state.cycle_count == 1
        assert state.tasks_completed == 1
        assert state.metrics_lifetime["signups"] == 47
        assert state.metrics_lifetime["revenue"] == 1000
        assert state.north_star.progress_pct == 1.0  # 1000/100000 * 100

    def test_metrics_decline_tracked(self, temp_project):
        """Should track when metrics go down (refunds, unsubscribes)."""
        dashboard = Dashboard(temp_project)
        dashboard.set_north_star("$10K MRR", target_value=10000)

        # Initial revenue
        dashboard.log_event(EventType.REVENUE, value=5000)

        # Refund (negative revenue)
        dashboard.log_event(EventType.REVENUE, value=-500)

        state = dashboard.compute_state()

        assert state.north_star.current_value == 4500

    def test_multiple_hypotheses_tracked(self, temp_project):
        """Should track success/failure rates across hypotheses."""
        dashboard = Dashboard(temp_project)
        dashboard.set_north_star("Test", target_value=1000)

        # 3 hypotheses created
        for i in range(3):
            dashboard.log_event(
                EventType.HYPOTHESIS_CREATED,
                hypothesis_id=f"hyp-{i:03d}",
            )

        # 2 validated, 1 invalidated
        dashboard.log_event(EventType.HYPOTHESIS_VALIDATED, hypothesis_id="hyp-000")
        dashboard.log_event(EventType.HYPOTHESIS_VALIDATED, hypothesis_id="hyp-001")
        dashboard.log_event(EventType.HYPOTHESIS_INVALIDATED, hypothesis_id="hyp-002")

        summary = dashboard.get_summary_for_imagination()

        # 2/3 success rate
        assert summary["hypothesis_success_rate"] == pytest.approx(0.666, rel=0.01)
