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

### Overload Detection (Grooming ≠ Breakdown)

If a draft item is clearly **multiple unrelated items** crammed into one file (a brain dump,
a list of 10+ observations, mixed JM concerns), grooming should NOT attempt to split and
classify it. Instead:

1. **Emit** `[PHASE: GROOMING_REJECTED — OVERLOADED]`
2. **Document** why: "This draft contains N distinct items spanning M JMs. Breakdown needed."
3. **Route** the item back to `raw/` for the `breakdown` pre-flow

Grooming handles ONE discrete, scoped item. If the item isn't discrete, it belongs in
breakdown — not grooming. This is a hard boundary.

> **See also:** `JM_COMPLETENESS_CHECKLIST.md` — the 5-layer gap-detection checklist used
> during JM creation, step grooming, and bulk intake triage.

## JM Completeness Checklist

When grooming a FEATURE or MAJOR_FIX that introduces or modifies a journey, run the
**JM Completeness Checklist** (`templates/JM_COMPLETENESS_CHECKLIST.md`) against the
relevant JM step(s):

- **New JM creation:** Run all 5 layers against the initial prompt/description
- **Step grooming:** Run Layers 2-5 against the step being groomed
- **Post-implementation review:** Run Layer 5 to verify cross-actor visibility

This surfaces missing flows, states, actors, and edge cases BEFORE development begins.
Flag gaps found but do not block — document as future work if out of scope.

> **See also:** ARCH_V3 Section 3.7 (Pre-Flow Pipeline) for the full raw → breakdown → draft → grooming → execute lifecycle, and how [PLANNED] catalog entries feed into grooming context.

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

## User Flow Management

During grooming, the user flow catalog must be consulted and maintained:

1. **Read** `docs/USER_FLOWS.md` (the project's flow catalog)
2. **Classify** the incoming item:
   - **JOURNEY** — describes a user experience → define flow(s) in catalog, derive tasks
   - **TASK** — describes something to build → check which existing flows it serves, create new ones if this task introduces new journeys
   - **INFRASTRUCTURE/CHORE** — no user-facing journey → mark as flow-independent, proceed normally

> **Note:** Some user flows may already have `Status: PLANNED` entries in `docs/USER_FLOWS.md`, created during the `kh breakdown` pre-flow. When grooming encounters a draft that maps to a `[PLANNED]` flow, grooming should:
> - Verify the [PLANNED] entry is accurate (correct JM mapping, correct lifecycle)
> - Fill in the `Steps:` section with concrete step definitions
> - Update `Status: PLANNED` → `Status: GROOMED` (indicating grooming has refined it)
> - Reference the flow in the grooming handoff's success criteria
>
> This avoids duplicate flow creation and maintains the breakdown → grooming → execution lifecycle.

3. **Update** `docs/USER_FLOWS.md` with any new or modified flows
4. **Include** flow references in success criteria — "this task serves flows: [list]"

> **See also:** EXECUTOR_STANDARDS Section 4 (TDD protocol) for how user flow tests are written and run during development.

---

## Delivery Handoff

At the end of DEVELOPMENT (before emitting DEVELOPMENT_COMPLETE), create a delivery handoff document using the DELIVERY_HANDOFF_TEMPLATE. This captures:

- What was built (summary)
- Files created/modified
- Deviations from grooming analysis
- Blocked items
- Future TODOs
- Documentation updates needed
