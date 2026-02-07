# ThousandHand v2: Layer Artifacts Documentation

This directory now contains comprehensive documentation of the **intermediate artifacts** that flow between the 5 loops in ThousandHand v2.

## Quick Reference

Three documents define the complete artifact system:

### 1. **LAYER_ARTIFACTS.md** - Main Specification
The authoritative definition of what flows between each layer.

**Contains:**
- REFLECTION → IMAGINATION: `ReflectionResult` with completeness, trajectory, recommendations
- IMAGINATION → INTENT: `list[dict]` hypotheses with feasibility & alignment scores
- INTENT → WORK: Split into `(approved, escalated)` based on scoring formula
- WORK → EXECUTION: `list[Task]` with concrete action items
- EXECUTION → Dashboard: `ExecutionResult` with success, metrics_delta, errors
- Dashboard → REFLECTION (next cycle): Aggregated events as state

**Key sections:**
- Complete dataclass definitions with fields and types
- Scoring formula: `score = feasibility * 0.4 + north_star_alignment * 0.6`
- Component status transitions: MISSING → PLANNED → BUILDING → LIVE
- Metrics gates: What prevents revenue from flowing
- Two-level hypothesis system: CAPABILITY vs IMPLEMENTATION

### 2. **ARTIFACT_TECHNICAL_REFERENCE.md** - Implementation Guide
Concrete code examples and imports for v3 implementation.

**Contains:**
- File locations and import statements for each module
- Complete function signatures
- JSON serialization formats (events.jsonl, run_state.json, system_state.json)
- Code examples showing how to:
  - Create and log events
  - Execute a task and get results
  - Query the dashboard state
  - Validate cycle output
- Debugging/inspection commands

### 3. **ARTIFACT_VISUAL_GUIDE.md** - Diagrams & Examples
Visual representations and real-world scenarios.

**Contains:**
- System architecture diagram
- Real SaaS example (Stripe payment integration):
  - Cycle 1: Can't generate revenue (no payment system)
  - Cycle 2: Revenue flows after payment system live
  - Cycle 3+: Optimization and growth
- Object relationship diagrams
- Decision trees (INTENT phase logic)
- Data structure relationships
- Component lifecycle state machine
- Event log evolution over time
- Configuration & tuning parameters
- Error handling & recovery strategies

## What Changed from v1 to v2 (This Analysis)

### Explicit Artifacts
v2 **formalizes** what flows between layers:
- **Hypothesis structure:** `id`, `description`, `feasibility` (0-1), `north_star_alignment` (0-1), and more
- **Scoring logic:** No magic; explicit formula `feasibility * 0.4 + alignment * 0.6`
- **Component tracking:** System state knows what's LIVE, BUILDING, PLANNED, MISSING
- **Event-based feedback:** Immutable append-only event log

### Two-Level Hypotheses
- **Level 1 (CAPABILITY):** "Enable payment processing" (technology-agnostic)
- **Level 2 (IMPLEMENTATION):** "Use Stripe" (technology-specific)
- Vendor selection can be preference-driven, user-driven, or default

