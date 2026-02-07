# ThousandHand CLI Quick Reference

## Overview

ThousandHand (1KH) is an autonomous business-building system. The CLI helps you:
1. **Set up** your business foundation (values, goals, constraints)
2. **Run** autonomous cycles that build toward your North Star
3. **Monitor** progress and system health
4. **Intervene** when human decisions are needed

---

## Getting Started

```bash
# 1. Initialize a new project (the "Initial Ceremony")
1kh init

# 2. Run your first cycle
1kh run cycle --demo        # Mock everything (no API calls)
1kh run cycle --local       # Real Claude, no Temporal
1kh run cycle               # Full production mode
```

---

## Command Reference

### `1kh init`
**Start a new project with the Initial Ceremony**

Creates your foundation documents:
- `oracle.md` - Your values, "always do" and "never do" rules
- `north_star.md` - Your goals and success metrics
- `context.md` - Resources, constraints, timeline
- `seeds.md` - Initial ideas (optional)

```bash
1kh init                    # Interactive wizard
1kh init --path ./my-biz    # Specify location
```

---

### `1kh run` - Execute Loops

#### `1kh run cycle` ⭐ **Main Command**
**Run full cycles: IMAGINATION → INTENT → WORK → EXECUTION**

```bash
# Modes
1kh run cycle --demo        # All mocked (fast, no API costs)
1kh run cycle --local       # Real Claude API, CLI prompts
1kh run cycle               # Production (requires Temporal)

# Options
--max N                     # Stop after N cycles (default: until goal reached)
--threshold 0.65            # Approval threshold (0.0-1.0)
--auto                      # Skip confirmation prompts
--fresh                     # Clear previous metrics (start from $0)
--verbose                   # Show hypothesis/task details
```

**Example:**
```bash
1kh run cycle --demo --max 5 --verbose
```

#### `1kh run imagination`
**Generate hypotheses only (no execution)**

```bash
1kh run imagination --local     # Use real Claude
1kh run imagination --dry-run   # Just show what would happen
```

#### `1kh run intent`
**Evaluate hypotheses and make decisions**

```bash
1kh run intent --local
```

---

### `1kh reflect` - Trajectory Analysis

**Analyze system state and get recommendations**

```bash
1kh reflect                     # Run analysis
1kh reflect --apply             # Auto-apply safe recommendations
1kh reflect --trust autonomous  # Auto-apply everything within Oracle bounds
```

**Trust Levels:**
- `manual` - All recommendations require approval
- `guided` - Auto-accept AUGMENT/OPTIMIZE, prompt for PIVOT
- `autonomous` - Auto-accept everything within Oracle bounds

**Subcommands:**
```bash
1kh reflect status              # Show current system state
1kh reflect clear               # Reset system state
```

---

### `1kh status`
**Check system health and progress**

```bash
1kh status                      # Overall status
1kh status metrics              # Detailed metrics
1kh status tree                 # Hypothesis tree view
```

---

### `1kh projects`
**List and switch between 1KH projects**

Manage multiple projects from a single CLI:

```bash
1kh projects                    # List all registered projects
1kh projects switch             # Interactive project selector
1kh projects switch NAME        # Switch to project by name (partial match)
1kh projects add PATH           # Register an existing project
1kh projects remove NAME        # Unregister (doesn't delete files)
1kh projects current            # Show current active project
```

**Example:**
```bash
$ 1kh projects
1KH Projects

┏━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃    ┃ Name   ┃ Path                         ┃ Phase       ┃
┡━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ ●  │ bix-v3 │ /path/to/bix-v3              │ Not started │
│    │ bix-v2 │ /path/to/bix-v2              │ Ready       │
└────┴────────┴──────────────────────────────┴─────────────┘

● = active project

$ 1kh projects switch bix-v2
✓ Switched to bix-v2
```

---

### `1kh forecast`
**Business simulation without execution**

Preview your journey, estimate costs/timeline, and identify risks before committing resources:

```bash
# Modes
1kh forecast                    # Live mode (real Claude, captures trace)
1kh forecast --mock             # Mock mode (no API calls, fast)
1kh forecast --replay TRACE_ID  # Replay with cached responses
1kh forecast --runs N           # Monte Carlo with N simulations

# Options
--cycles N                      # Max cycles to simulate (default: 50)
--human-quality LEVEL           # perfect, good, mediocre, poor (default: good)
--market RESPONSE               # optimistic, realistic, pessimistic (default: realistic)
--chaos LEVEL                   # none, low, medium, high (default: none)
--quiet                         # Minimal output

# Subcommands
1kh forecast list               # List saved traces
1kh forecast show TRACE_ID      # View trace details (see below)
1kh forecast delete TRACE_ID    # Delete a trace
1kh forecast sensitivity        # Sensitivity analysis (see below)
```

**Example output (BUSINESS SYSTEM):**
```
╭─────────────── FORECAST SUMMARY ───────────────╮
│ TARGET REACHED                                 │
│                                                │
│ Timeline:                                      │
│   Cycles: 47                                   │
│   Estimated Time: 4-6 months                   │
│                                                │
│ Financial:                                     │
│   Final Revenue: $1,050,000                    │
│   Target: $1,000,000                           │
│   API Cost: ~$0.38                             │
│                                                │
│ Risk Assessment:                               │
│   Risk Level: LOW                              │
│   Success Rate: 85%                            │
│                                                │
│ Trace saved: trace_20260205_143000             │
╰────────────────────────────────────────────────╯
```

**Example output (USER SYSTEM):**
```
╭─────────────── FORECAST SUMMARY ───────────────╮
│ 75.0% Progress                                 │
│                                                │
│ Timeline:                                      │
│   Cycles: 30                                   │
│   Estimated Time: 2-4 weeks                    │
│                                                │
│ Progress:                                      │
│   Features Completed: 6 / 8                    │
│   Tasks Completed: 24                          │
│   API Cost: ~$0.00                             │
│                                                │
│ Risk Assessment:                               │
│   Risk Level: LOW                              │
│   Success Rate: 90%                            │
╰────────────────────────────────────────────────╯
```

#### `1kh forecast show`
**View what actually happened in a trace**

Understand the simulation in detail - see every hypothesis, task, and decision:

```bash
# View a trace
1kh forecast show trace_20260205_164500

# Verbose mode (show all events)
1kh forecast show trace_xxx --verbose

# Filter to specific cycle
1kh forecast show trace_xxx --cycle 3

# JSON output
1kh forecast show trace_xxx --format json
```

**Example output:**
```
╭──────────────────── FORECAST TRACE ────────────────────╮
│ Trace: trace_20260205_164500                           │
│ Mode: mock | Cycles: 12 | TARGET REACHED               │
│                                                        │
│ Variables Applied:                                     │
│   human_quality=good → 90% approval rate               │
│   market_response=realistic → 1.0× growth multiplier   │
│   chaos_level=low → +10% extra task failures           │
╰────────────────────────────────────────────────────────╯

━━━ Cycle 1 ━━━
  IMAGINATION Generated 3 hypotheses
  ✓ APPROVED hyp-001-1: "Set up Stripe integration" (score: 0.85)
  ✗ REJECTED hyp-001-2: below threshold (score: 0.42)
  WORK Created 2 tasks
  ✓ TASK COMPLETED task-1 (+$150)
  ✗ TASK FAILED task-2: Service timeout
  👤 HUMAN approval_request: "Deploy to production" → Approved

━━━ Cycle 2 ━━━
  ...

╭──────────────────── SUMMARY ────────────────────╮
│ Execution Summary:                              │
│   Tasks: 18 completed, 3 failed (86% success)   │
│   Hypotheses: 12 approved, 5 rejected           │
│   Human Decisions: 8 approved, 2 rejected       │
│                                                 │
│ Final Metrics:                                  │
│   Cycles: 12                                    │
│   Time Estimate: 4-6 months                     │
│   Risk Level: LOW                               │
│   Success Rate: 85%                             │
╰─────────────────────────────────────────────────╯
```

**What the variables actually do:**

