# Executor Standards — Opinionated Build Guidelines

> **Type:** Process Requirements Document (Generic)
> **Consumed By:** Execution sessions (Claude Code), GROOMING (for handoff context)
> **Purpose:** Defines HOW systems are built during the Orchestrator phase
> **Version:** 1.0
> **Created:** 2026-02-09

---

## 1. Purpose

These standards define the opinionated defaults for how 1KH EXECUTION sessions build systems. They exist because completion rate matters more than flexibility — a system that ships at 100% locally is worth more than a half-built system on a sophisticated cloud stack.

The Orchestrator reads these standards before initiating any execution. GROOMING references them when hydrating handoffs. EXECUTION follows them unless the project's Foundation docs (Oracle, Context) explicitly override them.

---

## 2. Environment: Local Only

### Rule: Create within and deploy to LOCAL ENV only.

During the Orchestrator phase, everything runs on the founder's machine. No cloud deployments. No production pushes. No DNS configuration. The system must work at `localhost`.

**Why:** Cloud setup is a blocking dependency. Registration, API keys, billing, DNS propagation — these take time and create failure modes outside the executor's control. Local-first means the executor can build, test, and demonstrate without waiting on anything.

**What "local" means:**

- Web server: `localhost:8080` (or equivalent)
- Database: SQLite file (single file, no server, no credentials)
- Auth: Local mock (test users with bypass tokens)
- Payments: Mock (simulated transactions, seeded data)
- Email/SMS: Mock (written to local file or console log)
- File storage: Local filesystem
- Scheduling: Mock (seeded appointment data)

Production integrations are documented as GTM requirements (see CLOSING_CEREMONY.md) but NOT implemented during execution.

---

## 3. Tech Stack: Opinionated Defaults

### Default Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| **Database** | SQLite | Zero config, single file, portable, sufficient for MVP |
| **Backend** | Node.js (Express or plain http) | Widely understood, fast to scaffold, good tooling |
| **Frontend** | Plain vanilla HTML/CSS/JS | No build step, no bundler, no framework overhead. Edit and refresh. |
| **Auth** | Local mock with test users | Real auth is a GTM concern, not an MVP concern |
| **Testing** | Playwright (browser) + Node test runner (unit) | TDD standard from ARCH_V3 Section 6 |

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

### Seed Data Requirements

Every system must include:

- **Test users** — At least 3 per user type (NEW, EXISTING, RETURNING_INTERRUPTED)
- **Seeded tables** — All database tables populated with realistic data
- **Realistic product/pricing data** — Not placeholder "Product A $10" but actual representative data
- **Mock integrations** — Every external service call has a local mock that returns realistic responses
- **E2E test suites** — Full flow coverage for CRITICAL and HIGH risk paths

### Data Persistence

Use persisted data from DB over localStorage alone. Both may be necessary (localStorage for offline/draft state, DB for durable state), but the DB is the source of truth. If a system has user data, it goes in SQLite — not just `window.localStorage`.

---

## 5. Build Order

For any feature, follow this priority order:

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

## 7. Decision Making

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

## 8. Development Cycle

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

## 9. Relationship to Other Documents

| Document | How Executor Standards Relates |
|----------|-------------------------------|
| **ARCH_V3.md** | Executor Standards implements the principles from Sections 6 (Test-First), 12 (Local-First), and 14 (Automated Verification) |
| **OPENING_CEREMONY.md** | Produces the Foundation docs that inform executor preferences (especially Context) |
| **ORCHESTRATOR_STANDARDS.md** | Defines when and how the Orchestrator invokes execution sessions using these standards |
| **CLOSING_CEREMONY.md** | Defines what happens after execution — UAT, test reporting, GTM requirements |
| **GROOMING HANDOFF** | The handoff document that tells a specific execution session what to build, referencing these standards |

---

## 10. Overrides

These standards are defaults. They can be overridden by:

1. **Foundation docs** — If the Oracle says "use Python" or the Context says "existing React codebase," those take precedence
2. **GROOMING handoff** — If a specific task requires a different approach (e.g., "this task integrates with an existing Express server"), the handoff specifies the deviation
3. **Founder escalation** — If the founder explicitly requests a different approach during an escalation

Overrides are documented in the delivery doc with rationale. The standard is the default; the override is the exception that proves the rule.

---

**These standards optimize for one thing: shipping a working local system at 100% completion. Everything else is secondary.**
