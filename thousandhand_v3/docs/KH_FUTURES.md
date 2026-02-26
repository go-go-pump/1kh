# KH Futures — Vision, History, and Roadmap

> **Status:** LIVING DOCUMENT — captures the north star vision, lessons from v2, and the progression from where we are today to where we're going.
> **Created:** 2026-02-25
> **Purpose:** Don't lose sight of the vision while building incrementally. Each section is tiered by buildability: what's real now, what's next, and what's north star.

---

## The Full Picture

```
FOUNDATION (north star, values, context)
    ↓
ORCHESTRATOR (reflection → imagination → intent → planning)
    ↓
SYSTEM CONFIG (structured spec of business capabilities)
    ↓
SC BUILDER (generates JMs from SC)
    ↓
EXECUTOR (builds, tests, delivers artifacts)
    ↓
MONITORING (observes everything, feeds back to reflection)
    ↓
JAM SESSION (founder input channel — voice/text → triage → queue)
    ↓
    └──────── feedback loop back to ORCHESTRATOR ────────┘
```

Today we have the Executor (v3) and the SC concept (designed, not built). Everything else is documented vision. The goal is to work bottom-up — solidify what's closest to working, then progressively enable the higher layers.

---

## 1. Orchestrator — The Thinking Layer

### What It Is

The Orchestrator is the cognitive engine of 1KH. It handles everything between "I have a business idea" and "here is a structured, buildable specification." It does not produce source code, infrastructure, or deployable artifacts — that's the Executor's job. The Orchestrator *thinks*; the Executor *does*.

### The Five-Loop Model (from v2)

```
REFLECTION → IMAGINATION → INTENT → WORK → EXECUTION
     ↑                                         │
     └──────────── cycle repeats ──────────────┘
```

| Loop | Purpose | Input | Output |
|------|---------|-------|--------|
| **REFLECTION** | Analyze trajectory and system state | Monitoring data, metrics from previous cycle | Completeness analysis, trajectory, recommendations (AUGMENT/OPTIMIZE/PIVOT/CONTINUE) |
| **IMAGINATION** | Generate testable hypotheses | Foundation docs + REFLECTION guidance | Scored hypotheses (feasibility × 0.4 + north_star_alignment × 0.6) |
| **INTENT** | Evaluate and approve hypotheses | Hypotheses from IMAGINATION | Approved list (score ≥ 0.65 auto-approve, 0.40-0.65 escalate to human, < 0.40 reject) |
| **WORK** | Decompose into concrete tasks | Approved hypotheses | Task breakdown (which may include SC generation) |
| **EXECUTION** | Execute tasks, measure outcomes | Tasks from WORK | Results with metrics delta (feeds back to REFLECTION) |

### Foundation — The Input Layer

Every project begins with Foundation documents that anchor all decision-making:

**Oracle (Values & Principles):** Immutable constraints the system will NEVER violate. Changes require explicit amendment with justification. Guides all hypothesis generation.

**North Star (Objectives & Success Criteria):** Measurable, time-bound targets. Used to score hypothesis alignment. Example: "$10K MRR by month 6" or "100 active patients by Q3."

**Context (Constraints & Resources):** Budget, time, team size, existing capabilities, regulatory requirements. Used for feasibility scoring.

**Seeds (Initial Hypotheses):** Founder intuitions and hunches. NOT assumed truths — consumed during the first IMAGINATION cycle, become hypotheses to be scored and validated.

### System Completeness Gating

The Orchestrator tracks four components required for a business to generate revenue:

| Component | Description | Status States |
|-----------|-------------|---------------|
| **Product** | The thing you sell | MISSING → PLANNED → BUILDING → LIVE |
| **Payment** | How customers pay | MISSING → PLANNED → BUILDING → LIVE |
| **Channel** | How customers find you | MISSING → PLANNED → BUILDING → LIVE |
| **Fulfillment** | How value is delivered | MISSING → PLANNED → BUILDING → LIVE |

If Payment is MISSING, revenue MUST be zero regardless of other metrics. REFLECTION detects this and recommends AUGMENT. IMAGINATION prioritizes hypotheses that fill the gap.

