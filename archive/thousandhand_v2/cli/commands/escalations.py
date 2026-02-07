"""
1kh escalations - View and respond to pending escalations.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def list_escalations(
    tier: str = typer.Option(
        None,
        "--tier", "-t",
        help="Filter by tier: BLOCKING, ADVISORY, FYI",
    ),
    all_: bool = typer.Option(
        False,
        "--all", "-a",
        help="Show resolved escalations too",
    ),
):
    """
    List pending escalations that need human attention.
    """
    # TODO: Load escalations from .1kh/escalations/ or cloud state

    console.print(Panel.fit(
        "[yellow]Escalation management not yet implemented.[/yellow]\n\n"
        "This will show:\n"
        "- BLOCKING escalations (system waiting for you)\n"
        "- ADVISORY escalations (input wanted, has default)\n"
        "- FYI escalations (informational)\n\n"
        "You'll be able to respond directly from CLI.",
        title="1kh escalations",
    ))


@app.command()
def respond(
    escalation_id: str = typer.Argument(..., help="Escalation ID to respond to"),
):
    """Respond to a specific escalation."""
    # TODO: Load escalation, show options, capture response, update state
    console.print(f"[yellow]Responding to {escalation_id} not yet implemented.[/yellow]")


@app.command()
def dismiss(
    escalation_id: str = typer.Argument(..., help="Escalation ID to dismiss"),
):
    """Dismiss an FYI or ADVISORY escalation (use default if applicable)."""
    console.print(f"[yellow]Dismissing {escalation_id} not yet implemented.[/yellow]")
