"""
1kh config - View or modify configuration.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def show_config():
    """
    Display current configuration.
    """
    # TODO: Load from .1kh/config.yaml

    console.print(Panel.fit(
        "[yellow]Config management not yet implemented.[/yellow]\n\n"
        "Configuration includes:\n"
        "- deployment.psd_level (0-3)\n"
        "- communication channel preferences\n"
        "- safeguard thresholds\n"
        "- API connections",
        title="1kh config",
    ))


@app.command()
def get(
    key: str = typer.Argument(..., help="Config key (e.g., deployment.psd_level)"),
):
    """Get a specific config value."""
    console.print(f"[yellow]Getting {key} not yet implemented.[/yellow]")


@app.command()
def set(
    key: str = typer.Argument(..., help="Config key (e.g., deployment.psd_level)"),
    value: str = typer.Argument(..., help="New value"),
):
    """Set a config value."""
    console.print(f"[yellow]Setting {key}={value} not yet implemented.[/yellow]")


@app.command()
def connect():
    """Re-run the connection setup for API keys and services."""
    console.print("[yellow]Connection setup not yet implemented.[/yellow]")


@app.command()
def validate():
    """Validate all connections are working."""
    console.print("[yellow]Connection validation not yet implemented.[/yellow]")
