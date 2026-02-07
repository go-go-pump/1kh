# ThousandHand v2: Intermediate Artifacts Between Layers

## Executive Summary

The ThousandHand v2 system orchestrates a 5-loop cycle that transforms business ideas into executable work:

```
REFLECTION → IMAGINATION → INTENT → WORK → EXECUTION → [feedback to REFLECTION]
```

This document specifies the **exact data structures and interfaces** that flow between each layer. These artifacts are the contract between layers and must be defined precisely for v3 implementation.

---

## Layer 1: REFLECTION → IMAGINATION

**Purpose:** REFLECTION analyzes system completeness and trajectory, producing recommendations that guide IMAGINATION to generate focused hypotheses.

### REFLECTION Output

**Type:** `ReflectionResult` dataclass
**Location:** `/core/reflection.py` lines 100-143

```python
@dataclass
class ReflectionResult:
    """Complete result from a REFLECTION cycle."""
    timestamp: datetime
    cycle_number: int

    # Analyses
    completeness: CompletenessAnalysis
    trajectory: TrajectoryAnalysis

    # Recommendations
    recommendations: list[Recommendation]

    # Overall assessment
    status: str  # "healthy", "warning", "critical"
    summary: str

    def to_dict(self) -> dict:
        """Convert to serializable format"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cycle_number": self.cycle_number,
            "completeness": {
                "score": self.completeness.score,
                "can_generate_revenue": self.completeness.can_generate_revenue,
                "blockers": self.completeness.blockers,
                "missing_components": self.completeness.missing_components,
                "building_components": self.completeness.building_components,
                "live_components": self.completeness.live_components,
            },
            "trajectory": {
                "current_value": self.trajectory.current_value,
                "target_value": self.trajectory.target_value,
                "velocity_per_cycle": self.trajectory.velocity_per_cycle,
                "velocity_trend": self.trajectory.velocity_trend,
                "cycles_to_goal": self.trajectory.cycles_to_goal,
                "time_to_goal": self.trajectory.time_to_goal,
                "confidence": self.trajectory.confidence,
                "is_realistic": self.trajectory.is_realistic,
                "warning": self.trajectory.warning,
            },
            "recommendations": [r.to_dict() for r in self.recommendations],
            "status": self.status,
            "summary": self.summary,
        }
```

### CompletenessAnalysis (part of ReflectionResult)

```python
@dataclass
class CompletenessAnalysis:
    """Analysis of system completeness."""
    score: float  # 0-1 completeness
    can_generate_revenue: bool
    blockers: list[str]  # e.g., "No payment system - cannot process customer payments"
    missing_components: list[str]  # e.g., ["payment", "channel"]
    building_components: list[str]
    live_components: list[str]  # e.g., ["product", "fulfillment"]
```

### TrajectoryAnalysis (part of ReflectionResult)

```python
@dataclass
class TrajectoryAnalysis:
    """Analysis of current trajectory toward goal."""
    current_value: float
    target_value: float
    velocity_per_cycle: float  # Average change per cycle
    velocity_trend: str  # "accelerating", "steady", "decelerating", "stalled"
    cycles_to_goal: Optional[int]  # Estimated cycles to reach goal (None if unrealistic)
    time_to_goal: Optional[str]  # Human-readable estimate
    confidence: float  # 0-1 confidence in estimate
    is_realistic: bool  # True if we can reasonably reach goal
    warning: Optional[str] = None
```

### Recommendation (part of ReflectionResult)

```python
@dataclass
class Recommendation:
    """A recommendation from REFLECTION."""
    type: RecommendationType  # AUGMENT | OPTIMIZE | PIVOT | CONTINUE
    title: str
    description: str
    rationale: str
    priority: int = 1  # 1 = highest priority
    component_category: Optional[str] = None  # Which component this affects
    suggested_hypotheses: list[dict] = field(default_factory=list)  # Pre-suggested hypotheses
    requires_human: bool = False  # True for PIVOT

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "priority": self.priority,
            "component_category": self.component_category,
            "suggested_hypotheses": self.suggested_hypotheses,
            "requires_human": self.requires_human,
        }
```

### How It Flows to IMAGINATION

