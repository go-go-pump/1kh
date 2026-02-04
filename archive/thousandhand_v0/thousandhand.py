#!/usr/bin/env python3
"""
THOUSANDHAND ORCHESTRATOR
A recursive autonomous execution engine for Man vs Health

This script:
1. Reads current state from markdown files
2. Constructs a prompt with DNA + state + current task
3. Calls Claude API to get next action
4. Executes the action (or logs if human intervention needed)
5. Updates state files
6. Loops until objectives met or halt condition

USAGE:
    python thousandhand.py --mode=continuous    # Run until stopped
    python thousandhand.py --mode=single        # Run one cycle
    python thousandhand.py --mode=status        # Show current state

REQUIREMENTS:
    pip install anthropic
    export ANTHROPIC_API_KEY=your_key_here
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import anthropic
except ImportError:
    print("Install anthropic: pip install anthropic")
    sys.exit(1)

# Configuration
PROJECT_DIR = Path(__file__).parent
STATE_FILE = PROJECT_DIR / "STATE.md"
BACKLOG_FILE = PROJECT_DIR / "BACKLOG.md"
CONSTITUTION_FILE = PROJECT_DIR / "CONSTITUTION.md"
BLOCKED_FILE = PROJECT_DIR / "HUMAN_BLOCKED.md"
COMPLETED_FILE = PROJECT_DIR / "COMPLETED.md"
LOG_DIR = PROJECT_DIR / "logs"

# Model selection (per Constitution - use smallest that works)
MODEL_EXECUTE = "claude-sonnet-4-20250514"  # For execution tasks
MODEL_THINK = "claude-sonnet-4-20250514"       # For strategic decisions

# Cost controls
MAX_CYCLES_PER_RUN = 50
MAX_COST_PER_RUN = 10.0  # USD estimate
CYCLE_DELAY_SECONDS = 2  # Prevent runaway


class ThousandhandOrchestrator:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.cycle_count = 0
        self.estimated_cost = 0.0
        self.start_time = datetime.now()
        
        # Ensure log directory exists
        LOG_DIR.mkdir(exist_ok=True)
    
    def read_file(self, path: Path) -> str:
        """Read a markdown file."""
        if path.exists():
            return path.read_text()
        return ""
    
    def write_file(self, path: Path, content: str):
        """Write content to file."""
        path.write_text(content)
    
    def append_to_file(self, path: Path, content: str):
        """Append content to file."""
        with open(path, 'a') as f:
            f.write(content)
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] [{level}] {message}\n"
        print(log_line.strip())
        
        log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        self.append_to_file(log_file, log_line)
    
    def construct_prompt(self, task_context: str = "") -> str:
        """Build the full prompt with DNA + state + task."""
        constitution = self.read_file(CONSTITUTION_FILE)
        state = self.read_file(STATE_FILE)
        backlog = self.read_file(BACKLOG_FILE)
        blocked = self.read_file(BLOCKED_FILE)
        
        prompt = f"""# THOUSANDHAND EXECUTION CYCLE

## YOUR DNA (Constitution)
{constitution}

## CURRENT STATE
{state}

## BACKLOG
{backlog}

## BLOCKED ITEMS (Waiting on human)
{blocked}

## TASK CONTEXT
{task_context if task_context else "No specific task. Review backlog and execute next available item."}

---

## YOUR INSTRUCTIONS FOR THIS CYCLE

1. Review the backlog and identify work you can do NOW (not blocked)
2. Execute ONE task from the "Quick Wins" or unblocked TODO items
3. Produce the actual output (code, copy, plan, etc.)
4. Report what you did and any state updates needed

RESPOND WITH:

