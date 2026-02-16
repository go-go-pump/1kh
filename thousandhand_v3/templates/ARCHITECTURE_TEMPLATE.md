# Architecture — [PROJECT_NAME]

> Stateful anchor document. Every session reads this first, updates it last. Mitigates context drift across sessions and compactions.

---

## Project Overview

**Name:** [Project name]
**Purpose:** [One sentence — what does this system do for its users?]
**Phase:** [Current development phase]
**Stack:** [Primary technologies — e.g., Node.js, SQLite, vanilla HTML/CSS/JS]

---

## System Components

<!-- List each major component of the system with its current status -->

| Component | Status | Description |
|-----------|--------|-------------|
| _Example: Auth_ | _Not started_ | _User authentication and session management_ |
| _Example: Product catalog_ | _In progress_ | _Browse and search products_ |

---

## Feature Delivery Log

<!-- Updated at the END of every feature. Links to delivery handoff docs. -->

| Feature | Delivered | Delivery Doc | Notes |
|---------|-----------|-------------|-------|
| _Example: User intake flow_ | _2026-02-10_ | _DELIVERY_USER_INTAKE.md_ | _8/8 tests passing_ |

---

## Data Model

<!-- High-level schema overview. Updated when new tables/models are added. -->

_No data model yet._

---

## Key Decisions

<!-- Record architectural decisions with rationale. Future sessions reference these. -->

| # | Decision | Rationale | Date |
|---|----------|-----------|------|
| 1 | _Example: SQLite over PostgreSQL_ | _Local-first development, zero config, sufficient for MVP_ | _2026-02-10_ |

---

## Architectural Standards

<!-- Opinionated patterns learned from prior projects. Apply these by default on new projects.
     Override with rationale in Key Decisions if a project requires a different approach. -->

### Data Access Layer

**Standard: Always implement an API proxy between the frontend and database.**

Even when using a BaaS like Supabase that provides a client SDK for direct browser-to-database
queries, introduce a thin API layer (e.g., Express/Fastify server) between the frontend and
the database. This provides:

- **Environment swappability:** Point LOCAL at SQLite or a mock DB, MIXED at a test instance,
  PROD at production — without changing frontend code.
- **RLS decoupling:** Handle authorization in application code rather than relying entirely on
  database-level RLS policies. RLS is a defense-in-depth layer, not the primary access control.
- **Testability:** Mock the API layer for fast, offline tests instead of requiring a live database.
- **Migration path:** If you outgrow or change your BaaS, only the proxy layer changes — not
  every frontend file.

Without this layer, the frontend becomes tightly coupled to the database provider. Swapping
environments, running offline tests, or migrating providers becomes a full-codebase refactor.

### RLS Policy Management

**Standard: RLS policies are code, not dashboard clicks.**

- Define all RLS policies in migration files, never in the Supabase dashboard directly.
- Every table touched by a task must have its RLS policies reviewed and tested.
- Include RLS policy verification as part of the executor's delivery checklist.
- Test RLS behavior explicitly: seed data for User A, attempt access as User B, assert denial.
- Common failure mode: policies that block service-role operations, policies that allow
  unintended cross-user reads, policies missing on new tables.

### Test Environment Strategy

**Standard: Separate test and production data at the instance level, not just by convention.**

- Maintain a dedicated test environment (separate database instance, project, or container).
- Never rely solely on "test client IDs" in a shared production database for test isolation.
- Seed scripts create known-state data; reset scripts remove it completely.
- External services should use sandbox/test modes where available. Where no sandbox exists
  (e.g., LabCorp), document the safety constraints that make production use acceptable.

### Preferred Stage Architecture

**Standard: Three stages — DEV, INTEGRATION, PRODUCTION — with clear purpose separation.**

> The Executor Standards define LOCAL, MIXED, PRODUCTION contexts for build-time behavior.
> This section defines the **preferred naming and infrastructure** for production-grade projects.
> Projects SHOULD adopt DEV/INTEGRATION/PRODUCTION naming to communicate stage intent clearly.

| Concern | DEV | INTEGRATION | PRODUCTION |
|---------|-----|-------------|------------|
| **Database** | SQLite (via API proxy) | Cloud DB (e.g., Supabase, Aurora) | Production DB (Aurora, RDS, etc.) |
| **File storage** | Local filesystem (`./test_fixtures/s3/`) | Cloud storage (real bucket, test prefix) | Cloud storage (prod bucket) |
| **Functions** | SAM local / mock | Deployed (test data) | Deployed (prod) |
| **Auth** | Mock (bypass token, hardcoded test users) | Real auth provider | Real auth |
| **Messaging** | Write to local file | Sandbox (SES sandbox, Twilio test) | Production (SES, Twilio) |
| **Payments** | Mock (fixture responses) | Sandbox (Square sandbox, Stripe test) | Production |
| **UX hosting** | localhost | localhost | CDN / S3+CloudFront |
| **Workflows** | Skip — seed state directly | Temporal/Step Functions (test namespace) | Temporal/Step Functions (prod namespace) |

**Key principle: DEV is fast + isolated, INTEGRATION proves real services, PRODUCTION is live.**

