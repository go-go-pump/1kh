# ThousandHand v2: Technical Reference for Layer Artifacts

## File Locations & Imports

### Core Data Structures

**Location:** `/core/models.py`
**Key Imports:**
```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
```

**Enums to import:**
```python
from core.models import (
    BranchStatus,      # PROPOSED, BUILDING, ACTIVE, HEALTHY, ...
    TaskType,          # EXPLORE, BUILD, TEST, PRUNE
    TaskStatus,        # PENDING, IN_PROGRESS, COMPLETED, FAILED, BLOCKED
    EscalationTier,    # BLOCKING, ADVISORY, FYI
    HypothesisStatus,  # PROPOSED, BUILDING, TESTABLE, MEASURING, ...
)
```

---

### Runner & Execution

**Location:** `/core/runner.py`

**Key Classes:**
```python
from core.runner import (
    CycleRunner,           # Main orchestrator
    RunnerConfig,          # Configuration
    RunnerMode,            # DEMO | LOCAL
    Dependencies,          # Dependency injection container
    ExecutionResult,       # Output from execution
)
```

**Function Signatures:**
```python
# Main cycle orchestration
async def run() -> dict:
    """Run cycles until target reached or max cycles. Returns summary dict."""

async def _run_single_cycle() -> dict:
    """Run single REFLECTION → IMAGINATION → INTENT → WORK → EXECUTION cycle."""

async def _imagination_phase(self, reflection_result: dict = None) -> list[dict]:
    """Generate hypotheses using Claude (or mock), informed by reflection."""

async def _intent_phase(self, hypotheses: list[dict]) -> tuple[list[dict], list[dict]]:
    """Evaluate hypotheses and decide which to pursue.
    Returns (approved, escalated) tuples."""

async def _work_phase(self, approved: list[dict]) -> list[tuple[dict, dict]]:
    """Create tasks from approved hypotheses. Returns list of (task, hypothesis) pairs."""

async def _execution_phase(self, task: dict, hypothesis: dict) -> ExecutionResult:
    """Execute a task and log results. Returns ExecutionResult."""
```

---

### Reflection Engine

**Location:** `/core/reflection.py`

**Key Classes:**
```python
from core.reflection import (
    ReflectionEngine,          # Main engine
    ReflectionResult,          # Output data structure
    CompletenessAnalysis,      # Part of result
    TrajectoryAnalysis,        # Part of result
    Recommendation,            # Part of result
    RecommendationType,        # AUGMENT, OPTIMIZE, PIVOT, CONTINUE
    TrustLevel,                # MANUAL, GUIDED, AUTONOMOUS
)
```

**Complete ReflectionResult structure:**
```python
result = ReflectionResult(
    timestamp=datetime.utcnow(),
    cycle_number=42,

    completeness=CompletenessAnalysis(
        score=0.75,
        can_generate_revenue=True,
        blockers=[],
        missing_components=["support"],
        building_components=["payment"],
        live_components=["product", "channel", "fulfillment"],
    ),

    trajectory=TrajectoryAnalysis(
        current_value=50000.0,
        target_value=1000000.0,
        velocity_per_cycle=5000.0,
        velocity_trend="steady",
        cycles_to_goal=190,
        time_to_goal="190 cycles (570 days, ~19 months)",
        confidence=0.72,
        is_realistic=True,
        warning=None,
    ),

    recommendations=[
        Recommendation(
            type=RecommendationType.OPTIMIZE,
            title="Improve Conversion Rate",
            description="A/B test landing page",
            rationale="Trajectory is steady but slow. Optimization can accelerate.",
            priority=1,
            component_category="channel",
            suggested_hypotheses=[
                {
                    "description": "A/B test headlines on landing page",
                    "component": "channel",
                }
            ],
            requires_human=False,
        ),
    ],

    status="healthy",  # or "warning", "critical"
    summary="On track. Consider optimization to accelerate.",
)

# Convert to dict for serialization
result_dict = result.to_dict()
```

