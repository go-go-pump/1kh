# Design Analysis: `raw → breakdown → draft` Pre-Flow

> **Status:** PROPOSAL — v2 with owner feedback incorporated
> **Date:** 2026-02-12 (updated 2026-02-13)
> **Context:** Supabase outage; working on 1KH methodology while blocked
> **Decisions resolved:** 11 of 11 feedback items addressed (see Section 15)

---

## 1. The Problem

1KH currently assumes items arrive **discrete and roughly scoped**. The user writes a markdown file in `draft/`, and the single-session model (groom → execute → update) takes it from there.

But real product work doesn't produce discrete items. It produces **brain dumps**: 9 observations from clicking through a portal, 15 ideas from a customer call, 40 items from a competitive audit. These are messy, overlapping, and span multiple levels of the hierarchy (JMs, UFs, tasks, chores, non-actionable notes).

Today, the human does all the splitting and categorizing manually before anything enters 1KH. That's the bottleneck this proposal addresses.

### What Grooming Can't Do

Grooming (GROOMING_STANDARDS.md) is designed for **one discrete item** → analyze → classify → execute. It asks "what kind of item is this?" and "what are the requirements?"

The new problem asks a fundamentally different question: **"what items are IN this mess?"**

That's not grooming. That's triage. And triage needs to happen BEFORE grooming, because grooming can't start until you have a discrete item to groom.

---

## 2. Current Flow (for reference)

```
USER writes markdown  →  draft/  →  developing/  →  complete/
                            │           │              │
                         (stored)   (groom+execute    (done)
                                    single session)
```

**Assumption:** Each file in `draft/` = one discrete item.

---

## 3. The Proposal

Add a **pre-flow** stage that sits before `draft/`:

```
raw/           →    breakdown     →    draft/     →   developing/   →   complete/
(messy input)     (AI triage)       (discrete       (groom+execute)    (done)
                                     items)
```

### Three new concepts:

**`raw "name" <<< "text"` or `raw "name" < file.md`**
Intake command. Stores messy input verbatim. No intelligence, just storage.

**`breakdown "name"`**
AI-powered analysis. Reads the raw input, splits into discrete items, categorizes each one, and promotes the good ones to `draft/`.

**Output categories:**

| Category | What it means | Where it goes |
|----------|--------------|---------------|
| `JM_EXISTING_UF` | Maps to known JM + known UF | `draft/` as update task |
| `JM_NEW_UF` | Maps to known JM, but new user flow | `draft/` as UF definition + task |
| `JM_NEW` | Entirely new journey | `draft/` as JM definition |
| `CHORE` | Infrastructure, refactor, DX, rename | `draft/` as standalone task |
| `FUTURE_JM` | Good idea, wrong time | Documented in `raw/[name]_deferred.md` |
| `REDUNDANCY` | Already covered elsewhere | Noted in breakdown output with cross-ref |
| `VAGUE` | Can't determine what this means | `raw/[name]_rejected.md` for human review |
| `NON_IMPLEMENTATION` | Not a software task | `raw/[name]_rejected.md` for human review |

---

## 4. The Core Design Question

> **Should this be a SEPARATE STAGE or should grooming be ENHANCED to handle bulk input?**

This is the tension the user identified. Let me lay out both sides.

### Argument for SEPARATE STAGE (raw → breakdown → draft)

**The stages solve different problems:**

| Stage | Question it answers | Input shape | Output shape |
|-------|-------------------|-------------|--------------|
| `raw → breakdown` | "What items are in this mess?" | Unstructured blob | N discrete items |
| `draft → groom` | "What kind of item is this?" | 1 discrete item | Classified + scoped item |
| `groom → execute` | "How do I build this?" | Scoped item | Working code |

These are **genuinely different cognitive tasks**. Trying to do all three in one session means the session has to: parse a blob, split it, classify each piece, scope each piece, AND build each piece. That's too many context switches for a single session to do well.

**Separation gives you a review gate.** After breakdown, the human sees: "Here are 9 items extracted from your brain dump. 6 go to draft, 2 are deferred, 1 is vague." The human can correct misclassifications before any execution begins. This is the "you can't un-build something" principle — catching errors early is exponentially cheaper.

