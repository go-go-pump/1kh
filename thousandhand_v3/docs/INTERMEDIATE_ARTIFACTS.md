# Intermediate Artifacts Between Layers

> JSON schemas defining the data structures passed between 1KH layers.
> Thresholds and scoring formulas are initial values — calibrated with real data as v3 executes.

---

## Layer Transitions Summary

| Transition | Artifact | Structure |
|-----------|----------|-----------|
| REFLECTION → IMAGINATION | `ReflectionResult` | completeness score, trajectory analysis (velocity, trend, is_realistic), list of Recommendations (AUGMENT/OPTIMIZE/PIVOT/CONTINUE with priority) |
| IMAGINATION → INTENT | `list[Hypothesis]` | id, description, feasibility (0-1), north_star_alignment (0-1), estimated_effort, depends_on, risks |
| INTENT → WORK | `list[Hypothesis]` (approved subset) | Filtered by score formula: `feasibility * 0.4 + alignment * 0.6`. Threshold: ≥0.65 auto-approve, 0.40-0.65 escalate, <0.40 reject |
| WORK → GROOMING | `Task` (stateless) + `UserFlow` references | id, hypothesis_id, description, task_type, risk_tolerance (pre-authorized by human), estimated_tokens, user_flows served |
| GROOMING → EXECUTION | `GROOMING_HANDOFF` (stateful .md) | Full handoff document — architecture, success criteria, test execution contract, user flow references |
| EXECUTION → GROOMING | `DELIVERY_HANDOFF` (.md) | What was done, test results (summary.json), risk summary (criticality ratings), deviation assessment |
| Dashboard → REFLECTION | `Event` log (append-only) | event_type, value, timestamp, hypothesis_id, task_id |

---

## Artifact Concreteness Gradient

Artifacts get progressively more concrete as they flow through the layers:

```
ABSTRACT ──────────────────────────────────────────────→ CONCRETE

ReflectionResult → Hypothesis → Task → GROOMING_HANDOFF → DELIVERY_HANDOFF → Event
(strategic)       (a bet)      (work    (full build        (what actually    (measured
                               order)    spec)              happened)         outcome)
```

The event log closes the loop — measured outcomes feed back to REFLECTION for the next cycle.

---

## JSON Schemas

### ReflectionResult

Produced by REFLECTION, consumed by IMAGINATION. Summarizes system health and strategic direction.

```json
{
  "timestamp": "ISO-8601",
  "cycle_number": 5,
  "completeness": {
    "score": 0.75,
    "can_generate_revenue": false,
    "blockers": ["No payment system"],
    "missing_components": ["payment"],
    "building_components": ["channel"],
    "live_components": ["product", "fulfillment"]
  },
  "trajectory": {
    "current_value": 2500,
    "target_value": 10000,
    "velocity_per_cycle": 500,
    "velocity_trend": "accelerating",
    "cycles_to_goal": 15,
    "confidence": 0.6,
    "is_realistic": true
  },
  "recommendations": [
    {
      "type": "AUGMENT",
      "title": "Add payment processing",
      "description": "Cannot generate revenue without payment",
      "rationale": "Missing critical component",
      "priority": 1,
      "requires_human": false
    }
  ],
  "status": "warning",
  "summary": "Revenue growing but payment system blocking"
}
```

**Recommendation types**: AUGMENT (add missing capability), OPTIMIZE (improve existing), PIVOT (Foundation-level change — requires human), CONTINUE (stay the course).

### Hypothesis

Produced by IMAGINATION, scored by INTENT. Represents a strategic bet the system can make.

```json
{
  "id": "hyp-005-1",
  "description": "Implement Stripe payment integration for online orders",
  "rationale": "Payment is the missing component blocking revenue",
  "serves_objectives": ["$10K MRR"],
  "feasibility": 0.85,
  "north_star_alignment": 0.90,
  "estimated_effort": "days",
  "estimated_hours": 24,
  "depends_on": ["hyp-003-1"],
  "risks": ["Stripe approval timeline unknown", "PCI compliance scope"]
}
```

**Scoring formula** (initial — subject to calibration):
`score = feasibility * 0.4 + north_star_alignment * 0.6`

**Decision thresholds** (initial — subject to calibration):
- ≥0.65 → auto-approve
- 0.40-0.65 → escalate to human
- <0.40 → reject

These thresholds are starting hypotheses, not dogma. REFLECTION monitors threshold effectiveness and proposes adjustments. Human approves changes. See ARCH_V3 Section 11.6 for the preference detection system.

### Task (from WORK, pre-GROOMING)

Produced by WORK, consumed by GROOMING. Stateless — carries no project context.

