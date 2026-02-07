"""
1kh operate - Transition to OPERATE phase with SLA monitoring.

This command:
1. Transitions the project from BUILD to OPERATE phase
2. Auto-generates operations.md from utility subtype if not exists
3. Sets up SLA monitoring for REFLECTION loop
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from core.models import (
    SystemPhase,
    UtilitySubtype,
    UTILITY_OPERATIONAL_METRICS,
    UTILITY_SUBTYPE_METRICS,
)

app = typer.Typer()
console = Console()


def _load_ceremony_state(project_path: Path) -> Optional[dict]:
    """Load ceremony state from project."""
    state_file = project_path / ".1kh" / "state" / "ceremony_state.json"
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, IOError):
        return None


def _save_ceremony_state(project_path: Path, state: dict):
    """Save ceremony state to project."""
    state_file = project_path / ".1kh" / "state" / "ceremony_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2))


def _get_utility_subtype(state: dict) -> Optional[str]:
    """Extract utility subtype from ceremony state."""
    north_star = state.get("north_star", {})
    return north_star.get("utility_subtype")


def _generate_operations_md(
    utility_subtype: str,
    project_name: str,
) -> str:
    """Generate operations.md content from utility subtype."""

    # Get subtype info
    subtype_enum = UtilitySubtype(utility_subtype) if utility_subtype else UtilitySubtype.POC
    subtype_info = UTILITY_SUBTYPE_METRICS.get(subtype_enum, {})
    operational_metrics = UTILITY_OPERATIONAL_METRICS.get(utility_subtype, [])

    lines = [
        "# Operations",
        "",
        f"Operational configuration for **{project_name}** in OPERATE phase.",
        "",
        "> **Edit this file** to adjust SLA targets. REFLECTION monitors these metrics.",
        "",
        f"**System Phase:** OPERATE",
        f"**Utility Subtype:** {utility_subtype.upper() if utility_subtype else 'UNKNOWN'}",
        f"**Primary KPI:** {subtype_info.get('primary_kpi', 'User-defined')}",
        "",
        "---",
        "",
        "## SLA Targets",
        "",
    ]

    if operational_metrics:
        # Create markdown table
        lines.append("| Metric | Target | Warning | Critical | Unit | Current |")
        lines.append("|--------|--------|---------|----------|------|---------|")

        for metric in operational_metrics:
            name = metric.get("display_name", metric.get("name", "Unknown"))
            target = metric.get("target", "TBD")
            warning = metric.get("warning", "TBD")
            critical = metric.get("critical", "TBD")
            unit = metric.get("unit", "")

            # Format based on whether higher is better
            if metric.get("higher_is_better", True):
                lines.append(f"| {name} | ≥{target}{unit} | <{warning}{unit} | <{critical}{unit} | {unit} | TBD |")
            else:
                lines.append(f"| {name} | ≤{target}{unit} | >{warning}{unit} | >{critical}{unit} | {unit} | TBD |")
    else:
        lines.append("*No default metrics for this utility subtype. Add your own below.*")
        lines.append("")
        lines.append("| Metric | Target | Warning | Critical | Unit | Current |")
        lines.append("|--------|--------|---------|----------|------|---------|")
        lines.append("| (add metric) | TBD | TBD | TBD | | TBD |")

    lines.extend([
        "",
        "---",
        "",
        "## Alerting",
        "",
        "| Condition | Action |",
        "|-----------|--------|",
        "| Critical threshold breached | Immediate escalation |",
        "| Warning threshold breached | Daily digest |",
        "| All metrics healthy | No action |",
        "",
        "---",
        "",
        "## Health Check Configuration",
        "",
        "```yaml",
        "check_interval_minutes: 5",
        "alert_channels:",
        "  - cli  # 1kh escalations",
        "  # - email",
        "  # - slack",
        "```",
        "",
        "---",
        "",
        f"*Generated: {datetime.utcnow().isoformat()}*",
        f"*Utility Subtype: {utility_subtype}*",
    ])

    return "\n".join(lines)


@app.callback(invoke_without_command=True)
def operate(
    path: Optional[Path] = typer.Argument(
        None,
        help="Project directory. Defaults to current directory.",
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Overwrite existing operations.md",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be generated without writing files",
    ),
):
    """
    Transition project to OPERATE phase with SLA monitoring.

    This command:
    - Generates operations.md from your utility subtype (if not exists)
    - Sets system phase to OPERATE
    - Enables REFLECTION to monitor SLAs

    Run after your core features are built and deployed.
    """
    project_path = (path or Path.cwd()).resolve()

    # Check if this is a 1KH project
    if not (project_path / ".1kh").exists():
        console.print("[red]Error: Not a 1KH project. Run '1kh init' first.[/red]")
        raise typer.Exit(1)

    console.print()
    console.print(Panel.fit(
        "[bold cyan]Transitioning to OPERATE Phase[/bold cyan]",
        subtitle="SLA Monitoring Setup",
    ))
    console.print()

    # Load ceremony state
    state = _load_ceremony_state(project_path)
    if not state:
        console.print("[red]Error: Could not load ceremony state. Run '1kh init' first.[/red]")
        raise typer.Exit(1)

    project_name = state.get("project_name", project_path.name)
    utility_subtype = _get_utility_subtype(state)

    # Show current state
    console.print(f"[bold]Project:[/bold] {project_name}")
    console.print(f"[bold]Location:[/bold] {project_path}")
    console.print(f"[bold]Utility Subtype:[/bold] {utility_subtype or 'not set'}")
    console.print()

    # Check operations.md
    operations_file = project_path / "operations.md"
    operations_exists = operations_file.exists()

    if operations_exists and not force:
        console.print("[green]✓[/green] operations.md already exists")
        console.print("[dim]  Use --force to regenerate[/dim]")
        console.print()

        # Still update phase if needed
        current_phase = state.get("preferences", {}).get("custom", {}).get("system_phase", "build")
        if current_phase != "operate":
            if not dry_run:
                if "preferences" not in state:
                    state["preferences"] = {}
                if "custom" not in state["preferences"]:
                    state["preferences"]["custom"] = {}
                state["preferences"]["custom"]["system_phase"] = "operate"
                _save_ceremony_state(project_path, state)
            console.print(f"[green]✓[/green] Phase updated: BUILD → OPERATE")
        else:
            console.print(f"[dim]Already in OPERATE phase[/dim]")

        return

    # Generate operations.md
    if not utility_subtype:
        console.print("[yellow]Warning: No utility subtype set.[/yellow]")
        console.print("[dim]  Generic operations.md will be generated.[/dim]")
        console.print("[dim]  Set utility subtype via 1kh init or edit ceremony_state.json[/dim]")
        console.print()

    # Get metrics for this subtype
    operational_metrics = UTILITY_OPERATIONAL_METRICS.get(utility_subtype, [])

    if operational_metrics:
        console.print(f"[bold]SLA Metrics for {utility_subtype}:[/bold]")
        console.print()

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="white")
        table.add_column("Target", style="green")
        table.add_column("Warning", style="yellow")
        table.add_column("Critical", style="red")

        for metric in operational_metrics:
            name = metric.get("display_name", metric.get("name"))
            unit = metric.get("unit", "")
            target = f"{metric.get('target')}{unit}"
            warning = f"{metric.get('warning')}{unit}"
            critical = f"{metric.get('critical')}{unit}"
            table.add_row(name, target, warning, critical)

        console.print(table)
        console.print()

    # Confirm
    if not dry_run:
        action = "Overwrite" if operations_exists else "Create"
        if not Confirm.ask(f"{action} operations.md and enable OPERATE phase?"):
            console.print("[dim]Aborted.[/dim]")
            raise typer.Exit(0)

    # Generate content
    content = _generate_operations_md(utility_subtype or "poc", project_name)

    if dry_run:
        console.print()
        console.print("[bold]Would generate operations.md:[/bold]")
        console.print()
        console.print(Panel(content, title="operations.md", border_style="dim"))
        return

    # Write operations.md
    operations_file.write_text(content)
    console.print()
    console.print(f"[green]✓[/green] Created {operations_file}")

    # Update phase
    if "preferences" not in state:
        state["preferences"] = {}
    if "custom" not in state["preferences"]:
        state["preferences"]["custom"] = {}
    state["preferences"]["custom"]["system_phase"] = "operate"
    _save_ceremony_state(project_path, state)
    console.print(f"[green]✓[/green] Phase updated: BUILD → OPERATE")

    # Summary
    console.print()
    console.print(Panel.fit(
        "[bold green]OPERATE Phase Enabled[/bold green]\n\n"
        "[bold]What happens now:[/bold]\n"
        "• REFLECTION monitors SLA metrics in operations.md\n"
        "• Dashboard tracks operational health\n"
        "• Escalations created when SLAs breached\n"
        "• IMAGINATION can suggest optimizations\n\n"
        "[bold]Next steps:[/bold]\n"
        "• Review and customize operations.md\n"
        "• Set up health check pings from your service\n"
        "• Run '1kh reflect' to see operational status",
        title="Setup Complete",
        border_style="green",
    ))


@app.command()
def show():
    """Show current operational status and SLA health."""
    project_path = Path.cwd().resolve()

    operations_file = project_path / "operations.md"
    if not operations_file.exists():
        console.print("[yellow]No operations.md found. Run '1kh operate' to set up.[/yellow]")
        raise typer.Exit(1)

    console.print()
    console.print("[bold]Operational Status[/bold]")
    console.print()
    console.print("[yellow]Status monitoring not yet implemented.[/yellow]")
    console.print("[dim]This will show live SLA status from dashboard.[/dim]")
