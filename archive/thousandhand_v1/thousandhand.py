#!/usr/bin/env python3
"""
THOUSANDHAND ORCHESTRATOR v2.0
A system-aware execution engine for Man vs Health

This orchestrator:
1. Reads system specifications (versioned, immutable)
2. Picks tasks from the queue
3. Executes tasks using appropriate system specs
4. Records immutable run results
5. Updates control surfaces
6. Chains tasks (e.g., generate → validate)

USAGE:
    python thousandhand.py --mode=status      # Show dashboard
    python thousandhand.py --mode=single      # Run one task
    python thousandhand.py --mode=continuous  # Run until queue empty or limit hit
    python thousandhand.py --mode=task TASK-001  # Run specific task
"""

import os
import sys
import json
import re
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import anthropic
except ImportError:
    print("Install anthropic: pip install anthropic")
    sys.exit(1)

# Configuration
PROJECT_DIR = Path(__file__).parent
RUNS_DIR = PROJECT_DIR / "runs"
CONTROL_DIR = PROJECT_DIR / "control"
SYSTEMS_DIR = PROJECT_DIR / "systems"
GOALS_DIR = PROJECT_DIR / "goals"

# Files
NORTH_STAR = PROJECT_DIR / "north_star.md"
VALUES = PROJECT_DIR / "values.md"
PAUL_ORACLE = PROJECT_DIR / "paul_oracle.md"
QUEUE_FILE = CONTROL_DIR / "queue.md"
BLOCKED_FILE = CONTROL_DIR / "blocked.md"
DASHBOARD_FILE = CONTROL_DIR / "dashboard.md"

# Model selection
MODEL = "claude-sonnet-4-20250514"

# Limits
MAX_TASKS_PER_RUN = 20
MAX_COST_PER_RUN = 15.0
TASK_DELAY_SECONDS = 2


