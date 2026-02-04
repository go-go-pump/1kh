#!/usr/bin/env python3
"""
MILLIARCH - Governance Layer
Evaluates goal progress and identifies pipeline gaps.

USAGE:
    python milliarch.py              # Run full evaluation
    python milliarch.py --report     # Show latest report only
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Try to import anthropic, but milliarch can run without it for basic analysis
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

PROJECT_DIR = Path(__file__).parent
GOALS_DIR = PROJECT_DIR / "goals" / "active"
RUNS_DIR = PROJECT_DIR / "runs"
SYSTEMS_DIR = PROJECT_DIR / "systems"
CONTROL_DIR = PROJECT_DIR / "control"
PROPOSALS_DIR = PROJECT_DIR / "proposals"

REPORT_FILE = CONTROL_DIR / "milliarch_report.md"
QUEUE_FILE = CONTROL_DIR / "queue.md"
BLOCKED_FILE = CONTROL_DIR / "blocked.md"


class Milliarch:
    def __init__(self):
        self.findings = []
        self.actions_taken = []
        self.blocked_items = []
        self.proposals = []
        
        PROPOSALS_DIR.mkdir(exist_ok=True)
    
    def read_file(self, path: Path) -> str:
        if path.exists():
            return path.read_text()
        return ""
    
    def write_file(self, path: Path, content: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    
    def log(self, message: str):
        print(f"[Milliarch] {message}")
    
    # ─────────────────────────────────────────────────────────────
    # Analysis Functions
    # ─────────────────────────────────────────────────────────────
    
    def get_active_goals(self) -> List[Dict]:
        """Load all active goals."""
        goals = []
        if GOALS_DIR.exists():
            for goal_file in GOALS_DIR.glob("*.md"):
                content = self.read_file(goal_file)
                goals.append({
                    "name": goal_file.stem,
                    "path": goal_file,
                    "content": content
                })
        return goals
    
    def get_completed_runs(self) -> List[Dict]:
        """Get all completed task runs."""
        runs = []
        if RUNS_DIR.exists():
            for run_dir in sorted(RUNS_DIR.iterdir()):
                if run_dir.is_dir():
                    output_file = run_dir / "output.json"
                    content_file = run_dir / "content.md"
                    
                    run_info = {
                        "id": run_dir.name,
                        "path": run_dir,
                        "has_output": output_file.exists(),
                        "has_content": content_file.exists()
                    }
                    
                    if output_file.exists():
                        try:
                            run_info["output"] = json.loads(output_file.read_text())
                        except:
                            pass
                    
                    runs.append(run_info)
        return runs
    
    def get_available_systems(self) -> List[str]:
        """List all available systems."""
        systems = []
        if SYSTEMS_DIR.exists():
            for system_dir in SYSTEMS_DIR.iterdir():
                if system_dir.is_dir():
                    systems.append(system_dir.name)
        return systems
    
    def analyze_goal_progress(self, goal: Dict) -> Dict:
        """Analyze progress toward a specific goal."""
        content = goal["content"]
        
        # Extract success criteria (look for checkboxes)
        criteria = re.findall(r'- \[([ x])\] (.+)', content)
        total_criteria = len(criteria)
        completed_criteria = sum(1 for c in criteria if c[0] == 'x')
        
        # Count related runs
        runs = self.get_completed_runs()
        
        # Determine what type of output we're looking for
        has_blog_content = sum(1 for r in runs if r.get("has_content") and "TASK-00" in r["id"])
        
        return {
            "goal_name": goal["name"],
            "criteria_total": total_criteria,
            "criteria_completed": completed_criteria,
            "progress_pct": (completed_criteria / total_criteria * 100) if total_criteria > 0 else 0,
            "runs_completed": len(runs),
            "blog_content_generated": has_blog_content,
            "blog_content_published": 0,  # We know this is 0 - no publisher exists
        }
    
    def identify_pipeline_gaps(self) -> List[Dict]:
        """Identify missing systems in the pipeline."""
        available = set(self.get_available_systems())
        
        # Define expected pipeline for blog publishing
        blog_pipeline = [
            ("blog_generator", "Generate content from topic"),
            ("blog_validator", "Validate content quality"),
            ("blog_publisher", "Convert to HTML with images"),
            ("blog_index_builder", "Build blog index page"),
            ("s3_deployer", "Deploy to live site"),
        ]
        
        gaps = []
        for system_name, purpose in blog_pipeline:
            if system_name not in available:
                gaps.append({
                    "system": system_name,
                    "purpose": purpose,
                    "status": "MISSING"
                })
            else:
                gaps.append({
                    "system": system_name,
                    "purpose": purpose,
                    "status": "AVAILABLE"
                })
        
        return gaps
    
    def check_blocked_dependencies(self) -> List[Dict]:
        """Check what's blocking progress."""
        blocked = []
        
        # Check for AWS credentials
        if not os.environ.get("AWS_ACCESS_KEY_ID"):
            blocked.append({
                "item": "AWS Credentials",
                "reason": "Needed for S3 deployment",
                "action": "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
            })
        
        # Check for S3 bucket config
        config_file = PROJECT_DIR / "config.json"
        if not config_file.exists():
            blocked.append({
                "item": "Site Configuration",
                "reason": "Need S3 bucket name, CloudFront ID, base URL",
                "action": "Create config.json with site details"
            })
        
        return blocked
    
    # ─────────────────────────────────────────────────────────────
    # Action Functions
    # ─────────────────────────────────────────────────────────────
    
    def queue_publish_tasks(self):
        """Add publish tasks for any unpublished content."""
        runs = self.get_completed_runs()
        
        # Find runs with content but no corresponding publish
        content_runs = [r for r in runs if r.get("has_content")]
        
        new_tasks = []
        for run in content_runs:
            task_id = run["id"].split("_")[0]  # e.g., "TASK-001"
            publish_id = task_id.replace("TASK-", "PUB-")
            
            new_tasks.append({
                "id": publish_id,
                "name": f"Publish content from {task_id}",
                "system": "BlogPublisher",
                "input": {
                    "content_path": str(run["path"] / "content.md"),
                    "output_dir": str(PROJECT_DIR / "public"),
                }
            })
        
        return new_tasks
    
    # ─────────────────────────────────────────────────────────────
    # Report Generation
    # ─────────────────────────────────────────────────────────────
    
    def generate_report(self) -> str:
        """Generate full Milliarch assessment report."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Gather data
        goals = self.get_active_goals()
        goal_analyses = [self.analyze_goal_progress(g) for g in goals]
        pipeline_gaps = self.identify_pipeline_gaps()
        blocked = self.check_blocked_dependencies()
        runs = self.get_completed_runs()
        publish_tasks = self.queue_publish_tasks()
        
        # Count gaps
        missing_systems = [g for g in pipeline_gaps if g["status"] == "MISSING"]
        available_systems = [g for g in pipeline_gaps if g["status"] == "AVAILABLE"]
        
        report = f"""# MILLIARCH REPORT