**In runner.py lines 602-631:**

```python
async def _imagination_phase(self, reflection_result: dict = None) -> list[dict]:
    """Generate hypotheses using Claude (or mock), informed by reflection."""

    # ... load foundation ...

    # Generate hypotheses with reflection guidance
    hypotheses = await self._call_imagination_activity(
        oracle=self._oracle,
        north_star=self._north_star,
        context=self._context,
        dashboard_state=state,
        reflection=reflection_result,  # ← REFLECTION FLOWS HERE
    )
```

**Impact on IMAGINATION:** The `reflection` parameter guides hypothesis generation (line 821-932 mock logic):
- If `can_generate_revenue=False`, prioritizes hypotheses to fix missing components
- If trajectory is `stalled`, recommends optimization hypotheses
- If trajectory indicates `decline`, prepares for pivot decisions

---

## Layer 2: IMAGINATION → INTENT

**Purpose:** IMAGINATION generates hypotheses with scoring. INTENT receives these and decides which to pursue based on thresholds.

### IMAGINATION Output

**Type:** `list[dict]` (hypotheses)
**Location:** `/temporal/activities/imagination.py` lines 58-100+

```python
@dataclass
class Hypothesis:
    """A potential path toward the North Star."""
    id: str
    description: str
    rationale: str

    # Which North Star objectives does this serve?
    serves_objectives: list[str]  # List of objective indices/descriptions

    # How does it serve them?
    objective_mapping: str  # Explanation of how this connects to North Star

    # Effort and timeline
    estimated_effort: str  # "hours", "days", "weeks", "months"
    estimated_hours: int  # Concrete hour estimate

    # Multi-dimensional scoring
    feasibility: float  # 0.0-1.0: Can we build it?
    north_star_alignment: float  # 0.0-1.0: Will it achieve the goal?

    # Dependencies and relationships
    depends_on: list[str] = field(default_factory=list)  # Other hypothesis IDs
    blocks: list[str] = field(default_factory=list)  # What this blocks
    parent_id: Optional[str] = None  # For nested/child hypotheses

    # Risks and assumptions
    risks: list[str] = field(default_factory=list)
```

**Real-world example from demo mode (runner.py lines 954-961):**

```python
{
    "id": f"hyp-{self.cycle_count:03d}-1",
    "description": "Implement email marketing automation",
    "feasibility": 0.75,  # Can we technically build it?
    "north_star_alignment": 0.85,  # Will it move the needle toward goal?
    "estimated_effort": "medium",
    "estimated_hours": 40,
    # ... other fields ...
}
```

### How It Flows to INTENT

**In runner.py lines 642-694:**

```python
async def _intent_phase(self, hypotheses: list[dict]) -> tuple[list[dict], list[dict]]:
    """Evaluate hypotheses and decide which to pursue."""

    approved = []
    escalated = []

    for hyp in hypotheses:
        # Calculate combined score
        feasibility = hyp.get("feasibility", 0)
        alignment = hyp.get("north_star_alignment", 0)
        score = feasibility * 0.4 + alignment * 0.6  # ← SCORING FORMULA

        hyp["_combined_score"] = score

        if score >= self.config.approval_threshold:  # 0.65 default
            # Auto-approve
            approved.append(hyp)
        elif score >= self.config.escalation_threshold:  # 0.40 default
            # Needs human review
            escalated.append(hyp)
        else:
            # Reject
            pass

    return approved, escalated
```

---

## Layer 3: INTENT → WORK

**Purpose:** INTENT decides which hypotheses to pursue. WORK breaks them into concrete tasks.

### INTENT Output

**Type:** `list[dict]` (approved hypotheses) + context for task creation

**Key Data Passed:**
- `approved`: List of approved hypotheses (same structure as IMAGINATION output)
- `escalated`: List of hypotheses needing human approval
- Dashboard state: Current system metrics for context

**In runner.py lines 415-427:**

```python
if approved:
    if self.config.on_phase_start:
        self.config.on_phase_start("work")

    tasks = await self._work_phase(approved)  # ← APPROVED HYPOTHESES FLOW HERE
```

### WORK Input/Output

