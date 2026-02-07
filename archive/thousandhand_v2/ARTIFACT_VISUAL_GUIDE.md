# ThousandHand v2: Visual Guide to Layer Artifacts

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     THOUSANDHAND v2 LAYER ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────────────────┘

                              FOUNDATION LAYER
                          (Immutable throughout cycle)
                    ┌─────────────────────────────────┐
                    │  oracle.md     (values)          │
                    │  north_star.md (goals)           │
                    │  context.md    (constraints)     │
                    └─────────────────────────────────┘

                              EVENT LOOP LAYERS
                         (5 sequential operations)

    ┌────────────────────────────────────────────────────────────────┐
    │                                                                │
    │  CYCLE N                                                       │
    │  ┌──────────────────────────────────────────────────────────┐ │
    │  │  REFLECTION (analyze)                                    │ │
    │  │  ├─ Input:  Dashboard State + Component Status          │ │
    │  │  ├─ Process: Compute completeness, trajectory, velocity │ │
    │  │  └─ Output: ReflectionResult                            │ │
    │  │            ├─ completeness: can_generate_revenue?       │ │
    │  │            ├─ trajectory: on track? realistic?          │ │
    │  │            └─ recommendations: AUGMENT/OPTIMIZE/PIVOT   │ │
    │  └──────────────────────────────────────────────────────────┘ │
    │                           ↓                                    │
    │  ┌──────────────────────────────────────────────────────────┐ │
    │  │  IMAGINATION (generate)                                  │ │
    │  │  ├─ Input:  Foundation + ReflectionResult               │ │
    │  │  ├─ Process: Claude generates hypotheses (guided)        │ │
    │  │  └─ Output: list[Hypothesis]                            │ │
    │  │            ├─ id, description, rationale                │ │
    │  │            ├─ feasibility (0-1)                         │ │
    │  │            └─ north_star_alignment (0-1)                │ │
    │  └──────────────────────────────────────────────────────────┘ │
    │                           ↓                                    │
    │  ┌──────────────────────────────────────────────────────────┐ │
    │  │  INTENT (decide)                                         │ │
    │  │  ├─ Input:  list[Hypothesis]                            │ │
    │  │  ├─ Process:                                             │ │
    │  │  │  score = feasibility * 0.4 + alignment * 0.6         │ │
    │  │  │  if score >= 0.65: approve                           │ │
    │  │  │  if 0.40 ≤ score < 0.65: escalate (ask human)        │ │
    │  │  │  if score < 0.40: reject                             │ │
    │  │  └─ Output: (approved, escalated)                       │ │
    │  │            Two lists of Hypothesis                      │ │
    │  └──────────────────────────────────────────────────────────┘ │
    │                           ↓                                    │
    │  ┌──────────────────────────────────────────────────────────┐ │
    │  │  WORK (plan)                                             │ │
    │  │  ├─ Input:  list[Hypothesis] (approved)                 │ │
    │  │  ├─ Process: Claude breaks each into concrete task      │ │
    │  │  └─ Output: list[Task]                                  │ │
    │  │            ├─ id, hypothesis_id, description            │ │
    │  │            └─ task_type (build/research/deploy/test)    │ │
    │  └──────────────────────────────────────────────────────────┘ │
    │                           ↓                                    │
    │  ┌──────────────────────────────────────────────────────────┐ │
    │  │  EXECUTION (do)                                          │ │
    │  │  ├─ Input:  list[Task]                                  │ │
    │  │  ├─ Process:                                             │ │
    │  │  │  For each task:                                      │ │
    │  │  │    1. Claude generates execution plan                │ │
    │  │  │    2. Simulate realistic metrics                     │ │
    │  │  │    3. Log events to dashboard                        │ │
    │  │  └─ Output: ExecutionResult (per task)                  │ │
    │  │            ├─ success: bool                             │ │
    │  │            ├─ metrics_delta: {revenue, signups, ...}    │ │
    │  │            └─ errors: list[str]                         │ │
    │  └──────────────────────────────────────────────────────────┘ │
    │                           ↓                                    │
    │  ┌──────────────────────────────────────────────────────────┐ │
    │  │  DASHBOARD FEEDBACK                                      │ │
    │  │  ├─ Append Events: EventLog                             │ │
    │  │  ├─ Update State: SystemState (component status)        │ │
    │  │  └─ Ready: For REFLECTION of next cycle                 │ │
    │  └──────────────────────────────────────────────────────────┘ │
    │                                                                │
    └────────────────────────────────────────────────────────────────┘
                                  ↓
                            [REPEAT CYCLE]
