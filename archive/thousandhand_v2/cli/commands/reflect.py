"""
Reflect command - Trajectory analysis and pivot detection.

Usage:
    1kh reflect              Run reflection analysis
    1kh reflect --apply      Apply auto-acceptable recommendations
    1kh reflect --trust X    Set trust level (manual/guided/autonomous)
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from core.config import get_last_active_project

app = typer.Typer(no_args_is_help=False)
console = Console()


def resolve_project_path(project_path: str | None) -> Path:
    """Resolve the project path from arg or last active."""
    if project_path:
        return Path(project_path).resolve()

    last_project = get_last_active_project()
    if not last_project:
        console.print("[red]No active project found.[/red]")
        console.print("Run [bold]1kh init[/bold] first, or specify --project")
        raise typer.Exit(1)

    return Path(last_project["path"])


@app.callback(invoke_without_command=True)
def reflect(
    ctx: typer.Context,
    project_path: str = typer.Option(None, "--project", "-p"),
    apply: bool = typer.Option(False, "--apply", "-a", help="Apply auto-acceptable recommendations"),
    trust: str = typer.Option("guided", "--trust", "-t", help="Trust level: manual, guided, autonomous"),
    cycle: int = typer.Option(0, "--cycle", "-c", help="Cycle number (0 = current)"),
):
    """
    Run REFLECTION analysis.

    Analyzes system completeness, trajectory, and generates recommendations.

    Trust levels:
      manual     - All recommendations require approval
      guided     - Auto-accept AUGMENT/OPTIMIZE, prompt for PIVOT
      autonomous - Auto-accept everything within Oracle bounds
    """
    if ctx.invoked_subcommand is not None:
        return

    path = resolve_project_path(project_path)

    console.print()
    console.print(Panel(
        "[bold magenta]🔮 REFLECTION Analysis[/bold magenta]\n\n"
        "Analyzing:\n"
        "  • System completeness (can we generate revenue?)\n"
        "  • Trajectory (are we on track?)\n"
        "  • Recommendations (what should we do next?)\n\n"
        f"Trust level: [bold]{trust}[/bold]",
        border_style="magenta",
    ))
    console.print()

    from core.reflection import ReflectionEngine, TrustLevel
    from core.dashboard import Dashboard

    # Run reflection
    dashboard = Dashboard(path)
    engine = ReflectionEngine(path, dashboard=dashboard)

    with console.status("[bold blue]Analyzing system state...[/bold blue]"):
        result = engine.reflect(cycle_number=cycle)

    # Display results
    _display_reflection_result(result)

    # Handle recommendations based on trust level
    trust_level = TrustLevel(trust)

    if result.recommendations:
        auto_accept, needs_approval = engine.filter_recommendations_by_trust(
            result.recommendations,
            trust_level,
        )

        if auto_accept and apply:
            console.print()
            console.print("[bold green]Auto-accepting recommendations:[/bold green]")
            for rec in auto_accept:
                console.print(f"  ✓ {rec.title}")

            # Apply recommendations
            hypotheses = engine.apply_recommendations(auto_accept)

            if hypotheses:
                console.print()
                console.print(f"[green]Generated {len(hypotheses)} new hypotheses:[/green]")
                for hyp in hypotheses:
                    console.print(f"  • {hyp['id']}: {hyp['description'][:50]}...")

        elif auto_accept and not apply:
            console.print()
            console.print("[dim]Use --apply to auto-accept these recommendations:[/dim]")
            for rec in auto_accept:
                console.print(f"  • {rec.title}")

        if needs_approval:
            console.print()
            console.print("[yellow]These recommendations require your approval:[/yellow]")

            for rec in needs_approval:
                _display_recommendation_detail(rec)

                if Confirm.ask(f"Apply '{rec.title}'?", default=False):
                    hypotheses = engine.apply_recommendations([rec])
                    console.print(f"  [green]✓ Applied - generated {len(hypotheses)} hypotheses[/green]")
                else:
                    console.print(f"  [dim]Skipped[/dim]")

    # Save report
    _save_reflection_report(path, result)


def _display_reflection_result(result):
    """Display reflection result in CLI."""
    from core.reflection import ReflectionResult

    # Status header
    status_color = {
        "healthy": "green",
        "warning": "yellow",
        "critical": "red",
    }.get(result.status, "white")

    status_icon = {
        "healthy": "✓",
        "warning": "⚡",
        "critical": "⚠️",
    }.get(result.status, "?")

    console.print(Panel(
        f"[bold {status_color}]{status_icon} Status: {result.status.upper()}[/bold {status_color}]",
        border_style=status_color,
    ))
    console.print()

    # System Completeness
    console.print("[bold]System Completeness[/bold]")
    console.print()

    comp = result.completeness
    table = Table(show_header=True, header_style="bold")
    table.add_column("Component")
    table.add_column("Status")

    for comp_name in ["Product", "Payment", "Channel", "Fulfillment"]:
        if comp_name in comp.live_components:
            status = "[green]✓ Live[/green]"
        elif comp_name in comp.building_components:
            status = "[blue]◐ Building[/blue]"
        else:
            status = "[red]✗ Missing[/red]"
        table.add_row(comp_name, status)

    console.print(table)
    console.print()

    if not comp.can_generate_revenue:
        console.print(Panel(
            "[bold red]⚠️ Cannot Generate Revenue[/bold red]\n\n" +
            "\n".join(f"  • {b}" for b in comp.blockers),
            border_style="red",
        ))
        console.print()

    # Trajectory
    console.print("[bold]Trajectory Analysis[/bold]")
    console.print()

    traj = result.trajectory
    traj_table = Table(show_header=False)
    traj_table.add_column("Metric", style="dim")
    traj_table.add_column("Value")

    traj_table.add_row("Current", f"${traj.current_value:,.0f}")
    traj_table.add_row("Target", f"${traj.target_value:,.0f}")
    traj_table.add_row("Velocity", f"${traj.velocity_per_cycle:,.0f}/cycle")
    traj_table.add_row("Trend", traj.velocity_trend)
    traj_table.add_row("Time to Goal", traj.time_to_goal or "Unknown")

    console.print(traj_table)
    console.print()

    if traj.warning:
        console.print(f"[yellow]⚠️ {traj.warning}[/yellow]")
        console.print()

    # Recommendations
    if result.recommendations:
        console.print("[bold]Recommendations[/bold]")
        console.print()

        for i, rec in enumerate(result.recommendations, 1):
            rec_type = rec.type.value
            icon = {"augment": "🔧", "optimize": "📈", "pivot": "🔄", "continue": "➡️"}.get(rec_type, "?")
            type_color = {"augment": "green", "optimize": "yellow", "pivot": "red", "continue": "blue"}.get(rec_type, "white")

            console.print(f"  {i}. {icon} [{type_color}]{rec.title}[/{type_color}]")
            console.print(f"     [dim]{rec.description}[/dim]")
            if rec.requires_human:
                console.print(f"     [yellow](Requires approval)[/yellow]")
            console.print()


def _display_recommendation_detail(rec):
    """Display detailed recommendation for approval."""
    console.print()
    console.print(Panel(
        f"[bold]{rec.title}[/bold]\n\n"
        f"{rec.description}\n\n"
        f"[dim]Rationale: {rec.rationale}[/dim]\n\n"
        f"[bold]Suggested actions:[/bold]\n" +
        "\n".join(f"  • {h['description']}" for h in rec.suggested_hypotheses),
        title=f"[yellow]🔄 PIVOT Recommendation[/yellow]" if rec.type.value == "pivot" else f"[green]🔧 Recommendation[/green]",
        border_style="yellow" if rec.type.value == "pivot" else "green",
    ))


def _save_reflection_report(path: Path, result):
    """Save reflection report to file."""
    from core.report import ReportGenerator
    from core.dashboard import Dashboard

    dashboard = Dashboard(path)
    state = dashboard.compute_state()

    # Generate HTML report
    generator = ReportGenerator(path)

    report_path = generator.generate(
        cycle_number=result.cycle_number or 0,
        cycle_result={
            "hypotheses_generated": 0,
            "hypotheses_approved": 0,
            "tasks_executed": 0,
            "tasks_succeeded": 0,
            "revenue_delta": 0,
            "signups_delta": 0,
        },
        reflection_result=result.to_dict(),
        north_star_name=state.north_star.objective,
        north_star_target=state.north_star.target_value,
        north_star_current=state.north_star.current_value,
    )

    console.print()
    console.print(f"[dim]Report saved: {report_path}[/dim]")


@app.command("status")
def show_status(
    project_path: str = typer.Option(None, "--project", "-p"),
):
    """Show current system status."""
    path = resolve_project_path(project_path)

    from core.system_state import SystemStateManager

    manager = SystemStateManager(path)
    summary = manager.get_summary()

    console.print()
    console.print(Panel(
        f"[bold]System Status[/bold]\n\n"
        f"Mode: {summary['mode']}\n"
        f"Completeness: {summary['completeness']*100:.0f}%\n"
        f"Can Generate Revenue: {'✓ Yes' if summary['can_generate_revenue'] else '✗ No'}\n\n"
        f"[dim]{summary['revenue_capability']}[/dim]",
        border_style="cyan",
    ))

    # Components
    console.print()
    console.print("[bold]Components:[/bold]")
    for comp in summary["components"]:
        status_icon = {"live": "✓", "building": "◐", "planned": "○", "missing": "✗"}.get(comp["status"], "?")
        status_color = {"live": "green", "building": "blue", "planned": "dim", "missing": "red"}.get(comp["status"], "white")
        console.print(f"  [{status_color}]{status_icon}[/{status_color}] {comp['name']}: {comp['description']}")

    # Work in progress
    console.print()
    console.print(f"[dim]Active hypotheses: {summary['active_hypotheses']} | Active tasks: {summary['active_tasks']}[/dim]")


@app.command("clear")
def clear_state(
    project_path: str = typer.Option(None, "--project", "-p"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Clear system state (reset to fresh start)."""
    path = resolve_project_path(project_path)

    if not confirm:
        if not Confirm.ask("[yellow]This will reset all system state. Continue?[/yellow]", default=False):
            console.print("[dim]Cancelled[/dim]")
            return

    from core.system_state import SystemStateManager
    from core.dashboard import Dashboard

    # Clear system state
    manager = SystemStateManager(path)
    manager.clear()

    # Clear dashboard events
    dashboard = Dashboard(path)
    dashboard.event_log.clear()

    console.print("[green]✓ System state cleared[/green]")
