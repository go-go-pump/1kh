# DESIGN: Breakdown Enhancements — Scope Gating + Semantic Grouping

> Working design doc for two breakdown pipeline changes.
> Created: 2026-02-13
> Status: APPROVED — open questions resolved, ready for implementation

---

## Problem Statement

Two issues surfaced during the first real `kh breakdown` run against MVH's phase-1-dump-chunk-1:

**1. Scope discipline gap.** The breakdown correctly classified `admin-send-message-all-users` as `JM_NEW` — an entirely new journey. But it promoted it straight to `draft/`, placing it in the execution queue alongside items for the active journey (JM1: journey-med-consult-labs-rx). The 5-dimension execution sequence model says: complete the current JM's user flows before starting new journeys. Having a JM_NEW in the draft queue means `kh run` could spin up grooming + execution for a new journey while JM1 still has Steps 4-7 in DEFINED state. Classification was correct; the promotion decision was not scope-aware.

**2. Hierarchical input parsing.** The raw dump contained a clearly nested structure:

```
- MAJOR FEATURE: ADMIN LAB ORDERS
    - MANUAL IMPLEMENTATION: ... CREATE order on LabCorp
    SIGN - manual (should update state)
    - SEND - ...
    - VIEW - ...
```

The breakdown treated each line as an independent observation, losing the parent-child relationship. "Item 1: Manual Implementation — CREATE order on LabCorp" became a standalone item rather than a sub-operation under the ADMIN LAB ORDERS topic. The grouping intelligence (Execution Groups) partially recovered this by re-grouping items 1-4 into Group A, but the individual item descriptions were already flattened — the draft file needed manual rewriting.

---

## Design Change 1: DEFERRED_SCOPE

### Principle

Classification and scope gating are separate concerns. Classification answers "what IS this?" Scope gating answers "should we build this NOW?" Today, breakdown does classification only and promotes everything that isn't FUTURE_JM, VAGUE, or NON_IMPLEMENTATION. We need a second pass — a scope filter — that checks promoted items against the current execution scope.

### Current Behavior

```
AI classifies → JM_NEW → promote to draft/ → enters execution queue
```

The only items that avoid the draft queue are FUTURE_JM (terminal defer), VAGUE, and NON_IMPLEMENTATION (rejected). Everything else — including brand new journeys — gets promoted.

### Proposed Behavior

```
AI classifies → JM_NEW → scope filter checks active JMs → DEFERRED_SCOPE
                                                         (not promoted to draft/)
```

New category: **DEFERRED_SCOPE** — "This item is a real, classified piece of work, but it falls outside the currently active execution scope. It is documented and parked, not forgotten. It can be manually promoted via `kh promote` at any time."

Key distinction from existing categories:

| Category | Meaning | Where it lives | Resurrection |
|----------|---------|---------------|--------------|
| FUTURE_JM | Good idea, genuinely different system concern, needs its own JM definition | `raw/{name}_deferred.md` | Create new raw input |
| DEFERRED_SCOPE | Real, classified work — just not in the current execution cycle | `raw/{name}_deferred_scope.md` | `kh promote "id"` |
| draft | Ready for grooming + execution | `draft/{id}.md` | Already in queue |

### Scope Gating Logic

**v1 (simple, implement now):**

The scope filter applies to ONE category: **JM_NEW**. If the breakdown classifies an item as JM_NEW, and there exists at least one active JM in the project (any JM with status containing "IMPLEMENTED" or "IN PROGRESS" in JOURNEY_MAPPINGS.md), the item is redirected to `deferred_scope` instead of `draft`.

Rationale for v1 simplicity: The user's concern is specifically about new journeys entering the queue during active execution. Items within existing JMs (JM_EXISTING_UF, JM_NEW_UF) are legitimate scope — they extend the journey you're already building. CHOREs and bugfixes are maintenance. JM_NEW is the only category that represents genuine scope expansion.

**v2 (future, if needed):**

Add an `active_scope` field to `config.json` listing which JM IDs are currently in execution. The scope filter then also gates JM_EXISTING_UF and JM_NEW_UF items that target JMs NOT in `active_scope`. This handles the case where you have 4 defined journeys but are only executing one — work for the other three gets parked too.

```json
{
  "active_scope": ["journey-med-consult-labs-rx"],
  "scope_gating": true
}
```

For now, v2 is documented but not implemented. v1 covers the immediate need.

### Where the Filter Runs

**DECIDED: Option B — kh.sh post-processing.**