**Input Function Signature (runner.py lines 965-977):**

```python
async def _call_work_activity(self, hypothesis: dict) -> dict:
    """Call work activity to create task (real or mock)."""
    if self.config.mode == RunnerMode.DEMO:
        return self._mock_task(hypothesis)

    from temporal.activities.work import create_task

    return await create_task(
        project_path=str(self.config.project_path),
        hypothesis=hypothesis,
        oracle=self._oracle,
        context=self._context,
    )
```

**Activity Signature (temporal/activities/work.py lines 62-81):**

```python
@activity.defn
async def create_task(
    project_path: str,
    hypothesis: dict,
    oracle: dict,
    context: dict,
) -> dict:
    """
    Break a hypothesis into a concrete, actionable task.

    Returns:
        A task dictionary ready for execution
    """
```

### Task Structure

**Type:** `dict` (simplified Task)
**Location:** `/temporal/activities/work.py` lines 44-59

```python
@dataclass
class Task:
    """A concrete unit of work."""
    id: str
    hypothesis_id: str
    description: str
    task_type: str  # "build", "research", "deploy", "test"
    status: str  # "pending", "in_progress", "completed", "failed", "blocked"
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    # Resource declarations
    touches_resources: list = None  # [{type, identifier, access}]
    blocked_by: list = None  # List of task IDs blocking this task
```

**Mock implementation (runner.py lines 979-986):**

```python
def _mock_task(self, hypothesis: dict) -> dict:
    """Create mock task for demo mode."""
    return {
        "id": f"task-{self.cycle_count:03d}-{hypothesis['id'].split('-')[-1]}",
        "hypothesis_id": hypothesis["id"],
        "description": f"Execute: {hypothesis['description'][:40]}",
        "task_type": "build",
    }
```

---

## Layer 4: WORK → EXECUTION

**Purpose:** WORK creates tasks. EXECUTION runs them and tracks results.

### WORK Output

**Type:** `list[tuple[dict, dict]]` (task, hypothesis pairs)

**In runner.py lines 434-456:**

```python
for task, hyp in tasks:
    result = await self._execution_phase(task, hyp)

    # Track for report
    all_tasks.append({
        **task,
        "result": result.metrics_delta,
        "success": result.success,
    })

    if self.config.on_task_executed:
        self.config.on_task_executed(task, result)
```

### EXECUTION Input

**Function Signature (runner.py lines 715-720):**

```python
async def _execution_phase(self, task: dict, hypothesis: dict) -> ExecutionResult:
    """Execute a task and log results."""

    # Execute using injected executor
    result = self.deps.executor.execute(task, hypothesis)
```

### ExecutionResult (output from EXECUTION)

**Type:** `ExecutionResult` dataclass
**Location:** `/core/runner.py` lines 94-106

```python
@dataclass
class ExecutionResult:
    """Result of executing a task."""
    success: bool
    task_id: str
    hypothesis_id: Optional[str] = None
    result_text: str = ""
    duration_seconds: float = 0
    metrics_delta: dict = field(default_factory=dict)  # {revenue: X, signups: Y, ...}
    errors: list[str] = field(default_factory=list)
    needs_human: bool = False
    human_prompt: Optional[str] = None
```

**Real executor implementation (executor.py lines 70-128):**

```python
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
                metrics_delta=metrics,  # ← KEY ARTIFACT
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
```

### Metrics Structure

**Type:** `dict[str, float]`

**Example from executor.py:**

```python
metrics = {
    "revenue": 1500.0,      # Dollar amount
    "signups": 3,           # Number of new users
    "conversion": 0.025,    # Conversion rate
    "engagement": 45.0,     # Minutes spent
}
```

---

## Layer 5: EXECUTION → Back to State/Dashboard

**Purpose:** EXECUTION writes metrics to dashboard, which feeds back to REFLECTION.

### ExecutionResult → Dashboard Conversion

**In runner.py lines 715-748:**