### The Orchestrator's Relationship to SC

In the full vision, the Orchestrator *automatically produces* System Configs. The flow:

```
Foundation docs → REFLECTION (what's missing?) → IMAGINATION (what should we build?) →
INTENT (is this worth building?) → WORK (crystallize into SC) → SC Builder (generate JMs) →
Executor (build artifacts)
```

Today, the founder performs the REFLECTION/IMAGINATION/INTENT work mentally and writes SCs manually. The SC Builder handles WORK→EXECUTION. As the Orchestrator matures, the manual steps get automated progressively — first INTENT (scoring), then IMAGINATION (hypothesis generation), then REFLECTION (monitoring-driven analysis).

### Forecast & Simulation (v2 Concept — Future)

v2 introduced a business simulation engine that runs the five loops without actual execution:

- **Mock mode:** Everything simulated, no API cost, runs in seconds
- **Real planning mode:** Real LLM calls, no real execution — captures planning trace
- **Replay mode:** Replay prior simulation with cached responses
- **Monte Carlo mode:** Run N simulations with variable conditions to understand sensitivity

Configurable variables: human decision quality, market response multiplier, chaos/failure rate, execution variance. The purpose: learn from hypothetical failures before committing real resources. Run 100 simulations and discover which variables matter most.

This was powerful in concept but lacked connection to real execution outcomes. Future implementation should ground simulations in actual metrics from the Monitoring Platform, not mock data.

### Lessons from v2

**What v2 got right (carry forward):**

- Five-loop orchestration model — conceptually sound, validated through implementation
- Foundation-driven architecture — Oracle/North Star/Context/Seeds is the right intake model
- Hypothesis-driven development with weighted scoring (feasibility × 0.4 + alignment × 0.6)
- System completeness gating (Product/Payment/Channel/Fulfillment)
- Two-level hypothesis system: CAPABILITY (what) vs IMPLEMENTATION (how)
- Event log as append-only JSONL with immutable timestamped events
- Cycle reports as the primary visibility artifact (see bix-v3 dashboard below)

**What v2 got wrong (learn from):**

- Built the planning system without the execution engine — could simulate but couldn't *do*
- Hypothesis test conditions were never wired to real measurable outcomes
- Foundation intake flow was designed (7 phases) but not fully built
- Jumped directly from HYPOTHESIS → TASK without an intermediate WORK ITEMS decomposition
- Meta-build (factory of factories) attempted too early — system couldn't improve its own hypothesis generation

**The core v2→v3 lesson:** v2 was ~85% complete as a *planning system* and 0% complete as a *doing system*. v3 solved this by building the Executor first. The Orchestrator comes back when the execution layer is proven and there's real data to reflect on.

### Buildability Tier: NORTH STAR

The full Orchestrator is the most complex piece of 1KH and the furthest from implementation. Prerequisites: working SC Builder (to automate WORK output), working Monitoring Platform (to feed REFLECTION with real data), proven Executor patterns (to validate that the execution layer is reliable enough for autonomous orchestration).

---

## 2. Monitoring Platform — The Listening Station

### What It Is

A lightweight, always-on monitoring system that observes everything happening across a KH-managed project and feeds data back into the system. It's the *output channel* — the system telling you what's happening. Designed after Prometheus: simple text-based time series data, local-first, poll-based.

### Why It Matters

Without monitoring, the feedback loop is broken. REFLECTION can't analyze trajectory if there's no data. The Executor can't self-heal if it doesn't know something is broken. The founder can't make informed decisions from their phone if there's no listening station to check.

This should be the **first artifact that KH builds for any project.** Before features, before business logic — stand up the monitoring infrastructure. It validates that the deployment pipeline works (can we deploy something?) and immediately starts capturing data. Every subsequent JM publishes metrics to the same monitoring endpoint.

### Dimensions Tracked

