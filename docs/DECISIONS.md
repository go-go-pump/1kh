# ThousandHand Architectural Decisions

This document captures key architectural decisions and their rationale.

---

## DECISION-001: System Types (BIZ vs USER)

**Decision:** Distinguish between BIZ SYSTEM and USER SYSTEM at intake.

**Context:**
- BIZ SYSTEM = maximizing owner satisfaction (revenue, profit, KPIs)
- USER SYSTEM = maximizing user utility/fulfillment
- A USER SYSTEM can exist without a BIZ SYSTEM (open source, hobby)
- A BIZ SYSTEM cannot exist without at least one USER SYSTEM

**Implications:**
- Initial intake must detect which type user is building
- Different KPIs drive different hypothesis generation
- Hypothesis is OPTIONAL for USER SYSTEMS until optimizing for external users
- USER SYSTEM early stage = feature checklist, not hypothesis-driven

**Platform/Infrastructure Clarification:**
- Infrastructure that enables other businesses to operate = USER SYSTEM
- The business being enabled by infrastructure = BIZ SYSTEM
- Example: "bix" (multi-tenant conversation service) = USER SYSTEM
          "Man vs Health" (uses bix to serve customers) = BIZ SYSTEM
- Key question: "Does this project maximize USER UTILITY or OWNER REVENUE?"
- If primary goal is providing utility that others use → USER SYSTEM
- If primary goal is directly generating revenue from end-users → BIZ SYSTEM

**Revisit If:**
- We discover a third system type that doesn't fit
- The distinction causes more confusion than clarity

---

## DECISION-002: Foundation Structure

**Decision:** Foundation consists of three documents: Oracle, North Star, Context.

**Structure:**
- **Oracle** = What you're building (product/service definition)
- **North Star** = Where you're going (measurable goal)
- **Context** = Who you are, who it's for, WHY it matters (includes STORY)

**Implications:**
- STORY lives in Context, not as separate system
- Foundation is NOT a loop - it's the base that loops operate on
- Foundation is sensitive (not sacred) - changes cascade significantly

**Revisit If:**
- We need additional foundation documents
- STORY proves to need its own treatment

---

## DECISION-003: Foundation Change Levels

**Decision:** Four levels of Foundation changes, distinct from Imagination-level changes.

**Foundation Level:**
| Level | Scope | Impact |
|-------|-------|--------|
| TWEAK | Wording/clarification | Absorb silently |
| ADJUST | Narrow scope, shift priority | Re-score hypotheses, prune low-fit |
| PIVOT | New market/product/mechanism | Major pruning, 50%+ may be obsolete |
| RESTART | Fundamentally different vision | New project, archive old |

**Imagination Level:**
| Level | Scope |
|-------|-------|
| AUGMENT | Add capability (fill gaps) |
| OPTIMIZE | Improve existing (weak metrics) |

**Key Decision:** Reserve "PIVOT" for Foundation-level ONLY. Do not use at Imagination level.

**Revisit If:**
- We need finer granularity in change levels
- The PIVOT reservation causes confusion

---

## DECISION-004: Loop Structure

**Decision:** Four Loops with REFLECTION operating across cycles.

**Structure:**
```
FOUNDATION (one-time, unless modified)
    ↓
CYCLE (repeats):
    REFLECTION → IMAGINATION → INTENT → WORK → EXECUTION
    ↓
NORTH STAR (exit condition)
```

**Key Points:**
- REFLECTION analyzes patterns across cycles
- REFLECTION feeds guidance into IMAGINATION
- REFLECTION can trigger Foundation-level review (not change directly)

**Revisit If:**
- We need additional loops
- REFLECTION scope needs to change

---

## DECISION-005: Hypothesis Requirements

**Decision:** Hypotheses need test conditions to be valid.

**Requirements:**
- Every hypothesis must answer: "How will we know if this worked?"
- Example: "Email campaign will drive signups. Test: 100+ signups within 2 weeks."

**Implications:**
- Without test conditions, we're generating tasks, not testable hypotheses
- Test conditions enable proper evaluation in REFLECTION

**Revisit If:**
- Test conditions prove too burdensome for early-stage work
- We need different hypothesis types with different requirements

---

## DECISION-006: Task Breakdown Hierarchy

**Decision:** Three-level hierarchy from Hypothesis to Tasks.

**Hierarchy:**
```
HYPOTHESIS (the bet we're making)
    ↓
WORK ITEMS (what must exist to test the hypothesis)
    ↓
TASKS (specific build instructions: which factory + what artifact)
```

**Implications:**
- Need explicit WORK ITEMS layer in the system
- Tasks are work orders, not just descriptions

**Revisit If:**
- The three-level hierarchy is too complex
- We need additional levels

---

## DECISION-007: Execution Model (BUILD/TEST/OPS)

