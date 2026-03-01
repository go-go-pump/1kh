# Closing Ceremony — UAT Preparation & Delivery

> **Type:** Process Requirements Document (Generic)
> **Consumed By:** Executor (KU session, Claude Code, or human developer)
> **Produces:** UAT Delivery Package for System Owner
> **Version:** 1.0
> **Created:** 2026-02-08

---

## 1. Purpose

A **Closing Ceremony** is the final phase of a delivery block — the moment between "the executor says it's done" and "the system owner believes it's done." The executor has completed a set of tasks (development, testing, migrations, configuration) and now must prepare the system owner to verify that what was built matches what was requested.

This document defines **WHAT** the executor must produce during a Closing Ceremony and **WHY** each artifact matters. It does not prescribe implementation steps — the executor determines HOW based on the project's architecture, tech stack, and testing infrastructure.

### When to Invoke

Invoke a Closing Ceremony when ALL of these are true:

- A defined block of work has been executed (one feature, a sprint, a phase)
- The system owner has NOT yet verified the delivered work firsthand
- The work includes user-facing behavior that can be demonstrated
- There exists (or can exist) test data to support demonstration

### What It Is Not

- Not a go-live checklist (see: **Go-Live Ceremony** — a separate document for production readiness)
- Not a code review (the executor already verified implementation during development)
- Not a regression test suite (existing tests continue to run independently)
- Not a sign-off gate — the system owner decides whether to accept, not this document

---

## 2. Environment Assumptions

### Primary Target: Local Development

The Closing Ceremony is designed for **local-first verification**. The system owner should be able to run all demonstrations on their own machine without depending on external services being in a specific state.

This means:

- **Mocked integrations are acceptable.** If production uses Twilio SMS, the ceremony can demonstrate via mock email to S3 or console log. Coverage over channel fidelity.
- **Seeded data over live data.** Test users, test purchases, test products — all controlled, all reproducible, all resettable.
- **Local server over deployed server.** `localhost:8080` (or equivalent) is the demonstration surface.

### Mixed Environment Support

Some projects will be in a mixed state — some services mocked locally, others hitting real APIs (sandbox or production). The Closing Ceremony accommodates this:

- The **Flow Catalog** (Section 4) marks each flow step with its environment: `LOCAL`, `SANDBOX`, `PRODUCTION`, or `MOCKED`
- The **UAT Guide** (Section 9) includes environment prerequisites so the system owner knows what must be running
- The **Seed Script** (Section 5) handles mixed-environment data seeding (e.g., Supabase cloud DB + local file system)

---

## 3. Discovery Phase

Before producing any artifacts, the executor must understand the delivered system. This phase is research — no files are created yet.

### 3.1 Read the Architecture Document

Every project governed by 1KH maintains a single `ARCHITECTURE.md` (or equivalent) as source of truth. The executor reads it to extract:

**User Types** — Every distinct human role that interacts with the system.

Examples: Client, Admin, Physician, Support Agent, Anonymous Visitor. Each user type has different permissions, different interfaces, and different flows. The executor must identify ALL user types, not just the obvious ones.

**User Lifecycle States** — Within each user type, distinguish between lifecycle stages. The same user type behaves differently depending on where they are in the system's lifecycle:

- **New User** — Has no account. First encounter with the system. Flows start with discovery, registration, onboarding, and first-time actions (intake, first purchase, account creation). New user flows test the system's ability to acquire and onboard.
- **Existing User** — Has an account and history. Flows start with authentication and resume from a known state (return visit, second purchase, checking status of something already in progress). Existing user flows test the system's ability to retain and serve.
- **Returning User (interrupted)** — Started a flow previously but didn't finish. Flows test resume/recovery (e.g., abandoned intake, incomplete payment, expired session). These are distinct from "existing user" because they test state persistence and re-entry.

The Flow Catalog (Section 4) must include flows for BOTH new and existing users. A feature is not fully demonstrated until the system owner has seen it from first contact AND from return visit. The seed script (Section 5) must create test users at each lifecycle stage.