| Dimension | What It Captures | Example Metrics |
|-----------|-----------------|-----------------|
| **Site Health** | Uptime, response times, availability | `site_health_status{endpoint="/api/clients"} 200`, `site_health_latency_ms{endpoint="/api/clients"} 142` |
| **API/Site Errors** | Error rates, error types, stack traces | `error_count{type="500",endpoint="/api/intake"} 3`, `error_rate_pct{window="5m"} 0.02` |
| **Analytics** | User activity, page views, conversions | `analytics_pageview{page="/portal/dashboard"} 47`, `analytics_signup_count 12` |
| **Hypothesis Tracking** | Hypothesis status, validation progress | `hypothesis_status{id="hyp-001",state="validated"} 1`, `hypothesis_score{id="hyp-001"} 0.77` |
| **Campaign Performance** | Ad spend, impressions, conversions, ROI | `campaign_spend_usd{id="fb-001"} 150.00`, `campaign_conversions{id="fb-001"} 3` |
| **Escalations/Issues** | System issues (unexpected behavior, not operational support) | `escalation_count{severity="HIGH"} 2`, `escalation_open_duration_hours{id="ESC-14"} 4.5` |
| **Work Completion** | Task throughput, cycle time, delivery rate | `work_tasks_completed{cycle="003"} 7`, `work_cycle_time_hours{avg="true"} 3.2` |
| **Founder Input** | Input priority, queue depth, response time | `founder_input{priority="CRITICAL"} 1`, `founder_input_queue_depth 4` |

### Architecture — Prometheus-Inspired

```
┌─────────────────────────────────────────────────────────┐
│  END SYSTEMS (sources of truth)                         │
│                                                         │
│  App/API → error logs, latency, status codes            │
│  Analytics → page views, signups, conversions           │
│  Campaigns → spend, impressions, clicks                 │
│  KH Executor → task completions, cycle events           │
│  Escalation system → open issues, severity              │
│  Founder (Jam Session) → voice memos, priority inputs   │
│                                                         │
│  Each source: performs action → formats single-line      │
│  metric → publishes to local endpoint                   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  KH MONITOR (poller)                                    │
│                                                         │
│  Polls endpoint on configurable interval                │
│  (as often as 1 min, as infrequent as 1/day)            │
│  Takes single snapshot per poll                         │
│  Saves snapshot as TXT in local .kh/monitor/            │
│  Compares to previous snapshot (state management)       │
│  Evaluates thresholds and rules                         │
│  Makes choices: alert, queue action, trigger worker     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  DASHBOARD (visualization)                              │
│                                                         │
│  Live view: North Star progress, system health,         │
│  active hypotheses, recent task outcomes,               │
│  open escalations, founder input queue                  │
│  Aggregate and render from snapshot history             │
│  Locally hosted (same as testing dashboard pattern)     │
└─────────────────────────────────────────────────────────┘
```

### Data Format

Simple text-based exposition, one metric per line, Prometheus-style:

```
# HELP site_health_status HTTP status code for endpoint
# TYPE site_health_status gauge
site_health_status{endpoint="/api/clients",method="GET"} 200 1740528000
site_health_latency_ms{endpoint="/api/clients",method="GET"} 142 1740528000

# HELP error_count Total errors by type and endpoint
# TYPE error_count counter
error_count{type="500",endpoint="/api/intake"} 3 1740528000

# HELP founder_input Founder input items by priority
# TYPE founder_input gauge
founder_input{priority="CRITICAL"} 1 1740528000
founder_input{priority="MAINTENANCE"} 3 1740528000
```

State management: snapshots saved as timestamped TXT files in `.kh/monitor/snapshots/`. The monitor diff's current vs. previous to detect changes, trends, and threshold breaches.

### Local Worker — The Self-Healing Bridge

The critical architectural insight: **Claude Code runs locally, not in production.** So the monitoring platform needs a local worker that bridges prod observability with local execution.

```
PROD monitoring detects issue (error spike, failed campaign, escalation)
    ↓
Local worker receives alert (polls prod monitoring endpoint)
    ↓
Local worker emulates issue in DEV (docker-compose environment)
    ↓
Confirms reproduction (issue exists locally)
    ↓
Triggers Executor session: create tests, implement fix
    ↓
Validates fix passes in DEV
    ↓
Deploys to PROD (sst deploy --stage prod)
    ↓
Resolves issue in monitoring (closes escalation, updates metrics)
    ↓
Logs the cycle (what was found, what was fixed, what was deployed)
```

