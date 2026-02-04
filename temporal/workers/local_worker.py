"""
Local Temporal Worker

This worker runs on your local machine and executes activities that require:
- Claude API calls for reasoning (IMAGINATION loop)
- Local file system access (reading foundation docs)
- Eventually: Claude Code for building workflows (EXECUTION)

The worker connects to Temporal Cloud and polls for work on the specified task queue.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("1kh.worker")

console = Console()


async def run_worker(project_path: Path, task_queue: str = "1kh-local"):
    """
    Start the local Temporal worker.

    This function:
    1. Connects to Temporal Cloud using credentials from .1kh/.env
    2. Registers all activities
    3. Starts polling for work
    4. Runs until interrupted (Ctrl+C)

    Args:
        project_path: Path to the 1KH project
        task_queue: Temporal task queue to poll
    """
    # Import Temporal SDK (will fail gracefully if not installed)
    from temporalio.client import Client
    from temporalio.worker import Worker

    # Import our activities
    from temporal.activities.foundation import (
        read_oracle,
        read_north_star,
        read_context,
        read_seeds,
    )
    from temporal.activities.imagination import (
        generate_hypotheses,
        estimate_confidence,
    )
    from temporal.activities.work import (
        create_task,
        execute_task,
    )

    # Import client helper
    from temporal.client import create_client

    console.print("[dim]Connecting to Temporal Cloud...[/dim]")

    try:
        client = await create_client(project_path)
        console.print("[green]✓[/green] Connected to Temporal Cloud")
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise
    except Exception as e:
        console.print(f"[red]Connection failed:[/red] {e}")
        raise

    # List of all activities this worker handles
    activities = [
        # Foundation - reading local files
        read_oracle,
        read_north_star,
        read_context,
        read_seeds,
        # Imagination - Claude API calls
        generate_hypotheses,
        estimate_confidence,
        # Work - task creation and execution
        create_task,
        execute_task,
    ]

    console.print(f"[dim]Registering {len(activities)} activities...[/dim]")

    # Create and start the worker
    worker = Worker(
        client,
        task_queue=task_queue,
        activities=activities,
    )

    console.print()
    console.print(f"[green]✓[/green] Worker started on queue: [bold]{task_queue}[/bold]")
    console.print()
    console.print("[dim]Listening for work... (Ctrl+C to stop)[/dim]")
    console.print()

    # This runs until the worker is shut down
    await worker.run()


async def run_worker_with_workflows(project_path: Path, task_queue: str = "1kh-local"):
    """
    Start the worker with both workflows AND activities.

    Use this when you want to run workflows locally (for development/testing).
    In production, workflows typically run on Temporal Cloud.
    """
    from temporalio.client import Client
    from temporalio.worker import Worker

    # Import activities
    from temporal.activities.foundation import (
        read_oracle,
        read_north_star,
        read_context,
        read_seeds,
    )
    from temporal.activities.imagination import (
        generate_hypotheses,
        estimate_confidence,
    )
    from temporal.activities.work import (
        create_task,
        execute_task,
    )

    # Import workflows
    from temporal.workflows.imagination_loop import ImaginationLoopWorkflow
    from temporal.workflows.intent_loop import IntentLoopWorkflow
    from temporal.workflows.work_loop import WorkLoopWorkflow

    from temporal.client import create_client

    console.print("[dim]Connecting to Temporal Cloud...[/dim]")
    client = await create_client(project_path)
    console.print("[green]✓[/green] Connected to Temporal Cloud")

    activities = [
        read_oracle,
        read_north_star,
        read_context,
        read_seeds,
        generate_hypotheses,
        estimate_confidence,
        create_task,
        execute_task,
    ]

    workflows = [
        ImaginationLoopWorkflow,
        IntentLoopWorkflow,
        WorkLoopWorkflow,
    ]

    console.print(f"[dim]Registering {len(activities)} activities, {len(workflows)} workflows...[/dim]")

    worker = Worker(
        client,
        task_queue=task_queue,
        activities=activities,
        workflows=workflows,
    )

    console.print()
    console.print(f"[green]✓[/green] Worker started on queue: [bold]{task_queue}[/bold]")
    console.print("[dim]Running workflows AND activities locally[/dim]")
    console.print()
    console.print("[dim]Listening for work... (Ctrl+C to stop)[/dim]")
    console.print()

    await worker.run()


if __name__ == "__main__":
    # Allow running directly for testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m temporal.workers.local_worker <project_path>")
        sys.exit(1)

    project_path = Path(sys.argv[1])
    asyncio.run(run_worker(project_path))
