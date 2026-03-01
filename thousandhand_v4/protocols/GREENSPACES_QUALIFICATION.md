# Greenspaces Qualification Standard — First Build Integration

> **Type:** Process Requirements Document
> **Consumed By:** GROOMING phase, EXECUTION phase (first build PUMPs)
> **Purpose:** Defines how to evaluate and integrate Greenspaces shared components/services during a project's initial BUILD (0 → 1)
> **Version:** 1.0
> **Created:** 2026-03-01

---

## 1. Purpose

When a new project is built from scratch (FOUNDATION_FIRST or NEW_PROJECT PUMP type), the grooming/execution pipeline must evaluate which Greenspaces shared components and services should be wired in from day one.

**Why at first build, not later:**
- Shared components often require database schema (e.g., `metric-beacon` needs a metrics table, `auth-otp` needs users/sessions tables)
- Adding schema after initial rollout means migrations, data backfills, and regression risk
- Wiring monitoring, auth, and seeding at build time is 10x cheaper than retrofitting
- The first build is the only time ALL schema changes are coordinated in a single pass

---

## 2. When This Standard Applies

This standard is triggered when:
- PUMP type is `FOUNDATION_FIRST` or `NEW_PROJECT`
- The execution is building a project from scratch (no existing codebase)
- The pipeline is in the DATA layer of the first JM

It does **NOT** apply to:
- HOTFIX, ENHANCEMENT, or REFACTOR PUMPs on existing projects
- Projects that already have an established schema

---

## 3. The Qualification Process

### Step 1: Load the Greenspaces Catalog

Read `greenspaces/CATALOG.md` to get the current list of shared components and services with their statuses.

### Step 2: Score Each Component Against the Project

For every component with status `AVAILABLE` or `CANDIDATE` (with existing extractable code), evaluate:

| Criterion | Question | Weight |
|-----------|----------|--------|
| **Relevance** | Does this project need this capability at all? | GATE (if NO → skip) |
| **First-Build Fit** | Does this component require schema or config that's cheaper to add now than later? | HIGH |
| **Default Inclusion** | Is this component expected in ALL projects? (See Section 4) | HIGH |
| **Prompt Signal** | Did the founder's raw prompt mention or imply this capability? | MEDIUM |
| **Ecosystem Alignment** | Would adding this make the project a better citizen of the ecosystem? | LOW |

### Step 3: Classify Each Component

Based on scoring, classify into:

| Classification | Meaning | Action |
|----------------|---------|--------|
| `INCLUDE` | Required for this project, wire in during first build | Add to pre-launch checklist, include schema in initial migrations |
| `DEFER` | Useful but not needed at first build, no schema dependency | Note in ARCHITECTURE.md as future integration |
| `SKIP` | Not relevant to this project | No action |

### Step 4: Generate Pre-Launch Checklist

Produce a `TMP_PRELAUNCH_CHECKLIST.md` in the project root listing all `INCLUDE` components with:

```markdown
## Greenspaces Integration Checklist

| Component | Status | Schema Required | Integration Notes |
|-----------|--------|-----------------|-------------------|
| metric-beacon | PENDING | Yes — metrics table | Wire into Express middleware |
| metric-snapshot | PENDING | No — reads from beacon | Configure poll interval |
| seed-manager | PENDING | No — uses existing schema | Wire seed scripts |
```

This checklist is consumed during the DATA layer phase and marked `DONE` as each component is wired in.

---

## 4. Default Inclusions

These components are included in **every new project** unless explicitly excluded by the founder:

### Always Include

| Component | Rationale |
|-----------|-----------|
| `metric-beacon` | Every system must expose metrics. This is the 1KH monitoring standard. Wire at build time = free. Wire later = migration + retrofit. |
| `metric-snapshot` | Paired with metric-beacon. Enables monitoring dashboard consumption. No schema of its own but requires beacon to be present. |
| `seed-manager` | Every project needs seed data (per Executor Standards §4). Standardized seeding prevents per-project reinvention. |

### Include When Web-Facing

