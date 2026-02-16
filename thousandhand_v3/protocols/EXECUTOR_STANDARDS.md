# Executor Standards — Opinionated Build Guidelines

> **Type:** Process Requirements Document (Generic)
> **Consumed By:** Execution sessions (Claude Code), GROOMING (for handoff context)
> **Purpose:** Defines HOW systems are built — adapted to the current execution context
> **Version:** 2.0
> **Created:** 2026-02-09
> **Updated:** 2026-02-09

---

## 1. Purpose

These standards define the opinionated defaults for how 1KH EXECUTION sessions build systems. They exist because completion rate matters more than flexibility — a system that ships at 100% locally is worth more than a half-built system on a sophisticated cloud stack.

The Orchestrator reads these standards before initiating any execution. GROOMING references them when hydrating handoffs. EXECUTION follows them unless the project's Foundation docs (Oracle, Context) explicitly override them.

**These standards are context-aware.** The execution context (LOCAL, MIXED, or PRODUCTION) determines which environment rules apply. The context is set in the project's `config.json` and injected into every session prompt.

---

## 2. Execution Context

The executor operates in ONE of three contexts. The context determines where data lives, how integrations work, what gets mocked, and how to seed/test.

### 2.1 Context: LOCAL

**When:** Early development. Building from scratch. No cloud services configured yet.

| Concern | Approach |
|---------|----------|
| **Database** | SQLite file (single file, no server, no credentials) |
| **Auth** | Local mock (test users with bypass tokens, skip-OTP flags) |
| **File storage** | Local filesystem (download/upload to local directories) |
| **Payments** | Mock (simulated transactions, seeded data) |
| **Email/SMS** | Mock (written to local file or console log) |
| **Web server** | `localhost:8080` (or equivalent) |
| **Seed data** | SQLite inserts, local JSON fixtures |
| **Deployments** | None — everything is localhost |

**Why local first:** Cloud setup is a blocking dependency. Registration, API keys, billing, DNS propagation — these create failure modes outside the executor's control. Local-first means build, test, and demonstrate without waiting on anything. High velocity early.

### 2.2 Context: MIXED

**When:** Some services are production, some are local. Typical state after initial development when cloud services are being integrated incrementally.

| Concern | Approach |
|---------|----------|
| **Database** | USE THE ACTUAL DATABASE — if the project uses Supabase, query Supabase. If it uses SQLite locally, use that. Read the project's config/env to determine which. |
| **Auth** | Use whatever auth the project actually uses — if Supabase Auth is configured, use it. Keep bypass/skip-OTP for dev convenience but test real auth flows too. |
| **File storage** | If S3 is configured, use S3. If local, use local. Check the project's existing integration code. |
| **Payments** | Use sandbox/test mode if configured, otherwise mock |
| **Email/SMS** | If SES/Twilio is configured, use sandbox mode. Otherwise mock to console/file. |
| **Web server** | Localhost pointing to whatever backend is configured |
| **Seed data** | Seed into the ACTUAL database, not into mocks. If Supabase, use Supabase inserts. If SQLite, use SQLite inserts. Seed data must be visible in the actual UI. |
| **Deployments** | Only if the task explicitly requires it. Default: no deployment. |

**The critical rule for MIXED context:** DO NOT fall back to demo/mock data when real infrastructure exists. If the project has a Supabase database with tables, seed THAT database. If the project has S3 file storage, upload to S3. The whole point of MIXED is testing with real infrastructure. Falling back to local mocks defeats the purpose.

**How to detect MIXED state:** Look for `.env` files, `supabase/` directories, existing API integrations in the codebase. If cloud services are wired up and working, use them.

### 2.3 Context: PRODUCTION

**When:** Post-closing-ceremony. Preparing for or maintaining a live system. All services are production.

| Concern | Approach |
|---------|----------|
| **Database** | Production database (Supabase, PostgreSQL, etc.) — use with care |
| **Auth** | Production auth — real users, real sessions |
| **File storage** | Production storage (S3, etc.) |
| **Payments** | Production payment processor (Stripe live mode, etc.) — NEVER use test data in production payment systems without explicit founder approval |
| **Email/SMS** | Production messaging (SES, Twilio with A2P registration) |
| **Web server** | Production deployment (CloudFront, Vercel, etc.) |
| **Seed data** | Test data must be clearly identifiable and isolated. Use naming conventions (`test_*`, `555-000-XXXX`). Never pollute production data. |
| **Deployments** | Yes — CDN invalidation, edge function deployment, database migrations |