**Two modes:**

| Mode | Monitoring Source | Action Target | Use Case |
|------|-----------------|---------------|----------|
| **LOCAL (test)** | Local docker-compose metrics | Local dev environment | Development, UAT, testing self-healing logic |
| **PROD (live)** | Production AWS metrics | Local dev → deploy to prod | Real incidents, real fixes, real deployments |

The local worker listens to BOTH simultaneously. Local issues are fixed in place. Prod issues are emulated locally first, fixed, tested, then deployed back to prod. This keeps Claude Code in the execution loop without requiring it in production infrastructure.

### Campaign Intelligence (Future)

The monitoring platform tracks campaign performance over time. A worker evaluates completed campaigns and decides: create new campaigns with different targeting, increase budget on performing campaigns, extend duration, or — critically — recognize when an idea isn't working despite best efforts. This is REFLECTION applied to marketing: the data tells you when to PIVOT.

### Reference: bix-v3 Cycle Dashboard

The archived project at `/archive/bix-v3/.1kh/reports/cycle_003.html` demonstrates the v2 vision for cycle reporting. It included:

- North Star progress card ($11,442 / $1M ARR = 1.1%)
- Cycle summary (hypotheses generated, tasks executed, revenue delta, signup delta)
- System component status (Product/Payment/Channel/Fulfillment — all MISSING in cycle 3)
- Revenue gate warning ("Cannot generate revenue — no product, no payment system")
- Trajectory analysis (velocity, trend, cycles-to-goal estimate)
- AUGMENT recommendations (define product, add payment, add marketing channel)
- Hypothesis table with feasibility/alignment/composite scores
- Task outcomes with per-task revenue and signup deltas

This dashboard is the template for the Monitoring Platform's visualization layer. The difference: v2 generated these reports from simulated data. The future version generates them from real monitoring metrics.

### Buildability Tier: BUILD SOON

The Monitoring Platform should be one of the first things built after the SC Builder is working. It can be the first SC-generated artifact — a monitoring JM that creates the dashboard, the polling infrastructure, the snapshot storage, and the local worker. It validates the SC→JM pipeline while also producing something immediately useful.

Specifically: when any new project is initialized via KH, the monitoring infrastructure should be part of the bootstrap — just like how the first SC deployment includes Cognito, Aurora, and the project scaffolding. Monitoring is foundational infrastructure, not an add-on feature.

---

## 3. Jam Session — The Founder Input Channel

### What It Is

A lightweight input utility that lets the founder inject ideas, fixes, and decisions into the KH system from anywhere — including mobile, away from the development machine. It's the *input channel* — the founder telling the system what to do. Paired with Monitoring (the output channel), it creates a complete feedback loop.

### The Problem It Solves

You're walking your dog and realize the intake form needs a new field. You're in a meeting and a client mentions a bug. You read an article and have an idea for a new campaign. None of these can wait for you to sit down at your dev machine, open Claude Code, find the right context, and start a session. By then, you've lost the thought or the urgency has passed.

Jam Session captures the thought in the moment and triages it into the system.

### How It Works

```
CAPTURE (mobile/voice)
    ↓
    Voice memo or text input
    ↓
TRANSCRIBE + TRIAGE
    ↓
    Understand the intent
    Classify priority: CRITICAL (execute now) vs MAINTENANCE (next cycle)
    Classify type: bug fix, new feature, new concept, metric question, feedback
    ↓
ROUTE
    ↓
    kh raw <item>     → Raw backlog dump (unprocessed thought)
    kh add <item>     → Small, clear item (skip breakdown, go to grooming)
    kh sc <item>      → Entire new concept (draft a System Config)
    kh query <metric> → Question about metrics (route to Monitoring)
    ↓
QUEUE
    ↓
    Item lands in .kh/jam/queue/ with priority stamp
    Monitoring picks it up on next poll
    If CRITICAL + system can self-serve → trigger immediate Executor session
    If MAINTENANCE → queue for next development cycle
```

### Priority Classification