```python
async def _execution_phase(self, task: dict, hypothesis: dict) -> ExecutionResult:
    """Execute a task and log results."""

    # Execute using injected executor
    result = self.deps.executor.execute(task, hypothesis)

    if result.success:
        self.deps.dashboard.log_event(
            EventType.TASK_COMPLETED,
            task_id=task.get("id"),
        )

        # Log metrics
        if result.metrics_delta.get("revenue"):
            self.deps.dashboard.log_event(
                EventType.REVENUE,
                value=result.metrics_delta["revenue"],  # ← FLOWS HERE
                task_id=task.get("id"),
            )
        if result.metrics_delta.get("signups"):
            self.deps.dashboard.log_event(
                EventType.SIGNUP,
                value=result.metrics_delta["signups"],
                task_id=task.get("id"),
            )
    else:
        self.deps.dashboard.log_event(
            EventType.TASK_FAILED,
            task_id=task.get("id"),
            metadata={"errors": result.errors},
        )

    return result
```

### Event Structure

**Type:** `Event` dataclass
**Location:** `/core/dashboard.py` lines 75-137

```python
@dataclass
class Event:
    """A single event in the event log."""
    event_id: str
    timestamp: datetime
    event_type: EventType  # REVENUE, SIGNUP, TASK_COMPLETED, etc.
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
```

### Event Types (dashboard.py lines 30-73)

```python
class EventType(str, Enum):
    """Types of events that can be logged."""
    # Metric events
    REVENUE = "revenue"
    SIGNUP = "signup"
    CONVERSION = "conversion"
    PAGE_VIEW = "page_view"
    ENGAGEMENT = "engagement"

    # System events
    HYPOTHESIS_CREATED = "hypothesis_created"
    HYPOTHESIS_ACCEPTED = "hypothesis_accepted"
    HYPOTHESIS_REJECTED = "hypothesis_rejected"
    HYPOTHESIS_VALIDATED = "hypothesis_validated"
    HYPOTHESIS_INVALIDATED = "hypothesis_invalidated"

    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # ... others ...
```

### Dashboard State (computed view)

**The Dashboard computes aggregated state from the event log and feeds it back to REFLECTION.**

---

## Special: Two-Level Hypothesis System

### Hypothesis Levels

**Location:** `/core/hypothesis.py` lines 24-27

```python
class HypothesisLevel(str, Enum):
    """Hypothesis abstraction level."""
    CAPABILITY = "capability"      # WHAT - technology-agnostic
    IMPLEMENTATION = "implementation"  # HOW - technology-specific
```

### Vendor Selection in INTENT Phase

**In runner.py lines 662-680:**

```python
needs_vendor = (
    hyp.get("needs_vendor_decision") or  # Explicit flag (demo mode)
    (self._hypothesis_manager and self._hypothesis_manager.needs_implementation_decision(hyp))
)

if needs_vendor and self._hypothesis_manager:
    # This hypothesis needs a vendor/technology choice
    selection = self._hypothesis_manager.select_implementation(hyp)

    if selection:
        # Create implementation-specific hypothesis
        impl_hyp = self._hypothesis_manager.create_implementation_hypothesis(hyp, selection)

        # Replace capability hypothesis with implementation hypothesis
        hyp["implementation"] = impl_hyp
        hyp["selected_vendor"] = selection.selected_vendor
        hyp["vendor_source"] = selection.source
```

### VendorSelection Structure

**Location:** `/core/hypothesis.py` lines 92-97

```python
@dataclass
class VendorSelection:
    """Result of vendor selection process."""
    category: VendorCategory
    selected_vendor: str
    source: str  # "preference", "user_choice", "default"
    reason: Optional[str] = None
```

---

## Special: System State Completeness Tracking

### BusinessComponent Structure

**Location:** `/core/system_state.py` lines 54-89

```python
@dataclass
class BusinessComponent:
    """A component required for a viable business."""
    name: str
    category: str  # "product", "payment", "channel", "fulfillment", "support"
    status: ComponentStatus = ComponentStatus.MISSING
    description: str = ""
    details: dict = field(default_factory=dict)
    hypothesis_ids: list[str] = field(default_factory=list)  # Which hypotheses built this
    task_ids: list[str] = field(default_factory=list)  # Which tasks built this
    live_since: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "status": self.status.value,
            "description": self.description,
            "details": self.details,
            "hypothesis_ids": self.hypothesis_ids,
            "task_ids": self.task_ids,
            "live_since": self.live_since.isoformat() if self.live_since else None,
        }
```