### TASK SELECTED
[Which backlog item you're working on]

### OUTPUT
[The actual deliverable - code, copy, document, whatever the task requires]

### STATE UPDATES
[Any updates to STATE.md, BACKLOG.md, or COMPLETED.md]

### NEXT RECOMMENDED
[What should be done next cycle]

### BLOCKERS DISCOVERED
[Any new items for HUMAN_BLOCKED.md, or "None"]

DO NOT ask for permission. Execute based on the Constitution.
"""
        return prompt
    
    def call_claude(self, prompt: str, model: str = MODEL_EXECUTE) -> str:
        """Make API call to Claude."""
        self.log(f"Calling Claude ({model})...")
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Estimate cost (rough)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            # Sonnet pricing estimate: $3/1M input, $15/1M output
            cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000
            self.estimated_cost += cost
            
            self.log(f"Tokens: {input_tokens} in, {output_tokens} out. Est cost this call: ${cost:.4f}")
            
            return response.content[0].text
            
        except Exception as e:
            self.log(f"API Error: {e}", "ERROR")
            return f"ERROR: {e}"
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse Claude's structured response."""
        sections = {}
        current_section = None
        current_content = []
        
        for line in response.split('\n'):
            if line.startswith('### '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[4:].strip().upper().replace(' ', '_')
                current_content = []
            else:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def apply_state_updates(self, updates: str):
        """Apply state updates from Claude's response."""
        if not updates or updates.lower() == "none":
            return
        
        # Log the updates for manual review if needed
        self.log(f"State updates to apply:\n{updates}")
        
        # For now, append to state file with timestamp
        timestamp = datetime.now().isoformat()
        update_entry = f"\n\n---\n## Update {timestamp}\n{updates}\n"
        self.append_to_file(STATE_FILE, update_entry)
    
    def save_output(self, task_id: str, output: str):
        """Save task output to a file."""
        output_dir = PROJECT_DIR / "outputs"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"{task_id}_{timestamp}.md"
        self.write_file(output_file, output)
        self.log(f"Output saved to {output_file}")
    
    def run_cycle(self, task_context: str = "") -> bool:
        """Run one execution cycle. Returns True if should continue."""
        self.cycle_count += 1
        self.log(f"=== CYCLE {self.cycle_count} ===")
        
        # Safety checks
        if self.cycle_count > MAX_CYCLES_PER_RUN:
            self.log(f"Max cycles ({MAX_CYCLES_PER_RUN}) reached. Stopping.", "WARN")
            return False
        
        if self.estimated_cost > MAX_COST_PER_RUN:
            self.log(f"Cost limit (${MAX_COST_PER_RUN}) exceeded. Stopping.", "WARN")
            return False
        
        # Build and send prompt
        prompt = self.construct_prompt(task_context)
        response = self.call_claude(prompt)
        
        if response.startswith("ERROR:"):
            self.log("Cycle failed due to API error", "ERROR")
            return False
        
        # Parse response
        parsed = self.parse_response(response)
        
        # Save raw response for debugging
        self.save_output(f"cycle_{self.cycle_count}", response)
        
        # Apply updates
        task_selected = parsed.get('TASK_SELECTED', 'Unknown')
        self.log(f"Task executed: {task_selected}")
        
        if 'OUTPUT' in parsed:
            self.save_output(task_selected.replace(' ', '_'), parsed['OUTPUT'])
        
        if 'STATE_UPDATES' in parsed:
            self.apply_state_updates(parsed['STATE_UPDATES'])
        
        if 'BLOCKERS_DISCOVERED' in parsed:
            blockers = parsed['BLOCKERS_DISCOVERED']
            if blockers.lower() != 'none':
                self.log(f"New blockers: {blockers}", "WARN")
                self.append_to_file(BLOCKED_FILE, f"\n\n### New Blocker (auto-discovered)\n{blockers}\n")
        
        # Check if we should continue
        next_rec = parsed.get('NEXT_RECOMMENDED', '')
        if 'halt' in next_rec.lower() or 'stop' in next_rec.lower():
            self.log("Claude recommended halt. Stopping.")
            return False
        
        return True
    
    def run_continuous(self):
        """Run cycles continuously until stopped or limit hit."""
        self.log("Starting continuous mode...")
        
        try:
            while self.run_cycle():
                time.sleep(CYCLE_DELAY_SECONDS)
        except KeyboardInterrupt:
            self.log("Interrupted by user.")
        
        self.log(f"Session complete. Cycles: {self.cycle_count}, Est cost: ${self.estimated_cost:.4f}")
    
    def run_single(self, task: str = ""):
        """Run a single cycle."""
        self.log("Running single cycle...")
        self.run_cycle(task)
        self.log(f"Cycle complete. Est cost: ${self.estimated_cost:.4f}")
    
    def show_status(self):
        """Display current system status."""
        print("\n=== THOUSANDHAND STATUS ===\n")
        
        print("## State Summary")
        state = self.read_file(STATE_FILE)
        # Extract key info from state
        if "Current Phase" in state:
            for line in state.split('\n'):
                if "Current Phase" in line or "Active Focus" in line:
                    print(line)
        
        print("\n## Blocked Items")
        blocked = self.read_file(BLOCKED_FILE)
        # Count blocked items
        critical = blocked.count("## CRITICAL")
        high = blocked.count("## HIGH")
        print(f"Critical blockers: {critical}")
        print(f"High blockers: {high}")
        
        print("\n## Backlog Summary")
        backlog = self.read_file(BACKLOG_FILE)
        todo_count = backlog.count("| TODO |")
        blocked_count = backlog.count("| BLOCKED |")
        done_count = backlog.count("| DONE |")
        print(f"TODO: {todo_count}")
        print(f"BLOCKED: {blocked_count}")
        print(f"DONE: {done_count}")
        
        print("\n## Quick Wins Available")
        if "QUICK WINS" in backlog:
            qw_section = backlog.split("## QUICK WINS")[1].split("##")[0]
            print(qw_section.strip()[:500])


def main():
    parser = argparse.ArgumentParser(description="Thousandhand Orchestrator")
    parser.add_argument(
        "--mode",
        choices=["continuous", "single", "status"],
        default="status",
        help="Execution mode"
    )
    parser.add_argument(
        "--task",
        default="",
        help="Specific task context for single mode"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY") and args.mode != "status":
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        print("export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)
    
    orchestrator = ThousandhandOrchestrator()
    
    if args.mode == "continuous":
        orchestrator.run_continuous()
    elif args.mode == "single":
        orchestrator.run_single(args.task)
    else:
        orchestrator.show_status()


if __name__ == "__main__":
    main()
