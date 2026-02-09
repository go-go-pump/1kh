# DRAFT — Intermediate Artifacts Between Layers

> **STATUS: DRAFT — needs calibration with real data before stamping into ARCH_V3.md**
> Thresholds, scoring formulas, and specific structures are placeholders from v2.
> These will be refined as v3 executes real cycles.

---

## Layer Transitions Summary

| Transition | Artifact | Structure |
|-----------|----------|-----------|
| REFLECTION → IMAGINATION | `ReflectionResult` | completeness score, trajectory analysis (velocity, trend, is_realistic), list of Recommendations (AUGMENT/OPTIMIZE/PIVOT/CONTINUE with priority) |
| IMAGINATION → INTENT | `list[Hypothesis]` | id, description, feasibility (0-1), north_star_alignment (0-1), estimated_effort, depends_on, risks |
| INTENT → WORK | `list[Hypothesis]` (approved subset) | Filtered by score formula: `feasibility * 0.4 + alignment * 0.6`. Threshold: ≥0.65 auto-approve, 0.40-0.65 escalate, <0.40 reject |
| WORK → GROOMING | `Task` (stateless) | id, hypothesis_id, description, task_type, risk_tolerance (pre-authorized by human), estimated_tokens |
| GROOMING → EXECUTION | `REQ_HANDOFF` (stateful .md) | Full handoff document — architecture, implementation, tests, success criteria in Given/When/Then |
| EXECUTION → GROOMING | `DELIVERY_HANDOFF` (.md) | What was done, test results (summary.json), risk summary (criticality ratings), deviation assessment |
| Dashboard → REFLECTION | `Event` log (append-only) | event_type, value, timestamp, hypothesis_id, task_id |

---

## Key Insight

Artifacts get progressively more concrete as they flow through the layers:

```
ABSTRACT ──────────────────────────────────────────→ CONCRETE

ReflectionResult → Hypothesis → Task → REQ_HANDOFF → DELIVERY_HANDOFF → Event
(strategic)       (a bet)      (work    (full build   (what actually    (measured
                               order)    spec)         happened)         outcome)
```

The event log closes the loop — measured outcomes feed back to REFLECTION for the next cycle.

---

## Structures from v2 Code (Reference Only)

### ReflectionResult

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

### Hypothesis

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

**Scoring formula (PLACEHOLDER — needs calibration):**
`score = feasibility * 0.4 + north_star_alignment * 0.6`

**Thresholds (PLACEHOLDER):**
- ≥0.65 → auto-approve
- 0.40-0.65 → escalate to human
- <0.40 → reject

### Task (from WORK, pre-GROOMING)

```json
{
  "id": "task-005-1",
  "hypothesis_id": "hyp-005-1",
  "description": "Build Stripe payment integration with checkout flow",
  "task_type": "build",
  "estimated_tokens": { "input": 30000, "output": 15000 },
  "risk_tolerance": "proceed_with_auto_fallback",
  "touches_resources": [
    { "type": "api", "identifier": "stripe", "access": "write" }
  ],
  "blocked_by": []
}
```

### ExecutionResult

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

---

*DRAFT — Do not stamp into ARCH_V3.md until thresholds and schemas are calibrated with real execution data.*
*Source: v2 code analysis from `/archive/thousandhand_v2/core/` (runner.py, reflection.py, hypothesis.py, executor.py, dashboard.py)*

*Last Updated: 2026-02-07*
