"""
Dashboard - Shared state between EXECUTION and IMAGINATION.

The Dashboard is the feedback loop that enables learning:
- EXECUTION writes events (task completed, metrics changed)
- IMAGINATION reads dashboard to generate informed hypotheses

Data Model:
- Event Log: Append-only log of all events (transactions)
- Dashboard State: Computed/cached view of current state
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Any
import uuid

logger = logging.getLogger("1kh.dashboard")


# =============================================================================
# Event Types
# =============================================================================

class EventType(str, Enum):
    """Types of events that can be logged."""
    # Metric events
    REVENUE = "revenue"
    SIGNUP = "signup"
    CONVERSION = "conversion"
    PAGE_VIEW = "page_view"
    ENGAGEMENT = "engagement"  # Time on page, scroll depth, etc.

    # System events
    HYPOTHESIS_CREATED = "hypothesis_created"
    HYPOTHESIS_ACCEPTED = "hypothesis_accepted"
    HYPOTHESIS_REJECTED = "hypothesis_rejected"
    HYPOTHESIS_VALIDATED = "hypothesis_validated"
    HYPOTHESIS_INVALIDATED = "hypothesis_invalidated"

    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_BLOCKED = "task_blocked"

    ESCALATION_CREATED = "escalation_created"
    ESCALATION_RESOLVED = "escalation_resolved"

    CYCLE_STARTED = "cycle_started"
    CYCLE_COMPLETED = "cycle_completed"

    # Human events
    HUMAN_DECISION = "human_decision"
    HUMAN_WORK_STARTED = "human_work_started"
    HUMAN_WORK_COMPLETED = "human_work_completed"

    # Custom
    CUSTOM = "custom"


@dataclass
class Event:
    """
    A single event in the event log.

    Events are immutable and append-only.
    """
    event_id: str
    timestamp: datetime
    event_type: EventType
    value: float  # Numeric value (revenue amount, count, duration, etc.)
    metadata: dict = field(default_factory=dict)  # Additional context
    source: str = "system"  # "system", "human", "mock"
    hypothesis_id: Optional[str] = None
    task_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "value": self.value,
            "metadata": self.metadata,
            "source": self.source,
            "hypothesis_id": self.hypothesis_id,
            "task_id": self.task_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=EventType(data["event_type"]),
            value=data.get("value", 0),
            metadata=data.get("metadata", {}),
            source=data.get("source", "system"),
            hypothesis_id=data.get("hypothesis_id"),
            task_id=data.get("task_id"),
        )

    @classmethod
    def create(
        cls,
        event_type: EventType,
        value: float = 1.0,
        metadata: dict = None,
        source: str = "system",
        hypothesis_id: str = None,
        task_id: str = None,
    ) -> "Event":
        """Factory method to create a new event."""
        return cls(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow(),
            event_type=event_type,
            value=value,
            metadata=metadata or {},
            source=source,
            hypothesis_id=hypothesis_id,
            task_id=task_id,
        )


# =============================================================================
# Event Log
# =============================================================================

class EventLog:
    """
    Append-only event log stored as JSONL file.

    Each line is a single JSON event.
    """

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.log_file = project_path / ".1kh" / "events.jsonl"
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self.log_file.touch()

    def append(self, event: Event):
        """Append an event to the log."""
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")
        logger.debug(f"Logged event: {event.event_type.value}")

    def append_many(self, events: list[Event]):
        """Append multiple events efficiently."""
        with open(self.log_file, "a") as f:
            for event in events:
                f.write(json.dumps(event.to_dict()) + "\n")
        logger.debug(f"Logged {len(events)} events")

    def read_all(self) -> list[Event]:
        """Read all events from the log."""
        events = []
        if self.log_file.exists():
            with open(self.log_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(Event.from_dict(json.loads(line)))
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning(f"Skipping malformed event: {e}")
        return events

    def read_since(self, since: datetime) -> list[Event]:
        """Read events since a given timestamp."""
        return [e for e in self.read_all() if e.timestamp >= since]

    def read_by_type(self, event_type: EventType) -> list[Event]:
        """Read events of a specific type."""
        return [e for e in self.read_all() if e.event_type == event_type]

    def read_by_hypothesis(self, hypothesis_id: str) -> list[Event]:
        """Read events for a specific hypothesis."""
        return [e for e in self.read_all() if e.hypothesis_id == hypothesis_id]

    def count(self) -> int:
        """Count total events."""
        return len(self.read_all())

    def clear(self):
        """Clear all events (for testing)."""
        self.log_file.write_text("")
        logger.info("Cleared event log")


# =============================================================================
# Aggregators
# =============================================================================

def aggregate_sum(events: list[Event], event_type: EventType) -> float:
    """Sum values for a specific event type."""
    return sum(e.value for e in events if e.event_type == event_type)


def aggregate_count(events: list[Event], event_type: EventType) -> int:
    """Count events of a specific type."""
    return len([e for e in events if e.event_type == event_type])


def aggregate_by_time(
    events: list[Event],
    event_type: EventType,
    granularity: str = "daily",
) -> dict[str, float]:
    """
    Aggregate events by time period.

    granularity: "hourly", "daily", "weekly", "monthly"
    Returns dict of {period_key: sum_value}
    """
    result = {}
    for event in events:
        if event.event_type != event_type:
            continue

        if granularity == "hourly":
            key = event.timestamp.strftime("%Y-%m-%d %H:00")
        elif granularity == "daily":
            key = event.timestamp.strftime("%Y-%m-%d")
        elif granularity == "weekly":
            # ISO week
            key = event.timestamp.strftime("%Y-W%W")
        elif granularity == "monthly":
            key = event.timestamp.strftime("%Y-%m")
        else:
            key = "lifetime"

        result[key] = result.get(key, 0) + event.value

    return result


# =============================================================================
# Dashboard State
# =============================================================================

@dataclass
class NorthStarProgress:
    """Progress toward a North Star objective."""
    objective: str
    target_value: float
    current_value: float
    deadline: Optional[datetime] = None

    @property
    def progress_pct(self) -> float:
        if self.target_value == 0:
            return 0
        return (self.current_value / self.target_value) * 100

    @property
    def on_track(self) -> bool:
        """Simple check: are we on track for deadline?"""
        if not self.deadline:
            return True
        # Calculate expected progress based on time
        # This is simplified - real version would be more sophisticated
        return self.progress_pct > 0


@dataclass
class DashboardState:
    """
    Computed dashboard state.

    This is cached and recomputed periodically from the event log.
    """
    computed_at: datetime

    # North Star
    north_star: NorthStarProgress

    # Aggregate metrics
    metrics_lifetime: dict[str, float] = field(default_factory=dict)
    metrics_last_24h: dict[str, float] = field(default_factory=dict)
    metrics_last_7d: dict[str, float] = field(default_factory=dict)

    # Hypothesis stats
    hypotheses_total: int = 0
    hypotheses_validated: int = 0
    hypotheses_invalidated: int = 0
    hypotheses_active: int = 0

    # Task stats
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_blocked: int = 0

    # Cycle info
    cycle_count: int = 0
    last_cycle_at: Optional[datetime] = None

    # Pending items
    pending_escalations: list[dict] = field(default_factory=list)
    active_hypotheses: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "computed_at": self.computed_at.isoformat(),
            "north_star": {
                "objective": self.north_star.objective,
                "target_value": self.north_star.target_value,
                "current_value": self.north_star.current_value,
                "progress_pct": self.north_star.progress_pct,
                "deadline": self.north_star.deadline.isoformat() if self.north_star.deadline else None,
            },
            "metrics_lifetime": self.metrics_lifetime,
            "metrics_last_24h": self.metrics_last_24h,
            "metrics_last_7d": self.metrics_last_7d,
            "hypotheses": {
                "total": self.hypotheses_total,
                "validated": self.hypotheses_validated,
                "invalidated": self.hypotheses_invalidated,
                "active": self.hypotheses_active,
            },
            "tasks": {
                "completed": self.tasks_completed,
                "failed": self.tasks_failed,
                "blocked": self.tasks_blocked,
            },
            "cycle_count": self.cycle_count,
            "last_cycle_at": self.last_cycle_at.isoformat() if self.last_cycle_at else None,
            "pending_escalations": self.pending_escalations,
            "active_hypotheses": self.active_hypotheses,
        }


# =============================================================================
# Dashboard Manager
# =============================================================================

class Dashboard:
    """
    Main dashboard interface.

    Manages event log and computes dashboard state.
    """

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.event_log = EventLog(project_path)
        self.state_file = project_path / ".1kh" / "dashboard.json"
        self._north_star_config: Optional[dict] = None

    def set_north_star(self, objective: str, target_value: float, deadline: datetime = None):
        """Configure the North Star objective."""
        self._north_star_config = {
            "objective": objective,
            "target_value": target_value,
            "deadline": deadline,
        }

    def log_event(
        self,
        event_type: EventType,
        value: float = 1.0,
        metadata: dict = None,
        source: str = "system",
        hypothesis_id: str = None,
        task_id: str = None,
    ):
        """Log an event to the event log."""
        event = Event.create(
            event_type=event_type,
            value=value,
            metadata=metadata,
            source=source,
            hypothesis_id=hypothesis_id,
            task_id=task_id,
        )
        self.event_log.append(event)

    def compute_state(self) -> DashboardState:
        """Compute dashboard state from event log."""
        events = self.event_log.read_all()
        now = datetime.utcnow()

        # Time filters
        from datetime import timedelta
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        events_24h = [e for e in events if e.timestamp >= last_24h]
        events_7d = [e for e in events if e.timestamp >= last_7d]

        # Compute North Star progress
        ns_config = self._north_star_config or {
            "objective": "Unknown",
            "target_value": 1,
            "deadline": None,
        }
        north_star = NorthStarProgress(
            objective=ns_config["objective"],
            target_value=ns_config["target_value"],
            current_value=aggregate_sum(events, EventType.REVENUE),
            deadline=ns_config.get("deadline"),
        )

        # Compute metrics
        # Note: All metrics use aggregate_sum so value represents the actual count/amount
        # e.g., log_event(SIGNUP, value=47) means 47 signups occurred
        metrics_lifetime = {
            "revenue": aggregate_sum(events, EventType.REVENUE),
            "signups": aggregate_sum(events, EventType.SIGNUP),
            "conversions": aggregate_sum(events, EventType.CONVERSION),
            "page_views": aggregate_sum(events, EventType.PAGE_VIEW),
        }

        metrics_24h = {
            "revenue": aggregate_sum(events_24h, EventType.REVENUE),
            "signups": aggregate_sum(events_24h, EventType.SIGNUP),
            "conversions": aggregate_sum(events_24h, EventType.CONVERSION),
            "page_views": aggregate_sum(events_24h, EventType.PAGE_VIEW),
        }

        metrics_7d = {
            "revenue": aggregate_sum(events_7d, EventType.REVENUE),
            "signups": aggregate_sum(events_7d, EventType.SIGNUP),
            "conversions": aggregate_sum(events_7d, EventType.CONVERSION),
            "page_views": aggregate_sum(events_7d, EventType.PAGE_VIEW),
        }

        # Compute hypothesis stats
        hypotheses_created = aggregate_count(events, EventType.HYPOTHESIS_CREATED)
        hypotheses_validated = aggregate_count(events, EventType.HYPOTHESIS_VALIDATED)
        hypotheses_invalidated = aggregate_count(events, EventType.HYPOTHESIS_INVALIDATED)
        hypotheses_accepted = aggregate_count(events, EventType.HYPOTHESIS_ACCEPTED)
        hypotheses_rejected = aggregate_count(events, EventType.HYPOTHESIS_REJECTED)

        # Compute task stats
        tasks_completed = aggregate_count(events, EventType.TASK_COMPLETED)
        tasks_failed = aggregate_count(events, EventType.TASK_FAILED)
        tasks_blocked = aggregate_count(events, EventType.TASK_BLOCKED)

        # Compute cycle count
        cycle_count = aggregate_count(events, EventType.CYCLE_COMPLETED)
        cycle_events = [e for e in events if e.event_type == EventType.CYCLE_COMPLETED]
        last_cycle_at = cycle_events[-1].timestamp if cycle_events else None

        state = DashboardState(
            computed_at=now,
            north_star=north_star,
            metrics_lifetime=metrics_lifetime,
            metrics_last_24h=metrics_24h,
            metrics_last_7d=metrics_7d,
            hypotheses_total=hypotheses_created,
            hypotheses_validated=hypotheses_validated,
            hypotheses_invalidated=hypotheses_invalidated,
            hypotheses_active=hypotheses_accepted - hypotheses_validated - hypotheses_invalidated,
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
            tasks_blocked=tasks_blocked,
            cycle_count=cycle_count,
            last_cycle_at=last_cycle_at,
        )

        # Save to file
        self._save_state(state)

        return state

    def _save_state(self, state: DashboardState):
        """Save dashboard state to JSON file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(state.to_dict(), indent=2))

    def load_state(self) -> Optional[DashboardState]:
        """Load cached dashboard state from file."""
        if not self.state_file.exists():
            return None
        try:
            data = json.loads(self.state_file.read_text())
            # Reconstruct state from dict (simplified)
            return self.compute_state()  # Just recompute for now
        except (json.JSONDecodeError, KeyError):
            return None

    def get_summary_for_imagination(self) -> dict:
        """
        Get a summary suitable for IMAGINATION loop to read.

        This is what IMAGINATION uses to generate informed hypotheses.
        """
        state = self.compute_state()

        return {
            "north_star": {
                "objective": state.north_star.objective,
                "target": state.north_star.target_value,
                "current": state.north_star.current_value,
                "progress_pct": state.north_star.progress_pct,
                "on_track": state.north_star.on_track,
            },
            "recent_metrics": state.metrics_last_7d,
            "trends": {
                "revenue_growing": state.metrics_last_24h.get("revenue", 0) > 0,
                "signups_growing": state.metrics_last_24h.get("signups", 0) > 0,
            },
            "hypothesis_success_rate": (
                state.hypotheses_validated / state.hypotheses_total
                if state.hypotheses_total > 0 else 0
            ),
            "task_success_rate": (
                state.tasks_completed / (state.tasks_completed + state.tasks_failed)
                if (state.tasks_completed + state.tasks_failed) > 0 else 0
            ),
            "cycles_completed": state.cycle_count,
            "pending_escalations": len(state.pending_escalations),
        }