### Metrics Are Gated
- No payment system = revenue MUST be 0 (not estimated, literally impossible)
- No channel = signups must be minimal (organic only)
- No fulfillment = revenue 0 (customer acquired but can't deliver)

### Feedback Loop is Explicit
- Events flow: EXECUTION → Dashboard
- State computed: Dashboard aggregates events
- Fed back to: REFLECTION reads state for next cycle
- No magic; complete audit trail in `.1kh/events.jsonl`

## v3 Implementation Checklist

When building v3, ensure these contracts are honored:

### REFLECTION Output
- [ ] Returns `ReflectionResult` with `completeness`, `trajectory`, `recommendations`
- [ ] Recommendations include `type` (AUGMENT | OPTIMIZE | PIVOT | CONTINUE)
- [ ] Completeness includes `can_generate_revenue` flag
- [ ] Trajectory includes `is_realistic` and `cycles_to_goal` estimate

### IMAGINATION Output
- [ ] Produces list of hypotheses
- [ ] Each hypothesis has `feasibility: float` (0.0-1.0)
- [ ] Each hypothesis has `north_star_alignment: float` (0.0-1.0)
- [ ] Hypotheses can have optional `needs_vendor_decision` flag (for two-level system)

### INTENT Logic
- [ ] Applies formula: `score = feasibility * 0.4 + alignment * 0.6`
- [ ] Approves if `score >= 0.65`
- [ ] Escalates if `0.40 <= score < 0.65`
- [ ] Rejects if `score < 0.40`
- [ ] Returns tuple: `(approved: list[dict], escalated: list[dict])`
- [ ] Handles vendor selection for two-level hypotheses

### WORK Output
- [ ] Creates tasks from approved hypotheses
- [ ] Task has: `id`, `hypothesis_id`, `description`, `task_type`
- [ ] Returns list of (task, hypothesis) tuples for EXECUTION

### EXECUTION Output
- [ ] Returns `ExecutionResult` with:
  - [ ] `success: bool`
  - [ ] `metrics_delta: dict` with `revenue`, `signups`, etc.
  - [ ] `errors: list[str]`
  - [ ] `task_id`, `hypothesis_id` for tracing
- [ ] Metrics respect component gates (no revenue if payment not LIVE)
- [ ] Logs events to dashboard

### Dashboard Integration
- [ ] Appends events to EventLog (immutable)
- [ ] Events have: `timestamp`, `event_type`, `value`, `hypothesis_id`, `task_id`
- [ ] Aggregates events to compute state
- [ ] Returns aggregated state for REFLECTION

### State Persistence
- [ ] Saves component status to `system_state.json`
- [ ] Saves run state to `run_state.json`
- [ ] Appends events to `events.jsonl`
- [ ] Can replay/recompute from persisted data

## File Structure for v3 Reference

Use these as exact specifications:

```
Core Interfaces:
├─ core/runner.py
│  ├─ ExecutionResult (lines 94-106)
│  ├─ RunnerConfig (lines 118-165)
│  └─ CycleRunner (lines 185+)
│
├─ core/reflection.py
│  ├─ ReflectionResult (lines 100-143)
│  ├─ CompletenessAnalysis (lines 89-97)
│  └─ TrajectoryAnalysis (lines 75-86)
│
├─ core/models.py
│  ├─ Hypothesis (lines 672-689)
│  ├─ Task (lines 692-710)
│  └─ BranchStatus, TaskStatus, HypothesisStatus (enums)
│
├─ core/dashboard.py
│  ├─ Event (lines 75-137)
│  ├─ EventType (lines 30-73)
│  └─ EventLog (lines 143-206)
│
├─ core/system_state.py
│  ├─ SystemState (lines 130-176)
│  ├─ BusinessComponent (lines 54-89)
│  └─ ComponentStatus (lines 41-48)
│
├─ core/hypothesis.py
│  ├─ VendorSelection (lines 92-97)
│  └─ HypothesisLevel (lines 24-27)
│
└─ temporal/activities/
   ├─ imagination.py: Hypothesis dataclass (lines 58-100+)
   └─ work.py: Task dataclass (lines 44-59)
```

## Key Numbers to Remember

- **Approval threshold:** 0.65 (must meet this to auto-approve)
- **Escalation threshold:** 0.40 (must meet this to request human approval)
- **Feasibility weight:** 0.4 (40% of score)
- **Alignment weight:** 0.6 (60% of score)
- **Max hypotheses per cycle:** 5 (default, tunable)
- **Max tasks per cycle:** 3 (default, tunable)
- **Days per cycle:** 3 (for time estimation, tunable)
- **Default North Star target:** $1,000,000 ARR

## Testing & Validation

### Validate Hypothesis Structure
```python
assert isinstance(hyp["feasibility"], float)
assert 0.0 <= hyp["feasibility"] <= 1.0
assert isinstance(hyp["north_star_alignment"], float)
assert 0.0 <= hyp["north_star_alignment"] <= 1.0
assert "id" in hyp
assert "description" in hyp
```

### Validate INTENT Scoring
```python
feasibility = hyp["feasibility"]
alignment = hyp["north_star_alignment"]
score = feasibility * 0.4 + alignment * 0.6
assert score >= 0.0 and score <= 1.0

if score >= 0.65:
    assert hyp in approved_list
elif score >= 0.40:
    assert hyp in escalated_list
else:
    assert hyp not in approved_list
    assert hyp not in escalated_list
```

### Validate ExecutionResult
```python
assert isinstance(result.success, bool)
assert isinstance(result.metrics_delta, dict)
assert isinstance(result.errors, list)
if "revenue" in result.metrics_delta:
    assert isinstance(result.metrics_delta["revenue"], (int, float))
```

### Validate Event Log
```python
from core.dashboard import EventLog, EventType

log = EventLog(project_path)
events = log.read_all()
assert all(isinstance(e.timestamp, datetime) for e in events)
assert all(isinstance(e.event_type, EventType) for e in events)
assert all(isinstance(e.value, (int, float)) for e in events)
```

## Common Pitfalls to Avoid

1. **Don't hardcode scores:** Always compute from `feasibility * 0.4 + alignment * 0.6`
2. **Don't skip metrics:** EXECUTION must produce `metrics_delta` dict
3. **Don't ignore component gates:** Check if payment/channel/fulfillment/product are LIVE before allowing metrics
4. **Don't lose events:** EventLog is append-only; never modify or delete events
5. **Don't mutate frozen state:** Component status changes must be persisted
6. **Don't assume vendor selection:** Use preferences or ask user; don't hardcode "use Stripe"
7. **Don't lose hypothesis-task linking:** Keep `hypothesis_id` in every task and event

## Questions for v3 Design

1. **Distributed execution:** Will v3 use Temporal workflows or async/await?
2. **Persistence backend:** Will v3 use JSONL (like v2) or database (SQL, MongoDB)?
3. **Claude integration:** Will v3 cache Claude responses? Use different model?
4. **Multi-user:** Does v3 support multiple simultaneous projects? Shared resources?
5. **Metrics customization:** Can users define custom metric gates (not just payment/channel)?

---

**Generated from:** `/sessions/busy-peaceful-keller/mnt/projects/1KH/archive/thousandhand_v2/`
**Analysis Date:** 2025-02-07
**ThousandHand Version Analyzed:** v2