```

---

## Artifact Flow: Real-World Example

### Scenario: Building a SaaS with Stripe Payment Integration

```
CYCLE 1
═══════════════════════════════════════════════════════════════════════

REFLECTION OUTPUT:
─────────────────
{
  "cycle": 1,
  "completeness": {
    "score": 0.50,
    "can_generate_revenue": FALSE,  ← CRITICAL FINDING
    "blockers": ["No payment system - cannot process transactions"],
    "missing_components": ["payment"],
    "building_components": ["product"],
    "live_components": ["channel"]
  },
  "trajectory": {
    "current_value": 0.0,
    "target_value": 1000000.0,
    "velocity_per_cycle": 0.0,
    "velocity_trend": "stalled",
    "cycles_to_goal": null,
    "is_realistic": false,
    "warning": "Cannot generate revenue without payment system"
  },
  "recommendations": [
    {
      "type": "augment",                    ← Guided IMAGINATION
      "title": "Add Payment Processing",
      "priority": 1,
      "component_category": "payment",
      "suggested_hypotheses": [{
        "description": "Integrate payment processor (Stripe/PayPal/Square)"
      }]
    }
  ]
}

IMAGINATION OUTPUT:
──────────────────
[
  {
    "id": "hyp-001-PAY",
    "description": "Integrate Stripe payment processing",  ← Guided by reflection
    "rationale": "Enable customers to pay for product. Stripe has best documentation and integration ecosystem.",
    "estimated_effort": "days",
    "estimated_hours": 16,
    "feasibility": 0.85,              ← Will Claude be able to implement this?
    "north_star_alignment": 0.99,     ← Will this move us toward $1M ARR?
    "depends_on": ["hyp-003-PRD"],    ← Must have product first
    "risks": ["Rate limiting if high volume"]
  },
  {
    "id": "hyp-002-CHN",
    "description": "Launch email marketing campaign",
    "feasibility": 0.70,
    "north_star_alignment": 0.75,
  },
  // ... other hypotheses ...
]

INTENT ANALYSIS:
───────────────
For hyp-001-PAY:
  score = 0.85 * 0.4 + 0.99 * 0.6
        = 0.34 + 0.594
        = 0.934  ← WELL ABOVE 0.65 threshold
  → APPROVED ✓

For hyp-002-CHN:
  score = 0.70 * 0.4 + 0.75 * 0.6
        = 0.28 + 0.45
        = 0.73  ← ABOVE 0.65 threshold
  → APPROVED ✓

INTENT OUTPUT:
──────────────
approved = [hyp-001-PAY, hyp-002-CHN]
escalated = []

WORK OUTPUT:
────────────
[
  Task(
    id="task-001-PAY",
    hypothesis_id="hyp-001-PAY",
    description="Integrate Stripe payment processing",
    task_type="build",
    status="pending"
  ),
  Task(
    id="task-002-CHN",
    hypothesis_id="hyp-002-CHN",
    description="Set up email marketing campaign",
    task_type="build",
    status="pending"
  )
]

EXECUTION OUTPUT (per task):
────────────────────────────

task-001-PAY:
  ExecutionResult(
    success=True,
    metrics_delta={
      "revenue": 0.0,  ← No transactions yet (0 customers)
      "signups": 0
    },
    result_text="Stripe integration complete. Webhook handlers configured."
  )

  Dashboard Events Logged:
  - Event(type=TASK_COMPLETED, task_id="task-001-PAY")
  - Event(type=REVENUE, value=0.0)  ← Still 0 because no customers

  System State Updated:
  - Component(category="payment", status=LIVE)

task-002-CHN:
  ExecutionResult(
    success=True,
    metrics_delta={
      "revenue": 0.0,
      "signups": 5
    },
    result_text="Email campaign launched to 500 prospects"
  )

  Dashboard Events Logged:
  - Event(type=TASK_COMPLETED, task_id="task-002-CHN")
  - Event(type=SIGNUP, value=5)

