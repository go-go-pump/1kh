# ThousandHand (1KH) v3

> A lightweight wrapper that employs AI to create, manage, and monitor systems that drive business objectives.

ThousandHand is a methodology and CLI toolchain for building software products using AI-powered orchestration. It coordinates Claude Code sessions through a structured pipeline — from raw idea capture to tested, deployed systems — while keeping human judgment at the strategic layer.

## What It Does Today

**`kh` — a bash CLI** that manages a filesystem-based workflow for AI-orchestrated development:

```
kh init                        Initialize a .kh/ workspace in any project

kh raw "name" < dump.md        Capture a brain dump or observation list
kh raw list                    List all raw inputs + breakdown status
kh raw show "name"             View raw input + its breakdown report
kh breakdown "name"            AI-powered triage: split raw into discrete, categorized drafts

kh add "name" < task.md        Add a pre-scoped task directly (skips pre-flow)
kh status                      Show current queue + active phases
kh view "name"                 View a task file and its metadata
kh prioritize "name" <n>       Set task priority (lower = first)

kh run                         Process all drafts (grooming → execution per item)
kh logs                        Live-tail the active Claude session
kh watch                       Continuous monitoring mode
kh stop                        Stop a running watch/run

kh close [modifier]            Closing ceremony: UAT prep, test coverage audit, delivery

kh demote "name"               Move task back to draft (redo from scratch)
kh promote "name"              Manually advance task to complete
kh resume "name"               Resume a failed Claude session from checkpoint
kh remove "name"               Permanently remove an item and its files
```

The core innovation is the **pre-flow pipeline**: unstructured brain dumps (30+ observations in a stream of consciousness) get decomposed by AI into discrete, JM-mapped draft items ready for grooming. No manual splitting required.

```
BRAIN DUMP ──→ BREAKDOWN (AI triage) ──→ DISCRETE DRAFTS ──→ GROOMING ──→ EXECUTION
                     │
                     ├── Maps each item to Journey Mappings + User Flows
                     ├── Groups related items into execution batches
                     ├── Defers out-of-scope ideas (with auto re-evaluation)
                     └── Updates catalogs with [PLANNED] entries
```

## What It Seeks To Do

ThousandHand's north star is **autonomous system creation** — going from a founder's values and objectives to working, tested, deployed software with minimal human intervention. The human provides the *what* and *why*; 1KH orchestrates the *how*.

The full architecture defines five layers that fire in sequence:

```
FOUNDATION → IMAGINATION → INTENT → WORK → GROOMING → EXECUTION
     │              │          │        │        │           │
  Oracle,      Risk analysis  North   Tasks,   Scope      Working,
  North Star,  stress-test   Star →   User    validation, tested
  Context      across phases  Tasks   Flows   TDD setup   code
```

Three **ceremonies** (exchange events between human and system) punctuate the process: an **Opening Ceremony** to capture the founder's vision, a **Simulation Ceremony** to stress-test it, and a **Closing Ceremony** to verify and deliver it.

**Currently built:** The pre-flow pipeline (`raw` → `breakdown` → `draft`), the kh CLI, grooming standards, executor standards, closing ceremony protocol, journey mapping infrastructure, and the complete template system. **Not yet built:** The orchestrator (automated multi-session coordination), opening ceremony, simulation ceremony, and the full IMAGINATION/INTENT layers.

## The Methodology: Journey-First Development

Traditional development starts with features and hopes they compose into coherent user experiences. 1KH inverts this: **start with the journey, derive the features.**

A **Journey Mapping (JM)** describes a complete user experience — "new patient books a medical consultation." Each journey contains **User Flows (UFs)** — the discrete, testable paths through that journey. Features are decomposed *from* user flows, not the other way around.

This means every line of code traces back to a journey step, every test verifies a user experience, and nothing gets built that doesn't serve a journey someone actually walks through.

## Execution Sequencing Model

When you have multiple journeys, multiple user flows per journey, multiple build layers, and both happy and sad paths — the question of *what to build first* becomes a real strategic decision. 1KH defines five dimensions of execution sequencing, each following a "complete this before moving to next" rule:

```
DIM 1: PATH       Happy → Critical Escalation → Remaining Escalation
DIM 2: WORK UNIT  JM → UF → Task
DIM 3: STAGE      Local → Mixed → Production
DIM 4: LAYER      DATA → APP → UX-MIN → UX-FIN
DIM 5: SCOPE      Core/Shared → Specialized
```

In practice, this means: build all happy-path user flows for Journey 1 (data layer first, then app, then UI), deliver a working journey, then move to Journey 2. After all happy paths work, circle back for escalation paths. Start local, graduate to cloud when logic is proven.

### Intellectual Lineage

This model isn't new — it's a deliberate synthesis of proven patterns from software engineering history:

**Dimension 1 (Path)** draws from **Risk-Ordered Delivery**, articulated by Alistair Cockburn in the Crystal methods and present in the Unified Process. The principle: build the thing that proves the concept first, then harden it. In Lean Startup terms, ship the MVP before the edge cases. The Agile Manifesto's tenth principle — "maximize the amount of work not done" — is the undercurrent here. You may discover during happy-path execution that some escalation paths aren't needed at all.

**Dimension 2 (Work Unit)** is **Vertical Slicing**, popularized by Jeff Patton in *User Story Mapping* (2014). Each journey mapping is a vertical slice through the entire system that delivers a complete user experience. Patton's key insight: slice by *user outcome*, not by technical layer. A finished JM is a walking skeleton — it works end-to-end, even if the next journey doesn't exist yet.