| Component | Trigger |
|-----------|---------|
| `auth-otp` | Project has user authentication of any kind |
| `e2e-test-runner` | Project has a browser-facing UI (all web projects) |

### Include When Applicable

| Component | Trigger |
|-----------|---------|
| `email-send` | Project sends any emails |
| `vidgen-pipeline` | Project generates or publishes video content |
| `vidpub` | Project publishes to YouTube |
| `llm-tagger` | Project classifies or categorizes content via LLM |
| `browser-watcher` | Project needs browser automation (scraping, testing external sites) |

---

## 5. Schema Coordination

The critical insight: **Greenspaces components that require schema must have their schema created alongside the project's own schema during the DATA layer.**

### Process

1. During DATA layer execution, the executor creates migrations in this order:
   - **Core project schema** — The project's own tables
   - **Greenspaces schema** — Tables required by included shared components
   - **Bridge schema** — Any junction tables or foreign keys connecting project tables to Greenspaces tables

2. All migrations follow the idempotency standard from Executor Standards §4 (Migration Idempotency)

3. Seed data for Greenspaces components is included in the project's seed script (via `seed-manager` if included)

### Schema Ownership

| Schema Owner | Examples |
|-------------|----------|
| **Project** | campaigns, listings, products — tables unique to this project |
| **Greenspaces** | metrics, otp_sessions, seed_manifests — tables defined by the shared component's contract |
| **Bridge** | project_metrics (FK to both) — created by the project to connect its domain to the shared component |

Greenspaces component schemas are defined in each component's interface contract (`shared-components/<name>/schema.sql`). The executor copies or references these during migration creation. If the component is `CANDIDATE` (not yet extracted), the executor creates the schema based on the component's documented interface and flags it for future alignment when the component is formally extracted.

---

## 6. Integration with PUMP Pipeline

### During Supercharging (god-mode pipeline)

The supercharger should append a `GREENSPACES QUALIFICATION` section to the supercharged prompt for `FOUNDATION_FIRST` and `NEW_PROJECT` types:

```
GREENSPACES QUALIFICATION
─────────────────────────
Default inclusions: metric-beacon, metric-snapshot, seed-manager
Evaluate from catalog: [list components with AVAILABLE/CANDIDATE status]
Output: TMP_PRELAUNCH_CHECKLIST.md with INCLUDE/DEFER/SKIP classifications
```

### During Grooming

The grooming phase references this standard and includes Greenspaces integration tasks in the grooming handoff. Each `INCLUDE` component gets:
- A task for schema creation (in DATA layer)
- A task for integration wiring (in APP layer)
- Test coverage requirements (per Executor Standards §4)

### During Execution

The executor:
1. Reads `TMP_PRELAUNCH_CHECKLIST.md` before starting DATA layer
2. Creates all Greenspaces schema alongside project schema
3. Wires integrations during APP layer
4. Marks checklist items `DONE`
5. Documents integrations in ARCHITECTURE.md delivery section

---

## 7. Relationship to Other Documents

| Document | Relationship |
|----------|-------------|
| **Greenspaces CATALOG.md** | Source of truth for available components. This standard defines WHEN and HOW to evaluate them. |
| **Executor Standards** | Defines build order (§5), TDD (§4), migration idempotency (§4). This standard adds the Greenspaces evaluation step to the DATA layer. |
| **Grooming Standards** | Grooming produces the handoff that includes Greenspaces integration tasks identified by this standard. |
| **PUMP.md (god-mode)** | Supercharging pipeline adds Greenspaces qualification section for first-build PUMPs. |
| **ARCHITECTURE_TEMPLATE.md** | Project ARCHITECTURE.md documents which Greenspaces components are integrated and their status. |

---

## 8. Future Evolution

As more components reach `AVAILABLE` status:
- The "Always Include" list may grow (e.g., `deploy-script` once standardized)
- Component interface contracts will include migration files that can be directly imported
- The qualification process may become automated (CLI: `pump qualify-greenspaces --project <name>`)
- Printify, Stripe, and other integrations will follow the same pattern

---

**The goal: every new project starts with the ecosystem's best practices baked in, not bolted on.**
