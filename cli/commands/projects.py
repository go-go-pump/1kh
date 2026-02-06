"""
Projects command - List and switch between 1KH projects.

Usage:
    1kh projects              List all projects (shows active)
    1kh projects switch       Interactive project selector
    1kh projects switch NAME  Switch to project by name
    1kh projects add PATH     Register a new project
    1kh projects remove NAME  Unregister a project (doesn't delete files)
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from core.config import (
    get_known_projects,
    get_last_active_project,
    set_last_active_project,
    register_project,
    remove_project,
)

app = typer.Typer(no_args_is_help=False)
console = Console()


@app.callback(invoke_without_command=True)
def list_projects(ctx: typer.Context):
    """List all registered 1KH projects."""
    # If a subcommand was invoked, don't run the list
    if ctx.invoked_subcommand is not None:
        return

    projects = get_known_projects()
    active = get_last_active_project()
    active_path = active["path"] if active else None

    if not projects:
        console.print("[dim]No projects registered.[/dim]")
        console.print()
        console.print("Initialize a project with: [bold]1kh init[/bold]")
        console.print("Or register an existing one: [bold]1kh projects add /path/to/project[/bold]")
        return

    console.print()
    console.print("[bold]1KH Projects[/bold]")
    console.print()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("", width=2)  # Active indicator
    table.add_column("Name", style="bold")
    table.add_column("Path", style="dim")
    table.add_column("Phase")

    for proj in projects:
        is_active = proj["path"] == active_path
        indicator = "[green]●[/green]" if is_active else " "
        name = proj["name"]
        if is_active:
            name = f"[green]{name}[/green]"

        # Get phase description
        phase = proj.get("phase", 0)
        phase_names = {
            0: "Not started",
            1: "Grounding",
            2: "Listening",
            3: "Probing",
            4: "Structuring",
            5: "Committing",
            6: "Ready",
            7: "Running",
        }
        phase_desc = phase_names.get(phase, f"Phase {phase}")

        table.add_row(
            indicator,
            name,
            proj["path"],
            phase_desc,
        )

    console.print(table)
    console.print()
    console.print("[dim]● = active project[/dim]")
    console.print()
    console.print("Switch projects: [bold]1kh projects switch[/bold] or [bold]1kh projects switch NAME[/bold]")


@app.command("switch")
def switch_project(
    name: str = typer.Argument(None, help="Project name to switch to"),
):
    """Switch to a different project."""
    projects = get_known_projects()

    if not projects:
        console.print("[red]No projects registered.[/red]")
        raise typer.Exit(1)

    # If name provided, find and switch
    if name:
        # Find project by name (case-insensitive partial match)
        matches = [p for p in projects if name.lower() in p["name"].lower()]

        if not matches:
            console.print(f"[red]No project matching '{name}' found.[/red]")
            console.print()
            console.print("Available projects:")
            for p in projects:
                console.print(f"  • {p['name']}")
            raise typer.Exit(1)

        if len(matches) > 1:
            console.print(f"[yellow]Multiple projects match '{name}':[/yellow]")
            for p in matches:
                console.print(f"  • {p['name']}")
            console.print()
            console.print("Please be more specific.")
            raise typer.Exit(1)

        selected = matches[0]
    else:
        # Interactive selection
        console.print()
        console.print("[bold]Select a project:[/bold]")
        console.print()

        active = get_last_active_project()
        active_path = active["path"] if active else None

        for i, proj in enumerate(projects, 1):
            is_active = proj["path"] == active_path
            marker = "[green]●[/green]" if is_active else " "
            console.print(f"  {marker} [{i}] {proj['name']} [dim]({proj['path']})[/dim]")

        console.print()
        choice = Prompt.ask(
            "Enter number or name",
            default="1",
        )

        # Try to parse as number
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                selected = projects[idx]
            else:
                console.print("[red]Invalid selection.[/red]")
                raise typer.Exit(1)
        except ValueError:
            # Try as name
            matches = [p for p in projects if choice.lower() in p["name"].lower()]
            if not matches:
                console.print(f"[red]No project matching '{choice}'.[/red]")
                raise typer.Exit(1)
            selected = matches[0]

    # Switch to selected project
    set_last_active_project(Path(selected["path"]))

    console.print()
    console.print(f"[green]✓[/green] Switched to [bold]{selected['name']}[/bold]")
    console.print(f"  [dim]{selected['path']}[/dim]")


@app.command("add")
def add_project(
    path: str = typer.Argument(..., help="Path to project directory"),
    name: str = typer.Option(None, "--name", "-n", help="Project name (defaults to directory name)"),
):
    """Register an existing project directory."""
    project_path = Path(path).resolve()

    if not project_path.exists():
        console.print(f"[red]Path does not exist: {project_path}[/red]")
        raise typer.Exit(1)

    # Check if it's a 1KH project
    if not (project_path / ".1kh").exists():
        console.print(f"[yellow]Warning: {project_path} doesn't have a .1kh directory.[/yellow]")
        console.print("This may not be an initialized 1KH project.")
        console.print()
        from rich.prompt import Confirm
        if not Confirm.ask("Register anyway?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    # Use directory name if no name provided
    project_name = name or project_path.name

    # Check for duplicates
    existing = get_known_projects()
    for proj in existing:
        if proj["path"] == str(project_path):
            console.print(f"[yellow]Project already registered: {proj['name']}[/yellow]")
            return
        if proj["name"].lower() == project_name.lower():
            console.print(f"[yellow]A project named '{project_name}' already exists.[/yellow]")
            console.print("Use --name to specify a different name.")
            raise typer.Exit(1)

    # Register
    register_project(project_path, project_name)

    console.print(f"[green]✓[/green] Registered project [bold]{project_name}[/bold]")
    console.print(f"  [dim]{project_path}[/dim]")
    console.print()
    console.print("This is now your active project.")


@app.command("remove")
def remove_project_cmd(
    name: str = typer.Argument(..., help="Project name to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Unregister a project (doesn't delete files)."""
    projects = get_known_projects()

    # Find project
    matches = [p for p in projects if name.lower() in p["name"].lower()]

    if not matches:
        console.print(f"[red]No project matching '{name}' found.[/red]")
        raise typer.Exit(1)

    if len(matches) > 1:
        console.print(f"[yellow]Multiple projects match '{name}':[/yellow]")
        for p in matches:
            console.print(f"  • {p['name']}")
        console.print("Please be more specific.")
        raise typer.Exit(1)

    selected = matches[0]

    if not force:
        from rich.prompt import Confirm
        console.print(f"Remove project [bold]{selected['name']}[/bold] from 1KH?")
        console.print(f"  [dim]{selected['path']}[/dim]")
        console.print()
        console.print("[dim]This only removes the registration. Project files are not deleted.[/dim]")
        if not Confirm.ask("Continue?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    remove_project(Path(selected["path"]))

    console.print(f"[green]✓[/green] Removed [bold]{selected['name']}[/bold] from registered projects.")


@app.command("current")
def show_current():
    """Show the current active project."""
    active = get_last_active_project()

    if not active:
        console.print("[dim]No active project.[/dim]")
        console.print("Run [bold]1kh projects switch[/bold] to select one.")
        return

    console.print()
    console.print(Panel(
        f"[bold]{active['name']}[/bold]\n"
        f"[dim]{active['path']}[/dim]",
        title="Active Project",
        border_style="green",
    ))