| Variable | Value | Effect |
|----------|-------|--------|
| `human_quality=perfect` | 100% | Every decision is approved |
| `human_quality=good` | 90% | Most decisions approved, occasional rejection |
| `human_quality=mediocre` | 70% | More rejections, slower progress |
| `human_quality=poor` | 50% | Half of decisions rejected |
| `market_response=optimistic` | 1.3× | Revenue/signups grow 30% faster |
| `market_response=realistic` | 1.0× | Normal growth rate |
| `market_response=pessimistic` | 0.7× | Growth is 30% slower |
| `chaos_level=none` | +0% | Tasks fail only at base rate (~15%) |
| `chaos_level=low` | +10% | ~25% task failure rate |
| `chaos_level=medium` | +20% | ~35% task failure rate |
| `chaos_level=high` | +40% | ~55% task failure rate |

---

#### `1kh forecast sensitivity`
**Analyze which variables have the biggest impact**

Understand which forecast variables matter most for your outcomes:

```bash
# Analyze all variables
1kh forecast sensitivity

# Analyze specific variable
1kh forecast sensitivity --variable chaos_level

# Two-variable interaction
1kh forecast sensitivity --interaction human_quality,market_response

# Options
--cycles N              # Max cycles per simulation (default: 30)
--runs N                # Monte Carlo runs per value (default: 5)
--baseline "good,realistic,none"  # Baseline variable values
--format table|json     # Output format (default: table)
--save                  # Save results to .1kh/sensitivity/
--quiet                 # Minimal output
```

**Example output (all variables):**
```
╭──────────────────── SENSITIVITY ANALYSIS ────────────────────╮
│ Project: bix-v3 (USER SYSTEM)                                │
│ Baseline: human_quality=good, market=realistic, chaos=none   │
│ Runs per value: 5 | Cycles: 30                               │
╰──────────────────────────────────────────────────────────────╯

Impact on Success Rate:
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Variable           ┃ Impact (Δ)    ┃ Range                     ┃ Sensitivity┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ chaos_level        │ Δ 38%         │ none:95% → high:57%       │ ████████   │
│ human_quality      │ Δ 28%         │ perfect:89% → poor:61%    │ ██████     │
│ market_response    │ Δ 12%         │ optimistic:78% → pess:66% │ ███        │
│ execution_variance │ Δ 8%          │ 0.0:77% → 1.0:69%         │ ██         │
└────────────────────┴───────────────┴───────────────────────────┴────────────┘

Key Insights:
  → chaos_level has HIGHEST impact - focus here
  → human_quality also matters significantly
  → market_response has LOW impact - less critical
```

**Example output (two-variable interaction):**
```
Interaction: human_quality × market_response
Success Rate Matrix:

              │ Optimistic │ Realistic │ Pessimistic │
──────────────┼────────────┼───────────┼─────────────┤
 Perfect      │    95%     │    85%    │     65%     │
 Good         │    88%     │    72%    │     52%     │
 Mediocre     │    70%     │    55%    │     35%     │
 Poor         │    55%     │    40%    │     20%     │

Interaction Detected: WEAK (0.15)
→ Effects are mostly additive (no strong synergy/conflict)
→ Optimize variables independently
```

---

### `1kh operate`
**Transition to OPERATE phase with SLA monitoring**

After your core features are built and deployed, transition from BUILD to OPERATE phase:

```bash
1kh operate                     # Generate operations.md and enable OPERATE phase
1kh operate --dry-run           # Preview generated operations.md without writing
1kh operate --force             # Overwrite existing operations.md
1kh operate /path/to/project    # Specify project path
1kh operate show                # View current operational status
```

**What happens:**
- Auto-generates `operations.md` from your utility subtype (e.g., MULTI_TENANT → uptime, latency SLAs)
- Sets system phase to OPERATE in ceremony state
- REFLECTION starts monitoring SLAs instead of feature completion

**System Lifecycle:**
```
BUILD → LAUNCH → OPERATE → OPTIMIZE
  │                 │          │
  │                 │          └─ IMAGINATION proposes improvements
  │                 └─ REFLECTION monitors SLAs (operations.md)
  └─ WORK + EXECUTION build features (north-star.md)
```

---

### `1kh escalations`
**Handle pending human decisions**

```bash
1kh escalations                 # List pending
1kh escalations respond E001    # Respond to specific
```

---

### `1kh logs`
**View system logs**

```bash
1kh logs                        # Recent activity
1kh logs decisions              # Decision audit trail
1kh logs execution              # Task execution logs
```

---

### `1kh worker`
**Manage Temporal worker (for production mode)**

