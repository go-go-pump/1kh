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

**Standard: RLS policies are code, not dashboard clicks. Authorization lives in the API layer.**

With Cognito + API proxy (Lambda), the primary access control is in application code
(JWT validation, role checks, query scoping). RLS is a defense-in-depth layer on the database.

- Define all RLS policies in migration files, never in a database dashboard directly.
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
| **Orchestration** | docker-compose (Postgres, Redis, Node app) | SST v3 (`sst dev` — Live Lambda) | SST v3 (`sst deploy --stage prod`) |
| **Database** | Postgres container (via docker-compose) | Aurora Serverless v2 (test stage) | Aurora Serverless v2 (prod stage) |
| **File storage** | Local filesystem (`./test_fixtures/s3/`) | S3 (real bucket, test prefix) | S3 (prod bucket) |
| **Functions** | Node.js local (or `sst dev`) | Lambda via SST v3 (test data) | Lambda via SST v3 (prod) |
| **Auth** | Mock (bypass token, hardcoded test users) | Cognito (test user pool) | Cognito (prod user pool) |
| **Messaging** | Write to local file | Sandbox (SES sandbox, Twilio test) | Production (SES, Twilio) |
| **Payments** | Mock (fixture responses) | Sandbox (Square sandbox, Stripe test) | Production |
| **UX hosting** | localhost | localhost | CloudFront + S3 |
| **Queues/Events** | In-process / mock | SQS + EventBridge (test) | SQS + EventBridge (prod) |
| **Secrets** | `.env` file | SSM Parameter Store (test) | SSM Parameter Store (prod) |
| **Workflows** | Skip — seed state directly | Temporal/Step Functions (test namespace) | Temporal/Step Functions (prod namespace) |

**Key principle: DEV is fast + isolated, INTEGRATION proves real services, PRODUCTION is live.**

- **DEV**: Zero external dependencies. `docker-compose up` starts Postgres, Redis, and the Node
  app locally. Full UX implementation against local data. API proxy routes to local Postgres.
  Unit tests and Playwright e2e tests run here. Fastest feedback loop.
- **INTEGRATION**: Real AWS services with test data via `sst dev` (Live Lambda Development).
  Aurora Serverless v2 test stage, Cognito test user pool, S3 test buckets. Validates that real
  infrastructure behaves the same as local dev. UAT happens here. Testing dashboard seeds to
  any journey step.
- **PRODUCTION**: Everything real via `sst deploy --stage prod`. Test data clearly identifiable
  and removable.

**Mapping to Executor Standards contexts:**
- DEV = LOCAL context (Executor Standards Section 2.1)
- INTEGRATION = MIXED context (Executor Standards Section 2.2)
- PRODUCTION = PRODUCTION context (Executor Standards Section 2.3)

**Infrastructure progression:**
```
DEV (build fast)           →  INTEGRATION (prove it works)     →  PRODUCTION (ship it)
docker-compose + local PG      Aurora + Cognito via sst dev        sst deploy --stage prod
Fast, offline                  Real services, localhost             Live deployment
```

**Deployment workflow:**
```
docker-compose up  →  Claude Code builds features  →  sst dev (test against real AWS)  →  sst deploy --stage prod
```

### Preferred Tech Stack — The Founder's Playbook (Production-Grade)

**Standard: Full AWS-native stack via SST v3 + Aurora Serverless v2 + Cognito + CDN.**

This is the recommended production architecture. For projects with compliance requirements
(EHR, HIPAA, SOC2, etc.), use this stack from day one — do not start with a BaaS.

| Layer | Technology | Why |
|-------|-----------|-----|
| **Local Dev** | docker-compose (Postgres, Redis, Node app) | Zero cloud dependency, instant reset, full offline dev |
| **Database** | Aurora Serverless v2 (PostgreSQL) | Scales to zero, pay-per-use, managed, no vendor lock-in, full SQL |
| **Data Access** | Raw SQL via `pg` client (no ORM) | Full control, no abstraction leaks, query-level optimization |
| **API + Functions** | Lambda + API Gateway via **SST v3 (Ion)** | Live Lambda Dev, instant deploys, IaC in TypeScript |
| **Auth** | AWS Cognito | Managed auth, MFA/OTP built-in, JWT native, HIPAA-eligible |
| **File Storage** | S3 | Standard, cheap, pre-signed URLs |
| **Email** | SES | Cost-effective, AWS-native |
| **SMS** | Twilio | Best delivery, A2P compliance |
| **Queues/Events** | SQS + EventBridge | Decoupled async processing, cron jobs via EventBridge+Lambda |
| **Secrets** | SSM Parameter Store | Free, encrypted, Lambda-native access |
| **Frontend** | Vanilla HTML/CSS/JS or lightweight framework | No build step for MVP |
| **CDN/Hosting** | CloudFront + S3 | AWS-native, S3 origin, edge caching |
| **Monitoring** | CloudWatch | Unified logs, metrics, alarms, dashboards |
| **Workflows** | Temporal | Long-running orchestration, complex state machines, escalation paths |

**Why SST v3 (Ion):** SST replaces SAM/CDK/Serverless Framework as the deployment layer.
It provides Live Lambda Development (`sst dev`) for instant feedback during INTEGRATION,
infrastructure-as-code in TypeScript (not YAML), and single-command deployment to any stage.
All AWS resources (Aurora, Cognito, S3, SQS, etc.) are defined as SST constructs.

**When to use this stack:** Any new project, especially those with compliance or data
sovereignty requirements. The API proxy (Lambda behind API Gateway) is the keystone — it
enables environment switching (DEV → INTEGRATION → PRODUCTION) without changing frontend code.

**BaaS exception:** Supabase or Firebase are acceptable ONLY for non-regulated prototypes
or throwaway MVPs where speed-to-first-demo matters more than infrastructure control.
For anything touching health data, financial data, or user PII at scale, start with the
preferred stack. The migration tax from BaaS to AWS-native is real and grows with time.

**The workflow:**
```
docker-compose up → Claude Code + Cursor IDE build features → sst dev (live test) → sst deploy --stage prod
```

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
