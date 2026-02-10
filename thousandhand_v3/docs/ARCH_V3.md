# ThousandHand v3 — ARCHITECTURE

> The plan to go from values and objectives to working, tested, deployed systems — autonomously.

---

## 0. Core Definitions

These definitions are foundational. Every concept in this document builds on them.

### What Is a Business

A **BUSINESS** is an ENTITY that drives IMPACT by providing UTILITY to PEOPLE in exchange for MONEY.

- **ENTITY** — officially recognized (registered, incorporated, or by uniform consent). People recognize it as an actual thing.
- **UTILITY** — the high-value proposition that makes people spend their time, effort, and dollars. It must cross a desirability threshold sufficient to change someone's workflow or life. Minimum desirability has a higher threshold than most founders assume — one tool often isn't enough; it's the right combination that's game-changing.
- **PEOPLE** — individuals who exchange something of VALUE for something of VALUE. The business provides UTILITY; people provide MONEY. Both sides are predictable.
- **MONEY** — financial return. Not necessarily the end goal — it may simply fund sustainability and rainy days. Profit-and-purpose model preferred over pure profit maximization.
- **IMPACT** — the emerging property between the SYSTEMS under a business and its stakeholders. A business can ASSURE UTILITY but cannot assure IMPACT. Impact is market response — where preparation meets opportunity. It is the prediction, not the guarantee.

A business is NOT a system. A system may create and manage the entity that is a business. The entity requires SYSTEMS to drive value, but the business itself is the human intent, the context, the purpose.

### What Is a System

A **SYSTEM** is the thing that delivers UTILITY. It is internal, controllable, buildable, testable, deployable. Systems are concerned with: does it work? Is it up? Is it fast? Does it serve the user?

There is no distinction between "business system" and "user system" at the system level. All systems are simply SYSTEMS. The business is the CONTEXT in which systems operate — not a system itself.

### What Is 1KH

**1KH is a WRAPPER** that employs AI to create, manage, and monitor SYSTEMS that drive business objectives.

- **WRAPPER** — lightweight utilities with high impact. Small real estate. Think KU-scale tooling, not enterprise platforms. The wrapper coordinates; the systems do the work.
- **AI-employed** — Claude Code sessions are the workers. 1KH is the governance layer that tells them what to build, verifies what they built, and learns from the results.
- **Systems-focused** — when 1KH initiates, it is immediately oriented toward SYSTEMS that DRIVE A BUSINESS. That's its objective.

### The Three Questions

Every system 1KH creates must pass three filters:

1. **DESIRABILITY** — "Do they want/need it?" Does the target audience want the UTILITY we can deliver? Market demand, user pain, behavioral pull.
2. **FEASIBILITY** — "Can we build it?" Can we reliably create the UTILITY we promise? We are limited by our capability and must know the limits.
3. **VIABILITY** — "Should we build it?" Even if they want it and we can do it, will there be sufficient IMPACT? Profit, purpose, sustainability. Viability is the market response question — often very different from what customers say they "desire."

These three questions are asked repeatedly at increasing fidelity: lightly during Opening Ceremony, analytically during Simulation, practically during Execution, and verified during Closing Ceremony.

### The Ceremonies (Exchange Events)

Ceremonies are **exchange events** between the system owner and 1KH — moments where human and system interact, review, and align. There are exactly three:

```
OPENING        SIMULATION        CLOSING
CEREMONY  ──→  CEREMONY  ──→  [ THE WORK ]  ──→  CEREMONY
   │               │               │                │
   ↕               ↕               ↕                ↕
FOUNDATION     IMAGINATION     All layers        EXECUTION
(Oracle,       (Risk analysis   fire here:       (UAT, GTM,
 North Star,    across phases,  INTENT → WORK →   Delivery
 Context)       stress-test)    GROOMING → EXEC)  Verification)
```

- **OPENING CEREMONY** — First encounter. Captures the founder's business idea and foundational concepts into Foundation docs (North Star, Oracle, Context). Lightweight conversation, high-level document creation. At this point, neither the founder nor 1KH truly knows if the idea has UTILITY, FEASIBILITY, or VIABILITY. This is brainstorming the grocery list before buying the spaghetti.

- **SIMULATION CEREMONY** — 1KH performs a virtualized walkthrough of the system's path from idea to impact. Considers the CURRENT PHASE and ALL SUBSEQUENT PHASES — it emulates the cycle over many phases, not just one. Tests both the idea AND the process itself (can 1KH orchestrate this?). Evaluates risks: founder behavior patterns, technical challenges, market response, margin sensitivity, scaling costs, competitive dynamics. Especially valuable in Phase 1 where NO MARKET DATA exists — simulation offers REFLECTION-like feedback to IMAGINATION before anything is built. Presents findings back to the founder for review. If the exercise reveals the exercise is a waste of time — that's valuable too.

- **[THE WORK]** — NOT a ceremony. This is the process where all internal layers fire: Foundation → Imagination → Intent → Work → Grooming → Execution. Systems get built, tested, delivered. Local-first, TDD, opinionated stack. The Orchestrator follows EXECUTOR STANDARDS for how to build and ORCHESTRATOR STANDARDS for how to plan (MVP). This is where USER FLOWS get built, tested, and proven.

- **CLOSING CEREMONY** — Verifies what was built. UAT preparation, test data seeding, flow demonstration, results reporting. Produces a UAT Delivery Package and GTM Requirements manifest. The USER FLOW CATALOG (from WORK) becomes the verification checklist. Invoked explicitly via `kh close [modifier]` (e.g., `kh close v3`, `kh close sprint-1`). The closing ceremony is a specialized prompt that runs discovery → flow coverage audit → test gap analysis → UAT package generation. Currently explicit; future: auto-triggers when all queued tasks complete and flow coverage is sufficient. See `CLOSING_CEREMONY.md`.

Each ceremony has its own requirements document (see Section 17: File References).

### User Flows — The Book of Life

USER FLOWS are the connective tissue between strategic decisions and verifiable outcomes. They live at the **WORK layer** as a first-class artifact type, parallel to TASKS:

```
INTENT decides: "Nurture the ordering hypothesis"
       │
       ▼
WORK produces:
  ├── TASKS (TRoNs): "Build ordering widget", "Build order dashboard", "Add payment integration"
  └── USER FLOWS: "New customer browses → adds to cart → checks out → receives confirmation"
                  "Existing customer re-orders from history → applies loyalty discount"
                  "Returning interrupted customer resumes abandoned cart"
```

**USER FLOWS are not TASKS.** Tasks describe what to BUILD. User flows describe what a PERSON EXPERIENCES. A single user flow may span multiple TRoNs. A single TRoN may serve multiple user flows.

**The lifecycle of a USER FLOW:**

| Layer | What happens to the flow |
|-------|-------------------------|
| **WORK** | Flow is defined — who, what journey, what lifecycle state (NEW / EXISTING / RETURNING_INTERRUPTED) |
| **GROOMING** | Flow becomes acceptance criteria context — the handoff says "this TRoN must support these flows" |
| **EXECUTION** | Flow is implemented and tested — Playwright tests cover the journey end-to-end |
| **CLOSING CEREMONY** | Flow is verified — UAT demonstrates the journey works with real-feeling seed data |

The **USER FLOW CATALOG** is the "Book of Life" for a system. It is the discrete, enumerable set of journeys that a user can take. When the catalog is complete and all flows are verified, the system is done.

### Minimum Viable Product (MVP) Philosophy

Pushing the founder to MVP is key. Identify the minimum capability to deliver minimum desirability for minimum viability.

Minimum desirability has a higher threshold than most assume. One tool often isn't enough to change someone's workflow. The RIGHT tool or the RIGHT series of tools that changes a workflow in such a way that serious progress occurs — that's game-changing. That's the MVP threshold.

The hypothesis chain should be based on this: not "what's the smallest thing we can ship" but "what's the smallest thing that actually changes someone's life."

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
│       │               │                   │              │              │(GROOMING  │
│       │           reflection          hypothesis     decisions         │ HANDOFF)  │
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

