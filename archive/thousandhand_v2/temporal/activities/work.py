"""
Work Activities - Create and execute tasks.

These activities handle the concrete work:
1. Breaking hypotheses into actionable tasks
2. Declaring resources before execution
3. Acquiring locks and executing tasks
4. Releasing locks after completion
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from temporalio import activity

# Logger for running outside Temporal context
logger = logging.getLogger("1kh.work")


def _safe_heartbeat(msg: str):
    """Send heartbeat if in activity context, otherwise log."""
    try:
        activity.heartbeat(msg)
    except RuntimeError:
        logger.debug(f"Heartbeat: {msg}")


def _safe_log_info(msg: str):
    """Log info whether in activity context or not."""
    try:
        activity.logger.info(msg)
    except RuntimeError:
        logger.info(msg)


@dataclass
class Task:
    """A concrete unit of work."""
    id: str
    hypothesis_id: str
    description: str
    task_type: str  # "build", "research", "deploy", "test"
    status: str  # "pending", "in_progress", "completed", "failed", "blocked"
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    # Resource declarations
    touches_resources: list = None  # [{type, identifier, access}]
    blocked_by: list = None  # List of task IDs blocking this task


@activity.defn
async def create_task(
    project_path: str,
    hypothesis: dict,
    oracle: dict,
    context: dict,
) -> dict:
    """
    Break a hypothesis into a concrete, actionable task.

    Uses Claude to determine what specific work needs to be done.

    Args:
        project_path: Path to the 1KH project
        hypothesis: The hypothesis to work on
        oracle: The parsed oracle.md content
        context: The parsed context.md content

    Returns:
        A task dictionary ready for execution
    """
    activity.logger.info(f"Creating task for hypothesis: {hypothesis.get('id', 'unknown')}")

    from anthropic import Anthropic

    # Load API key
    env_path = Path(project_path) / ".1kh" / ".env"
    api_key = None
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break

    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        activity.logger.error("No ANTHROPIC_API_KEY found")
        return {
            "id": f"task-{uuid.uuid4().hex[:8]}",
            "hypothesis_id": hypothesis.get("id", "unknown"),
            "description": "Failed to create task - no API key",
            "task_type": "error",
            "status": "failed",
            "error": "No ANTHROPIC_API_KEY configured",
        }

    client = Anthropic(api_key=api_key)

    prompt = f"""You are the WORK loop of ThousandHand, an autonomous business-building system.

Given a hypothesis, create a specific, actionable task that moves it forward.

## Hypothesis
ID: {hypothesis.get('id', 'unknown')}
Description: {hypothesis.get('description', 'No description')}
Rationale: {hypothesis.get('rationale', 'None')}

## Oracle (Values - must respect)
{oracle.get('raw', 'No oracle')}

## Context (Resources)
{context.get('raw', 'No context')}

## Task
Create ONE specific task that:
1. Makes concrete progress on this hypothesis
2. Respects the Oracle values
3. Is achievable with the given Context
4. Has a clear definition of "done"

Task types:
- "research": Gather information, analyze data
- "build": Create code, workflows, integrations
- "deploy": Put something into production
- "test": Validate something works

IMPORTANT - Resource Declaration:
You MUST declare what resources this task will touch. This enables conflict detection
and prevents multiple tasks from modifying the same files/APIs at once.

Resource types:
- "file": Specific file path (e.g., "src/api/main.py")
- "file_glob": File pattern (e.g., "temporal/activities/*.py")
- "api": External API endpoint (e.g., "stripe.com/v1/customers")
- "database": Database table (e.g., "users_table")
- "service": External service (e.g., "aws-s3")
- "deployment": Deployment target (e.g., "production")
- "budget": Spending money

Respond in JSON:
```json
{{
  "description": "Specific task description",
  "task_type": "build",
  "acceptance_criteria": ["Criterion 1", "Criterion 2"],
  "estimated_minutes": 30,
  "requires_human": false,
  "human_reason": null,
  "touches_resources": [
    {{"type": "file", "identifier": "src/api/main.py", "access": "write"}},
    {{"type": "api", "identifier": "stripe.com/v1/customers", "access": "read"}}
  ]
}}
```