---

### Dashboard & Events

**Location:** `/core/dashboard.py`

**Key Classes:**
```python
from core.dashboard import (
    Dashboard,          # Main dashboard class
    EventLog,           # Append-only event log
    Event,              # Individual event
    EventType,          # Enum of event types
)
```

**Creating and logging events:**
```python
from core.dashboard import Event, EventType

# Method 1: Factory method (recommended)
event = Event.create(
    event_type=EventType.REVENUE,
    value=1500.0,
    metadata={"campaign": "email_marketing"},
    source="system",
    hypothesis_id="hyp-001-PAY",
    task_id="task-001-PAY",
)

# Method 2: Direct constructor
event = Event(
    event_id=f"evt-{uuid.uuid4().hex[:12]}",
    timestamp=datetime.utcnow(),
    event_type=EventType.REVENUE,
    value=1500.0,
    metadata={},
    source="system",
    hypothesis_id="hyp-001-PAY",
    task_id="task-001-PAY",
)

# Log to event log
dashboard = Dashboard(project_path)
dashboard.log_event(EventType.REVENUE, value=1500.0, task_id="task-001-PAY")

# Or log directly with Event object
event_log = EventLog(project_path)
event_log.append(event)

# Query events
all_events = event_log.read_all()
revenue_events = event_log.read_by_type(EventType.REVENUE)
hyp_events = event_log.read_by_hypothesis("hyp-001-PAY")
recent_events = event_log.read_since(datetime.utcnow() - timedelta(hours=1))
```

**EventType enum values:**
```python
EventType.REVENUE              # Metric: revenue generated
EventType.SIGNUP               # Metric: new user signup
EventType.CONVERSION           # Metric: conversion rate
EventType.PAGE_VIEW            # Metric: page views
EventType.ENGAGEMENT           # Metric: time/interaction
EventType.HYPOTHESIS_CREATED   # System event
EventType.HYPOTHESIS_ACCEPTED  # System event
EventType.HYPOTHESIS_REJECTED  # System event
EventType.TASK_CREATED         # System event
EventType.TASK_COMPLETED       # System event
EventType.TASK_FAILED          # System event
EventType.CYCLE_STARTED        # System event
EventType.CYCLE_COMPLETED      # System event
```

---

### System State Tracking

**Location:** `/core/system_state.py`

**Key Classes:**
```python
from core.system_state import (
    SystemState,           # Complete state
    SystemMode,            # BUSINESS | SYSTEM
    BusinessComponent,     # Individual component
    ComponentStatus,       # MISSING, PLANNED, BUILDING, LIVE, BROKEN
    SystemStateManager,    # Manager class
)
```

**Working with system state:**
```python
from core.system_state import (
    SystemState,
    BusinessComponent,
    ComponentStatus,
    SystemMode,
)

# Load or create state
manager = SystemStateManager(project_path)
state = manager.load()

# Check components
product_comp = state.get_component("product")
is_payment_live = state.is_component_live("payment")

# Get all missing components
missing = state.get_missing_components()  # Returns list[BusinessComponent]
building = state.get_building_components()
live = state.get_live_components()

# Update component status
payment_comp = state.get_component("payment")
if payment_comp:
    payment_comp.status = ComponentStatus.LIVE
    payment_comp.live_since = datetime.utcnow()
    state.updated_at = datetime.utcnow()
    manager.save(state)

# Check if system can generate revenue
if state.is_component_live("product") and state.is_component_live("payment") and \
   state.is_component_live("channel") and state.is_component_live("fulfillment"):
    can_generate_revenue = True
else:
    can_generate_revenue = False
```

---

### Hypothesis Management

**Location:** `/core/hypothesis.py`

