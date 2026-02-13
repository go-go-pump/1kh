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