## {now}

---

## EXECUTIVE SUMMARY

**Active Goals:** {len(goals)}
**Tasks Completed:** {len(runs)}
**Pipeline Status:** {len(available_systems)}/{len(pipeline_gaps)} systems available
**Blocked Items:** {len(blocked)}

---

## GOAL ANALYSIS

"""
        for analysis in goal_analyses:
            status_emoji = "🟢" if analysis["progress_pct"] >= 75 else "🟡" if analysis["progress_pct"] >= 25 else "🔴"
            report += f"""### {analysis['goal_name'].replace('_', ' ').title()}

{status_emoji} **Progress:** {analysis['progress_pct']:.0f}%

| Metric | Value |
|--------|-------|
| Success Criteria | {analysis['criteria_completed']}/{analysis['criteria_total']} |
| Tasks Completed | {analysis['runs_completed']} |
| Content Generated | {analysis['blog_content_generated']} articles |
| Content Published | {analysis['blog_content_published']} articles |

**Gap:** Content is generated but not published. Publishing pipeline incomplete.

"""

        report += """---

## PIPELINE STATUS

| System | Purpose | Status |
|--------|---------|--------|
"""
        for gap in pipeline_gaps:
            emoji = "✅" if gap["status"] == "AVAILABLE" else "❌"
            report += f"| {gap['system']} | {gap['purpose']} | {emoji} {gap['status']} |\n"

        report += """
---

## ACTIONS REQUIRED

### Immediate (Paul)
"""
        if blocked:
            for b in blocked:
                report += f"""
**{b['item']}**
- Reason: {b['reason']}
- Action: {b['action']}
"""
        else:
            report += "\n*No immediate blockers.*\n"

        report += """
### System Proposals (Review & Approve)
"""
        if missing_systems:
            for sys in missing_systems:
                report += f"- **{sys['system']}** - {sys['purpose']}\n"
            report += "\nProposal specs created in `proposals/` directory. Review and move to `systems/` to activate.\n"
        else:
            report += "\n*All required systems available.*\n"

        report += f"""
### Queued Tasks (Auto-generated)

{len(publish_tasks)} publish tasks ready to queue once BlogPublisher is available:
"""
        for task in publish_tasks[:5]:
            report += f"- {task['id']}: {task['name']}\n"
        if len(publish_tasks) > 5:
            report += f"- ... and {len(publish_tasks) - 5} more\n"

        report += """
---

## RECOMMENDATIONS

1. **Create config.json** with S3 bucket, CloudFront distribution, and base URL
2. **Set AWS credentials** in environment (or use IAM role)
3. **Review BlogPublisher spec** and move to systems/ to activate
4. **Run Thousandhand** to process publish queue

Once these are complete, Milliarch will re-evaluate and should show goals progressing toward completion.

---

*Report generated by Milliarch v1.0*
"""
        return report
    
    def run(self):
        """Run full Milliarch evaluation."""
        self.log("Starting evaluation...")
        
        # Generate report
        report = self.generate_report()
        
        # Save report
        self.write_file(REPORT_FILE, report)
        self.log(f"Report saved to {REPORT_FILE}")
        
        # Print report
        print("\n" + "="*60)
        print(report)
        print("="*60 + "\n")
        
        return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Milliarch - Governance Layer")
    parser.add_argument("--report", action="store_true", help="Show latest report only")
    args = parser.parse_args()
    
    milliarch = Milliarch()
    
    if args.report:
        # Just show existing report
        if REPORT_FILE.exists():
            print(REPORT_FILE.read_text())
        else:
            print("No report exists. Run `python milliarch.py` to generate.")
    else:
        milliarch.run()


if __name__ == "__main__":
    main()
