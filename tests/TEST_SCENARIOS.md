# Test Scenario Coverage Matrix

This document defines the test scenarios we need to cover before moving to the EXECUTION layer.

## Test Layers

| Layer | Claude | Human | Dashboard | Execution | Speed | Purpose |
|-------|--------|-------|-----------|-----------|-------|---------|
| 1 | Mock | N/A | N/A | N/A | <1s | Unit tests |
| 2a | Mock | Mock (simple) | Mock (fixed) | Mock | <5s | Deterministic happy/sad paths |
| 2b | Mock | Mock (nuanced) | Mock (events) | Mock | <10s | Edge cases, complex scenarios |
| 3 | Real | Mock (nuanced) | Mock (events) | Mock | ~30s | Claude behavior validation |
| 4 | Real | Real (decisions) | Mock (events) | Mock | Manual | Human decision testing |

### Layer Definitions

**Mock Human (simple)**: Configurable patterns - "always_approve", "always_reject", "prioritize_first"
**Mock Human (nuanced)**: Scenario-based responses - delays, partial approvals, asks for clarification, makes mistakes
**Mock Dashboard (fixed)**: Static metrics that don't change - good for testing IMAGINATION reads
**Mock Dashboard (events)**: Event log that accumulates, aggregates computed - tests feedback loop

---

## Layer 2: Deterministic Dry Runs

### Happy Path Scenarios

| ID | Scenario | Expected Outcome |
|----|----------|------------------|
| H1 | Single hypothesis → task → execution → metrics improve | North Star progress shown on dashboard |
| H2 | Multiple hypotheses, no conflicts | All execute in parallel, metrics aggregate |
| H3 | Multiple hypotheses with dependencies | Execute in correct order (depends_on respected) |
| H4 | Hypothesis evaluation improves scores | Re-evaluated hypothesis shows updated feasibility |
| H5 | Multi-cycle run: 3 cycles of IMAGINATION→INTENT→WORK | Dashboard shows cumulative progress |
| H6 | Metric milestone reached | System recognizes North Star achieved |

### Sad Path Scenarios

| ID | Scenario | Expected Outcome |
|----|----------|------------------|
| S1 | Hypothesis violates Oracle | Rejected with clear reason, not executed |
| S2 | Two hypotheses conflict on same resource | INTENT detects, escalates to human |
| S3 | Task execution fails | Error captured, hypothesis marked failed, system continues |
| S4 | All hypotheses have low confidence | Escalation to human for guidance |
| S5 | Task requires human action | Blocked, escalation created, waits for response |
| S6 | Metrics go DOWN after task | IMAGINATION generates corrective hypotheses |
| S7 | Repeated failures on same hypothesis | System learns, deprioritizes or abandons |
| S8 | Resource lock stuck (crashed task) | Manual release works, queue processes |
| S9 | API error during hypothesis generation | Graceful failure, retryable |
| S10 | Budget/time constraint exceeded | System pauses, escalates |

### Human Interaction Scenarios

| ID | Scenario | Human Response | Expected Outcome |
|----|----------|----------------|------------------|
| HI1 | Escalation: conflicting hypotheses | "Prioritize hyp-001" | hyp-001 executes, hyp-002 queued |
| HI2 | Escalation: low confidence | "Try hyp-003 anyway" | hyp-003 proceeds despite low score |
| HI3 | Escalation: task needs approval | "Approved" | Task executes |
| HI4 | Escalation: task needs approval | "Rejected" | Task cancelled, alternative sought |
| HI5 | Escalation: stuck, need guidance | "Try X instead" | New hypothesis injected |
| HI6 | Human provides new seed | "What about Y?" | Seed added, processed in IMAGINATION |
| HI7 | Human overrides metric | "Actually we made $5000" | Dashboard updated, IMAGINATION sees new data |

---

## Layer 3: Real Claude Validation

### Guardrails
- Max tokens per session: 50,000
- Max cycles: 5
- Max time: 5 minutes
- Auto-stop if same hypothesis generated 3x

### Claude Behavior Tests