**Key Classes:**
```python
from core.hypothesis import (
    HypothesisManager,       # Main manager
    HypothesisLevel,         # CAPABILITY | IMPLEMENTATION
    VendorCategory,          # PAYMENT, HOSTING, DATABASE, EMAIL, etc.
    VendorSelection,         # Result of vendor selection
    Preference,              # User preference
    PreferencesManager,      # Preference manager
)
```

**Two-level hypothesis system:**
```python
from core.hypothesis import HypothesisManager, HypothesisLevel

# Create manager
manager = HypothesisManager(
    project_path=Path("/my/project"),
    ask_user_callback=lambda cat, options: "stripe",  # Callback for user choice
)

# Load preferences
preferences = manager.preferences_manager.load()
# Example: preferences["payment"].preferred = "stripe"

# Check if hypothesis needs implementation decision
needs_impl = manager.needs_implementation_decision(hypothesis)

# If it does, select implementation
selection = manager.select_implementation(hypothesis)
# Returns VendorSelection with selected_vendor="stripe", source="preference"

# Create implementation-specific hypothesis
impl_hyp = manager.create_implementation_hypothesis(hypothesis, selection)

# Store in original hypothesis
hypothesis["implementation"] = impl_hyp
hypothesis["selected_vendor"] = selection.selected_vendor
hypothesis["vendor_source"] = selection.source
```

---

### Executor

**Location:** `/core/executor.py`

**Key Classes:**
```python
from core.executor import (
    ClaudeExecutor,     # Real executor using Claude
)

from core.runner import (
    ExecutionResult,    # Output type
)
```

**Executing tasks:**
```python
from core.executor import ClaudeExecutor
from core.dashboard import Dashboard
from core.conversation import ConversationManager

dashboard = Dashboard(project_path)
conv_manager = ConversationManager(project_path)
executor = ClaudeExecutor(
    project_path=project_path,
    dashboard=dashboard,
    conversation_manager=conv_manager,
    claude_client=client,
    simulate_metrics=True,  # Use realistic mock metrics (local mode)
)

# Execute a task
result = executor.execute(
    task={
        "id": "task-001-PAY",
        "hypothesis_id": "hyp-001-PAY",
        "description": "Integrate Stripe payment processing",
        "task_type": "build",
    },
    hypothesis={
        "id": "hyp-001-PAY",
        "description": "Enable payment processing",
        "feasibility": 0.85,
        "north_star_alignment": 0.99,
    }
)

# Result structure
assert result.success == True
assert result.task_id == "task-001-PAY"
assert result.hypothesis_id == "hyp-001-PAY"
assert "revenue" in result.metrics_delta
assert result.metrics_delta["revenue"] >= 0
```

---

### Temporal Activities (for distributed execution)

**Location:** `/temporal/activities/imagination.py`

**Function signature:**
```python
from temporal.activities.imagination import generate_hypotheses

hypotheses = await generate_hypotheses(
    project_path: str,
    oracle: dict,
    north_star: dict,
    context: dict,
    existing_hypotheses: list[dict],
    max_new: int,
    reflection: dict = None,  # Optional: guides generation
) -> list[dict]
```

**Location:** `/temporal/activities/work.py`

**Function signature:**
```python
from temporal.activities.work import create_task

task = await create_task(
    project_path: str,
    hypothesis: dict,
    oracle: dict,
    context: dict,
) -> dict
```

**Returns task dict:**
```python
{
    "id": "task-001-PAY",
    "hypothesis_id": "hyp-001-PAY",
    "description": "Integrate Stripe payment processing",
    "task_type": "build",
    "status": "pending",
    "created_at": datetime.utcnow(),
    # ... other fields
}
```

---

## Complete Example: One Cycle

