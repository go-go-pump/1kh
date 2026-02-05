"""
Forecast command - Business simulation without execution.

Usage:
    1kh forecast                    Run live forecast (real Claude, captures trace)
    1kh forecast --mock             Fast mock mode (no API calls)
    1kh forecast --replay <id>      Replay with different inputs
    1kh forecast --runs N           Monte Carlo with N simulations
    1kh forecast list               List saved traces
    1kh forecast compare <t1> <t2>  Compare two traces (future)

Configurable Variables:
    --human-quality     perfect, good, mediocre, poor (default: good)
    --market            optimistic, realistic, pessimistic (default: realistic)
    --chaos             none, low, medium, high (default: none)
    --cycles            Max cycles to run (default: 50)
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

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
def forecast_main(
    ctx: typer.Context,
    project_path: str = typer.Option(
        None, "--project", "-p",
        help="Path to 1KH project",
    ),
    mock: bool = typer.Option(
        False, "--mock", "-m",
        help="Mock mode - no API calls, fast testing",
    ),
    replay: str = typer.Option(
        None, "--replay", "-r",
        help="Replay from trace ID",
    ),
    runs: int = typer.Option(
        0, "--runs", "-n",
        help="Number of Monte Carlo runs (0 = single run)",
    ),
    cycles: int = typer.Option(
        50, "--cycles", "-c",
        help="Maximum cycles to simulate",
    ),
    human_quality: str = typer.Option(
        "good", "--human-quality", "--human",
        help="Simulated human quality: perfect, good, mediocre, poor",
    ),
    market: str = typer.Option(
        "realistic", "--market",
        help="Market response: optimistic, realistic, pessimistic",
    ),
    chaos: str = typer.Option(
        "none", "--chaos",
        help="Chaos level: none, low, medium, high",
    ),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Force run even if foundation has drifted",
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q",
        help="Minimal output",
    ),
):
    """
    Simulate business trajectory without executing real work.

    Preview your journey, estimate costs/timeline, and identify risks
    before committing resources.

    \b
    MODES:
      (default)    Live mode - real Claude, captures trace
      --mock       Mock mode - no API calls, fast testing
      --replay     Replay mode - use cached responses
      --runs N     Scenario mode - Monte Carlo simulations

    \b
    EXAMPLES:
      1kh forecast                          # Live forecast
      1kh forecast --mock --cycles 10       # Quick mock test
      1kh forecast --replay trace_xxx       # Replay with cached data
      1kh forecast --runs 100               # Monte Carlo analysis
    """
    # If a subcommand was invoked, don't run the main forecast
    if ctx.invoked_subcommand is not None:
        return

    path = resolve_project_path(project_path)

    # Determine mode
    if mock:
        mode = "mock"
    elif replay:
        mode = "replay"
    else:
        mode = "live"

    if runs > 0:
        _run_scenario_mode(path, runs, cycles, human_quality, market, chaos, replay, quiet)
    else:
        _run_single_forecast(path, mode, cycles, human_quality, market, chaos, replay, force, quiet)


def _run_single_forecast(
    path: Path,
    mode: str,
    cycles: int,
    human_quality: str,
    market: str,
    chaos: str,
    replay_trace: str | None,
    force: bool,
    quiet: bool,
):
    """Run a single forecast."""
    from core.forecast import ForecastRunner, ForecastVariables, TraceManager

    variables = ForecastVariables(
        human_quality=human_quality,
        market_response=market,
        chaos_level=chaos,
    )

    # Check for foundation drift on replay
    if mode == "replay" and replay_trace:
        trace_manager = TraceManager(path)
        drift = trace_manager.check_foundation_drift(replay_trace)
        if drift and not force:
            console.print("[yellow]Foundation has changed since trace was created:[/yellow]")
            for file in drift:
                console.print(f"  • {file}")
            console.print()
            console.print("Use [bold]--force[/bold] to run anyway, or create a new trace.")
            raise typer.Exit(1)

    if not quiet:
        mode_desc = {
            "mock": "[cyan]Mock[/cyan] - No API calls",
            "live": "[green]Live[/green] - Real Claude API",
            "replay": f"[yellow]Replay[/yellow] - {replay_trace}",
        }
        console.print()
        console.print(Panel(
            f"[bold]Business Forecast[/bold]\n\n"
            f"Mode: {mode_desc[mode]}\n"
            f"Max Cycles: {cycles}\n\n"
            f"[dim]Variables:[/dim]\n"
            f"  Human Quality: {human_quality}\n"
            f"  Market Response: {market}\n"
            f"  Chaos Level: {chaos}",
            border_style="cyan",
        ))
        console.print()

    runner = ForecastRunner(
        project_path=path,
        mode=mode,
        variables=variables,
        max_cycles=cycles,
        trace_id=replay_trace,
    )

    # Run with progress
    if quiet:
        outcome = asyncio.run(runner.run())
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total} cycles"),
            console=console,
        ) as progress:
            task = progress.add_task("Running forecast...", total=cycles)

            async def run_with_progress():
                # We can't easily hook into cycle progress, so just run
                return await runner.run()

            outcome = asyncio.run(run_with_progress())
            progress.update(task, completed=outcome.cycles_completed)

    # Display results
    _display_outcome(outcome, runner.trace_id, quiet)


def _run_scenario_mode(
    path: Path,
    num_runs: int,
    cycles: int,
    human_quality: str,
    market: str,
    chaos: str,
    replay_trace: str | None,
    quiet: bool,
):
    """Run Monte Carlo simulations."""
    from core.forecast import ScenarioRunner, ForecastVariables

    variables = ForecastVariables(
        human_quality=human_quality,
        market_response=market,
        chaos_level=chaos,
    )

    if not quiet:
        console.print()
        console.print(Panel(
            f"[bold]Monte Carlo Forecast[/bold]\n\n"
            f"Runs: {num_runs}\n"
            f"Max Cycles per Run: {cycles}\n\n"
            f"[dim]Randomizing human quality, market response, and chaos[/dim]",
            border_style="magenta",
        ))
        console.print()

    runner = ScenarioRunner(
        project_path=path,
        variables=variables,
        num_runs=num_runs,
        max_cycles=cycles,
        trace_id=replay_trace,
    )

    # Run with progress
    completed = [0]

    def on_run_complete(run_num: int, outcome):
        completed[0] = run_num

    runner.on_run_complete = on_run_complete

    if quiet:
        results = asyncio.run(runner.run())
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total} runs"),
            console=console,
        ) as progress:
            task = progress.add_task("Running scenarios...", total=num_runs)

            async def run_with_progress():
                result = await runner.run()
                return result

            # Poll for progress (simple approach)
            import threading

            result_holder = [None]

            def run_async():
                result_holder[0] = asyncio.run(runner.run())

            thread = threading.Thread(target=run_async)
            thread.start()

            while thread.is_alive():
                progress.update(task, completed=completed[0])
                thread.join(timeout=0.5)

            results = result_holder[0]
            progress.update(task, completed=num_runs)

    # Display results
    _display_scenario_results(results, quiet)


def _display_outcome(outcome, trace_id: str, quiet: bool):
    """Display forecast outcome."""
    if quiet:
        status = "REACHED" if outcome.target_reached else "NOT REACHED"
        console.print(f"{status} | {outcome.cycles_completed} cycles | ${outcome.final_revenue:,.0f} | {trace_id}")
        return

    # Status color
    if outcome.target_reached:
        status_text = "[bold green]TARGET REACHED[/bold green]"
        border_style = "green"
    else:
        status_text = f"[bold yellow]{outcome.progress_pct:.1f}% Progress[/bold yellow]"
        border_style = "yellow"

    # Risk color
    risk_colors = {"low": "green", "medium": "yellow", "high": "red"}
    risk_color = risk_colors.get(outcome.risk_level, "white")

    console.print()
    console.print(Panel(
        f"{status_text}\n\n"
        f"[bold]Timeline:[/bold]\n"
        f"  Cycles: {outcome.cycles_completed}\n"
        f"  Estimated Time: {outcome.time_estimate}\n\n"
        f"[bold]Financial:[/bold]\n"
        f"  Final Revenue: [bold]${outcome.final_revenue:,.0f}[/bold]\n"
        f"  Target: ${outcome.target_revenue:,.0f}\n"
        f"  API Cost: ~${outcome.estimated_api_cost:.2f}\n\n"
        f"[bold]Risk Assessment:[/bold]\n"
        f"  Risk Level: [{risk_color}]{outcome.risk_level.upper()}[/{risk_color}]\n"
        f"  Success Rate: {outcome.success_rate:.0%}\n"
        f"  Human Decisions Required: {outcome.human_decisions_required}\n\n"
        f"[dim]Trace saved: {trace_id}[/dim]",
        title="[bold]FORECAST SUMMARY[/bold]",
        border_style=border_style,
    ))


def _display_scenario_results(results: dict, quiet: bool):
    """Display Monte Carlo results."""
    if quiet:
        console.print(f"Success: {results['success_rate']:.0%} | Avg Cycles: {results['cycles']['average']:.0f}")
        return

    console.print()
    console.print(Panel(
        f"[bold]Results from {results['num_runs']} simulations[/bold]\n\n"
        f"[bold]Success Rate:[/bold]\n"
        f"  Target Reached: [bold]{results['success_rate']:.0%}[/bold] ({results['successes']}/{results['num_runs']})\n\n"
        f"[bold]Cycles Distribution:[/bold]\n"
        f"  Average: {results['cycles']['average']:.0f}\n"
        f"  Range: {results['cycles']['min']} - {results['cycles']['max']}\n\n"
        f"[bold]Revenue Distribution:[/bold]\n"
        f"  Average: ${results['revenue']['average']:,.0f}\n"
        f"  Range: ${results['revenue']['min']:,.0f} - ${results['revenue']['max']:,.0f}\n\n"
        f"[bold]Time Estimate:[/bold]\n"
        f"  Median: {results['time']['estimate']}\n\n"
        f"[bold]Risk Distribution:[/bold]\n"
        f"  Low: {results['risk_distribution']['low']}\n"
        f"  Medium: {results['risk_distribution']['medium']}\n"
        f"  High: {results['risk_distribution']['high']}",
        title="[bold]SCENARIO ANALYSIS[/bold]",
        border_style="magenta",
    ))


@app.command("list")
def list_traces(
    project_path: str = typer.Option(None, "--project", "-p"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max traces to show"),
):
    """List saved forecast traces."""
    from core.forecast import TraceManager

    path = resolve_project_path(project_path)
    trace_manager = TraceManager(path)
    traces = trace_manager.list_traces()

    if not traces:
        console.print("[dim]No forecast traces found.[/dim]")
        console.print("Run [bold]1kh forecast[/bold] to create one.")
        return

    console.print()
    console.print(f"[bold]Forecast Traces[/bold] ({len(traces)} total)")
    console.print()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Trace ID", style="cyan")
    table.add_column("Created", style="dim")
    table.add_column("Mode")
    table.add_column("Cycles")
    table.add_column("Result")
    table.add_column("Revenue")

    for trace in traces[:limit]:
        # Format created date
        try:
            created = datetime.fromisoformat(trace["created_at"])
            created_str = created.strftime("%Y-%m-%d %H:%M")
        except (ValueError, KeyError):
            created_str = "?"

        # Format outcome
        outcome = trace.get("outcome")
        if outcome:
            if outcome.get("target_reached"):
                result = "[green]Target Reached[/green]"
            else:
                result = f"[yellow]{outcome.get('progress_pct', 0):.0f}%[/yellow]"
            revenue = f"${outcome.get('final_revenue', 0):,.0f}"
        else:
            result = "[dim]In Progress[/dim]"
            revenue = "-"

        table.add_row(
            trace["trace_id"],
            created_str,
            trace["mode"],
            str(trace["cycles_completed"]),
            result,
            revenue,
        )

    console.print(table)
    console.print()
    console.print("[dim]Use 'forecast --replay <trace_id>' to replay a trace[/dim]")


@app.command("compare")
def compare_traces(
    trace1: str = typer.Argument(..., help="First trace ID"),
    trace2: str = typer.Argument(..., help="Second trace ID"),
    project_path: str = typer.Option(None, "--project", "-p"),
):
    """Compare two forecast traces (placeholder for future)."""
    console.print()
    console.print("[yellow]Compare feature coming soon![/yellow]")
    console.print()
    console.print("This will show side-by-side comparison of:")
    console.print("  • Timeline and cycles")
    console.print("  • Revenue progression")
    console.print("  • Human decisions made")
    console.print("  • Risk assessment differences")
    console.print()
    console.print(f"Traces to compare:")
    console.print(f"  1. {trace1}")
    console.print(f"  2. {trace2}")


@app.command("delete")
def delete_trace(
    trace_id: str = typer.Argument(..., help="Trace ID to delete"),
    project_path: str = typer.Option(None, "--project", "-p"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a forecast trace."""
    from core.forecast import TraceManager

    path = resolve_project_path(project_path)
    trace_manager = TraceManager(path)

    # Check trace exists
    if not trace_manager.get_trace(trace_id):
        console.print(f"[red]Trace not found: {trace_id}[/red]")
        raise typer.Exit(1)

    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"Delete trace {trace_id}?", default=False):
            console.print("[yellow]Cancelled[/yellow]")
            return

    if trace_manager.delete_trace(trace_id):
        console.print(f"[green]✓[/green] Deleted: {trace_id}")
    else:
        console.print(f"[red]Failed to delete: {trace_id}[/red]")