| ID | Scenario | What We're Testing |
|----|----------|-------------------|
| C1 | Vague North Star | Does Claude ask for clarification or make reasonable assumptions? |
| C2 | Conflicting Oracle values | Does Claude flag the conflict? |
| C3 | Impossible timeline | Does Claude push back or generate unrealistic hypotheses? |
| C4 | Metrics show failure | Does Claude generate meaningfully different hypotheses? |
| C5 | Resource exhaustion | Does Claude respect budget constraints? |
| C6 | Repeated same hypothesis | Does Claude recognize it's spinning? |

---

## Dashboard & Metrics Architecture

### Metric Types

**1. Point-in-Time Metrics (Boolean/State)**
- Is feature X deployed? (boolean)
- Current system status (enum: running/paused/error)
- Number of active hypotheses (count at moment)
- Current resource locks (count at moment)

**2. Aggregate Metrics (Computed from Event Log)**
- Total revenue (sum of transactions)
- Email signups (count of signup events)
- Conversion rate (signups / visitors)
- Hypothesis success rate (validated / total)

**3. Time-Series Considerations**
Each aggregate needs to support time filtering:
- Hourly, Daily, Weekly, Monthly, Yearly, Lifetime
- For v1: Lifetime only (simplest)
- For v2: Configurable time windows

### Data Model

```
Event Log (append-only)
├── event_id: uuid
├── timestamp: datetime
├── event_type: string (e.g., "revenue", "signup", "task_completed")
├── value: float (e.g., 99.00 for revenue, 1 for count)
├── metadata: dict (e.g., {"hypothesis_id": "hyp-001", "task_id": "task-001"})
└── source: string ("system" | "human" | "mock")

Dashboard State (computed/cached)
├── north_star_progress: dict[objective_id → current_value]
├── hypothesis_stats: dict[hypothesis_id → {status, tasks, metrics_delta}]
├── cycle_history: list[{cycle_num, hypotheses, tasks, metrics_before, metrics_after}]
├── pending_escalations: list[escalation]
└── computed_at: datetime
```

### Storage Strategy

**v1 (Mock/Testing)**
- Event log: JSON file (`.1kh/events.jsonl` - one JSON per line)
- Dashboard state: JSON file (`.1kh/dashboard.json`)
- CLI reads files, displays summary

**v2 (Production)**
- Event log: SQLite or time-series DB
- Dashboard state: Computed on-demand or cached with TTL
- Web UI reads from DB/cache

### Dashboard Views

**CLI View (`1kh status`)**
```
🎯 North Star: $1M ARR by Dec 2025
   └─ Current: $12,450 (1.2%)

📊 Active Hypotheses: 3
   └─ hyp-001: Building landing page [EXECUTING]
   └─ hyp-002: Payment integration [QUEUED]
   └─ hyp-003: Email campaign [PROPOSED]

📈 Last 24h:
   └─ +47 signups, +$450 revenue, 2 tasks completed

⚠️  Pending Escalations: 1
   └─ ESC-001: hyp-002 conflicts with hyp-003 [AWAITING]
```

**File View (`.1kh/dashboard.json`)**
```json
{
  "computed_at": "2025-01-31T12:00:00Z",
  "north_star": {
    "objective": "$1M ARR",
    "deadline": "2025-12-31",
    "current_value": 12450,
    "progress_pct": 1.2
  },
  "metrics": {
    "lifetime": {"revenue": 12450, "signups": 847, "conversions": 12},
    "last_24h": {"revenue": 450, "signups": 47, "conversions": 1}
  },
  "hypotheses": [...],
  "escalations": [...],
  "cycle_count": 15
}
```

### Mock Dashboard Iterations

**Iteration 1: Fixed Mock**
- Static `dashboard.json` with fixed values
- Good for testing IMAGINATION reads dashboard
- No event log, no aggregation

**Iteration 2: Event-Driven Mock**
- Mock execution writes events to `events.jsonl`
- Dashboard computed from events
- Tests feedback loop works
- 10-1000 events per test scenario

**Iteration 3: Live (Future)**
- Real execution writes events
- Background job computes dashboard every N minutes
- Cache locally, sync to DB

### Dashboard Requirements