class ThousandhandOrchestrator:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.task_count = 0
        self.estimated_cost = 0.0
        self.start_time = datetime.now()
        
        # Ensure directories exist
        RUNS_DIR.mkdir(exist_ok=True)
        CONTROL_DIR.mkdir(exist_ok=True)
    
    # ─────────────────────────────────────────────────────────────
    # File Operations
    # ─────────────────────────────────────────────────────────────
    
    def read_file(self, path: Path) -> str:
        if path.exists():
            return path.read_text()
        return ""
    
    def write_file(self, path: Path, content: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    # ─────────────────────────────────────────────────────────────
    # System Loading
    # ─────────────────────────────────────────────────────────────
    
    def load_system_spec(self, system_name: str) -> str:
        """Load the current version of a system specification."""
        current_link = SYSTEMS_DIR / system_name / "current.md"
        if current_link.exists():
            return self.read_file(current_link)
        
        # Fallback to v1.0
        v1 = SYSTEMS_DIR / system_name / "v1.0.md"
        if v1.exists():
            return self.read_file(v1)
        
        raise FileNotFoundError(f"System not found: {system_name}")
    
    def load_context(self) -> str:
        """Load all foundational context (north star, values, oracle)."""
        north_star = self.read_file(NORTH_STAR)
        values = self.read_file(VALUES)
        oracle = self.read_file(PAUL_ORACLE)
        
        return f"""# FOUNDATIONAL CONTEXT

## NORTH STAR
{north_star}

## VALUES
{values}

## PAUL ORACLE
{oracle}
"""
    
    # ─────────────────────────────────────────────────────────────
    # Queue Management
    # ─────────────────────────────────────────────────────────────
    
    def parse_queue(self) -> List[Dict[str, Any]]:
        """Parse the queue file and extract tasks."""
        queue_content = self.read_file(QUEUE_FILE)
        tasks = []
        
        # Find task blocks (### TASK-XXX)
        task_pattern = r'### (TASK-\d+):([^\n]+)\n(.*?)(?=###|\Z)'
        matches = re.findall(task_pattern, queue_content, re.DOTALL)
        
        for match in matches:
            task_id = match[0].strip()
            task_name = match[1].strip()
            task_body = match[2].strip()
            
            # Extract system
            system_match = re.search(r'\*\*System:\*\*\s*(\w+)\s+v[\d.]+', task_body)
            system = system_match.group(1).lower() if system_match else None
            
            # Extract input JSON
            input_match = re.search(r'```json\n(.*?)\n```', task_body, re.DOTALL)
            input_data = json.loads(input_match.group(1)) if input_match else {}
            
            tasks.append({
                "id": task_id,
                "name": task_name,
                "system": system,
                "input": input_data,
                "raw": task_body
            })
        
        return tasks
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get the next task from the queue."""
        tasks = self.parse_queue()
        return tasks[0] if tasks else None
    
    def mark_task_complete(self, task_id: str, run_dir: Path):
        """Move task from queue to completed (update queue file)."""
        queue_content = self.read_file(QUEUE_FILE)
        
        # Find and remove the task block
        task_pattern = rf'### {task_id}:[^\n]+\n.*?(?=###|\n## |\Z)'
        updated = re.sub(task_pattern, '', queue_content, flags=re.DOTALL)
        
        # Clean up extra whitespace
        updated = re.sub(r'\n{3,}', '\n\n', updated)
        
        self.write_file(QUEUE_FILE, updated)
        self.log(f"Task {task_id} completed, results in {run_dir}")
    
    # ─────────────────────────────────────────────────────────────
    # Task Execution
    # ─────────────────────────────────────────────────────────────
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task using its system specification."""
        task_id = task["id"]
        system_name = task["system"]
        input_data = task["input"]
        
        self.log(f"Executing {task_id}: {task['name']}")
        self.log(f"System: {system_name}")
        
        # Create run directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = RUNS_DIR / f"{task_id}_{timestamp}"
        run_dir.mkdir(parents=True)
        
        # Save input
        self.write_file(run_dir / "input.json", json.dumps(input_data, indent=2))
        
        # Load context and system spec
        context = self.load_context()
        
        # Map system name to directory
        system_dir_map = {
            "bloggenerator": "blog_generator",
            "blogvalidator": "blog_validator",
            "coursestructurer": "course_structurer"
        }
        system_dir = system_dir_map.get(system_name.lower(), system_name.lower())
        system_spec = self.load_system_spec(system_dir)
        
        # Build prompt
        prompt = f"""{context}

---

# SYSTEM SPECIFICATION
{system_spec}

---

# TASK EXECUTION

You are executing as the system specified above. Follow the PROCESS defined in the spec exactly.

## Input
```json
{json.dumps(input_data, indent=2)}
```

## Instructions
1. Follow the system specification's PROCESS step by step
2. Produce output matching the OUTPUT SCHEMA
3. Apply all CONSTRAINTS
4. Self-validate before returning

## Required Response Format
Return your response as valid JSON matching the output schema. Do not include any text before or after the JSON.
"""
        
        # Save prompt for debugging
        self.write_file(run_dir / "prompt.md", prompt)
        
        # Call Claude
        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Track cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000
            self.estimated_cost += cost
            
            self.log(f"Tokens: {input_tokens} in, {output_tokens} out (${cost:.4f})")
            
            result_text = response.content[0].text
            
            # Save raw response
            self.write_file(run_dir / "raw_response.txt", result_text)
            
            # Try to parse as JSON
            try:
                # Clean up potential markdown wrapping
                clean_text = result_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                result = json.loads(clean_text)
                self.write_file(run_dir / "output.json", json.dumps(result, indent=2))
                
                # Also save content as readable file if it exists
                if "content" in result:
                    self.write_file(run_dir / "content.md", result["content"])
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "run_dir": str(run_dir),
                    "output": result
                }
                
            except json.JSONDecodeError as e:
                self.log(f"JSON parse error: {e}", "WARN")
                # Save as text if not valid JSON
                self.write_file(run_dir / "output.txt", result_text)
                return {
                    "success": True,
                    "task_id": task_id,
                    "run_dir": str(run_dir),
                    "output": {"raw_text": result_text}
                }
                
        except Exception as e:
            self.log(f"Execution error: {e}", "ERROR")
            self.write_file(run_dir / "error.txt", str(e))
            return {
                "success": False,
                "task_id": task_id,
                "run_dir": str(run_dir),
                "error": str(e)
            }
    
    # ─────────────────────────────────────────────────────────────
    # Dashboard Updates
    # ─────────────────────────────────────────────────────────────
    
    def update_dashboard(self, result: Dict[str, Any]):
        """Update the dashboard with latest run info."""
        dashboard = self.read_file(DASHBOARD_FILE)
        
        # Update last updated timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        dashboard = re.sub(
            r'\*\*Last Updated:\*\*.*',
            f'**Last Updated:** {now}',
            dashboard
        )
        
        # Add to recent activity
        task_id = result.get("task_id", "Unknown")
        status = "✅ Success" if result.get("success") else "❌ Failed"
        activity_line = f"| {now} | Task {task_id} | {status} |"
        
        dashboard = re.sub(
            r'(\| Timestamp \| Event \| Details \|\n\|[-|]+\|)',
            f'\\1\n{activity_line}',
            dashboard
        )
        
        self.write_file(DASHBOARD_FILE, dashboard)
    
    # ─────────────────────────────────────────────────────────────
    # Run Modes
    # ─────────────────────────────────────────────────────────────
    
    def run_single(self, specific_task: str = None):
        """Run a single task."""
        if specific_task:
            tasks = self.parse_queue()
            task = next((t for t in tasks if t["id"] == specific_task), None)
            if not task:
                self.log(f"Task {specific_task} not found in queue", "ERROR")
                return
        else:
            task = self.get_next_task()
            if not task:
                self.log("Queue is empty")
                return
        
        result = self.execute_task(task)
        
        if result["success"]:
            self.mark_task_complete(task["id"], Path(result["run_dir"]))
        
        self.update_dashboard(result)
        
        self.log(f"Session complete. Cost: ${self.estimated_cost:.4f}")
        
        # Show output location
        if result.get("run_dir"):
            self.log(f"Output: {result['run_dir']}")
    
    def run_continuous(self):
        """Run tasks continuously until queue empty or limit hit."""
        self.log("Starting continuous mode...")
        
        try:
            while self.task_count < MAX_TASKS_PER_RUN:
                if self.estimated_cost > MAX_COST_PER_RUN:
                    self.log(f"Cost limit ${MAX_COST_PER_RUN} reached", "WARN")
                    break
                
                task = self.get_next_task()
                if not task:
                    self.log("Queue empty")
                    break
                
                result = self.execute_task(task)
                self.task_count += 1
                
                if result["success"]:
                    self.mark_task_complete(task["id"], Path(result["run_dir"]))
                
                self.update_dashboard(result)
                
                time.sleep(TASK_DELAY_SECONDS)
                
        except KeyboardInterrupt:
            self.log("Interrupted by user")
        
        self.log(f"Session complete. Tasks: {self.task_count}, Cost: ${self.estimated_cost:.4f}")
    
    def show_status(self):
        """Display the dashboard."""
        dashboard = self.read_file(DASHBOARD_FILE)
        print(dashboard)
        
        # Also show next task
        task = self.get_next_task()
        if task:
            print(f"\n📋 Next task: {task['id']} - {task['name']}")
            print(f"   System: {task['system']}")
        else:
            print("\n✅ Queue is empty")


def main():
    parser = argparse.ArgumentParser(description="Thousandhand Orchestrator v2.0")
    parser.add_argument(
        "--mode",
        choices=["status", "single", "continuous", "task"],
        default="status",
        help="Execution mode"
    )
    parser.add_argument(
        "task_id",
        nargs="?",
        help="Specific task ID (for --mode=task)"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    if args.mode in ["single", "continuous", "task"]:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("ERROR: Set ANTHROPIC_API_KEY environment variable")
            sys.exit(1)
    
    orchestrator = ThousandhandOrchestrator()
    
    if args.mode == "status":
        orchestrator.show_status()
    elif args.mode == "single":
        orchestrator.run_single()
    elif args.mode == "continuous":
        orchestrator.run_continuous()
    elif args.mode == "task":
        if not args.task_id:
            print("ERROR: Specify task ID with --mode=task TASK-001")
            sys.exit(1)
        orchestrator.run_single(args.task_id)


if __name__ == "__main__":
    main()
