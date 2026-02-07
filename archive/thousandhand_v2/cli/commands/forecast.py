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
import json
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


def resolve_project_path(project_path: str | None) -> tuple[Path, str]:
    """Resolve the project path from arg or last active.

    Returns: (path, project_name)
    """
    if project_path:
        path = Path(project_path).resolve()
        return path, path.name

    last_project = get_last_active_project()
    if not last_project:
        console.print("[red]No active project found.[/red]")
        console.print("Run [bold]1kh init[/bold] first, or specify --project")
        raise typer.Exit(1)

    return Path(last_project["path"]), last_project.get("name", "Unknown")


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

    path, project_name = resolve_project_path(project_path)

    # Determine mode
    if mock:
        mode = "mock"
    elif replay:
        mode = "replay"
    else:
        mode = "live"

    if runs > 0:
        _run_scenario_mode(path, project_name, runs, cycles, human_quality, market, chaos, replay, quiet)
    else:
        _run_single_forecast(path, project_name, mode, cycles, human_quality, market, chaos, replay, force, quiet)


def _run_single_forecast(
    path: Path,
    project_name: str,
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
    from core.forecast import ForecastRunner, ForecastVariables, TraceManager, FoundationContext

    variables = ForecastVariables(
        human_quality=human_quality,
        market_response=market,
        chaos_level=chaos,
    )

    # Load foundation context for grounded simulation
    foundation = FoundationContext.load(path)

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
        # Show project context
        system_info = f"{foundation.system_type}" if foundation.system_type else "Unknown"
        if foundation.north_star_type:
            system_info += f" ({foundation.north_star_type})"

        console.print()
        console.print(Panel(
            f"[bold]Forecast: {project_name}[/bold]\n"
            f"[dim]{path}[/dim]\n\n"
            f"System: {system_info}\n"
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
        foundation=foundation,
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
    project_name: str,
    num_runs: int,
    cycles: int,
    human_quality: str,
    market: str,
    chaos: str,
    replay_trace: str | None,
    quiet: bool,
):
    """Run Monte Carlo simulations."""
    from core.forecast import ScenarioRunner, ForecastVariables, FoundationContext

    variables = ForecastVariables(
        human_quality=human_quality,
        market_response=market,
        chaos_level=chaos,
    )

    # Load foundation context
    foundation = FoundationContext.load(path)

    if not quiet:
        system_info = f"{foundation.system_type}" if foundation.system_type else "Unknown"
        if foundation.north_star_type:
            system_info += f" ({foundation.north_star_type})"

        console.print()
        console.print(Panel(
            f"[bold]Monte Carlo Forecast: {project_name}[/bold]\n"
            f"[dim]{path}[/dim]\n\n"
            f"System: {system_info}\n"
            f"Runs: {num_runs}\n"
            f"Max Cycles per Run: {cycles}\n\n"
            f"[dim]Randomizing human quality, market response, and chaos[/dim]",
            border_style="magenta",
        ))
        console.print()

    runner = ScenarioRunner(
        project_path=path,
        variables=variables,
        foundation=foundation,
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
    # Determine display format based on system type
    is_user_system = getattr(outcome, 'system_type', 'BUSINESS') == "USER SYSTEM"
    metric_label = getattr(outcome, 'primary_metric_label', 'Revenue')
    metric_unit = getattr(outcome, 'primary_metric_unit', '$')

    if quiet:
        status = "REACHED" if outcome.target_reached else "NOT REACHED"
        if is_user_system:
            console.print(f"{status} | {outcome.cycles_completed} cycles | {outcome.final_revenue:.0f}/{outcome.target_revenue:.0f} features | {trace_id}")
        else:
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

    # Format metrics based on system type
    if is_user_system:
        metrics_section = (
            f"[bold]Progress:[/bold]\n"
            f"  {metric_label}: [bold]{outcome.final_revenue:.0f}[/bold] / {outcome.target_revenue:.0f}\n"
            f"  Tasks Completed: {outcome.total_tasks}\n"
            f"  API Cost: ~${outcome.estimated_api_cost:.2f}\n"
        )
    else:
        metrics_section = (
            f"[bold]Financial:[/bold]\n"
            f"  Final Revenue: [bold]${outcome.final_revenue:,.0f}[/bold]\n"
            f"  Target: ${outcome.target_revenue:,.0f}\n"
            f"  API Cost: ~${outcome.estimated_api_cost:.2f}\n"
        )

    console.print()
    console.print(Panel(
        f"{status_text}\n\n"
        f"[bold]Timeline:[/bold]\n"
        f"  Cycles: {outcome.cycles_completed}\n"
        f"  Estimated Time: {outcome.time_estimate}\n\n"
        f"{metrics_section}\n"
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

    path, project_name = resolve_project_path(project_path)
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

    path, _ = resolve_project_path(project_path)
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


@app.command("show")
def show_trace(
    trace_id: str = typer.Argument(..., help="Trace ID to display"),
    project_path: str = typer.Option(None, "--project", "-p"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all events"),
    cycle: int = typer.Option(None, "--cycle", "-c", help="Show specific cycle only"),
    format: str = typer.Option("timeline", "--format", "-f", help="Output format: timeline or json"),
):
    """
    View details of a forecast trace.

    Shows what actually happened during a simulation:
    - What hypotheses were generated and approved/rejected
    - What tasks succeeded or failed (and why)
    - What human decisions were simulated
    - How variables affected the outcomes

    \b
    EXAMPLES:
      1kh forecast show trace_20260205_164500
      1kh forecast show trace_xxx --verbose        # Show all events
      1kh forecast show trace_xxx --cycle 3        # Show only cycle 3
    """
    import json as json_module
    from core.forecast import TraceManager, ForecastVariables

    path, project_name = resolve_project_path(project_path)
    trace_manager = TraceManager(path)

    # Get trace directory
    trace_dir = trace_manager.get_trace(trace_id)
    if not trace_dir:
        console.print(f"[red]Trace not found: {trace_id}[/red]")
        console.print()
        console.print("Available traces:")
        for t in trace_manager.list_traces()[:5]:
            console.print(f"  • {t['trace_id']}")
        raise typer.Exit(1)

    # Load manifest
    manifest = trace_manager.get_manifest(trace_id)
    if not manifest:
        console.print(f"[red]Could not load manifest for: {trace_id}[/red]")
        raise typer.Exit(1)

    # Load events
    events = _load_trace_events(trace_dir)

    # Load human decisions
    decisions = _load_human_decisions(trace_dir)

    # Load outcome
    outcome = _load_trace_outcome(trace_dir)

    if format == "json":
        output = {
            "manifest": manifest.to_dict(),
            "outcome": outcome,
            "events": events,
            "decisions": decisions,
        }
        console.print(json_module.dumps(output, indent=2, default=str))
        return

    # Display timeline view
    _display_trace_timeline(
        trace_id=trace_id,
        manifest=manifest,
        events=events,
        decisions=decisions,
        outcome=outcome,
        verbose=verbose,
        cycle_filter=cycle,
    )


def _load_trace_events(trace_dir: Path) -> list[dict]:
    """Load events from trace events.jsonl file."""
    events_file = trace_dir / "events.jsonl"
    events = []
    if events_file.exists():
        for line in events_file.read_text().strip().split("\n"):
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return events


def _load_human_decisions(trace_dir: Path) -> list[dict]:
    """Load human decisions from trace."""
    decisions_file = trace_dir / "human_decisions" / "decisions.json"
    if decisions_file.exists():
        try:
            return json.loads(decisions_file.read_text())
        except json.JSONDecodeError:
            pass
    return []


def _load_trace_outcome(trace_dir: Path) -> dict | None:
    """Load outcome from trace."""
    outcome_file = trace_dir / "outcome.json"
    if outcome_file.exists():
        try:
            return json.loads(outcome_file.read_text())
        except json.JSONDecodeError:
            pass
    return None


def _display_trace_timeline(
    trace_id: str,
    manifest,
    events: list[dict],
    decisions: list[dict],
    outcome: dict | None,
    verbose: bool,
    cycle_filter: int | None,
):
    """Display trace as a timeline."""
    from rich.tree import Tree

    # Header with variables explained
    variables = manifest.variables
    console.print()

    # Outcome status
    if outcome:
        if outcome.get("target_reached"):
            status = "[bold green]TARGET REACHED[/bold green]"
            border = "green"
        else:
            progress = outcome.get("progress_pct", 0)
            status = f"[bold yellow]{progress:.1f}% Progress[/bold yellow]"
            border = "yellow"
    else:
        status = "[dim]In Progress[/dim]"
        border = "dim"

    # Explain variables
    human_q = variables.get("human_quality", "good")
    market = variables.get("market_response", "realistic")
    chaos = variables.get("chaos_level", "none")

    human_rates = {"perfect": "100%", "good": "90%", "mediocre": "70%", "poor": "50%"}
    market_mult = {"optimistic": "1.3×", "realistic": "1.0×", "pessimistic": "0.7×"}
    chaos_rates = {"none": "0%", "low": "+10%", "medium": "+20%", "high": "+40%"}

    variables_explained = (
        f"[bold]Variables Applied:[/bold]\n"
        f"  human_quality=[cyan]{human_q}[/cyan] → {human_rates.get(human_q, '?')} approval rate\n"
        f"  market_response=[cyan]{market}[/cyan] → {market_mult.get(market, '?')} growth multiplier\n"
        f"  chaos_level=[cyan]{chaos}[/cyan] → {chaos_rates.get(chaos, '?')} extra task failures"
    )

    cycles_completed = outcome.get("cycles_completed", 0) if outcome else "?"
    console.print(Panel(
        f"[bold]Trace:[/bold] {trace_id}\n"
        f"[bold]Mode:[/bold] {manifest.mode} | [bold]Cycles:[/bold] {cycles_completed} | {status}\n\n"
        f"{variables_explained}",
        title="FORECAST TRACE",
        border_style=border,
    ))

    # Group events by cycle
    cycles_data = _group_events_by_cycle(events, decisions)

    if not cycles_data:
        console.print()
        console.print("[dim]No events recorded in this trace.[/dim]")
        return

    # Display each cycle
    console.print()

    for cycle_num in sorted(cycles_data.keys()):
        if cycle_filter is not None and cycle_num != cycle_filter:
            continue

        cycle_events = cycles_data[cycle_num]
        _display_cycle_events(cycle_num, cycle_events, verbose)

    # Summary
    if outcome and cycle_filter is None:
        console.print()
        _display_trace_summary(outcome, events, decisions)


def _group_events_by_cycle(events: list[dict], decisions: list[dict]) -> dict:
    """Group events by cycle number."""
    cycles = {}
    current_cycle = 0

    for event in events:
        event_type = event.get("event_type", "")

        # Track cycle transitions
        if event_type == "cycle_started":
            current_cycle += 1

        if current_cycle not in cycles:
            cycles[current_cycle] = {
                "events": [],
                "decisions": [],
                "hypotheses_created": [],
                "hypotheses_accepted": [],
                "hypotheses_rejected": [],
                "tasks_created": [],
                "tasks_completed": [],
                "tasks_failed": [],
            }

        cycles[current_cycle]["events"].append(event)

        # Categorize events
        if event_type == "hypothesis_created":
            cycles[current_cycle]["hypotheses_created"].append(event)
        elif event_type == "hypothesis_accepted":
            cycles[current_cycle]["hypotheses_accepted"].append(event)
        elif event_type == "hypothesis_rejected":
            cycles[current_cycle]["hypotheses_rejected"].append(event)
        elif event_type == "task_created":
            cycles[current_cycle]["tasks_created"].append(event)
        elif event_type == "task_completed":
            cycles[current_cycle]["tasks_completed"].append(event)
        elif event_type == "task_failed":
            cycles[current_cycle]["tasks_failed"].append(event)

    # Add decisions to cycles (approximate by decision number)
    decisions_per_cycle = max(1, len(decisions) // max(1, len(cycles)))
    for i, decision in enumerate(decisions):
        cycle_num = min(i // decisions_per_cycle + 1, max(cycles.keys()) if cycles else 1)
        if cycle_num in cycles:
            cycles[cycle_num]["decisions"].append(decision)

    return cycles


def _display_cycle_events(cycle_num: int, cycle_data: dict, verbose: bool):
    """Display events for a single cycle."""
    console.print(f"[bold cyan]━━━ Cycle {cycle_num} ━━━[/bold cyan]")

    # IMAGINATION phase
    hyp_created = cycle_data["hypotheses_created"]
    if hyp_created:
        console.print(f"  [dim]IMAGINATION[/dim] Generated {len(hyp_created)} hypotheses")
        if verbose:
            for h in hyp_created:
                meta = h.get("metadata", {})
                # Try multiple key formats for compatibility
                hyp_id = meta.get("id") or h.get("hypothesis_id") or "?"
                desc = meta.get("desc") or meta.get("description") or ""
                desc = desc[:60] if desc else ""
                console.print(f"    • {hyp_id}: {desc}")

    # INTENT phase - build lookup of hypothesis descriptions from created events
    hyp_desc_lookup = {}
    for h in hyp_created:
        meta = h.get("metadata", {})
        hyp_id = meta.get("id") or h.get("hypothesis_id")
        desc = meta.get("desc") or meta.get("description") or ""
        if hyp_id:
            hyp_desc_lookup[hyp_id] = desc

    hyp_accepted = cycle_data["hypotheses_accepted"]
    hyp_rejected = cycle_data["hypotheses_rejected"]
    if hyp_accepted or hyp_rejected:
        for h in hyp_accepted:
            meta = h.get("metadata", {})
            hyp_id = meta.get("id") or h.get("hypothesis_id") or "?"
            score = meta.get("score") or meta.get("combined_score") or ""
            # Look up description from created hypotheses
            desc = meta.get("desc") or meta.get("description") or hyp_desc_lookup.get(hyp_id, "")
            desc = desc[:50] if desc else ""
            score_str = f" (score: {score:.2f})" if isinstance(score, (int, float)) else ""
            console.print(f"  [green]✓ APPROVED[/green] {hyp_id}: \"{desc}\"{score_str}")

        for h in hyp_rejected:
            meta = h.get("metadata", {})
            hyp_id = meta.get("id") or h.get("hypothesis_id") or "?"
            score = meta.get("score") or meta.get("combined_score") or ""
            reason = meta.get("reason", "below threshold")[:40]
            desc = meta.get("desc") or meta.get("description") or hyp_desc_lookup.get(hyp_id, "")
            desc = desc[:40] if desc else ""
            score_str = f" (score: {score:.2f})" if isinstance(score, (int, float)) else ""
            if desc:
                console.print(f"  [red]✗ REJECTED[/red] {hyp_id}: \"{desc}\" - {reason}{score_str}")
            else:
                console.print(f"  [red]✗ REJECTED[/red] {hyp_id}: {reason}{score_str}")

    # WORK phase
    tasks_created = cycle_data["tasks_created"]
    if tasks_created:
        console.print(f"  [dim]WORK[/dim] Created {len(tasks_created)} tasks")
        if verbose:
            for t in tasks_created:
                task_id = t.get("task_id") or t.get("metadata", {}).get("id") or "?"
                meta = t.get("metadata", {})
                desc = meta.get("desc") or meta.get("description") or meta.get("title") or ""
                hyp_id = t.get("hypothesis_id") or ""
                if desc:
                    console.print(f"    • {task_id}: {desc[:50]}")
                elif hyp_id:
                    console.print(f"    • {task_id} (for {hyp_id})")
                else:
                    console.print(f"    • {task_id}")

    # EXECUTION phase - aggregate revenue events
    all_events = cycle_data["events"]
    revenue_by_task = {}
    for e in all_events:
        if e.get("event_type") == "revenue":
            task_id = e.get("task_id", "")
            revenue_by_task[task_id] = revenue_by_task.get(task_id, 0) + e.get("value", 0)

    tasks_completed = cycle_data["tasks_completed"]
    tasks_failed = cycle_data["tasks_failed"]

    # Deduplicate completed tasks (show each task_id only once)
    seen_completed = set()
    for t in tasks_completed:
        task_id = t.get("task_id") or "?"
        if task_id in seen_completed:
            continue
        seen_completed.add(task_id)

        revenue = revenue_by_task.get(task_id, 0)
        hyp_id = t.get("hypothesis_id") or ""
        hyp_info = f" [dim]({hyp_id})[/dim]" if hyp_id and verbose else ""

        if revenue > 0:
            console.print(f"  [green]✓ COMPLETED[/green] {task_id}{hyp_info} [green]+${revenue:.0f}[/green]")
        else:
            console.print(f"  [green]✓ COMPLETED[/green] {task_id}{hyp_info}")

    # Deduplicate failed tasks
    seen_failed = set()
    for t in tasks_failed:
        task_id = t.get("task_id") or "?"
        if task_id in seen_failed:
            continue
        seen_failed.add(task_id)

        meta = t.get("metadata", {})
        error = meta.get("error") or "unknown error"
        console.print(f"  [red]✗ FAILED[/red] {task_id}: {error}")

    # Human decisions
    decisions = cycle_data["decisions"]
    for d in decisions:
        esc_type = d.get("escalation_type", "decision")
        summary = d.get("summary", "")[:50]
        result = d.get("result", {})
        action = result.get("action", result.get("approved", "?"))

        if action in (True, "approve", "approved"):
            console.print(f"  [blue]👤 HUMAN[/blue] {esc_type}: \"{summary}\" → [green]Approved[/green]")
        elif action in (False, "reject", "rejected"):
            console.print(f"  [blue]👤 HUMAN[/blue] {esc_type}: \"{summary}\" → [red]Rejected[/red]")
        else:
            console.print(f"  [blue]👤 HUMAN[/blue] {esc_type}: \"{summary}\" → {action}")

    console.print()


def _display_trace_summary(outcome: dict, events: list[dict], decisions: list[dict]):
    """Display summary statistics for the trace."""
    # Count events by type
    event_counts = {}
    for e in events:
        et = e.get("event_type", "unknown")
        event_counts[et] = event_counts.get(et, 0) + 1

    tasks_completed = event_counts.get("task_completed", 0)
    tasks_failed = event_counts.get("task_failed", 0)
    total_tasks = tasks_completed + tasks_failed
    task_success_rate = tasks_completed / total_tasks if total_tasks > 0 else 0

    hyp_accepted = event_counts.get("hypothesis_accepted", 0)
    hyp_rejected = event_counts.get("hypothesis_rejected", 0)
    total_hyp = hyp_accepted + hyp_rejected
    hyp_accept_rate = hyp_accepted / total_hyp if total_hyp > 0 else 0

    # Decision summary
    approvals = sum(1 for d in decisions if d.get("result", {}).get("approved", False) or d.get("result", {}).get("action") in ("approve", "approved", True))
    rejections = len(decisions) - approvals

    console.print(Panel(
        f"[bold]Execution Summary:[/bold]\n"
        f"  Tasks: {tasks_completed} completed, {tasks_failed} failed ({task_success_rate:.0%} success)\n"
        f"  Hypotheses: {hyp_accepted} approved, {hyp_rejected} rejected ({hyp_accept_rate:.0%} acceptance)\n"
        f"  Human Decisions: {approvals} approved, {rejections} rejected\n\n"
        f"[bold]Final Metrics:[/bold]\n"
        f"  Cycles: {outcome.get('cycles_completed', 0)}\n"
        f"  Time Estimate: {outcome.get('time_estimate', '?')}\n"
        f"  Risk Level: {outcome.get('risk_level', '?').upper()}\n"
        f"  Success Rate: {outcome.get('success_rate', 0):.0%}",
        title="SUMMARY",
        border_style="cyan",
    ))


@app.command("sensitivity")
def sensitivity_analysis(
    variable: str = typer.Option(
        None, "--variable", "-v",
        help="Specific variable to analyze (default: all)",
    ),
    interaction: str = typer.Option(
        None, "--interaction", "-i",
        help="Two variables to test interaction (comma-separated, e.g. 'human_quality,market')",
    ),
    cycles: int = typer.Option(
        30, "--cycles", "-c",
        help="Max cycles per simulation",
    ),
    runs_per_value: int = typer.Option(
        5, "--runs", "-n",
        help="Monte Carlo runs per variable value",
    ),
    baseline: str = typer.Option(
        "good,realistic,none", "--baseline", "-b",
        help="Baseline values: human_quality,market,chaos (default: good,realistic,none)",
    ),
    format: str = typer.Option(
        "table", "--format", "-f",
        help="Output format: table or json",
    ),
    save: bool = typer.Option(
        False, "--save", "-s",
        help="Save results to .1kh/sensitivity/",
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q",
        help="Minimal output",
    ),
    project_path: str = typer.Option(
        None, "--project", "-p",
        help="Path to 1KH project",
    ),
):
    """
    Analyze which variables have the biggest impact on outcomes.

    Run sensitivity analysis to understand:
    - Which inputs matter most (chaos, human quality, market)
    - How robust your forecast is to changes
    - Where to focus optimization efforts

    \b
    EXAMPLES:
      1kh forecast sensitivity                    # Analyze all variables
      1kh forecast sensitivity -v chaos_level     # Analyze specific variable
      1kh forecast sensitivity -i human_quality,market  # Two-variable interaction
      1kh forecast sensitivity --cycles 10 --runs 3     # Quick test
    """
    from core.forecast import (
        SensitivityRunner,
        ForecastVariables,
        FoundationContext,
        SensitivityResult,
    )
    import json as json_module

    path, project_name = resolve_project_path(project_path)
    foundation = FoundationContext.load(path)

    # Parse baseline values
    baseline_parts = baseline.split(",")
    baseline_human = baseline_parts[0] if len(baseline_parts) > 0 else "good"
    baseline_market = baseline_parts[1] if len(baseline_parts) > 1 else "realistic"
    baseline_chaos = baseline_parts[2] if len(baseline_parts) > 2 else "none"

    baseline_vars = ForecastVariables(
        human_quality=baseline_human,
        market_response=baseline_market,
        chaos_level=baseline_chaos,
    )

    # Progress tracking
    progress_state = {"task": None, "progress": None}

    def on_progress(var_name: str, current: int, total: int):
        if progress_state["progress"] and progress_state["task"]:
            progress_state["progress"].update(
                progress_state["task"],
                completed=current,
                description=f"Analyzing {var_name}...",
            )

    runner = SensitivityRunner(
        project_path=path,
        baseline=baseline_vars,
        runs_per_value=runs_per_value,
        max_cycles=cycles,
        foundation=foundation,
        on_progress=on_progress if not quiet else None,
    )

    if interaction:
        # Two-variable interaction analysis
        parts = interaction.replace(" ", "").split(",")
        if len(parts) != 2:
            console.print("[red]--interaction requires exactly two comma-separated variable names[/red]")
            console.print("Example: --interaction human_quality,market_response")
            raise typer.Exit(1)

        var1, var2 = parts[0].strip(), parts[1].strip()

        if not quiet:
            console.print()
            console.print(Panel(
                f"[bold]Project: {project_name}[/bold]\n"
                f"Interaction Analysis: {var1} × {var2}\n"
                f"Runs per combination: {runs_per_value} | Cycles: {cycles}",
                title="SENSITIVITY ANALYSIS",
                border_style="cyan",
            ))

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
                console=console,
                disable=quiet,
            ) as progress:
                # Estimate total combinations
                from core.forecast import SensitivityRunner as SR
                total = len(SR.VARIABLE_DEFINITIONS.get(var1, [])) * len(SR.VARIABLE_DEFINITIONS.get(var2, []))
                progress_state["progress"] = progress
                progress_state["task"] = progress.add_task(f"Analyzing {var1} × {var2}...", total=total)

                result = asyncio.run(runner.analyze_interaction(var1, var2))

            if format == "json":
                console.print(json_module.dumps(result.to_dict(), indent=2))
            else:
                _display_interaction_result(result, quiet)

            if save:
                _save_sensitivity_results(path, {"interaction": result.to_dict()}, "interaction")

        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    elif variable:
        # Single variable analysis
        if not quiet:
            console.print()
            console.print(Panel(
                f"[bold]Project: {project_name}[/bold]\n"
                f"Variable: {variable}\n"
                f"Runs per value: {runs_per_value} | Cycles: {cycles}",
                title="SENSITIVITY ANALYSIS",
                border_style="cyan",
            ))

        try:
            from core.forecast import SensitivityRunner as SR
            values = SR.VARIABLE_DEFINITIONS.get(variable, [])

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
                console=console,
                disable=quiet,
            ) as progress:
                progress_state["progress"] = progress
                progress_state["task"] = progress.add_task(f"Analyzing {variable}...", total=len(values))

                result = asyncio.run(runner.analyze_variable(variable))

            if format == "json":
                console.print(json_module.dumps(result.to_dict(), indent=2))
            else:
                _display_single_sensitivity(result, quiet)

            if save:
                _save_sensitivity_results(path, {variable: result.to_dict()}, "single")

        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    else:
        # Full analysis (all variables)
        if not quiet:
            system_type = foundation.system_type or "Unknown"
            console.print()
            console.print(Panel(
                f"[bold]Project: {project_name}[/bold] ({system_type})\n"
                f"Baseline: human_quality={baseline_human}, market={baseline_market}, chaos={baseline_chaos}\n"
                f"Runs per value: {runs_per_value} | Cycles: {cycles}",
                title="SENSITIVITY ANALYSIS",
                border_style="cyan",
            ))

        from core.forecast import SensitivityRunner as SR
        all_vars = list(SR.VARIABLE_DEFINITIONS.keys())
        total_values = sum(len(SR.VARIABLE_DEFINITIONS[v]) for v in all_vars)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
            disable=quiet,
        ) as progress:
            progress_state["progress"] = progress
            progress_state["task"] = progress.add_task("Analyzing all variables...", total=total_values)

            results = asyncio.run(runner.analyze_all())

        if format == "json":
            output = {name: r.to_dict() for name, r in results.items()}
            console.print(json_module.dumps(output, indent=2))
        else:
            _display_sensitivity_results(results, project_name, foundation, baseline_vars, runs_per_value, cycles, quiet)

        if save:
            output = {name: r.to_dict() for name, r in results.items()}
            trace_id = _save_sensitivity_results(path, output, "full")
            if not quiet:
                console.print(f"\n[dim]Results saved: {trace_id}[/dim]")


def _display_sensitivity_results(
    results: dict,
    project_name: str,
    foundation,
    baseline: "ForecastVariables",
    runs_per_value: int,
    max_cycles: int,
    quiet: bool,
):
    """Display ranked sensitivity analysis."""
    from core.forecast import SensitivityResult

    if quiet:
        # Just show ranking
        ranked = sorted(results.values(), key=lambda r: r.sensitivity_score(), reverse=True)
        for r in ranked:
            console.print(f"{r.variable_name}: Δ{r.success_rate_delta:.0%}")
        return

    console.print()

    # Create ranked table
    table = Table(title="Impact on Success Rate")
    table.add_column("Variable", style="bold")
    table.add_column("Impact (Δ)")
    table.add_column("Range")
    table.add_column("Sensitivity", justify="right")

    ranked = sorted(results.values(), key=lambda r: r.sensitivity_score(), reverse=True)
    max_delta = ranked[0].success_rate_delta if ranked else 1.0

    for r in ranked:
        # Visual bar based on relative sensitivity
        bar_length = int(8 * r.success_rate_delta / max_delta) if max_delta > 0 else 0
        bar = "█" * bar_length

        # Format range showing best to worst
        min_sr, max_sr = r.success_rate_range
        # Find values corresponding to min/max
        best_idx = max(range(len(r.outcomes)), key=lambda i: r.outcomes[i].get("success_rate", 0))
        worst_idx = min(range(len(r.outcomes)), key=lambda i: r.outcomes[i].get("success_rate", 0))
        best_val = r.variable_values[best_idx]
        worst_val = r.variable_values[worst_idx]

        range_str = f"{best_val}:{max_sr:.0%} → {worst_val}:{min_sr:.0%}"

        table.add_row(
            r.variable_name,
            f"Δ {r.success_rate_delta:.0%}",
            range_str,
            f"[cyan]{bar}[/cyan]",
        )

    console.print(table)

    # Key insights
    console.print()
    console.print("[bold]Key Insights:[/bold]")
    if ranked:
        top = ranked[0]
        console.print(f"  → [green]{top.variable_name}[/green] has HIGHEST impact - focus here")
        if len(ranked) > 1:
            second = ranked[1]
            console.print(f"  → [yellow]{second.variable_name}[/yellow] also matters significantly")
        if len(ranked) > 2:
            low = ranked[-1]
            console.print(f"  → [dim]{low.variable_name}[/dim] has LOW impact - less critical")


def _display_single_sensitivity(result, quiet: bool):
    """Display results for a single variable analysis."""
    if quiet:
        console.print(f"{result.variable_name}: Δ{result.success_rate_delta:.0%}")
        return

    console.print()
    console.print(f"[bold]Variable:[/bold] {result.variable_name}")
    console.print(f"[bold]Baseline:[/bold] {result.baseline_value}")
    console.print()

    table = Table()
    table.add_column("Value", style="bold")
    table.add_column("Success Rate")
    table.add_column("Avg Cycles")
    table.add_column("Runs")

    for i, val in enumerate(result.variable_values):
        outcome = result.outcomes[i]
        sr = outcome.get("success_rate", 0.0)
        cycles = outcome.get("cycles_avg", 0)
        runs = outcome.get("num_runs", 0)

        # Highlight baseline value
        val_str = str(val)
        if val == result.baseline_value:
            val_str = f"[bold cyan]{val}[/bold cyan] (baseline)"

        # Color success rate
        if sr >= 0.8:
            sr_str = f"[green]{sr:.0%}[/green]"
        elif sr >= 0.5:
            sr_str = f"[yellow]{sr:.0%}[/yellow]"
        else:
            sr_str = f"[red]{sr:.0%}[/red]"

        table.add_row(val_str, sr_str, f"{cycles:.0f}", str(runs))

    console.print(table)

    console.print()
    min_sr, max_sr = result.success_rate_range
    console.print(f"[bold]Impact:[/bold] Δ {result.success_rate_delta:.0%} (range: {min_sr:.0%} - {max_sr:.0%})")


def _display_interaction_result(result, quiet: bool):
    """Display two-variable interaction heatmap."""
    if quiet:
        strength = "STRONG" if result.has_interaction else "WEAK"
        console.print(f"{result.var1_name} × {result.var2_name}: {strength} interaction ({result.interaction_strength:.2f})")
        return

    console.print()
    console.print(f"[bold]Interaction:[/bold] {result.var1_name} × {result.var2_name}")
    console.print()

    # Build header
    table = Table(title="Success Rate Matrix")
    table.add_column(result.var2_name, style="bold")

    for v1 in result.var1_values:
        table.add_column(str(v1), justify="center")

    # Add rows
    for r, v2 in enumerate(result.var2_values):
        row_data = [str(v2)]
        for c in range(len(result.var1_values)):
            sr = result.outcomes_grid[r][c].get("success_rate", 0.0)
            # Color code
            if sr >= 0.8:
                cell = f"[green]{sr:.0%}[/green]"
            elif sr >= 0.5:
                cell = f"[yellow]{sr:.0%}[/yellow]"
            else:
                cell = f"[red]{sr:.0%}[/red]"
            row_data.append(cell)
        table.add_row(*row_data)

    console.print(table)

    # Interaction analysis
    console.print()
    strength = "STRONG" if result.has_interaction else "WEAK"
    color = "red" if result.has_interaction else "green"
    console.print(f"[bold]Interaction Detected:[/bold] [{color}]{strength}[/{color}] ({result.interaction_strength:.2f})")

    if result.has_interaction:
        console.print("  → Variables have synergistic/antagonistic effects")
        console.print("  → Optimize them together, not independently")
    else:
        console.print("  → Effects are mostly additive (no strong synergy/conflict)")
        console.print("  → Optimize variables independently")


def _save_sensitivity_results(path: Path, results: dict, analysis_type: str) -> str:
    """Save sensitivity results to .1kh/sensitivity/ directory."""
    import json as json_module

    sensitivity_dir = path / ".1kh" / "sensitivity"
    sensitivity_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    trace_id = f"sensitivity_{timestamp}"
    analysis_dir = sensitivity_dir / trace_id
    analysis_dir.mkdir(exist_ok=True)

    # Save manifest
    manifest = {
        "trace_id": trace_id,
        "created_at": datetime.now().isoformat(),
        "analysis_type": analysis_type,
    }
    (analysis_dir / "manifest.json").write_text(json_module.dumps(manifest, indent=2))

    # Save results
    (analysis_dir / "results.json").write_text(json_module.dumps(results, indent=2))

    return trace_id


@app.command("explore")
def explore_ideas(
    user_ideas: int = typer.Option(
        10, "--user", "-u",
        help="Number of USER SYSTEM ideas to explore",
    ),
    biz_ideas: int = typer.Option(
        5, "--biz", "-b",
        help="Number of BUSINESS SYSTEM ideas to explore",
    ),
    runs_per_idea: int = typer.Option(
        3, "--runs", "-n",
        help="Forecast runs per idea",
    ),
    cycles: int = typer.Option(
        15, "--cycles", "-c",
        help="Max cycles per forecast",
    ),
    top: int = typer.Option(
        10, "--top", "-t",
        help="Show top N results",
    ),
    format: str = typer.Option(
        "table", "--format", "-f",
        help="Output format: table or json",
    ),
    save: bool = typer.Option(
        False, "--save", "-s",
        help="Save results to .1kh/explore/",
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q",
        help="Minimal output",
    ),
):
    """
    Explore multiple business/service ideas through simulation.

    Generate and forecast diverse ideas to find the best candidates.
    Useful for comparing different approaches before committing.

    \b
    EXAMPLES:
      1kh forecast explore                        # Default: 10 USER + 5 BIZ
      1kh forecast explore --user 20 --biz 10     # More ideas
      1kh forecast explore --user 50 --biz 0      # Only USER systems
      1kh forecast explore --runs 5 --cycles 20   # More thorough
    """
    from core.forecast import IdeaExplorer, ForecastVariables
    import json as json_module

    total_ideas = user_ideas + biz_ideas

    if not quiet:
        console.print()
        console.print(Panel(
            f"[bold]Exploring {total_ideas} Ideas[/bold]\n"
            f"USER SYSTEM ideas: {user_ideas}\n"
            f"BUSINESS SYSTEM ideas: {biz_ideas}\n"
            f"Runs per idea: {runs_per_idea} | Cycles: {cycles}",
            title="IDEA EXPLORATION",
            border_style="magenta",
        ))

    variables = ForecastVariables()

    # Progress tracking
    progress_state = {"task": None, "progress": None}

    def on_progress(idea_name: str, current: int, total: int):
        if progress_state["progress"] and progress_state["task"]:
            progress_state["progress"].update(
                progress_state["task"],
                completed=current,
                description=f"Forecasting: {idea_name}...",
            )

    explorer = IdeaExplorer(
        num_user_ideas=user_ideas,
        num_biz_ideas=biz_ideas,
        runs_per_idea=runs_per_idea,
        max_cycles=cycles,
        variables=variables,
        on_progress=on_progress if not quiet else None,
    )

    # Generate and explore ideas
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
        disable=quiet,
    ) as progress:
        progress_state["progress"] = progress
        progress_state["task"] = progress.add_task("Exploring ideas...", total=total_ideas)

        results = asyncio.run(explorer.explore())

    if format == "json":
        output = [r.to_dict() for r in results]
        console.print(json_module.dumps(output, indent=2))
        return

    # Display results table
    _display_explore_results(results, top, quiet)

    if save:
        trace_id = _save_explore_results(results)
        if not quiet:
            console.print(f"\n[dim]Results saved: {trace_id}[/dim]")


def _display_explore_results(results: list, top: int, quiet: bool):
    """Display exploration results as ranked table."""
    if quiet:
        for i, r in enumerate(results[:top]):
            console.print(f"{i+1}. {r.idea_name} ({r.system_type[:4]}): {r.success_rate:.0%}")
        return

    console.print()

    # Create table
    table = Table(title=f"Top {min(top, len(results))} Ideas by Success Rate")
    table.add_column("#", style="dim", width=3)
    table.add_column("Idea", style="bold")
    table.add_column("Type", width=6)
    table.add_column("Success", justify="right")
    table.add_column("Time", justify="right")
    table.add_column("Risk", justify="center")
    table.add_column("Description")

    for i, r in enumerate(results[:top]):
        # Color code success rate
        if r.success_rate >= 0.8:
            sr_str = f"[green]{r.success_rate:.0%}[/green]"
        elif r.success_rate >= 0.5:
            sr_str = f"[yellow]{r.success_rate:.0%}[/yellow]"
        else:
            sr_str = f"[red]{r.success_rate:.0%}[/red]"

        # Color code risk
        risk_colors = {"low": "green", "medium": "yellow", "high": "red"}
        risk_str = f"[{risk_colors.get(r.risk_level, 'white')}]{r.risk_level.upper()}[/{risk_colors.get(r.risk_level, 'white')}]"

        # System type abbreviation
        sys_type = "USER" if "USER" in r.system_type else "BIZ"

        table.add_row(
            str(i + 1),
            r.idea_name,
            sys_type,
            sr_str,
            r.time_estimate,
            risk_str,
            r.description[:40] + "..." if len(r.description) > 40 else r.description,
        )

    console.print(table)

    # Summary by system type
    user_results = [r for r in results if "USER" in r.system_type]
    biz_results = [r for r in results if "BIZ" in r.system_type or "BUSINESS" in r.system_type]

    console.print()
    console.print("[bold]Summary by System Type:[/bold]")

    if user_results:
        avg_sr = sum(r.success_rate for r in user_results) / len(user_results)
        best = max(user_results, key=lambda r: r.success_rate)
        console.print(f"  USER SYSTEM: avg {avg_sr:.0%} success, best = {best.idea_name} ({best.success_rate:.0%})")

    if biz_results:
        avg_sr = sum(r.success_rate for r in biz_results) / len(biz_results)
        best = max(biz_results, key=lambda r: r.success_rate)
        console.print(f"  BUSINESS: avg {avg_sr:.0%} success, best = {best.idea_name} ({best.success_rate:.0%})")


def _save_explore_results(results: list) -> str:
    """Save exploration results."""
    import json as json_module

    # Save to current directory's .1kh
    explore_dir = Path(".1kh") / "explore"
    explore_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    trace_id = f"explore_{timestamp}"

    output = {
        "trace_id": trace_id,
        "created_at": datetime.now().isoformat(),
        "results": [r.to_dict() for r in results],
    }

    (explore_dir / f"{trace_id}.json").write_text(json_module.dumps(output, indent=2))
    return trace_id