### ComponentStatus Enum

**Location:** `/core/system_state.py` lines 41-48

```python
class ComponentStatus(str, Enum):
    """Status of a system component."""
    MISSING = "missing"      # Not defined, not planned
    PLANNED = "planned"      # Defined but not started
    BUILDING = "building"    # Work in progress
    LIVE = "live"            # Deployed and functional
    BROKEN = "broken"        # Was live, now broken
```

---

## Cycle Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE CYCLE FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

1. REFLECTION PHASE (runner.py:501-515)
   ├─ Input: Dashboard state (metrics, events from previous cycle)
   ├─ Process: Analyze completeness, trajectory, velocity
   └─ Output: ReflectionResult
       ├─ completeness: CompletenessAnalysis
       ├─ trajectory: TrajectoryAnalysis
       └─ recommendations: list[Recommendation]
                ├─ type: AUGMENT | OPTIMIZE | PIVOT | CONTINUE
                ├─ component_category: Optional[str]
                ├─ suggested_hypotheses: list[dict]
                └─ requires_human: bool

2. IMAGINATION PHASE (runner.py:602-640)
   ├─ Input: ReflectionResult + Foundation (Oracle, NorthStar, Context)
   ├─ Process: Claude generates hypotheses guided by reflection recommendations
   └─ Output: list[dict] (hypotheses)
       ├─ id: str
       ├─ description: str
       ├─ feasibility: float (0-1)
       ├─ north_star_alignment: float (0-1)
       ├─ estimated_effort: str
       └─ ... other fields

3. INTENT PHASE (runner.py:642-694)
   ├─ Input: list[dict] (hypotheses from IMAGINATION)
   ├─ Process:
   │  ├─ Score = feasibility * 0.4 + alignment * 0.6
   │  ├─ If score >= 0.65: approve
   │  ├─ If 0.40 <= score < 0.65: escalate (request human)
   │  └─ If score < 0.40: reject
   ├─ Handle vendor selection (two-level hypothesis system)
   └─ Output: (approved: list[dict], escalated: list[dict])

4. WORK PHASE (runner.py:696-712)
   ├─ Input: approved: list[dict] (approved hypotheses)
   ├─ Process: For each hypothesis, create a concrete task
   ├─ Call: create_task(hypothesis, oracle, context)
   └─ Output: list[tuple[dict, dict]] (task, hypothesis pairs)

5. EXECUTION PHASE (runner.py:715-748)
   ├─ Input: (task: dict, hypothesis: dict)
   ├─ Process:
   │  ├─ Call Claude to plan execution
   │  ├─ Generate realistic metrics based on system state
   │  └─ Log events to dashboard
   └─ Output: ExecutionResult
       ├─ success: bool
       ├─ metrics_delta: dict
       │   ├─ revenue: float
       │   ├─ signups: int
       │   └─ ... other metrics
       └─ errors: list[str]

6. DASHBOARD FEEDBACK
   ├─ Events logged: EventType.REVENUE, EventType.SIGNUP, etc.
   ├─ State updated: Components marked as LIVE after successful execution
   └─ Ready for next REFLECTION cycle

┌─────────────────────────────────────────────────────────────────────────────┐
│                    METRICS FLOW (Key for Feedback)                          │
└─────────────────────────────────────────────────────────────────────────────┘

ExecutionResult.metrics_delta
    ↓
dashboard.log_event(EventType.REVENUE, value=X)
dashboard.log_event(EventType.SIGNUP, value=Y)
    ↓
EventLog.append() → ".1kh/events.jsonl"
    ↓
Dashboard.compute_state() → reads all events
    ↓