CYCLE 1 SUMMARY:
────────────────
{
  "cycle": 1,
  "hypotheses_generated": 5,
  "hypotheses_approved": 2,
  "tasks_executed": 2,
  "tasks_succeeded": 2,
  "revenue_delta": 0.0,
  "signups_delta": 5
}


CYCLE 2
═══════════════════════════════════════════════════════════════════════

DASHBOARD STATE (fed to REFLECTION):
────────────────────────────────────
From Events Log:
  - Total signups: 5
  - Total revenue: $0
  - Component payment: LIVE ✓
  - Component product: LIVE ✓
  - Component channel: LIVE ✓
  - Component fulfillment: BUILDING

REFLECTION OUTPUT (NEW):
────────────────────────
{
  "cycle": 2,
  "completeness": {
    "score": 0.75,
    "can_generate_revenue": TRUE,  ← CHANGED! We have payment system
    "blockers": ["Missing fulfillment component"],
    "missing_components": [],
    "building_components": ["fulfillment"],
    "live_components": ["product", "payment", "channel"]
  },
  "trajectory": {
    "current_value": 0.0,
    "target_value": 1000000.0,
    "velocity_per_cycle": 0.0,
    "velocity_trend": "stalled",
    "warning": "We have payment system but not generating revenue. Check conversion rate."
  },
  "recommendations": [
    {
      "type": "optimize",
      "title": "Improve Landing Page Conversion",
      "priority": 1,
      "component_category": "channel",
      "suggested_hypotheses": [{
        "description": "A/B test landing page headline/CTA"
      }]
    }
  ]
}

IMAGINATION OUTPUT (NEW):
─────────────────────────
[
  {
    "id": "hyp-003-CRO",
    "description": "A/B test landing page to improve conversion",  ← Guided by OPTIMIZE recommendation
    "feasibility": 0.80,
    "north_star_alignment": 0.85,
  },
  {
    "id": "hyp-004-FUL",
    "description": "Build fulfillment system for digital delivery",
    "feasibility": 0.75,
    "north_star_alignment": 0.95,
  },
  // ... other hypotheses ...
]

INTENT → WORK → EXECUTION:
──────────────────────────

task-003-CRO executed:
  metrics_delta = {
    "revenue": 150.0,  ← FIRST REVENUE! (3 customers × $50)
    "signups": 12      ← Better conversion from A/B test
  }

task-004-FUL executed:
  metrics_delta = {
    "revenue": 300.0,  ← More customers completing purchase
    "signups": 15
  }

CYCLE 2 SUMMARY:
────────────────
{
  "cycle": 2,
  "revenue_delta": 450.0,
  "signups_delta": 27,
  "tasks_succeeded": 2
}

Dashboard State After Cycle 2:
  current_value: $450
  velocity_per_cycle: $225
  projected_cycles_to_goal: 4,444 cycles (unrealistic)


