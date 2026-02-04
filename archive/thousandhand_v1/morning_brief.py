#!/usr/bin/env python3
"""
MORNING BRIEF
Runs on cron, does automated tasks, prepares your daily focus.

This is NOT trying to replace Claude Code. It's the prep work
so when you open Claude Code, everything is ready.

WHAT IT DOES:
1. Auto-publishes any generated content waiting in runs/
2. Auto-deploys to S3 if configured
3. Checks goal progress
4. Generates today's brief (what needs your attention)
5. Sends notification (optional)

USAGE:
    python morning_brief.py              # Run everything
    python morning_brief.py --brief-only # Just show the brief
    python morning_brief.py --no-notify  # Skip notification

CRON (daily at 5 AM, before you wake):
    0 5 * * * cd /path/to/thousandhand && python morning_brief.py >> logs/morning.log 2>&1
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

PROJECT_DIR = Path(__file__).parent
RUNS_DIR = PROJECT_DIR / "runs"
GOALS_DIR = PROJECT_DIR / "goals" / "active"
CONTROL_DIR = PROJECT_DIR / "control"
PUBLIC_DIR = PROJECT_DIR / "public"
CONFIG_FILE = PROJECT_DIR / "config.json"
BRIEF_FILE = CONTROL_DIR / "TODAY.md"
BACKLOG_FILE = CONTROL_DIR / "backlog.md"
LOG_DIR = PROJECT_DIR / "logs"

# Daily recurring tasks - customize these
DAILY_TASKS = {
    "monday": [
        "Review weekly goals and adjust priorities",
        "Check analytics from last week",
    ],
    "tuesday": [],
    "wednesday": [
        "Mid-week goal check-in",
    ],
    "thursday": [],
    "friday": [
        "Week review - what shipped, what didn't",
        "Plan next week's priorities",
    ],
    "saturday": [],
    "sunday": [
        "Light planning for Monday",
    ],
    "daily": [
        "Publish any pending blog content",
        "Check for blocked items needing decisions",
        "10 min on highest priority backlog item",
    ]
}


def log(message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def run_publisher() -> Dict[str, Any]:
    """Run blog publisher, return results."""
    publisher = PROJECT_DIR / "blog_publisher.py"
    if not publisher.exists():
        return {"ran": False, "reason": "blog_publisher.py not found"}
    
    result = subprocess.run(
        [sys.executable, str(publisher)],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True
    )
    
    # Parse output for summary
    published = []
    for line in result.stdout.split('\n'):
        if '✅' in line and '→' in line:
            published.append(line.strip())
    
    return {
        "ran": True,
        "published_count": len(published),
        "published": published,
        "output": result.stdout
    }


def run_deployer() -> Dict[str, Any]:
    """Deploy to S3 if configured."""
    config = load_config()
    bucket = config.get("aws", {}).get("s3_bucket", "")
    
    if not bucket or bucket == "YOUR_BUCKET_NAME":
        return {"ran": False, "reason": "S3 not configured"}
    
    if not os.environ.get("AWS_ACCESS_KEY_ID"):
        return {"ran": False, "reason": "AWS credentials not set"}
    
    if not PUBLIC_DIR.exists() or not any(PUBLIC_DIR.iterdir()):
        return {"ran": False, "reason": "No content to deploy"}
    
    result = subprocess.run(
        ["aws", "s3", "sync", str(PUBLIC_DIR), f"s3://{bucket}", "--delete"],
        capture_output=True,
        text=True
    )
    
    return {
        "ran": True,
        "success": result.returncode == 0,
        "bucket": bucket,
        "output": result.stdout
    }


def check_goal_progress() -> List[Dict]:
    """Check progress on active goals."""
    goals = []
    
    if not GOALS_DIR.exists():
        return goals
    
    for goal_file in GOALS_DIR.glob("*.md"):
        content = goal_file.read_text()
        
        # Count checkboxes
        checked = len([l for l in content.split('\n') if '- [x]' in l.lower()])
        unchecked = len([l for l in content.split('\n') if '- [ ]' in l])
        total = checked + unchecked
        
        progress = (checked / total * 100) if total > 0 else 0
        
        goals.append({
            "name": goal_file.stem.replace("_", " ").title(),
            "file": goal_file.name,
            "progress": progress,
            "done": checked,
            "total": total
        })
    
    return goals


def get_pending_content() -> List[Dict]:
    """Find generated content not yet published."""
    pending = []
    
    # Load published log
    published_log = CONTROL_DIR / "published.json"
    published_ids = set()
    if published_log.exists():
        data = json.loads(published_log.read_text())
        published_ids = set(data.get("published", {}).keys())
    
    # Check runs
    if RUNS_DIR.exists():
        for run_dir in RUNS_DIR.iterdir():
            if run_dir.is_dir() and (run_dir / "content.md").exists():
                if run_dir.name not in published_ids:
                    # Get title from output.json if exists
                    title = "Untitled"
                    output_file = run_dir / "output.json"
                    if output_file.exists():
                        try:
                            data = json.loads(output_file.read_text())
                            title = data.get("title", "Untitled")
                        except:
                            pass
                    
                    pending.append({
                        "id": run_dir.name,
                        "title": title,
                        "path": str(run_dir)
                    })
    
    return pending


def get_blocked_items() -> List[str]:
    """Get items from blocked.md."""
    blocked_file = CONTROL_DIR / "blocked.md"
    if not blocked_file.exists():
        return []
    
    content = blocked_file.read_text()
    
    # Find ### headers in CURRENT BLOCKS section
    items = []
    in_current = False
    for line in content.split('\n'):
        if '## CURRENT BLOCKS' in line:
            in_current = True
        elif line.startswith('## ') and in_current:
            in_current = False
        elif in_current and line.startswith('### '):
            items.append(line[4:].strip())
    
    return items


def get_backlog_items() -> List[Dict]:
    """Get top items from backlog."""
    if not BACKLOG_FILE.exists():
        return []
    
    content = BACKLOG_FILE.read_text()
    items = []
    
    # Simple parse - find lines that look like tasks
    for line in content.split('\n'):
        if line.strip().startswith('- [ ]'):
            items.append({
                "task": line.strip()[6:].strip(),
                "done": False
            })
        elif line.strip().startswith('- [x]'):
            items.append({
                "task": line.strip()[6:].strip(),
                "done": True
            })
    
    return items[:10]  # Top 10


def generate_brief(
    publish_result: Dict,
    deploy_result: Dict,
    goals: List[Dict],
    pending: List[Dict],
    blocked: List[str],
    backlog: List[Dict]
) -> str:
    """Generate the daily brief markdown."""
    
    now = datetime.now()
    day_name = now.strftime("%A").lower()
    date_str = now.strftime("%A, %B %d, %Y")
    
    # Get day-specific tasks
    today_tasks = DAILY_TASKS.get(day_name, []) + DAILY_TASKS.get("daily", [])
    
    brief = f"""# TODAY'S BRIEF