**Interfaces** — Every surface the system exposes to users.

Examples: Marketing site, Client portal, Admin dashboard, Email notifications, SMS notifications. Map which user types access which interfaces. An interface may serve multiple user types (e.g., both Clients and Admins use the portal, but see different things).

**Feature Flows** — The end-to-end journeys that user types take across interfaces.

A feature flow is NOT a single page or a single API call. It is the complete path from trigger to outcome, potentially spanning multiple interfaces and involving background processes. Example: "Client purchases a medical consult" starts on Marketing (intake), moves to Payment, triggers Temporal workflows, creates records visible on the Client portal AND the Admin dashboard, and may generate email notifications.

### 3.2 Inventory Existing Tests

The executor reviews what testing already exists:

- **E2E tests** (Playwright, Cypress, etc.) — What flows are covered? What's the pass rate?
- **Workflow tests** (Temporal, background jobs) — What operational flows are verified?
- **Integration tests** — What external service interactions are tested?
- **Seed data** — What test fixtures, demo data, or factory functions already exist?

This inventory prevents duplication. The Closing Ceremony creates NEW tests in an isolated directory, but it should leverage existing test utilities, fixtures, and patterns.

### 3.3 Identify Delivered Work

Cross-reference the task block (the work that triggered this ceremony) against the architecture document. For each delivered feature:

- What user types does it affect?
- What interfaces does it touch?
- What is the happy path?
- What are the critical sad paths?
- What data must exist for it to be demonstrable?

---

## 4. Flow Catalog

The executor produces a **Flow Catalog** — a structured inventory of every demonstrable user flow. This is the backbone of the Closing Ceremony.

### Structure

Each flow entry contains:

```
FLOW: [Name]
  TYPE: [HAPPY | SAD | ESCALATION]
  RISK: [CRITICAL | HIGH | MEDIUM | LOW]
  USER_TYPE: [Who initiates]
  INTERFACES: [Which surfaces are touched, in order]
  PRECONDITIONS: [What data/state must exist before the flow starts]
  STEPS:
    1. [Interface] — [Action] — [Expected Result] — [ENV: LOCAL|SANDBOX|PRODUCTION|MOCKED]
    2. ...
  POSTCONDITIONS: [What data/state should exist after the flow completes]
  EXISTING_COVERAGE: [Reference to existing tests that partially cover this flow, or "None"]
```

### Coverage Triage

Not every flow needs a test. The executor triages based on:

**CRITICAL** — Flows that represent the project's core value proposition. If these fail, the project has not delivered. All CRITICAL flows get both a Playwright test AND a manual UAT walkthrough.

**HIGH** — Flows that are important but have workarounds if they fail. These get Playwright tests. Manual UAT walkthrough is optional.

**MEDIUM** — Flows that matter but are not deal-breakers. These get Playwright tests if straightforward, or are documented for manual verification only.

**LOW** — Edge cases, cosmetic flows, nice-to-haves. Documented in the catalog but not actively tested during the ceremony. Existing test coverage (if any) is sufficient.

### Happy vs Sad Paths

For each CRITICAL flow, the executor documents at minimum:

- **1 Happy Path** — The flow completes successfully, user sees expected outcome
- **1 Sad Path** — The flow encounters the most likely failure mode, system handles it gracefully

For HIGH flows: Happy path required, sad path recommended.
For MEDIUM/LOW: Happy path only.

### Escalation Flows

Some sad paths involve time-based escalation (e.g., "after 10 days with no action, system sends reminders and creates an escalation"). These are special because they cannot be demonstrated in real-time during UAT.

For escalation flows, the executor must:

- Seed data that represents the POST-escalation state (the reminders have already been sent, the escalation record exists)
- Provide the system owner a way to VIEW the escalation artifacts (email in S3, escalation record in admin queue) rather than WAIT for them to occur
- Optionally: create a Playwright test that uses time manipulation or pre-seeded state to show the full flow compressed into seconds

