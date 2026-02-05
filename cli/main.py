"""
ThousandHand CLI - Autonomous business-building system.

QUICK START:
    1kh init                    Set up your foundation (values, goals)
    1kh run cycle --demo        Run a demo cycle (no API costs)
    1kh run cycle --local       Run with real Claude API
    1kh reflect                 Check trajectory and get recommendations

CORE COMMANDS:
    init        Start the Initial Ceremony (create foundation docs)
    run         Execute loops (imagination, intent, cycle)
    reflect     Analyze trajectory and suggest course corrections
    status      Check system health and progress

See 'CLI_GUIDE.md' for full documentation.
"""

import typer
from rich.console import Console

from cli.commands import init, status, escalations, logs, config, worker, run, resources, reflect, operate

# ASCII art for help - using 1KH which fits better
BANNER = """
[bold cyan]╔════════════════════════════════════════════════════════════╗
║                                                            ║
║      ██╗██╗  ██╗██╗  ██╗                                  ║
║     ███║██║ ██╔╝██║  ██║                                  ║
║     ╚██║█████╔╝ ███████║                                  ║
║      ██║██╔═██╗ ██╔══██║                                  ║
║      ██║██║  ██╗██║  ██║                                  ║
║      ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝                                  ║
║                                                            ║
║          [bold white]ThousandHand[/bold white]                                  ║
║          [dim]Autonomous Business Builder[/dim]                      ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝[/bold cyan]
"""

app = typer.Typer(
    name="1kh",
    help="""
ThousandHand (1KH) - Autonomous business-building system.

Give me your values and objectives. I will imagine paths forward,
estimate what's feasible, build what's needed, measure what happens,
and learn from the results.

[bold]QUICK START:[/bold]
  1kh init                  Set up foundation (values, goals)
  1kh run cycle --demo      Run demo cycle (no API)
  1kh run cycle --local     Run with real Claude
  1kh reflect               Check trajectory

[bold]See CLI_GUIDE.md for full documentation.[/bold]
    """,
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()

# =============================================================================
# Core Commands (most used)
# =============================================================================
app.add_typer(
    init.app,
    name="init",
    help="[bold]Start the Initial Ceremony[/bold] - Create foundation docs (oracle, north_star, context)"
)

app.add_typer(
    run.app,
    name="run",
    help="[bold]Run loops[/bold] - Execute imagination, intent, or full cycles"
)

app.add_typer(
    reflect.app,
    name="reflect",
    help="[bold]Trajectory analysis[/bold] - Check progress and get recommendations (AUGMENT/OPTIMIZE/PIVOT)"
)

app.add_typer(
    status.app,
    name="status",
    help="[bold]System health[/bold] - Check tree health, metrics, and active branches"
)

app.add_typer(
    operate.app,
    name="operate",
    help="[bold]OPERATE phase[/bold] - Transition to production with SLA monitoring"
)

# =============================================================================
# Supporting Commands
# =============================================================================
app.add_typer(
    escalations.app,
    name="escalations",
    help="Handle pending human decisions"
)

app.add_typer(
    logs.app,
    name="logs",
    help="View system logs (decisions, execution, etc.)"
)

app.add_typer(
    config.app,
    name="config",
    help="View or modify configuration"
)

app.add_typer(
    worker.app,
    name="worker",
    help="Manage Temporal worker (for production mode)"
)

app.add_typer(
    resources.app,
    name="resources",
    help="View resource locks and conflicts"
)


@app.callback()
def main_callback():
    """
    ThousandHand (1KH) - Autonomous business-building system.
    """
    pass


@app.command("guide")
def show_guide():
    """Show the full CLI guide."""
    from pathlib import Path
    from rich.markdown import Markdown

    guide_path = Path(__file__).parent.parent / "CLI_GUIDE.md"
    if guide_path.exists():
        md = Markdown(guide_path.read_text())
        console.print(md)
    else:
        console.print("[yellow]CLI_GUIDE.md not found. See the project root.[/yellow]")


@app.command("quickstart")
def quickstart():
    """Show quick start instructions."""
    console.print()
    console.print(BANNER)
    console.print()
    console.print("""
[bold]Quick Start Guide[/bold]

[cyan]Step 1:[/cyan] Initialize your project
    [bold]1kh init[/bold]

    This creates your foundation documents:
    • oracle.md     - Your values and rules
    • north_star.md - Your goals ($1M ARR, etc.)
    • context.md    - Resources and constraints

[cyan]Step 2:[/cyan] Run a demo cycle (no API costs)
    [bold]1kh run cycle --demo --max 3 --verbose[/bold]

    Watch the system:
    • Generate hypotheses (IMAGINATION)
    • Evaluate and approve (INTENT)
    • Create tasks (WORK)
    • Execute and measure (EXECUTION)

[cyan]Step 3:[/cyan] Run with real Claude
    [bold]export ANTHROPIC_API_KEY=sk-ant-...[/bold]
    [bold]1kh run cycle --local --fresh[/bold]

[cyan]Step 4:[/cyan] Check progress
    [bold]1kh reflect[/bold]
    [bold]1kh status[/bold]

[cyan]Step 5:[/cyan] Transition to OPERATE phase (after features built)
    [bold]1kh operate[/bold]

    Generates operations.md with SLA targets:
    • Uptime, latency, error rate thresholds
    • REFLECTION monitors operational health
    • Escalations when SLAs breached

[dim]For full documentation: 1kh guide[/dim]
""")


if __name__ == "__main__":
    app()