| Priority | Meaning | Action |
|----------|---------|--------|
| **CRITICAL** | Production issue, revenue impact, user-facing bug | Trigger immediate local worker response if possible. Alert founder if human decision needed. |
| **HIGH** | Important but not breaking — new feature insight, significant UX issue | Queue for next available Executor session (same day) |
| **MAINTENANCE** | Nice-to-have, improvement idea, future concept | Queue for next development cycle / grooming session |
| **SEED** | Vague idea, hunch, "what if" thought | Store as Foundation Seed for next IMAGINATION cycle |

### Deliberate Jam Session (`kh jam-sesh <item>`)

Beyond passive capture, there's a deliberate mode: `kh jam-sesh` is an interactive breakdown session. Like `kh breakdown` but more conversational — it prompts for missing data by asking questions, explores the idea with you, and routes to the appropriate KH command when the item is sufficiently formed.

```
$ kh jam-sesh "I think we need a referral program"
> What's the goal? (more signups, revenue, retention?)
> "More signups"
> Who refers? (existing clients, partners, anyone?)
> "Existing clients"
> What's the incentive? (discount, credit, free service?)
> "Free month"
> This sounds like a new capability. Want me to draft an SC or add as a feature to an existing JM?
> "SC"
> Creating SC draft: referral-program...
```

### The Always-On Machine

Since the local development machine is always on and accessible, Jam Session items flow through the same local worker as Monitoring alerts. The machine is both the *listener* (monitoring prod) and the *responder* (executing fixes). Jam Session adds a third role: *receiver* (accepting founder input from anywhere).

Future: when Claude Code or equivalent can run on EC2 or cloud instances, the local machine constraint goes away. But the architecture doesn't change — the worker pattern (poll → evaluate → execute locally → deploy to prod) works the same whether "locally" means a laptop or a cloud VM.

### Buildability Tier: AFTER FEATURE

Jam Session requires: Monitoring Platform (to poll the queue), working Executor (to process items), and ideally a working SC Builder (to handle `kh sc` routing). It's a quality-of-life multiplier that makes the whole system more responsive, but it doesn't unlock new capabilities — it makes existing capabilities accessible from anywhere.

The voice capture component is the most uncertain piece. It needs: a mobile app (or shortcut) for recording, transcription (Whisper API or similar), and a way to push the transcribed text to the local machine's `.kh/jam/queue/`. Each of these is individually simple but the integration requires thought.

---

## 4. Roadmap — Tiered by Buildability

### Tier 1: BUILD NOW

| Item | What | Prerequisites |
|------|------|---------------|
| **SC Builder (intake-portal flavor)** | Generate JM(s) from System Config JSON. First flavor: marketing landing + intake + auth + client portal + admin portal. | Executor (working), Founder's Playbook stack (documented) |

### Tier 2: BUILD SOON

| Item | What | Prerequisites |
|------|------|---------------|
| **Monitoring Platform — Core** | Prometheus-inspired metrics collection, snapshot storage, local dashboard. First artifact generated by SC Builder as part of project bootstrap. | SC Builder (working), at least one deployed project to monitor |
| **Local Worker — Self-Healing** | Poll prod monitoring, emulate issues locally, fix via Executor, deploy to prod. | Monitoring Platform (core), Executor, deployment pipeline (SST) |

### Tier 3: BUILD LATER

| Item | What | Prerequisites |
|------|------|---------------|
| **Jam Session — Capture + Triage** | Voice/text input from mobile → transcribe → classify → route to KH commands. | Monitoring Platform (for queue polling), Executor (for processing) |
| **Jam Session — `kh jam-sesh`** | Interactive breakdown session via CLI. Conversational exploration of ideas with routing to `raw`/`add`/`sc`. | Executor breakdown/grooming flow (existing) |
| **SC Builder — Additional Flavors** | New flavors as patterns emerge: virtual-consultation, product-catalog, monitoring-dashboard. | SC Builder proven with intake-portal, at least one hand-built JM per flavor to extract patterns from |
| **Campaign Intelligence** | Monitoring worker that evaluates campaign performance and recommends next actions (new campaign, increase budget, pivot). | Monitoring Platform, external campaign API integrations |