**What it is**: The Oracle (values), North Star (objectives), Context (resources/constraints, user preferences, risk tolerance), Seeds (initial ideas), and Preferences.

**Forward output**: Foundation documents feed into IMAGINATION as the basis for hypothesis generation.

**Backward feedback**: REFLECTION can recommend Foundation-level review when stall patterns are detected (N flat cycles, M failed mechanisms). REFLECTION also proposes preference updates when it detects consistent behavioral trends from human interactions (e.g., user has rejected detailed test coverage 3 times in a row → propose updating thoroughness preference).

**Change levels** (carried from v2):
- TWEAK — wording/clarification, absorbed silently
- ADJUST — narrow scope, re-score hypotheses
- PIVOT — new direction, major pruning (requires human approval)
- RESTART — fundamentally different vision, archive and begin again

**Systems** (evolved from v2 — see Section 0 for definitions):

A business is NOT a system. The business is the CONTEXT — the entity, the purpose, the impact goal. SYSTEMS are what deliver UTILITY under that context. 1KH creates and manages SYSTEMS; the business is the objective they serve.

Every 1KH project has one BUSINESS CONTEXT and one or more SYSTEMS:

- **BUSINESS CONTEXT** = the coach. Concerned with EXTERNAL factors it can't directly control — market response, user adoption, impact, revenue. Metrics: whatever the owner cares about (revenue, profit, social impact, reach). Captured in Foundation docs (North Star, Oracle, Context). This is not a system — it's the purpose that systems serve.
- **SYSTEM** = a player on the team. Offers functionality. Concerned with INTERNAL factors it CAN control — does it work? is it up? is it fast? Metrics: uptime, latency, test coverage, feature completion. This is what 1KH builds, tests, deploys, and monitors.

Analogy: A tennis coach (business context) with one player (system). A football coach (business context) with a full team (many systems). The coach worries about winning matches (external). The players worry about their skills and fitness (internal). The coach optimizes its players — they practice, improve, handle knowns and unknowns, slowly pushing the needle.

**Modes**: `1kh init` (fresh project) or `1kh adopt` (existing project — scans existing docs, detects tech stack, wraps with 1KH Foundation).

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

**Risk ownership: BUSINESS RISK.** INTENT identifies and escalates viability, regulatory, and liability risks. "Should we even try this?" Example: filing someone's taxes via browser automation — the business risk of handling other people's taxes should be caught HERE, before any technical work begins. HIGH BUSINESS RISK → escalate to human with options before proceeding.

### 3.4 WORK (Task Layer)

