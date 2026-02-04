# THOUSANDHAND - SIMPLIFIED
## A practical daily workflow with Claude Code

---

## What This Is Now

After iteration 1, we learned: Claude Code is better at the creative/complex work. 
What we need is:

1. **Automation** for things that don't need AI (publishing, deploying)
2. **A daily brief** so you know what needs attention
3. **Simple state files** Claude Code can read and update

---

## Daily Workflow

### 5:00 AM - Cron runs automatically
```
morning_brief.py runs:
  → Publishes any pending content to HTML
  → Deploys to S3 (if configured)
  → Generates TODAY.md with your focus items
```

### When you're ready (3-4 AM work session?)
```
1. Open Claude Code in your MVH project
2. Say: "Read thousandhand/control/TODAY.md and help me with today's focus"
3. Work through items with Claude Code
4. Claude Code updates backlog.md as things complete
```

That's it. No custom orchestrator. No queue.md formatting. Just Claude Code doing what it does best, with automated prep work.

---

## File Structure (Simplified)

```
thousandhand/
├── control/
│   ├── TODAY.md          # Generated daily - your focus
│   ├── backlog.md        # Simple task list you maintain
│   ├── blocked.md        # Decisions needed
│   └── published.json    # Auto-tracked by publisher
│
├── goals/active/         # Your objectives
├── runs/                 # Generated content waiting
├── public/               # Published HTML output
│
├── north_star.md         # Your vision (Claude Code reads this)
├── values.md             # Your constraints
├── paul_oracle.md        # Your voice guide
│
├── morning_brief.py      # Runs on cron
├── blog_publisher.py     # Runs on cron (via morning_brief)
└── config.json           # Your site settings
```

---

## Setup (One Time)

### 1. Set up cron
```bash
crontab -e

# Add this line (runs at 5 AM daily):
0 5 * * * cd /path/to/thousandhand && /usr/bin/python3 morning_brief.py >> logs/morning.log 2>&1
```

### 2. Set environment (add to ~/.zshrc or ~/.bashrc)
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

### 3. Configure site (config.json)
```json
{
  "site": {
    "name": "Man vs Health",
    "base_url": "https://manvshealth.com",
    "blog_path": "/blog"
  },
  "aws": {
    "s3_bucket": "your-bucket-name",
    "region": "us-east-1"
  }
}
```

---

## Using with Claude Code

### Starting your session
```
"Read thousandhand/control/TODAY.md and let's work through today's priorities."
```

### Generating content
```
"Read paul_oracle.md and write a blog post about [topic]. 
Save it to thousandhand/runs/TASK-XXX/content.md"
```

### Checking progress
```
"Check my goal progress in thousandhand/goals/active/ 
and update the checkboxes based on what we've done."
```

### Updating backlog
```
"Add [task] to my backlog and mark [other task] as done."
```

---

## What Runs Automatically vs. With You

| Task | Automatic | With Claude Code |
|------|-----------|------------------|
| Publish content → HTML | ✅ | |
| Deploy to S3 | ✅ | |
| Generate TODAY.md | ✅ | |
| Generate content | | ✅ |
| Review/edit content | | ✅ |
| Make decisions | | ✅ |
| Code changes | | ✅ |
| Complex planning | | ✅ |

---

## The Edison Note

This is iteration 1.5. We learned that:

- Custom Claude API orchestration ≠ better than Claude Code
- Markdown queue files are fragile
- The value is in the state files + automation, not the orchestrator

Future iterations might explore:
- Claude Code MCP integrations
- Scheduled Claude Code sessions (if that becomes possible)
- More sophisticated automation that truly doesn't need AI

For now: automate what you can, use Claude Code for the rest.

---

*"I have not failed. I've just found 10,000 ways that won't work." - Edison*