**Breakdown can reference the JM Completeness Checklist.** When breakdown encounters something that *might* be a new JM, it can run a quick Layer 1 (Actor Enumeration) to validate. When something maps to an existing JM, breakdown can check the checklist layers to see if it fills a known gap — making it higher priority.

### Argument for ENHANCED GROOMING

**Fewer moving parts.** The current system has one intake point (`draft/`) and one processing model (single session). Adding `raw/` + `breakdown` doubles the surface area.

**Grooming already classifies.** GROOMING_STANDARDS already has the JOURNEY / TASK / INFRASTRUCTURE/CHORE classification (lines 86-88). You could extend this to handle "this item is actually N items."

**Risk of over-engineering.** If breakdown is too aggressive about splitting, you get 20 tiny tasks that should have been 3 coherent features. The human has to re-aggregate. You've added work, not removed it.

### My Assessment

**Separate stage wins, but with constraints.**

The key insight: breakdown is a **reading + classifying** operation, while grooming is a **scoping + planning** operation. These aren't just different in degree — they're different in kind. Breakdown reads a blob and says "there are 9 things here." Grooming reads one thing and says "here's how to build it." Conflating them means the grooming session has to do split-and-classify AND scope-and-plan, which degrades both.

The constraint: **breakdown should NOT groom.** It should categorize and split, nothing more. The moment breakdown starts writing acceptance criteria or suggesting implementations, it's doing grooming's job. The output of breakdown should be: "Item 3 maps to JM1, Step 3, appears to be a CLIENT UX enhancement for the lab results section." Full stop. Grooming then picks it up and says "here's what that means technically."

### The Reverse Boundary: Grooming Should Not Breakdown

Just as breakdown shouldn't groom, **grooming should not breakdown.** If a draft item arrives
at grooming and it's clearly overloaded (10+ observations, multiple JMs, a brain dump), grooming
should NOT try to split it. Instead:

1. Emit `[PHASE: GROOMING_REJECTED — OVERLOADED]`
2. Route the item back to `raw/` for breakdown
3. Document why: "This draft contains N distinct items spanning M concerns. Needs breakdown first."

This creates a **two-way hard boundary**: breakdown doesn't scope, grooming doesn't split. Each
stays in its lane. (This is now formalized in GROOMING_STANDARDS.md under "Overload Detection.")

### Is Breakdown Required? (Can You Bypass It?)

**No — breakdown is optional.** If you have a well-scoped item, drop it straight into `draft/`
as you always have. The flow is:

```
                         ┌─────────────────────────────┐
                         │   Discrete item              │
                         │   (well-scoped, single JM)   │
                         └──────────┬──────────────────┘
                                    │ BYPASS → directly to draft/
                                    ▼
raw/ → breakdown → draft/ → developing/ → complete/
         ▲                     │
         │                     │ KICKBACK (overloaded)
         └─────────────────────┘
```

The pre-flow exists for brain dumps. If you have a discrete task, skip it. If grooming
discovers something slipped through that should have been broken down, it kicks it back.
This keeps the system self-correcting without making breakdown mandatory.

---

## 5. Naming

The user proposed `raw → breakdown → draft`. Let me evaluate the names.

**`raw`** — Perfect. It's what it is: raw, unprocessed input. Alternatives like `intake` or `ingest` sound enterprise-y. `raw` is honest.

**`breakdown`** — Good but has a subtle problem: "breakdown" could imply the system is breaking DOWN (failing). Alternatives:

| Name | Pro | Con |
|------|-----|-----|
| `breakdown` | Descriptive, matches "break it down" | Could read as "system breakdown" |
| `triage` | Medical metaphor, accurate (sort by urgency/type) | Overloaded term in engineering |
| `sift` | Implies separating wheat from chaff | Too cute |
| `sort` | Clear | Too generic, collides with Unix `sort` |
| `split` | Accurate for the splitting action | Doesn't capture the categorization |

**Recommendation:** Keep `breakdown`. The verb "break down" is well-understood in project management ("break down the work"). The noun collision is minor and context makes it clear.

**`draft`** — Already exists. No change needed. This is the existing entry point.

**Full flow name:** `raw → breakdown → draft → execute`

---

## 6. File Storage Design