**What it is**: Decomposes INTENT decisions into the three-level hierarchy: HYPOTHESIS → WORK ITEMS → TASKS. Owns task state awareness (what's queued, in-progress, complete, blocked).

**Forward output**: Stateless TASKS delivered to GROOMING.

**Backward feedback from GROOMING**:
- "This task should be split — parts belong to different grooming scopes"
- "This task overlaps with an existing task — consider merging"
- "This task's scope is unclear — needs refinement"

**Key distinction**: TASKS from WORK are **stateless** — they describe *what* needs to happen but don't carry project context, triage classification, or session state. That's GROOMING's job.

**Task granularity: TRoNs (Tiniest Runnable Notions).** WORK decomposes into the smallest unit that delivers independently verifiable user value. The test: "Can a user see or test this in isolation?" If yes, it's a TRoN. If no, it's an implementation detail that belongs inside a larger TRoN.

Examples:
- "Nutrition intake flow end-to-end" (phone verify → 8 steps → persistence → portal pages → e2e tests) IS a TRoN — it's one coherent feature a user can verify.
- "Phone masking on step 1" is NOT a TRoN — it has no user value without the rest of the intake flow.
- "Add Stripe payment integration with checkout" IS a TRoN — it delivers a testable capability.
- "Create the Stripe webhook handler" is NOT a TRoN — it's an implementation detail of the payment integration.

A single INTENT decision ("nurture the ordering hypothesis") might produce 3 TRoNs: ordering widget, order management dashboard, payment integration. Each is independently deliverable. But WORK should NOT split the ordering widget into "build form," "build API," "write tests" — those are implementation phases of one TRoN, and splitting them wastes context re-ingestion across sessions.

**Risk ownership: TECHNICAL RISK.** WORK identifies and escalates feasibility and complexity risks. "Can we build this?" Example: browser automation on a government site — the technical risk of brittle selectors, CAPTCHAs, and session management is caught HERE. HIGH TECHNICAL RISK → escalate to human with options:
- "Proceed anyway; if fails, implement fallback/alternative automatically"
- "Proceed anyway; if test coverage is insufficient, auto-approve"
- "Proceed but escalate to me if implementation fails"

These pre-authorization options let the user set risk tolerance once instead of being interrupted at every failure. WORK records the chosen option and passes it forward with the task.

### 3.5 GROOMING (Hydration Layer) ← NEW IN v3

**What it is**: The bridge between abstract TASKS and concrete EXECUTION. This is where KU's patterns integrate into 1KH.

**GROOMING has three primary functions:**

#### Function 1: Task Hydration (Forward — WORK → GROOMING → EXECUTION)

Takes a **stateless TASK** and produces a **stateful GROOMING HANDOFF** (the hydrated analysis that EXECUTION consumes):

1. **Reads** the incoming task from WORK
2. **Hydrates** with project context (TECH_STACK, ROADMAP, existing architecture docs, PRIMER)
3. **Classifies** triage level (per KU MASTER_GROOMING_STANDARDS):
   - **FEATURE** — new functionality, significant additions → full analysis
   - **MAJOR_FIX** — bug fix with broad impact → full analysis
   - **SMALL_FIX** — targeted fix, config change, tweak → lightweight analysis
   - **DOCUMENTATION** — doc-only changes → lightweight analysis
4. **Emits** triage classification: `[TRIAGE: FEATURE]` (or MAJOR_FIX, SMALL_FIX, DOCUMENTATION)
5. **Produces** a GROOMING HANDOFF containing:
   - Objective, Background (current → target state), Architecture
   - Database Schema, Files to Create/Modify
   - Success Criteria, Out of Scope, Questions, Processing Notes
   - USER FLOW references (which flows from the catalog does this task serve?)

**The WHAT-not-HOW principle** (from KU MASTER_GROOMING_STANDARDS): GROOMING specifies WHAT needs to change and WHY — not HOW to implement it. The handoff should contain: objective, architecture diagrams, database schema, success criteria (testable outcomes), files map, and out of scope. It should NOT contain: exact HTML snippets, JavaScript function implementations, or line-by-line code changes. That's EXECUTION's job.

Why this matters: EXECUTION reads the actual codebase and makes its own implementation decisions based on what it finds. Over-specified handoffs waste tokens twice — once when GROOMING writes the code, and again when EXECUTION reads the codebase and deviates from the spec anyway. A 1,000-line handoff full of code snippets is slower to ingest and produces more "deviations" than a 400-line handoff with clear constraints and testable outcomes. GROOMING provides the constraints that define done; EXECUTION provides the implementation that meets them.

**Exception**: Database schemas and migration SQL SHOULD be specified — these are structural contracts, not implementation opinions. Architecture diagrams showing data flow and component relationships SHOULD be specified. These constrain EXECUTION without micro-managing it.

**Phase markers** (from KU MASTER_GROOMING_STANDARDS): The single-session model tracks progress with markers: `[PHASE: GROOMING_COMPLETE]` → `[PHASE: DEVELOPMENT_COMPLETE]` → `[PHASE: UPDATE_COMPLETE]`. These replace the old workflow assignment system.

**If GROOMING realizes parts of a task are genuinely unrelated** (different hypotheses, different user-facing features, no shared context), it sends feedback to WORK to decompose. But if a task is one coherent feature with multiple implementation phases (intake flow + persistence + portal pages + tests), it stays as one task. The phases are interdependent — splitting them into separate sessions wastes context re-ingestion without adding value. GROOMING detects overlap and merger opportunities across tasks.

#### Function 2: Delivery Processing (Backward — EXECUTION → GROOMING)

Receives a **DELIVERY HANDOFF** from EXECUTION and:

1. **Reviews** what was built, what passed, what failed
2. **Creates follow-up TASKS** to update architecture docs and status docs
3. **Grooms** those follow-up tasks as **Document Workflow** handoffs
4. This ensures cross-project alignment after every delivery

#### Function 3: Escalation Handling

- If a task cannot be groomed (ambiguous, conflicting requirements) → escalate to WORK with feedback
- If project lacks capabilities needed for this task → flag and escalate
- If task doesn't fit the current project architecture → escalate with specific misalignment details

**Risk ownership: PROJECT RISK.** GROOMING identifies risks specific to the project context — "we don't have a database yet but this task assumes one", "this requires a shared component we haven't built", "this conflicts with our existing auth approach." HIGH PROJECT RISK → escalate to human before producing the grooming handoff. By the time something passes GROOMING, it should have the best chance of succeeding in EXECUTION because business risk (INTENT), technical risk (WORK), and project risk (GROOMING) have all been filtered.

**Model**: Sonnet (fast triage, context assembly)
**Tools**: Read, Write, Glob, Grep (no execution tools)
**Max turns**: 15

### 3.6 EXECUTION (Implementation Layer) ← NEW IN v3

**What it is**: Takes HANDOFFS from GROOMING and produces working, tested code.

**Two execution paths:**

#### Path A: Feature / Major Fix (from GROOMING HANDOFF)

```
GROOMING HANDOFF (includes Test Execution Contract — see Section 6.1)
    │
    ▼
Development Phase
    │
    ├──→ FIRST: Create TEST assets (Playwright specs, unit tests, workflow tests)
    │         + Create test runner script (bash, JSON output — see Section 6.2)
    │
    ├──→ THEN: Create OPS assets (source code, configs, deployments)
    │
    ├──→ Run tests via bash runner → read summary.json (token-efficient)
    │         │
    │         ├── ALL PASS → Emit [PHASE: DEVELOPMENT_COMPLETE]
    │         │                Send DELIVERY HANDOFF (success + summary.json) → GROOMING
    │         │
    │         └── ANY FAIL → Read failure detail → Fix code → Re-run
    │                  │
    │                  ├── Fixed → Loop back (re-run, read summary, check)
    │                  │
    │                  └── Same failure 3x →
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

**Session continuity: checkpoint-based resume.** When a session fails (turn limit hit, crash, race condition, API error), the system does NOT start a new session from scratch. Instead:

1. **Detect progress**: Scan the working directory for files created or modified since session start. Compare against the handoff's files-to-create/modify list. Determine what's done vs. what's remaining.
2. **Resume with context**: Use `claude --resume <session_id>` with a scoped prompt: "These files are complete: [list]. Continue from [next incomplete item]. Original handoff: [path]."
3. **Retry limit**: Max 2 resume attempts per task. If the session fails 3 times total (initial + 2 resumes), escalate via DELIVERY HANDOFF with partial progress documented.

This preserves the session's accumulated context (what it read, what decisions it made) rather than burning tokens re-ingesting the entire codebase from scratch. A resumed session already knows the architecture — it just needs to know where it left off.

**Why resume over restart**: A 65-turn session at $10 might spend $3-4 on context ingestion (reading existing files, understanding architecture). Restarting means paying that $3-4 again. Resuming skips it. Even if compaction has occurred, the resumed session retains more context than a fresh session that has to re-read everything.

**Risk ownership: TEST RISK.** EXECUTION identifies coverage gaps and quantifies them. For items implemented but not fully testable: assign a criticality rating (HIGH: payment logic, auth flows; MEDIUM: form validation; LOW: tooltips, cosmetics) so the human knows what matters. For items NOT implemented: escalate with failure details. The DELIVERY HANDOFF includes a risk summary:
- Implemented + tested (passing) → no risk
- Implemented + tested (failing after retries) → escalated with failure detail
- Implemented + NOT testable → criticality rating + reason ("requires live Stripe credentials")
- NOT implemented → escalation with explanation + suggestion for WORK to re-decompose with alternative approach

When EXECUTION fails on implementation, the failure routes back through GROOMING → WORK. WORK understands the hypothesis context and can present an alternative path that still serves the North Star. If the user pre-authorized "proceed with auto-fallback" (from WORK's risk assessment), this happens automatically.

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
- Task spans multiple unrelated scopes → split
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
| Grooming handoffs frequently failing in execution | Escalate — possible architectural issue |
| Test coverage declining | Execution quality needs attention |
| SLAs degrading (OPERATE phase) | IMAGINATION proposes optimizations |

---

## 5. Learning System and Shared Capabilities

### 5.1 The Collapse: Grooming Standards Replace Build Workflows

v3 (and KU's evolution) eliminated the BUILD_WORKFLOW and META_BUILD_WORKFLOW abstractions. They were unnecessary layers:

- **META_BUILD_WORKFLOW = GROOMING.** Creating build instructions for a new type of task is exactly what GROOMING does — it hydrates a task with project context and produces a grooming handoff. There's no separate "meta" step. KU's MASTER_GROOMING_STANDARDS now defines this directly.
- **BUILD_WORKFLOW = GROOMING HANDOFF.** The handoff document IS the build instructions. It contains architecture, success criteria, triage classification, and testable outcomes. That's a "build workflow" in every practical sense.
- **REQ_HANDOFF_TEMPLATE → MASTER_GROOMING_STANDARDS.** The old template-based approach was replaced by grooming standards that define HOW grooming is conducted, with phase markers (`[PHASE: GROOMING_COMPLETE]`, `[PHASE: DEVELOPMENT_COMPLETE]`, `[PHASE: UPDATE_COMPLETE]`) tracking progress.
- **"Shared build patterns" = accumulated DELIVERY_HANDOFFs.** Institutional memory, not a formal artifact. KU still uses MASTER_DELIVERY_HANDOFF_TEMPLATE for documenting completed work.

### 5.2 Three-Tier Learning System

Learning happens across three tiers, each at a different abstraction level:

**Tier 1: PATTERNS.md (abstract guidelines)**

Architectural and design patterns distilled from successful deliveries. Not exact functions — more like guidelines:
- "When building Temporal workflows, use signal-based state transitions, not polling"
- "For multi-tenant data, always use row-level security in Supabase"
- "Mobile forms should use steppers with localStorage persistence"

GROOMING reads PATTERNS.md during hydration. Over time, patterns emerge naturally from DELIVERY_HANDOFFs.

**Tier 2: SHARED_COMPONENTS catalog (concrete, unit-testable)**

Actual utility functions, modules, or services that multiple features import. These are code artifacts with tests:
- A phone number formatter function
- An auth middleware module
- A standard test runner script

Managed as a catalog (inventory file listing available components with paths, descriptions, and consumer lists). GROOMING references the catalog when hydrating to avoid rebuilding what already exists. Consumer linking enables impact assessment before changes.

**Tier 3: Grooming Standards evolution (template evolution)**

When GROOMING finds itself referencing the same PATTERN or SHARED_COMPONENT in 3+ consecutive handoffs, the update phase should fold it into the project's local grooming standards. This is organic template growth — the standards evolve to reflect what the project actually needs, not what we guessed at init time.

### 5.3 Learning Flow

```
EXECUTION produces DELIVERY_HANDOFF
         │
         ├── Update phase reviews delivery [PHASE: UPDATE_COMPLETE]
         │         │
         │         ├── Lessons learned? → Add to PATTERNS.md
         │         │
         │         ├── New reusable utility? → Add to SHARED_COMPONENTS catalog
         │         │
         │         └── Pattern repeated 3+ times? → Update local grooming standards
         │
         └── Next GROOMING session reads all three
                   → Produces better grooming handoffs
                   → Faster execution, fewer surprises
```

---

## 5.5 Execution Context

The executor operates in one of three contexts, set during `kh init` and injected into every session as `[EXECUTION_CONTEXT: LOCAL|MIXED|PRODUCTION]`. The context determines where data lives, how integrations work, what gets mocked, and how seed data is created.

**LOCAL** — Early development. SQLite, mocks, localhost. Maximum velocity, zero dependencies on external services. This is the default and the starting point for every project.

**MIXED** — Some services are production, some are local. The critical rule: DO NOT fall back to demo/mock data when real infrastructure exists. If the project has a Supabase database, seed THAT database. If S3 is configured, upload to S3. The executor reads `.env` files and existing integration code to determine what's real.

**PRODUCTION** — All services are production. Every mutation is real. Seed data must be clearly identifiable and cleanly removable. Extra caution required.

The executor fires TWICE in a full phase lifecycle — once during LOCAL/MIXED development, and again in PRODUCTION for post-go-live fixes and hotfixes. The same GROOMING and EXECUTION protocols apply in both, but the environment rules differ radically. See `protocols/EXECUTOR_STANDARDS.md` Section 2 for full context-specific rules.

```
EXECUTOR (LOCAL/MIXED)  ──→  CLOSING CEREMONY  ──→  GO-LIVE  ──→  EXECUTOR (PRODUCTION)
     │                                                                  │
     └── Build it right                                                 └── Make it real
         (SQLite/Supabase, mocks/real)                                     (all production)
```

`kh init` allows re-running to change context as the project evolves. Templates are always refreshed on re-init; config and state are preserved.

---

## 6. The Test-First Standard

Development always follows this pattern:

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

The GROOMING HANDOFF must instruct the execution session to be **aggressive about test cycling**. This is not "write tests, write code, run once, report." This is:

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

**The GROOMING HANDOFF must include this loop instruction explicitly.** It's not optional behavior — it's the standard execution contract (codified in KU's MASTER_GROOMING_STANDARDS). The session doesn't get to say "here's a checklist for you to verify." It verifies itself.

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

**The runner script** is itself a deliverable of the development phase. It:
- Runs the test suite with JSON reporter
- Parses output into `summary.json` (pass/fail counts, test names, durations)
- Extracts failure details into `failures/[test-name].txt` (just the error message and stack trace, not full DOM)
- Returns exit code 0 (all pass) or 1 (any fail)

**Token cost**: Reading a 20-line JSON summary vs. 2000 lines of raw Playwright output. Orders of magnitude difference. The CC session stays focused on analysis and fixes, not parsing noise.

---

## 7. State Management

### 7.1 Stateless vs. Stateful Boundary

```
STATELESS                          STATEFUL
(no session context)               (full project context)

  Foundation docs                    GROOMING HANDOFF
  Hypotheses                         (hydrated with project context,
  Decisions                           tech stack, architecture,
  Tasks from WORK                     triage classification)
       │                                    │
       └──── GROOMING BOUNDARY ─────────────┘
             (this is where hydration happens)
```

**Why this matters**: Claude Code sessions are stateless by default. Each session starts fresh. The GROOMING HANDOFF is the mechanism that gives a session everything it needs to execute — it IS the state.

### 7.2 Four Storage Types

Each storage type serves a different purpose at a different layer:

**Markdown files** — Human-readable documents that CC sessions consume and produce. Foundation docs (Oracle, North Star, Context), handoff documents (GROOMING_HANDOFF, DELIVERY_HANDOFF), project docs (ROADMAP, PRIMER, ARCHITECTURE), PATTERNS.md. These ARE the state for the abstract layers. REFLECTION reads Foundation + project docs. GROOMING reads project docs + patterns + handoff history.

**JSON files** — Simple configuration. `config.json` for orchestration settings (models, tools, paths, polling intervals). Lightweight, human-editable, no relationships needed.

**SQLite** (`.1kh/state.db`) — Queryable relational state for everything that needs relationships, aggregation, or concurrent access. Task dependencies ("what depends on task-003?"), hypothesis tracking across cycles, token usage history with aggregation, event log (append-only, feeds REFLECTION), shared component consumer links, human decision history (for preference trend detection). Single file, no server, portable. WAL mode for concurrent writes during parallel execution.

**Filesystem directories** — Queue state for the execution pipeline. The proven KU pattern: numbered directories (1_draft through 6_complete), file movement = state transition, `ls` = queue visibility. The execution engine keeps this internally for its pipeline mechanics.

**How they relate:**

```
┌─────────────────────────────────────────────────┐
│  1KH COORDINATOR                                 │
│                                                   │
│  SQLite (.1kh/state.db)                          │
│  ├── tasks table (id, hypothesis_id, state,      │
│  │    priority, dependencies, risk_tolerance)     │
│  ├── hypotheses table                             │
│  ├── events table (append-only log)               │
│  ├── tokens table (per-task, per-phase costs)     │
│  ├── components table (shared capability registry)│
│  └── decisions table (human choice history)       │
│                                                   │
│  Markdown (Foundation, project docs, patterns)    │
│  JSON (config.json)                               │
│                                                   │
├─────────────────────────────────────────────────┤
│  EXECUTION ENGINE (1KH internal)                  │
│                                                   │
│  Filesystem dirs (1_draft → 6_complete)           │
│  Markdown (GROOMING_HANDOFFs, DELIVERY_HANDOFFs)  │
│                                                   │
└─────────────────────────────────────────────────┘
```

The execution engine reports results (tokens, success/failure, delivery handoff path) back to the coordinator, which records them in SQLite.

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

### Headless Execution: No User Prompting, Ever

All CC sessions run with `claude -p` (print mode) — fully headless. Claude has no stdin access and **physically cannot prompt the user**. This is a safety guarantee, not a convention. The implications:

- **`--dangerously-skip-permissions`** (EXECUTION build phases): All tool calls auto-approved. Claude can read, write, edit, and run bash without pausing. This is what enables the aggressive test loop — the session runs freely until it hits the turn limit or completes.
- **`--allowedTools "Read,Write,Glob,Grep"`** (GROOMING, doc update phases): Restricts available tools. Anything outside the list is silently denied. Claude can't accidentally run bash in a grooming session. This is defense-in-depth — the prompt says "don't run code" but the tool restriction enforces it.

Claude will never block waiting for user input. The only "hang" scenarios are: API latency, long-running tool calls (big test suites), or hitting the turn limit. All three are observable via session logs (Section 11.8) and have natural timeouts.

### Token Estimation and Tracking

Every task carries two token fields:
- **`estimated_tokens`** — set by WORK/GROOMING based on triage level and historical averages for similar tasks
- **`actual_tokens`** — set after EXECUTION, extracted from Claude CLI JSON response (input, output, cost_usd per phase)

Over time, the system builds a calibration model: "FEATURE tasks for this project average 35K input + 18K output tokens." REFLECTION flags when estimates diverge significantly from actuals — either estimates need recalibrating or tasks are hitting unexpected complexity.

**Pre-cycle cost forecast**: Before starting a cycle, estimate total cost across all pending tasks: "This cycle has 5 tasks, estimated total cost: ~$4.20." User can approve, adjust scope, or set a budget ceiling.

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
   - Triage classification emitted: `[TRIAGE: FEATURE]`
   - Produces: GROOMING_HANDOFF_ORDERING_WIDGET.md
     (architecture, DB schema, success criteria, test execution contract)

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
| Handoff documents | Not present | GROOMING_HANDOFF and DELIVERY_HANDOFF (evolved from KU) |
| State management | Conceptual | Filesystem queue + JSON state (from KU) |
| Model selection | Not specified | Sonnet/Opus by phase (from KU) |
| Shared capabilities | Deferred to Phase 13 | Three-tier learning system (PATTERNS, SHARED_COMPONENTS, template evolution) |
| Meta Build | "Factory of factories" concept | **Eliminated** — GROOMING IS the meta build; the grooming handoff IS the build spec |
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

### 11.6 User Preference Trend Detection

**Decision**: Moving-average trend detection on human decisions, surfaced by REFLECTION, stored in SQLite.

**The problem**: Over time, the human makes choices — approving some hypotheses, rejecting others, overriding GROOMING's triage classification, choosing risk tolerance options, accepting or refusing escalations. Each individual decision is noise. But patterns across decisions reveal real preferences that the system should learn. We try to ignore single signals and follow moving averages.

**WHERE decisions are tracked:**

SQLite `decisions` table in `.1kh/state.db`:

```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,          -- ISO-8601
    decision_type TEXT NOT NULL,      -- 'hypothesis_approval', 'risk_tolerance',
                                      -- 'escalation_response', 'triage_override',
                                      -- 'scope_adjustment', 'foundation_change'
    category TEXT NOT NULL,           -- grouping key (e.g., 'test_coverage',
                                      -- 'risk_appetite', 'feature_scope',
                                      -- 'tech_preference', 'ux_priority')
    choice TEXT NOT NULL,             -- what the human chose
    alternatives TEXT,                -- JSON array of what was offered
    context TEXT,                     -- brief context (hypothesis id, task id, etc.)
    layer TEXT NOT NULL               -- which layer surfaced this decision
);
```

Every time the human makes a choice at an escalation point, WORK/GROOMING/EXECUTION logs it here. This is NOT a separate tracking system — it's a natural byproduct of the existing escalation flow. When WORK presents risk tolerance options and the human picks one, that's a row. When INTENT asks whether to nurture or prune, that's a row.

**HOW trends are detected:**

REFLECTION queries the `decisions` table during its analysis pass. The mechanism:

1. **Group by category** — e.g., all decisions tagged `risk_appetite` in the last N decisions (default window: last 10 decisions per category).
2. **Compute moving average** — for each category, what percentage of recent decisions lean the same way? Example: 8 out of last 10 `risk_appetite` decisions chose "proceed with auto-fallback" over "escalate to me."
3. **Apply threshold** — if 70%+ of decisions in a window lean the same direction, flag as a trend. The 70% threshold is a starting default, not dogma.
4. **Recency weighting** (optional, future refinement) — more recent decisions count slightly more than older ones. Simple linear decay within the window. Not required for v3 MVP; flat average is fine to start.

```
Example REFLECTION query:

SELECT category, choice, COUNT(*) as count,
       COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY category) as pct
FROM decisions
WHERE category = 'risk_appetite'
ORDER BY timestamp DESC
LIMIT 10
GROUP BY choice

Result:
  risk_appetite | proceed_with_auto_fallback | 8 | 80%
  risk_appetite | escalate_to_me             | 2 | 20%

→ 80% > 70% threshold → trend detected
```

**WHAT triggers a proposal:**

When REFLECTION detects a trend (70%+ consistency within a window), it generates a Foundation preference update proposal:

```
REFLECTION RECOMMENDATION:
  Type: PREFERENCE_UPDATE
  Category: risk_appetite
  Observation: "In 8 of your last 10 risk decisions, you chose 'proceed with
               auto-fallback' over 'escalate to me.' This suggests you're
               comfortable with autonomous error recovery."
  Proposal: "Update Foundation preferences to default risk_tolerance =
            'proceed_with_auto_fallback' for TECHNICAL RISK and PROJECT RISK.
            This would reduce escalation interrupts. You can still override
            per-task."
  Requires: Human approval (this is a Foundation-level TWEAK)
```

The key: REFLECTION doesn't silently change behavior. It presents the trend, proposes the update, and waits for approval. The human sees the data and decides.

**WHEN it runs:**

Preference trend detection runs as part of REFLECTION's standard analysis pass — the same triggers defined in Section 11.4 (schedule + delivery events + escalations). It's not a separate process. When REFLECTION fires, one of its analysis steps is: "query decisions table, check for trends, include any proposals in recommendations."

**What it does NOT do:**

- Does NOT auto-update Foundation preferences without human approval
- Does NOT track or analyze the *content* of what was built — only the *decisions* the human made at escalation points
- Does NOT override explicit per-task choices — even if the default changes, the human can still choose differently
- Does NOT fire on single signals — the whole point is moving averages over a window

### 11.7 Shared Capability Conflict Resolution

**Decision**: Simple local queue. First-to-complete locks, second waits.

When two parallel tasks both modify the same shared component, the system queues the conflict rather than racing. The mechanism:

1. Before EXECUTION writes to a shared component, it checks a lockfile (`.1kh/locks/{component_id}.lock`). If absent, it creates one with its task ID and proceeds.
2. If the lock exists, the task pauses that specific write and continues with other work. It retries the locked write on a short interval (configurable, default 30s).
3. When the first task completes and releases the lock, the second task acquires it. At this point, EXECUTION reads the updated component state before applying its own changes — ensuring it's working against the latest version.
4. If a lock is held for longer than a timeout (configurable, default 10 minutes), the system escalates to GROOMING as a blocked task.

This is deliberately simple — filesystem lockfiles, no external coordination service. It works because the execution engine already uses filesystem-as-queue patterns (from KU). Locks are cleaned up on session completion and on graceful shutdown (same cleanup path as KU's sentinel-based stop).

**Why queue over first-to-merge**: Merging requires diffing and conflict resolution logic that's complex to get right autonomously. Queuing is predictable — the second writer always sees the first writer's complete output. The tradeoff is latency (one task waits), but shared component writes are typically fast compared to the full build cycle.

### 11.8 Watch Mode Implementation

**Decision**: Log tailing MVP, tmux build-out.

**MVP (immediate)**: Stream-based log tailing, proven by KU's `ku logs` command. The implementation:

- Every CC session runs with `--output-format stream-json`, capturing output to `.1kh/sessions/{task_id}_{phase}_stream.jsonl`
- An `active_stream` marker file tracks the currently-running session
- `1kh logs` (or `1kh watch`) tails the active stream with `tail -f` piped through `jq` parsing
- Displays: session ID, tool calls (with file paths / commands / patterns), and final result (success/fail, turn count, cost)
- For completed sessions, falls back to the most recent stream file without live tailing

This is exactly KU's approach — it works today. The parsed output shows what Claude is doing (reading files, writing code, running tests) without drowning the user in raw JSON.

**Build-out (next)**: tmux-based multi-pane interface for concurrent session monitoring:

```
┌──────────────────────────────┬──────────────────────────────┐
│  Task A: Ordering Widget     │  Task B: Dashboard           │
│  [live stream]               │  [live stream]               │
│  [tool] Read: /src/widget.ts │  [tool] Bash: npm test       │
│  [tool] Write: /src/api.ts   │  [tool] Read: results.json   │
│  ...                         │  ...                         │
├──────────────────────────────┴──────────────────────────────┤
│  1KH Status: 2 active sessions | 1 queued | $2.15 spent    │
└─────────────────────────────────────────────────────────────┘
```

tmux is the right tool because: it's local, requires no web server, handles multiple panes natively, and the user can attach/detach without affecting running sessions. The coordinator spawns tmux panes for each active session and a status bar pane.

**Session logging storage** (from KU v0.2 patterns):

- Stream files: `{task_id}_{phase}_stream.jsonl` (live JSONL from Claude CLI)
- Result files: `{task_id}_{phase}.json` (final parsed result)
- Prompt files: `{task_id}_{phase}_prompt.txt` (exact prompt sent, for debugging)
- Append-only event log: `.1kh/1kh.log` (timestamps, phase transitions, errors)

### 11.9 Simulation → Production Handoff

**Decision**: Early research, knowledge center with breadcrumbs, seed data scripts, mock-to-real credential swap.

The handoff from simulation to production is not a single event — it's a progression that starts at FOUNDATION and completes at EXECUTION. The system anticipates production needs early and prepares incrementally.

**Phase 1: Research during FOUNDATION/IMAGINATION**

Between FOUNDATION (init or adopt) and WORK, the system researches what production will require. Claude already does this well — exploring APIs, reading docs, understanding integration requirements. Research findings go to a **knowledge center**: `.1kh/knowledge/` with markdown files organized by topic (e.g., `stripe_integration.md`, `supabase_auth.md`). Each file includes:
- What the integration requires (API keys, accounts, configuration)
- What the user needs to do (register, enable features, configure webhooks)
- Estimated timeline for user setup
- Pointer references / breadcrumbs back to the specific hypothesis or task that needs this

The knowledge center is a living reference — GROOMING reads it during hydration, EXECUTION reads it during implementation. It prevents the system from re-researching the same integration twice.

**Phase 2: Mock infrastructure during SIMULATE**

During local simulation, the system creates the full credential and data infrastructure in mock form:

- **Environment templates**: `.env.example` with every required variable, commented with descriptions and where to get the real value. `.env.local` populated with mock/test credentials.
- **Config profiles**: `config.local.json`, `config.staging.json`, `config.production.json` — same structure, different values. The swap from local to production is changing which config file is active, not restructuring anything.
- **Test users and seed data**: Scripts that populate the database with realistic test data representing all the various end-to-end outcomes users can encounter. `scripts/seed.sh` creates test users, sample orders, edge-case data. `scripts/purge.sh` cleans it all out for fresh test runs. These scripts are themselves tested — they're part of the e2e suite.
- **Realistic mocks for business data**: If the user hasn't specified all pricing, products, or business details, the system researches comparable businesses and fills in realistic placeholders. This gets the build as close to MVP as possible without blocking on user decisions. These mocks are flagged as business risk items that the user should review pre-launch.

**Phase 3: Credential swap during EXECUTE**

The actual production cutover:
1. User provides real credentials (API keys, database URLs, etc.)
2. System populates `.env.production` from the template
3. Run the full test suite against staging/production config
4. Any failures from real API behavior differences (vs mocks) route through the normal test loop (Section 6.1)
5. Seed scripts can optionally run against production for initial data setup

**Business risk escalation**: Any business data the system filled in as "realistic mocks" (pricing, product details, terms) gets escalated back to the user as BUSINESS RISK before launch. The system says: "I used mock pricing based on research of comparable businesses. Here's what I assumed — please review and correct before going live." This is INTENT-layer risk (Section 3.3) surfaced at the right time.

### 11.10 Session Continuity and Task Granularity

**Decision**: Lean handoffs + long sessions + checkpoint resume. No task splitting for coherent features.

This decision resolves the fundamental tension between splitting large tasks into mini-tasks vs. running long expensive sessions. The answer is neither extreme — it's optimizing the pieces we control.

**The problem, observed in practice**: A MAJOR_FIX task (nutrition intake overhaul) ran 65 turns, cost $10.19, and produced 12 files / ~5,000 lines. It succeeded — but ~30% of token spend was context ingestion (reading 15+ files, re-reading several), not implementation. The handoff was 1,055 lines including exact code snippets that EXECUTION largely ignored in favor of what it found in the codebase. The session hit a false-failure due to a race condition in result parsing, despite producing a correct delivery.

**Why NOT split into mini-tasks (the SCRUM lesson)**: Splitting one coherent feature into 4 sub-tasks means 4 sessions that each re-read most of the same files. The same "dev" picks up all 4 stories because they share context. They deploy together because the feature only works as a whole. User verification (UX, e2e) can only occur once everything is delivered. Splitting adds overhead (context re-ingestion, state management between sub-tasks) without adding value. This mirrors the XP team insight: splitting a 13-point story into four 3-point stories creates waste when the same developer handles all four and they ship together.

**Why NOT just accept $10 sessions**: The cost isn't inherently wrong — $10 for 5,000 lines of working code is reasonable per-line. But $3-4 of that was avoidable context ingestion caused by an over-specified handoff. A leaner handoff (WHAT not HOW) reduces ingestion cost. And when sessions DO fail, checkpoint-based resume avoids re-paying the ingestion tax.

**The three-part solution:**

1. **Lean handoffs (GROOMING)**: Specify WHAT and WHY, not HOW. Objective, architecture, schema, success criteria, files map, out of scope. Cut the code snippets — EXECUTION reads the codebase and makes its own implementation decisions. A 400-line handoff instead of 1,055. (See Section 3.5, Function 1.)

2. **One session per TRoN (EXECUTION)**: A TRoN (Tiniest Runnable Notion) is the smallest unit of independently verifiable user value. One TRoN = one session. Don't split coherent features into implementation phases across separate sessions. (See Section 3.4.)

3. **Checkpoint-based resume (EXECUTION)**: When sessions fail, detect progress and resume — don't restart from scratch. The accumulated context is worth preserving. (See Section 3.6.)

**What GROOMING CAN reject**: If a task from WORK contains genuinely unrelated features crammed together (different hypotheses, different user-facing capabilities, no shared context), GROOMING pushes back to WORK for decomposition. But "nutrition intake with phone auth + persistence + portal migration + e2e tests" is one coherent feature — the pieces are interdependent and must ship together. GROOMING keeps it as one task.

**What GROOMING CANNOT do**: Split a coherent TRoN into implementation phases ("first build the API, then build the UI, then write tests"). That's EXECUTION's internal concern. GROOMING provides the constraints; EXECUTION decides the implementation sequence.

### 11.11 Project Documentation Organization

**Status: RESOLVED (2026-02-08)**
**Context:** MVH had 7 overlapping docs (PRIMER, ARCHITECTURE_STATUS, ROADMAP, TECH_STACK, SETUP_GUIDE, SUBDOMAIN_ARCHITECTURE, PREPROD_CHECKLIST) totaling ~2,200 lines. Three Claude sessions reading the same redundant docs = context waste.

**Principle: ONE Central Architecture Document Per Project**

Every managed project must have a single `ARCHITECTURE.md` that:
1. Is ALWAYS read at session start (GROOMING reads it, EXECUTION reads it)
2. Is ALWAYS updated at session end (EXECUTION updates feature status, roadmap)
3. Contains: quick reference, tech stack, deployment, integrations, feature status, roadmap, pre-production checklist, delivery index
4. Target: 600-800 lines (not 2,200 across 7 files)

**Document Directory Structure:**

```
docs/
├── ARCHITECTURE.md          ← Single source of truth (always read, always update)
├── WORKFLOW_CATALOG.md      ← Separate (Mermaid diagrams, reference-only)
├── CC_HANDOFF_*.md          ← Active implementation specs (not yet delivered)
├── delivery/                ← Completed delivery handoff docs
│   └── DELIVERY_*.md
├── handoffs/                ← Paired CC_HANDOFF + DELIVERY for completed features
│   ├── CC_HANDOFF_*.md
│   └── DELIVERY_*.md
├── reference/               ← Supporting material (not primary reading)
│   ├── SETUP_GUIDE.md       ← Code examples for integrations
│   └── *.md                 ← Design docs, specs, trackers
├── lessons/                 ← Operational lessons learned
└── __ARCHIVE__/             ← Deprecated docs (never reference)
```

**Rules:**
- **Consolidate, don't concatenate.** When 3 docs describe the same deployment sites, write it once.
- **DELIVERY HANDOFFs are living feature guides.** They document what was built, what changed, what needs deployment. ARCHITECTURE.md links to them via a Delivery Index section.
- **Reference docs are NOT primary reading.** SETUP_GUIDE with code examples stays in reference/ — ARCHITECTURE.md says "see reference/SETUP_GUIDE.md for full code examples."
- **Archive aggressively.** If a doc's content has been fully absorbed into ARCHITECTURE.md, move it to __ARCHIVE__/.
- **`ku init` suggests ARCHITECTURE.md first.** When initializing a project, the doc selector should highlight the central architecture doc as the primary choice.

**Anti-pattern:** Multiple docs that each cover "deployment sites" (PRIMER says 3 sites, TECH_STACK says 3 sites, ARCHITECTURE_STATUS says 3 sites, SUBDOMAIN_ARCHITECTURE says 3 sites). One of them will get stale. Write it once in ARCHITECTURE.md.

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

### 12.4 Data-First Development Directive

For vaguely-described large features, the system follows this priority order:

```
1. DATA LAYER (schema, API routes, business logic, persistence)
   │  Fully testable autonomously. No subjective judgment needed.
   │  Build and test this before anything visual.
   │
   ▼