**Current State**
- [ ] North Star objectives and current progress (%)
- [ ] Active hypotheses with status
- [ ] Current/recent tasks with status
- [ ] Resource locks (if any)
- [ ] Pending escalations

**History**
- [ ] Cycle history (what happened in each cycle)
- [ ] Metric trends over time (from event log)
- [ ] Hypothesis success/failure rates
- [ ] Time breakdown (system/human wait/human work)

**Learning**
- [ ] What worked (validated hypotheses)
- [ ] What didn't (invalidated hypotheses)
- [ ] Patterns noticed (e.g., "3 hypotheses about X all failed")

---

## Mock Data Requirements

### Mock Execution Results
Must generate realistic outcomes:
```python
{
    "task_id": "task-001",
    "status": "completed",
    "outputs": {
        "files_created": ["landing_page.html"],
        "deployments": ["staging.example.com"],
    },
    "metrics_delta": {
        "email_signups": +47,
        "page_views": +1200,
        "revenue": +0,  # Not yet
    },
    "duration_seconds": 3600,
    "cost_dollars": 0.50,
}
```

### Mock Human Responses

**Layer 2a: Simple Patterns**
```python
MockHumanSimple(
    response_delay=0,  # Instant for testing
    patterns={
        "conflict_resolution": "prioritize_first",  # or "prioritize_highest_score", "reject_both"
        "approval_requests": "always_approve",      # or "always_reject", "approve_if_score_above_0.7"
        "guidance_requests": "provide_default",     # or "provide_empty", "ask_clarification"
    }
)
```

**Layer 2b: Nuanced Scenarios**
```python
MockHumanNuanced(
    response_delay=2.0,  # Simulate thinking time
    scenarios={
        # Scenario-based responses
        "first_escalation": "approve",
        "second_escalation": "reject_with_reason",
        "third_escalation": "ask_for_more_info",
        "after_failure": "try_alternative",
        "budget_exceeded": "pause_and_review",
    },
    behaviors={
        "typo_rate": 0.05,           # 5% of responses have typos
        "misunderstand_rate": 0.1,   # 10% misunderstand the question
        "delay_variance": 0.5,       # ±50% on response delay
        "abandon_rate": 0.02,        # 2% never respond (timeout)
    }
)
```

**Layer 4: Real Human (Decisions Only)**
```python
RealHumanDecisions(
    # For testing, we only ask for DECISIONS, not actual work
    decision_types=[
        "approve_or_reject",    # Binary choice
        "prioritize",           # Order a list
        "select_option",        # Choose from options
        "provide_guidance",     # Free text input
    ],
    # Actual work (e.g., "register business on site X") is mocked
    work_is_mocked=True,
)
```

### Mock Metric Progression
Realistic growth curves:
```python
MockMetrics(
    north_star="$1M ARR",
    starting_value=0,
    progression="exponential",  # or "linear", "stepwise"
    noise=0.1,  # 10% random variation
    failure_rate=0.2,  # 20% of tasks don't improve metrics
)
```

---

## Coverage Gaps to Address

Before building these tests, we should verify:

1. **INTENT Loop**
   - [ ] Does it actually detect conflicts correctly? (tested)
   - [ ] Does it generate escalations? (needs test)
   - [ ] Does it respect depends_on ordering? (needs test)
   - [ ] Does it handle human responses? (not implemented)

2. **WORK Loop**
   - [ ] Does it respect resource locks? (tested)
   - [ ] Does it queue blocked tasks? (tested)
   - [ ] Does it release locks on failure? (tested)
   - [ ] Does it retry failed tasks? (needs test)
   - [ ] Does it report metrics? (not implemented)

3. **Cross-Loop**
   - [ ] Does IMAGINATION receive dashboard data? (not implemented)
   - [ ] Does the cycle actually loop? (not implemented)
   - [ ] Is state persisted between cycles? (partial)

---

## Next Steps

1. Review this matrix - are we missing scenarios?
2. Identify which existing tests cover which scenarios
3. Build missing unit tests for coverage gaps
4. Then build Layer 2 infrastructure (mocks + dashboard)
5. Then implement `1kh run cycle --demo`