The AI classifies honestly (JM_NEW stays JM_NEW). After extracting the JSON, kh.sh checks: are there active JMs? If yes, redirect JM_NEW items to `deferred_scope` instead of `draft`. The AI doesn't need to know about DEFERRED_SCOPE — it continues classifying JM_NEW as JM_NEW. The script intercepts.

Rationale: The whole point is that we don't trust the AI to be scope-disciplined — that's a structural decision, not a judgment call. Let the AI classify; let the script enforce scope. Mechanical and reliable.

> **Future consideration:** As we learn more, Option A (AI-in-the-loop nuance) could layer on top of Option B — but that's a separate design for another day. Option B is the floor; Option A would be the ceiling.

### Implementation: kh.sh Changes

In `cmd_breakdown()`, after extracting the JSON block and before creating draft files:

1. **Check for active JMs.** Read JOURNEY_MAPPINGS.md (already loaded as `$jm_context`). If any JM has status containing "IMPLEMENTED" or "IN PROGRESS", set `has_active_scope=true`.

2. **Filter JM_NEW items.** When processing groups and standalone items, if `category == "JM_NEW"` and `has_active_scope == true`:
   - Do NOT create a draft file
   - Do NOT add to state.json items array
   - Instead, append to `raw/{name}_deferred_scope.md`
   - Still add [PLANNED] entry to JOURNEY_MAPPINGS.md (so the idea is documented)
   - Print a distinct message: `⟲ Scope-deferred: {id} [JM_NEW → active scope exists]`

3. **Track deferred_scope in state.json raw_items.** Add `deferred_scope_count` alongside existing `deferred_count`.

4. **`kh promote` enhancement.** Currently promotes from developing/complete states. Add ability to promote from deferred_scope:
   - `kh promote "id"` — if ID matches a deferred_scope entry, create the draft file from the stored content and add to state.json items.
   - The deferred_scope file stores the full draft_content so nothing is lost.

### Implementation: ARCH_V3 Changes

**Section 3.7 (Pre-Flow Pipeline) — Classification categories table:**
Add row:
```
| DEFERRED_SCOPE | Real work, outside active execution scope | Defer (promotable via kh promote) |
```

**Section 3.7 — New subsection: "Scope Gating"**

After the classification categories table, add:

> **Scope Gating (post-classification filter):** After the AI classifies raw items, kh.sh applies a scope filter. Items classified as JM_NEW are checked against the current execution scope. If active JMs exist (any JM with IMPLEMENTED or IN PROGRESS status), JM_NEW items are redirected to `deferred_scope` instead of `draft`. This enforces the execution sequence model (Dimension 2: complete current JM before starting new ones) at the pipeline level.
>
> The scope filter is mechanical, not judgmental — it doesn't evaluate whether a JM_NEW item is "small enough" to justify breaking sequence. That's a human decision made explicitly via `kh promote`.
>
> Scope-deferred items are stored in `raw/{name}_deferred_scope.md` with their full draft content preserved. They still receive [PLANNED] entries in JOURNEY_MAPPINGS.md so the idea is documented. They can be promoted to draft at any time via `kh promote "id"`.

**Section 18 (CLI reference):**
Update `kh promote` description to include deferred_scope promotion.

### deferred_scope File Format

```markdown
# Scope-Deferred Items from: {raw_name}
> These items were classified as JM_NEW but deferred because active JM execution
> is in progress. Promote to draft with: kh promote "id"

## {item_title}
- **ID:** {draft_id}
- **Category:** JM_NEW
- **Maps to:** {maps_to}
- **Reasoning:** {reasoning}

### Stored Draft Content
{full draft_content that would have been written to draft/{id}.md}
```

This format stores everything needed for `kh promote` to create the draft file without re-running breakdown.

---

## Design Change 2: Semantic Grouping in Breakdown

### Principle

"Structure-aware" means the breakdown AI recognizes *semantic relationships between adjacent lines* in the raw input — not that it expects a specific formatting standard. The user's brain dumps come from a Notes app and may have inconsistent indentation, missing bullets, or choppy formatting. The AI should read for meaning the way a human PM would: if someone writes "LAB ORDERS — sign, send, view," a PM creates one ticket with three acceptance criteria, not three unrelated tickets.

### Current Behavior

The breakdown prompt says:

> "For each DISTINCT observation or request in the raw input..."
>
> "AMBIGUITY RULE: If a line could be either a section header OR a standalone observation, err toward classifying it as a standalone item."

This produces a flat list of items. The grouping intelligence (Execution Groups) re-groups related items afterward, but by then each item's description has already lost its hierarchical context. The draft files contain flattened observations.

### Proposed Behavior

Add a **pre-classification step** to the breakdown prompt: before enumerating individual items, first scan for semantic parent-child relationships in the raw input.