### Tier 4: NORTH STAR

| Item | What | Prerequisites |
|------|------|---------------|
| **Orchestrator — INTENT** | Automated hypothesis scoring (feasibility × 0.4 + alignment × 0.6) with auto-approve/escalate/reject thresholds. | Foundation docs defined, Monitoring Platform providing real metrics for scoring |
| **Orchestrator — IMAGINATION** | LLM-driven hypothesis generation from Foundation + REFLECTION output. | INTENT working, enough historical data for meaningful REFLECTION |
| **Orchestrator — REFLECTION** | Automated trajectory analysis from Monitoring data. Completeness gating. AUGMENT/OPTIMIZE/PIVOT/CONTINUE recommendations. | Monitoring Platform with sufficient history, system completeness model |
| **Orchestrator — Full Loop** | Foundation → REFLECTION → IMAGINATION → INTENT → auto-SC generation → SC Builder → Executor → Monitoring → repeat. | All above components working and proven individually |
| **Forecast & Simulation** | Monte Carlo simulation of business scenarios grounded in real metrics. Variable sensitivity analysis. | Full Orchestrator, substantial historical data |
| **Product Config (PC)** | Multi-SC coordination: shared infrastructure, cross-journey data, unified auth across SACs. | Multiple working SCs deployed to the same product |

### The Progression

```
TODAY:     Executor (piecemeal) ─── manual everything
            ↓
TIER 1:    SC Builder ─── manual SC authoring, automated JM generation
            ↓
TIER 2:    Monitoring ─── real data flowing, self-healing capability
            ↓
TIER 3:    Jam Session ─── founder input from anywhere, campaign intelligence
            ↓
TIER 4:    Orchestrator ─── autonomous planning from Foundation to deployment
            ↓
NORTH STAR: One prompt → running business ─── the elusive one-and-done
```

Each tier makes the previous tier more powerful. The SC Builder benefits from Monitoring (real validation data). Monitoring benefits from Jam Session (founder can respond to alerts from anywhere). The Orchestrator benefits from all of them (real metrics for REFLECTION, real execution data for IMAGINATION calibration, real founder input for INTENT validation).

The north star — "one prompt to a running business" — is the asymptote. We'll get closer with each tier but may never fully arrive. That's fine. The value is in the journey, not the destination. Each tier independently delivers real capability, and each one shortens the gap between idea and execution.

---

## Historical References

| Artifact | Location | Significance |
|----------|----------|-------------|
| **v2 FOUNDATION.md** | `/archive/thousandhand_v2/FOUNDATION.md` | Complete five-loop orchestration specification |
| **v2 LAYER_ARTIFACTS.md** | `/archive/thousandhand_v2/LAYER_ARTIFACTS.md` | Data flow contracts between loops (ReflectionResult, Hypothesis, Task, ExecutionResult) |
| **v2 CLI_GUIDE.md** | `/archive/thousandhand_v2/CLI_GUIDE.md` | Command reference including `1kh forecast` simulation |
| **v2 TH_PRIMER** | `/archive/thousandhand_v2/TH_PRIMER.md` | Conceptual introduction to the ThousandHand approach |
| **v2 runner.py** | `/archive/thousandhand_v2/core/runner.py` | Cycle orchestration implementation (5-loop coordinator) |
| **v2 forecast.py** | `/archive/thousandhand_v2/core/forecast.py` | Simulation engine with Monte Carlo support |
| **v2→v3 Reflections** | `/archive/REFLECTIONS_FROM_v2_TO_v3.md` | Transition analysis — what worked, what didn't, what v3 needed to solve |
| **bix-v3 Cycle Report** | `/archive/bix-v3/.1kh/reports/cycle_003.html` | Dashboard prototype: North Star progress, component status, hypothesis scores, task outcomes, trajectory analysis, recommendations |
| **v3 ARCH_V3.md** | `/docs/ARCH_V3.md` | Current architecture — Executor-focused, journey-first development |
| **v3 SYSTEM_CONFIG.md** | `/docs/SYSTEM_CONFIG.md` | System Config and Product Config specification (SC Builder design) |