```
.kh/
├── raw/                              # NEW: unprocessed input
│   ├── portal-observations.md        # Original brain dump (preserved forever)
│   ├── portal-observations_breakdown.md  # AI analysis output
│   ├── portal-observations_rejected.md   # VAGUE + NON_IMPLEMENTATION items
│   └── portal-observations_deferred.md   # FUTURE_JM items (good but not now)
├── draft/                            # EXISTING: discrete items (breakdown output lands here)
│   ├── jm1-lab-results-section.md    # From breakdown: JM_EXISTING_UF
│   ├── jm1-lab-order-details.md      # From breakdown: JM_EXISTING_UF
│   ├── rename-lab-results-html.md    # From breakdown: CHORE
│   └── ...
├── developing/                       # EXISTING: unchanged
├── complete/                         # EXISTING: unchanged
└── ...
```

**Key decisions:**

1. **Raw input is NEVER deleted.** It's the source of truth. Even after breakdown, the original blob stays in `raw/`. This is important because the human might re-run breakdown with updated context or re-read the original observations later.

2. **Breakdown output is a readable report**, not just a routing table. The human should be able to open `_breakdown.md` and see exactly what the AI did with each item. Format:

```markdown
# Breakdown: portal-observations
> Source: raw/portal-observations.md
> Run: 2026-02-12 14:30
> Items found: 9
> Promoted to draft: 6
> Deferred: 2
> Rejected: 1

## Item 1: Rename lab-results.html → lab-orders.html
- **Category:** CHORE
- **Maps to:** JM1 (general — affects Steps 1-4)
- **Draft file:** draft/rename-lab-results-html.md
- **Reasoning:** File rename with URL implications. Not tied to a specific UF
  but prerequisite for several.

## Item 2: Add Lab Order Details section
- **Category:** JM_EXISTING_UF
- **Maps to:** JM1, Step 1, Client UX
- **Draft file:** draft/jm1-step1-lab-order-details.md
- **Reasoning:** Purchase date, LabCorp order number, status, completion date.
  This fills a gap in Step 1's client-facing UX (currently minimal).

...

## Item 8: BYOL customer handling
- **Category:** FUTURE_JM
- **Maps to:** New JM (BYOL — Bring Your Own Labs)
- **Deferred file:** raw/portal-observations_deferred.md
- **Reasoning:** BYOL is a distinct journey with different intake, verification,
  and processing patterns. Not current scope for JM1.
```

3. **Promoted drafts are self-contained.** Each file in `draft/` created by breakdown should contain enough context that grooming doesn't need to reference the raw blob. The draft should include: the original observation text, the categorization, the JM/UF mapping, and a brief "what this probably means." Grooming takes it from there.

---

## 7. The Top-Down Principle

The user's key architectural rule: **always work JM → UF → Task.** Never the other way.

This means breakdown must:

1. **First:** Identify which JM(s) the raw input touches. If it doesn't map to any known JM, is it a new JM or is it a chore/non-implementation?

2. **Second:** Within each JM, identify which steps/UFs the items map to. If an item maps to a JM but not a known UF, it's either a new UF or a gap that the JM Completeness Checklist would have caught.

3. **Third:** Within each UF, identify whether this is a new implementation, an update to existing, or a fix.

**This is where the JM Completeness Checklist integrates.** When breakdown encounters a raw item and needs to determine "does this fit in JM1?", it can run against the checklist layers:

- Layer 1 (Actors): Does this item introduce a new actor? If so, it might be a new JM.
- Layer 2 (States): Does this item describe a missing entity state? If so, it's filling a gap in an existing JM.
- Layer 3 (Sad paths): Is this item a "what if they don't?" scenario? If so, it maps to an existing step's sad path.
- Layer 5 (Other screen): Is this item about what another actor sees? If so, it maps to an existing step's cross-actor visibility.

Breakdown doesn't run the FULL checklist (that's a 7-minute process per JM). It uses the checklist layers as a **classification heuristic**: "this observation looks like a Layer 2 gap (missing entity state) in JM1, Step 3."

---

## 8. The Grooming Overlap Question

The user asked: "should we be doing this in GROOMING essentially?"

Here's the precise boundary:

