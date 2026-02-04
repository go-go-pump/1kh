# MILLIARCH
## Governance Layer - Goal Evaluation and System Orchestration

---

## PURPOSE

Milliarch sits above Thousandhand and evaluates whether goals are actually being achieved. It:
1. Reviews execution results against goal success criteria
2. Identifies gaps in the system pipeline
3. Proposes new systems or system modifications
4. Flags issues for Milliprime (Paul) when needed

**Thousandhand asks:** "What's the next task?"
**Milliarch asks:** "Are we actually achieving the goal?"

---

## INTERFACE

### Input

Milliarch reviews:
- `goals/active/*.md` - Current objectives and success criteria
- `runs/*/` - Execution results from Thousandhand
- `control/dashboard.md` - Current metrics
- `systems/*/current.md` - Available system capabilities

### Output

Milliarch produces:
- `control/milliarch_report.md` - Assessment and recommendations
- Updates to `control/queue.md` - New tasks if gaps identified
- Updates to `control/blocked.md` - Issues requiring human input
- Proposals in `proposals/` - New system specs for review

---

## PROCESS

### Step 1: Goal Analysis

For each active goal, extract:
- Success criteria (what does "done" look like?)
- Current progress (what's been completed?)
- Gap analysis (what's missing?)

Example:
```
Goal: Learning Portal MVP
Criteria: "10 blog articles published"
Current: 6 content files in runs/
Gap: "published" ≠ "generated" - no publishing pipeline exists
```

### Step 2: Pipeline Completeness Check

For each goal, trace the full pipeline:
```
Input → System A → System B → ... → Desired Outcome
```

Identify:
- Missing systems (no system to do X)
- Broken connections (output of A doesn't feed B)
- Missing automation (manual step required)

### Step 3: Capability Gap Analysis

Compare required capabilities vs. available systems:

| Required | Available System | Status |
|----------|-----------------|--------|
| Generate content | BlogGenerator v1.0 | ✅ |
| Validate quality | BlogValidator v1.0 | ✅ |
| Publish to web | ??? | ❌ MISSING |
| Deploy to S3 | ??? | ❌ MISSING |

### Step 4: Recommendation Generation

For each gap, determine action:

**If system can be specified:**
→ Create system proposal in `proposals/`

**If system exists but isn't in queue:**
→ Add tasks to `control/queue.md`

**If human decision required:**
→ Add to `control/blocked.md` with clear question

**If goal itself is flawed:**
→ Propose goal modification to Milliprime

### Step 5: Generate Report

```markdown
# MILLIARCH REPORT
## {date}

### Goals Assessed
- Learning Portal MVP: 30% complete (content generated, not published)

### Gaps Identified
1. No publishing pipeline (BlogGenerator → ??? → Live site)
2. No image generation for blog posts
3. No deployment automation

### Actions Taken
- Created system proposal: BlogPublisher v1.0
- Created system proposal: S3Deployer v1.0
- Added 6 tasks to queue (publish existing content)

### Blocked on Human
- S3 bucket name and credentials needed
- Image approach decision (AI generate vs. stock)

### Recommendations
1. Approve BlogPublisher and S3Deployer specs
2. Provide AWS credentials
3. Decide on image strategy
```

---

## EVALUATION CRITERIA

### Goal Progress Scoring

```
0%   - Not started
25%  - Systems exist, tasks queued
50%  - Execution underway, partial output
75%  - Output complete, not yet deployed/verified
100% - Success criteria fully met
```

### System Health Scoring

```
GREEN  - System working, producing quality output
YELLOW - System working, output needs improvement
RED    - System failing or missing
```

---

## TRIGGER CONDITIONS

Milliarch runs:
1. After every N Thousandhand tasks (default: 5)
2. When queue becomes empty
3. On manual trigger (`python milliarch.py`)
4. Daily at scheduled time

---

## AUTHORITY LEVELS

| Action | Authority |
|--------|-----------|
| Add tasks to queue | AUTONOMOUS |
| Create system proposals | AUTONOMOUS (requires approval to activate) |
| Modify existing systems | PROPOSE ONLY |
| Modify goals | PROPOSE ONLY |
| Spend money (API calls) | Within limits |
| Access external services | Requires credentials |

Milliarch can act autonomously on queue management but cannot unilaterally change goals, values, or system specifications. Those require Milliprime (Paul) approval.

---

## EXAMPLE: CATCHING THE BLOG GAP

**Situation:** 
BlogGenerator ran 6 times. Content exists in runs/. Dashboard shows "0 articles published."

**Milliarch Analysis:**
```
Goal: "10 blog articles published"
Evidence: 
- 6 runs with content.md files
- Dashboard: "Blog Articles: 0 published"
- No BlogPublisher system exists
- No S3Deployer system exists

Conclusion: Content generation working, but no path to publication.

Action Plan:
1. Create BlogPublisher v1.0 proposal ✓
2. Create S3Deployer v1.0 proposal ✓
3. Queue: Publish TASK-001 through TASK-006 content
4. Block: Need S3 credentials from Paul
```

**Output:**
- New proposals created
- Queue updated with publish tasks
- Blocked item added for credentials
- Report generated for Paul review

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-17 | Initial specification |