CYCLE 3+
════════════════════════════════════════════════════════════════════════
[Cycle continues, refining conversion, expanding channels, optimizing price, etc.]
```

---

## Data Structure Relationships

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     OBJECT RELATIONSHIP DIAGRAM                          │
└──────────────────────────────────────────────────────────────────────────┘

                              ReflectionResult
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
            CompletenessAnalysis   │   TrajectoryAnalysis
                    │              │              │
              can_generate_revenue  │   velocity_trend
              missing_components    │   cycles_to_goal
              blockers             │   confidence
                    │              │              │
                    └──────────────┼──────────────┘
                                   │
                         Recommendations: list
                                   │
                            Recommendation
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
              type: AUGMENT    priority: 1   component_category
              requires_human       │           suggested_hypotheses
                    │              │              │
                    └──────────────┴──────────────┘


                             Hypothesis (from IMAGINATION)
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                feasibility (0-1)  │   north_star_alignment (0-1)
                    │              │              │
                    └──────────────┼──────────────┘
                                   │
                         INTENT Phase: calculate score
                         score = feasibility * 0.4 + alignment * 0.6
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
              score >= 0.65                 score < 0.65
              APPROVED ✓                    if score >= 0.40:
                    │                       ESCALATE (human)
                    │                             │
                    ↓                             ↓
          (approved_list)                 (escalated_list)
                    │
                    ↓
             WORK Phase: create_task()
                    │
                    ↓
               Task (concrete)
                    │
                    ├─ id: str
                    ├─ hypothesis_id: str  ← Links back to Hypothesis
                    ├─ description: str
                    └─ task_type: str
                         │
                         ↓
                  EXECUTION Phase
                         │
                         ↓
                  ExecutionResult
                         │
        ┌────────────────┼────────────────┐
        │                │                │
      success: bool   metrics_delta    errors: list
                         │
        ┌────────────────┼────────────────┐
        │                │                │
      revenue: float  signups: int   engagement: float
        │                │                │
        └────────────────┼────────────────┘
                         │
                    Dashboard.log_event()
                         │
                    Event (append-only)
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    event_id: str    timestamp: dt   event_type: EventType
      │                │                │
      │            REVENUE          value: float
      │            SIGNUP           hypothesis_id
      │            TASK_COMPLETED   task_id
      │
    EventLog (JSONL file)
      │
      ↓
  Dashboard.compute_state()
      │
      ↓
  DashboardState (in-memory aggregation)
      │
      ├─ north_star:
      │  ├─ current_value: $450
      │  ├─ progress_pct: 0.045%
      │  └─ velocity: $225/cycle
      │
      └─ system_state:
         ├─ Component(payment, LIVE)
         ├─ Component(product, LIVE)
         ├─ Component(channel, LIVE)
         └─ Component(fulfillment, BUILDING)
           │
           └─ Fed back to REFLECTION next cycle


SystemState (persistent)
    │
    ├─ mode: BUSINESS
    ├─ components: list[BusinessComponent]
    │  ├─ name: str
    │  ├─ category: str (product, payment, channel, fulfillment)
    │  ├─ status: ComponentStatus (MISSING, PLANNED, BUILDING, LIVE)
    │  ├─ hypothesis_ids: list  ← Links back to Hypotheses
    │  └─ task_ids: list         ← Links back to Tasks
    │
    ├─ active_hypotheses: list
    ├─ completed_hypotheses: list
    ├─ active_tasks: list
    └─ completed_tasks: list
```

---

## Decision Tree: INTENT Phase

```
     Hypothesis received
            │
            ↓
    Calculate Score:
    score = feasibility * 0.4 + alignment * 0.6
            │
            ├─────────────────┬──────────────────┬──────────────┐
            │                 │                  │              │
       score >= 0.65      0.40 <= score < 0.65  score < 0.40   │
            │                 │                  │              │
            ↓                 ↓                  ↓              │
        APPROVED          ESCALATE            REJECTED         │
            │              (ask human)          (reject)        │
            │                 │                  │              │
            │                 ↓                  │              │
            │          Does human              │              │
            │          approve?                │              │
            │              │                    │              │
            │          ┌───┴───┐               │              │
            │          │       │               │              │
            │         YES     NO              │              │
            │          │       │               │              │
            │          ↓       ↓               │              │
            │       APPROVED REJECTED         │              │
            │          │       │               │              │
            │          ↓       ↓               ↓              │
            └─────────────────────────────────────────────────┘
                              │
                              ↓
                    Check for two-level hypotheses:
                    Does hypothesis need vendor selection?
                              │
                         ┌────┴────┐
                         │         │
                        YES       NO
                         │         │
                         ↓         │
                    Ask user for  │
                    vendor choice │
                    (or use pref) │
                         │         │
                    Attach to:    │
                    impl_hyp      │
                         │         │
                         └────┬────┘
                              │
                              ↓
                    approved_list.append(hypothesis)
                              │
                              ↓
                    WORK phase: create_task()
```

---

## Metric Calculation Example

### Real Metrics (based on system state)