**Decision:** Three BUILD factories producing artifacts that are ALL in production.

**Factories (General Purpose):**
- `BUILD-UX` → produces UI artifacts (pages, interfaces)
- `BUILD-TEST` → produces test workflows (user emulation, validation)
- `BUILD-OP` → produces operational workflows (business logic)

**Key Points:**
- Factories are cookie cutters (general)
- Artifacts are cookies (specific instantiations)
- TEST and OPS are BOTH production artifacts
- TEST validates OPS (TDD thinking, NOT environment distinction)
- META-BUILD creates new factories (experimental, high failure rate)

**TDD Flow:**
1. Write TEST workflow (emulates user)
2. TEST fails (OPS doesn't exist)
3. Write OPS workflow
4. TEST passes (OPS works)
5. Both deployed to PRODUCTION

**Revisit If:**
- We need additional factory types
- TDD approach proves impractical

---

## DECISION-008: When to Challenge Foundation

**Decision:** REFLECTION tracks stall patterns and triggers Foundation review.

**Triggers:**
- North Star flat for N cycles (default: 10?)
- M different mechanisms tried without movement (default: 3?)
- User explicitly requests review

**REFLECTION Output:**
- "Recommend reviewing Foundation"
- Specific: "North Star X hasn't moved despite Y, Z, W attempts"
- Options: ADJUST scope? PIVOT direction? RESTART?

**Revisit If:**
- Default thresholds prove wrong
- Need more sophisticated detection

---

## DECISION-009: Deployment Model

**Decision:** All deployments are PRODUCTION. No test environment distinction.

**Rationale:**
- TEST workflows validate OPS in production
- Trusting Temporal, Supabase, Lambda/SES for uptime
- Simplifies infrastructure model

**Revisit If:**
- We need environment separation for safety
- Production-only proves too risky

---

## DECISION-010: Deferred Items

**Explicitly Deferred:**

| Item | Deferred To | Reason |
|------|-------------|--------|
| Shared components | Phase 13 | Need proven single-project pattern first |
| Hypothesis conflict resolution | Phase 2+ | May be edge case, need data first |
| Story as separate system | TBD | Currently treating as part of Context |
| Production monitoring | Phase 6+ | Trusting infrastructure providers |

**Revisit When:**
- We hit Phase 2 and have simulation data
- Single-project pattern is proven

---

## DECISION-011: Utility Subtypes and Natural KPIs

**Decision:** For USER SYSTEMS, detect the utility subtype and suggest appropriate KPIs early.

**Context:**
Different utility types naturally gravitate toward different metrics. Detecting this early:
- Helps users think about the right success criteria
- Enables the system to suggest appropriate metrics
- Determines whether hypothesis-driven testing is beneficial

**Utility Subtypes:**

| Subtype | Description | Primary KPI | Hypothesis-Driven? |
|---------|-------------|-------------|-------------------|
| POC | Proof of Concept | "IT JUST WORKS" (binary) | No |
| MULTI_TENANT | Shared Service | Uptime, latency, isolation | Yes |
| ORCHESTRATOR | Service Manager | Config ability, visibility | Yes |
| SCHEDULER | Event-driven | Timing accuracy, throughput | Yes |
| INTERNAL_TOOL | Productivity | Task completion, time saved | No |
| LIBRARY | SDK/API | Time to first call, docs | No |
| DATA_PIPELINE | ETL/Streaming | Throughput, accuracy | Yes |
| AUTOMATION | Workflow | Success rate, MTTR | Yes |

**Key Insight:**
Infrastructure that serves other systems (like bix) is USER SYSTEM with MULTI_TENANT subtype.
Its KPIs are reliability metrics, not adoption or revenue metrics.

**Implementation:**
1. After detecting USER SYSTEM + UTILITY north star, detect utility subtype
2. Present suggested metrics to user
3. If accepted, auto-populate success_metrics in north-star.md
4. User can edit/customize in north-star.md after ceremony

**Revisit If:**
- New utility subtypes emerge that don't fit categories
- Suggested metrics prove unhelpful or misleading

---

## Decision Log

| ID | Date | Decision | Status |
|----|------|----------|--------|
| 001 | Current | BIZ vs USER system types | Active |
| 002 | Current | Foundation structure | Active |
| 003 | Current | Foundation change levels | Active |
| 004 | Current | Loop structure | Active |
| 005 | Current | Hypothesis requirements | Active |
| 006 | Current | Task breakdown hierarchy | Active |
| 007 | Current | Execution model | Active |
| 008 | Current | Challenge Foundation triggers | Active |
| 009 | Current | Deployment model | Active |
| 010 | Current | Deferred items | Active |
| 011 | Current | Utility subtypes and natural KPIs | Active |

---

*Last Updated: Current Session*
