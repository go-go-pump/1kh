# ThousandHand (1KH)

**Autonomous business-building system**

> Give me your values and objectives. I will imagine paths forward, estimate what's feasible, build what's needed, measure what happens, and learn from the results. I will ask for help when I'm stuck, and I will never violate your values.

## Status

🚧 **Active Development** - Core loops implemented, REFLECTION system live.

## Quick Start

```bash
# 1. Install dependencies
pip install -e .

# 2. Initialize a new project (the "Initial Ceremony")
1kh init

# 3. Run a demo cycle (no API costs - everything mocked)
1kh run cycle --demo --max 3 --verbose

# 4. Run with real Claude API
export ANTHROPIC_API_KEY=sk-ant-...
1kh run cycle --local --fresh --verbose

# 5. Check trajectory and get recommendations
1kh reflect
```

## CLI Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `1kh init` | Start the Initial Ceremony - create foundation documents |
| `1kh run cycle` | **Main command** - run full REFLECTION → IMAGINATION → INTENT → WORK → EXECUTION cycles |
| `1kh reflect` | Analyze trajectory and get AUGMENT/OPTIMIZE/PIVOT recommendations |
| `1kh status` | Check system health and progress |
| `1kh operate` | Transition to OPERATE phase with SLA monitoring |

### Run Options

```bash
# Execution modes
1kh run cycle --demo        # Mock everything (fast, no API costs)
1kh run cycle --local       # Real Claude API, CLI prompts for human decisions
1kh run cycle               # Production mode (requires Temporal)

# Common options
--max N                     # Stop after N cycles
--fresh                     # Clear previous metrics (start from $0)
--verbose                   # Show hypothesis/task details
--threshold 0.65            # Approval threshold (0.0-1.0)
--auto                      # Skip confirmation prompts
```

### Reflection & Analysis

```bash
1kh reflect                 # Analyze system state and trajectory
1kh reflect --apply         # Auto-apply safe recommendations
1kh reflect status          # Show current system components
1kh reflect clear           # Reset system state
```

### Operate Phase

```bash
1kh operate                 # Generate operations.md, transition to OPERATE
1kh operate --dry-run       # Preview without writing files
1kh operate show            # View operational status
```

### Other Commands

```bash
1kh quickstart              # Interactive getting started guide
1kh guide                   # Full CLI documentation
1kh escalations             # Handle pending human decisions
1kh logs                    # View system logs
1kh worker start            # Start Temporal worker (production)
```

## Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=cli --cov=temporal

# Run specific test files
pytest tests/test_runner.py -v
pytest tests/test_imagination.py -v

# Run demo mode tests (fast, no API)
pytest tests/ -k "demo" -v
```

## Development Setup

```bash
# Clone and install in development mode
git clone <repo>
cd 1KH
pip install -e ".[dev]"

# Set up pre-commit hooks (optional)
pre-commit install

# Run linting
ruff check .
black --check .

# Run type checking
mypy core/ cli/
```

## System Lifecycle

Projects progress through phases with different metrics:

```
BUILD → LAUNCH → OPERATE → OPTIMIZE
  │                 │          │
  │                 │          └─ IMAGINATION proposes improvements
  │                 └─ REFLECTION monitors SLAs (operations.md)
  └─ WORK + EXECUTION build features (north-star.md)
```

| Phase | Focus | Command |
|-------|-------|---------|
| BUILD | Feature completion checklist | `1kh init` (default) |
| OPERATE | SLA monitoring (uptime, latency) | `1kh operate` |

## The Five Loops

```
┌─────────────────────────────────────────────────────────────────┐
│                         THE FIVE LOOPS                          │
├─────────────────────────────────────────────────────────────────┤
│  0. REFLECTION  │  Analyze trajectory, recommend course changes │
│  1. IMAGINATION │  Generate hypotheses from foundation docs     │
│  2. INTENT      │  Evaluate feasibility and alignment           │
│  3. WORK        │  Create concrete tasks from hypotheses        │
│  4. EXECUTION   │  Execute tasks and measure outcomes           │
└─────────────────────────────────────────────────────────────────┘
```

**REFLECTION** analyzes system state and provides guidance:
- **AUGMENT** - Add a missing component (e.g., payment system)
- **OPTIMIZE** - Improve existing component (e.g., conversion rate)
- **PIVOT** - Change direction (requires human approval)

## System Components

For revenue generation, the system tracks four components:

| Component | Description | Example |
|-----------|-------------|---------|
| **Product** | The thing you sell | SaaS app, API, course |
| **Payment** | How customers pay | Stripe, PayPal |
| **Channel** | How customers find you | SEO, ads, referrals |
| **Fulfillment** | How value is delivered | API access, downloads |

The system won't generate revenue metrics until payment is live.

## Project Structure

```
1KH/
├── README.md               # This file
├── FOUNDATION.md           # Architecture document
├── CLI_GUIDE.md            # Detailed CLI documentation
├── pyproject.toml          # Python package config
│
├── cli/                    # Command-line interface
│   ├── main.py             # Entry point (1kh command)
│   └── commands/           # Subcommands (init, run, reflect, etc.)
│
├── core/                   # Core logic
│   ├── runner.py           # Cycle orchestration
│   ├── reflection.py       # REFLECTION loop
│   ├── system_state.py     # Component tracking
│   ├── executor.py         # Task execution
│   ├── dashboard.py        # Metrics & events (includes operational metrics)
│   ├── models.py           # Data models (SystemPhase, UtilitySubtype, SLAs)
│   └── report.py           # HTML report generation
│
├── temporal/               # Temporal Cloud integration
│   ├── activities/         # Reusable activities
│   │   ├── imagination.py  # Hypothesis generation
│   │   ├── work.py         # Task creation
│   │   └── foundation.py   # Document loading
│   └── workflows/          # Temporal workflows
│
├── tests/                  # Test suite
│   ├── test_runner.py
│   ├── test_imagination.py
│   └── mocks/              # Mock implementations
│
└── your-project/.1kh/      # Project data (created by init)
    ├── foundation/         # Oracle, North Star, Context
    ├── state/              # System state, hypotheses
    ├── reports/            # HTML cycle reports
    └── events.jsonl        # Event log
```

## Key Concepts

- **Oracle**: Your values and boundaries (what you'll never violate)
- **North Star**: Your measurable goal (e.g., $1M ARR)
- **Hypothesis**: A testable idea for achieving the North Star
- **System Completeness**: The four components needed for revenue
- **Trajectory**: Current pace toward the goal

## Example Workflow

```bash
# Initialize project with your goals
1kh init
# Answer questions about values, goals, constraints

# Run demo to see how it works
1kh run cycle --demo --max 5 --verbose
# Watch hypotheses get generated, evaluated, executed

# Check the HTML reports
open .1kh/reports/cycle_001.html

# Run with real Claude
export ANTHROPIC_API_KEY=sk-ant-...
1kh run cycle --local --fresh

# After a few cycles, check trajectory
1kh reflect
# System will tell you if you need to PIVOT or AUGMENT

# Apply recommendations
1kh reflect --apply --trust guided

# Once features are built, transition to OPERATE phase
1kh operate
# Generates operations.md with SLA targets based on utility subtype
# REFLECTION now monitors operational health instead of feature completion
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Required for `--local` mode |
| `TEMPORAL_ADDRESS` | Temporal Cloud address (production) |
| `TEMPORAL_NAMESPACE` | Temporal namespace (production) |

Or add to `.1kh/.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

## License

MIT
