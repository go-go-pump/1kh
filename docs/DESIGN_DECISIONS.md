# Design Decisions: Cycles, Hypotheses, and Abstraction

This document addresses key architectural questions about how ThousandHand operates.

---

## 1. What Defines a Cycle?

### Current Definition
A **cycle** is one pass through all five loops:
```
REFLECTION → IMAGINATION → INTENT → WORK → EXECUTION
```

### What Gets Done in One Cycle?
- **REFLECTION**: ~1 second (local analysis)
- **IMAGINATION**: ~10-30 seconds (Claude generates hypotheses)
- **INTENT**: ~1 second (score and filter)
- **WORK**: ~5-10 seconds (Claude creates tasks)
- **EXECUTION**: ~5-30 seconds per task (mock or real execution)

**Total**: ~30 seconds to 2 minutes per cycle

### What SHOULD a Cycle Represent?
Options:
1. **Time-boxed** (1 day, 1 week) - "What can we accomplish this sprint?"
2. **Goal-boxed** - "Until we complete this milestone"
3. **Resource-boxed** - "Until we spend $X or Y hours"
4. **Iteration-boxed** (current) - "One pass through the loops"

**Recommendation**: Keep iteration-boxed but add a **time simulation** for realistic planning:
```
Cycle 1: Day 1-3 (building payment integration)
Cycle 2: Day 4-5 (building landing page)
Cycle 3: Day 6-7 (first customers)
```

---

## 2. Cycle Persistence and Resume

### Current Behavior
- `--fresh`: Clears events, starts from Cycle 1
- Without `--fresh`: Events persist, but cycle count resets to 1

### Problem
If interrupted mid-run, you lose cycle context but keep some metrics.

### Proposed Fix
Store cycle state in `.1kh/state/run_state.json`:
```json
{
  "last_cycle": 3,
  "last_run_at": "2025-01-31T12:00:00Z",
  "interrupted": true,
  "total_cycles_ever": 47
}
```

**Behavior**:
- Without `--fresh`: Resume from `last_cycle + 1`
- With `--fresh`: Reset everything including cycle count

---

## 3. Hypothesis Abstraction Levels

### The Problem
"Integrate Stripe payment processing" is too prescriptive. What if the user:
- Uses Square instead of Stripe?
- Already has a payment processor?
- Needs a different integration pattern?

### Proposed Solution: Two-Level Hypotheses

#### Level 1: WHAT (Capability Hypothesis)
Abstract, technology-agnostic:
```yaml
id: hyp-001-PAY
level: capability
description: "Enable customers to pay for the product"
category: payment
required_capability: "payment_processing"
success_criteria:
  - "Customers can complete transactions"
  - "Revenue is trackable"
  - "Refunds are possible"
```

#### Level 2: HOW (Implementation Hypothesis)
Specific, technology-specific:
```yaml
id: hyp-001-PAY-STRIPE
level: implementation
parent: hyp-001-PAY
description: "Integrate Stripe Checkout for payment processing"
technology: "stripe"
alternatives:
  - "hyp-001-PAY-SQUARE"
  - "hyp-001-PAY-PAYPAL"
requires_decision: true
decision_prompt: "Which payment processor should we use?"
```

### Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    HYPOTHESIS LIFECYCLE                         │
├─────────────────────────────────────────────────────────────────┤
│  1. REFLECTION identifies: "Missing payment system"            │
│                            ↓                                    │
│  2. IMAGINATION generates: CAPABILITY hypothesis               │
│     "Enable customers to pay for the product"                  │
│                            ↓                                    │
│  3. INTENT approves the CAPABILITY                              │
│                            ↓                                    │
│  4. WORK phase asks: "Which implementation?"                    │
│     Options: [Stripe, Square, PayPal, Other]                   │
│     User chooses or we use context clues                        │
│                            ↓                                    │
│  5. EXECUTION runs the specific implementation                  │
└─────────────────────────────────────────────────────────────────┘
```

### When to Ask vs Prescribe

| Situation | Action |
|-----------|--------|
| User context mentions specific tech | Use that tech |
| Multiple equivalent options exist | Ask user |
| Oracle/Context has constraints | Follow constraints |
| Industry-standard choice exists | Suggest with option to change |
| Choice affects architecture | Always ask |
| Choice is easily reversible | Suggest, proceed if no response |

### Implementation

Add to `context.md` or new `preferences.md`:
```markdown
## Technology Preferences

### Payment
- Preferred: Square (already have account)
- Avoid: PayPal (fee structure)

### Hosting
- Preferred: Vercel (team familiarity)
- Avoid: AWS (complexity)

### Database
- Preferred: Supabase (already using)
```

The system reads these and:
1. Uses preferred options without asking
2. Avoids explicitly excluded options
3. Asks only when no preference exists

---

## 4. Linking Components ↔ Hypotheses ↔ Tasks

### The Traceability Problem
User can't see: "This task builds the Payment component"

### Proposed Solution: Explicit Tagging

Every hypothesis declares which component(s) it builds:
```yaml
id: hyp-001-PAY
builds_component: "payment"
component_transition: "missing → building"
```

Every task inherits from its hypothesis:
```yaml
id: task-001
hypothesis_id: hyp-001-PAY
builds_component: "payment"  # inherited
```

### Report View

```
┌─────────────────────────────────────────────────────────────────┐
│ COMPONENT: Payment                                              │
│ Status: building → live                                         │
├─────────────────────────────────────────────────────────────────┤
│ Hypotheses:                                                     │
│   • hyp-001-PAY: Enable payment processing ✓ Approved           │
│   • hyp-002-PAY: Add subscription billing ○ Planned            │
├─────────────────────────────────────────────────────────────────┤
│ Tasks:                                                          │
│   • task-001: Integrate Stripe Checkout ✓ Done                  │
│   • task-002: Add webhook handlers ✓ Done                       │
│   • task-003: Test payment flow ◐ In Progress                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Recommendations

### Immediate Changes (This Session)

1. **Add `--max` alias** ✓ Done
2. **Clear reports on `--fresh`** ✓ Done
3. **Store cycle state for resume** - Add run_state.json
4. **Tag hypotheses with component** - Add `builds_component` field

### Future Changes (Next Session)

1. **Two-level hypotheses** (WHAT vs HOW)
2. **Technology preferences** in context.md
3. **Component-centric report view**
4. **Time simulation** for realistic planning

---

## Questions for You

1. **Cycle definition**: Do you want cycles to represent real time periods (days/weeks) or keep them as iteration units?

2. **Hypothesis levels**: Should we implement two-level hypotheses now, or is one level with "ask when uncertain" sufficient?

3. **Preferences file**: Should technology preferences be part of `context.md` or a separate `preferences.md`?

4. **Resume behavior**: When resuming after interrupt, should we:
   - A) Continue exactly where we left off (same hypotheses)
   - B) Start fresh cycle but keep metrics
   - C) Let user choose