| Concern | Breakdown handles | Grooming handles |
|---------|------------------|-----------------|
| "How many items are in this blob?" | ✅ | ❌ |
| "What JM does this belong to?" | ✅ | ❌ (already decided) |
| "Is this actionable or vague?" | ✅ | ❌ (only gets actionable items) |
| "What are the acceptance criteria?" | ❌ | ✅ |
| "What's the technical scope?" | ❌ | ✅ |
| "FEATURE or SMALL_FIX?" | ❌ | ✅ |
| "What tests need to pass?" | ❌ | ✅ |

The overlap zone — where it gets fuzzy — is **"is this a new UF or an update to an existing UF?"** Both breakdown and grooming could reasonably answer this. The rule should be: **breakdown makes the call, grooming can override it.** If breakdown says "this is a new UF" but grooming discovers it's actually an update to UF-C03, grooming corrects the classification. Breakdown is first-pass triage, not a binding verdict.

---

## 9. Walked Example: Portal Observations

If the user's 9 portal observations went through this system:

```bash
kh raw "portal-lab-observations" < observations.md
kh breakdown "portal-lab-observations"
```

**Breakdown output:**

| # | Observation | Category | Maps to | Output |
|---|------------|----------|---------|--------|
| 1 | Rename lab-results.html → lab-orders.html | `CHORE` | JM1 (general) | → `draft/` |
| 2 | Add Lab Order Details section | `JM_EXISTING_UF` | JM1 Step 1 Client UX | → `draft/` |
| 3 | Add LAB PANELS PURCHASED section | `JM_EXISTING_UF` | JM1 Step 1 Client UX | → `draft/` |
| 4 | Lab Orders by Man vs Health (print/view) | `JM_EXISTING_UF` | JM1 Step 2 Client UX | → `draft/` |
| 5 | Lab Results section improvements | `JM_EXISTING_UF` | JM1 Step 3 Client UX | → `draft/` |
| 6 | Remove "My Uploads" (redundant) | `REDUNDANCY` | JM1 (noted) | → `_breakdown.md` only |
| 7 | Fix Upload Lab Results (VIEW/DELETE) | `JM_EXISTING_UF` | JM1 Step 3 Client UX | → `draft/` |
| 8 | BYOL customer handling | `FUTURE_JM` | New JM: BYOL | → `_deferred.md` |
| 9 | Fix byol-upload.html | `FUTURE_JM` | New JM: BYOL (depends on #8) | → `_deferred.md` |

**Human review moment:** The human opens `_breakdown.md`, sees this table, and decides:
- "Actually, items 2 and 3 should be one draft, not two — they're the same section."
- "Item 6 is right, skip it."
- "Items 8-9 confirmed deferred."
- "Proceed with the rest."

**After human adjusts:** 5 items land in `draft/`, each pre-tagged with its JM step.

**Then normal flow resumes:** Each draft item gets groomed and executed individually.

---

## 10. Grouping Intelligence

One thing the example above reveals: breakdown shouldn't just split — it should also **suggest groupings.** Items 2 and 3 are both "JM1 Step 1 Client UX" and probably should be one execution unit. Item 5 and 7 are both "JM1 Step 3 Client UX."

Breakdown should output a **suggested grouping** alongside the item list:

```
Suggested execution groups:
  Group A (JM1 Step 1 Client UX): Items 2, 3 → single draft
  Group B (JM1 Step 2 Client UX): Item 4 → single draft
  Group C (JM1 Step 3 Client UX): Items 5, 7 → single draft
  Standalone: Item 1 (CHORE, prerequisite for Groups A-C)
```

The human approves or adjusts the grouping, then breakdown promotes the groups as draft files. This prevents the "20 tiny tasks that should have been 3 features" problem.

---

## 11. Integration with kh.sh

### New commands needed:

```bash
kh raw "name" <<< "messy text"     # Intake from stdin
kh raw "name" < file.md            # Intake from file
kh raw "name"                      # Opens $EDITOR for input

kh breakdown "name"                # Run AI triage on raw input
kh breakdown "name" --dry-run      # Show what would happen without promoting

kh raw list                        # List all raw inputs + status
kh raw show "name"                 # Show raw input + breakdown results
```

### --dry-run explained

`kh breakdown "name" --dry-run` runs the full AI analysis but **writes nothing**. It prints
the breakdown report to stdout so you can see the categorization, grouping suggestions,
and routing decisions before any files are created or promoted. Think of it as "show me
what you WOULD do." If it looks right, run `kh breakdown "name"` without `--dry-run` and
everything auto-promotes.

### New state transitions:

```
raw (stored)  →  breakdown (analyzed)  →  draft (promoted)
                                       →  deferred (TERMINAL — documented, parked)
                                       →  rejected (TERMINAL — documented, closed)
```

**Deferred and rejected are TERMINAL states** — like `complete/`, they're done. The
`_deferred.md` and `_rejected.md` files are reference documents, not queues. If a
deferred item becomes relevant later (e.g., BYOL gets prioritized), the human creates
a NEW raw input or draft for it. They don't "un-defer" the old item. This keeps the
system clean — no zombie items cycling between states.

### state.json changes:

```json
{
  "raw_items": [
    {
      "id": "portal-lab-observations",
      "raw_file": "raw/portal-lab-observations.md",
      "status": "broken_down",  // "pending" | "broken_down"
      "breakdown_file": "raw/portal-lab-observations_breakdown.md",
      "promoted_drafts": ["jm1-step1-lab-order-details", "jm1-step3-lab-results"],
      "deferred_count": 2,
      "rejected_count": 1,
      "breakdown_at": "2026-02-12T14:30:00Z"
    }
  ],
  "items": [...]  // existing
}
```

---

## 12. What Breakdown Needs to Know

For breakdown to categorize accurately, it needs context:

1. **Known JMs:** List of journey mappings with their steps. Source: `docs/JOURNEY_MAPPINGS.md`
2. **Known UFs:** List of user flows per JM. Source: `docs/USER_FLOWS.md`
3. **JM Completeness Checklist:** For gap-detection heuristics. Source: `.kh/templates/JM_COMPLETENESS_CHECKLIST.md`
4. **Existing drafts:** To detect redundancy. Source: `.kh/draft/` + `.kh/state.json`
5. **Existing completed items:** To detect "already built." Source: `.kh/complete/` + `.kh/state.json`

This is a **read-only** operation. Breakdown doesn't modify any of these sources. It reads them, uses them for classification, and outputs its analysis to `raw/`.

---

## 13. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breakdown misclassifies items | Medium | Human review gate before promotion. `--dry-run` flag for preview. |
| Over-splitting (20 tiny items) | Medium | Grouping intelligence (Section 10). Human adjusts groups. |
| Under-splitting (items stay clumped) | Low | Human can re-run breakdown with hints, or manually split in draft. |
| Adds complexity to 1KH | Medium | Keep breakdown stateless — it reads raw, writes analysis, promotes to draft. No new daemon, no polling. |
| Breakdown tries to groom | High | Hard boundary: breakdown outputs category + JM mapping + original text. NO acceptance criteria, NO technical scope, NO implementation hints. |
| Raw items accumulate forever | Low | `kh raw list` shows status. `kh raw archive` moves old items to `raw/archive/`. |

---

## 14. Recommendation

**Build it as a separate pre-flow.** The arguments for separation are stronger:

1. **Different cognitive task** — splitting ≠ scoping ≠ building.
2. **Human review gate** — catch misclassifications before any code runs.
3. **JM Completeness Checklist integration** — breakdown becomes the first consumer of the checklist we just built.
4. **Grooming stays focused** — no "oh wait, this is actually 3 items" mid-session.

**Implementation order:**

1. `kh raw` command (just storage — trivial)
2. Breakdown report format (the `_breakdown.md` template)
3. `kh breakdown` command with `--dry-run`
4. Promotion logic (breakdown → draft)
5. Grouping intelligence
6. state.json integration

But before ANY implementation: this document needs your review. The walked example in Section 9 is the best test — does that match how you'd want the 9 portal observations to flow?

---

## 15. Resolved Decisions (from owner feedback)

All 11 feedback items have been resolved:

### Decision 1: Auto-promote ✅
**Resolved:** Breakdown auto-promotes to `draft/`. No separate `kh promote` step.

The human review gate is the `_breakdown.md` report + the `--dry-run` flag. If the human
wants to preview first, they use `--dry-run`. Otherwise, `kh breakdown` categorizes AND
promotes in one step. Adding an explicit promote command is an extra gate that slows down
the common case (most breakdowns are straightforward).

If the human disagrees with a promotion after the fact, they can delete or move the draft
file. Drafts are cheap — they haven't been groomed or executed yet.

### Decision 2: JM mapping granularity — specific UF level ✅
**Resolved:** Breakdown should map all the way down to specific UFs (e.g., "UF-C09: View Lab Results").

**Is this expensive?** Not particularly. Breakdown already reads `JOURNEY_MAPPINGS.md` and
`USER_FLOWS.md` as context (Section 12). Mapping to a specific UF is just a lookup against
data already in the context window. It doesn't require additional AI calls — it's the same
triage pass, just more precise. The cost is in the context window size (loading the full UF
catalog), not in compute time. Since breakdown runs its own dedicated session (not sharing
context with grooming or execution), the extra context is well-spent.

### Decision 3: Heuristic, not full checklist run ✅
**Resolved:** Breakdown uses the JM Completeness Checklist layers as **heuristics** for
classification, not as a full 7-minute run. Full checklist runs are reserved for:
- New JM creation (during grooming or dedicated sessions)
- Post-implementation review

### Decision 4: Cross-JM items → one CHORE draft ✅
**Resolved:** Items spanning multiple JMs become one `CHORE` draft flagged as "cross-JM"
with references to each JM it serves. Grooming decides how to scope and implement.

### Decision 5: Re-running breakdown — version, not overwrite ✅
**Resolved:** If the raw input has CHANGED, create a **new version** of the breakdown:

```
raw/portal-observations.md                    # original raw (immutable after first breakdown)
raw/portal-observations_breakdown.md          # first breakdown
raw/portal-observations_v2.md                 # updated raw input
raw/portal-observations_v2_breakdown.md       # second breakdown
```

If the raw input is the SAME but context has changed (new JMs defined, new UFs added),
re-running `kh breakdown` overwrites `_breakdown.md` since the raw source is unchanged —
only the classification context evolved. But previously promoted drafts are NOT deleted.
They stay in `draft/` (or wherever they've moved). The human resolves any duplication
manually — the system flags potential overlaps in the new breakdown report:

```
⚠ Item 3 may overlap with existing draft: jm1-step1-lab-order-details.md
  (promoted from previous breakdown on 2026-02-12)
```

This avoids silent duplication while keeping the system honest about what changed.

### Additional resolutions from feedback:

**#1 — JM Completeness Checklist integration:** Done. Template exists at
`.kh/templates/JM_COMPLETENESS_CHECKLIST.md`. Now formally referenced in
GROOMING_STANDARDS.md (new "JM Completeness Checklist" section + "Overload Detection").

**#2 — Design doc location:** Moved to `docs/TEMP_DOCS/DESIGN_RAW_BREAKDOWN_DRAFT.md`.

**#3 — Grooming kickback:** Formalized. Grooming emits `[PHASE: GROOMING_REJECTED — OVERLOADED]`
and routes back to `raw/`. Updated in GROOMING_STANDARDS.md (Overload Detection section).

**#4 — Full flow name:** Confirmed: `raw → breakdown → draft → execute`.

**#5 — Raw input preserved:** Confirmed. Raw is NEVER deleted — it's the source of truth.

**#6 — Grouping intelligence:** Confirmed. Breakdown suggests execution groups. Human
approves/adjusts before promotion. Like items within the same JM step get grouped.

**#7 — Deferred/rejected are terminal:** Confirmed. These are closed states, not queues.
If a deferred item becomes relevant, create a new raw input.

**#8 — UF tracking:** Confirmed UFs are tracked in `docs/USER_FLOWS.md`. Breakdown reads
this as context for classification. Lots of updates needed as JMs expand, but the structure
is sound.

**#9 — What breakdown needs to know:** Confirmed. Section 12 is approved as-is.

**#10 — Breakdown is optional:** Confirmed. Discrete items bypass straight to `draft/`.
Grooming kicks back to `raw/` if it encounters an overloaded item. Self-correcting loop.

---

## 16. Remaining Open Question

One question remains unresolved:

**Should `kh breakdown` require the human to review `_breakdown.md` before auto-promoting,
or promote immediately?**

Current decision: auto-promote immediately (Decision 1). But the user could also use
`--dry-run` first for anything they're unsure about. This feels right — fast by default,
cautious when needed. But worth noting as a potential adjustment if auto-promotion causes
problems in practice.
