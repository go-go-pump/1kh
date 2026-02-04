"""
WORK Loop - Task creation and execution.

This Temporal workflow handles:
1. Receiving selected paths from INTENT
2. Breaking paths into concrete tasks
3. Executing tasks (research, build, deploy, test)
4. Tracking progress and results
5. Escalating blocked tasks to human

This is where concrete work gets done.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from temporal.activities.foundation import read_oracle, read_context
    from temporal.activities.work import create_task, execute_task


@workflow.defn
class WorkLoopWorkflow:
    """
    The WORK loop executes concrete tasks.

    Input:
        project_path: Path to the 1KH project
        selected_paths: Paths selected by INTENT

    Output:
        Task results and any escalations
    """

    def __init__(self):
        self.tasks = []
        self.completed_tasks = []
        self.blocked_tasks = []
        self.status = "initializing"

    @workflow.run
    async def run(
        self,
        project_path: str,
        selected_paths: list[dict],
    ) -> dict:
        """
        Execute the work loop.

        1. Load context for task creation
        2. Create tasks for each selected path
        3. Execute tasks
        4. Collect results
        """
        self.status = "loading_context"

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
        )

        # Load foundation for task context
        oracle = await workflow.execute_activity(
            read_oracle,
            project_path,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        context = await workflow.execute_activity(
            read_context,
            project_path,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # Create tasks for each path
        self.status = "creating_tasks"

        for path in selected_paths:
            task = await workflow.execute_activity(
                create_task,
                args=[project_path, path, oracle, context],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
                heartbeat_timeout=timedelta(minutes=1),
            )
            self.tasks.append(task)

        workflow.logger.info(f"Created {len(self.tasks)} tasks")

        # Execute tasks
        self.status = "executing_tasks"

        for task in self.tasks:
            # Check if task requires human
            if task.get("requires_human"):
                self.blocked_tasks.append(task)
                workflow.logger.info(
                    f"Task {task.get('id')} blocked - requires human: "
                    f"{task.get('human_reason')}"
                )
                continue

            # Execute the task
            result = await workflow.execute_activity(
                execute_task,
                args=[project_path, task, oracle],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
                heartbeat_timeout=timedelta(minutes=5),
            )

            if result.get("status") == "completed":
                self.completed_tasks.append(result)
            elif result.get("status") == "blocked":
                self.blocked_tasks.append(result)
            else:
                # Failed - could retry or escalate
                workflow.logger.warning(
                    f"Task {result.get('id')} failed: {result.get('error')}"
                )
                self.blocked_tasks.append(result)

        self.status = "complete"

        return {
            "status": "complete",
            "total_tasks": len(self.tasks),
            "completed": len(self.completed_tasks),
            "blocked": len(self.blocked_tasks),
            "completed_tasks": self.completed_tasks,
            "blocked_tasks": self.blocked_tasks,
            "escalations": [
                {
                    "task_id": t.get("id"),
                    "reason": t.get("escalation_reason") or t.get("error") or t.get("human_reason"),
                    "task_description": t.get("description"),
                }
                for t in self.blocked_tasks
            ],
        }

    @workflow.query
    def get_status(self) -> str:
        """Query the current status."""
        return self.status

    @workflow.query
    def get_tasks(self) -> dict:
        """Query all tasks and their status."""
        return {
            "pending": [t for t in self.tasks if t.get("status") == "pending"],
            "completed": self.completed_tasks,
            "blocked": self.blocked_tasks,
        }

    @workflow.query
    def get_escalations(self) -> list:
        """Query blocked tasks that need human intervention."""
        return self.blocked_tasks

    @workflow.signal
    def unblock_task(self, task_id: str, resolution: dict):
        """
        Signal that a blocked task has been resolved by human.

        resolution = {
            "action": "continue" | "skip" | "modify",
            "new_task": {...}  # if action is "modify"
        }
        """
        workflow.logger.info(f"Task {task_id} unblocked: {resolution.get('action')}")
        # Remove from blocked, potentially re-queue
        self.blocked_tasks = [
            t for t in self.blocked_tasks
            if t.get("id") != task_id
        ]

    @workflow.signal
    def add_task(self, task: dict):
        """Signal to add a new task to the queue."""
        self.tasks.append(task)
        workflow.logger.info(f"Added new task: {task.get('id')}")