```bash
1kh worker start                # Start local worker
1kh worker stop                 # Stop worker
1kh worker status               # Check worker status
```

---

## The Four Loops

Every cycle runs through four phases:

```
┌─────────────────────────────────────────────────────────────────┐
│                         THE FOUR LOOPS                          │
├─────────────────────────────────────────────────────────────────┤
│  1. IMAGINATION  │  Generate hypotheses from foundation docs   │
│  2. INTENT       │  Evaluate feasibility and alignment         │
│  3. WORK         │  Create concrete tasks from hypotheses      │
│  4. EXECUTION    │  Execute tasks and measure outcomes         │
└─────────────────────────────────────────────────────────────────┘
```

Plus **REFLECTION** - analyzes trajectory and suggests course corrections.

---

## Execution Modes

| Mode | Claude | Human | Orchestrator | Use Case |
|------|--------|-------|--------------|----------|
| `--demo` | Mock | Mock | CycleRunner | Quick testing, demos |
| `--local` | Real | CLI prompts | CycleRunner | Development, API testing |
| (default) | Real | Webhooks/UI | Temporal | Production |

---

## Key Concepts

### North Star
Your ultimate goal (e.g., "$1M ARR"). The system works toward this.

### Hypotheses
Ideas for achieving the North Star. Each has:
- **Feasibility** (0-100%) - Can we do this?
- **Alignment** (0-100%) - Does this move us toward the goal?
- **Combined Score** = 40% feasibility + 60% alignment

### System Completeness
Four components needed to generate revenue:
- **Product** - The thing you sell
- **Payment** - How customers pay you
- **Channel** - How customers find you
- **Fulfillment** - How customers receive value

### Recommendations
- **AUGMENT** - Add a missing piece (auto-approvable)
- **OPTIMIZE** - Improve something existing (auto-approvable)
- **PIVOT** - Change direction (requires human approval)

---

## System Lifecycle

Projects progress through phases:

```
BUILD → LAUNCH → OPERATE → OPTIMIZE
```

| Phase | Focus | Metrics Document | REFLECTION Monitors |
|-------|-------|------------------|---------------------|
| BUILD | Feature completion | north-star.md | Feature checklist |
| OPERATE | Production health | operations.md | SLA thresholds |
| OPTIMIZE | Performance tuning | operations.md | Improvement opportunities |

**Transition commands:**
- `1kh init` → Starts in BUILD phase
- `1kh operate` → Transitions to OPERATE phase

---

## File Structure

```
your-project/
├── .1kh/
│   ├── foundation/
│   │   ├── oracle.md       # Your values and rules
│   │   ├── north_star.md   # Your goals
│   │   ├── context.md      # Resources and constraints
│   │   └── seeds.md        # Initial ideas
│   ├── state/
│   │   ├── system_state.json
│   │   ├── ceremony_state.json  # System type, phase, utility subtype
│   │   └── hypotheses.json
│   ├── reports/
│   │   ├── cycle_001.html
│   │   ├── cycle_002.html
│   │   └── ...
│   └── events.jsonl        # Event log
├── operations.md           # SLA targets (generated by 1kh operate)
```

---

## Common Workflows

### Quick Demo
```bash
1kh init
1kh run cycle --demo --max 3
# Open .1kh/reports/cycle_001.html in browser
```

### Real Development
```bash
export ANTHROPIC_API_KEY=sk-...
1kh init
1kh run cycle --local --fresh --verbose
```

### Check Progress
```bash
1kh reflect status
1kh status
```

### Course Correct
```bash
1kh reflect --apply --trust guided
```

---

## Tips

1. **Start with `--demo`** to understand the flow before using API credits
2. **Use `--fresh`** when starting over to clear previous metrics
3. **Use `--verbose`** to see what hypotheses and tasks are being generated
4. **Check reports** in `.1kh/reports/` for visual dashboards
5. **Run `reflect`** periodically to check if you need to pivot

---

## Troubleshooting

**"No active project found"**
```bash
1kh init  # or specify --project path
```

**"ANTHROPIC_API_KEY not found"**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or add to .1kh/.env
```

**"Revenue stuck at $0"**
```bash
1kh reflect status  # Check if payment system is missing
```
