# TH CONTEXT PRIMER
> ThousandHands (1KH) Project | Paste at session start
> **See also:** WORKING_AGREEMENT.md in `/projects/CLAUDE_CONTEXT`

**Last updated:** 2026-02-04

---

## Project Identity

**ThousandHands (1KH)** is an autonomous business-building system powered by Claude AI.

> Give me your values and objectives. I will imagine paths forward, estimate what's feasible, build what's needed, measure what happens, and learn from the results. I will ask for help when I'm stuck, and I will never violate your values.

### Tech Stack
- **Language:** Python
- **Workflows:** Temporal Cloud
- **AI:** Claude API (Anthropic)
- **CLI:** `1kh` command

---

## Current State (Architecture Delivered)

**Phase:** 1 (Pre-Execution Development) ~60-75% complete

### The Five Loops
```
REFLECTION → IMAGINATION → INTENT → WORK → EXECUTION
     ↑                                         │
     └─────────── cycle repeats ───────────────┘
```

### Implemented (Hardened)
- [x] Four Loops concept (IMAGINATION → INTENT → WORK → EXECUTION)
- [x] REFLECTION feeding into IMAGINATION
- [x] BIZ vs USER system distinction (conceptually)
- [x] Foundation-level vs Imagination-level change types
- [x] Demo mode with scenarios (AUGMENT, OPTIMIZE, PIVOT, vendor-choice)
- [x] Phase callbacks and loading indicators
- [x] Cycle persistence and resume
- [x] CLI interface (`1kh init`, `1kh run cycle`, `1kh reflect`)

---

## Current Priority (Setting/Hardening)

- [ ] **Foundation intake flow** ← CURRENT PRIORITY
  - [ ] BIZ vs USER system detection
  - [ ] Value surfacing conversation
  - [ ] North Star type confirmation
- [ ] Hypothesis definition (needs test conditions)
- [ ] WORK ITEMS layer between HYPOTHESIS and TASKS
- [ ] Task types (BUILD/TEST/OPS conceptually mapped)
- [ ] When to challenge Foundation (REFLECTION triggers)
- [ ] STORY as part of Context in Foundation

---

## Roadmap (Future Activities)

| Phase | Name | Status |
|-------|------|--------|
| **1** | Pre-Execution Development | **IN PROGRESS** ~60-75% |
| 2 | Pre-Execution Simulation | Not Started |
| 3 | Pre-Execution Live Workflows | Not Started |
| 4 | Execution Development (Local) | Not Started |
| 5 | Execution Simulation (Local) | Not Started |
| 6 | Execution Live Workflows | Not Started |
| 7 | End-to-End Development (Local) | Not Started |
| 8 | End-to-End Simulation (Local) | Not Started |
| 9 | End-to-End Live Workflows | Not Started |
| 10 | Real World - USER SYSTEM | Not Started |
| 11 | Real World - BIZ SYSTEM | Not Started |
| 12 | Real World - Integration | Not Started |
| 13 | Shared Components | Not Started |

**Phase 1 Exit Criteria:**
- Foundation intake properly detects system type
- Foundation documents have clear structure
- Hypothesis generation produces testable hypotheses
- REFLECTION can recommend Foundation-level changes
- Demo scenarios all work correctly

---

## Detail Docs (Where to Look)

| Purpose | Doc | Location |
|---------|-----|----------|
| Architecture concept | `FOUNDATION.md` | `/1KH/` |
| Implementation status | `ROADMAP.md` | `/1KH/docs/` |
| Design decisions | `DECISIONS.md` | `/1KH/docs/` |
| Testing approach | `TESTING_STRATEGY.md` | `/1KH/docs/` |
| CLI reference | `CLI_GUIDE.md` | `/1KH/` |
| This primer | `TH_PRIMER.md` | `/MVH/man-plan-architecture/` |

---

## Notes for Claude

1. **Run demo mode for testing** — `1kh run cycle --demo --max 3 --verbose` (no API costs)
2. **Core logic lives in** `/1KH/core/`
3. **CLI entry point** — `/1KH/cli/main.py`
4. **Temporal workflows** — `/1KH/temporal/`
5. **Foundation docs** — Oracle, North Star, Context (stored in project's `.1kh/foundation/`)

### Key Commands
```bash
# Demo mode (no API costs)
1kh run cycle --demo --max 3 --verbose

# Real Claude API
export ANTHROPIC_API_KEY=sk-ant-...
1kh run cycle --local --fresh --verbose

# Check trajectory
1kh reflect
```

---

## Quick Review (Session Start)

Per `REVIEW_PROTOCOL.md`:

```
1. State check — "What's current reality in 1KH?"
2. Doc alignment — "Does ROADMAP.md still match implementation?"
3. Scope — "Today's focus: [X]. Any blockers?"
```

---

## Sync Protocol

| Session Type | Update Which Doc |
|--------------|------------------|
| EXECUTION (build) | `ROADMAP.md` (implementation status) |
| STRATEGIC (plan) | `DECISIONS.md`, `ROADMAP.md` |
| REVIEW (sync) | This PRIMER if focus changed |

---

## Key Concepts

- **Oracle** — Your values and boundaries (what you'll never violate)
- **North Star** — Your measurable goal (e.g., $1M ARR)
- **Hypothesis** — A testable idea for achieving the North Star
- **System Completeness** — Four components needed for revenue: Product, Payment, Channel, Fulfillment
- **Trajectory** — Current pace toward the goal

### Change Levels

**Foundation Level:**
| Level | Impact |
|-------|--------|
| TWEAK | Wording/clarification — absorb silently |
| ADJUST | Narrow scope, shift priority — re-score hypotheses |
| PIVOT | New market/product/mechanism — major pruning |
| RESTART | Fundamentally different vision — new project |

**Imagination Level:**
| Level | Scope |
|-------|-------|
| AUGMENT | Add capability (fill gaps) |
| OPTIMIZE | Improve existing (weak metrics) |

---

## Last Session

**Date:** 2026-02-04
**Focus:** Initial primer creation
**Accomplished:**
- Created TH_PRIMER.md following MVH_PRIMER.md format
- Captured current 1KH project state from ROADMAP.md, DECISIONS.md, README.md
