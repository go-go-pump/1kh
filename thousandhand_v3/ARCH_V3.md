# ThousandHand v3 — ARCHITECTURE

> The plan to go from values and objectives to working, tested, deployed systems — autonomously.

---

## 1. The v3 Flow

v3 introduces a layered architecture where each layer is a **loop** with forward output and backward feedback. The layers go from abstract (Foundation documents) to concrete (source code, tests, deployed artifacts).

```
FOUNDATION  ←→  (reflection)  ←→  IMAGINATION  ←→  (hypothesis)  ←→  INTENT  ←→  (decisions)  ←→  WORK  ←→  (tasks)  ←→  GROOMING  ←→  (handoffs)  →  EXECUTION
```

### Full Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│  ┌──────────┐     ┌─────────────┐     ┌────────┐     ┌──────┐     ┌─────────┐     │
│  │FOUNDATION│ ←─→ │ IMAGINATION │ ←─→ │ INTENT │ ←─→ │ WORK │ ←─→ │GROOMING │     │
│  └──────────┘     └─────────────┘     └────────┘     └──────┘     └────┬────┘     │
│       ↑               ↑                   ↑              ↑              │           │
│       │               │                   │              │              │ (REQ      │
│       │           reflection          hypothesis     decisions         │  HANDOFF) │
│       │           feedback            feedback       feedback          │           │
│       │               │                   │              ↑              ▼           │
│       │               │                   │              │        ┌──────────┐     │
│       │               │                   │              │        │EXECUTION │     │
│       │               │                   │              │        └────┬─────┘     │
│       │               │                   │              │             │           │
│       │               │                   │              │        (DELIVERY        │
│       │               │                   │              │         HANDOFF)        │
│       │               │                   │              │             │           │
│       │               │                   │              └─────────────┘           │
│       │               │                   │         task feedback                   │
│       │               │                   │         (split tasks,                   │
│       │               │                   │          update status)                 │
│       └───────────────┴───────────────────┘                                        │
│                 REFLECTION spans all layers                                         │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The Layer Model

### Core Principle: Each Layer is a Loop

Every layer has:
- **Forward output** (passes refined information to the next layer)
- **Backward feedback** (returns learnings to the previous layer)
- **Internal processing** (its own cycle of work)

### Abstraction Gradient

```
ABSTRACT ──────────────────────────────────────────────→ CONCRETE

FOUNDATION    IMAGINATION    INTENT    WORK    GROOMING    EXECUTION
(docs)        (hypotheses)   (decisions)(tasks) (handoffs)  (source code)
```

### Frequency & Depth Gradient

As we move from abstract to concrete:

| Property | Foundation | Imagination | Intent | Work | Grooming | Execution |
|----------|-----------|-------------|--------|------|----------|-----------|
| **Frequency** | Rarely changes | Per-cycle | Per-cycle | Many per cycle | Many per cycle | Continuous |
| **Depth** | High-level values | Scored hypotheses | Strategic choices | Actionable specs | Hydrated handoffs | Implementation detail |
| **Example** | "Never spam users" | "Email drives signups (82% viable)" | "Nurture email hypothesis" | "Build signup form, connect Mailchimp" | CC_HANDOFF with architecture, tests, deployment plan | React component, API route, Playwright test |

**Frequency example**: Tasks are more frequent than hypotheses; hypotheses more frequent than North Star objectives.

**Depth example**: Handoffs are deeper than tasks; tasks are deeper than decisions.

### Metrics at Every Level

Metrics can be derived at practically every layer:

| Layer | Example Metrics |
|-------|----------------|
| **EXECUTION** | Test PASS/FAIL, test coverage %, build success rate |
| **GROOMING** | Handoff quality, task split rate, escalation rate |
| **WORK** | Task throughput, blocked task count, dependency resolution time |
| **INTENT** | Decision accuracy (did nurturing actually help?), pivot frequency |
| **IMAGINATION** | Hypothesis hit rate, viability score accuracy vs actual |
| **FOUNDATION** | System health, trajectory toward North Star |

---

## 3. Layer Details

### 3.1 FOUNDATION (Base Layer)

**What it is**: The Oracle (values), North Star (objectives), Context (resources/constraints), Seeds (initial ideas), and Preferences.

**Forward output**: Foundation documents feed into IMAGINATION as the basis for hypothesis generation.

**Backward feedback**: REFLECTION can recommend Foundation-level review when stall patterns are detected (N flat cycles, M failed mechanisms).

**Change levels** (carried from v2):
- TWEAK — wording/clarification, absorbed silently
- ADJUST — narrow scope, re-score hypotheses
- PIVOT — new direction, major pruning (requires human approval)
- RESTART — fundamentally different vision, archive and begin again

### 3.2 IMAGINATION (Planning Layer)

**What it is**: Generates 3-5 hypothesis candidates from Foundation, decomposes into requirements, estimates viability via Capability Registry.

**Forward output**: Ranked hypotheses with viability scores, test conditions, and dependency maps → feeds INTENT.