```json
{
  "id": "task-005-1",
  "hypothesis_id": "hyp-005-1",
  "description": "Build Stripe payment integration with checkout flow",
  "task_type": "build",
  "estimated_tokens": { "input": 30000, "output": 15000 },
  "risk_tolerance": "proceed_with_auto_fallback",
  "user_flows": ["flow-checkout-new", "flow-checkout-existing"],
  "touches_resources": [
    { "type": "api", "identifier": "stripe", "access": "write" }
  ],
  "blocked_by": []
}
```

**task_type values**: `build` (standard feature), `fix` (bug/defect), `documentation` (doc-only change)

**risk_tolerance values** (pre-authorized by human at WORK layer):
- `proceed_with_auto_fallback` — if build fails, try alternative approach automatically
- `proceed_with_escalation` — if build fails, escalate to human
- `proceed_with_auto_approve` — if test coverage is insufficient, auto-approve anyway

**user_flows**: References to entries in the USER FLOW CATALOG. Connects this task to the journeys it serves. GROOMING uses these to write acceptance criteria; CLOSING CEREMONY uses these to verify the built system.

### UserFlow (from WORK — the Book of Life)

Produced by WORK alongside Tasks. Defines a discrete user journey through the system.

```json
{
  "id": "flow-checkout-new",
  "description": "New customer completes first purchase",
  "lifecycle": "NEW",
  "steps": [
    "Browse product catalog",
    "Add item to cart",
    "Enter shipping information",
    "Enter payment information",
    "Confirm order",
    "Receive confirmation email"
  ],
  "hypothesis_id": "hyp-005-1",
  "touches_tasks": ["task-005-1", "task-005-2"],
  "verification_mode": "playwright"
}
```

**lifecycle values**: `NEW` (first-time user), `EXISTING` (returning user with history), `RETURNING_INTERRUPTED` (user resuming abandoned session)

**verification_mode**: `playwright` (automated browser test), `manual` (human walkthrough), `mixed` (automated with manual verification steps)

### ExecutionResult

Produced by EXECUTION inside DELIVERY_HANDOFF, consumed by GROOMING. What actually happened.

```json
{
  "success": true,
  "task_id": "task-005-1",
  "hypothesis_id": "hyp-005-1",
  "duration_seconds": 1847,
  "metrics_delta": {
    "revenue": 0,
    "signups": 0,
    "feature_completion": 0.15
  },
  "test_summary": {
    "total": 8,
    "passing": 8,
    "failing": 0,
    "skipped": 0,
    "fix_iterations": 2
  },
  "risk_summary": {
    "implemented_tested_passing": 6,
    "implemented_tested_failing": 0,
    "implemented_not_testable": 1,
    "not_implemented": 1,
    "highest_untested_criticality": "MEDIUM"
  },
  "errors": [],
  "needs_human": false
}
```

### Event (append-only log)

Produced by Dashboard/EXECUTION, consumed by REFLECTION. Closes the feedback loop.

```json
{
  "event_id": "evt-2026-02-07-001",
  "timestamp": "2026-02-07T14:30:00Z",
  "event_type": "TASK_COMPLETED",
  "value": null,
  "task_id": "task-005-1",
  "hypothesis_id": "hyp-005-1",
  "metadata": {
    "triage": "FEATURE",
    "tokens_used": { "input": 28500, "output": 14200, "cost_usd": 0.41 },
    "test_results": "8/8 passing"
  }
}
```

**event_type values**: `TASK_COMPLETED`, `TASK_FAILED`, `HYPOTHESIS_APPROVED`, `HYPOTHESIS_REJECTED`, `HUMAN_DECISION`, `METRIC_UPDATE`, `ESCALATION_RESOLVED`

---

## Calibration Notes

All thresholds and scoring weights are initial values derived from v2 analysis. The calibration process:

1. **Ship with initial values** — these are reasonable starting points, not guesses
2. **REFLECTION monitors effectiveness** — tracks approval/rejection accuracy, escalation outcomes
3. **REFLECTION proposes adjustments** — "approval threshold should drop to 0.60 based on 10 cycles of data"
4. **Human approves threshold changes** — the system doesn't self-modify decision boundaries without consent
5. **Iterate** — thresholds stabilize as the system accumulates cycle data

This is the same pattern as KU's aggressive execution philosophy: start with a pragmatic default, move forward, adjust based on real outcomes.

---

*Source: v2 code analysis from `/archive/thousandhand_v2/core/` (runner.py, reflection.py, hypothesis.py, executor.py, dashboard.py)*
*Promoted from DRAFT: 2026-02-09*
