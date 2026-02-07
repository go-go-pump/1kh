"""
Worker command - Start/stop the local Temporal worker.

Usage:
    1kh worker start    Start the local worker (connects to Temporal Cloud)
    1kh worker stop     Stop the running worker
    1kh worker status   Check if worker is running
"""
from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from core.config import get_last_active_project

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("start")
def start_worker(
    project_path: str = typer.Option(
        None,
        "--project", "-p",
        help="Path to 1KH project (defaults to last active project)",
    ),
    task_queue: str = typer.Option(
        "1kh-local",
        "--queue", "-q",
        help="Temporal task queue name",
    ),
):
    """
    Start the local Temporal worker.

    This connects to Temporal Cloud and begins processing activities
    for the IMAGINATION, INTENT, and WORK loops.
    """
    # Resolve project path
    if project_path:
        path = Path(project_path).resolve()
    else:
        last_project = get_last_active_project()
        if not last_project:
            console.print("[red]No active project found.[/red]")
            console.print("Run [bold]1kh init[/bold] first, or specify --project")
            raise typer.Exit(1)
        # get_last_active_project returns a dict with project info
        path = Path(last_project["path"])

    # Verify it's a valid 1KH project
    env_file = path / ".1kh" / ".env"
    if not env_file.exists():
        console.print(f"[red]Not a valid 1KH project: {path}[/red]")
        console.print("Missing .1kh/.env file. Run [bold]1kh init[/bold] first.")
        raise typer.Exit(1)

    console.print()
    console.print(Panel(
        f"[bold]Starting 1KH Worker[/bold]\n\n"
        f"Project: {path.name}\n"
        f"Task Queue: {task_queue}\n\n"
        "[dim]Press Ctrl+C to stop[/dim]",
        border_style="blue",
    ))
    console.print()

    # Run the async worker
    try:
        from temporal.workers.local_worker import run_worker
        asyncio.run(run_worker(project_path=path, task_queue=task_queue))
    except KeyboardInterrupt:
        console.print("\n[yellow]Worker stopped by user.[/yellow]")
    except ImportError as e:
        console.print(f"[red]Missing dependency: {e}[/red]")
        console.print()
        console.print("Install Temporal SDK with:")
        console.print("  [bold]pip install 'temporalio>=1.4.0' --break-system-packages[/bold]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Worker error: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
def worker_status():
    """Check if the worker is running."""
    # TODO: Implement proper process tracking
    console.print("[yellow]Worker status check not yet implemented.[/yellow]")
    console.print("[dim]For now, check if a worker process is running manually.[/dim]")


@app.command("stop")
def stop_worker():
    """Stop the running worker."""
    # TODO: Implement graceful shutdown via signal/PID file
    console.print("[yellow]Worker stop not yet implemented.[/yellow]")
    console.print("[dim]Use Ctrl+C in the terminal running the worker.[/dim]")