**Backward feedback**: REFLECTION provides pattern data (what hypothesis types keep failing, what's working) → influences generation strategy.

**Viability thresholds** (carried from v2):
- Above 70% → recommend proceeding
- 40-70% → proceed but flag risks
- Below 40% → generate alternatives or escalate

### 3.3 INTENT (Decision Layer)

**What it is**: Observes tree state, evaluates active hypotheses, makes strategic decisions.

**Forward output**: Decisions (nurture, pivot, prune) with rationale → feeds WORK.

**Backward feedback**: IMAGINATION surfaces market response data and hypothesis outcomes → informs future decisions.

**Decision types** (carried from v2):
- AUGMENT — add missing capability
- OPTIMIZE — improve existing capability
- (PIVOT reserved for Foundation level only)

### 3.4 WORK (Task Layer)

**What it is**: Decomposes INTENT decisions into the three-level hierarchy: HYPOTHESIS → WORK ITEMS → TASKS.

**Forward output**: Stateless TASKS delivered to GROOMING.

**Backward feedback from GROOMING**:
- "This task should be split — parts belong to different build workflows"
- "This task overlaps with an existing task — consider merging"
- "This task's scope is unclear — needs refinement"

**Key distinction**: TASKS from WORK are **stateless** — they describe *what* needs to happen but don't carry project context, build workflow assignment, or session state. That's GROOMING's job.

### 3.5 GROOMING (Hydration Layer) ← NEW IN v3

**What it is**: The bridge between abstract TASKS and concrete EXECUTION. This is where KU's patterns integrate into 1KH.

**GROOMING has three primary functions:**

#### Function 1: Task Hydration (Forward — WORK → GROOMING → EXECUTION)

Takes a **stateless TASK** and produces a **stateful CC REQUIREMENT HANDOFF**:

1. **Reads** the incoming task from WORK
2. **Hydrates** with project context (TECH_STACK, ROADMAP, existing architecture docs, PRIMER)
3. **Classifies** triage level:
   - **FEATURE** — new functionality, significant additions
   - **MAJOR_FIX** — bug fix with broad impact
   - **SMALL_FIX** — targeted fix, config change, tweak
   - **DOCUMENTATION** — doc-only changes
4. **Assigns** workflow type:
   - **Build Workflow** — for features, big defects (the standard path)
   - **Meta Build Workflow** — when the required Build Workflow *does not yet exist*
   - **Document Workflow** — for basic document updates, global code fixes
5. **Produces** a REQ_HANDOFF document following KU's template structure:
   - Status, Triage, Objective, Background, Architecture, Implementation
   - Database Schema, Signals/Activities, UI Changes, Configuration
   - Files to Create/Modify, Testing guidance, Deployment steps
   - Success Criteria, Out of Scope, Questions, CC Processing Notes

**If GROOMING realizes parts of a task are better suited to a different Build Workflow**, it sends feedback to WORK to break down the task. Likewise, GROOMING detects overlap and merger opportunities.

#### Function 2: Delivery Processing (Backward — EXECUTION → GROOMING)

Receives a **DELIVERY HANDOFF** from EXECUTION and:

1. **Reviews** what was built, what passed, what failed
2. **Creates follow-up TASKS** to update architecture docs and status docs
3. **Grooms** those follow-up tasks as **Document Workflow** handoffs
4. This ensures cross-project alignment after every delivery

#### Function 3: Escalation Handling

- If a task cannot be groomed (ambiguous, conflicting requirements) → escalate to WORK with feedback
- If no Build Workflow exists for a task type → generate a **Meta Build Workflow Handoff** and invoke the Meta Build Workflow to create one
- If Meta Build Workflow fails to produce a viable first attempt → escalate back to WORK / human

**Model**: Sonnet (fast triage, context assembly)
**Tools**: Read, Write, Glob, Grep (no execution tools)
**Max turns**: 15

### 3.6 EXECUTION (Implementation Layer) ← NEW IN v3

**What it is**: Takes HANDOFFS from GROOMING and produces working, tested code.

**Two execution paths:**

#### Path A: Build/Meta Build Workflow (from REQ HANDOFF)

```
REQ HANDOFF (includes Test Execution Contract — see Section 6.1)
    │
    ▼
Build Workflow (or Meta Build Workflow)
    │
    ├──→ FIRST: Create TEST assets (Playwright specs, unit tests, workflow tests)
    │         + Create test runner script (bash, JSON output — see Section 6.2)
    │
    ├──→ THEN: Create OPS assets (source code, configs, deployments)
    │
    ├──→ Run tests via bash runner → read summary.json (token-efficient)
    │         │
    │         ├── ALL PASS → Mark Build Workflow as VALID
    │         │                Send DELIVERY HANDOFF (success + summary.json) → GROOMING
    │         │
    │         └── ANY FAIL → Read failure detail → Fix code → Re-run
    │                  │
    │                  ├── Fixed → Loop back (re-run, read summary, check)
    │                  │
    │                  └── Same failure 3x →
    │                       Mark Build Workflow as INVALID
    │                       Send DELIVERY HANDOFF (escalation + summary.json) → GROOMING
    │
    └──→ Evaluate: Is this REUSABLE or ONE-OFF?
              If reusable → publish as shared capability
              If one-off → document but don't generalize
```

#### Path B: Document Workflow (from Document Task)

```
DOCUMENT TASK HANDOFF
    │
    ▼
Document Workflow
    │
    ├──→ Update specified documents
    ├──→ Verify cross-references and alignment
    └──→ Simple feedback to GROOMING: completion status
```

**Model**: Opus (deep implementation, long context)
**Tools**: Read, Write, Edit, Bash, Glob, Grep (full power)
**Max turns**: 50
**Mode**: `--dangerously-skip-permissions` (aggressive execution)

**UX Test Standard (new in v3)**: UX tests should reveal errors — read them AND fix them. If the same issue cannot be fixed after repeated attempts, it gets escalated via the DELIVERY HANDOFF.

---

## 4. Feedback Loops in Detail

### 4.1 GROOMING → WORK (Task Feedback)

```
WORK creates TASK: "Build user authentication system"
                          │
                          ▼
                      GROOMING
                          │
              ┌───────────┼────────────┐
              │           │            │
         "Split this"  "Overlap"   "Unclear"
              │           │            │
              ▼           ▼            ▼
         WORK splits   WORK merges  WORK refines
         into 3 tasks  with existing  and re-sends
```

**When GROOMING pushes back:**
- Task spans multiple build workflow domains → split
- Task duplicates or overlaps with existing work → merge suggestion
- Task scope is ambiguous → request refinement with specific questions

### 4.2 EXECUTION → GROOMING (Delivery Feedback)

```
EXECUTION completes (or fails)
              │
              ▼
       DELIVERY HANDOFF
              │
     ┌────────┼────────┐
     │                  │
  SUCCESS            FAILURE
     │                  │
     ▼                  ▼
GROOMING creates    GROOMING creates
doc-update tasks    escalation task
     │                  │
     ▼                  ▼
Document Workflow   Routes back to WORK
updates arch docs   for re-planning
```

**The DELIVERY HANDOFF document is the feedback mechanism.** It contains:
- Summary of what was done (or couldn't be done)
- Deviation assessment (None / Minor / Significant)
- Completed items, blocked items, future TODOs
- Test results (passing / skipped / failing)
- Documentation updates needed
- Notes for the doc-update session

**On success**: GROOMING creates DOCUMENT WORKFLOW tasks to update ROADMAP, ARCHITECTURE, PRIMER, WORKFLOW_CATALOG — ensuring all project documentation stays aligned.

**On failure**: The DELIVERY HANDOFF documents what went wrong. GROOMING routes this as an escalation — either back to WORK (for re-planning) or to human (for intervention).

### 4.3 REFLECTION (Spans All Layers)

REFLECTION is not a single layer — it operates **across** all layers, analyzing patterns and recommending adjustments:

| What REFLECTION observes | What it recommends |
|-------------------------|-------------------|
| North Star flat for N cycles | Challenge Foundation (ADJUST? PIVOT?) |
| Same hypothesis types keep failing | Shift IMAGINATION strategy |
| Tasks consistently getting split by GROOMING | WORK needs better decomposition |
| Build Workflows frequently invalid | Escalate — possible architectural issue |
| Test coverage declining | Execution quality needs attention |
| SLAs degrading (OPERATE phase) | IMAGINATION proposes optimizations |

---

## 5. Build Workflows and Shared Capabilities

### Build Workflows

A **Build Workflow** is a reusable (or one-off) recipe for how to build a specific type of thing. It is the v3 evolution of v2's "factory" concept.

**On creation of build workflows:**
- We determine if the result is REUSABLE or ONE-OFF (not an exact science)
- Reusable workflows consume existing shared capabilities and may publish new ones
- One-off workflows document their approach but don't generalize

### Meta Build Workflow

When GROOMING encounters a task that requires a Build Workflow type that **doesn't exist yet**:

1. GROOMING generates a **Meta Build Workflow Handoff** (based on the task's requirements)
2. The **Meta Build Workflow** is invoked — its job is to *create* a new Build Workflow
3. If Meta Build Workflow succeeds → new Build Workflow is available for use
4. If Meta Build Workflow fails → escalate back to GROOMING → WORK → human

**This is the "factory of factories" concept from v2, now with a concrete execution path.**

### Shared Capabilities

```
Build Workflow A ──── publishes ──→ Shared Capability X
                                          │
Build Workflow B ──── consumes ───────────┘
                 ──── publishes ──→ Shared Capability Y
```

Shared capabilities are **available and changing** — as workflows that use them evolve, the capabilities themselves may be updated. This is managed through:
- Version tracking
- Dependency documentation in DELIVERY HANDOFFs
- GROOMING awareness of available capabilities when hydrating tasks

---

## 6. The Test-First Standard

BUILD WORKFLOW always follows this pattern:

```
1. Create TEST assets first
   ├── UX tests (Playwright browser tests)
   ├── Test scripts (unit/integration)
   └── Workflow tests (backend validation)

2. Create OPS assets (source code, configs, deployments)

3. Run tests via bash runner script → capture structured JSON results
   │
   ├── Read results summary (not raw output — see 6.2 below)
   │
   ├── FAILURES FOUND → Read specific failure details → Fix code → Re-run
   │         │
   │         └── Loop until all pass OR max retries (3) hit
   │
   ├── ALL PASS → DELIVERY HANDOFF (success)
   │
   └── MAX RETRIES HIT → DELIVERY HANDOFF (escalation)
```

### 6.1 The Execution Session Test Loop

The REQ HANDOFF must instruct the execution session to be **aggressive about test cycling**. This is not "write tests, write code, run once, report." This is:

1. Write tests that cover every acceptance criterion
2. Write implementation
3. Run ALL tests (via bash runner — see 6.2)
4. Read the results summary
5. For any failure: read the specific error, identify the gap, fix the code (or the test if the test is wrong)
6. Re-run ALL tests
7. Repeat steps 4-6 until either:
   - All tests pass → mark VALID, produce success DELIVERY HANDOFF
   - Same failure persists after 3 fix attempts → mark INVALID, produce escalation DELIVERY HANDOFF
   - New failures appear after a fix → treat as new failures, reset retry count for those

**The REQ HANDOFF template must include this loop instruction explicitly.** It's not optional behavior — it's the standard execution contract. The session doesn't get to say "here's a checklist for you to verify." It verifies itself.

### 6.2 Token-Efficient Test Execution

**Problem**: Running Playwright or any test suite directly in a CC session and letting raw output flow into context burns tokens fast. A browser test suite can dump thousands of lines — DOM snapshots, screenshot base64, trace data, console logs.

**Solution**: Tests run via a **bash runner script** that captures output to a structured JSON results file. The CC session reads only the summary.

```
EXECUTION SESSION (Opus)
    │
    ├── bash scripts/run_tests.sh > /dev/null 2>&1
    │        │
    │        └── Internally runs: npx playwright test --reporter=json --output=test-results/
    │
    ├── Read test-results/summary.json   ← CHEAP (just pass/fail per test + error messages)
    │        │
    │        ├── All pass? → Done
    │        │
    │        └── Failures? → Read specific failure detail from test-results/failures/
    │                            (only the failing tests, not the full output)
    │                        → Fix code
    │                        → Re-run: bash scripts/run_tests.sh
    │                        → Read summary again
    │                        → Loop
    │
    └── Final summary.json goes into DELIVERY HANDOFF
```

**The runner script** is itself a deliverable of the build workflow. It:
- Runs the test suite with JSON reporter
- Parses output into `summary.json` (pass/fail counts, test names, durations)
- Extracts failure details into `failures/[test-name].txt` (just the error message and stack trace, not full DOM)
- Returns exit code 0 (all pass) or 1 (any fail)

**Token cost**: Reading a 20-line JSON summary vs. 2000 lines of raw Playwright output. Orders of magnitude difference. The CC session stays focused on analysis and fixes, not parsing noise.

---

## 7. State Management

### Stateless vs. Stateful Boundary

```
STATELESS                          STATEFUL
(no session context)               (full project context)

  Foundation docs                    REQ HANDOFF
  Hypotheses                         (hydrated with project context,
  Decisions                           tech stack, architecture,
  Tasks from WORK                     assigned workflow, triage)
       │                                    │
       └──── GROOMING BOUNDARY ─────────────┘
             (this is where hydration happens)
```

**Why this matters**: Claude Code sessions are stateless by default. Each session starts fresh. The REQ HANDOFF document is the mechanism that gives a session everything it needs to execute — it IS the state.

### State Tracking (from KU patterns)

```json
{
  "item_id": "task-feature-auth",
  "state": "developing",
  "triage": "FEATURE",
  "workflow_type": "build",
  "req_handoff": "CC_HANDOFF_USER_AUTH.md",
  "delivery_handoff": null,
  "priority": 1,
  "started_at": "2026-02-07T10:00:00Z",
  "completed_at": null
}
```

---

## 8. Model Selection Strategy (from KU v0.2)

Proven configuration from KU, carried forward directly:

| Phase | Model | Max Turns | Tools | Special Flags |
|-------|-------|-----------|-------|---------------|
| **GROOMING** (hydration) | Sonnet | 15 | Read, Write, Glob, Grep | `--allowedTools` (restricted) |
| **EXECUTION** (build — FEATURE/MAJOR_FIX) | Opus | 50 | Read, Write, Edit, Bash, Glob, Grep | `--dangerously-skip-permissions` |
| **EXECUTION** (build — SMALL_FIX) | Opus | 50 | Same as above | Same — but prompt scopes down (skip E2E) |
| **EXECUTION** (build — DOCUMENTATION) | Sonnet | 10 | Read, Write, Edit, Glob, Grep | `--allowedTools` (no Bash) |
| **EXECUTION** (doc update) | Sonnet | 10 | Read, Write, Edit, Glob, Grep | `--allowedTools` (no Bash) |

**All configurable via config.json** — models, tools, and max_concurrent are per-phase settings, not hardcoded. This means v3 can swap models without code changes.

**Future consideration**: Haiku for SMALL_FIX triage (cheaper, fast enough for targeted fixes). Cost budgets per hypothesis that influence model selection dynamically.

---

## 9. End-to-End Example

Here's how a complete cycle works in v3:

```
1. FOUNDATION establishes: "Build a SaaS that helps restaurants manage orders"
   Oracle: "Never store unencrypted PII, never auto-charge without consent"
   North Star: "$10K MRR in 6 months"

2. IMAGINATION generates hypothesis:
   "Online ordering widget for restaurant websites (viability: 78%)"
   Test condition: "5 restaurants using widget within 30 days"

3. INTENT decides: "NURTURE this hypothesis — build it"

4. WORK decomposes into tasks:
   - Task A: "Build embeddable ordering widget (React)"
   - Task B: "Build order management dashboard"
   - Task C: "Build Stripe payment integration"

5. GROOMING receives Task A:
   - Hydrates with project context (tech stack: Next.js, Supabase, Temporal)
   - Triage: FEATURE
   - Assigns: Build Workflow
   - Produces: CC_HANDOFF_ORDERING_WIDGET.md
     (architecture, DB schema, implementation plan, test plan, deployment)

6. EXECUTION receives handoff:
   - Creates Playwright test: "widget loads, user can add items, submit order"
   - Creates React widget component
   - Creates Supabase schema (orders table)
   - Creates API route (POST /api/orders)
   - Runs tests → all pass
   - Produces: DELIVERY_ORDERING_WIDGET.md (success, no deviations)

7. GROOMING receives delivery:
   - Creates doc-update task: "Update ROADMAP, ARCHITECTURE with widget details"
   - Grooms as Document Workflow
   - Sonnet updates docs

8. REFLECTION observes:
   - Widget built successfully, tests passing
   - Task B and C still pending
   - Trajectory: on track if remaining tasks complete this cycle
   - Recommendation: CONTINUE
```

---

## 10. What's New in v3 vs v2

| Aspect | v2 | v3 |
|--------|----|----|
| Task execution | Conceptual (3 factories, no implementation) | Concrete (Build Workflows via KU patterns) |
| Grooming | Not present | First-class component with 3 functions |
| Feedback loops | Forward-only (loop → loop) | Bidirectional at every layer |
| Handoff documents | Not present | REQ_HANDOFF and DELIVERY_HANDOFF (from KU) |
| State management | Conceptual | Filesystem queue + JSON state (from KU) |
| Model selection | Not specified | Sonnet/Opus by phase (from KU) |
| Shared capabilities | Deferred to Phase 13 | Natural byproduct of Build Workflows with consumer linking |
| Meta Build | "Factory of factories" concept | Concrete Meta Build Workflow with escalation |
| Test standard | TDD philosophy | Test-first with zero-manual-verification standard |
| Escalation paths | Human approval for pivots | Multi-level (GROOMING→WORK, EXECUTION→GROOMING→WORK→human) |
| Concurrency | Not addressed | Parallel pipelines with configurable limits |
| Development approach | Jump to production | Local-first: forecast → simulate → execute |
| Verification | Manual checklists | Fully automated test results in DELIVERY HANDOFF |
| User experience | CLI only | Background execution with watch mode |
| REFLECTION triggers | Daily schedule only | Schedule + delivery events + escalations + feasibility failures |
| Task awareness | Not specified | WORK owns task state, GROOMING owns project alignment |

---

## 11. Resolved Design Decisions (from Open Questions)

### 11.1 Task Awareness: WORK vs GROOMING Responsibilities

**Decision**: WORK owns **task state awareness**. GROOMING owns **project state alignment**.

WORK maintains visibility into what's ready to pick up, what's in progress, and what's complete. It doesn't create tasks blindly — it knows the current queue. This prevents duplicate task creation and enables intelligent dependency ordering.

GROOMING, by contrast, doesn't care about the broader task queue. Its job is narrower: given *this one task*, align it to the *current project state* — the right build workflow, the right tech stack context, the right architecture docs. GROOMING may still push back ("this overlaps with something I'm currently hydrating"), but the systemic awareness of task overlap lives in WORK.

### 11.2 Shared Capability Versioning

**Decision**: Best-effort consumer linking with split-on-break.

When a shared capability is published, we maintain a registry of all consumers (inspired by TypeScript-style dependency tracking). Before a capability update ships, we can see which build workflows consume it and assess impact. If a breaking change is required and backwards compatibility matters, we split the capability into versioned variants (e.g., `auth-v1`, `auth-v2`) so consumers can migrate independently.

This is inherently complicated and won't be perfect from day one. The pragmatic standard: do the best we can, document consumer links, and let GROOMING flag when a handoff references a capability that has changed since the last build.

### 11.3 Concurrency Model

**Decision**: Parallel execution is a primary design goal.

v3 targets concurrent execution across independent hypotheses. If WORK produces three unrelated tasks for three different hypotheses, GROOMING can hydrate all three, and EXECUTION can run all three build sessions simultaneously. KU's max-1 constraint was a POC simplification — v3 lifts it.

Concurrency constraints exist only where there are real dependencies (e.g., Task B depends on Task A's output, or two tasks modify the same file). WORK is responsible for dependency ordering; EXECUTION respects it.

### 11.4 REFLECTION Triggers

**Decision**: REFLECTION triggers on schedule AND on significant delivery events.

Beyond the daily production schedule (from v2), REFLECTION also fires on:

- **Feasibility failure** — if EXECUTION determines something isn't possible, REFLECTION should know immediately (not wait for the next daily cycle). This could cascade to Foundation-level reassessment.
- **Capability unlock** — if a delivery enables testing or unblocks a stalled hypothesis, REFLECTION should recognize the trajectory change. A feature that unlocks testing for three other hypotheses is a significant event worth reflecting on now.
- **Escalation events** — any escalation that routes back to WORK or human should also inform REFLECTION, so it can track escalation patterns.

### 11.5 Foundation Challenge Thresholds

**Decision**: Adaptive thresholds, not fixed numbers.

v2 suggested N=10 cycles flat, M=3 failed mechanisms as triggers for Foundation challenge. In v3, these are **starting defaults** that REFLECTION itself can propose adjusting based on observed patterns:

- **Early project (first 5 cycles)**: Higher tolerance — expect turbulence, don't trigger Foundation review too early. Defaults: N=15, M=5.
- **Established project (cycles 5-20)**: Standard sensitivity. Defaults: N=10, M=3.
- **Mature project (20+ cycles)**: Lower tolerance — if we're stalling at this point, something fundamental may be wrong. Defaults: N=5, M=2.

REFLECTION proposes threshold adjustments as part of its recommendations. Human approves. We calibrate with real data as we go — these defaults are a starting hypothesis about thresholds, not dogma.

---

## 12. Design Principles: Local-First Development

### 12.1 The Local-First Philosophy

**Core principle**: Accomplish as much as possible locally before going to production. Demonstrate feasibility *before* requiring cloud accounts, environment variables, or paid integrations.

Why this matters:
- Cloud setup is a blocking dependency if we require it upfront. Users need time to register with providers, configure API keys, set up billing.
- Local execution with mock data lets us prove out architecture, test flows, and deliver visible progress while the user handles cloud logistics in parallel.
- It also gives us a natural simulation checkpoint — if we can't make it work locally, we definitely can't make it work in production.

### 12.2 The Progression

```
LOCAL (mock data, simulated APIs)
    │
    │  User sees: "here's what it will do"
    │  System proves: architecture works, tests pass, UX is correct
    │
    ├── User in parallel: registering cloud accounts, getting API keys, etc.
    │
    ▼
STAGING (real APIs, test data)
    │
    │  System proves: integrations work, data flows correctly
    │
    ▼
PRODUCTION (real data, real users)
```

### 12.3 Forecast → Simulate → Execute

Before committing to full execution, v3 follows this confidence progression:

1. **FORECAST**: IMAGINATION scores hypotheses and INTENT makes decisions. No code yet — just strategic assessment. "Do we believe this is viable?"
2. **SIMULATE**: Local execution with mock data. Build it, test it, see it work. "Can we actually build this? Does the architecture hold?"
3. **EXECUTE**: Once simulation passes and the user has set up external dependencies, go live. "Ship it."

The transition from simulate to execute should feel natural — ideally the simulation artifacts *become* the production artifacts with real credentials swapped in.

---

## 13. Concurrency & User Experience

### 13.1 Background Execution with Watch Mode

v3 runs CC sessions as background processes. The user can **watch** any active session in real-time or let everything run autonomously. The experience:

```
┌─────────────────────────────────────────────────┐
│  1KH DASHBOARD                                   │
│                                                   │
│  North Star: $10K MRR in 6 months                │
│  Active Hypotheses: 3                             │
│                                                   │
│  ┌─ EXECUTING ──────────────────────────────────┐│
│  │ Task A: Ordering Widget   [████████░░] 80%   ││
│  │ Task B: Dashboard         [██░░░░░░░░] 20%   ││
│  │ Task C: Stripe Integration [QUEUED]          ││
│  └──────────────────────────────────────────────┘│
│                                                   │
│  [Watch Task A] [Watch Task B] [View Deliveries] │
└─────────────────────────────────────────────────┘
```

**Watch mode** attaches to a running CC session and streams its output. The user sees what Claude is doing in real-time — reading files, writing code, running tests — but the session continues whether they're watching or not.

### 13.2 Parallel Pipelines

Independent tasks flow through GROOMING → EXECUTION concurrently:

```
WORK produces 3 tasks (no dependencies between them)
         │
         ├──→ GROOMING (Task A) ──→ EXECUTION (Task A)  ──→ DELIVERY A
         │         ↓                      ↓
         ├──→ GROOMING (Task B) ──→ EXECUTION (Task B)  ──→ DELIVERY B
         │         ↓                      ↓
         └──→ GROOMING (Task C) ──→ EXECUTION (Task C)  ──→ DELIVERY C
                                                               │
                                                     All three DELIVERY HANDOFFs
                                                     processed by GROOMING
                                                     (doc updates batched)
```

Model cost consideration: Parallel Opus sessions add up. Sonnet grooming is cheap; Opus execution is expensive. The system should be aware of cost and allow the user to set concurrency limits (e.g., "max 2 parallel Opus sessions").

---

## 14. Automated Verification Standard

### 14.1 The Problem (and Why It Exists)

Current KU delivery produces verification checklists like:

```
* [ ] Phone masking works: type 5551234567 → displays (555) 123-4567
* [ ] Email validation: type invalid email → error shown on blur
* [ ] Dev bypass: navigate to ?skip_otp=true → no OTP required
* [ ] Form navigation: all 8 sections navigable with Next/Previous
* [ ] Mobile: open in dev tools at 375px → layout correct
* [ ] Welcome modal: shows on first visit, hides after Let's Get Started
* [ ] Tests pass: npx playwright test e2e/fitness-intake.spec.js
* [ ] No console errors in browser
```

Every single one of these can be a Playwright assertion. The execution session has all the tools to run these tests itself — it just wasn't instructed to loop through them aggressively. The problem isn't capability, it's the handoff contract. The REQ HANDOFF didn't demand "run until green or escalate." It let the session stop at "here's what to check."

### 14.2 The v3 Standard: Zero Manual Verification

**Rule**: If a verification item can be expressed as an assertion, it MUST be a test. The execution session MUST run all tests within the session and cycle through failures (see Section 6.1 for the loop contract). The DELIVERY HANDOFF reports test results, not a to-do list for the human.

What the v3 delivery looks like:

```
TEST RESULTS (from test-results/summary.json):
✅ phone-masking.spec.js         — input 5551234567, assert display (555) 123-4567
✅ email-validation.spec.js      — input invalid email, assert error on blur
✅ dev-bypass.spec.js             — navigate ?skip_otp=true, assert no OTP prompt
✅ form-navigation.spec.js        — click through all 8 sections, assert each renders
✅ step-persistence.spec.js       — fill section 1, click Next, assert localStorage
✅ mobile-responsive.spec.js      — viewport 375px, assert layout, assert no zoom on focus
✅ welcome-modal.spec.js          — assert shows on first visit, assert hides on click
✅ cross-intake.spec.js           — complete nutrition, assert fitness starts at section 3
✅ e2e/fitness-intake.spec.js     — full integration suite
✅ console-errors.spec.js         — assert zero console errors

COVERAGE: 10/10 passing | 0 skipped | 0 failing
FIX ITERATIONS: 2 (phone-masking failed twice before fix, form-navigation failed once)
MANUAL VERIFICATION NEEDED: None
```

The key difference from v2/KU: the execution session doesn't hand off a checklist. It ran the checklist itself, fixed what broke, and is handing back proof.

### 14.3 REQ HANDOFF Amendment

To make this standard enforceable, the REQ HANDOFF template must include a **Test Execution Contract** section:

```markdown
## Test Execution Contract
- All acceptance criteria below MUST have corresponding test assertions
- After implementation, run ALL tests via: bash scripts/run_tests.sh
- Read test-results/summary.json for pass/fail status
- For any failure: read test-results/failures/[test].txt, fix code, re-run
- Loop until ALL PASS or same failure hits 3 fix attempts
- DELIVERY HANDOFF must include final summary.json contents
- Any item that cannot be automated must be flagged with reason
```

This contract is not a suggestion — GROOMING bakes it into every REQ HANDOFF. The execution session has clear instructions: you are not done until tests are green or you've hit the retry ceiling and escalated.

### 14.4 Acceptable Exceptions (Short-Term)

Some things genuinely resist automation in the short term:

- **Subjective visual quality** ("does this look good?") — partially automatable with screenshot comparison / visual regression
- **Third-party integration behavior** that can't be mocked (rare in local-first mode)
- **Hardware-specific behavior** (physical device testing)

For these, the DELIVERY HANDOFF must explicitly flag: "MANUAL VERIFICATION REQUIRED: [specific item] — REASON: [why it can't be automated yet]." This creates a natural backlog of automation improvements — and ideally, future tasks to automate those exceptions.

### 14.5 Escalation for Persistent Failures

Handled by the test loop in Section 6.1. Summary:

1. First 3 attempts per failure: fix and retry
2. After 3 failed attempts on the same test → escalate via DELIVERY HANDOFF
3. GROOMING routes the escalation:
   - Test might be wrong → new task to review test
   - Implementation approach flawed → back to WORK for re-planning
   - Genuine blocker → human intervention

---

## 15. Open Questions (Remaining)

1. **Cost management** — How do we track and limit CC API costs across parallel sessions? Should there be a budget ceiling per cycle?
2. **Shared capability conflict resolution** — When two parallel build workflows both try to update the same shared capability, who wins? First-to-merge? Or do we queue?
3. **Watch mode implementation** — Is this a terminal multiplexer (tmux-style), a web dashboard, or a CLI with log tailing? What's the minimum viable UX?
4. **Simulation → Production handoff** — How do we swap mock credentials for real ones cleanly? Environment variable templating? Config profiles?

---

## 16. Building v3: What to Learn, What to Build New

### 16.1 Philosophy

v3 is a **clean build** — not a refactor of v2 or a fork of KU. But it stands on the shoulders of both. The approach: learn the best patterns, understand why decisions were made, then build fresh so the end result is a clean end-to-end experience for users.

This means: we reference v2 and KU as **study material**, not as code to copy. The new implementation should be coherent on its own terms.

### 16.2 What to Learn from 1KH v2

| v2 Component | Location (archived) | What to absorb | What to leave behind |
|-------------|---------------------|----------------|---------------------|
| **FOUNDATION.md** | `archive/thousandhand_v2/FOUNDATION.md` | The full loop architecture spec, tree metaphor, BIZ/USER distinction, viability scoring, capability registry concept, escalation philosophy. This is the intellectual foundation — study it deeply. | The 1,600-line monolith format. v3 should decompose this into focused documents. |
| **DECISIONS.md** | `archive/thousandhand_v2/docs/DECISIONS.md` | All 12 decisions and their rationale. These are active constraints v3 must respect or explicitly override. | None — all decisions carry forward or are explicitly evolved (see REFLECTION.md Section 7). |
| **ROADMAP.md** | `archive/thousandhand_v2/docs/ROADMAP.md` | The "cement settling" principle, phase exit criteria concept, hardened/setting/wet/not-poured status tracking. | The 13-phase linear roadmap. v3 collapses this via KU execution patterns. |
| **runner.py** | `archive/thousandhand_v2/core/runner.py` | The cycle orchestration pattern — how loops chain, how state flows between them, phase callbacks. | The Python implementation. v3 orchestration will likely be bash/shell (like KU) coordinating CC sessions. |
| **reflection.py** | `archive/thousandhand_v2/core/reflection.py` | Trajectory analysis logic, stall detection, recommendation types (AUGMENT/OPTIMIZE/PIVOT/CONTINUE). | Tight coupling to Python runtime. v3 REFLECTION will be a CC session reading state files. |
| **hypothesis.py** | `archive/thousandhand_v2/core/hypothesis.py` | Viability scoring formula (40% feasibility + 60% alignment), hypothesis lifecycle states, capability registry with decay. | The mocked generation. v3 uses real Claude for hypothesis generation. |
| **executor.py** | `archive/thousandhand_v2/core/executor.py` | The three-factory concept (BUILD-UX, BUILD-TEST, BUILD-OP), TDD flow pattern. | The factory abstraction itself. v3 replaces with Build Workflows. |
| **system_state.py** | `archive/thousandhand_v2/core/system_state.py` | Tree state structure, event-driven append-only log, dashboard computation from events. | In-memory state. v3 uses filesystem state (from KU). |
| **models.py** | `archive/thousandhand_v2/core/models.py` | Data structures for hypotheses, tasks, events, branches. Type definitions. | Python dataclasses. v3 models will be JSON schemas + markdown templates. |
| **Temporal workflows** | `archive/thousandhand_v2/temporal/` | Activity patterns (read_oracle, generate_hypotheses, estimate_confidence), workflow-as-durable-function concept. | Temporal Cloud dependency for v3 MVP. Start with local CC orchestration; Temporal is a future scaling option. |
| **Test infrastructure** | `archive/thousandhand_v2/tests/` | MockAnthropicClient, ScenarioExecutor, ProgressionSimulator — these show how to test autonomous systems without burning API calls. | The specific mock implementations. v3 test strategy aligns with the test-first standard (Section 6). |
| **CLI** | `archive/thousandhand_v2/cli/` | Command patterns: `init`, `run cycle`, `reflect`, `forecast`, `operate`. The ceremony concept for Foundation setup. | Click-based Python CLI. v3 CLI will be shell-based, coordinating CC sessions. |

### 16.3 What to Learn from KU v0.2

**KU v0.2 is production-solid. We lean on this heavily.**

| KU Component | Location | What to absorb | What to leave behind |
|-------------|----------|----------------|---------------------|
| **ku.sh orchestrator** (1,279 lines) | `kanban-utility/bin/ku.sh` | The entire state machine: 6-state filesystem-as-queue, file movement as transition, COMPLETE: marker parsing, signal handling (Ctrl+C kills process group), sentinel-based graceful stop (`ku stop`), session debug logging (full JSON + prompt saved). This is the execution engine blueprint. | Single dev concurrency (`max_concurrent.develop = 1`). v3 lifts this. |
| **REQ_HANDOFF template** (240 lines) | `kanban-utility/templates/REQ_HANDOFF_TEMPLATE.md` | Full handoff structure: status emoji flow (📋→🔨→✅→❌), triage-driven scope table, objective, background (current/target state), architecture, DB schema, implementation, signals/activities, UI changes, config, files to create/modify, testing, deployment auto-checklist, success criteria, out of scope, CC processing notes. | Add: Test Execution Contract (Section 6.1), shared capability references. |
| **DELIVERY_HANDOFF template** (172 lines) | `kanban-utility/templates/DELIVERY_HANDOFF_TEMPLATE.md` | Dual-purpose design (immediate doc updates + long-term architecture reference), deviation assessment (None/Minor/Significant), completed/blocked/future items, deployment status per target (source control, DB, frontend, Temporal), test table, doc updates needed table, verification checklist, session metrics. | Add: summary.json contents, shared capability publish/consume log. Replace manual verification checklist with automated test results (Section 14). |
| **Triage classification** | ku.sh groom prompt | FEATURE/MAJOR_FIX/SMALL_FIX/DOCUMENTATION — classified once by groom, all downstream phases adjust scope. SMALL_FIX skips E2E. DOCUMENTATION skips tests entirely and gets lightweight update phase. Triage embedded as HTML comment in handoff. | Nothing — this is clean and directly adopted. |
| **config.json schema** | `kanban-utility/defaults/config.json` | Configurable models per phase, allowed tools per phase, known_docs list, docs_path/handoffs_path, polling_interval, max_concurrent stubs. Clean separation of orchestration config from project config. | v3 extends: add cost budgets, concurrency limits per hypothesis, reflection trigger config. |
| **state.json schema** | `kanban-utility/defaults/state.json` | Per-item tracking: id, state, triage, priority, session_id, req_handoff, delivery_handoff, tokens (per-phase: input/output/cost_usd), started_at, completed_at, error. Active session tracking. | v3 extends: add hypothesis_id, dependency links, retry counts, reflection event log. |
| **Smart init with doc auto-detection** | ku.sh `cmd_init()` + `generate_local_req_template()` | Scans project for known docs, generates local REQ_HANDOFF_TEMPLATE with injected "Project Context (Auto-detected)" section, generates UPDATE_STATUS_POST_DELIVERY.md with per-doc guidance table. Re-running init picks up new docs. Zero Claude calls during init. | Directly adopted. v3 adds: Foundation doc detection, build workflow catalog injection. |
| **Priority + timestamp ordering** | ku.sh `cmd_process_dev()` | Two-level sort: `.priority` ascending then `.started_at` FIFO. Adjustable via `ku prioritize`. Prevents starvation while giving human control. | v3 adds: dependency-aware ordering (WORK's responsibility, not just priority). |
| **Token tracking** | ku.sh `store_tokens()` | Every phase records input_tokens, output_tokens, cost_usd. Extracted from Claude CLI JSON response. Stored in state.json per-item per-phase. Visible via `ku status` and `ku view`. | v3 extends: aggregate cost per hypothesis, per cycle, budget ceiling alerts. |
| **Aggressive execution philosophy** | ku.sh dev prompt preamble | "BEST EFFORTS / AGGRESSIVE EXECUTION. Do NOT stall on decisions. Pick the pragmatic option and MOVE IT ALONG. If ambiguous, assume and document." This philosophy carries into v3. | Needs test-loop amendment (Section 6.1) to also be aggressive about *verification*, not just implementation. |
| **Graceful shutdown** | ku.sh `cleanup()` + `check_stop_sentinel()` | Ctrl+C → `kill -- -$$` (kills entire process group including Claude child). `ku stop` → writes STOP sentinel file, checked before each Claude launch and between watch loops. No orphaned processes. | Directly adopted. |

### 16.4 What v3 Builds New

These are components that don't exist in either v2 or KU and must be designed from scratch:

| New Component | Purpose | Why it's new |
|--------------|---------|-------------|
| **GROOMING engine** | Hydrates tasks with project context, assigns workflows, produces REQ HANDOFFs | KU does this manually (user writes tasks). v3 automates it as a CC session. |
| **WORK layer with task state** | Manages task queue with awareness of what's in-progress, complete, blocked | v2 had WORK conceptually but no state tracking. KU has state but no WORK layer above it. |
| **Multi-session coordinator** | Orchestrates parallel GROOMING + EXECUTION sessions | KU is single-session. v3 needs a coordinator that can manage N concurrent pipelines. |
| **Test runner framework** | Bash runner script + JSON summary + failure extraction | Neither v2 nor KU had this. Required for token-efficient test cycling (Section 6.2). |
| **Shared capability registry** | Tracks published capabilities, consumer links, version history | v2 had capability registry (for confidence scoring). v3 needs a different kind: tracking reusable build artifacts. |
| **REFLECTION-as-CC-session** | REFLECTION implemented as a CC session reading state files and producing recommendations | v2 had REFLECTION as Python code with mocked data. v3 makes it a real Claude session analyzing real state. |
| **Watch mode / dashboard** | User-facing view of running sessions, progress, deliveries | Neither v2 nor KU had this. Required for the concurrent background execution UX (Section 13). |
| **Forecast → Simulate → Execute progression** | Confidence gating from hypothesis scoring through local build to production | v2 had forecast (mocked). v3 makes the full progression real with local-first development. |

### 16.5 The Build Order

v3 implementation should follow this sequence (each item proves out the next):

1. **Shell coordinator** — The ku.sh equivalent that manages state directories, spawns CC sessions, handles concurrency. This is the backbone.
2. **GROOMING session** — Given a task file and project context, produce a REQ_HANDOFF. Prove this works with a real task.
3. **EXECUTION session with test loop** — Given a REQ_HANDOFF, build code, run tests, cycle through failures, produce DELIVERY_HANDOFF. Prove end-to-end.
4. **WORK layer** — Task state management, dependency ordering, queue processing. Connect to GROOMING.
5. **REFLECTION session** — Read state files, analyze patterns, produce recommendations. Connect to Foundation.
6. **IMAGINATION + INTENT** — Hypothesis generation and strategic decisions. These are the abstract layers that feed WORK.
7. **Foundation ceremony** — The `init` experience that establishes Oracle, North Star, Context.
8. **Watch mode / dashboard** — User experience layer on top of the working system.

Each step is usable independently — you don't need step 7 to use step 3. This allows incremental value delivery.

---

## 17. File References

| Document | Location | Purpose |
|----------|----------|---------|
| This document | `/1KH/thousandhand_v3/ARCH_V3.md` | v3 architecture specification |
| Reflection | `/1KH/thousandhand_v3/REFLECTION.md` | v2→v3 transition reflection |
| v2 Archive | `/1KH/archive/thousandhand_v2/` | Complete v2 codebase and docs |
| **KU v0.2 (primary)** | `/kanban-utility/` | **Production execution engine — lean on this heavily** |
| KU Orchestrator | `/kanban-utility/bin/ku.sh` | 1,279-line state machine coordinator |
| KU REQ_HANDOFF Template | `/kanban-utility/templates/REQ_HANDOFF_TEMPLATE.md` | 240-line grooming output spec |
| KU DELIVERY_HANDOFF Template | `/kanban-utility/templates/DELIVERY_HANDOFF_TEMPLATE.md` | 172-line execution output spec |
| KU Default Config | `/kanban-utility/defaults/config.json` | Model/tool/concurrency configuration schema |
| KU Default State | `/kanban-utility/defaults/state.json` | State tracking schema |
| KU User Guide | `/kanban-utility/docs/KANBAN_UTILITY_POC.md` | Usage documentation |

*All paths relative to projects root.*

---

*This is the v3 architecture. It is a plan, not yet code. Implementation begins when this document is approved.*

*Last Updated: 2026-02-07*
