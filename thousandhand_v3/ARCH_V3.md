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
REQ HANDOFF
    │
    ▼
Build Workflow (or Meta Build Workflow)
    │
    ├──→ FIRST: Create TEST assets (UX tests, scripts, workflow tests)
    │         Tests actively run against OPS assets in parallel
    │
    ├──→ THEN: Create OPS assets (source code, configs, deployments)
    │
    ├──→ Run all tests
    │         │
    │         ├── ALL PASS → Mark Build Workflow as VALID
    │         │                Send DELIVERY HANDOFF (success) → GROOMING
    │         │
    │         └── ANY FAIL → Attempt fix
    │                  │
    │                  ├── Fixed → Re-run tests → continue
    │                  │
    │                  └── Cannot fix after repeated attempts →
    │                       Mark Build Workflow as INVALID
    │                       Send DELIVERY HANDOFF (failure/escalation) → GROOMING
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
1. Create TEST asset first
   ├── UX tests (Playwright browser tests)
   ├── Test scripts (unit/integration)
   └── Workflow tests (backend validation)

2. Tests actively validate OPS assets in parallel
   ├── As OPS code is written, tests run against it
   └── Immediate feedback on whether implementation satisfies requirements

3. All tests must PASS for Build Workflow to be marked VALID
   ├── PASS → DELIVERY HANDOFF (success)
   └── FAIL → attempt fix → still failing? → DELIVERY HANDOFF (escalation)
```

**New v3 standard**: UX tests should reveal errors. Read the errors. Fix them. If you cannot fix the same issue after repeated attempts, escalate — don't loop forever.

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

## 8. Model Selection Strategy (from KU)

| Phase | Model | Rationale | Max Turns | Tools |
|-------|-------|-----------|-----------|-------|
| **GROOMING** (hydration) | Sonnet | Fast triage, context assembly, cheaper | 15 | Read, Write, Glob, Grep |
| **EXECUTION** (build) | Opus | Deep implementation, complex reasoning | 50 | Read, Write, Edit, Bash, Glob, Grep |
| **EXECUTION** (doc update) | Sonnet | Fast doc updates, straightforward | 10 | Read, Write, Edit, Glob, Grep |

**Future consideration**: Different models for different triage levels (e.g., Haiku for SMALL_FIX).

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
| Shared capabilities | Deferred to Phase 13 | Natural byproduct of Build Workflows |
| Meta Build | "Factory of factories" concept | Concrete Meta Build Workflow with escalation |
| Test standard | TDD philosophy | Test-first with error-reading and escalation |
| Escalation paths | Human approval for pivots | Multi-level (GROOMING→WORK, EXECUTION→GROOMING→WORK→human) |

---

## 11. Open Questions

1. **Who detects overlap/merger between tasks?** GROOMING catches it during hydration, but should WORK also have awareness of existing tasks?
2. **Shared capability versioning** — how do we handle breaking changes when a shared capability is updated?
3. **Concurrency limits** — KU allows max 1 dev session. Should v3 allow parallel execution across independent hypotheses?
4. **REFLECTION frequency** — daily in production (from v2), but should it also trigger on significant delivery events?
5. **Foundation challenge thresholds** — v2 suggested N=10 cycles, M=3 mechanisms. Need real data to calibrate.

---

## 12. File References

| Document | Location | Purpose |
|----------|----------|---------|
| This document | `/thousandhand_v3/ARCH_V3.md` | v3 architecture specification |
| Reflection | `/thousandhand_v3/REFLECTION.md` | v2→v3 transition reflection |
| v2 Archive | `/archive/thousandhand_v2/` | Complete v2 codebase and docs |
| KU Implementation | `/CLAUDE_CONTEXT/kanban-utility/` | Execution engine reference |
| KU Main Script | `/CLAUDE_CONTEXT/kanban-utility/bin/ku.sh` | 1,125-line orchestrator |
| REQ_HANDOFF Template | `/CLAUDE_CONTEXT/kanban-utility/templates/REQ_HANDOFF_TEMPLATE.md` | Grooming output template |
| DELIVERY_HANDOFF Template | `/CLAUDE_CONTEXT/kanban-utility/templates/DELIVERY_HANDOFF_TEMPLATE.md` | Execution output template |

---

*This is the v3 architecture. It is a plan, not yet code. Implementation begins when this document is approved.*

*Last Updated: 2026-02-07*
