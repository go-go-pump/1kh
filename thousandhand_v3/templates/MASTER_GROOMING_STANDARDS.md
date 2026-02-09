# Grooming Standards

> These are the standards Claude follows during the GROOMING phase of a task.
> This is NOT a template to fill out. It defines how grooming analysis should be conducted.

---

## Execution Philosophy

> **BEST EFFORTS / AGGRESSIVE EXECUTION.**
> When faced with multiple valid options, choose the recommended one and proceed.
> Do NOT stall on decisions — pick the pragmatic path and MOVE IT ALONG.
> If something is ambiguous, make a reasonable assumption, document it, and keep going.

---

## WHAT, Not HOW

Grooming specifies WHAT needs to change and WHY, not HOW to implement it.

- **DO:** Describe requirements, acceptance criteria, architectural constraints
- **DO:** Include DDL schemas, flow diagrams, integration points
- **DON'T:** Include code snippets or implementation details
- **DON'T:** Prescribe specific functions, methods, or variable names

The development phase reads the codebase and decides HOW.

---

## Task Triage

Classify every item as one of:

| Triage | Scope | What to Analyze |
|--------|-------|-----------------|
| `FEATURE` | New functionality, significant additions | Full analysis: objective, architecture, schema, success criteria, scope |
| `MAJOR_FIX` | Bug fix with broad impact or complex root cause | Full analysis: objective, architecture, success criteria |
| `SMALL_FIX` | Targeted bug fix, config change, small tweak | Lightweight: objective, files affected, success criteria |
| `DOCUMENTATION` | Doc-only changes (README, guides, etc.) | Lightweight: objective, files affected, success criteria |

Emit the classification as: `[TRIAGE: FEATURE]` (or MAJOR_FIX, SMALL_FIX, DOCUMENTATION)

---

## Scope Validation

- If implementation would touch >5 files or produce >3 user-facing outcomes, note this for consideration
- Large scope items may benefit from being broken into smaller tasks (TRoNs)
- Flag scope concerns but proceed — do not block on scope alone

---

## Testing Requirements (by Triage)

Tests are written during DEVELOPMENT, not grooming. But grooming should set expectations:

| Triage | Testing Expectation |
|--------|-------------------|
| `FEATURE` | Full test coverage: unit tests for logic, integration/browser tests for UX flows |
| `MAJOR_FIX` | Unit tests for the fix, regression tests for affected areas |
| `SMALL_FIX` | Unit tests only if logic warrants it |
| `DOCUMENTATION` | No tests needed |

Tests must pass before DEVELOPMENT_COMPLETE is emitted.

---

## Phase Markers

The single-session model uses these markers to track progress:

| Marker | When to Emit | Meaning |
|--------|-------------|---------|
| `[PHASE: GROOMING_COMPLETE]` | After grooming analysis is done | Ready to begin development |
| `[PHASE: DEVELOPMENT_COMPLETE]` | After implementation + tests pass + delivery handoff created | Ready to update docs |
| `[PHASE: UPDATE_COMPLETE]` | After project docs are updated | Item is fully complete |

---

## Delivery Handoff

At the end of DEVELOPMENT (before emitting DEVELOPMENT_COMPLETE), create a delivery handoff document using the DELIVERY_HANDOFF_TEMPLATE. This captures:

- What was built (summary)
- Files created/modified
- Deviations from grooming analysis
- Blocked items
- Future TODOs
- Documentation updates needed
