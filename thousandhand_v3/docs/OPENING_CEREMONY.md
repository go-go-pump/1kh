# Opening Ceremony — Foundation Capture & Business Discovery

> **Type:** Process Requirements Document (Generic)
> **Consumed By:** 1KH Orchestrator (first-run) or Executor (manual init)
> **Produces:** Foundation Documents (North Star, Oracle, Context)
> **Version:** 1.0
> **Created:** 2026-02-09

---

## 1. Purpose

The **Opening Ceremony** is the first interaction between a founder and 1KH. It captures the founder's business idea, values, constraints, and preferences into Foundation documents that every downstream layer reads.

This is a **lightweight conversation** — not a business plan exercise. The goal is to extract enough signal to feed IMAGINATION with a starting hypothesis, while being honest that at this stage, nobody knows if the idea has UTILITY, FEASIBILITY, or VIABILITY. The Opening Ceremony is brainstorming the grocery list. We haven't left the building to buy the spaghetti, much less thrown it at the wall.

### What It Produces

Three Foundation documents:

- **North Star** — The business objective. What does success look like? What are we driving toward? This is the compass, not the map.
- **Oracle** — Values and constraints. What will we NEVER do? What must ALWAYS be true? These are the guardrails that survive pivots.
- **Context** — Preferences, resources, constraints, initial ideas, technical leanings, risk tolerance, founder background. This is the texture that makes the system feel like the founder's system.

### What It Does NOT Produce

