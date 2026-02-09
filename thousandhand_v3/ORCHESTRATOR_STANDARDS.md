# Orchestrator Standards — MVP Planning & Simulation Framework

> **Type:** Process Requirements Document (Generic)
> **Consumed By:** 1KH Orchestrator, IMAGINATION layer, INTENT layer
> **Purpose:** Defines HOW the Orchestrator plans MVPs and runs simulations
> **Version:** 1.0
> **Created:** 2026-02-09

---

## 1. Purpose

The Orchestrator is responsible for driving a BUSINESS CONTEXT from Foundation docs to working SYSTEMS. It operates the full internal flow (Foundation → Imagination → Intent → Work → Grooming → Execution) and performs two critical pre-build activities:

1. **MVP Planning** — Identifying the minimum set of capabilities that crosses the desirability threshold
2. **Simulation** — Stress-testing the idea AND the process before committing to execution

This document defines the standards for both.

---

## 2. MVP Planning

### The MVP Threshold

The Orchestrator pushes the founder toward MVP, but MVP does not mean "minimum effort." It means **minimum capability to deliver minimum desirability for minimum viability.**

Minimum desirability has a higher threshold than most founders assume. One tool often isn't enough to change someone's workflow. The right combination of tools that changes a workflow in such a way that someone starts making serious progress — that's game-changing. That's the MVP.

Example: For an EHR, it's not enough to just be another clinic website. You need intake → recommendations → lab ordering → nutrition plans → fitness plans → coaching integration. That combination IS the MVP. Any less and the desirability threshold isn't crossed.

### MVP Identification Process

The Orchestrator works with IMAGINATION and INTENT to identify MVP:

1. **Start from North Star** — What did the founder say success looks like?
2. **List all envisioned capabilities** — Everything the founder wants (from Context seeds)
3. **Filter by desirability** — For each capability, ask: "If this were missing, would a user still change their workflow?" Remove everything where the answer is "yes, they'd still switch"
4. **Filter by feasibility** — For remaining capabilities, ask: "Can we build this locally with the default stack?" Flag anything that requires production integrations
5. **Filter by viability** — For the remaining set, ask: "Does this combination generate enough impact to sustain the business?" If not, add back the minimum needed
6. **Define the MVP boundary** — The surviving set is the MVP. Everything else is post-MVP

### MVP Documentation

The Orchestrator produces an MVP definition that feeds WORK:

```markdown
## MVP Definition — [System Name]

### Core Capabilities (must ship together)
1. [Capability] — [Why it's essential for desirability threshold]
2. [Capability] — [Why it's essential]
...

### Deferred Capabilities (post-MVP)
1. [Capability] — [Why it can wait] — [What trigger brings it back]
2. ...

### MVP Hypothesis
"If we deliver [core capabilities] to [target audience], we expect [measurable outcome]
within [timeframe]. We'll know it worked when [test condition]."

### Technical Boundary
- Local-only: [Yes/No — if No, what production dependency is required and why]
- Default stack: [Yes/No — if No, what override and why]
- Estimated scope: [S/M/L] — [number of features, estimated sessions]
```

---

## 3. Simulation

### What Simulation Is

Simulation is a **ceremony** — an exchange event between 1KH and the founder. The Orchestrator performs it AFTER MVP planning and BEFORE committing to full execution. It runs a virtualized walkthrough of the system's path from idea to impact.

Simulation tests two things:

1. **The IDEA** — Will this system achieve the impact the founder envisions?
2. **The PROCESS** — Can 1KH actually orchestrate the construction of this system?

### Multi-Phase Scope

Critically, simulation does NOT only consider the current phase. It considers the **CURRENT PHASE AND ALL SUBSEQUENT PHASES** — emulating the full cycle over many phases to reveal risks that only surface at scale or over time.

This is especially valuable in **Phase 1** where NO MARKET DATA exists. Without real user behavior to inform decisions, simulation offers REFLECTION-like feedback to IMAGINATION before anything is built. It can push back on FOUNDATION assumptions, stress-test USER FLOWS, and identify where the MVP hypothesis is weakest — all before a single line of code is written.

Example: A Phase 1 simulation might reveal that the MVP's payment integration (Phase 1) depends on a subscription model (Phase 2) that requires usage analytics (Phase 3) that assumes a user base of 500+ (Phase 4). If the Phase 4 assumption is unrealistic, the entire chain unravels — and simulation catches this before Phase 1 build begins.