2. MINIMAL UX (simple copy, form inputs, validation, controls, persistence)
   │  Functional but unstyled. Proves the data layer works end-to-end.
   │  Focus: correct behavior, not appearance.
   │
   ▼
3. MOBILE-FIRST LAYOUT (responsive structure, navigation, viewport)
   │  Design for smallest screen first, expand up.
   │  Layout and information architecture, not visual polish.
   │
   ▼
4. STYLING (colors, fonts, sizes, brand personality)
   │  Fit to user preferences, brand identity, and project personality.
   │  This is the last step, not the first.
```

**Why this order**: Data layer is objectively testable — the system can verify it works without human judgment. UX requires subjective evaluation that the system can't fully automate. Building data first means the UX is wiring up to proven, tested endpoints — not building on sand.

**Exception**: If the user explicitly requests "I just want a landing page design" or is specifically working on UX interfaces only, respect that. GROOMING should verify: "This task appears to be UX-only with no data layer component — confirming this is intentional before proceeding."

### 12.5 Acceptance Criteria: Given/When/Then as One Tool in the Toolbelt

Given/When/Then is **one tool in the toolbelt** for writing acceptance criteria — not the only way. It's the default for behavioral, interaction-driven criteria because it maps cleanly to test assertions. But not every acceptance criterion is behavioral.

**When to use Given/When/Then** — user-facing behavior, form interactions, navigation flows, state transitions:

```
Given: user navigates to /intake
When: user types "5551234567" in phone field
Then: display shows "(555) 123-4567"

