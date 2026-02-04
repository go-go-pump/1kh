# THOUSANDHAND v2.0
## Autonomous Content & Publishing Pipeline

---

## What This Does

Thousandhand automatically:
1. **Generates** blog content in your voice
2. **Validates** quality before publishing  
3. **Publishes** to HTML with images and proper URLs
4. **Deploys** to your S3-hosted site
5. **Evaluates** whether goals are being met

All without your involvement (once configured).

---

## Quick Start

### 1. Configure

```bash
cp config.example.json config.json
# Edit config.json with your S3 bucket, etc.
```

### 2. Set Credentials

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

### 3. Run

```bash
# Full pipeline (evaluate → execute → evaluate)
python runner.py

# Or step by step:
python milliarch.py      # Evaluate goals, identify gaps
python thousandhand.py --mode=continuous  # Execute tasks
```

### 4. Automate (Optional)

```bash
bash setup_scheduler.sh  # Sets up daily cron job
```

---

## Architecture

```
thousandhand/
├── north_star.md          # Immutable vision
├── values.md              # Constraints (versioned)
├── paul_oracle.md         # Voice/judgment model (evolves)
│
├── goals/
│   ├── active/            # Current objectives
│   │   └── learning_portal_mvp.md
│   └── archived/          # Completed/deprecated goals
│
├── systems/
│   ├── blog_generator/
│   │   ├── v1.0.md        # Immutable spec
│   │   └── current.md     # Symlink to active version
│   ├── blog_validator/
│   │   └── ...
│   └── course_structurer/
│       └── ...
│
├── control/
│   ├── queue.md           # Tasks ready to execute
│   ├── blocked.md         # Tasks needing human input
│   └── dashboard.md       # Status at a glance
│
├── runs/
│   └── TASK-001_20260117_143022/
│       ├── input.json     # What was given
│       ├── prompt.md      # Full prompt sent
│       ├── output.json    # Structured result
│       ├── content.md     # Generated content (if any)
│       └── raw_response.txt
│
└── thousandhand.py        # Orchestrator
```

---

## Core Concepts

### Systems Are Immutable
A system is a versioned specification. When you change a system, you create a new version (v1.1, v2.0). Old versions remain for rollback and comparison.

### Runs Are Immutable
Every execution creates a timestamped folder in `runs/`. Input, output, and full prompt are recorded. Nothing is overwritten.

### Control Is Yours
- `queue.md` - Tasks ready to run. Reorder by editing.
- `blocked.md` - Tasks needing you. Resolve and move back.
- `dashboard.md` - Current status.

---

## Quick Start

### Check Status
```bash
python thousandhand.py --mode=status
```

### Run Next Task
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python thousandhand.py --mode=single
```

### Run Until Done
```bash
python thousandhand.py --mode=continuous
```

### Run Specific Task
```bash
python thousandhand.py --mode=task TASK-001
```

---

## Current Goal: Learning Portal MVP

**Target:** 10 blog articles + 1 course structure
**Systems Used:** BlogGenerator, BlogValidator, CourseStructurer
**Timeline:** ~4 weeks

Progress tracked in `control/dashboard.md`

---

## Workflow

1. **Queue populated** with tasks (manual or by Milliprax decomposition)
2. **Orchestrator picks** next task from queue
3. **System spec loaded** (e.g., BlogGenerator v1.0)
4. **Task executed** via Claude API with full context
5. **Results saved** to `runs/TASK-XXX_timestamp/`
6. **Dashboard updated**
7. **Paul reviews** outputs when convenient
8. **Oracle updated** if corrections needed

---

## Your Control Points

| I want to... | Do this... |
|--------------|------------|
| See what's happening | `cat control/dashboard.md` |
| See what needs me | `cat control/blocked.md` |
| Review outputs | `ls runs/` then read content.md |
| Change priorities | Edit `control/queue.md` |
| Add new task | Add to `control/queue.md` following format |
| Stop the system | Ctrl+C or empty the queue |
| Modify a system | Create new version in `systems/X/` |
| Update the Oracle | Edit `paul_oracle.md` |

---

## System Specifications

### BlogGenerator v1.0
- **Input:** topic, angle, keywords, length, type
- **Output:** title, meta_description, content, keywords_used, status
- **Purpose:** Generate blog articles in Paul's voice

### BlogValidator v1.0
- **Input:** content, title, article_type, keywords
- **Output:** verdict, scores, issues, strengths, summary
- **Purpose:** Quality gate before Paul review

### CourseStructurer v1.0
- **Input:** topic, learning_objectives, duration, depth
- **Output:** course structure with modules, lessons, slides
- **Purpose:** Transform topic into teachable course

---

## Costs

Estimated per task (using claude-sonnet-4-20250514):
- Blog generation: ~$0.02-0.05
- Blog validation: ~$0.01-0.03
- Course structure: ~$0.05-0.10

Full Learning Portal MVP (~20 tasks): ~$1-2

---

## Safety Limits

- Max 20 tasks per continuous run
- Max $15 spend per run
- 2 second delay between tasks
- All runs logged immutably

---

*This system exists to amplify Paul, not replace him.*