### What Simulation Is NOT

- Not a prototype (no code is written)
- Not a market research study (no customers are contacted)
- Not a financial model (no spreadsheets)
- Not a guarantee (it's a stress test, not a prediction)

### When to Simulate

Simulation is recommended when:

- The MVP is non-trivial (3+ features, multiple user types, complex integrations)
- The founder is investing significant resources (time, money, opportunity cost)
- There are known risk factors (regulatory, competitive, technical uncertainty)
- The founder wants confidence before committing to build
- Phase 1 with no existing market data (simulation is the only pre-build feedback mechanism)

Simulation can be skipped when:

- The founder explicitly wants to "just build it" (noted as risk tolerance in Context)
- The MVP is small enough to build quickly (1-2 features, single user type)
- The cost of simulation exceeds the cost of building (very small projects)

### Simulation Assumptions

Simulation assumes the full Orchestrator is working (Foundation → Imagination → Intent → Work → Grooming → Execution). The simulation runs through this flow with MOCK EVENTS rather than real execution. The simulation considers all phases from current through projected future, not just the immediate build phase.

---

## 4. Simulation Framework

### 4.1 Risk Dimensions

The simulation evaluates the idea across multiple risk dimensions:

**Founder Risk** — Could the founder unwittingly be their own enemy?

- Participation sensitivity: Is the project sensitive to how much they participate? Or can it largely run on its own?
- Distraction patterns: What happens if the founder drifts, adds distractions, doesn't execute?
- Trust patterns: What if they don't trust the process and start doing their own thing?
- Decision latency: What if they're slow to approve escalations?

**Technical Risk** — Could unforeseen technical challenges kill the project?

- Integration complexity: How many external services? How stable are their APIs?
- Data sensitivity: PII, HIPAA, financial data — what are the compliance requirements?
- Scalability cliffs: Does the architecture hit walls at certain user counts?
- AI dependency: How much relies on AI accuracy? What's the fallback if AI is wrong?

**Market Risk** — Could the market respond differently than expected?

- Demand validation: Is there evidence beyond the founder's intuition?
- Competitive response: What if an incumbent copies the feature set?
- Margin sensitivity: What happens to margins at scale? Higher overhead? Diminishing returns?
- Timing risk: Is this time-sensitive? What happens if development takes 2x longer?

**External Risk** — Could outside forces derail the project?

- Regulatory changes: New laws, compliance requirements
- Economic conditions: Downturn, funding dry-up, customer spending reduction
- Legal exposure: Patent issues, liability, terms of service violations
- Platform dependency: What if a key platform (Stripe, AWS, etc.) changes terms?

### 4.2 Simulation Runs

A simulation consists of multiple RUNS — each exploring a different scenario path.

**Happy Path Run** — Everything goes according to plan. MVP ships on time, market responds positively, founder is engaged. This establishes the baseline.

**Sad Path Runs** — Each explores a specific failure mode:

- **Negative market response** — The system ships but adoption is 20% of expectation. What happens to viability?
- **Undeliverable functionality** — A core MVP feature turns out to be infeasible mid-build. What's the fallback?
- **Founder drift** — The founder gets busy, doesn't respond to escalations for 2 weeks. Does the project stall completely?
- **Technical surprise** — A critical integration has unexpected limitations (rate limits, missing API features). How does the system adapt?
- **Scaling pressure** — Early traction creates demand beyond what the local system can handle. What's the path to production?

**Chaos Run** — Multiple things go wrong simultaneously. Economic downturn + founder distraction + technical setback. How resilient is the plan?

### 4.3 Simulation Output

Each run produces:

```markdown
## Simulation Run: [Scenario Name]

### Scenario
[What happened in this run — the mock events and conditions]

### Path Taken
[How the Orchestrator responded at each decision point]

### Outcome
[What state the system ended in — success, partial success, failure]

### Risks Revealed
[What this run taught us — new risks, confirmed risks, mitigated risks]

### Risk Level: [LOW | MEDIUM | HIGH | CRITICAL]

### Recommendation
[What should change in the plan, if anything]
```

### 4.4 Simulation Report

After all runs, the Orchestrator produces a consolidated report:

```markdown
# Simulation Report — [System Name]

## Summary
- Total runs: X
- Happy path: [outcome]
- Sad paths: Y runs, Z revealed critical risks
- Chaos: [outcome]

## Critical Findings
[Risks that change the Foundation docs or MVP definition]

## Risk Registry
| Risk | Dimension | Likelihood | Impact | Mitigation |
|------|-----------|-----------|--------|------------|

## Recommendation
[PROCEED | PROCEED WITH CAUTION | RECONSIDER | ABORT]
[Rationale]

## MVP Adjustments
[Any changes to the MVP definition based on simulation findings]

## Foundation Updates
[Any changes to North Star, Oracle, or Context needed]
```

### 4.5 Auto-Accept vs. Critical Review

Eventually, the founder could **auto-accept** simulation findings unless presented with CRITICAL findings that would change Foundation docs.

- **LOW/MEDIUM risks** → Logged in risk registry, founder notified in summary, no blocking review needed
- **HIGH risks** → Highlighted in report, founder should review but can auto-accept
- **CRITICAL risks** → Blocks progression. Founder must explicitly acknowledge and either accept the risk, adjust the plan, or abort

---

## 5. The Learning Question

If a simulation doesn't teach us something, it's not worth running. Before each run, the Orchestrator should articulate:

"What are we trying to learn from this run?"

Possible learnings:

- "Is the idea going to struggle producing DESIRABILITY?" → Run market response scenarios
- "Is the idea going to struggle producing FEASIBILITY?" → Run technical challenge scenarios
- "Is the idea going to struggle producing VIABILITY?" → Run margin/scale scenarios
- "Is the PROCESS going to struggle?" → Run founder-behavior and orchestration-load scenarios
- "Are there RISKS or PITFALLS we haven't thought of?" → Run chaos scenarios

If we aren't learning, we're wasting time. And if the exercise reveals that the exercise itself is a waste of time — that's a valuable finding that saves the founder from committing resources to a doomed approach.

---

## 6. Simulation Maturity

Simulation is the least mature part of the 1KH framework. The framework above is a starting structure, not a proven process.

### What We Know Works

- Running mock data through orchestration flows to see what they produce (proven in v2 forecast)
- Using live Claude calls to evaluate how the system responds to mock events (proven in v2 simulation experiments)
- Testing happy and sad paths against idea viability (standard practice)

### What Needs Exploration

- **Founder modeling** — How accurately can we simulate founder behavior patterns? This is novel territory.
- **Market response modeling** — How much can we infer from research vs. how much is unknowable without real users?
- **Fidelity vs. cost tradeoff** — How detailed should simulation runs be? High-fidelity costs tokens. Low-fidelity might miss critical risks.
- **Iterative refinement** — How do we calibrate simulation accuracy over time as we compare predictions to actual outcomes?

### The Honest Assessment

Simulation at this stage is more of a structured brainstorming exercise than a predictive model. Its primary value is forcing systematic thinking about risks that founders typically skip — especially founder-risk and market-risk. The quantitative aspects (likelihood, impact ratings) are educated guesses. The qualitative aspects (risk identification, mitigation planning) are where the real value lies.

As 1KH matures and we accumulate data from real projects, simulation fidelity should improve. But v1 simulation is intentionally humble about its predictive power.

---

## 7. Post-Simulation → Execution

After simulation, the Orchestrator has:

- A validated (or adjusted) MVP definition
- A risk registry with mitigations
- Confidence level: PROCEED / PROCEED WITH CAUTION / RECONSIDER / ABORT
- Any Foundation doc updates applied

If PROCEED or PROCEED WITH CAUTION:

1. The Orchestrator enters the execution phase
2. IMAGINATION generates hypotheses from the MVP definition
3. INTENT prioritizes and decides
4. WORK decomposes into tasks
5. GROOMING hydrates with project context + Executor Standards
6. EXECUTION builds, following Executor Standards

The Orchestrator monitors execution against the risk registry — if a simulated risk materializes, the pre-planned mitigation activates rather than requiring emergency decision-making.

---

## 8. Relationship to Other Documents

| Document | How Orchestrator Standards Relates |
|----------|-----------------------------------|
| **ARCH_V3.md** | Orchestrator Standards operationalizes the ceremony flow from Section 0 and the layer model from Sections 1-3 |
| **OPENING_CEREMONY.md** | Produces the Foundation docs that Orchestrator reads as input |
| **EXECUTOR_STANDARDS.md** | Defines how execution sessions operate once the Orchestrator decides to build |
| **CLOSING_CEREMONY.md** | Defines what happens after execution completes — UAT and GTM |

---

**This document will evolve significantly as simulation patterns mature through real project experience. Treat it as a v1 framework, not a finished process.**