---

## 5. Test Data Strategy

### Seed Script

The executor creates a **seed script** that populates the database (and any file stores) with all data necessary to demonstrate every flow in the catalog.

Requirements for the seed script:

- **Idempotent.** Running it twice produces the same result, not duplicate data.
- **Isolated.** Test data is identifiable and does not collide with real data. Use naming conventions like `test_*`, phone numbers in the `555-000-XXXX` range, email addresses at a test domain.
- **Comprehensive.** Every flow's preconditions are satisfied by the seed data. If Flow X requires a user with a completed intake AND a pending lab order, that user exists after seeding.
- **Documented.** The seed script includes a manifest (comment block or companion file) listing every test entity created: users, purchases, orders, records, files.

### Reset Script

The executor creates a **reset script** that cleanly removes all seeded test data without affecting non-test data.

Requirements:

- **Safe.** Must not delete production data, real users, or non-test records.
- **Complete.** Removes everything the seed script created, including S3 files, database records, localStorage entries, and any other artifacts.
- **Reversible pairing.** Seed + Reset are complementary — running seed then reset returns the system to its pre-ceremony state.

The reset script is NOT called during UAT. It exists for post-ceremony cleanup and for re-running the ceremony from scratch.

### Test User Matrix

The seed script creates test users that map to the Flow Catalog:

```
USER: [Identifier / Display Name]
  TYPE: [User type from Section 3.1]
  LIFECYCLE: [NEW | EXISTING | RETURNING_INTERRUPTED]
  AUTH: [How to log in — phone number, OTP bypass, test credentials]
  STATE: [What state this user is in — e.g., "completed intake, pending payment"]
  DEMONSTRATES: [Which flows this user supports — by flow name]
```

Each test user should be purpose-built for specific flows. Avoid a single "god user" that has done everything — the system owner needs to see the system from different vantage points.