```python
#!/usr/bin/env python
"""
Example: Orchestrate one complete cycle manually.
"""
import asyncio
from pathlib import Path

from core.runner import CycleRunner, RunnerConfig, RunnerMode, Dependencies
from core.dashboard import Dashboard
from core.executor import MockExecutor  # Or ClaudeExecutor for real
from core.reflection import ReflectionEngine

async def example_cycle():
    project_path = Path("/my/1kh/project")

    # Create config
    config = RunnerConfig(
        mode=RunnerMode.DEMO,
        project_path=project_path,
        approval_threshold=0.65,
        escalation_threshold=0.40,
        max_cycles=1,
        max_hypotheses_per_cycle=5,
        max_tasks_per_cycle=3,
    )

    # Create dependencies
    dashboard = Dashboard(project_path)
    deps = Dependencies(
        claude_client=None,  # Mock in demo mode
        human_responder=MockHumanResponder(),
        executor=MockExecutor(project_path, dashboard),
        dashboard=dashboard,
    )

    # Create runner
    runner = CycleRunner(config, deps)

    # Run one cycle
    print("=" * 80)
    print("REFLECTION PHASE")
    print("=" * 80)
    reflection_result = runner._run_reflection()
    print(f"Status: {reflection_result['status']}")
    print(f"Blockers: {reflection_result['completeness']['blockers']}")
    print(f"Recommendations: {len(reflection_result['recommendations'])}")

    print("\n" + "=" * 80)
    print("IMAGINATION PHASE")
    print("=" * 80)
    hypotheses = await runner._imagination_phase(reflection_result)
    print(f"Generated {len(hypotheses)} hypotheses")
    for hyp in hypotheses:
        print(f"  - {hyp['id']}: {hyp['description']}")
        print(f"    Feasibility: {hyp['feasibility']:.2f}, "
              f"Alignment: {hyp['north_star_alignment']:.2f}")

    print("\n" + "=" * 80)
    print("INTENT PHASE")
    print("=" * 80)
    approved, escalated = await runner._intent_phase(hypotheses)
    print(f"Approved: {len(approved)}")
    for hyp in approved:
        print(f"  - {hyp['id']}")
    print(f"Escalated (need human): {len(escalated)}")
    for hyp in escalated:
        print(f"  - {hyp['id']}")

    print("\n" + "=" * 80)
    print("WORK PHASE")
    print("=" * 80)
    tasks = await runner._work_phase(approved)
    print(f"Created {len(tasks)} tasks")
    for task, hyp in tasks:
        print(f"  - {task['id']}: {task['description']}")

    print("\n" + "=" * 80)
    print("EXECUTION PHASE")
    print("=" * 80)
    for task, hyp in tasks:
        result = await runner._execution_phase(task, hyp)
        print(f"  {task['id']}: {'SUCCESS' if result.success else 'FAILED'}")
        if result.metrics_delta:
            print(f"    Metrics: {result.metrics_delta}")
        if result.errors:
            print(f"    Errors: {result.errors}")

    print("\n" + "=" * 80)
    print("FINAL STATE")
    print("=" * 80)
    final_state = dashboard.compute_state()
    print(f"Current value: ${final_state.north_star.current_value:,.2f}")
    print(f"Target value: ${final_state.north_star.target_value:,.2f}")
    print(f"Progress: {final_state.north_star.progress_pct:.1f}%")

if __name__ == "__main__":
    asyncio.run(example_cycle())
```

---

## JSON Serialization Format

### Event (as stored in events.jsonl)

```json
{
  "event_id": "evt-a1b2c3d4e5f6",
  "timestamp": "2025-02-07T15:30:45.123456",
  "event_type": "revenue",
  "value": 1500.0,
  "metadata": {
    "campaign": "email_marketing",
    "source": "stripe"
  },
  "source": "system",
  "hypothesis_id": "hyp-001-PAY",
  "task_id": "task-001-PAY"
}
```

### RunState (as stored in .1kh/state/run_state.json)

