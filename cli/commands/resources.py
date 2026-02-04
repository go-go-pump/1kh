"""
CLI commands for managing resources and viewing locks.

Usage:
    1kh resources locks          Show active resource locks
    1kh resources queue          Show pending tasks in queue
    1kh resources conflicts      Show detected conflicts between hypotheses
    1kh resources release <id>   Force release locks held by a task
"""
import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from core.config import get_last_active_project
from core.resources import ResourceQueue, detect_hypothesis_conflicts

app = typer.Typer(
    name="resources",
    help="Manage resources and view locks",
    no_args_is_help=True,
)

console = Console()


def _get_project_path() -> Path:
    """Get the current project path."""
    last_project = get_last_active_project()
    if not last_project:
        console.print("[red]No active project. Run '1kh init' first.[/red]")
        raise typer.Exit(1)
    return Path(last_project["path"])


@app.command("locks")
def show_locks():
    """
    Show all active resource locks.

    Displays which tasks currently hold locks on which resources.
    """
    project_path = _get_project_path()
    queue = ResourceQueue(project_path)

    locks = queue.get_active_locks()

    if not locks:
        console.print(Panel(
            "[green]No active locks[/green]\n\n"
            "All resources are available for new tasks.",
            title="Resource Locks",
        ))
        return

    table = Table(title="Active Resource Locks")
    table.add_column("Resource", style="cyan")
    table.add_column("Type", style="dim")
    table.add_column("Held By", style="yellow")
    table.add_column("Since", style="dim")

    for lock in locks:
        table.add_row(
            lock["resource"],
            lock["type"],
            lock["holder"],
            lock["acquired_at"][:19],  # Trim microseconds
        )

    console.print(table)


@app.command("queue")
def show_queue():
    """
    Show tasks waiting in the queue.

    These tasks are waiting for resources to become available.
    """
    project_path = _get_project_path()
    queue = ResourceQueue(project_path)

    queue_status = queue.get_queue_status()

    if not queue_status:
        console.print(Panel(
            "[green]Queue is empty[/green]\n\n"
            "No tasks are waiting for resources.",
            title="Task Queue",
        ))
        return

    table = Table(title="Tasks Waiting for Resources")
    table.add_column("Task ID", style="cyan")
    table.add_column("Resources", style="dim")
    table.add_column("Write Resources", style="yellow")
    table.add_column("Waiting Since", style="dim")

    for item in queue_status:
        table.add_row(
            item["task_id"],
            str(item["resources"]),
            str(item["write_resources"]),
            item["declared_at"][:19],
        )

    console.print(table)


@app.command("conflicts")
def show_conflicts(
    hypotheses_file: str = typer.Option(
        None,
        "--file", "-f",
        help="Path to hypotheses JSON file (defaults to latest)",
    ),
):
    """
    Show detected conflicts between hypotheses.

    Reads the hypotheses from the last imagination run and
    detects which ones would conflict if run in parallel.
    """
    project_path = _get_project_path()

    # Find the hypotheses file
    if hypotheses_file:
        hyp_path = Path(hypotheses_file)
    else:
        # Look for latest hypotheses file
        hyp_dir = project_path / ".1kh" / "hypotheses"
        if not hyp_dir.exists():
            console.print("[yellow]No hypotheses found. Run '1kh run imagination' first.[/yellow]")
            raise typer.Exit(1)

        hyp_files = list(hyp_dir.glob("hypotheses*.json"))
        if not hyp_files:
            console.print("[yellow]No hypotheses found. Run '1kh run imagination' first.[/yellow]")
            raise typer.Exit(1)

        hyp_path = max(hyp_files, key=lambda p: p.stat().st_mtime)

    console.print(f"[dim]Reading from: {hyp_path}[/dim]\n")

    try:
        hypotheses = json.loads(hyp_path.read_text())
    except (json.JSONDecodeError, FileNotFoundError) as e:
        console.print(f"[red]Failed to read hypotheses: {e}[/red]")
        raise typer.Exit(1)

    # Check if hypotheses have resource declarations
    has_resources = any(h.get("touches_resources") for h in hypotheses)
    if not has_resources:
        console.print(Panel(
            "[yellow]No resource declarations found in hypotheses.[/yellow]\n\n"
            "To detect conflicts, hypotheses need 'touches_resources' declarations.\n"
            "This may require re-running imagination with the updated prompts.",
            title="Missing Resource Declarations",
        ))
        return

    # Detect conflicts
    conflicts = detect_hypothesis_conflicts(hypotheses)

    if not conflicts:
        console.print(Panel(
            "[green]No conflicts detected[/green]\n\n"
            "All hypotheses can theoretically run in parallel.\n"
            "(Though we still recommend sequential execution for safety.)",
            title="Conflict Detection",
        ))
        return

    # Display conflicts
    console.print(Panel(
        f"[yellow]Found conflicts between {len(conflicts)} hypotheses[/yellow]",
        title="Resource Conflicts",
    ))

    for hyp_id, conflict_list in conflicts.items():
        # Find the hypothesis description
        hyp = next((h for h in hypotheses if h.get("id") == hyp_id), {})
        desc = hyp.get("description", "No description")[:60]

        console.print(f"\n[cyan]{hyp_id}[/cyan]: {desc}...")
        for conflict in conflict_list:
            console.print(f"  [red]↔ Conflicts with[/red] [yellow]{conflict['with']}[/yellow]")
            for resource in conflict["resources"]:
                console.print(f"      Resource: [dim]{resource}[/dim]")


@app.command("release")
def release_locks(
    task_id: str = typer.Argument(
        ...,
        help="Task ID to release locks for",
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Skip confirmation",
    ),
):
    """
    Force release all locks held by a task.

    Use this if a task crashed or was interrupted and left locks behind.
    """
    project_path = _get_project_path()
    queue = ResourceQueue(project_path)

    # Show current locks for this task
    locks = [l for l in queue.get_active_locks() if l["holder"] == task_id]

    if not locks:
        console.print(f"[yellow]No locks found for task {task_id}[/yellow]")
        raise typer.Exit(0)

    console.print(f"[cyan]Found {len(locks)} locks for task {task_id}:[/cyan]")
    for lock in locks:
        console.print(f"  • {lock['resource']} ({lock['type']})")

    if not force:
        confirm = typer.confirm("Release these locks?")
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(0)

    queue.release(task_id)
    console.print(f"[green]✓ Released {len(locks)} locks[/green]")

    # Check if this unblocks anything
    started = queue.process_queue()
    if started:
        console.print(f"\n[green]Unblocked {len(started)} queued tasks:[/green]")
        for tid in started:
            console.print(f"  • {tid}")


@app.command("process-queue")
def process_queue():
    """
    Process the queue and start any tasks that can now run.

    Call this after releasing locks or when you suspect tasks
    are stuck in the queue.
    """
    project_path = _get_project_path()
    queue = ResourceQueue(project_path)

    started = queue.process_queue()

    if started:
        console.print(f"[green]Started {len(started)} tasks from queue:[/green]")
        for task_id in started:
            console.print(f"  • {task_id}")
    else:
        queue_status = queue.get_queue_status()
        if queue_status:
            console.print(f"[yellow]{len(queue_status)} tasks still waiting for resources[/yellow]")
        else:
            console.print("[dim]Queue is empty, nothing to process.[/dim]")