The key instruction (to be added to the prompt):

> **SEMANTIC GROUPING (pre-classification step):**
>
> Before classifying individual items, read the raw input for semantic structure. Look for lines that serve as **topic declarations** — broad statements that introduce a feature area — followed by lines that describe **sub-operations** within that topic.
>
> Signals that indicate parent-child relationships (any of these, not all required):
> - A broad feature name followed by specific actions (e.g., "ADMIN LAB ORDERS" followed by "SIGN," "SEND," "VIEW")
> - A line that names a workflow followed by lines that describe steps in that workflow
> - A labeled section (e.g., "CONSENT WORKFLOW:") followed by actor-specific details
> - Lines that only make sense in the context of the line above them
>
> When you detect a parent-child structure:
> - The parent line becomes the **group title**, not a standalone observation
> - The child lines become **observations within that group**
> - The resulting draft should frame these as a workflow or feature with named operations — not as independent items that happen to be grouped
>
> This is semantic, not format-based. Do NOT rely on indentation, bullet characters, or markdown syntax. The raw input may have inconsistent formatting from a notes app — tabs vs spaces, missing bullets, mixed nesting. Read for MEANING, not for structure.
>
> The AMBIGUITY RULE ("when in doubt, promote — don't absorb") still applies to genuinely ambiguous standalone lines. It does NOT apply to lines that are clearly sub-operations of a parent concept.

### What This Changes in the Output

**Before (current behavior — flat items):**
```
### Item 1: Manual Implementation — CREATE order on LabCorp
We implemented some great things on "Lab Order PDFs", but Dr could CREATE order on LabCorp.

### Item 2: SIGN — manual (should update state)
Manual signing of lab order — should update lab order state in database.

### Item 3: SEND — sends to CLIENT with message (should update state)
SENDS to CLIENT with message ...
```

**After (semantic grouping — workflow-framed):**
```
### Admin Lab Orders — Manual Workflow

Operations within the existing lab order admin page. Source context: "We implemented some great things on Lab Order PDFs."

**CREATE**: Dr could CREATE order on LabCorp (currently missing from admin UX).
**SIGN**: Manual signing of lab order — should update lab order state in database.
**SEND**: Send to client with message (manual — physician does it here). Should update state.
**VIEW**: Need URL to pop up PDF for viewing lab order documents.
```

Note: the grouped draft still doesn't include implementation details (lambda ARNs, S3 keys, etc.) — that's grooming's job. But it correctly frames the items as sub-operations of a single workflow rather than independent features.

### Implementation: Breakdown Prompt Changes

In kh.sh `cmd_breakdown()`, in the prompt string (around line 1936), insert the semantic grouping instruction **before** the classification rules. The placement matters — the AI should identify topic groupings FIRST, then classify the groups.

Current order:
```
## CLASSIFICATION RULES
(for each distinct observation...)
```

New order:
```
## SEMANTIC GROUPING (pre-classification)
(scan for parent-child relationships first...)

## CLASSIFICATION RULES
(for each distinct observation or identified group...)
```

Also update the AMBIGUITY RULE to scope its application:

Current:
> "If a line could be either a section header OR a standalone observation, err toward classifying it as a standalone item."

Updated:
> "If a line could be either a section header OR a standalone observation, AND it has no clearly related sub-items following it, err toward classifying it as a standalone item. If the line IS followed by sub-items that only make sense in its context, treat it as a topic declaration and group the sub-items under it."

### Implementation: ARCH_V3 Changes

**Section 3.7 — Update "Ambiguity handling" paragraph:**

Current:
> Brain dumps often contain lines that could be either section headers or standalone observations (e.g., "CROSS-OP (medical-consult and labs)"). The prompt instructs: "When in doubt, promote — don't absorb." Let grooming merge if redundant, rather than losing an item by treating it as decoration.

Updated:
> Brain dumps often contain lines that could be either section headers or standalone observations. Two rules apply: (1) **Semantic grouping**: When consecutive lines describe sub-operations of a broader feature (e.g., "ADMIN LAB ORDERS" followed by CREATE, SIGN, SEND, VIEW), the AI recognizes the parent-child relationship semantically — not by format or indentation — and groups them into a single draft with the parent as the topic and children as observations within it. (2) **Ambiguity rule**: For genuinely standalone lines with no clearly related sub-items (e.g., "CROSS-OP (medical-consult and labs)"), err toward promoting as a standalone item rather than absorbing as decoration. Let grooming merge if redundant, rather than losing an item by treating it as a header.

**Section 3.7 — Key principles, add new principle:**

