# ThousandHand v3 — REFLECTION

> This document reflects on v2, distills what we learned, and sets the stage for v3.
> Written at the transition point between architecture and execution.

---

## 1. What ThousandHand Is

ThousandHand (1KH) is an **autonomous business-building system** powered by Claude AI. You give it your values and objectives. It imagines paths forward, estimates feasibility, builds what's needed, measures what happens, and learns from results. It asks for help when stuck and never violates your values.

It is not a chatbot, not a simple automation tool, and not a replacement for human judgment. It is a **cultivator** — you plant the roots and tend the soil; it grows the tree.

---

## 2. The Tree Analogy

The system's state and purpose map to a living tree:

```
                    ☀️  ENVIRONMENT
                 (market, timing, luck)
                 You cannot control this.
                         │
                         ▼
                    🍎  FRUIT
           (outcomes: revenue, leads, metrics)
           You observe this. You don't command it.
                         ▲
                         │
                    🌿  BRANCHES
              (workflows, integrations, apps)
              You build these. They may or may not bear fruit.
                         ▲
                         │
                  🍃  LEAVES
           (test workflows — health indicators)
           They tell you if a branch is alive.
                         ▲
                         │
                    🪵  TRUNK
               (ThousandHand core: the loops)
               The foundation everything grows from.
                         ▲
                         │
                    🌱  ROOTS
              (Oracle + North Star)
              Invisible but essential — values and objectives.
                         ▲
                         │
                    🌍  SOIL
           (resources: budget, time, skills, constraints)
```

**The key insight**: You cultivate, you don't command. You control roots (values) and soil (resources). You influence branches (what gets built). You observe fruit (outcomes). You cannot control the environment (market).

---

## 3. What 1KH Creates

ThousandHand creates **systems** — both business systems and the user systems they require:

```
1 BIZ SYSTEM  ──── requires ───→  1 or many USER SYSTEMS
                                        or
                                  many BIZ SYSTEMS (platform)

1 USER SYSTEM ──── provides ───→  1 functional feature
                                        or
                                  many composable user systems
```

**BIZ SYSTEM** = maximizes owner satisfaction (revenue, profit, customer KPIs). Requires four components for revenue: Product, Payment, Channel, Fulfillment.

**USER SYSTEM** = maximizes user utility (uptime, latency, feature completeness). Has 20 utility subtypes across 6 categories (infrastructure, data, compute, developer, content, general) — each with natural KPIs.

A USER SYSTEM can exist without a BIZ SYSTEM (open source, hobby projects). A BIZ SYSTEM cannot exist without at least one USER SYSTEM. Infrastructure that *enables* other businesses (like a multi-tenant platform) is classified as a USER SYSTEM.

---

## 4. The Five Loops (v2 Architecture)

Every cycle in v2 runs through five coordinated loops:

```
REFLECTION → IMAGINATION → INTENT → WORK → EXECUTION
     ↑                                         │
     └──────────── cycle repeats ──────────────┘
```

| Loop | Purpose | Key Output |
|------|---------|------------|
| **REFLECTION** | Trajectory analysis across cycles | AUGMENT / OPTIMIZE / PIVOT / CONTINUE |
| **IMAGINATION** | Generate and score hypotheses | Ranked hypotheses with viability scores |
| **INTENT** | Observe tree state, make strategic decisions | Nurture / pivot / prune decisions |
| **WORK** | Decompose decisions into actionable tasks | Task queue with dependencies |
| **EXECUTION** | Execute tasks, create artifacts | Deployed workflows, updated metrics |

Each hypothesis needs a **test condition** ("How will we know if this worked?"). Task hierarchy is three levels: HYPOTHESIS → WORK ITEMS → TASKS. Three build factories exist: BUILD-UX, BUILD-TEST, BUILD-OP — all producing production artifacts. No test environments; TEST workflows validate OPS workflows *in* production (TDD thinking).

---

## 5. Where We Are: Simulation vs. Execution

### What v2 Achieved (~80-85% of Phase 1)

**Hardened (cement dry):**
- Five-loop orchestration engine
- BIZ vs USER system distinction with detection
- Foundation document structure (Oracle, North Star, Context, Seeds, Preferences)
- Demo mode with mock scenarios (AUGMENT, OPTIMIZE, PIVOT, vendor-choice)
- Cycle persistence and resume
- 20 utility subtypes with natural KPIs
- OPERATE phase with SLA monitoring
- System lifecycle model (BUILD → LAUNCH → OPERATE → OPTIMIZE)
- Phase callbacks and loading indicators

**Still setting (cement wet):**
- Foundation intake flow (value surfacing, North Star confirmation)
- Hypothesis test conditions (defined but not wired)
- WORK ITEMS layer between HYPOTHESIS and TASKS
- REFLECTION triggers for Foundation challenges
- STORY integration into Context