**Dimension 3 (Stage)** follows the **Deployment Pipeline** pattern from Jez Humble and David Farley's *Continuous Delivery* (2010). The progression through environments with increasing fidelity (local → staging → production) is a core CD principle. It also embodies the **Last Responsible Moment** principle from Lean software development (Mary and Tom Poppendieck, *Lean Software Development*, 2003) — don't introduce cloud complexity until you've proven the logic locally.

**Dimension 4 (Layer)** combines **Bottom-Up Integration** with the **Tracer Bullet** concept from Andy Hunt and Dave Thomas's *The Pragmatic Programmer* (1999). Build the foundation layers first because they're objectively testable, then wire the subjective layers on top. The 1KH "cement settling" metaphor is a restatement of the same idea — let each layer harden before building on it. This also draws from Kent Beck's principle of "make it work, make it right, make it fast" — but applied per-layer rather than per-feature.

**Dimension 5 (Scope)** is **Dependency-Ordered Construction** — topological sorting of shared infrastructure. This is standard practice in build systems (Make, Gradle, Bazel) applied to product development. Build the `patients` table before `prescription_refills` because five user flows depend on the former and one depends on the latter.

**The composite pattern** — all five dimensions operating simultaneously — aligns most closely with what Cockburn called **Incremental Architecture** in *Crystal Clear* (2004), or more precisely, **Walking Skeleton with Incremental Fattening**: build the thinnest possible working version (one happy path, one journey, local, data-through-UI), then fatten it dimension by dimension. Craig Larman and Bas Vodde's *Large-Scale Scrum* (2016) describes a similar "feature team" delivery model where cross-functional teams own vertical slices end-to-end.

The contribution of 1KH is not inventing any of these patterns, but formalizing their *intersection* into a five-dimensional model that can be reasoned about, sequenced, and — critically — automated by AI orchestration.

## Repository Structure

```
thousandhand_v3/
├── bin/
│   ├── kh.sh                              # The CLI (bash)
│   └── fix-codecommit-creds.sh            # AWS CodeCommit credential helper
├── package.json                            # npm package definition (enables `npm link`)
├── docs/
│   └── ARCH_V3.md                          # Primary architecture document
├── protocols/
│   ├── EXECUTOR_STANDARDS.md               # How execution sessions build systems
│   └── CLOSING_CEREMONY.md                 # UAT preparation and delivery protocol
├── templates/
│   ├── MASTER_GROOMING_STANDARDS.md        # Grooming phase standards
│   ├── MASTER_DELIVERY_HANDOFF_TEMPLATE.md # Execution → delivery handoff format
│   ├── ARCHITECTURE_TEMPLATE.md            # Per-project architecture doc template
│   ├── USER_FLOWS_TEMPLATE.md              # User flow catalog template
│   ├── JOURNEY_MAPPINGS_TEMPLATE.md        # Journey mapping catalog template
│   ├── JM_COMPLETENESS_CHECKLIST.md        # 5-layer gap detection for journeys
│   └── JM_PATTERNS.md                      # Reusable journey behavioral patterns
├── defaults/
│   ├── config.json                         # Default project configuration
│   └── state.json                          # Default state structure
├── staging/                                # Documents awaiting their CLI commands
│   ├── OPENING_CEREMONY.md                 # → protocols/ when kh open is built
│   ├── ORCHESTRATOR_STANDARDS.md           # → protocols/ when orchestrator is built
│   └── INTERMEDIATE_ARTIFACTS.md           # → absorbed when layer coordination is built
└── archive/
    └── DESIGN_RAW_BREAKDOWN_DRAFT.md       # Completed design doc (reference only)
```

## How kh init Works

Running `kh init` in any project directory creates a `.kh/` workspace:

```
your-project/
├── .kh/
│   ├── config.json          # Project configuration
│   ├── state.json           # Queue state (drafts, phases, priorities)
│   ├── raw/                 # Brain dumps and breakdown reports
│   ├── draft/               # Discrete items awaiting grooming
│   ├── developing/          # Currently executing items
│   ├── complete/            # Delivered items
│   └── sessions/            # Claude session logs
├── docs/
│   ├── ARCHITECTURE.md      # (from template)
│   ├── USER_FLOWS.md        # (from template)
│   └── JOURNEY_MAPPINGS.md  # (from template, if JMs detected)
└── ... your existing project files
```

Templates are copied from the 1KH source repo. The project's `.kh/` directory is the workspace; the 1KH repo is the source of truth for standards and templates.

## Requirements

- Bash 4+
- Claude Code CLI (`claude`) with API access
- jq (for JSON processing)
- Node.js (for `npm link` installation)

## Installation

```bash
cd thousandhand_v3
npm link
```

This makes `kh` available globally. Run `kh init` in any project directory to get started.

## Status

**Version:** 0.1.0 (active development)

**Working today:** All CLI commands are implemented — `kh init`, `kh raw/list/show`, `kh breakdown`, `kh add`, `kh status`, `kh view`, `kh prioritize`, `kh run`, `kh logs`, `kh watch`, `kh stop`, `kh close`, `kh demote`, `kh promote`, `kh resume`, `kh remove`. The pre-flow pipeline (raw → breakdown → draft) is fully operational with AI-powered classification, grouping, deferred re-evaluation, and catalog updates.

**In progress:** End-to-end Playwright test coverage for the first real project (Man vs Health).

**Planned:** `kh open` (opening ceremony), orchestrator layer (automated multi-session coordination), simulation ceremony, and the full IMAGINATION/INTENT layer automation.

## License

Private. Not yet open-sourced.