> 6. **Semantic grouping, not format parsing.** Breakdown reads for meaning, not structure. Raw input from notes apps may have inconsistent indentation, missing bullets, or mixed formatting. The AI identifies parent-child relationships between adjacent lines based on semantic context — a broad feature name followed by specific operations forms a group regardless of how it's formatted. This is pre-classification: groups are identified before individual items are categorized.

---

## Implementation Checklist

All items are atomic: code change + doc change ship together.

### Change 1: DEFERRED_SCOPE

| # | Task | Files | Notes |
|---|------|-------|-------|
| 1a | Add scope detection function to kh.sh | `bin/kh.sh` | New function: `has_active_jm_scope()` — reads JOURNEY_MAPPINGS.md, returns true if any JM is IMPLEMENTED or IN PROGRESS |
| 1b | Add scope filter in `cmd_breakdown()` post-processing | `bin/kh.sh` | After JSON extraction, before draft creation. JM_NEW + active scope → redirect to deferred_scope file |
| 1c | Create `deferred_scope` file output | `bin/kh.sh` | New file: `raw/{name}_deferred_scope.md` with stored draft content |
| 1d | Track `deferred_scope_count` in state.json | `bin/kh.sh` | Add field to raw_items update |
| 1e | Extend `kh promote` to handle deferred_scope items | `bin/kh.sh` | Read stored draft content from deferred_scope file, create draft, add to state.json |
| 1f | Add deferred_scope re-evaluation to breakdown context gathering | `bin/kh.sh` | Read `_deferred_scope.md` files alongside `_deferred.md` files in `cmd_breakdown()` context section |
| 1g | Update `kh status` to show scope-deferred count | `bin/kh.sh` | New section: "Scope-deferred: N items (use kh promote to activate)" |
| 1h | Update ARCH_V3 classification table | `docs/ARCH_V3.md` | Add DEFERRED_SCOPE row |
| 1i | Add "Scope Gating" subsection to ARCH_V3 §3.7 | `docs/ARCH_V3.md` | Describe the filter, its rationale, how promote works |
| 1j | Update ARCH_V3 CLI reference for `kh promote` | `docs/ARCH_V3.md` | Document deferred_scope promotion |
| 1k | Update README CLI table | `README.md` | Add note about scope gating to `kh breakdown` description |

### Change 2: Semantic Grouping

| # | Task | Files | Notes |
|---|------|-------|-------|
| 2a | Add SEMANTIC GROUPING section to breakdown prompt | `bin/kh.sh` | Insert before CLASSIFICATION RULES in the prompt string |
| 2b | Update AMBIGUITY RULE in breakdown prompt | `bin/kh.sh` | Scope the rule: applies to standalone lines without sub-items |
| 2c | Update ARCH_V3 §3.7 "Ambiguity handling" | `docs/ARCH_V3.md` | Replace with two-rule explanation (semantic grouping + ambiguity) |
| 2d | Add principle #6 to ARCH_V3 §3.7 key principles | `docs/ARCH_V3.md` | "Semantic grouping, not format parsing" |

### Validation

| # | Task | Notes |
|---|------|-------|
| V1 | Re-run `kh breakdown "phase-1-dump-chunk-1" --dry-run` against MVH | Verify: admin-send-message-all-users lands in deferred_scope, not draft |
| V2 | Verify admin-lab-orders items come out as a single workflow-framed group | Compare against manually rewritten admin-lab-orders-manual-workflow.md |
| V3 | Verify FUTURE_JM items (MPN/MPF, OM Cross Promo) still land in deferred as before | Regression check — scope gating shouldn't affect FUTURE_JM behavior |

---

## Resolved Questions

1. **`kh status` shows deferred_scope items.** YES — as a separate section: "Scope-deferred: N items (use kh promote to activate)." Visibility without noise.

2. **`kh run` ignores deferred_scope.** NO warning. The user will manually locate and promote scope-deferred items when ready. No nagging from the CLI.

3. **Auto-promotion on scope change: SHELVED.** The concept is sound — comparing `active_scope` in config against deferred item scope would be a clean auto-promote trigger. But this depends on formalizing which JM is active and establishing what the NEXT JM is. We're close to that but haven't implemented it yet. Design this AFTER the current implementation ships. Pairs with v2's `active_scope` config field.

4. **Multiple raw inputs check deferred_scope files.** YES — breakdown should read existing `_deferred_scope.md` files as context, same pattern as FUTURE_JM re-evaluation. If a deferred_scope item now maps to a JM that's become active (e.g., someone ran `kh promote` on its parent journey), it can be surfaced. Relatively simple and consistent with existing deferred re-evaluation pattern.