## {date_str}

---

*Generated at {now.strftime("%H:%M")} by morning_brief.py*

---

## 🌅 OVERNIGHT AUTOMATION

"""
    
    # Publishing results
    if publish_result.get("ran"):
        if publish_result.get("published_count", 0) > 0:
            brief += f"✅ **Published {publish_result['published_count']} articles**\n"
            for p in publish_result.get("published", []):
                brief += f"   {p}\n"
        else:
            brief += "📝 Publisher ran - no new content to publish\n"
    else:
        brief += f"⏭️ Publisher skipped: {publish_result.get('reason', 'unknown')}\n"
    
    brief += "\n"
    
    # Deploy results
    if deploy_result.get("ran"):
        if deploy_result.get("success"):
            brief += f"✅ **Deployed to S3** ({deploy_result.get('bucket')})\n"
        else:
            brief += "❌ Deploy failed - check logs\n"
    else:
        brief += f"⏭️ Deploy skipped: {deploy_result.get('reason', 'unknown')}\n"
    
    brief += """
---

## 🎯 GOAL PROGRESS

"""
    
    if goals:
        for g in goals:
            bar_filled = int(g['progress'] / 10)
            bar_empty = 10 - bar_filled
            bar = '█' * bar_filled + '░' * bar_empty
            brief += f"**{g['name']}**\n"
            brief += f"{bar} {g['progress']:.0f}% ({g['done']}/{g['total']})\n\n"
    else:
        brief += "*No active goals found*\n"
    
    brief += """---