```python
def _generate_realistic_metrics(task, hypothesis):
    """
    Generate realistic metrics for local/dev mode.
    CRITICAL: Metrics depend on system state!
    """
    state = SystemStateManager(project_path).load()

    # Base assumptions
    total_signups = get_signup_count_from_events()  # e.g., 27 after cycle 2
    current_revenue = get_revenue_from_events()     # e.g., $450 after cycle 2

    # Metric gates based on completeness

    # Gate 1: No payment system = NO revenue possible
    if not state.is_component_live("payment"):
        return {"revenue": 0.0, "signups": 0}

    # Gate 2: No channel = minimal signups (organic only)
    if not state.is_component_live("channel"):
        base_signups = 1  # Very rare organic
    else:
        base_signups = random.randint(5, 20)

    # Gate 3: No product = no fulfillment = no revenue conversion
    if not state.is_component_live("product"):
        return {"revenue": 0.0, "signups": base_signups}

    # Gate 4: No fulfillment = customer acquired but can't deliver
    # Revenue = 0, but signups count
    if not state.is_component_live("fulfillment"):
        return {
            "revenue": 0.0,
            "signups": base_signups
        }

    # All gates passed: realistic revenue possible
    conversion_rate = 0.10  # 10% of signups convert to customers
    customers = int(base_signups * conversion_rate)
    price_per_customer = 50.0
    revenue = customers * price_per_customer

    return {
        "revenue": revenue,
        "signups": base_signups,
        "conversion": conversion_rate
    }

# Examples
Example 1: Payment system missing (Cycle 1)
├─ state.is_component_live("payment") = False
└─ return {"revenue": 0.0, "signups": 0}

Example 2: Payment + Product + Channel live, Fulfillment building (Cycle 1.5)
├─ state.is_component_live("payment") = True
├─ state.is_component_live("channel") = True
├─ state.is_component_live("product") = True
├─ state.is_component_live("fulfillment") = False
└─ return {"revenue": 0.0, "signups": 12}

Example 3: All systems live (Cycle 2+)
├─ state.is_component_live("payment") = True
├─ state.is_component_live("channel") = True
├─ state.is_component_live("product") = True
├─ state.is_component_live("fulfillment") = True
├─ base_signups = 15
├─ conversion_rate = 0.10
├─ customers = 1 (rounded down from 1.5)
├─ price = $50
└─ return {"revenue": 50.0, "signups": 15}
```

---

## Component Lifecycle State Machine

```
         ┌─────────────────────────────────────┐
         │     ComponentStatus Transitions     │
         └─────────────────────────────────────┘

        ┌─────────────┐
        │   MISSING   │  ← Initial state (not defined, not planned)
        └──────┬──────┘
               │ (REFLECTION recommends AUGMENT)
               │ (user/system plans component)
               ↓
        ┌─────────────┐
        │   PLANNED   │  ← Defined, not started
        └──────┬──────┘
               │ (WORK phase: task created)
               ↓
        ┌─────────────┐
        │  BUILDING   │  ← Work in progress
        └──────┬──────┘
               │ (EXECUTION phase: task succeeds)
               ↓
        ┌─────────────┐
        │    LIVE     │  ← Deployed and functional ✓
        └──────┬──────┘
               │ (REFLECTION detects failure)
               ↓
        ┌─────────────┐
        │   BROKEN    │  ← Was live, now broken
        └──────┬──────┘
               │ (WORK phase: fix task)
               ↓
        ┌─────────────┐
        │   LIVE      │  ← Restored
        └─────────────┘

Revenue gates depend on component transitions:
- Product: MISSING or BUILDING  → revenue must be 0
- Payment: MISSING or BUILDING  → revenue must be 0
- Channel: MISSING or BUILDING  → signups must be 0 or minimal
- Fulfillment: MISSING or BUILDING → revenue must be 0

Only when ALL components are LIVE can full revenue flow.
```

---

## Event Log Structure Over Time

```
Cycle 1:
────────
.1kh/events.jsonl
Line 1: {"event_type":"hypothesis_created","hypothesis_id":"hyp-001-PAY",...}
Line 2: {"event_type":"hypothesis_accepted","hypothesis_id":"hyp-001-PAY",...}
Line 3: {"event_type":"task_created","task_id":"task-001-PAY",...}
Line 4: {"event_type":"task_completed","task_id":"task-001-PAY",...}
Line 5: {"event_type":"revenue","value":0.0,"task_id":"task-001-PAY",...}
Line 6: {"event_type":"hypothesis_created","hypothesis_id":"hyp-002-CHN",...}
...
Line N: {"event_type":"cycle_completed","cycle":1,...}

Cycle 2:
────────
(APPEND to same file)
Line N+1: {"event_type":"hypothesis_created","hypothesis_id":"hyp-003-CRO",...}
...
Line M: {"event_type":"revenue","value":150.0,"task_id":"task-003-CRO",...}
Line M+1: {"event_type":"signup","value":12,"task_id":"task-003-CRO",...}
...

Aggregation (done at runtime):
──────────────────────────────
EventLog.read_by_type(EventType.REVENUE)
  → Sum all REVENUE events: 0 + 150 + 300 + ... = $450

EventLog.read_by_type(EventType.SIGNUP)
  → Count all SIGNUP events: 5 + 12 + 15 + ... = 32

Dashboard.compute_state()
  → current_value = 450.0
  → velocity_per_cycle = (450 - 0) / 2 = 225.0
  → cycles_to_goal = (1000000 - 450) / 225.0 ≈ 4,443

Persistence benefits:
✓ Immutable audit trail
✓ Replay capability
✓ No aggregation errors
✓ Can recompute from raw data
```

