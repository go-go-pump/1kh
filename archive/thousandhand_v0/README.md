# THOUSANDHAND
## Autonomous Execution System for Man vs Health

---

## What This Is

Thousandhand is a self-managing work system that:
- Maintains its own backlog of tasks
- Executes work autonomously when possible
- Flags items for human input when blocked
- Tracks state across sessions
- Evolves its own DNA based on learnings

## Quick Start

### 1. View Current Status
```bash
python thousandhand.py --mode=status
```

### 2. Run Single Cycle
```bash
export ANTHROPIC_API_KEY=your_key_here
python thousandhand.py --mode=single
```

### 3. Run Continuous
```bash
export ANTHROPIC_API_KEY=your_key_here
python thousandhand.py --mode=continuous
```

## File Structure

```
thousandhand/
├── CONSTITUTION.md    # The DNA - Paul Oracle, values, boundaries
├── STATE.md           # Current context, learnings, active threads
├── BACKLOG.md         # Work queue with priorities and status
├── HUMAN_BLOCKED.md   # Items waiting on Paul
├── COMPLETED.md       # Done work and outcomes
├── thousandhand.py    # The orchestrator script
├── outputs/           # Generated work products
└── logs/              # Execution logs
```

## How It Works

Each cycle:
1. Reads CONSTITUTION (DNA) + STATE + BACKLOG
2. Identifies next executable task
3. Produces output
4. Updates state files
5. Loops or halts

## For Paul

**To unblock work:**
Check HUMAN_BLOCKED.md and provide answers. Even partial info helps.

**To review outputs:**
Check the `outputs/` directory for generated work.

**To adjust priorities:**
Edit BACKLOG.md directly.

**To update the DNA:**
Edit CONSTITUTION.md (the Paul Oracle section especially).

## Safety Controls

- Max 50 cycles per run
- Max $10 estimated cost per run
- 2 second delay between cycles
- Logs everything
- Halts on errors

## Current Priority

PRIORITY 1: LAUNCH
- Man Plan (Free + Premium)
- Book sales
- PHO services
- Medical consults (with wife)
- Post-launch marketing

---

*This system exists to amplify Paul, not replace him.*