## 📋 TODAY'S FOCUS

"""
    
    # Blocked items first (need decisions)
    if blocked:
        brief += "### 🚫 Blocked (Need Your Decision)\n"
        for item in blocked:
            brief += f"- [ ] {item}\n"
        brief += "\n"
    
    # Pending content
    if pending:
        brief += f"### 📝 Content Ready to Review ({len(pending)})\n"
        for p in pending[:3]:
            brief += f"- [ ] Review: {p['title']}\n"
        if len(pending) > 3:
            brief += f"- ... and {len(pending) - 3} more\n"
        brief += "\n"
    
    # Daily tasks
    if today_tasks:
        brief += "### 📆 Daily Tasks\n"
        for task in today_tasks:
            brief += f"- [ ] {task}\n"
        brief += "\n"
    
    # Backlog
    if backlog:
        undone = [b for b in backlog if not b['done']][:3]
        if undone:
            brief += "### 📚 From Backlog\n"
            for item in undone:
                brief += f"- [ ] {item['task']}\n"
            brief += "\n"
    
    brief += """---

## 💡 SUGGESTED CLAUDE CODE SESSION

When you open Claude Code, start with:

```
Read thousandhand/control/TODAY.md and help me work through today's focus items.
Start with any blocked items that need decisions.
```

---

*Don't try to do everything. Pick 1-3 things that move the needle.*
"""
    
    return brief


def send_notification(brief: str, config: dict):
    """Send notification (placeholder - implement your preferred method)."""
    notify_config = config.get("notifications", {})
    
    # Example: SMS via Twilio
    if notify_config.get("twilio"):
        # TODO: Implement Twilio SMS
        pass
    
    # Example: Email via AWS SES
    if notify_config.get("ses"):
        # TODO: Implement SES email
        pass
    
    # Example: Slack webhook
    if notify_config.get("slack_webhook"):
        # TODO: Implement Slack notification
        pass
    
    # For now, just log
    log("Notification: Brief ready at control/TODAY.md")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Morning Brief Generator")
    parser.add_argument("--brief-only", action="store_true", help="Only generate brief, skip automation")
    parser.add_argument("--no-notify", action="store_true", help="Skip notification")
    args = parser.parse_args()
    
    LOG_DIR.mkdir(exist_ok=True)
    CONTROL_DIR.mkdir(exist_ok=True)
    
    log("=" * 50)
    log("MORNING BRIEF")
    log("=" * 50)
    
    config = load_config()
    
    # Run automations (unless brief-only)
    if args.brief_only:
        publish_result = {"ran": False, "reason": "brief-only mode"}
        deploy_result = {"ran": False, "reason": "brief-only mode"}
    else:
        log("\n📝 Running publisher...")
        publish_result = run_publisher()
        
        log("\n🚀 Running deployer...")
        deploy_result = run_deployer()
    
    # Gather status
    log("\n📊 Checking status...")
    goals = check_goal_progress()
    pending = get_pending_content()
    blocked = get_blocked_items()
    backlog = get_backlog_items()
    
    # Generate brief
    log("\n📋 Generating brief...")
    brief = generate_brief(
        publish_result, deploy_result,
        goals, pending, blocked, backlog
    )
    
    # Save brief
    BRIEF_FILE.write_text(brief)
    log(f"✅ Brief saved to {BRIEF_FILE}")
    
    # Send notification
    if not args.no_notify:
        send_notification(brief, config)
    
    # Print brief to stdout too
    print("\n" + "=" * 50)
    print(brief)
    print("=" * 50)
    
    log("\n✨ Morning brief complete!")


if __name__ == "__main__":
    main()