- A business plan (too heavy, too early)
- A technical architecture (that's IMAGINATION → WORK)
- Revenue projections (that's SIMULATION)
- A validated idea (that's the whole point of the subsequent phases)

---

## 2. The Three Questions

The Opening Ceremony pushes the founder through three filters. These are asked lightly here — they'll be asked again with increasing rigor during Simulation and Execution.

### DESIRABILITY — "Do they want/need it?"

The executor explores:

- Who are the PEOPLE this system serves? Be specific — not "everyone" but "busy professionals aged 30-50 who want to lose weight but don't have time for traditional clinics."
- What pain does it solve? What's the current alternative? Why is the current alternative insufficient?
- What would make someone change their workflow to use this? What's the switching cost? What's the pull?
- Is there evidence of demand (even anecdotal)? Has the founder observed this need firsthand?

**Push for specificity.** "It helps people manage their health" is too vague. "Men over 35 who want structured nutrition and fitness plans integrated with lab work, delivered through a single portal with coaching support" — that's a hypothesis.

### FEASIBILITY — "Can we build it?"

The executor explores:

- What is the founder's technical capability? What can they build/manage themselves vs. what needs to be fully automated?
- Are there known technical risks? (Browser automation, government APIs, regulatory compliance, AI accuracy requirements)
- What integrations are required? (Payment processors, communication channels, scheduling tools, data sources)
- What is the founder's capacity? Full-time on this? Part-time with another job? How many hours per week?
- What's the timeline expectation? "Working in a week" vs. "ready in 6 months" changes everything.

**Be honest about limits.** If the founder wants real-time video processing and the tech stack is vanilla HTML/JS, that's a feasibility gap to surface now.

### VIABILITY — "Should we build it?"

The executor explores:

- Even if people want it and we can build it — will there be sufficient IMPACT?
- What does the founder's profit-and-purpose model look like? Pure revenue? Social impact? Combination?
- What's the revenue model? Subscription, one-time, freemium, advertising, something else?
- What's the competitive landscape? Are there incumbents? What's the differentiation?
- What happens at scale? Does the business model get better or worse with more users?
- What are the regulatory/legal considerations?

**Viability is market response.** It's the prediction. The founder might say "everyone wants this" but the market might not respond. Note the uncertainty — don't pretend to know.

---

## 3. The Conversation Flow

The Opening Ceremony is a guided conversation, not a form. The executor adapts based on the founder's responses. However, the conversation must cover these stages:

### Stage 1: The Idea (5-10 minutes)

"Tell me about your business idea. What problem are you solving and for whom?"

Let the founder talk. Don't interrupt with structure yet. Listen for:

- The core value proposition (what UTILITY does it provide?)
- The target audience (which PEOPLE?)
- The founder's passion and motivation (this informs Oracle values)
- Any existing work or research (this informs Context)

### Stage 2: The Values (5-10 minutes)

"What are the non-negotiables? What must always be true about how this operates?"

Push for specifics:

- "Never spam users" → How do we define spam? What's the communication philosophy?
- "Always put users first" → What does that mean when user interests conflict with revenue?
- "No unencrypted PII" → What's the data handling philosophy?
- "Profit and purpose" → What's the purpose component?

These become the Oracle. They should be short, memorable, and testable.

### Stage 3: The Minimum (5-10 minutes)

"What's the minimum set of capabilities that would make this genuinely useful — not just launched, but actually changing someone's life?"

This is the MVP exploration. Push the founder past "just a landing page" toward the actual desirability threshold:

- "If someone signed up tomorrow, what would they be able to DO?"
- "What's the one thing that, if it didn't work, the whole system has no value?"
- "What combination of features creates the 'aha' moment?"

Capture this as the initial hypothesis for IMAGINATION.

### Stage 4: The Context (5-10 minutes)

Practical questions that inform how 1KH operates:

- Technical preferences (languages, frameworks, hosting, existing accounts)
- Risk tolerance (conservative vs. aggressive, preference for escalation vs. autonomy)
- Communication style (detailed updates vs. "just tell me when it's done")
- Available resources (budget, time, existing assets, team)
- Decision-making style (data-driven, intuition-driven, delegator)
- Known constraints (regulatory, timeline, budget ceilings)

### Stage 5: Feedback Loop (5 minutes)

Read back the captured Foundation documents. Ask the founder:

- "Does this North Star capture what you're driving toward?"
- "Are these Oracle values right? Anything missing? Anything wrong?"
- "Does this Context feel like YOU?"

Iterate until the founder confirms. This is the first calibration — it establishes the trust relationship between founder and system.

---

## 4. Foundation Document Formats

### North Star

```markdown
# North Star — [Business Name / Working Title]

## Objective
[1-2 sentences. What does success look like? Be measurable where possible.]

## Audience
[Who are the PEOPLE? Be specific.]

## Value Proposition
[What UTILITY does this provide? What changes in someone's life when they use this?]

## Impact Goal
[What IMPACT are we driving toward? Revenue target, social impact metric, reach goal, or combination.]

## MVP Hypothesis
[What is the minimum set of capabilities that crosses the desirability threshold?]
```

### Oracle

```markdown
# Oracle — [Business Name / Working Title]

## Values
[Numbered list of non-negotiable principles. Each should be testable —
 "never do X" is testable, "be good" is not.]

## Constraints
[Hard limits: regulatory requirements, budget ceilings, timeline deadlines,
 technical non-negotiables.]

## Anti-Patterns
[Specific things the system must NEVER do or suggest. These are the guardrails
 that catch misalignment early.]
```

### Context

```markdown
# Context — [Business Name / Working Title]

## Founder Profile
[Background, skills, availability, decision-making style, risk tolerance.]

## Technical Preferences
[Languages, frameworks, hosting, existing accounts, tools already in use.]

## Communication Preferences
[How often, how detailed, what format for updates and escalations.]

## Existing Assets
[Any existing code, designs, content, accounts, domains, integrations.]

## Known Risks
[Regulatory, competitive, technical, personal risks the founder is aware of.]

## Seeds
[Initial ideas, feature concepts, hypotheses the founder wants to explore.
 These feed IMAGINATION as starting material.]
```

---

## 5. Post-Ceremony State

After the Opening Ceremony completes, the project has:

- Three Foundation documents (North Star, Oracle, Context) in the project's doc directory
- An initial ARCHITECTURE.md stub referencing the Foundation docs
- At least one MVP hypothesis ready for IMAGINATION to evaluate
- A founder preference profile that informs all downstream escalation and communication

What the project does NOT have:

- Validated desirability (we don't know if people want it)
- Validated feasibility (we don't know if we can build it)
- Validated viability (we don't know if it will generate impact)
- Any code, tests, or deployable artifacts

The next step is either SIMULATION (to stress-test the hypothesis before building) or direct entry into the Orchestrator (if the founder wants to skip simulation and build immediately — their choice, noted as a risk tolerance preference in Context).

---

## 6. Encoded Preferences

One critical output of the Opening Ceremony is encoding the founder's preferences into machine-readable form. "Go with your gut" is a valid instruction for an experienced human developer, but 1KH sessions need the "gut" to be explicit.

During the conversation, the executor captures preference signals and encodes them:

```json
{
  "risk_tolerance": "moderate",
  "escalation_preference": "escalate_critical_only",
  "communication_frequency": "daily_summary",
  "decision_style": "recommend_and_proceed",
  "test_coverage_priority": "high",
  "ux_fidelity_priority": "functional_over_beautiful",
  "tech_stack_flexibility": "opinionated",
  "autonomy_level": "high"
}
```

These preferences are stored in Context and referenced by GROOMING (when deciding how much detail to include in handoffs), EXECUTION (when deciding how to handle ambiguous design choices), and REFLECTION (when analyzing decision trends).

The preferences are not final — REFLECTION's trend detection (ARCH_V3 Section 11.6) will propose updates as the founder's actual behavior reveals more about their true preferences.

---

## 7. Re-Opening

The Opening Ceremony can be re-invoked when:

- A PIVOT-level Foundation change is approved (new direction, fundamentally different vision)
- A new system is being added to an existing business context
- The founder's circumstances change significantly (new resources, new constraints, new market information)

Re-opening reads the existing Foundation docs as starting state and guides the founder through targeted updates rather than starting from scratch.

---

## 8. Success Criteria

The Opening Ceremony is **complete** when:

- [ ] North Star document exists with measurable objective and specific audience
- [ ] Oracle document exists with at least 3 testable values/constraints
- [ ] Context document exists with founder profile, technical preferences, and risk tolerance
- [ ] At least one MVP hypothesis is captured in North Star or Context seeds
- [ ] Founder has reviewed and confirmed all three documents
- [ ] Encoded preferences are stored in Context
- [ ] ARCHITECTURE.md stub is created with Foundation doc references

The Opening Ceremony is **incomplete** if:

- The founder cannot articulate who the PEOPLE are (audience is too vague)
- The founder cannot identify at least one non-negotiable value (Oracle is empty)
- There is no hypothesis to hand to IMAGINATION (no seeds)

In these cases, the executor should note the gaps, provide the founder with reflection prompts, and schedule a follow-up conversation.

---

**This document defines the Opening Ceremony process. See ARCH_V3.md Section 0 for the definitions that inform it.**
