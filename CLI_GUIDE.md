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
│   │   └── hypotheses.json
│   ├── reports/
│   │   ├── cycle_001.html
│   │   ├── cycle_002.html
│   │   └── ...
│   └── events.jsonl        # Event log
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
