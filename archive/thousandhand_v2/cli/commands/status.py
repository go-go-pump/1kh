"""
1kh status - Check tree health and active branches.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def show_status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed status"),
):
    """
    Display current tree health, active branches, and fruit summary.
    """
    # TODO: Load tree state from .1kh/state/tree_state.json
    # TODO: Connect to Temporal to get loop and workflow status

    console.print(Panel.fit(
        "[yellow]Status check not yet implemented.[/yellow]\n\n"
        "This will show:\n"
        "- Tree health (roots, trunk, branches)\n"
        "- Active hypotheses and their viability scores\n"
        "- Recent fruit (KPIs, outcomes)\n"
        "- Pending escalations\n"
        "- Loop status (IMAGINATION, INTENT, WORK, EXECUTION)",
        title="1kh status",
    ))


@app.command()
def branches():
    """List all branches and their health."""
    console.print("[yellow]Not yet implemented.[/yellow]")


@app.command()
def fruit():
    """Show recent outcomes and KPIs."""
    console.print("[yellow]Not yet implemented.[/yellow]")


@app.command()
def loops():
    """Show status of coordination loops."""
    console.print("[yellow]Not yet implemented.[/yellow]")