---

## Configuration & Tuning Parameters

```
.1kh/config.json or RunnerConfig()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Approval Thresholds:
  approval_threshold: 0.65          Hypothesis score for auto-approval
  escalation_threshold: 0.40        Score for requesting human review

  Scoring formula: score = feasibility * 0.4 + alignment * 0.6

  Adjusting these:
  ├─ Higher approval_threshold (0.75): Pickier, fewer approved
  ├─ Lower approval_threshold (0.50): More aggressive
  ├─ Higher escalation_threshold (0.50): More human prompts
  └─ Lower escalation_threshold (0.25): Fewer escalations

Limits:
  max_cycles: 100                   Stop after N cycles
  max_hypotheses_per_cycle: 5       Max hypotheses to generate
  max_tasks_per_cycle: 3            Max tasks to execute per cycle

  Adjusting these:
  ├─ Higher max_hypotheses: More exploration, slower
  ├─ Lower max_hypotheses: Faster, less exploration
  ├─ Higher max_tasks: Execute more per cycle, faster progress
  └─ Lower max_tasks: More conservative, slower progress

Time Simulation:
  days_per_cycle: 3                 Each cycle represents N days of work

  Adjusting this:
  ├─ Higher value: "Slower" time progression, same cycle count
  ├─ Lower value: "Faster" time progression
  └─ Useful for forecasting time-to-goal

North Star:
  north_star_name: "$1M ARR"
  north_star_target: 1000000.0

  Dashboard computes:
  ├─ current_value: 450.0
  ├─ progress_pct: 0.045%
  └─ cycles_to_goal: 4443
```

---

## Error Handling & Recovery

```
Errors can occur at each layer:
══════════════════════════════════

REFLECTION Phase:
├─ Dashboard is empty (first run)
│  └─ Recommendation: AUGMENT (foundation exists, no metrics yet)
├─ All metrics are 0
│  └─ Recommendation: AUGMENT (missing critical component)
└─ Metrics declining
   └─ Recommendation: PIVOT (current approach failing)

IMAGINATION Phase:
├─ No API key configured
│  └─ Error: "ANTHROPIC_API_KEY not found"
├─ Claude returns invalid JSON
│  └─ Error: Logged, mock hypotheses generated instead
└─ Foundation documents missing
   └─ Error: "oracle.md not found"

INTENT Phase:
├─ No hypotheses to evaluate
│  └─ Result: approved=[], escalated=[]
├─ Escalation requires human decision (score 0.40-0.65)
│  └─ Action: Call human_responder.request_approval()
└─ Two-level hypothesis needs vendor choice
   └─ Action: Call on_vendor_selection_needed callback

WORK Phase:
├─ Cannot create task from hypothesis
│  └─ Error: Logged, hypothesis skipped
└─ Task creation times out
   └─ Error: ExecutionResult with success=False

EXECUTION Phase:
├─ Claude plan generation fails
│  └─ Metric: metrics_delta = {}, success = False
├─ Metrics show component missing
│  └─ Gate: revenue = 0.0 (component status check)
└─ Task completes but no metric improvement
   └─ Analysis: Check REFLECTION for "plateau" or "stalled"

Recovery Strategy:
────────────────
1. Check logs: `1kh logs --recent`
2. Verify foundation: `1kh status --foundation`
3. Check events: Review .1kh/events.jsonl
4. Reset state: `1kh run cycle --fresh` (clear run_state.json)
5. Manual reflection: `1kh reflect`
```