The matrix MUST include users at different lifecycle stages for the same user type. For example, if the project has a "Client" user type, the seed data should include at minimum: one NEW client (no account, will go through onboarding), one EXISTING client (has account + history, will demonstrate return-visit flows), and one RETURNING_INTERRUPTED client (started a flow but didn't finish, will demonstrate resume/recovery).

---

## 6. Test Suite

### Isolation

Closing Ceremony tests live in their own directory, separate from the project's existing test suite:

```
testing/
├── e2e/                    ← Existing project tests (untouched)
├── closing-ceremony/       ← Ceremony-specific tests
│   ├── seed.sql            ← (or seed.ts, seed.sh — whatever fits the stack)
│   ├── reset.sql
│   ├── flows/
│   │   ├── [flow-name].spec.js
│   │   └── ...
│   ├── fixtures/
│   │   └── test-users.json (or equivalent)
│   ├── helpers/
│   │   └── (shared utilities, login helpers, etc.)
│   └── RESULTS.md          ← Generated after test execution
```

### Test Design

Each Playwright (or equivalent) test file maps to one flow from the catalog:

- **File name matches flow name** — `medical-consult-happy.spec.js` for the "Medical Consult Flow — Happy Path"
- **Test describes the full flow** — not individual page assertions, but the complete journey from precondition to postcondition
- **Tests are self-contained** — each test can run independently (no ordering dependencies between test files)
- **Tests use seeded data** — they assume the seed script has run, they do not create their own data
- **Tests support headed mode** — they must be runnable with `--headed` for the system owner to watch

### What Tests Verify

For each flow, tests verify:

- **Navigation** — User arrives at the correct pages in the correct order
- **Data display** — Seeded data appears correctly (names, amounts, statuses, dates)
- **State transitions** — Actions change system state as expected (button clicks update records, forms persist data)
- **Cross-interface consistency** — What the client sees matches what the admin sees (e.g., a purchase appears in both portals)
- **Error handling** — Sad path flows trigger the correct error states, messages, and fallbacks

### What Tests Do NOT Verify

- Performance (not a ceremony concern)
- Visual pixel-perfection (not a ceremony concern)
- External service behavior (mocked during ceremony)
- Previously verified features outside the current delivery block (covered by existing tests)

---

## 7. Language Support Verification

If the project supports (or intends to support) multiple languages on client-facing interfaces, the Closing Ceremony must verify language behavior. Language support is a cross-cutting concern — it affects every client-facing flow, not just a single feature.

### Discovery

During the Discovery Phase (Section 3), the executor identifies:

- **Which interfaces support multiple languages?** Typically client-facing only (marketing, portal, intake). Admin interfaces often remain in the default language.
- **Which languages are supported?** Check for i18n configuration, translation files, locale detection logic, or language toggle UI.
- **How is language selected?** Common patterns: URL parameter (`?lang=es`), browser `Accept-Language` header, user preference in profile, explicit language picker, subdomain (`es.example.com`).
- **What is the translation coverage?** Full translation of all strings vs partial (some pages translated, others not). The executor documents gaps.

### Language Test Strategy

Language support testing has two layers:

**Layer 1: Mechanism Verification** — Does the language switching mechanism work? This is a MEDIUM-risk test at minimum, escalated to HIGH if the project serves a multilingual user base.

The executor creates tests that verify:

- Language can be activated (via the project's switching mechanism)
- The interface responds to the language change (visible text changes)
- Language preference persists across page navigation within a session
- Language preference persists across sessions (if that's a supported behavior)
- Fallback behavior when a translation is missing (graceful degradation to default language, not broken UI or empty strings)

**Layer 2: Content Verification** — Are the translations correct and complete? This is typically a MEDIUM-risk manual verification — automated tests can confirm that *something* renders, but correctness of translation is a human judgment.

The executor documents:

- Which pages/flows have been tested in each supported language
- Any pages where translation is missing or incomplete
- Any layout issues caused by text length differences (longer translations breaking UI)

### Flow Catalog Integration

For CRITICAL and HIGH flows on client-facing interfaces, the Flow Catalog (Section 4) includes a `LANGUAGE` field:

```
FLOW: [Name]
  ...
  LANGUAGE: [DEFAULT | Specify language code for non-default test, e.g., "es", "fr"]
  ...
```

The executor does NOT need to duplicate every flow in every language. Instead:

- **1-2 CRITICAL flows** are tested in each supported non-default language (confirms the mechanism works end-to-end through a real user journey)
- **All other flows** are tested in the default language only
- **1 dedicated language-switching flow** tests the mechanism itself (toggle/select language, verify change, navigate, verify persistence)

### Seed Data

If the project stores language preferences per user, the seed script creates test users with different language settings. The Test User Matrix (Section 5) includes a `LANGUAGE` field:

```
USER: [Identifier]
  ...
  LANGUAGE: [Language code or "default"]
  ...
```

### UAT Guide

The UAT Guide (Section 9) includes a **Language Verification** subsection:

- How to activate each supported language
- Which test user has which language preference
- Which flows to walk through in non-default languages
- Screenshot or note of any known layout issues from text expansion

---

## 8. Test Execution & Results Report

### Execution

The executor runs the full Closing Ceremony test suite and captures results. The execution must be reproducible — the system owner should be able to re-run the same tests and get the same results.

Execution prerequisites (documented in the UAT Guide):

- Local server running (e.g., `npm run serve`)
- Database seeded (seed script has been run)
- Any required services running (Supabase, Temporal, etc. — or their mocks)

### Results Report (RESULTS.md)

The executor generates a results report:

```
# Closing Ceremony Test Results

## Summary
- Total flows tested: X
- Passing: Y
- Failing: Z
- Skipped: W

## Execution Environment
- Date: YYYY-MM-DD
- Local server: [command + port]
- Database: [connection detail or "local"]
- Mocked services: [list]

## Results by Risk Level

### CRITICAL
| Flow | Type | Result | Notes |
|------|------|--------|-------|

### HIGH
| Flow | Type | Result | Notes |
|------|------|--------|-------|

### MEDIUM
...

### LOW
...

## Failing Flows
[For each failure: flow name, failure point, error message, screenshot if available,
 assessment of whether this is a test issue or a product issue]

## Risk Assessment
[Summary: Are CRITICAL flows passing? Are there patterns in failures?
 What is the overall risk to the delivery block?]
```

### Failure Handling

If CRITICAL flows fail:

- The ceremony is **not complete**. The executor must either fix the issue or escalate it.
- Escalation means documenting the failure in the results report with `[ESCALATION: reason]` and flagging it for the system owner before proceeding.

If HIGH/MEDIUM flows fail:

- Document in results report. The ceremony can proceed. The system owner decides whether to accept or request fixes.

---

## 9. UAT Delivery Package

The final output of a Closing Ceremony is a **UAT Delivery Package** — a single document (or small set of documents) that the system owner consumes to verify the delivered work.

### UAT Guide Structure

```markdown
# UAT Guide — [Project Name] [Phase/Block Name]

## What Was Built
[2-3 paragraph summary of the delivery block: what features were implemented,
 what user types are affected, what the system now does that it didn't before]

## How to Start
[Step-by-step environment setup: start server, seed database, verify prerequisites.
 Copy-paste commands — the system owner should not need to think.]

## Test Users
[Table of test users with login credentials and what each demonstrates.
 The system owner picks a user, logs in, and sees the system from that perspective.]

## User Flows

### [Flow Name] — [CRITICAL/HIGH/MEDIUM]
**As:** [User type]
**Starting at:** [URL]
**Login as:** [Test user name + credentials]

**Manual Walkthrough:**
1. [Navigate to X, you should see Y]
2. [Click Z, you should see W]
3. ...

**Playwright Replay:**
[Command to run this specific test in headed mode with slowMo,
 so the system owner can watch it execute]

### [Next Flow]
...

## Two UAT Modes

### Mode A: Manual Exploration
Log in as any test user. Browse the system. The seed data creates a realistic
environment — you should see purchases, appointments, notifications, and all
the artifacts of a working system. Use this mode to get a feel for the product
and catch anything that looks wrong.

### Mode B: Playwright Replay
Run individual flow tests in headed mode. Watch the browser execute the flow
automatically. Pause at any point to inspect. Use this mode to verify specific
flows quickly and see the system respond to scripted interactions.

**Replay commands:**
- All flows: `npx playwright test testing/closing-ceremony/ --headed`
- Single flow: `npx playwright test testing/closing-ceremony/flows/[flow-name].spec.js --headed`
- Slow replay: append `-- --slow-mo=1000` for 1-second delays between actions
- Debug mode: `npx playwright test [file] --debug` for step-by-step with inspector

## Known Issues
[Any failing tests, known limitations, or items flagged for follow-up.
 Cross-reference the RESULTS.md report.]

## Cleanup
[How to reset after UAT: run the reset script, clear localStorage, etc.
 This section is for AFTER the system owner has finished verifying.]
```

### Knowledge Transfer

The UAT Guide also serves as **knowledge transfer** — after reading it, the system owner should understand:

- What user types exist and how they differ
- What the system's core flows are
- How to demonstrate any feature to a stakeholder
- What test infrastructure exists for ongoing verification
- What's mocked vs real in the current environment

---

## 10. Artifacts Checklist

A complete Closing Ceremony produces these artifacts:

| # | Artifact | Location | Purpose |
|---|----------|----------|---------|
| 1 | **Flow Catalog** | `testing/closing-ceremony/FLOW_CATALOG.md` | Inventory of all demonstrable flows with risk ratings |
| 2 | **Seed Script** | `testing/closing-ceremony/seed.*` | Populates test data for all flows |
| 3 | **Reset Script** | `testing/closing-ceremony/reset.*` | Removes all test data cleanly |
| 4 | **Test Suite** | `testing/closing-ceremony/flows/*.spec.js` | Playwright tests for CRITICAL and HIGH flows |
| 5 | **Test Fixtures** | `testing/closing-ceremony/fixtures/` | Test user definitions, mock data files |
| 6 | **Results Report** | `testing/closing-ceremony/RESULTS.md` | Execution results with risk assessment |
| 7 | **UAT Guide** | `docs/delivery/UAT_GUIDE_[BLOCK_NAME].md` | System owner's verification walkthrough |
| 8 | **GTM Requirements** | `docs/delivery/GTM_[BLOCK_NAME].md` | Go-to-market requirements for local→production transition |

### GTM Requirements Manifest

The Closing Ceremony delivery includes a **Go-to-Market Requirements** document that bridges the gap between "it works locally" and "it's live in production." This manifest lists everything needed to take the locally-verified system to production, organized by category:

**Category 1: Infrastructure Services** — Production hosting and operational infrastructure. These are the platforms that the system runs on.

Examples: AWS (S3, CloudFront, SES, Lambda), Supabase (PostgreSQL, Auth, Edge Functions), DNS/domain registration, SSL certificates, monitoring/alerting services.

Format per item:
```
SERVICE: [Name]
  PURPOSE: [What it does for the system]
  LOCAL MOCK: [How it's currently mocked locally]
  PRODUCTION SETUP: [What the founder needs to do — register, configure, enable]
  ESTIMATED EFFORT: [Time to set up]
  DEPENDENCIES: [Other services that must be configured first]
```

**Category 2: Service Integrations** — External services the system interacts with. These are the APIs and platforms that provide capabilities the system doesn't build itself.

Examples: Twilio (SMS/voice), LabCorp (lab orders/results), pharmacy APIs, payment processors (Square, Stripe), scheduling (Cal.com), AI services (Claude API, OpenAI).

Format per item: same as Category 1, plus:
```
  INTEGRATION TYPE: [API | Browser Automation | Webhook | SDK]
  SANDBOX AVAILABLE: [Yes/No — can we test with sandbox before production?]
  REGULATORY NOTES: [Any compliance requirements — A2P registration, HIPAA, etc.]
```

**Category 3: Channel Integrations** — Impact-driving distribution channels. These are how the system reaches people beyond direct access.

Examples: Marketing campaigns, social media syndication, video posting platforms, email marketing, SEO, advertising platforms, content creation tools.

Format per item:
```
CHANNEL: [Name]
  PURPOSE: [How it drives impact — acquisition, retention, engagement]
  SETUP: [What needs to be configured]
  CONTENT REQUIREMENTS: [What assets need to be created]
  ESTIMATED EFFORT: [Time to set up and populate]
```

**Example: GTM for an EHR System**
- Go-Live Infrastructure: `.env` + deployment scripts (DNS, S3, CloudFront) — one-time manual setup
- Go-Live Services: LabCorp Order/Result API, Pharmacy Order/Status API, Twilio A2P registration
- Go-Live Channels: Marketing portal campaigns, pricing adjustments, content creation → asset deployment → syndication

### Phase Markers

The executor signals ceremony progress via phase markers in stdout (or equivalent logging):

```
[CEREMONY: DISCOVERY_COMPLETE]      — Architecture read, flows identified
[CEREMONY: SEED_COMPLETE]           — Test data seeded, seed/reset scripts created
[CEREMONY: TESTS_COMPLETE]          — All ceremony tests written
[CEREMONY: EXECUTION_COMPLETE]      — Tests run, RESULTS.md generated
[CEREMONY: UAT_GUIDE_COMPLETE]      — UAT delivery package written
[CEREMONY: CLOSING_COMPLETE]        — All artifacts delivered
```

If any CRITICAL flow fails and cannot be resolved:

```
[CEREMONY: ESCALATION] — [Flow name]: [Brief reason]
```

---

## 11. Relationship to Other Ceremonies

### Go-Live Ceremony (Future — Separate Document)

The Closing Ceremony verifies that features WORK. The Go-Live Ceremony verifies that features are DEPLOYED and INTEGRATED with production services.

| Concern | Closing Ceremony | Go-Live Ceremony |
|---------|-----------------|-----------------|
| Environment | Local / Sandbox | Production |
| Integrations | Mocked where needed | Real (Twilio, SES, Square, etc.) |
| Data | Seeded test data | Production data (or production-like) |
| Verification | "Does it work?" | "Is it live and operational?" |
| Audience | System owner (UAT) | System owner + end users |
| Frequency | After each delivery block | Before public launch / major release |

A project in a **mixed state** (some services real, some mocked) runs a Closing Ceremony with the mixed configuration documented. The Go-Live Ceremony is invoked later when all integrations are production-ready.

### Sprint/Block Delivery

The Closing Ceremony is the capstone of a delivery block. It follows the normal delivery flow:

```
GROOMING → DEVELOPMENT → DELIVERY_HANDOFF → CLOSING_CEREMONY → UAT → [ACCEPT / REQUEST CHANGES]
```

If the system owner requests changes after UAT, those changes become a new task block — they do not reopen the Closing Ceremony. A new ceremony is invoked after the changes are delivered.

---

## 12. Executor Guidance

### Reading This Document

This document is a **requirements specification**, not a tutorial. The executor should:

1. Read it once fully before starting
2. Reference specific sections during execution
3. Adapt to the project's actual tech stack (the examples use Playwright/SQL/S3, but the principles apply to any stack)

### Adapting to Project Scale

**Small delivery (1-3 features):** Flow Catalog may have 5-10 flows. Seed script may be a single SQL file. Tests may be 3-5 spec files. UAT Guide may be 2-3 pages.

**Large delivery (full phase):** Flow Catalog may have 30+ flows. Seed script may be a multi-file orchestration. Tests may be 15-20 spec files. UAT Guide may be 8-10 pages with multiple user journeys.

Scale the ceremony to the delivery. A 2-feature delivery does not need a 30-flow catalog.

### Quality Bar

The executor's job is to make the system owner's UAT experience smooth, fast, and confidence-building. The system owner should be able to:

- Start UAT within 5 minutes of reading the guide (environment setup is copy-paste)
- See any CRITICAL flow demonstrated within 2 minutes (seed data is ready, test is runnable)
- Understand what was built without reading source code (the UAT Guide explains it)
- Trust the results report (failures are honest, risk assessments are calibrated)
- Reset and re-run at will (seed + reset scripts are reliable)

---

## 13. Success Criteria

A Closing Ceremony is **complete** when:

- [ ] Flow Catalog exists and covers all delivered features
- [ ] Every CRITICAL flow has both happy and sad path entries
- [ ] Seed script runs without errors and creates all required test data
- [ ] Reset script runs without errors and removes all test data
- [ ] All CRITICAL flow tests pass
- [ ] All HIGH flow tests pass (or failures are documented with risk assessment)
- [ ] RESULTS.md is generated with accurate pass/fail counts
- [ ] UAT Guide is written and includes both Manual and Replay modes
- [ ] Language support verified on client-facing interfaces (if applicable)
- [ ] GTM Requirements manifest produced with all three categories populated
- [ ] System owner can start UAT within 5 minutes of reading the guide
- [ ] No unresolved CRITICAL escalations remain

A Closing Ceremony is **escalated** when:

- A CRITICAL flow fails and cannot be fixed within the ceremony scope
- Required test data cannot be seeded (missing schema, missing tables, permissions)
- The delivered features do not match the original task block specification

Escalation does not mean failure — it means the system owner is informed about gaps before they discover them during UAT.

---

**This document is a living reference. Update it as ceremony patterns mature across projects.**