Given: user is on intake form with all fields empty
When: user clicks Submit
Then: validation errors appear on all required fields
```

**Why it works here**: Forces GROOMING to specify precondition, action, and expected outcome. Prevents vague criteria like "phone masking works." Maps 1:1 to Playwright test assertions — EXECUTION translates each Given/When/Then directly into a test spec.

**When to use other formats** — performance targets, schema constraints, integration contracts, infrastructure requirements:

- "API response time < 200ms at P95 under 100 concurrent requests" (measurable threshold)
- "Database schema includes orders table with columns: id, user_id, total, status, created_at" (structural assertion)
- "Stripe webhook handler returns 200 for valid signatures and 400 for invalid" (contract spec)
- "All environment variables defined in .env.example exist in production config" (checklist)

These are perfectly valid acceptance criteria that don't need Given/When/Then framing. GROOMING should pick the format that communicates the criterion most clearly to EXECUTION. The goal is unambiguous, testable criteria — the syntax is a means, not an end.

**Where it applies**: Success Criteria section of grooming handoffs only. The rest of the requirements chain uses natural language. This is a communication convention between GROOMING and EXECUTION, not a system-wide format. The system writes acceptance criteria; human 1KH owners don't need to use any specific syntax.

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

Every single one of these can be a Playwright assertion. The execution session has all the tools to run these tests itself — it just wasn't instructed to loop through them aggressively. The problem isn't capability, it's the handoff contract. The grooming handoff didn't demand "run until green or escalate." It let the session stop at "here's what to check."

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

### 14.3 Grooming Handoff Amendment

To make this standard enforceable, the grooming handoff must include a **Test Execution Contract** section:

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

This contract is not a suggestion — GROOMING bakes it into every handoff (enforced by KU's MASTER_GROOMING_STANDARDS). The execution session has clear instructions: you are not done until tests are green or you've hit the retry ceiling and escalated.

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

**No blocking open questions remain.** All questions from prior revisions have been resolved.

*Resolved this revision: Intermediate artifact schemas — JSON schemas for ReflectionResult, Hypothesis, Task, UserFlow, ExecutionResult, Event promoted from draft to `INTERMEDIATE_ARTIFACTS.md`. Thresholds (0.65 approval, 0.40 escalation) shipped as initial values with calibration process defined. See Section 17 for file reference.*

*Resolved prior revisions: Cost management (Section 8). BUILD_WORKFLOW/META_BUILD collapse → Grooming Standards (Section 5). Risk layering (Sections 3.3-3.6). State management storage (Section 7). Data-first development (Section 12.4). User preference trend detection (Section 11.6). Shared capability conflict resolution (Section 11.7). Watch mode (Section 11.8). Simulation → production handoff (Section 11.9). KU terminology alignment — REQ_HANDOFF → GROOMING_HANDOFF, MASTER_GROOMING_STANDARDS replaces old templates. Ceremony model — 3 ceremonies (Opening, Simulation, Closing) + the work as a process. User Flow Catalog as first-class WORK layer artifact (Section 0).*

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

### 16.3 What to Learn from KU (latest)

**KU is production-solid and actively evolving. We lean on this heavily.**

*KU latest: 2,067-line orchestrator with WHAT-not-HOW groom prompts, master/local template split, interactive doc selection, checkpoint resume, and triage-aware content scoping.*

| KU Component | Location | What to absorb | What to leave behind |
|-------------|----------|----------------|---------------------|
| **ku.sh orchestrator** (2,067 lines) | `kanban-utility/bin/ku.sh` | The entire state machine: 6-state filesystem-as-queue, file movement as transition, COMPLETE: marker parsing, signal handling (Ctrl+C kills process group), sentinel-based graceful stop (`ku stop`), session debug logging (full JSON + prompt saved), `ku logs` with stream-json tailing, `ku resume` for checkpoint-based session recovery. This is the execution engine blueprint. | Single dev concurrency (`max_concurrent.develop = 1`). v3 lifts this. |
| **MASTER_GROOMING_STANDARDS** | `kanban-utility/templates/MASTER_GROOMING_STANDARDS.md` | Grooming phase standards enforcing WHAT-not-HOW, triage classification (FEATURE/MAJOR_FIX/SMALL_FIX/DOCUMENTATION), phase markers (`[PHASE: GROOMING_COMPLETE]` etc.), testing expectations by triage level. Replaced the old REQ_HANDOFF_TEMPLATE with a standards-driven approach. | v3 evolves: add Test Execution Contract (Section 6.1), USER FLOW references, shared capability references. |
| **MASTER_DELIVERY_HANDOFF template** (92 lines) | `kanban-utility/templates/MASTER_DELIVERY_HANDOFF_TEMPLATE.md` | Compact delivery format: summary with deviation assessment, completed/blocked/future items, deployments checklist, test table, doc updates needed (project-specific rows injected at init). | v3 evolves: add summary.json contents, shared capability publish/consume log. Replace manual verification checklist with automated test results (Section 14). |
| **Master + local template pattern** | `templates/MASTER_*.md` → `.kanban/templates/` | Immutable master blueprints at package level. `ku init` generates local copies injected with project-specific doc references. Local templates evolve per-project; masters don't change. This IS the Tier 3 learning infrastructure (Section 5.2). | Directly adopted. |
| **Interactive doc selection** | ku.sh `select_project_docs()` + `cmd_init()` | Scans project for `.md` files, interactive numbered menu, user selects which docs matter. Stored in `config.json` as `known_docs[]` (relative paths). Template generators inject these into grooming and delivery contexts. Zero Claude calls during init. Re-running init picks up new docs. | v3 extends: Foundation doc detection (`init` vs `adopt`), USER FLOW CATALOG injection. |
| **WHAT-not-HOW groom prompt** | ku.sh groom prompt (lines 770-806) | Explicit instruction: "Specify WHAT needs to change and WHY, not HOW. NO code snippets. Architecture = flow diagrams only. Database = DDL only." Dev prompt mirrors: "The handoff is a constraint doc, not a recipe." | Directly adopted — this is the lean handoff principle (Section 3.5) working in practice. |
| **Triage-aware content scoping** | ku.sh groom + dev prompts | FEATURE/MAJOR_FIX/SMALL_FIX/DOCUMENTATION — classified once by groom, all downstream phases adjust. SMALL_FIX skips E2E + uses only 3 handoff sections. DOCUMENTATION skips tests and gets lightweight update. Triage embedded as HTML comment. | Nothing — this is clean and directly adopted. |
| **Checkpoint resume** | ku.sh `cmd_resume()` (lines 1514-1711) | Re-attaches to prior session via `claude --resume <session_id>`. Moves file back to active queue. Injects minimal resume prompt. Extracts new session_id (can chain resumes). Phase-aware: knows which phase to resume based on item state. | v3 extends: add progress detection (scan working dir for created/modified files, compare against handoff files-to-modify). |
| **config.json schema** | `kanban-utility/defaults/config.json` | Configurable models per phase, allowed tools per phase, `known_docs[]` (user-curated relative paths), docs_path/handoffs_path, polling_interval, max_concurrent stubs. Clean separation of orchestration config from project config. | v3 extends: add cost budgets, concurrency limits per hypothesis, reflection trigger config. |
| **state.json schema** | `kanban-utility/defaults/state.json` | Per-item tracking: id, state, triage, priority, per-phase session IDs (`.sessions.groom`, `.sessions.dev`, `.sessions.update`), req_handoff, delivery_handoff, tokens (per-phase: input/output/cost_usd), started_at, completed_at, error. Active session tracking. | v3 extends: add hypothesis_id, dependency links, retry counts, reflection event log. |
| **Priority + timestamp ordering** | ku.sh `cmd_process_dev()` | Two-level sort: `.priority` ascending then `.started_at` FIFO. Adjustable via `ku prioritize`. Prevents starvation while giving human control. | v3 adds: dependency-aware ordering (WORK's responsibility, not just priority). |
| **Token tracking** | ku.sh `store_tokens()` | Every phase records input_tokens, output_tokens, cost_usd. Extracted from Claude CLI JSON response. Stored in state.json per-item per-phase. Visible via `ku status` and `ku view`. | v3 extends: aggregate cost per hypothesis, per cycle, budget ceiling alerts. |
| **Aggressive execution philosophy** | ku.sh dev prompt preamble | "BEST EFFORTS / AGGRESSIVE EXECUTION. Do NOT stall on decisions. Pick the pragmatic option and MOVE IT ALONG. If ambiguous, assume and document." This philosophy carries into v3. | Needs test-loop amendment (Section 6.1) to also be aggressive about *verification*, not just implementation. |
| **Graceful shutdown** | ku.sh `cleanup()` + `check_stop_sentinel()` | Ctrl+C → `kill -- -$$` (kills entire process group including Claude child). `ku stop` → writes STOP sentinel file, checked before each Claude launch and between watch loops. No orphaned processes. | Directly adopted. |

### 16.4 What v3 Builds New

These are components that don't exist in either v2 or KU and must be designed from scratch:

| New Component | Purpose | Why it's new |
|--------------|---------|-------------|
| **GROOMING engine** | Hydrates tasks with project context, classifies triage, produces grooming handoffs | KU does this manually (user writes tasks). v3 automates it as a CC session. |
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
2. **GROOMING session** — Given a task file and project context, produce a grooming handoff following MASTER_GROOMING_STANDARDS. Prove this works with a real task.
3. **EXECUTION session with test loop** — Given a grooming handoff, build code, run tests, cycle through failures, produce DELIVERY_HANDOFF. Prove end-to-end.
4. **WORK layer** — Task state management, dependency ordering, queue processing. Connect to GROOMING.
5. **REFLECTION session** — Read state files, analyze patterns, produce recommendations. Connect to Foundation.
6. **IMAGINATION + INTENT** — Hypothesis generation and strategic decisions. These are the abstract layers that feed WORK.
7. **Foundation ceremony** — The `init` experience that establishes Oracle, North Star, Context.
8. **Watch mode / dashboard** — User experience layer on top of the working system.

Each step is usable independently — you don't need step 7 to use step 3. This allows incremental value delivery.

---

## 17. File References

### docs/ — Foundational Architecture (guides source creation)

| Document | Purpose |
|----------|---------|
| `docs/ARCH_V3.md` | v3 architecture specification — the primary document |

### protocols/ — Runtime Protocols (consumed as-is by kh.sh sessions)

| Protocol | Consumed By | Purpose |
|----------|-------------|---------|
| `protocols/EXECUTOR_STANDARDS.md` | `kh run` (DEVELOPMENT phase) | Opinionated local-first build guidelines + TDD protocol |
| `protocols/CLOSING_CEREMONY.md` | `kh close` | UAT preparation & delivery process |

### templates/ — Per-Project Templates (customized during kh init)

| Template | Purpose |
|----------|---------|
| `MASTER_GROOMING_STANDARDS.md` | Grooming phase standards: triage, WHAT-not-HOW, user flow management, phase markers |
| `MASTER_DELIVERY_HANDOFF_TEMPLATE.md` | Delivery handoff blueprint with project-specific doc rows |
| `USER_FLOWS_TEMPLATE.md` | Starter user flow catalog — created by `kh init` if no catalog exists |
| `ARCHITECTURE_TEMPLATE.md` | Starter architecture doc — created by `kh init` if no arch doc exists |

### staging/ — TBD (not yet integrated into source)

| Document | Future Home | Dependency |
|----------|-------------|------------|
| `OPENING_CEREMONY.md` | → `protocols/` | When `kh open` is built |
| `ORCHESTRATOR_STANDARDS.md` | → `protocols/` | When orchestrator layer is built |
| `INTERMEDIATE_ARTIFACTS.md` | → absorbed into ARCH or `protocols/` | When full layer coordination is built (see note below) |

> **Note on INTERMEDIATE_ARTIFACTS:** Defines JSON schemas for inter-layer data contracts (ReflectionResult, Hypothesis, Task, UserFlow, ExecutionResult, Event). Currently referenced by ARCH_V3 but not consumed by kh.sh at runtime. Two futures: (a) ARCH_V3 absorbs the schemas inline, or (b) when the full layer system is built (IMAGINATION→INTENT→WORK→GROOMING→EXECUTION as coordinated sessions), the schemas become a runtime protocol. Decision deferred until that work begins.

### KH CLI Commands

| Command | Purpose |
|---------|---------|
| `kh init` | Initialize .kh structure, select project docs, create USER_FLOWS.md and ARCHITECTURE.md if missing |
| `kh add "name"` | Add draft task from stdin. Flows are managed by AI during grooming (no separate add-flow needed) |
| `kh run` | Process all drafts through GROOMING → DEVELOPMENT → UPDATE |
| `kh close [modifier]` | **Closing ceremony** — comprehensive test review, flow coverage audit, UAT preparation |
| `kh status` | Show queue status + user flow coverage + token usage |
| `kh logs` | Live-tail active session or show last completed |
| `kh resume "name"` | Resume a failed session from checkpoint |
| `kh demote/promote/remove` | Manual queue management |

### Archive

| Document | Location | Purpose |
|----------|----------|---------|
| v2 Archive | `/1KH/archive/thousandhand_v2/` | Complete v2 codebase and docs |
| v2→v3 Reflection (archived) | `/1KH/archive/REFLECTIONS_FROM_v2_TO_v3.md` | Historical transition notes (archived — do not reference for current state) |
| KU Demo Archive | `/1KH/archive/demo-kanban-utility-mvh/` | Original KU installation from MVH project |

*All paths relative to thousandhand_v3/ unless noted with leading `/`.*

---

*This is the v3 architecture. No blocking open questions remain. Implementation begins when the founder approves.*

*Last Updated: 2026-02-09*