**Extra caution in PRODUCTION:** Every mutation is real. Seed data must be cleanly removable. Test users must not collide with real users. Migration rollbacks must be planned.

### 2.4 Context Detection in Session

The execution context is injected into the session prompt as `[EXECUTION_CONTEXT: LOCAL|MIXED|PRODUCTION]`. The executor MUST read this and adapt behavior accordingly. When in doubt about which services are real vs mocked, read the project's configuration files (`.env`, `supabase/config.toml`, existing service integration code) to determine actual state.

### 2.5 Recommended Stage Naming

Projects MAY adopt **DEV / INTEGRATION / PRODUCTION** naming to better communicate stage intent:

| Executor Context | Recommended Name | Purpose |
|-----------------|-----------------|---------|
| LOCAL | **DEV** | Fast offline development, zero external dependencies |
| MIXED | **INTEGRATION** | Real services with test data, UAT verification |
| PRODUCTION | **PRODUCTION** | Live system, real users |

The mapping is 1:1 — all behavioral rules from Sections 2.1–2.3 apply unchanged.
The recommended naming avoids confusion between "LOCAL" (which sounds like a location)
and "MIXED" (which doesn't communicate what's mixed). See `ARCHITECTURE_TEMPLATE.md` →
"Preferred Stage Architecture" for the full infrastructure matrix per stage.

**When using the recommended naming**, the context injection becomes:
`[EXECUTION_CONTEXT: DEV|INTEGRATION|PRODUCTION]`

---

## 3. Tech Stack: Opinionated Defaults

### Default Stack (LOCAL context)

| Layer | Technology | Reason |
|-------|-----------|--------|
| **Database** | SQLite | Zero config, single file, portable, sufficient for MVP |
| **Backend** | Node.js (Express or plain http) | Widely understood, fast to scaffold, good tooling |
| **Frontend** | Plain vanilla HTML/CSS/JS | No build step, no bundler, no framework overhead. Edit and refresh. |
| **Auth** | Local mock with test users | Real auth is a GTM concern, not an MVP concern |
| **Testing** | Playwright (browser) + Node test runner (unit) | TDD standard from ARCH_V3 Section 6 |

### Stack in MIXED/PRODUCTION context

When the execution context is MIXED or PRODUCTION, the "default stack" is whatever the project ACTUALLY uses. Read the codebase. If it uses Supabase + Express + vanilla JS, that's the stack. Don't introduce SQLite when Supabase is already configured. Don't mock auth when Supabase Auth is wired up. The project's existing infrastructure IS the stack.

### When to Override

The founder's Context preferences (from Opening Ceremony) may specify a different stack. Overrides are respected when:

- The founder has existing code in a specific framework → use that framework
- The founder has a strong preference expressed in Oracle/Context → respect it
- The system requires a capability that vanilla JS can't provide → justify and document

Overrides are NOT respected when:

- "I heard React is better" (opinion without project-specific reason)
- "We'll need it at scale" (premature optimization — solve local first)
- "It's industry standard" (standards don't matter if the MVP never ships)

---

## 4. Test-Driven Development

### Standard: TDD to exhaustion

Every feature follows the test-first standard from ARCH_V3 Section 6, with these execution-level specifics:

**Unit tests** — Cover data layer logic: database operations, business rules, validation, calculations. These run fast and catch logic errors before the browser is involved.

**Playwright browser automation** — Cover all user-facing outcomes: form interactions, navigation flows, state persistence, responsive behavior, error handling. Every acceptance criterion that can be expressed as an assertion MUST be a Playwright test.

**Test-to-exhaustion protocol:**

1. Write tests first (from handoff acceptance criteria)
2. Write implementation
3. Run all tests
4. If TEST fails → try to FIX (up to 3 attempts per failure)
5. If fix succeeds → re-run all tests (new failures may appear)
6. If same failure persists after 3 attempts → **accept and document** the gap
7. Document: what failed, what was tried, risk assessment of the gap

**Coverage gaps representing major risk** get max retries. Coverage gaps on cosmetic/low-risk items can be accepted sooner.

### User Flow Test Coverage

When the grooming handoff references user flows (from `docs/USER_FLOWS.md`), the executor must:

1. **Write end-to-end Playwright tests** that cover each referenced user flow as a complete journey (not individual page assertions — the full path from precondition to postcondition)
2. **Create new user flow tests** for any new flows introduced by this task
3. **Update existing flow tests** if this task modifies behavior in an existing flow
4. **Mark flow-independent tasks** (infrastructure, chores) as exempt from flow testing — unit/integration tests are sufficient

> **See also:** GROOMING_STANDARDS "User Flow Management" section for how flows are identified and classified during grooming.

### Seed Data Requirements

Every system must include:

- **Test users** — At least 3 per user type (NEW, EXISTING, RETURNING_INTERRUPTED)
- **Seeded tables** — All database tables populated with realistic data
- **Realistic product/pricing data** — Not placeholder "Product A $10" but actual representative data
- **Mock integrations** — In LOCAL context: every external service call has a local mock. In MIXED/PRODUCTION context: use real integrations where configured, mock only what's not yet wired up.
- **E2E test suites** — Full flow coverage for CRITICAL and HIGH risk paths

**Context-specific seeding:**

| Context | Where to seed | How |
|---------|--------------|-----|
| LOCAL | SQLite + local fixtures | SQL inserts, JSON files, filesystem |
| MIXED | The ACTUAL database (Supabase, PostgreSQL, etc.) | Supabase client inserts, SQL migrations, API calls |
| PRODUCTION | Production database with isolated test data | Clearly prefixed test data (`test_*`), separate test org/tenant if possible |

**The seed data must be visible in the actual UI.** If the user opens their browser and the page shows "No data" or falls back to "demo mode," the seeding failed. Seed the real database, not a mock layer.

### Data Persistence

Use persisted data from DB over localStorage alone. Both may be necessary (localStorage for offline/draft state, DB for durable state), but the DB is the source of truth. In LOCAL context, "the DB" is SQLite. In MIXED/PRODUCTION context, "the DB" is whatever cloud database the project uses.

---

## 5. Build Order

### 5.1 Single Feature: Layer Order

For any individual feature or user flow, follow this layer priority:

```
1. DATA LAYER
   Schema, API routes, business logic, persistence.
   Fully testable autonomously. No subjective judgment needed.
   Build and test this BEFORE anything visual.
        │
        ▼
2. APP LAYER
   Minimal UX handling: form inputs, navigation, validation, controls, persistence.
   Functional but unstyled. Proves the data layer works end-to-end.
   Focus: correct behavior, not appearance.
        │
        ▼
3. MINIMAL RESPONSIVE LAYOUT
   Mobile-first structure. Navigation. Viewport handling.
   Layout and information architecture, not visual polish.
        │
        ▼
4. FINAL STYLE GUIDE
   Colors, fonts, sizes, brand personality.
   Fit to founder preferences from Context doc.
   This is the LAST step, not the first.
```

**Why this order:** The data layer is objectively testable. The UX requires subjective judgment. Building data first means the UI wires up to proven, tested endpoints — not sand.

### 5.2 Multi-UF Execution Within a JM: Layer-Horizontal

When a JM contains multiple user flows (UF1, UF2, UF3), execute ALL UFs at the same layer before moving to the next layer:

```
JM1:  UF1-DATA → UF2-DATA → UF3-DATA        (complete DATA layer)
      UF1-APP  → UF2-APP  → UF3-APP          (complete APP layer)
      UF1-UX   → UF2-UX   → UF3-UX           (complete UX-MIN layer)
      UF1-FIN  → UF2-FIN  → UF3-FIN          (complete UX-FIN layer)
```

Do NOT execute UF1 through all layers, then UF2 through all layers (vertical/flow-first). Vertical execution causes schema rework — UF2's DATA needs may alter tables UF1 already built, breaking UF1's tests.

**Why layer-horizontal:** UFs within a JM share tables, RLS policies, and API patterns. Building all DATA first means the complete schema exists before APP layer starts. Each layer "settles" before the next is poured.

### 5.3 Multi-JM Execution: JM-Complete Delivery

When executing across multiple JMs, complete each JM through ALL layers before starting the next:

```
JM1: DATA(all UFs) → APP(all UFs) → UX-MIN(all UFs) → UX-FIN(all UFs)  ✓ deliverable
JM2: DATA(all UFs) → APP(all UFs) → UX-MIN(all UFs) → UX-FIN(all UFs)  ✓ deliverable
JM3: DATA(all UFs) → APP(all UFs) → UX-MIN(all UFs) → UX-FIN(all UFs)  ✓ deliverable
```

Do NOT execute all DATA across all JMs first. That produces a massive data layer and zero working features for weeks.

**Why JM-complete:** A finished JM is demoable, testable, and validatable end-to-end. Feedback from JM1 informs JM2's schema design. JMs that share tables build incrementally via migrations.

### 5.4 Happy Paths Before Escalation Paths

Across all JMs, execute happy path user flows before escalation/sad path variants:

- **Phase 1:** All JM happy paths (JM-complete, layer-horizontal per JM)
- **Phase 2:** Critical escalation paths (>50% real usage frequency — these are effectively second happy paths)
- **Phase 3:** Remaining escalation paths by priority

Happy paths are the product. Escalation paths are the safety net. You can demo and validate with happy paths only. Escalation paths that occur in >50% of usage are reclassified as Phase 1.

**See also:** ARCH_V3 Section 3.8 (Execution Sequencing Model) for the full rationale and visual models.

---

## 6. Architecture Documentation

### Rule: Create and maintain an ARCHITECTURE.md

Every system gets a single ARCHITECTURE.md (per ARCH_V3 Section 11.11) that:

- Tracks the roadmap of features (planned, in-progress, complete)
- Records delivery of features (links to delivery docs)
- Captures major architectural decisions
- Gets updated at the START and END of every feature

**Why:** Context drift is inevitable. Sessions compact. The ARCHITECTURE.md is the antidote — it's the file every session reads first and updates last. It mitigates context drift by externalizing the project's memory.

### Delivery Breadcrumbs

At feature end, document the entire delivery:

- Where source lives (file paths)
- Data models (schema, tables, migrations)
- Tests (what's covered, pass rates)
- Summary of implementation decisions

Save as a delivery doc. Reference from ARCHITECTURE.md. This trail means any future session can trace back to understand WHY something was built the way it was.

### Source Control

Commit code to local git repo to close off each feature. Use descriptive commit messages that reference the feature name and delivery doc. Since everything is local, no remote pushes needed yet — that's a GTM concern.

---

## 7. Catalog Updates at Delivery

When execution completes a task that was tagged during breakdown/grooming as a JM_NEW_UF, JM_NEW, or DEFERRED_PROMOTED item, the executor MUST update the project's catalog documents at delivery time:

### USER_FLOWS.md — Status Update

For tasks that serve user flows with `Status: PLANNED` (created during breakdown):
1. Find the flow entry by its `flow-{draft_id}` ID
2. Update `Status: PLANNED` → `Status: IMPLEMENTED`
3. Fill in the `Steps:` section with the actual implemented steps (replacing "(defined during grooming)")
4. Update `Test file:` with the actual test file path (if Playwright tests were written)
5. Update `Verification:` from `TBD` to the appropriate mode (playwright/manual/mixed)

### JOURNEY_MAPPINGS.md — Status Update

For tasks that introduce a new journey (JM_NEW):
1. Find the journey entry by its ID
2. Update status from `PLANNED` to `IN PROGRESS` or `IMPLEMENTED` depending on scope
3. Add step definitions as they become clear during implementation

### Why at Delivery

Breakdown creates [PLANNED] entries so future breakdowns and grooming sessions have context. Execution converts them to [IMPLEMENTED] so the catalogs reflect reality. This two-stage update ensures:
- Grooming always sees what's been identified (even if not yet built)
- Future breakdowns don't re-discover items that are already in the pipeline
- The catalogs are always an accurate reflection of both planned and completed work

See also: ARCH_V3 Section 3.7 (Pre-Flow Pipeline) for how [PLANNED] entries are created during breakdown.

---

## 8. Decision Making

### Rule: Recommend and proceed.

When the executor encounters an unknown design decision:

1. **Break it down** — Decompose the decision into concrete options
2. **Research** — If the decision requires external knowledge, research it
3. **Use sound judgment** — Ask: "If the founder asked 'what would you recommend?' what would I say?"
4. **Go with the recommendation** — Pick the pragmatic option and move forward
5. **Document the decision** — Note what was chosen and why in the delivery doc

**Do NOT:**

- Come back with a long list of human TODO items
- Block on decisions that have a clear pragmatic answer
- Over-engineer because "we might need it later"
- Under-build because "we can add it later" (if it's in the MVP, build it now)

**The founder's encoded preferences** (from Opening Ceremony Context doc) inform the "gut" — the executor references these for ambiguous calls about UX style, error handling verbosity, feature depth, etc.

### Go the Distance

The expectation is a **fully functioning LOCAL site** at the end of a session. Not a skeleton. Not a "here's what you need to finish." A working system that the founder can run, log into, and use.

---

## 9. Development Cycle

### Context Window Management

Before starting a feature, estimate whether it fits in a single session:

- **Small feature** (single form, single page, 1-2 API routes): fits easily
- **Medium feature** (multi-page flow, 3-5 API routes, complex logic): fits with lean handoff
- **Large feature** (entire subsystem, 5+ pages, complex state): may need to be split

If a feature is too large (will materially compact before completion), break it into parts that each accommodate a sufficient context window. Mark each part's beginning and end by emitting phase markers:

```
[FEATURE: START] feature-name
[FEATURE: CHECKPOINT] feature-name — data layer complete
[FEATURE: CHECKPOINT] feature-name — app layer complete
[FEATURE: END] feature-name
```

### Per-Feature Cycle

1. **At feature beginning:**
   - Read ARCHITECTURE.md
   - Trace down any DELIVERY documents pertinent to this feature
   - Understand what exists, what's changing, what depends on this

2. **During feature creation:**
   - Follow build order (Section 5)
   - Follow TDD standard (Section 4)
   - Spirit of development is TDD, but feel free to write TESTS then CODE then execute TESTS in one go to optimize time and token usage
   - Apply guidelines from this document

3. **At feature end:**
   - Document the delivery (source paths, data models, tests, implementation summary)
   - Save delivery doc
   - Reference from ARCHITECTURE.md
   - Commit to local git repo

### No Deployments

Since everything is local, no deployment scripts are needed during execution. Deployment is a GTM concern addressed by the Closing Ceremony's GTM requirements manifest.

---

## 10. Relationship to Other Documents

| Document | How Executor Standards Relates |
|----------|-------------------------------|
| **ARCH_V3.md** | Executor Standards implements the principles from Sections 6 (Test-First), 12 (Local-First), and 14 (Automated Verification). Section 5 (Build Order) implements the execution sequencing model from ARCH_V3 Section 3.8. Section 7 (Catalog Updates at Delivery) ensures that ARCH_V3 Section 3.7 (Pre-Flow Pipeline) [PLANNED] entries transition to [IMPLEMENTED] at execution completion. |
| **GROOMING_STANDARDS** | Defines the grooming phase: triage classification, WHAT-not-HOW, scope validation, user flow management, and sequencing guidance (aligns with Section 5 Build Order). Grooming sets the testing expectations; Executor Standards defines the TDD protocol for meeting them. |
| **OPENING_CEREMONY.md** | Produces the Foundation docs that inform executor preferences (especially Context) |
| **ORCHESTRATOR_STANDARDS.md** | Defines when and how the Orchestrator invokes execution sessions using these standards |
| **CLOSING_CEREMONY.md** | Defines what happens after execution — UAT, test reporting, GTM requirements |
| **GROOMING HANDOFF** | The handoff document that tells a specific execution session what to build, referencing these standards |

---

## 11. Overrides

These standards are defaults. They can be overridden by:

1. **Foundation docs** — If the Oracle says "use Python" or the Context says "existing React codebase," those take precedence
2. **GROOMING handoff** — If a specific task requires a different approach (e.g., "this task integrates with an existing Express server"), the handoff specifies the deviation
3. **Founder escalation** — If the founder explicitly requests a different approach during an escalation

Overrides are documented in the delivery doc with rationale. The standard is the default; the override is the exception that proves the rule.

---

**These standards optimize for one thing: shipping a working local system at 100% completion. Everything else is secondary.**