- **DEV**: Zero external dependencies. Build and validate features offline. SQLite requires the
  API proxy layer (see Data Access Layer standard). Full UX implementation against mock data.
  Unit tests and Playwright e2e tests run here. Fastest feedback loop.
- **INTEGRATION**: Real cloud services with test data. Validates that real infrastructure behaves
  the same as mocks. UAT happens here. Testing dashboard seeds to any journey step.
- **PRODUCTION**: Everything real. Test data clearly identifiable and removable.

**Mapping to Executor Standards contexts:**
- DEV = LOCAL context (Executor Standards Section 2.1)
- INTEGRATION = MIXED context (Executor Standards Section 2.2)
- PRODUCTION = PRODUCTION context (Executor Standards Section 2.3)

**Infrastructure progression:**
```
DEV (build fast)  →  INTEGRATION (prove it works)  →  PRODUCTION (ship it)
SQLite + mocks        Real DB + sandboxes               Real everything
Fast, offline         Real services, localhost           Live deployment
```

### Preferred Tech Stack (Production-Grade)

**Standard: API proxy + managed PostgreSQL + serverless functions + CDN.**

This is the recommended production architecture for projects that outgrow BaaS providers
(Supabase, Firebase, etc.) or that need full infrastructure control from the start.

| Layer | Technology | Why |
|-------|-----------|-----|
| **Database** | Aurora PostgreSQL (AWS) | Managed, scalable, no vendor lock-in, full SQL |
| **API Proxy** | Express/Fastify (Node.js) | Environment-swappable backend, auth middleware, caching |
| **Functions** | AWS Lambda (via SAM) | Full language support, VPC access, longer timeouts |
| **File Storage** | S3 | Standard, cheap, pre-signed URLs |
| **Auth** | Custom (bearer token + validator) | Simple, portable, no vendor dependency |
| **Email** | SES | Cost-effective, AWS-native |
| **SMS** | Twilio | Best delivery, A2P compliance |
| **Frontend** | Vanilla HTML/CSS/JS or lightweight framework | No build step for MVP, S3+CloudFront for hosting |
| **Workflows** | Temporal | Long-running orchestration, complex state machines, escalation paths |
| **CDN** | CloudFront | AWS-native, S3 origin |

**When to use this stack:** When starting a new project, or when migrating away from a BaaS
after proving the product. The API proxy is the keystone — it enables environment switching
(DEV → INTEGRATION → PRODUCTION) without changing frontend code.

**Acceptable BaaS starting point:** Supabase or Firebase are fine for early development
(INTEGRATION-first strategy). When you hit these triggers, migrate to the preferred stack:
- Outage sensitivity (free/shared tier instability)
- RLS policy complexity exceeding application logic
- Need for offline development (DEV stage)
- Edge function limitations vs Lambda capabilities
- Vendor lock-in concern for core data

### Journey Testing Dashboard Pattern

**Standard: Every project with Journey Mappings should implement a testing dashboard.**

The testing dashboard is a browser-based tool for seeding, inspecting, and advancing
journey state during UAT. It provides visibility into the database state at each journey
step without requiring CLI access or direct SQL queries.

**Core capabilities:**
- Stage selector (switch between INTEGRATION and PRODUCTION views)
- Step-by-step journey visualization with current state detection
- Per-step seed/advance buttons (seeds or advances DB to that step's expected state)
- Real-time state checks (queries DB and compares to expected values per step)
- Direct links to relevant portal and admin pages per step
- Activity log for seed/reset operations
- Reset button (cleans all test data by known test IDs)

**Implementation pattern:**
```
sites/testing/dashboard/
├── index.html          ← Dashboard UI (step cards, state grid, log panel)
└── dashboard.js        ← Config (stages, test IDs, step definitions, seed functions)
```

**Step definition structure:**
```javascript
{
  num: 1,
  title: 'Step Name',
  subtitle: 'What happens at this step',
  stateChecks: [
    { table: 'table_name', id: 'testIdKey', field: 'status', expect: 'value', label: 'Display Label' },
  ],
  portalPage: '/portal/page.html?param=value',
  adminPage: '/admin/page.html?param=value',
  canSeed: true,
  seedLabel: 'Seed/Advance to Step N',
}
```

**Test data isolation:** All test IDs should use a recognizable prefix pattern
(e.g., `a0e2e001-*`) so test data is trivially identifiable and bulk-deletable.

**UAT workflow:** Seed Step 1 → verify in dashboard → click "Open as Client" → manually
test portal → click "Open as Admin" → manually test admin → advance to Step 2 → repeat.
Playwright e2e tests can also run against dashboard-seeded state.

---

## Current State

<!-- Brief summary of where the project stands RIGHT NOW. Updated at start and end of each session. -->

_Project initialized. No features delivered yet._

---

## Next Up

<!-- What should the next session focus on? Updated at end of each session. -->

_See task queue (`kh status`) for current priorities._

---

*Per EXECUTOR_STANDARDS Section 6: this document is read at the START and updated at the END of every feature session.*
*Per EXECUTOR_STANDARDS Section 7: when a task delivers a [PLANNED] flow or journey, update the catalog docs (USER_FLOWS.md, JOURNEY_MAPPINGS.md) from [PLANNED] → [IMPLEMENTED].*