If the task MUST involve human action (e.g., signing up for a service, making a payment),
set requires_human=true and explain why in human_reason.
"""

    _safe_heartbeat("Creating task with Claude")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    import re
    text = response.content[0].text
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)

    task_id = f"task-{uuid.uuid4().hex[:8]}"

    if json_match:
        try:
            task_data = json.loads(json_match.group(1))

            # Get resource declarations (inherit from hypothesis if not specified)
            touches_resources = task_data.get("touches_resources", [])
            if not touches_resources:
                # Fall back to hypothesis resources
                touches_resources = hypothesis.get("touches_resources", [])

            return {
                "id": task_id,
                "hypothesis_id": hypothesis.get("id", "unknown"),
                "description": task_data.get("description", "No description"),
                "task_type": task_data.get("task_type", "research"),
                "status": "pending",
                "acceptance_criteria": task_data.get("acceptance_criteria", []),
                "estimated_minutes": task_data.get("estimated_minutes", 30),
                "requires_human": task_data.get("requires_human", False),
                "human_reason": task_data.get("human_reason"),
                "touches_resources": touches_resources,
                "created_at": datetime.utcnow().isoformat(),
            }
        except json.JSONDecodeError as e:
            _safe_log_info(f"Failed to parse task JSON: {e}")

    # Fallback
    return {
        "id": task_id,
        "hypothesis_id": hypothesis.get("id", "unknown"),
        "description": f"Explore: {hypothesis.get('description', 'unknown')[:100]}",
        "task_type": "research",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }


@activity.defn
async def execute_task(
    project_path: str,
    task: dict,
    oracle: dict,
) -> dict:
    """
    Execute a task, potentially using Claude Code.

    For now, this uses Claude API directly. In the future,
    "build" tasks could invoke Claude Code for actual implementation.

    IMPORTANT: This function handles resource locking:
    1. Attempts to acquire locks on declared resources
    2. If blocked, returns task with status="blocked"
    3. Releases locks after completion (success or failure)

    Args:
        project_path: Path to the 1KH project
        task: The task to execute
        oracle: The parsed oracle.md (for safety checks)

    Returns:
        Updated task with results
    """
    from core.resources import ResourceQueue, ResourceDeclaration, Resource, ResourceType

    task_id = task.get("id", "unknown")
    task_type = task.get("task_type", "research")

    _safe_log_info(f"Executing task {task_id} (type: {task_type})")

    # Create resource declaration
    resources = []
    for res_dict in task.get("touches_resources", []):
        try:
            resources.append(Resource(
                type=ResourceType(res_dict.get("type", "file")),
                identifier=res_dict.get("identifier", "unknown"),
                access=res_dict.get("access", "read"),
            ))
        except ValueError:
            _safe_log_info(f"Unknown resource type: {res_dict.get('type')}")

    declaration = ResourceDeclaration(
        task_id=task_id,
        resources=resources,
    )

    # Try to acquire locks
    queue = ResourceQueue(Path(project_path))
    can_start, blockers = queue.can_acquire(declaration)

    if not can_start:
        _safe_log_info(f"Task {task_id} blocked by: {blockers}")
        task["status"] = "blocked"
        task["blocked_by"] = blockers
        queue.enqueue(declaration)
        return task

    # Acquire locks
    queue.acquire(declaration)
    _safe_log_info(f"Task {task_id} acquired {len(declaration.get_write_resources())} resource locks")

    # Check if task requires human
    if task.get("requires_human"):
        _safe_log_info(f"Task {task_id} requires human action")
        task["status"] = "blocked"
        task["result"] = "Requires human action"
        task["escalation_reason"] = task.get("human_reason", "Human intervention needed")
        # Release locks since we're not proceeding
        queue.release(task_id)
        return task

    # For now, all tasks go through Claude for research/planning
    # Build tasks would eventually invoke Claude Code

    from anthropic import Anthropic

    env_path = Path(project_path) / ".1kh" / ".env"
    api_key = None
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break

    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        task["status"] = "failed"
        task["error"] = "No ANTHROPIC_API_KEY configured"
        queue.release(task_id)
        return task

    client = Anthropic(api_key=api_key)

    # Different prompts based on task type
    if task_type == "research":
        prompt = f"""Research task:

{task.get('description', 'No description')}

Acceptance criteria:
{json.dumps(task.get('acceptance_criteria', []), indent=2)}

Provide a thorough research summary that addresses the acceptance criteria.
Be specific and actionable. Include sources or reasoning for your findings.
"""
    elif task_type == "build":
        prompt = f"""Build task (planning phase):

{task.get('description', 'No description')}

Acceptance criteria:
{json.dumps(task.get('acceptance_criteria', []), indent=2)}

Create a detailed implementation plan including:
1. Files to create/modify
2. Key code structures
3. Dependencies needed
4. Testing approach

Note: Actual code execution will be handled by Claude Code in a future version.
For now, provide the complete plan.
"""
    else:
        prompt = f"""Task:

{task.get('description', 'No description')}

Acceptance criteria:
{json.dumps(task.get('acceptance_criteria', []), indent=2)}

Complete this task and report results.
"""

    _safe_heartbeat(f"Executing {task_type} task")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        result = response.content[0].text

        task["status"] = "completed"
        task["result"] = result
        task["completed_at"] = datetime.utcnow().isoformat()

        _safe_log_info(f"Task {task_id} completed successfully")

    except Exception as e:
        _safe_log_info(f"Task {task_id} failed: {e}")
        task["status"] = "failed"
        task["error"] = str(e)

    finally:
        # ALWAYS release locks when done
        queue.release(task_id)
        _safe_log_info(f"Task {task_id} released resource locks")

        # Process the queue to unblock waiting tasks
        started = queue.process_queue()
        if started:
            _safe_log_info(f"Unblocked tasks from queue: {started}")

    return task
