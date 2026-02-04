# ThousandHand Foundation Document

**Version:** 0.1.0-draft
**Last Updated:** 2025-01-30
**Status:** Design Phase

---

## Table of Contents

1. [Overview](#1-overview)
2. [Core Philosophy](#2-core-philosophy)
3. [The Tree Model](#3-the-tree-model)
4. [Structured Input: The Initial Ceremony](#4-structured-input-the-initial-ceremony)
5. [The Four Loops](#5-the-four-loops)
6. [Workflow Types](#6-workflow-types)
7. [Key Data Structures](#7-key-data-structures)
8. [System Safeguards](#8-system-safeguards)
9. [Deployment Architecture](#9-deployment-architecture)
10. [The Starting Point: Initial Ceremony](#10-the-starting-point-initial-ceremony)
11. [Resolved Design Decisions](#11-resolved-design-decisions)
12. [Future Considerations](#12-future-considerations-out-of-scope-for-v01)

---

## 1. Overview

### What is ThousandHand?

ThousandHand (1KH) is an autonomous business-building system that:

- Takes high-level objectives and values as input
- Generates and validates hypotheses for achieving those objectives
- Builds, tests, and operates workflows that execute on those hypotheses
- Measures outcomes and adapts based on results
- Escalates to humans when blocked or uncertain

### The Core Promise

> "Give me your values and objectives. I will imagine paths forward, estimate what's feasible, build what's needed, measure what happens, and learn from the results. I will ask for help when I'm stuck, and I will never violate your values."

### What ThousandHand Is NOT

- **Not a chatbot**: It doesn't wait for instructions. It works autonomously toward objectives.
- **Not a simple automation tool**: It reasons about strategy, not just execution.
- **Not infallible**: It makes mistakes, but it learns and escalates appropriately.
- **Not a replacement for human judgment**: Critical decisions require human approval.

---

## 2. Core Philosophy

### 2.1 Epistemic Humility

The system knows what it doesn't know. It:

- Estimates confidence in its capabilities
- Recognizes when exploration is needed before building
- Pushes back when a path seems too costly or uncertain
- Asks questions rather than assuming

### 2.2 Bias Toward Action (With Guardrails)

The system favors doing over endless planning, but within bounds:

- Exploration has budgets and time-boxes
- Building happens only after validation
- Failure triggers learning, not just retry

### 2.3 Transparency Over Magic

The system explains its reasoning:

- Why it chose a particular hypothesis
- What assumptions it's making
- Where its confidence is low
- Why it's escalating

### 2.4 Values Are Inviolable

The Oracle (values) cannot be circumvented:

- No hypothesis that violates values will be pursued
- No shortcut that compromises principles will be taken
- The system will refuse and escalate rather than violate

---

## 3. The Tree Model

ThousandHand uses a tree metaphor to understand its state and progress.

```
                            ☀️ ENVIRONMENT
                         (market, timing, luck)
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────┐
    │                      🍎 FRUIT                           │
    │              (outcomes: revenue, leads, metrics)        │
    │                                                         │
    │         You observe this. You don't control it.         │
    │         Fruit is evidence, not a deliverable.           │
    └─────────────────────────────────────────────────────────┘
                                  ▲
                                  │
    ┌─────────────────────────────────────────────────────────┐
    │                    🌿 BRANCHES                          │
    │              (workflows, integrations)                  │
    │                                                         │
    │         You build these. They may or may not            │
    │         bear fruit. Some need pruning.                  │
    └─────────────────────────────────────────────────────────┘
                                  ▲
                                  │
    ┌─────────────────────────────────────────────────────────┐
    │                     🪵 TRUNK                            │
    │              (core platform: ThousandHand itself)       │
    │                                                         │
    │         The foundation. Stable. Everything              │
    │         grows from here.                                │
    └─────────────────────────────────────────────────────────┘
                                  ▲
                                  │
    ┌─────────────────────────────────────────────────────────┐
    │                     🌱 ROOTS                            │
    │              (Oracle + North Star)                      │
    │                                                         │
    │         Invisible but essential. Determines             │
    │         what the tree can become.                       │
    └─────────────────────────────────────────────────────────┘
                                  ▲
                                  │
                            🌍 SOIL
                    (resources: budget, time, skills)
```

### Tree Components Mapped to System

| Tree Part | System Equivalent | Description |
|-----------|-------------------|-------------|
| **Roots** | Oracle + North Star | Values and objectives that guide everything |
| **Trunk** | ThousandHand Core | The loops and infrastructure (built once) |
| **Branches** | Op Workflows | Active business operations |
| **Leaves** | Test Workflows | Health indicators for branches |
| **Fruit** | KPIs & Outcomes | What we measure (revenue, leads, etc.) |
| **Soil** | Context | Resources and constraints |
| **Environment** | Market Conditions | External factors we don't control |

### Key Insight

**You cultivate, you don't command.**

- You control: Roots (values), Soil (resources)
- You influence: Branches (what you build)
- You observe: Fruit (outcomes)
- You cannot control: Environment (market)

---

## 4. Structured Input: The Initial Ceremony

Before ThousandHand begins, human provides structured input. This is not a casual conversation—it's a deliberate ceremony that shapes everything.

### 4.1 Input Categories

#### ORACLE (Values & Principles)
> "Who are we? What do we stand for? What will we never do?"

- **Mutability**: Immutable. Changes require explicit "Oracle Amendment" with justification.
- **Purpose**: Absolute constraints. System will NEVER violate these.
- **Examples**:
  - "We are relationship-focused. No spam."
  - "We prioritize quality over speed."
  - "We don't mislead customers."

#### NORTH STAR (Objectives & Success Criteria)
> "What does success look like? By when? How will we measure it?"

- **Mutability**: Versioned. Can be revised with changelog and explicit approval.
- **Purpose**: The target the system works toward.
- **Requirements**: Must be measurable and time-bound.
- **Examples**:
  - "$10K MRR by month 6"
  - "50 paying customers by Q2"
  - "Launch MVP by March 15"

#### CONTEXT (Constraints & Resources)
> "What do we have? What can't we exceed?"

- **Mutability**: Dynamic. Updates as reality changes.
- **Purpose**: Bounds for decision-making.
- **Examples**:
  - "Budget: $500/month for tools"
  - "Time: 10 hours/week of human attention"
  - "Existing assets: Landing page, email list of 200"

#### SEEDS (Hypotheses & Hunches)
> "What do you think might work? What have you tried? What's your intuition?"

- **Mutability**: Consumed. Used once by IMAGINATION, then become hypotheses.
- **Purpose**: Starting points for exploration (NOT assumed truths).
- **Examples**:
  - "I think FB groups might be a good channel"
  - "We tried cold email before; it didn't work well"
  - "My hunch is that our audience prefers video content"

#### PREFERENCES (Soft Constraints)
> "What do you prefer, all else being equal?"

- **Mutability**: Adjustable anytime.
- **Purpose**: Influences decisions but doesn't dictate.
- **Examples**:
  - "I prefer email communication over phone calls"
  - "I'd rather move slowly and carefully than fast and risky"
  - "I like clean, minimal design"

### 4.2 Input Processing Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     STEP 1: RAW INPUT                               │
│                                                                     │
│  Human provides initial input (may be messy, contradictory)         │
│                                                                     │
└───────────────────────────────────────────────────────────────────┬─┘
                                                                    │
                                                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     STEP 2: CATEGORIZATION                          │
│                                                                     │
│  System (Claude) analyzes input and separates into:                │
│  • Oracle (values)                                                 │
│  • North Star (objectives)                                         │
│  • Context (constraints)                                           │
│  • Seeds (hypotheses to test)                                      │
│  • Preferences (soft constraints)                                  │
│                                                                     │
│  Also identifies:                                                  │
│  • Contradictions                                                  │
│  • Ambiguities                                                     │
│  • Unstated assumptions                                            │
│  • Missing information                                             │
│                                                                     │
└───────────────────────────────────────────────────────────────────┬─┘
                                                                    │
                                                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     STEP 3: CLARIFICATION                           │
│                                                                     │
│  System returns:                                                   │
│  • Proposed structure (here's how I understood your input)         │
│  • Questions (I need clarity on these points)                      │
│  • Concerns (these items seem to conflict)                         │
│                                                                     │
│  Human reviews, answers, adjusts.                                  │
│                                                                     │
└───────────────────────────────────────────────────────────────────┬─┘
                                                                    │
                                                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     STEP 4: VALIDATION                              │
│                                                                     │
│  System checks:                                                    │
│  • Oracle is internally consistent                                 │
│  • North Star is measurable and time-bound                         │
│  • Context is complete (no critical gaps)                          │
│  • Seeds don't violate Oracle                                      │
│                                                                     │
│  Returns: APPROVED or MORE QUESTIONS                               │
│                                                                     │
└───────────────────────────────────────────────────────────────────┬─┘
                                                                    │
                                                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     STEP 5: INITIALIZATION                          │
│                                                                     │
│  System begins IMAGINATION loop with Seeds as starting hypotheses  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 The Everything-Through-IMAGINATION Rule

**All human input enters as Seeds, not direct tasks.**

Even specific instructions like "build me an email sequence" go through IMAGINATION for validation:

- Does this align with Oracle?
- Does this serve North Star?
- Do we have capability?
- Is this the best approach?
- What assumptions does this make?

**Exception**: Human can flag "DIRECT TASK" to bypass, but system logs this as "bypassed validation."

---

## 5. The Four Loops

ThousandHand operates through four coordinated loops. These are infrastructure—built once, rarely changed.

### 5.1 Loop Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        IMAGINATION LOOP                             │
│                    (Planning & Feasibility)                         │
│                                                                     │
│  "Before we commit, let's imagine what it takes."                  │
│                                                                     │
│  • Generates hypothesis candidates                                 │
│  • Decomposes into requirements                                    │
│  • Estimates capability confidence                                 │
│  • Calculates viability                                            │
│  • Recommends path or escalates                                    │
│                                                                     │
└───────────────────────────────────────────────────────────────────┬─┘
                                                                    │
                                            Approved hypotheses     │
                                                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          INTENT LOOP                                │
│                    (Observation & Direction)                        │
│                                                                     │
│  "Given what we know, what should we focus on?"                    │
│                                                                     │
│  • Observes Tree State (branches, fruit)                           │
│  • Compares to North Star                                          │
│  • Assesses branch health                                          │
│  • Projects trajectory                                             │
│  • Decides: nurture, pivot, prune, or graft                        │
│  • Triggers DECAY for stale branches                               │
│                                                                     │
└───────────────────────────────────────────────────────────────────┬─┘
                                                                    │
                                            Strategic decisions     │
                                                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           WORK LOOP                                 │
│                       (Task Management)                             │
│                                                                     │
│  "Break decisions into actionable tasks."                          │
│                                                                     │
│  • Receives decisions from Intent                                  │
│  • Decomposes into tasks                                           │
│  • Assigns and prioritizes                                         │
│  • Tracks status and retries                                       │
│  • Manages escalation queue                                        │
│                                                                     │
└───────────────────────────────────────────────────────────────────┬─┘
                                                                    │
                                            Tasks ready             │
                                                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        EXECUTION LOOP                               │
│                       (Doing the Work)                              │
│                                                                     │
│  "Actually build, test, and explore."                              │
│                                                                     │
│  • Claims tasks from queue                                         │
│  • Executes via Claude Code                                        │
│  • Creates workflows (EXPLORE, TEST, OP)                           │
│  • Deploys as Temporal workflows                                   │
│  • Reports results                                                 │
│  • Updates Tree State and Capability Registry                      │
│                                                                     │
└───────────────────────────────────────────────────────────────────┬─┘
                                                                    │
                                            Tree State updated      │
                                                                    │
                                    ┌───────────────────────────────┘
                                    │
                                    ▼
                              ┌───────────┐
                              │  REPEAT   │──► Back to INTENT
                              └───────────┘    (or IMAGINATION if stuck)
```

### 5.2 IMAGINATION Loop (Detail)

**Purpose**: Plan before committing. Estimate feasibility. Push back if path is too costly.

**Triggers**:
- North Star exists but no path defined (first run)
- Existing paths hitting dead ends
- Human provides new Seeds
- INTENT requests new hypotheses

**Process**:

```
1. GENERATE HYPOTHESES
   Input: North Star, Tree State, Seeds
   Output: 3-5 hypothesis candidates

2. DECOMPOSE EACH HYPOTHESIS
   For each hypothesis:
   └── Break into specific requirements
       └── "To do X, we need: A, B, C, D"

3. ESTIMATE CONFIDENCE
   For each requirement:
   ├── Check Capability Registry
   ├── Note previous failures
   ├── Estimate effort if capability gap
   └── Flag unknowns

4. CALCULATE VIABILITY
   For each hypothesis:
   ├── Aggregate confidence scores
   ├── Count capability gaps
   ├── Estimate total effort
   └── Assess risk of cascading unknowns

5. DECIDE
   ├── Viability > 70% → Recommend proceeding
   ├── Viability 40-70% → Proceed but flag risks
   ├── Viability < 40% → Generate alternatives
   └── All paths low viability → ESCALATE to human
```

**Outputs**:
- Ranked hypothesis candidates with viability scores
- Capability gaps to explore
- Escalation requests (if needed)
- Recommended path forward

**Safeguards**:
- Exploration budget (max N explore tasks per hypothesis)
- Time-box (must produce actionable output within X hours)
- Bias toward action (after N explores, must BUILD or ABANDON)

### 5.3 INTENT Loop (Detail)

**Purpose**: Observe the tree. Make strategic decisions. Catch problems early.

**Triggers**:
- Scheduled (daily)
- Significant Tree State change
- EXECUTION reports major failure
- Human requests assessment

**Process**:

```
1. OBSERVE TREE STATE
   ├── Pull current branch inventory
   ├── Pull latest fruit data (KPIs)
   └── Check capability health

2. COMPARE TO NORTH STAR
   ├── Are we making progress?
   ├── Which branches are contributing?
   └── Project trajectory: "At current rate, we'll hit X by deadline"

3. ASSESS BRANCH HEALTH
   For each branch:
   ├── Expected fruit vs. actual fruit
   ├── Time since planted
   ├── Activity level
   └── Test pass rate

4. DECIDE
   For each branch:
   ├── HEALTHY → Continue nurturing
   ├── UNDERPERFORMING → Consider pivot
   ├── FAILING → Consider prune
   └── STALE → Trigger DECAY

5. CHECK TRAJECTORY
   ├── On track → Continue
   ├── Behind but recoverable → Flag, continue
   ├── Significantly behind → ESCALATE with options
   └── Impossible → ESCALATE urgently

6. EMIT DECISIONS
   └── Strategic decisions to WORK loop
```

**Outputs**:
- Branch assessments
- Decisions (nurture, pivot, prune, graft)
- Trajectory analysis
- Escalations (if off-track)

**Safeguards**:
- Early warning escalation ("We're 60% through time but 20% to goal")
- Trajectory analysis, not just snapshot
- DECAY mechanism for stale branches

### 5.4 WORK Loop (Detail)

**Purpose**: Translate strategic decisions into actionable tasks. Track progress.

**Triggers**:
- Receives decisions from INTENT
- Receives approved hypotheses from IMAGINATION
- Tasks change status (complete, fail, blocked)

**Process**:

```
1. RECEIVE DECISION
   ├── "Build branch X"
   ├── "Explore capability Y"
   ├── "Prune branch Z"
   └── etc.

2. DECOMPOSE INTO TASKS
   Decision → Tasks
   ├── EXPLORE tasks (research, discovery)
   ├── BUILD tasks (create OP workflows)
   ├── TEST tasks (create TEST workflows)
   └── PRUNE tasks (archive/remove)

3. ASSIGN AND PRIORITIZE
   ├── Check dependencies
   ├── Estimate effort
   ├── Assign priority
   └── Place in queue

4. TRACK STATUS
   ├── PENDING → waiting for execution
   ├── IN_PROGRESS → being worked
   ├── COMPLETED → done successfully
   ├── FAILED → error occurred
   └── BLOCKED → needs human input

5. MANAGE RETRIES
   ├── Failure + retries < max → Re-queue
   ├── Failure + retries >= max → BLOCKED
   └── Update Capability Registry on repeated failures

6. MANAGE ESCALATIONS
   ├── Categorize: BLOCKING vs. ADVISORY vs. FYI
   ├── Batch similar escalations
   ├── Apply defaults if human doesn't respond in X time
   └── Respect escalation budget (max N blocking per week)
```

**Outputs**:
- Task Queue
- Status updates to INTENT
- Escalation queue to human

**Safeguards**:
- Escalation tiers (prevent fatigue)
- Escalation batching (daily digest, not constant interrupts)
- Default behaviors (if no response in X time, assume Y)
- Escalation budget (max N blocking per week)

### 5.5 EXECUTION Loop (Detail)

**Purpose**: Actually do the work. Create artifacts. Update state.

**Triggers**:
- Tasks available in queue

**Process**:

```
1. CLAIM TASK
   └── Pull highest priority task from queue

2. PREPARE
   ├── Load relevant context
   ├── Select execution method:
   │   ├── EXPLORE → Claude API (research)
   │   ├── BUILD → Claude Code (create workflows)
   │   ├── TEST → Claude Code (create test workflows)
   │   └── PRUNE → Temporal API (archive/delete)
   └── Load relevant prompts/templates

3. EXECUTE
   ├── Invoke Claude Code / Claude API
   ├── Create artifacts (workflows, documents, code)
   └── Capture output

4. VALIDATE
   ├── Check artifact structure
   ├── Run tests if applicable
   └── Verify against requirements

5. DEPLOY (if BUILD/TEST)
   ├── Deploy workflow to Temporal Cloud
   ├── Activate if tests pass
   └── Record in Tree State

6. REPORT
   ├── Update task status
   ├── Update Tree State (new branch, new capability)
   ├── Update Capability Registry (success/failure)
   └── Emit events for INTENT to observe
```

**Outputs**:
- Temporal workflows (deployed and active)
- Artifacts in /thousandhand
- Updated Tree State
- Updated Capability Registry

**Safeguards**:
- Validation before deployment
- Capability Registry feedback (failures update confidence)
- Logging for debugging

---

## 6. Workflow Types

Workflows are the dynamic outputs created by the EXECUTION loop. They are implemented as Temporal workflows.

### 6.1 Workflow Type Summary

| Type | Purpose | Created When | Created By |
|------|---------|--------------|------------|
| **META** | System observation, coordination | Early (often manual) | Human or Claude Code |
| **EXPLORE** | Research, discovery, learning | When knowledge is needed | Claude Code |
| **TEST** | Validate that OP workflows work | Before OP deployment | Claude Code |
| **OP** | Actual business operations | When building branches | Claude Code |

### 6.2 META Workflows

**Purpose**: Observe and coordinate the system itself.

**Examples**:
- `pull-daily-analytics`: Gather KPI data from various sources
- `assess-tree-health`: Calculate branch health scores
- `notify-human`: Send escalations via email/Slack

**Characteristics**:
- Often built early, manually
- Rarely change once working
- Support the loops, not the business directly

### 6.3 EXPLORE Workflows

**Purpose**: Research and discover before building.

**Examples**:
- `research-fb-marketing`: Deep dive on Facebook outreach strategies
- `user-interview-synthesis`: Analyze interview transcripts for insights
- `competitor-analysis`: Understand what competitors are doing

**Characteristics**:
- Created when IMAGINATION needs more information
- Time-boxed (must produce output within X hours)
- Output feeds back into hypothesis refinement

### 6.4 TEST Workflows

**Purpose**: Validate that OP workflows function correctly.

**Examples**:
- `test-email-sequence`: Verify emails send with correct content
- `test-payment-flow`: Confirm Stripe integration works
- `test-lead-capture`: Check that form submissions are recorded

**Characteristics**:
- Created alongside OP workflows
- Run before deployment
- Run periodically to catch regressions

### 6.5 OP Workflows (Operational)

**Purpose**: Perform actual business operations.

**Examples**:
- `email-nurture-sequence`: Send onboarding emails to new leads
- `stripe-payment-handler`: Process incoming payments
- `lead-capture-webhook`: Record form submissions
- `social-post-scheduler`: Publish content on schedule

**Characteristics**:
- The "branches" of the tree
- What actually generates fruit (outcomes)
- Created by Claude Code, deployed as Temporal workflows

---

## 7. Key Data Structures

### 7.1 Tree State

The current state of the entire system.

```json
{
  "tree_id": "thousandhand-biz-001",
  "assessed_at": "2025-01-30T10:00:00Z",

  "roots": {
    "oracle_version": "v1.0",
    "north_star_version": "v1.0",
    "health": "strong"
  },

  "trunk": {
    "core_systems": ["auth", "billing", "notifications"],
    "health": "stable"
  },

  "branches": [
    {
      "branch_id": "branch-001",
      "name": "Email Nurture Funnel",
      "hypothesis_id": "hyp-001",
      "workflows": ["email-capture", "email-nurture-sequence"],
      "status": "active",
      "health": "healthy",
      "planted_at": "2025-01-15",
      "expected_fruit": {"leads_per_month": 50, "conversion_rate": 0.10},
      "actual_fruit": {"leads_per_month": 47, "conversion_rate": 0.08},
      "last_fruit_check": "2025-01-30"
    }
  ],

  "fruit_summary": {
    "period": "last_30_days",
    "total_revenue": 1500,
    "total_leads": 94,
    "north_star_progress": "15% toward $10K MRR"
  },

  "soil": {
    "budget_remaining": 3500,
    "api_credits_remaining": 8000,
    "human_hours_available_weekly": 10
  }
}
```

### 7.2 Capability Registry

What the system knows how to do (and how confident it is).

```json
{
  "capabilities": [
    {
      "id": "cap-001",
      "name": "Create Temporal workflow",
      "confidence": 0.95,
      "proven_by": ["workflow-001", "workflow-002"],
      "last_validated": "2025-01-28",
      "notes": "Standard capability, well-tested"
    },
    {
      "id": "cap-002",
      "name": "Send email via SendGrid",
      "confidence": 0.85,
      "proven_by": ["workflow-email-nurture"],
      "last_validated": "2025-01-25",
      "notes": "Working, but API key expires in 30 days"
    },
    {
      "id": "cap-003",
      "name": "Post to Facebook programmatically",
      "confidence": 0.20,
      "proven_by": [],
      "attempted": ["task-fb-001"],
      "failure_notes": "API requires app review, limited access",
      "workarounds": ["Manual posting", "Buffer integration"]
    }
  ],

  "decay_policy": {
    "unused_days_before_confidence_decay": 30,
    "decay_rate_per_month": 0.10
  }
}
```

### 7.3 Hypothesis

A testable belief about how to achieve North Star.

```json
{
  "hypothesis_id": "hyp-001",
  "statement": "Inbound content marketing will generate qualified leads",
  "north_star_ref": "NS-10k-mrr",
  "oracle_alignment": ["relationship-focused", "no-spam"],

  "expected_outcomes": {
    "leads_per_month": 50,
    "conversion_rate": 0.10,
    "revenue_per_customer": 200,
    "expected_mrr_contribution": 1000
  },

  "minimum_viable_outcome": {
    "leads_per_month": 10,
    "note": "At least 10 leads proves concept"
  },

  "requirements": [
    {"id": "req-1", "description": "Landing page", "capability_confidence": 0.90},
    {"id": "req-2", "description": "Email capture form", "capability_confidence": 0.85},
    {"id": "req-3", "description": "Nurture email sequence", "capability_confidence": 0.80},
    {"id": "req-4", "description": "Content creation", "capability_confidence": 0.75}
  ],

  "viability_score": 0.82,
  "status": "BUILDING",

  "experiment_start": "2025-01-15",
  "experiment_duration_days": 30,
  "current_pivot": 0,
  "max_pivots": 3
}
```

### 7.4 Task

A unit of work to be executed.

```json
{
  "task_id": "task-001",
  "type": "BUILD",
  "description": "Create email nurture sequence workflow",
  "hypothesis_id": "hyp-001",
  "branch_id": "branch-001",

  "requirements": [
    "Send welcome email immediately after signup",
    "Send value email 2 days later",
    "Send offer email 5 days later"
  ],

  "assigned_to": "execution-worker-01",
  "status": "PENDING",
  "priority": 1,

  "retry_count": 0,
  "max_retries": 3,

  "dependencies": ["task-000"],

  "created_at": "2025-01-30T09:00:00Z",
  "started_at": null,
  "completed_at": null
}
```

### 7.5 Escalation

A request for human input.

```json
{
  "escalation_id": "esc-001",
  "tier": "BLOCKING",
  "source_loop": "IMAGINATION",

  "summary": "All paths to North Star have low viability",

  "context": {
    "north_star": "$10K MRR by month 6",
    "hypotheses_evaluated": 5,
    "best_viability_score": 0.35
  },

  "options": [
    {
      "id": "opt-a",
      "description": "Extend timeline to 9 months",
      "recommendation": true,
      "rationale": "More time to build capabilities"
    },
    {
      "id": "opt-b",
      "description": "Reduce target to $5K MRR",
      "recommendation": false,
      "rationale": "May not be viable long-term"
    },
    {
      "id": "opt-c",
      "description": "Invest in capability development (hire, buy tools)",
      "recommendation": false,
      "rationale": "Exceeds current budget"
    }
  ],

  "default_if_no_response": "opt-a",
  "default_after_hours": 48,

  "created_at": "2025-01-30T10:00:00Z",
  "responded_at": null,
  "response": null
}
```

---

## 8. System Safeguards

Protections against common failure modes.

### 8.1 Runaway Junk Prevention (DECAY Mechanism)

**Problem**: System creates workflows faster than it cleans up.

**Solution**: DECAY mechanism in INTENT loop.

```
DECAY Rules:
├── Branch inactive > 14 days → FLAG for review
├── Branch inactive > 30 days → AUTO-PRUNE (archive, deactivate)
├── Workflow never tested > 7 days → FLAG
├── Failed hypothesis not retired > 7 days → FLAG
└── Orphaned workflows (no branch) → AUTO-PRUNE
```

### 8.2 Infinite Exploration Trap Prevention

**Problem**: System keeps researching, never building.

**Solution**: Exploration budgets and time-boxes.

```
Exploration Limits:
├── Max EXPLORE tasks per hypothesis: 3
├── Max EXPLORE duration per task: 4 hours
├── After 3 explores, must: BUILD, PIVOT, or ABANDON
└── Total exploration time per hypothesis: 12 hours max
```

### 8.3 Stale Capability Prevention

**Problem**: Confidence scores based on past success, but capabilities can rot.

**Solution**: Capability health checks and decay.

```
Capability Health:
├── Last validated > 30 days → Confidence decays 10%
├── Last validated > 60 days → Confidence decays 25%
├── Runtime failure → Immediate confidence reduction
└── Periodic health check workflows for critical capabilities
```

### 8.4 North Star Drift Prevention

**Problem**: System makes tactical progress but misses strategic goal.

**Solution**: Trajectory analysis in INTENT loop.

```
Trajectory Analysis:
├── Daily: Compare actual progress vs. required pace
├── Calculate: "At current rate, we'll reach X% of goal by deadline"
├── Thresholds:
│   ├── On track (>80% projected) → Continue
│   ├── Behind (50-80% projected) → Flag, continue
│   ├── Significantly behind (25-50% projected) → ESCALATE
│   └── Critical (<25% projected) → URGENT ESCALATE
└── Include in every human digest
```

### 8.5 Escalation Fatigue Prevention

**Problem**: Too many escalations, human ignores them.

**Solution**: Tiers, batching, defaults, budgets.

```
Escalation Management:
├── Tiers:
│   ├── BLOCKING: Requires response, system waits
│   ├── ADVISORY: Wants input, has default if no response
│   └── FYI: Informational only, no response needed
├── Batching: Daily digest for ADVISORY and FYI
├── Defaults: Each escalation specifies default action if no response in X hours
└── Budget: Max 3 BLOCKING escalations per week (forces system to decide more autonomously)
```

### 8.6 Competency Trap Prevention

**Problem**: System only does what it's confident in, never develops new capabilities.

**Solution**: Exploration quotas and strategic capability development.

```
Capability Development:
├── Exploration quota: 20% of effort must go to low-confidence capabilities
├── Strategic gap analysis: "North Star requires X, we must learn X"
├── Discomfort budget: 1 high-risk exploration per week minimum
└── Learning reflection: Every failed capability attempt → documented learnings
```

### 8.7 Hypothesis Learning

**Problem**: System prunes branches but doesn't learn WHY hypotheses failed.

**Solution**: Hypothesis postmortems and pattern registry.

```
Hypothesis Learning:
├── On hypothesis retire: Generate postmortem
│   ├── What was the hypothesis?
│   ├── What actually happened?
│   ├── Why did it fail? (execution vs. assumption)
│   └── What should we learn?
├── Pattern Registry: Track hypothesis-level patterns
│   ├── "Cold outreach hypotheses have 80% failure rate"
│   ├── "Content marketing takes >60 days to show results"
│   └── etc.
└── Feed patterns back to IMAGINATION priors
```

---

## 9. Deployment Architecture

### 9.1 High-Level Architecture (Temporal-Only)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Cloud Layer                                 │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    Temporal Cloud                            │  │
│   │                                                             │  │
│   │   ORCHESTRATION (Loop Workflows):                           │  │
│   │   ├── IMAGINATION Loop (Temporal Workflow)                  │  │
│   │   ├── INTENT Loop (Temporal Workflow)                       │  │
│   │   ├── WORK Loop (Temporal Workflow)                         │  │
│   │   └── Activity Queue                                        │  │
│   │                                                             │  │
│   │   EXECUTION (Business Workflows):                           │  │
│   │   ├── META workflows (system observation)                   │  │
│   │   ├── EXPLORE workflows (research)                          │  │
│   │   ├── TEST workflows (validation)                           │  │
│   │   └── OP workflows (business operations)                    │  │
│   │                                                             │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ Workers poll for activities
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Local Layer (Your Mac)                      │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    Temporal Worker                           │  │
│   │                                                             │  │
│   │   Executes activities:                                      │  │
│   │   ├── generate_hypotheses() → Claude API                    │  │
│   │   ├── estimate_confidence() → Claude API                    │  │
│   │   ├── execute_build_task() → Claude Code                    │  │
│   │   └── deploy_workflow() → Temporal Cloud API                │  │
│   │                                                             │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                      Claude Code                             │  │
│   │                                                             │  │
│   │   Actually creates files, runs commands, builds artifacts   │  │
│   │   (using --dangerously-skip-permissions for autonomy)       │  │
│   │                                                             │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    /1KH                                      │  │
│   │                                                             │  │
│   │   Local workspace for artifacts, configs, state             │  │
│   │                                                             │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Repository Structure

```
github.com/paul/1KH/
├── docs/
│   └── FOUNDATION.md              ← This document
│
├── temporal/
│   ├── workflows/
│   │   ├── loops/
│   │   │   ├── imagination_loop.py    ← Orchestration workflow
│   │   │   ├── intent_loop.py
│   │   │   └── work_loop.py
│   │   └── business/
│   │       ├── meta/                  ← META workflow definitions
│   │       ├── explore/               ← EXPLORE workflow definitions
│   │       ├── test/                  ← TEST workflow definitions
│   │       └── op/                    ← OP workflow definitions
│   ├── activities/
│   │   └── activities.py          ← Activities (Claude API, Temporal API calls)
│   └── workers/
│       └── local_worker.py        ← Runs on your Mac
│
├── schemas/
│   ├── tree_state.json
│   ├── capability_registry.json
│   ├── hypothesis.json
│   ├── task.json
│   └── escalation.json
│
├── prompts/
│   ├── imagination/
│   │   ├── generate_hypotheses.md
│   │   └── estimate_confidence.md
│   ├── execution/
│   │   ├── build_workflow.md
│   │   └── explore.md
│   └── intent/
│       └── assess_tree.md
│
├── state/                         ← Local state storage
│   ├── tree_state.json
│   ├── capability_registry.json
│   └── escalations/
│
├── artifacts/                     ← Created by Claude Code
│   ├── workflows/
│   ├── documents/
│   └── code/
│
└── archive/                       ← Previous implementations
```

### 9.3 Execution Flow Example

```
1. IMAGINATION Loop (Temporal Cloud) generates hypotheses
   └── Calls activity: generate_hypotheses()

2. Temporal Worker (Your Mac) picks up activity
   └── Calls Claude API with imagination prompts
   └── Returns hypothesis candidates to Temporal

3. IMAGINATION Loop evaluates, recommends, passes to INTENT

4. INTENT Loop makes strategic decision: "Build email funnel"
   └── Emits decision to WORK Loop

5. WORK Loop decomposes into tasks:
   └── Task 1: BUILD email-capture workflow
   └── Task 2: BUILD email-nurture workflow
   └── Task 3: TEST email flow

6. EXECUTION (via Temporal Worker) picks up Task 1:
   └── Invokes Claude Code: "Create email capture workflow"
   └── Claude Code generates workflow definition
   └── Worker deploys workflow to Temporal Cloud
   └── Worker reports success to WORK Loop

7. WORK Loop updates task status, INTENT observes new branch

8. META workflow (Temporal Cloud) runs on schedule:
   └── Pulls analytics
   └── Updates Tree State

9. INTENT Loop observes fruit data
   └── Decides branch is healthy
   └── Cycle continues
```

---

## 10. The Starting Point: Initial Ceremony

Before any loops run or workflows exist, there must be a structured onboarding process. This happens via CLI and is **real-time and interactive**.

### 10.1 The Eight Phases of Initialization

```
PHASE 0: AWAKENING
└── Human launches: $ 1kh init

PHASE 1: GROUNDING
└── "Where should this project live?"
└── Scaffold directory structure
└── Create .1kh/.env template

PHASE 1.5: KEYS (Deterministic - No AI Required)
└── Show status table of required vs optional keys
└── Prompt for Anthropic API key (required for all intelligent behavior)
└── Show file location: .1kh/.env
└── Mention user can edit file directly
└── Optionally collect Temporal Cloud keys (can add later)
└── Gate: Cannot proceed to Phase 2 without ANTHROPIC_API_KEY

PHASE 2: LISTENING
└── "Tell me what you want to build."
└── Capture raw, unstructured input
└── (Requires Claude for intelligent responses)

PHASE 3: PROBING
└── Ask clarifying questions (iterative)
└── Push for specificity on values, objectives, constraints
└── Surface hidden assumptions

PHASE 4: STRUCTURING
└── Present categorized understanding
└── Oracle, North Star, Context, Seeds, Preferences
└── Human reviews, edits, confirms

PHASE 5: COMMITTING
└── Write foundation documents to project
└── oracle.md, north-star.md, context.md
└── .1kh/seeds.json, .1kh/preferences.json

PHASE 6: CONNECTING
└── Validate existing API key connections
└── Collect optional integrations (SendGrid, Twilio, etc.)
└── Test connections where possible

PHASE 7: IGNITING
└── Deploy loops to Temporal Cloud
└── Create initial META workflows
└── Begin IMAGINATION loop
└── Confirm communication channel for first update
```

**Why Phase 1.5 exists:** The Anthropic API key is required for any intelligent behavior. Without it, Phases 2-4 cannot function. By collecting it early (deterministically, no AI needed), we ensure the ceremony can proceed smoothly. The user is also informed they can edit `.1kh/.env` directly if they prefer.

### 10.2 Sparse Input Handling

If human provides vague input ("just make me money"), the system must **probe harder**:

- Present extreme scenarios to surface values ("Would you be okay with X?")
- Offer concrete examples to anchor abstract goals ("What does 'serious money' mean—$100/mo or $10,000?")
- Set minimum thresholds for proceeding (must have: 1 measurable objective, 1 value statement, 1 time constraint)

The system should **bias toward asking more questions upfront** rather than guessing and building wrong things.

---

## 11. Resolved Design Decisions

Based on initial design discussions, the following decisions are **resolved** (not open):

### 11.1 Human Interface

| Question | Decision |
|----------|----------|
| How does human receive escalations? | **Configurable per user preference.** Initial implementation: CLI + Email. Future: SMS, Slack, Dashboard. This is set during Phase 6 (Connecting). |
| How does human approve/respond? | **CLI for initial ceremony (real-time required).** Async responses via configured channel (email reply, SMS, CLI command). |
| How real-time does communication need to be? | **Initial Ceremony: Real-time (CLI).** Ongoing: Async with configurable urgency. BLOCKING escalations may warrant SMS; ADVISORY can be daily email digest. |

### 11.2 State Persistence

| Question | Decision |
|----------|----------|
| Where does Tree State live? | **Temporal for coordination state. Database (cloud) for persistent data.** Not local files—system should not depend solely on local machine. |
| State conflicts between loops? | **Optimistic locking with grace period.** See PRUNE_PENDING pattern below. Each loop operates on its own schedule; state mutations are atomic activities. |

#### State Conflict Resolution: PRUNE_PENDING Pattern

When INTENT decides to prune a branch while EXECUTION has in-flight work:

```
INTENT decides to prune branch "fb-outreach"
         │
         ▼
Check: Any IN_PROGRESS tasks for this branch?
         │
    ┌────┴────┐
    │         │
   Yes        No
    │         │
    ▼         ▼
Set status:   Set status:
PRUNE_PENDING PRUNED
    │              │
    │              └──► Archive workflows immediately
    │
    ▼
Wait for IN_PROGRESS tasks (max 24 hours)
    │
    ├── Task completes successfully
    │   └── Re-evaluate: Check fruit again
    │       ├── Still no fruit → PRUNE
    │       └── Now has fruit → Cancel prune, set HEALTHY
    │
    └── Task fails
        └── PRUNE (no loss—work failed anyway)
```

**Why this matters:** Prevents discarding hours of work on a "final attempt" that might succeed. If the last effort produces fruit, the prune is canceled.

```json
// Branch status with PRUNE_PENDING
{
  "branch_id": "branch-fb-outreach",
  "status": "PRUNE_PENDING",
  "prune_reason": "No fruit for 30 days",
  "prune_blocked_by": ["task-fb-dm-sender"],
  "prune_deadline": "2025-02-01T10:00:00Z",
  "prune_cancel_condition": "any_fruit_detected"
}
```
| Backup and recovery? | **Git for source artifacts (workflows, configs). Temporal for execution history. Database backups for state.** Workflows are JSON—version controlled in project repo before deployment. |

### 11.3 Multi-Business Support

| Question | Decision |
|----------|----------|
| Can one 1KH instance support multiple businesses? | **Yes, as separate "Trees."** Each project is a Tree with its own Oracle, North Star, and branches. |
| How are Trees isolated? | **By project directory and Temporal namespace.** Each `1kh init` creates a separate tree. Cross-tree dependencies are explicit integrations. |
| Shared capabilities across businesses? | **Via a COMPONENTS repository (future).** Cross-cutting concerns (Finance, Marketing, IT) become shared services. A Tree can "subscribe" to another Tree's capabilities. This enables the network topology you described. **Note: This is out of scope for v0.1 but architecturally planned.** |

### 11.4 Security

| Question | Decision |
|----------|----------|
| How are API keys managed? | **Local: `.1kh/.env` (gitignored).** Production: Environment-specific config. Keys passed to Temporal workflows via activities at deployment time. **Pin for later: Enterprise key management (Vault, etc.)** |
| How is Claude Code sandboxed? | **Configurable policy.** Default: `--dangerously-skip-permissions` for autonomy. Option: Policy-based approval (allow specific paths, commands). User selects during setup. |
| Blast radius of runaway workflow? | **Managed by safeguards in Section 8.** Thresholds are configurable. Breaking changes to thresholds = 1KH version change. **Note: Backward compatibility of 1KH versions with existing Trees is a future concern—document migration path when needed.** |

### 11.5 Observability

| Question | Decision |
|----------|----------|
| How do we debug? | **For v0.1: Structured logging to files + Temporal's built-in visibility.** Future: Dedicated observability (Datadog, custom dashboard). The "black box" philosophy applies—human should trust outputs, not micromanage process. Logs exist for debugging failures, not surveillance. |
| Logging strategy? | **Log decisions, not mechanics.** Each loop logs: what it decided, why, confidence level. EXECUTION logs: what was attempted, result. Avoid logging every API call—focus on meaningful state changes. |
| Alerting? | **Escalations ARE the alerts.** System health issues become BLOCKING escalations. No separate alerting system for v0.1. If loops fail to run, Temporal's own monitoring catches this. |

#### The "Black Box with X-Ray" Model

```
Philosophy:
──────────────────────────────────────────────────────────────────────────────

• Default to BLACK BOX: Human sees inputs (Oracle, Seeds) and outputs (Fruit)
• X-RAY ON DEMAND: When something fails, human can inspect that specific failure
• NO SURVEILLANCE: Logs exist for debugging, not monitoring every move
• TRUST PROGRESSION: Over time, human checks less, trusts more

Observability Stack (v0.1):
──────────────────────────────────────────────────────────────────────────────

1. DECISION LOG (the "what and why")
   ├── Every loop writes structured decisions
   ├── Format: timestamp, loop, decision, reasoning, confidence
   ├── Storage: .1kh/logs/decisions/ (append-only)
   └── Query: `1kh logs decisions --since=yesterday`

2. TEMPORAL VISIBILITY (the "execution trace")
   ├── Built-in UI showing workflow executions
   ├── Activity attempts, retries, failures with stack traces
   ├── This is the "X-ray" for debugging
   └── No extra work—comes free with Temporal Cloud

3. ESCALATIONS AS ALERTS (the "system talks to you")
   ├── System health issues → BLOCKING escalation
   ├── Example: "INTENT loop failed 3 times. Investigate."
   └── Human investigates via Temporal UI or logs

4. FRUIT SUMMARY (the "outcomes")
   ├── META workflow generates daily summary
   ├── Sends: "Yesterday: 5 leads, $0 revenue, 2 branches active"
   └── Human cares about THIS, not internals

Trust Progression:
──────────────────────────────────────────────────────────────────────────────

Day 1-30:    Human checks logs frequently, validates outputs
Day 30-90:   Human checks logs when something seems off
Day 90+:     Human trusts outputs, only investigates failures
Eventually:  Black box with occasional X-ray
```

### 11.6 Versioning (Point-and-Shoot Deployments)

| Question | Decision |
|----------|----------|
| How do we version workflows? | **Every workflow change = new version.** Workflow definitions stored in git. Deployed versions tagged. Multiple versions can be LIVE simultaneously. |
| Rollback strategy? | **DNS-based routing between versions.** See PSD (Point-and-Shoot Deployment) model below. |
| Schema breaking changes? | **Workflow schemas: Migration scripts when needed.** System DB schemas: Standard migration practices. 1KH core schemas: Versioned, backward-compatible where possible. |

#### Point-and-Shoot Deployment (PSD) Model

```
Version Lifecycle:
──────────────────────────────────────────────────────────────────────────────

v2.3.12 ──► ARCHIVED (was previous-stable)
v2.3.13 ──► ARCHIVED
v2.3.14 ──► ARCHIVED
v2.3.15 ──► PREVIOUS-STABLE (rollback target)
v2.3.16 ──► LIVE (being tested)
v2.3.17 ──► LIVE (being tested)
v2.3.18 ──► CURRENT-STABLE ◄── DNS points here (end users see this)
v2.3.19 ──► LIVE (just deployed, under QA)
v2.3.20 ──► LIVE (in development)

Operations:
──────────────────────────────────────────────────────────────────────────────

DEPLOY: Create new version, mark LIVE, available for testing
ROLLFORWARD: Mark a LIVE version as CURRENT-STABLE, archive versions below PREVIOUS-STABLE
ROLLBACK: Point DNS to PREVIOUS-STABLE (instant, no deployment)
REJECT: Mark CURRENT-STABLE as rejected, PREVIOUS-STABLE becomes both

Constraints:
──────────────────────────────────────────────────────────────────────────────

• ~8-10 LIVE versions max (configurable)
• Enables parallel development and testing in production
• Higher infrastructure cost—may not suit bootstrap budgets
• Simplified mode for v0.1: Just CURRENT and PREVIOUS (2 versions)
```

#### PSD Maturity Levels

The PSD model scales with your needs. Architecture supports all levels from day 1; you choose what to activate.

```
LEVEL 0: BOOTSTRAP (Default for v0.1)
──────────────────────────────────────────────────────────────────────────────
Versions:     1 (just CURRENT)
Rollback:     Manual (redeploy previous commit)
Testing:      Local or staging environment
Use case:     Solo founder, proving concept, minimal budget
Cost:         Lowest
Complexity:   Lowest
Risk:         Highest (no instant rollback)


LEVEL 1: SAFE (Recommended once you have users)
──────────────────────────────────────────────────────────────────────────────
Versions:     2 (CURRENT-STABLE + PREVIOUS-STABLE)
Rollback:     Instant (DNS switch)
Testing:      Can test new version before promoting
Use case:     Small team, real users, need safety net
Cost:         2x resources
Complexity:   Low
Risk:         Low (instant rollback)


LEVEL 2: AGILE (For active development teams)
──────────────────────────────────────────────────────────────────────────────
Versions:     4-6 (CURRENT, PREVIOUS, + 2-4 LIVE development)
Rollback:     Instant
Testing:      QA validates specific versions in production
Use case:     Dev team pushing multiple features, parallel testing
Cost:         4-6x resources
Complexity:   Medium
Risk:         Low


LEVEL 3: EXPERIMENTAL (For optimization and growth)
──────────────────────────────────────────────────────────────────────────────
Versions:     8-10+ (CURRENT, PREVIOUS, LIVE dev, + experiment variants)
Rollback:     Instant
Testing:      Full production testing
Experiments:  Multi-variant testing (beyond A/B)
              Route users based on: segment, geography, random, feature flags
Use case:     Mature product, optimizing conversion, running experiments
Cost:         8-10x resources
Complexity:   High (routing logic, per-variant analytics)
Risk:         Low (but complexity risk)
```

#### PSD Configuration

```yaml
# .1kh/config.yaml

deployment:
  psd_level: 0  # 0=bootstrap, 1=safe, 2=agile, 3=experimental

  # Level 1+ settings
  max_live_versions: 2
  auto_archive_after_days: 7

  # Level 3 settings (ignored if level < 3)
  experiments:
    enabled: false
    max_concurrent: 0
    routing_strategy: "random"  # or "segment", "geography", "feature_flag"
```

To level up:
```bash
$ 1kh config set deployment.psd_level 1
# System provisions additional infrastructure
# Next deploy creates PREVIOUS-STABLE slot
```

---

## 12. Future Considerations (Out of Scope for v0.1)

Documented for architectural awareness, not immediate implementation.

### 12.1 Components Repository

A separate repository of reusable solutions:
- Cross-cutting concerns: Finance, Marketing, Legal, HR, IT
- Plug into one project or span multiple
- Searchable, versioned, composable
- Enables "subscribe to capability" model

### 12.2 Tree Networks

When Trees depend on each other:
- Service Trees (provide capabilities to other Trees)
- Consumer Trees (use capabilities from Service Trees)
- Circular dependencies possible (Marketing Tree serves Product Tree which serves Marketing Tree)
- Requires dependency resolution and health propagation

### 12.3 Enterprise Features

- Centralized key management (Vault)
- SSO for human interface
- Audit logging for compliance
- Multi-tenant hosting
- Custom observability integrations

### 12.4 1KH Self-Evolution

- How does 1KH update itself?
- Backward compatibility with existing Trees
- Migration tooling for schema changes
- Versioned 1KH core vs. versioned Tree artifacts

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Oracle** | Immutable values and principles that the system will never violate |
| **North Star** | Measurable, time-bound objectives the system works toward |
| **Tree State** | Current state of all branches, fruit, and system health |
| **Tree** | A complete project instance with its own Oracle, North Star, and branches |
| **Branch** | A set of workflows pursuing a specific hypothesis |
| **Fruit** | Measurable outcomes (KPIs, revenue, leads) |
| **Capability** | Something the system knows how to do, with confidence score |
| **Hypothesis** | A testable belief about how to achieve North Star |
| **Seeds** | Human hunches/ideas that become initial hypotheses |
| **Loop** | Long-running coordination process (part of 1KH infrastructure) |
| **Workflow** | Temporal workflow created dynamically to accomplish tasks |
| **Task** | A unit of work assigned by WORK loop, executed by EXECUTION loop |
| **Escalation** | A request for human input when system is blocked or uncertain |
| **DECAY** | Mechanism for cleaning up stale/unused workflows and branches |
| **Viability Score** | Estimate of how likely a hypothesis is to succeed given current capabilities |
| **PSD** | Point-and-Shoot Deployment - versioning model where multiple versions are LIVE simultaneously |
| **CURRENT-STABLE** | The version end-users see (DNS points here) |
| **PREVIOUS-STABLE** | Rollback target if CURRENT-STABLE fails |
| **PRUNE_PENDING** | Branch status indicating intent to prune, but waiting for in-flight tasks to complete |
| **Initial Ceremony** | The structured onboarding process (Phases 0-7) that occurs before any loops run |
| **Components Repository** | (Future) Shared, reusable solutions for cross-cutting concerns |
| **Service Tree** | (Future) A Tree that provides capabilities to other Trees |

---

## Appendix B: Change Log

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0-draft | 2025-01-30 | Initial foundation document |
| 0.1.1-draft | 2025-01-30 | Added Starting Point (Initial Ceremony phases), Resolved Design Decisions, Future Considerations. Resolved open questions for Human Interface, State Persistence, Multi-Business Support, Security, Observability, Versioning. Added PSD model. |
| 0.1.2-draft | 2025-01-30 | Added Black Box with X-Ray observability model, PSD Maturity Levels (0-3), PRUNE_PENDING pattern for graceful state conflict resolution. |
| 0.1.3-draft | 2025-01-30 | Added Phase 1.5 (Keys) to Initial Ceremony. API key collection now happens early, before any AI-powered phases. Deterministic walkthrough shows status table, file location, and allows direct file editing. |
| 0.1.4-draft | 2025-01-30 | Migrated to Temporal-only architecture. Removed n8n Cloud from deployment architecture. Temporal Cloud now orchestrates all loops AND executes all workflow types (META, EXPLORE, TEST, OP). Claude Code (via Temporal activities) performs the actual work. Updated repository structure, execution flow, and glossary accordingly. |

---

*This document is the single source of truth for ThousandHand architecture. All implementation should reference this document. Updates require explicit versioning.*