```json
{
  "last_cycle": 42,
  "hypotheses_total": 127,
  "tasks_total": 89,
  "escalations_total": 12,
  "failures": 3,
  "last_run_at": "2025-02-07T15:30:45.123456",
  "target_reached": false,
  "simulated_days": 126,
  "days_per_cycle": 3
}
```

### SystemState (as stored in .1kh/system_state.json)

```json
{
  "mode": "business",
  "components": [
    {
      "name": "Product",
      "category": "product",
      "status": "live",
      "description": "The thing you sell",
      "details": {},
      "hypothesis_ids": ["hyp-001", "hyp-005"],
      "task_ids": ["task-001", "task-005"],
      "live_since": "2025-01-15T10:00:00"
    },
    {
      "name": "Payment",
      "category": "payment",
      "status": "live",
      "description": "How customers pay you",
      "details": {
        "vendor": "stripe",
        "type": "credit_card"
      },
      "hypothesis_ids": ["hyp-010"],
      "task_ids": ["task-010"],
      "live_since": "2025-01-20T14:30:00"
    }
  ],
  "custom_kpis": {},
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-02-07T15:30:45.123456",
  "active_hypotheses": [],
  "completed_hypotheses": [...],
  "active_tasks": [],
  "completed_tasks": [...]
}
```

---

## Measurement & Validation

### Validating Cycle Output

```python
def validate_cycle_result(result: dict) -> bool:
    """Validate that cycle produced correct structure."""
    required_keys = {
        "cycle",
        "hypotheses_generated",
        "hypotheses_approved",
        "hypotheses_escalated",
        "tasks_executed",
        "tasks_succeeded",
        "tasks_failed",
        "revenue_delta",
        "signups_delta",
    }
    return required_keys.issubset(set(result.keys()))

def validate_hypothesis(hyp: dict) -> bool:
    """Validate hypothesis structure."""
    required_keys = {"id", "description", "feasibility", "north_star_alignment"}
    has_floats = (
        isinstance(hyp.get("feasibility"), float) and
        isinstance(hyp.get("north_star_alignment"), float) and
        0.0 <= hyp["feasibility"] <= 1.0 and
        0.0 <= hyp["north_star_alignment"] <= 1.0
    )
    return required_keys.issubset(set(hyp.keys())) and has_floats

def validate_execution_result(result: ExecutionResult) -> bool:
    """Validate ExecutionResult structure."""
    return (
        isinstance(result.success, bool) and
        isinstance(result.task_id, str) and
        isinstance(result.metrics_delta, dict) and
        isinstance(result.errors, list)
    )
```

---

## Debugging & Inspection

### Inspect Event Log

```python
from core.dashboard import EventLog, EventType

log = EventLog(project_path)

# Count by type
revenue_events = log.read_by_type(EventType.REVENUE)
total_revenue = sum(e.value for e in revenue_events)
print(f"Total revenue: ${total_revenue:,.2f}")

# Events for hypothesis
hyp_events = log.read_by_hypothesis("hyp-001-PAY")
print(f"Events for hyp-001-PAY: {len(hyp_events)}")

# Recent events
from datetime import datetime, timedelta
since = datetime.utcnow() - timedelta(hours=1)
recent = log.read_since(since)
print(f"Events in last hour: {len(recent)}")

# Export for analysis
import json
events_data = [e.to_dict() for e in log.read_all()]
with open("events_dump.json", "w") as f:
    json.dump(events_data, f, indent=2)
```

### Inspect System State

```python
from core.system_state import SystemStateManager, ComponentStatus

manager = SystemStateManager(project_path)
state = manager.load()

print("Component Status:")
for comp in state.components:
    print(f"  {comp.name}: {comp.status.value} (live since {comp.live_since})")

print("\nMissing components:")
for comp in state.get_missing_components():
    print(f"  - {comp.name}")

print("\nCan generate revenue:",
      state.is_component_live("product") and
      state.is_component_live("payment") and
      state.is_component_live("channel") and
      state.is_component_live("fulfillment"))
```

