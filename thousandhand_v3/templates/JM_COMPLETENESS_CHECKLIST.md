# JM Completeness Checklist

> Run this checklist against any initial product prompt or JM draft to surface missing
> flows, states, actors, and edge cases BEFORE building. The goal is to find the gaps
> that founders discover organically over weeks — in one structured pass.
>
> This is NOT a template to fill out. It defines a layered analysis process.

---

## When to Use

- **New JM creation:** Run all 5 layers against the initial prompt/description
- **JM grooming:** Run Layers 2-5 against any step being groomed for execution
- **Post-implementation review:** Run Layer 5 against built steps to verify nothing was missed
- **Bulk intake triage:** Run Layer 1 to classify raw items before breakdown

---

## Layer 1 — Actor Enumeration

> Most initial prompts only mention 1-2 actors. Every missing actor is a missing set of flows.

**Process:** For every noun in the prompt that takes an action or receives information, ask:

```
□ Who INITIATES this action?
□ Who RECEIVES the result?
□ Who MONITORS for problems?
□ Who INTERVENES when something goes wrong?
□ Is there a SYSTEM actor (cron, webhook, workflow) doing work between human actions?
□ Is there an EXTERNAL SERVICE (API, third-party) that acts as a participant?
```

**Output:** Complete actor list. For each actor, note:
- What they can SEE (read access)
- What they can DO (write access)
- When they need to be NOTIFIED

**Red flag:** If the prompt mentions only "user" and "system," you're missing at minimum
an admin/operator actor and likely an external service actor.

---

## Layer 2 — Entity State Mapping

> For every data entity in the system, enumerate ALL possible states.
> Each state transition is either a human action, a system event, or time passing.
> Missing states = missing flows.

**Process:** For each entity (table/record) in the JM:

```
□ List every possible status/state value
□ For each state transition: what TRIGGERS it? (human action / system event / time)
□ For each state: what does each ACTOR see when the entity is in this state?
□ Are there any TERMINAL states? (completed, cancelled, expired)
□ Are there any ERROR states? (failed, stuck, requires_intervention)
□ Can the entity move BACKWARDS? (reopen, retry, revert)
```

**Output:** State diagram per entity. Format:

```
entity_name:
  STATE_A → STATE_B  (trigger: human action by Actor X)
  STATE_B → STATE_C  (trigger: system event — Lambda/Temporal/webhook)
  STATE_B → STATE_E  (trigger: timeout — 3 days no action)
  STATE_C → STATE_D  (trigger: human action by Actor Y)
  STATE_* → ERROR    (trigger: external service failure)
```

**Red flag:** If an entity has fewer than 4 states, you're probably missing error handling
and timeout paths. Real-world entities almost always have: initial, in-progress, complete,
error, and at least one timeout/escalation state.

---

## Layer 3 — "What If They Don't?" Analysis

> For every human action in the JM, ask what happens if the human does NOT do it.
> This single question generates roughly half of all user flows in a mature product.

**Process:** For each step where a human actor must take an action:

```
□ What if they NEVER do it? (abandoned flow — needs reminders + escalation)
□ What if they do it WRONG? (validation, error recovery, retry)
□ What if they do it LATE? (still valid? degraded experience? escalation?)
□ What if they do it TWICE? (idempotency — system must handle gracefully)
□ What if they UNDO it? (cancel, refund, revert — is this possible? should it be?)
```

**Output:** For each "what if they don't" scenario, classify as:

| Classification | Action |
|---------------|--------|
| **ABANDONMENT** | Define reminder cadence + escalation threshold → becomes a Temporal workflow |
| **VALIDATION** | Define error message + recovery path → becomes UI logic |
| **IDEMPOTENCY** | Define "already done" behavior → becomes backend guard |
| **REVERSAL** | Define undo/cancel flow → may become a new UF |
| **ACCEPTED_RISK** | Document why this is OK to ignore (with justification) |

**Red flag:** If you have more than 5 human actions in a JM and zero abandonment flows,
you're building a happy-path-only product.

---

## Layer 4 — Temporal Gap Analysis

> Where does time pass between steps? Every gap longer than a user session is a
> re-entry problem, a reminder opportunity, and an admin visibility need.

**Process:** Walk the JM timeline and identify every point where the user leaves:

```
□ Is there a gap > 1 hour between steps? → Session-Recovery needed
□ Is there a gap > 1 day? → Email/SMS reminder opportunity
□ Is there a gap > 3 days? → Escalation indicator for admin
□ Is there a gap where EXTERNAL PROCESSING happens? → Status page / polling needed
□ Can the user CHECK STATUS during the gap? → Portal state must reflect waiting
□ Does the admin need to SEE the gap? → Operations queue must show aging items
```

**Output:** Gap inventory with durations and required mechanisms:

```
Gap: Between purchase and lab order print
  Duration: minutes to days
  Client needs: reminder to print
  Admin needs: escalation indicator after 3 days
  System needs: Temporal workflow with reminder cadence

Gap: Between print and lab results
  Duration: 5-14 days (external: LabCorp processing)
  Client needs: status page showing "awaiting results"
  Admin needs: visibility into aging orders
  System needs: daily polling for results (Lambda/cron)
```

**Red flag:** If your JM has no temporal gaps, either it's a single-session flow (rare)
or you haven't thought about what happens between steps.

---

## Layer 5 — "Other Screen" Test

> For every action by any actor, ask: what does every OTHER actor see?
> This is how admin dashboards, notification systems, and audit trails emerge.

**Process:** For each step in the JM:

```
□ Client takes action → What does ADMIN see? (queue item? notification? nothing?)
□ Admin takes action → What does CLIENT see? (portal update? email? nothing?)
□ System processes something → Who gets NOTIFIED? (both? one? neither?)
□ Something fails → Who SEES the failure? (just logs? admin alert? client error page?)
□ Time passes → Is the AGING visible? (to admin? to client? to both?)
```

**Output:** Notification/visibility matrix:

```
Step: Client completes purchase
  Client sees: confirmation page, receipt email
  Admin sees: new item in ops queue
  System does: triggers lab order processing

Step: Lab results arrive (system event)
  Client sees: portal status update, email notification
  Admin sees: ops queue item updated, treatment plan available
  System does: AI processing, treatment plan generation
```

**Red flag:** If any step has "admin sees: nothing" for a client-facing action,
you probably need an ops queue entry or at minimum an audit log.

---

## Coverage Scoring

After running all 5 layers, score the JM:

| Dimension | Question | Score |
|-----------|----------|-------|
| **Actors** | Are all actors enumerated with read/write/notify access? | □ Yes □ Partial □ No |
| **States** | Does every entity have complete state diagrams including error/timeout? | □ Yes □ Partial □ No |
| **Sad Paths** | Does every human action have a "what if they don't" answer? | □ Yes □ Partial □ No |
| **Temporal** | Is every time gap documented with re-entry + reminder + escalation? | □ Yes □ Partial □ No |
| **Visibility** | Does every step have cross-actor visibility defined? | □ Yes □ Partial □ No |

**Scoring:**
- 5× Yes = Production-ready JM (rare on first pass)
- 3-4× Yes = Good draft, address Partial items before building
- 1-2× Yes = Needs another pass — significant gaps will surface during development
- 0× Yes = Prompt-stage — run full checklist before any implementation

---

## Quick-Run: From Prompt to Gap List

For rapid application against a new product prompt:

1. **Read the prompt once.** Highlight every noun (entity), verb (action), and actor.
2. **Layer 1 (30 sec):** Write down every actor. Add "admin" and "system" if missing.
3. **Layer 2 (2 min):** For each entity, list states. Mark any with < 4 states.
4. **Layer 3 (2 min):** For each human action, write the "don't" scenario. Count abandonment flows needed.
5. **Layer 4 (1 min):** Draw the timeline. Circle every gap > 1 hour.
6. **Layer 5 (1 min):** For each step, write what the OTHER actor sees.
7. **Count gaps.** Each gap is a flow, feature, or documented accepted-risk.

Total time: ~7 minutes. Output: a list of every flow the prompt didn't mention.

---

## Example Application

**Prompt:** "Create a purchase funnel where client can get recommendations for lab panels
and they can pay for them."

**Layer 1 — Actors found:** Client, System. **Missing:** Admin (who monitors?), Physician
(who signs orders?), LabCorp (external service), Payment provider (Square).

**Layer 2 — Entities:** lab_order has states: ??? Prompt only implies "ordered."
**Gap:** Need: pending, ordered, sent_to_patient, printed, results_received, failed, cancelled.

**Layer 3 — "What if they don't":**
- Don't complete intake → abandoned intake flow (2 reminders + close)
- Don't pay → abandoned cart flow (2 reminders + close)
- Don't print lab order → abandoned print flow (2 reminders + escalation)
- Don't visit LabCorp → no system visibility (accepted risk? or escalation?)

**Layer 4 — Temporal gaps:**
- Between payment and print: minutes-days → reminder needed
- Between print and LabCorp visit: days → no system visibility
- Between LabCorp and results: 5-14 days → polling + status page needed

**Layer 5 — "Other screen":**
- Client pays → admin sees... nothing? **Gap.** Need ops queue.
- Results arrive → client sees... nothing? **Gap.** Need portal update + email.

**Result:** 6 compact sentences in the prompt → 4 missing actors, 5+ missing states,
3 abandonment flows, 3 temporal gaps, 2 visibility gaps. ~15 additional flows identified.