**Not yet poured:**
- Actual hypothesis generation prompts
- Task breakdown logic
- Temporal integration
- Real execution (BUILD/TEST/OPS workflows)
- META-BUILD (factory of factories)
- Shared components / multi-project

### The Gap: Simulation → Execution

v2 can **simulate** cycles: forecast outcomes, explore hypotheses, run mock cycles. It has three execution modes (demo, local, default/production). But it has **no real execution pathway** — no mechanism to take a TASK and turn it into actual working code, tests, and deployed artifacts.

This is the gap v3 fills. And this is where **Kanban Utility (KU)** enters the picture.

---

## 6. Roadmap Position

v2's roadmap defined 13 phases. We completed roughly 80-85% of Phase 1. Phases 2-9 were simulation and integration stages. Phases 10-13 were real-world execution.

**The v3 realization**: We don't need to crawl through 13 phases sequentially. We now have a **proven execution engine** (KU) that can be integrated directly. The roadmap collapses:

| v2 Phases | v3 Equivalent |
|-----------|--------------|
| Phase 1 (Pre-Execution Dev) | ✅ Done — archived as v2 |
| Phases 2-9 (Simulation + Integration) | Partially absorbed — v3 layers handle this naturally |
| Phases 10-13 (Real World + Shared) | v3 GROOMING + EXECUTION — powered by KU patterns |

---

## 7. Key Decisions Carried Forward to v3

From the 12 architectural decisions documented in v2:

| Decision | Status in v3 |
|----------|-------------|
| BIZ vs USER system types | **Carried forward** — foundational distinction |
| Foundation structure (Oracle, North Star, Context) | **Carried forward** — unchanged |
| Foundation change levels (TWEAK/ADJUST/PIVOT/RESTART) | **Carried forward** — unchanged |
| Loop structure (5 loops with REFLECTION) | **Evolved** — v3 adds explicit feedback loops between layers |
| Hypothesis test conditions | **Carried forward** — still required |
| Task hierarchy (3 levels) | **Evolved** — GROOMING now hydrates TASKS into HANDOFFS |
| Execution model (3 factories) | **Evolved** — BUILD WORKFLOW replaces factory concept |
| Foundation challenge triggers | **Carried forward** — REFLECTION still triggers |
| All-production deployment | **Carried forward** — no test environments |
| Deferred: shared components | **Still deferred** — but now closer with KU patterns |
| Utility subtypes | **Carried forward** — 20 types, natural KPIs |
| OPERATE phase | **Carried forward** — operations.md, SLA monitoring |

---

## 8. What KU Teaches Us

Kanban Utility v0.2 is a production-solid utility (1,279 lines of bash orchestration) that demonstrates **stateful task execution through Claude Code**. Its state machine:

```
DRAFT → GROOMING (Sonnet) → READY → DEVELOPING (Opus) → DELIVERED → UPDATING (Sonnet) → COMPLETE
```

**Key patterns proven by KU:**

1. **Filesystem as queue** — directories as state, file movement as transition
2. **Handoff documents as context hydration** — REQ_HANDOFF and DELIVERY_HANDOFF solve the stateless-session problem
3. **Model selection by phase** — Sonnet for triage/docs, Opus for implementation
4. **Triage classification** — FEATURE/MAJOR_FIX/SMALL_FIX/DOCUMENTATION controls scope
5. **Tool restrictions by phase** — least privilege (no Bash in grooming)
6. **Aggressive execution philosophy** — "pick pragmatic, move along, document assumptions"
7. **Completion signaling** — simple `COMPLETE:` convention parsed by coordinator
8. **Priority-based selection** — consistent ordering even as queue grows

**The critical insight**: KU's GROOMING → EXECUTION → UPDATE cycle is *exactly* what 1KH v2 was missing. It bridges the gap between abstract TASKS (from the WORK loop) and concrete implementation.

---

## 9. What v3 Must Be

v3 is not a rewrite. It is an **evolution** that:

1. **Preserves** the philosophical and architectural foundation of v2 (tree analogy, five loops, foundation documents, BIZ/USER distinction)
2. **Integrates** KU's proven execution patterns (grooming, handoffs, stateful sessions, model selection)
3. **Adds** explicit feedback loops between every layer (not just forward flow)
4. **Introduces** GROOMING as a first-class component (task hydration, workflow assignment, escalation)
5. **Defines** BUILD WORKFLOWS and META BUILD WORKFLOWS as the concrete execution mechanism
6. **Establishes** shared capabilities as a natural byproduct of build workflows

The result: a system that goes from "I have an objective" to "Here is working, tested, deployed code" — autonomously, with human oversight at escalation points.

---

*This reflection was written at the v2→v3 transition. It is a living document — update it as v3 evolves.*
*See: `/archive/thousandhand_v2/` for the complete v2 codebase and documentation.*
*See: `/kanban-utility/` for the KU v0.2 implementation that informs v3 execution.*

---

*Last Updated: 2026-02-07*