state.north_star.progress_pct ← fed to REFLECTION in next cycle
```

---

## CLI Triggers for Each Phase

### IMAGINATION Phase
```bash
1kh run imagination --project /path/to/project --local
```

**Function:** `cli/commands/run.py:44-88`

**Flow:**
1. Load foundation docs (oracle, north_star, context, seeds)
2. Call `generate_hypotheses()`
3. Display hypotheses for user review
4. Confirmation before moving to INTENT

---

### INTENT Phase (usually part of cycle, not standalone)
**Integrated in cycle flow** - not typically called directly

---

### Full Cycle (all 5 loops)
```bash
1kh run cycle --demo --max 5
1kh run cycle --local --fresh
```

**Function:** `core/runner.py:271-323`

**Flow:**
1. Validates foundation exists
2. Loops until target reached or max_cycles:
   - `_run_single_cycle()` (lines 325-464)
     - REFLECTION
     - IMAGINATION
     - INTENT
     - WORK
     - EXECUTION
   - Save state and check progress

---

### REFLECTION/Status Check
```bash
1kh reflect
1kh status
```

**Function:** `cli/commands/reflect.py`, `cli/commands/status.py`

**Purpose:** Manually check trajectory without running full cycle

---

## Key Configuration & Thresholds

**Location:** `/core/runner.py` lines 118-165

```python
@dataclass
class RunnerConfig:
    """Configuration for the cycle runner."""
    mode: RunnerMode
    project_path: Path

    # Thresholds
    approval_threshold: float = 0.65  # Hypothesis score for auto-approval
    escalation_threshold: float = 0.40  # Score for human review

    # Limits
    max_cycles: int = 100
    max_hypotheses_per_cycle: int = 5
    max_tasks_per_cycle: int = 3

    # Time simulation
    days_per_cycle: int = 3  # Each cycle represents 3 days of work

    # North Star
    north_star_target: float = 1_000_000
    north_star_name: str = "$1M ARR"

    # Callbacks for UI
    on_cycle_start: Optional[Callable[[int], None]] = None
    on_cycle_end: Optional[Callable[[int, dict], None]] = None
    on_hypothesis_generated: Optional[Callable[[dict], None]] = None
    on_task_executed: Optional[Callable[[dict, ExecutionResult], None]] = None
    on_escalation: Optional[Callable[[str, dict], None]] = None
    on_progress_update: Optional[Callable[[float, float], None]] = None
    on_vendor_selection_needed: Optional[Callable[[str, list[dict]], str]] = None
    on_pivot_decision_needed: Optional[Callable[[dict], str]] = None
    on_phase_start: Optional[Callable[[str], None]] = None
    on_phase_end: Optional[Callable[[str], None]] = None
    generate_reports: bool = True
```

---

## Persistence & State Management

### Persisted State Files

```
.1kh/
├─ state/
│  └─ run_state.json          # Cycle count, hypothesis total, failures, etc.
├─ events.jsonl               # Append-only event log (one JSON per line)
├─ preferences.json           # User vendor/tech preferences
├─ system_state.json          # Component status (product, payment, channel, etc.)
└─ reports/
   ├─ cycle_001.html
   ├─ cycle_002.html
   └─ ...
```

### Run State Structure (runner.py lines 221-256)

```python
state = {
    "last_cycle": int,
    "hypotheses_total": int,
    "tasks_total": int,
    "escalations_total": int,
    "failures": int,
    "last_run_at": str (ISO datetime),
    "target_reached": bool,
    "simulated_days": int,
    "days_per_cycle": int,
}
```

---

## Data Flow Diagrams

### Simple Artifact Passing

```
REFLECTION
  │ ReflectionResult
  │ ├─ completeness.blockers: ["No payment system"]
  │ ├─ recommendations: [{type: "augment", component: "payment", ...}]
  │ └─ trajectory.is_realistic: true
  │
  ↓ (used to guide)
  │
IMAGINATION
  │ list[dict] hypotheses
  │ ├─ [0].id = "hyp-001-PAY"
  │ ├─ [0].description = "Integrate Stripe payment processing"
  │ ├─ [0].feasibility = 0.85
  │ ├─ [0].north_star_alignment = 0.99
  │ └─ ...
  │
  ↓ (passed to)
  │
INTENT
  │ (splits into two lists)
  │
  ├─ approved (score >= 0.65)
  │  └─ [{same hypothesis}, selected_vendor: "stripe"]
  │
  └─ escalated (0.40 <= score < 0.65)
     └─ (request human approval)

  ↓ (approved list fed to)
  │
WORK
  │ list[dict] tasks
  │ ├─ [0].id = "task-001-PAY"
  │ ├─ [0].hypothesis_id = "hyp-001-PAY"
  │ ├─ [0].description = "Integrate Stripe..."
  │ └─ [0].task_type = "build"
  │
  ↓ (each task fed to)
  │
EXECUTION
  │ ExecutionResult
  │ ├─ success: true
  │ ├─ metrics_delta: {revenue: 500.0, signups: 2}
  │ └─ task_id: "task-001-PAY"
  │
  ↓ (logged to)
  │
DASHBOARD
  │ Event Log (append-only)
  │ ├─ Event(type: TASK_COMPLETED, task_id: "task-001-PAY")
  │ ├─ Event(type: REVENUE, value: 500.0, task_id: "task-001-PAY")
  │ └─ Event(type: SIGNUP, value: 2, task_id: "task-001-PAY")
  │
  ↓ (aggregated, fed back to)
  │
REFLECTION (next cycle)
  │ completeness.can_generate_revenue = TRUE (because payment system now LIVE)
  │ trajectory.current_value = 500.0 (accumulated revenue)
  │ velocity_per_cycle = X (calculated from events)
  └─ ...
```

---

## Critical Design Insights for v3

### 1. Scoring is Deterministic
The INTENT phase uses a simple, explicit formula:
```
score = feasibility * 0.4 + north_star_alignment * 0.6
```

Both `feasibility` and `north_star_alignment` must be **real floats (0.0-1.0)** produced by IMAGINATION.

### 2. Metrics are the Feedback Loop
- EXECUTION must produce `metrics_delta` dict
- These metrics are logged as Events
- REFLECTION reads events to compute trajectory
- If metrics are missing, REFLECTION can't guide IMAGINATION

### 3. System Completeness Gates Possibility
- If `can_generate_revenue=False` (no payment system), execution can generate any other metrics but revenue MUST be 0
- REFLECTION must explicitly recommend AUGMENT recommendations
- IMAGINATION must prioritize fixing blockers

### 4. Two-Level Hypotheses Are Optional
- CAPABILITY level: "Enable payment processing"
- IMPLEMENTATION level: "Use Stripe"
- Not all hypotheses need both levels; vendor selection is conditional on category/preferences

### 5. Events Are Immutable
- EventLog is append-only JSONL
- Each event is immutable and timestamped
- Aggregation happens on read, not write
- Enables audit trail and replay capability

### 6. State Machines Matter
- ComponentStatus: MISSING → PLANNED → BUILDING → LIVE
- HypothesisStatus: PROPOSED → BUILDING → TESTABLE → VALIDATING → VALIDATED/INVALIDATED
- TaskStatus: PENDING → IN_PROGRESS → COMPLETED/FAILED
- RecommendationType: AUGMENT (auto) vs OPTIMIZE (auto) vs PIVOT (manual) vs CONTINUE

---

## Validation Checklist for v3

When implementing v3 layers, verify these contracts:

- [ ] REFLECTION produces `ReflectionResult` with `completeness`, `trajectory`, `recommendations`
- [ ] IMAGINATION consumes `reflection` parameter and adjusts hypothesis priorities
- [ ] IMAGINATION produces hypotheses with `feasibility` and `north_star_alignment` as floats
- [ ] INTENT applies scoring formula: `score = feasibility * 0.4 + alignment * 0.6`
- [ ] INTENT produces two lists: `approved` (score >= 0.65) and `escalated` (0.40-0.65)
- [ ] WORK produces tasks with `hypothesis_id`, `description`, `task_type`
- [ ] EXECUTION produces `ExecutionResult` with `success`, `metrics_delta`, `errors`
- [ ] Metrics dict includes at minimum: `revenue`, `signups` (if revenue system)
- [ ] Dashboard logs events: `EventType.REVENUE`, `EventType.SIGNUP`, `EventType.TASK_COMPLETED`
- [ ] Component statuses are updated: BUILDING → LIVE after successful execution
- [ ] Next REFLECTION cycle can read dashboard state and compute velocity

