"""
Run command - Trigger workflows manually.

Usage:
    1kh run imagination     Run the IMAGINATION loop (generate hypotheses)
    1kh run intent          Run the INTENT loop (make decisions)
    1kh run cycle           Run full IMAGINATION → INTENT cycle
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
from rich.markdown import Markdown
from rich.status import Status
from rich.prompt import Prompt, Confirm

from core.config import get_last_active_project, set_last_active_project

app = typer.Typer(no_args_is_help=True)
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


@app.command("imagination")
def run_imagination(
    project_path: str = typer.Option(
        None,
        "--project", "-p",
        help="Path to 1KH project",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-n",
        help="Show what would happen without calling Claude",
    ),
    auto: bool = typer.Option(
        False,
        "--auto", "-y",
        help="Skip user confirmation prompts",
    ),
    local: bool = typer.Option(
        True,
        "--local/--cloud",
        help="Run locally (no Temporal) or via Temporal Cloud",
    ),
):
    """
    Run the IMAGINATION loop.

    Reads your foundation documents and generates hypotheses for
    achieving your North Star objectives.
    """
    path = resolve_project_path(project_path)

    console.print()
    console.print(Panel(
        f"[bold]IMAGINATION Loop[/bold]\n\n"
        f"Project: {path.name}\n"
        f"Mode: {'Dry run' if dry_run else 'Local' if local else 'Temporal Cloud'}\n"
        f"User prompts: {'Disabled (--auto)' if auto else 'Enabled'}",
        border_style="cyan",
    ))
    console.print()

    if local:
        asyncio.run(_run_imagination_local(path, dry_run, auto))
    else:
        asyncio.run(_run_imagination_temporal(path, auto))


async def _run_imagination_local(path: Path, dry_run: bool, auto: bool):
    """Run imagination loop locally (without Temporal orchestration)."""
    from temporal.activities.foundation import (
        read_oracle,
        read_north_star,
        read_context,
        read_seeds,
    )
    from temporal.activities.imagination import (
        generate_hypotheses,
        evaluate_hypothesis,
    )

    project_path = str(path)

    # Step 1: Load foundation
    console.print("[bold cyan]Step 1: Loading Foundation[/bold cyan]")

    with Status("[dim]Reading oracle.md...[/dim]", console=console):
        oracle = await read_oracle(project_path)
    console.print(f"  [green]✓[/green] Oracle: {len(oracle.get('values', []))} values, {len(oracle.get('never_do', []))} boundaries")

    with Status("[dim]Reading north-star.md...[/dim]", console=console):
        north_star = await read_north_star(project_path)
    console.print(f"  [green]✓[/green] North Star: {len(north_star.get('objectives', []))} objectives, {len(north_star.get('success_metrics', []))} metrics")

    with Status("[dim]Reading context.md...[/dim]", console=console):
        context = await read_context(project_path)
    console.print(f"  [green]✓[/green] Context: {len(context.get('constraints', []))} constraints")

    with Status("[dim]Reading seeds.json...[/dim]", console=console):
        seeds = await read_seeds(project_path)
    console.print(f"  [green]✓[/green] Seeds: {len(seeds)} initial ideas")

    console.print()

    # Show objectives we're mapping to
    console.print("[bold cyan]North Star Objectives:[/bold cyan]")
    for i, obj in enumerate(north_star.get('objectives', []), 1):
        console.print(f"  {i}. {obj}")
    console.print()

    if dry_run:
        console.print("[yellow]Dry run mode - skipping Claude API calls[/yellow]")
        console.print()
        console.print("[dim]In a real run, Claude would:[/dim]")
        console.print("  1. Generate hypotheses that map to each objective")
        console.print("  2. Identify dependencies between hypotheses")
        console.print("  3. Score each on feasibility AND goal alignment")
        console.print("  4. Present for your review and approval")
        return

    # Step 2: Generate hypotheses
    console.print("[bold cyan]Step 2: Generating Hypotheses[/bold cyan]")
    console.print("[dim]Claude is analyzing your foundation and generating comprehensive hypotheses...[/dim]")
    console.print()

    with Status("[bold blue]Generating hypotheses...", console=console):
        hypotheses = await generate_hypotheses(
            project_path=project_path,
            oracle=oracle,
            north_star=north_star,
            context=context,
            existing_hypotheses=[],
            max_new=20,  # Allow more comprehensive generation
        )

    if not hypotheses:
        console.print("[yellow]No hypotheses generated. Check your API key and foundation docs.[/yellow]")
        return

    # Extract analysis if present
    analysis = hypotheses[0].get("_analysis", {}) if hypotheses else {}

    console.print(f"[green]✓[/green] Generated {len(hypotheses)} hypotheses")
    console.print()

    # Show coverage analysis
    if analysis.get("objective_coverage"):
        console.print("[bold cyan]Objective Coverage:[/bold cyan]")
        for obj_num, hyp_ids in analysis["objective_coverage"].items():
            console.print(f"  Objective {obj_num}: {len(hyp_ids)} hypothesis(es)")
        console.print()

    # Step 3: Show hypotheses for review
    console.print("[bold cyan]Step 3: Hypothesis Review[/bold cyan]")
    console.print()

    # Display each hypothesis in detail
    for i, hyp in enumerate(hypotheses):
        _display_hypothesis_detail(hyp, i + 1, len(hypotheses))

        if not auto and i < len(hypotheses) - 1:
            console.print()
            action = Prompt.ask(
                "[dim]Continue to next hypothesis?[/dim]",
                choices=["y", "n", "all", "skip"],
                default="y"
            )
            if action == "n":
                break
            elif action == "all":
                auto = True  # Show rest without prompting
            elif action == "skip":
                continue

        console.print()

    # Step 4: User confirmation
    console.print("[bold cyan]Step 4: Hypothesis Confirmation[/bold cyan]")
    console.print()

    if not auto:
        # Show summary
        _display_hypothesis_summary(hypotheses)
        console.print()

        # Ask for approval
        action = Prompt.ask(
            "What would you like to do?",
            choices=["accept", "evaluate", "reject", "edit"],
            default="evaluate"
        )

        if action == "reject":
            console.print("[yellow]Hypotheses rejected. Consider revising your foundation docs.[/yellow]")
            return
        elif action == "edit":
            console.print("[yellow]Manual editing not yet implemented.[/yellow]")
            console.print(f"[dim]Edit the output file directly: {path}/.1kh/hypotheses.json[/dim]")
            # Still save for manual editing
        elif action == "evaluate":
            # Deep evaluation
            console.print()
            console.print("[bold cyan]Step 5: Deep Evaluation[/bold cyan]")
            console.print("[dim]Evaluating each hypothesis against Oracle, Context, and North Star...[/dim]")
            console.print()

            evaluated = []
            for i, hyp in enumerate(hypotheses):
                with Status(f"[dim]Evaluating {hyp.get('id')} ({i+1}/{len(hypotheses)})...[/dim]", console=console):
                    updated = await evaluate_hypothesis(
                        project_path=project_path,
                        hypothesis=hyp,
                        oracle=oracle,
                        context=context,
                        north_star=north_star,
                    )
                    evaluated.append(updated)

                # Show quick result
                feas = updated.get("feasibility", 0)
                align = updated.get("north_star_alignment", 0)
                status_icon = "🟢" if feas >= 0.7 and align >= 0.7 else "🟡" if feas >= 0.4 and align >= 0.4 else "🔴"
                console.print(f"  {status_icon} {updated.get('id')}: Feasibility {feas:.0%}, Alignment {align:.0%}")

            hypotheses = evaluated
            console.print()
    else:
        console.print("[dim]Auto mode - skipping confirmation[/dim]")

    # Save results
    _save_hypothesis_docs(path, hypotheses, analysis, oracle, north_star, context)

    console.print()
    console.print(f"[green]✓[/green] Saved to {path}/.1kh/hypotheses/")
    console.print()

    # Show what INTENT would do
    console.print(Panel(
        _format_intent_preview(hypotheses),
        title="What INTENT Would Do Next",
        border_style="yellow",
    ))


def _display_hypothesis_detail(hyp: dict, num: int, total: int):
    """Display a single hypothesis in detail."""
    feas = hyp.get("feasibility", 0)
    align = hyp.get("north_star_alignment", 0)

    # Color based on scores
    feas_color = "green" if feas >= 0.7 else "yellow" if feas >= 0.4 else "red"
    align_color = "green" if align >= 0.7 else "yellow" if align >= 0.4 else "red"

    console.print(Panel(
        f"[bold]{hyp.get('description', 'No description')}[/bold]\n\n"
        f"[dim]Rationale:[/dim] {hyp.get('rationale', 'None')}\n\n"
        f"[dim]Serves Objectives:[/dim] {hyp.get('serves_objectives', [])}\n"
        f"[dim]How:[/dim] {hyp.get('objective_mapping', 'Not specified')}\n\n"
        f"[dim]Effort:[/dim] {hyp.get('estimated_effort', '?')} (~{hyp.get('estimated_hours', '?')} hours)\n"
        f"[dim]Feasibility:[/dim] [{feas_color}]{feas:.0%}[/{feas_color}] (Can we build it?)\n"
        f"[dim]Alignment:[/dim] [{align_color}]{align:.0%}[/{align_color}] (Will it achieve the goal?)\n\n"
        f"[dim]Dependencies:[/dim] {hyp.get('depends_on', []) or 'None'}\n"
        f"[dim]Blocks:[/dim] {hyp.get('blocks', []) or 'None'}\n\n"
        f"[dim]Risks:[/dim] {', '.join(hyp.get('risks', [])) or 'None identified'}\n"
        f"[dim]Assumptions:[/dim] {', '.join(hyp.get('assumptions', [])) or 'None stated'}",
        title=f"[{num}/{total}] {hyp.get('id', 'Unknown')}",
        border_style="blue",
    ))


def _display_hypothesis_summary(hypotheses: list):
    """Display summary table of all hypotheses."""
    table = Table(title="Hypothesis Summary", show_lines=True)
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Objectives", width=12)
    table.add_column("Description", width=40)
    table.add_column("Feas.", width=6)
    table.add_column("Align.", width=6)
    table.add_column("Effort", width=8)
    table.add_column("Deps", width=10)

    for hyp in hypotheses:
        feas = hyp.get("feasibility", 0)
        align = hyp.get("north_star_alignment", 0)
        feas_color = "green" if feas >= 0.7 else "yellow" if feas >= 0.4 else "red"
        align_color = "green" if align >= 0.7 else "yellow" if align >= 0.4 else "red"

        table.add_row(
            hyp.get("id", "?"),
            str(hyp.get("serves_objectives", [])),
            hyp.get("description", "")[:40] + "...",
            f"[{feas_color}]{feas:.0%}[/{feas_color}]",
            f"[{align_color}]{align:.0%}[/{align_color}]",
            hyp.get("estimated_effort", "?"),
            ", ".join(hyp.get("depends_on", [])) or "-",
        )

    console.print(table)


def _save_hypothesis_docs(path: Path, hypotheses: list, analysis: dict, oracle: dict, north_star: dict, context: dict):
    """Save hypothesis documents for reference and editing."""
    hyp_dir = path / ".1kh" / "hypotheses"
    hyp_dir.mkdir(parents=True, exist_ok=True)

    # Save raw JSON
    (hyp_dir / "hypotheses.json").write_text(json.dumps({
        "generated_at": datetime.utcnow().isoformat(),
        "analysis": analysis,
        "hypotheses": hypotheses,
    }, indent=2))

    # Save analysis JSON
    if analysis:
        (hyp_dir / "analysis.json").write_text(json.dumps(analysis, indent=2))

    # Generate readable markdown
    md_lines = [
        "# Hypothesis Report",
        "",
        f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "---",
        "",
        "## Analysis Summary",
        "",
    ]

    if analysis.get("objective_coverage"):
        md_lines.append("### Objective Coverage")
        md_lines.append("")
        for obj_num, hyp_ids in analysis["objective_coverage"].items():
            obj_text = north_star.get("objectives", [])[int(obj_num)-1] if int(obj_num) <= len(north_star.get("objectives", [])) else f"Objective {obj_num}"
            md_lines.append(f"**Objective {obj_num}**: {obj_text[:80]}...")
            md_lines.append(f"  - Covered by: {', '.join(hyp_ids)}")
            md_lines.append("")

    if analysis.get("critical_dependencies"):
        md_lines.append("### Critical Dependencies")
        for dep in analysis["critical_dependencies"]:
            md_lines.append(f"- {dep}")
        md_lines.append("")

    if analysis.get("highest_risk_areas"):
        md_lines.append("### Highest Risk Areas")
        for risk in analysis["highest_risk_areas"]:
            md_lines.append(f"- ⚠️ {risk}")
        md_lines.append("")

    if analysis.get("recommended_starting_point"):
        md_lines.append(f"### Recommended Starting Point: `{analysis['recommended_starting_point']}`")
        md_lines.append("")

    md_lines.extend([
        "---",
        "",
        "## Hypotheses",
        "",
    ])

    for hyp in hypotheses:
        feas = hyp.get("feasibility", 0)
        align = hyp.get("north_star_alignment", 0)

        md_lines.extend([
            f"### {hyp.get('id', 'Unknown')}",
            "",
            f"**{hyp.get('description', 'No description')}**",
            "",
            f"*Rationale:* {hyp.get('rationale', 'None')}",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Serves Objectives | {hyp.get('serves_objectives', [])} |",
            f"| Feasibility | {feas:.0%} |",
            f"| North Star Alignment | {align:.0%} |",
            f"| Effort | {hyp.get('estimated_effort', '?')} (~{hyp.get('estimated_hours', '?')}h) |",
            f"| Dependencies | {hyp.get('depends_on', []) or 'None'} |",
            f"| Blocks | {hyp.get('blocks', []) or 'None'} |",
            "",
            f"**Objective Mapping:** {hyp.get('objective_mapping', 'Not specified')}",
            "",
        ])

        if hyp.get("risks"):
            md_lines.append("**Risks:**")
            for risk in hyp["risks"]:
                md_lines.append(f"- {risk}")
            md_lines.append("")

        if hyp.get("assumptions"):
            md_lines.append("**Assumptions:**")
            for assumption in hyp["assumptions"]:
                md_lines.append(f"- {assumption}")
            md_lines.append("")

        # Include evaluation if present
        if hyp.get("evaluation"):
            eval_data = hyp["evaluation"]
            md_lines.append("**Evaluation:**")

            if eval_data.get("oracle_compliance"):
                oc = eval_data["oracle_compliance"]
                status = "✅ Compliant" if oc.get("compliant") else "❌ VIOLATION"
                md_lines.append(f"- Oracle Compliance: {status}")
                if oc.get("concerns"):
                    for concern in oc["concerns"]:
                        md_lines.append(f"  - ⚠️ {concern}")

            if eval_data.get("recommendation"):
                rec = eval_data["recommendation"]
                proceed = "✅ Proceed" if rec.get("proceed") else "⏸️ Hold"
                md_lines.append(f"- Recommendation: {proceed} ({rec.get('confidence', 0):.0%} confidence)")
                if rec.get("questions_for_human"):
                    md_lines.append("  - Questions for you:")
                    for q in rec["questions_for_human"]:
                        md_lines.append(f"    - {q}")

            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

    (hyp_dir / "report.md").write_text("\n".join(md_lines))

    # Also save to legacy location for compatibility
    (path / ".1kh" / "imagination_output.json").write_text(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "hypotheses": hypotheses,
        "analysis": analysis,
    }, indent=2))


async def _run_imagination_temporal(path: Path, auto: bool):
    """Run imagination loop via Temporal Cloud workflow."""
    from temporal.client import create_client
    from temporal.workflows.imagination_loop import ImaginationLoopWorkflow

    console.print("[dim]Connecting to Temporal Cloud...[/dim]")

    try:
        client = await create_client(path)
    except Exception as e:
        console.print(f"[red]Failed to connect: {e}[/red]")
        console.print("[dim]Make sure your worker is running: 1kh worker start[/dim]")
        return

    console.print("[green]✓[/green] Connected to Temporal Cloud")
    console.print()

    workflow_id = f"imagination-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    console.print(f"[dim]Starting workflow: {workflow_id}[/dim]")

    handle = await client.start_workflow(
        ImaginationLoopWorkflow.run,
        args=[str(path), 20],  # Allow comprehensive generation
        id=workflow_id,
        task_queue="1kh-local",
    )

    console.print(f"[green]✓[/green] Workflow started: {workflow_id}")
    console.print("[dim]Waiting for results...[/dim]")
    console.print()

    with Status("[bold blue]Running imagination loop...", console=console):
        result = await handle.result()

    console.print("[green]✓[/green] Workflow completed")
    console.print()

    hypotheses = result.get("hypotheses", [])
    _display_hypothesis_summary(hypotheses)

    console.print()
    console.print(Panel(
        _format_intent_preview(hypotheses),
        title="What INTENT Would Do Next",
        border_style="yellow",
    ))


def _format_intent_preview(hypotheses: list) -> str:
    """Show what INTENT would do with these hypotheses."""
    # Use combined score for decision
    def combined_score(h):
        return (h.get("feasibility", 0) * 0.4) + (h.get("north_star_alignment", 0) * 0.6)

    high_confidence = [h for h in hypotheses if combined_score(h) >= 0.65]
    medium_confidence = [h for h in hypotheses if 0.4 <= combined_score(h) < 0.65]
    low_confidence = [h for h in hypotheses if combined_score(h) < 0.4]

    # Check for oracle violations
    violations = [h for h in hypotheses if h.get("status") == "oracle_violation"]

    lines = []

    if violations:
        lines.append(f"[red]❌ {len(violations)} ORACLE VIOLATIONS[/red]")
        lines.append("  These hypotheses conflict with your values and will be rejected.")
        lines.append("")

    if high_confidence:
        lines.append(f"[green]✓ {len(high_confidence)} ready to proceed[/green] (combined score ≥65%)")
        lines.append("  INTENT would: [bold]Create tasks and begin work[/bold]")
        for h in high_confidence[:3]:
            lines.append(f"    → {h.get('id')}: {h.get('description', 'Unknown')[:50]}...")
        if len(high_confidence) > 3:
            lines.append(f"    [dim]... and {len(high_confidence) - 3} more[/dim]")
    else:
        lines.append("[yellow]⚠ No high-confidence paths[/yellow]")
        lines.append("  INTENT would: [bold]Escalate to you for decision[/bold]")

    if medium_confidence:
        lines.append("")
        lines.append(f"[yellow]? {len(medium_confidence)} need more research[/yellow] (40-65%)")
        lines.append("  INTENT would: Request deeper analysis or human input")

    if low_confidence:
        lines.append("")
        lines.append(f"[red]✗ {len(low_confidence)} unlikely to succeed[/red] (<40%)")
        lines.append("  INTENT would: Defer or suggest alternatives")

    lines.append("")
    lines.append("[dim]Run '1kh run intent' to execute the INTENT loop[/dim]")
    lines.append("[dim]View details: .1kh/hypotheses/report.md[/dim]")

    return "\n".join(lines)


def _format_foundation_summary(oracle: dict, north_star: dict, context: dict, seeds: list) -> str:
    """Format foundation docs for display."""
    lines = []

    lines.append("[bold]Oracle (Your Values):[/bold]")
    for v in oracle.get("values", [])[:3]:
        lines.append(f"  • {v[:80]}{'...' if len(v) > 80 else ''}")
    if len(oracle.get("values", [])) > 3:
        lines.append(f"  [dim]... and {len(oracle['values']) - 3} more[/dim]")

    lines.append("")
    lines.append("[bold]North Star (Objectives):[/bold]")
    for obj in north_star.get("objectives", [])[:3]:
        lines.append(f"  • {obj[:80]}{'...' if len(obj) > 80 else ''}")

    lines.append("")
    lines.append("[bold]Context (Key Constraints):[/bold]")
    for c in context.get("constraints", [])[:3]:
        lines.append(f"  • {c[:80]}{'...' if len(c) > 80 else ''}")

    if seeds:
        lines.append("")
        lines.append(f"[bold]Seeds:[/bold] {len(seeds)} initial ideas to explore")

    return "\n".join(lines)


@app.command("intent")
def run_intent(
    project_path: str = typer.Option(None, "--project", "-p"),
    threshold: float = typer.Option(0.65, "--threshold", "-t", help="Combined score threshold for approval"),
    auto: bool = typer.Option(False, "--auto", "-y", help="Skip user prompts"),
):
    """
    Run the INTENT loop.

    Reviews hypotheses from imagination and makes decisions.
    """
    path = resolve_project_path(project_path)

    # Load imagination output
    output_file = path / ".1kh" / "imagination_output.json"
    if not output_file.exists():
        console.print("[red]No imagination output found.[/red]")
        console.print("Run [bold]1kh run imagination[/bold] first.")
        raise typer.Exit(1)

    data = json.loads(output_file.read_text())
    hypotheses = data.get("hypotheses", [])
    analysis = data.get("analysis", {})

    console.print()
    console.print(Panel(
        f"[bold]INTENT Loop[/bold]\n\n"
        f"Project: {path.name}\n"
        f"Hypotheses to review: {len(hypotheses)}\n"
        f"Approval threshold: {threshold:.0%}",
        border_style="yellow",
    ))
    console.print()

    # Combined score function
    def combined_score(h):
        return (h.get("feasibility", 0) * 0.4) + (h.get("north_star_alignment", 0) * 0.6)

    # Apply decision logic
    approved = []
    escalated = []
    pruned = []
    violations = []

    for hyp in hypotheses:
        if hyp.get("status") == "oracle_violation":
            violations.append(hyp)
        elif combined_score(hyp) >= threshold:
            approved.append(hyp)
        elif combined_score(hyp) >= 0.3:
            escalated.append(hyp)
        else:
            pruned.append(hyp)

    console.print("[bold cyan]Decision Summary:[/bold cyan]")
    console.print()

    if violations:
        console.print(f"[red]❌ ORACLE VIOLATIONS ({len(violations)}):[/red]")
        for h in violations:
            console.print(f"  • {h.get('id')}: {h.get('description', 'Unknown')[:60]}...")
        console.print()

    if approved:
        console.print(f"[green]✓ APPROVED ({len(approved)}):[/green]")
        for h in approved:
            score = combined_score(h)
            console.print(f"  • [{score:.0%}] {h.get('id')}: {h.get('description', 'Unknown')[:60]}...")
        console.print()

    if escalated:
        console.print(f"[yellow]? NEEDS YOUR INPUT ({len(escalated)}):[/yellow]")
        for h in escalated:
            score = combined_score(h)
            console.print(f"  • [{score:.0%}] {h.get('id')}: {h.get('description', 'Unknown')[:60]}...")

        if not auto:
            console.print()
            console.print("[dim]These hypotheses are borderline. Would you like to:[/dim]")
            action = Prompt.ask(
                "Action",
                choices=["approve_all", "review_each", "reject_all", "skip"],
                default="review_each"
            )

            if action == "approve_all":
                approved.extend(escalated)
                escalated = []
            elif action == "review_each":
                for h in escalated[:]:
                    _display_hypothesis_detail(h, escalated.index(h) + 1, len(escalated))
                    decision = Prompt.ask(
                        f"Decision for {h.get('id')}",
                        choices=["approve", "reject", "skip"],
                        default="skip"
                    )
                    if decision == "approve":
                        approved.append(h)
                        escalated.remove(h)
                    elif decision == "reject":
                        pruned.append(h)
                        escalated.remove(h)
            elif action == "reject_all":
                pruned.extend(escalated)
                escalated = []

        console.print()

    if pruned:
        console.print(f"[red]✗ PRUNED ({len(pruned)}):[/red]")
        for h in pruned[:5]:
            score = combined_score(h)
            console.print(f"  • [{score:.0%}] {h.get('id')}: {h.get('description', 'Unknown')[:60]}...")
        if len(pruned) > 5:
            console.print(f"  [dim]... and {len(pruned) - 5} more[/dim]")
        console.print()

    # Save intent output
    intent_output = path / ".1kh" / "intent_output.json"
    intent_output.write_text(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "threshold": threshold,
        "approved": approved,
        "escalated": escalated,
        "pruned": pruned,
        "violations": violations,
    }, indent=2))

    console.print(f"[dim]Results saved to: {intent_output}[/dim]")
    console.print()

    if approved:
        console.print(Panel(
            "[bold]Next Step: WORK Loop[/bold]\n\n"
            f"Ready to create {len(approved)} task(s) from approved hypotheses.\n\n"
            "[dim]Tasks would be:[/dim]\n"
            "  • Broken down into concrete steps\n"
            "  • Ordered by dependencies\n"
            "  • Executed via Claude (research) or Claude Code (build)\n\n"
            "[dim]Run '1kh run work' to create tasks (coming soon)[/dim]",
            title="What WORK Would Do",
            border_style="green",
        ))
    elif escalated:
        console.print(Panel(
            "[bold]Human Decision Needed[/bold]\n\n"
            f"{len(escalated)} hypothesis(es) still need your input.\n\n"
            "Options:\n"
            f"  • Lower threshold: [bold]1kh run intent --threshold {threshold - 0.1:.1f}[/bold]\n"
            "  • Review individually above\n"
            "  • Edit foundation docs to clarify constraints\n"
            "  • Re-run imagination with more context\n",
            title="Escalation",
            border_style="yellow",
        ))
    else:
        console.print(Panel(
            "[bold]Reality Check[/bold]\n\n"
            "No hypotheses passed the threshold. This could mean:\n\n"
            "  1. [yellow]Constraints too tight[/yellow] - Is your budget/time realistic?\n"
            "  2. [yellow]Objectives too ambitious[/yellow] - Can you break them down?\n"
            "  3. [yellow]Missing context[/yellow] - Add more detail to context.md\n"
            "  4. [yellow]Need different approach[/yellow] - Re-run imagination\n\n"
            "This is valuable feedback! Better to know now than fail later.",
            title="⚠️ No Viable Paths",
            border_style="red",
        ))


@app.command("cycle")
def run_cycle(
    project_path: str = typer.Option(None, "--project", "-p"),
    threshold: float = typer.Option(0.65, "--threshold", "-t"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n"),
    auto: bool = typer.Option(False, "--auto", "-y"),
    demo: bool = typer.Option(False, "--demo", help="Run simulation demo showing $0 → North Star"),
    local: bool = typer.Option(False, "--local", help="Run with real Claude but no Temporal (local dev mode)"),
    demo_speed: float = typer.Option(1.0, "--speed", "-s", help="Demo speed multiplier (higher = faster)"),
    demo_cycles: int = typer.Option(0, "--cycles", "--max", "-c", help="Max cycles to run (0 = until target)"),
    demo_chaos: bool = typer.Option(False, "--chaos", help="Include chaotic human behaviors in demo"),
    scenario: str = typer.Option(None, "--scenario", help="Demo scenario: missing-payment, stalled, pivot-needed, vendor-choice"),
    fresh: bool = typer.Option(False, "--fresh", help="Clear previous event history and start from $0"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output for each step"),
):
    """
    Run full IMAGINATION → INTENT cycle.

    Modes:
      --demo    All mocked (no API calls) - for visualization
      --local   Real Claude, CLI human prompts - for development
      (default) Real Claude via Temporal - for production

    Scenarios (use with --demo):
      --scenario missing-payment   Start without payment - triggers AUGMENT
      --scenario stalled           Metrics plateau - triggers OPTIMIZE
      --scenario pivot-needed      Repeated failures - triggers PIVOT (asks human)
      --scenario vendor-choice     Hypothesis needs vendor decision (asks human)

    Use --demo to run a visual simulation showing progression from $0 to North Star.
    Use --local to run with real Claude but without Temporal orchestration.
    """
    path = resolve_project_path(project_path)

    if demo:
        _run_demo_v2(path, demo_speed, demo_cycles, demo_chaos, fresh, scenario)
        return

    if local:
        _run_local(path, threshold, auto, demo_cycles, fresh, verbose)
        return

    console.print()
    console.print(Panel(
        "[bold]Full Cycle: IMAGINATION → INTENT[/bold]\n\n"
        f"Project: {path.name}\n"
        f"Approval threshold: {threshold:.0%}\n"
        f"Mode: {'Dry run' if dry_run else 'Live'}\n"
        f"User prompts: {'Disabled (--auto)' if auto else 'Enabled'}",
        border_style="magenta",
    ))
    console.print()

    # Run imagination
    console.print("[bold]=== IMAGINATION ===[/bold]")
    console.print()
    run_imagination(
        project_path=str(path),
        dry_run=dry_run,
        auto=auto,
        local=True,
    )

    if dry_run:
        console.print()
        console.print("[yellow]Dry run - skipping INTENT[/yellow]")
        return

    console.print()
    console.print("[bold]=== INTENT ===[/bold]")
    console.print()
    run_intent(
        project_path=str(path),
        threshold=threshold,
        auto=auto,
    )


def _run_demo_v2(path: Path, speed: float, max_cycles: int, include_chaos: bool, fresh: bool = False, scenario: str = None):
    """
    Run demo using the shared CycleRunner.

    Uses all mocked components - no API calls.

    Scenarios:
      - missing-payment: Start without payment component (triggers AUGMENT)
      - stalled: Metrics plateau after initial growth (triggers OPTIMIZE)
      - pivot-needed: Repeated failures (triggers PIVOT - asks human)
      - vendor-choice: Hypothesis needs vendor decision (asks human)
    """
    import time
    from core.runner import create_demo_runner
    from core.dashboard import Dashboard

    # Handle --fresh flag
    if fresh:
        dashboard = Dashboard(path)
        dashboard.event_log.clear()

        # Clear run state (cycle count, etc.)
        run_state_path = path / ".1kh" / "state" / "run_state.json"
        if run_state_path.exists():
            run_state_path.unlink()

        # Also clear old HTML reports
        reports_dir = path / ".1kh" / "reports"
        if reports_dir.exists():
            for f in reports_dir.glob("cycle_*.html"):
                f.unlink()

        console.print("[yellow]✓ Cleared previous data (events, cycle state, reports) - starting fresh[/yellow]")

    # Scenario descriptions
    scenario_desc = {
        "missing-payment": "🔴 Starting WITHOUT payment - will trigger AUGMENT",
        "stalled": "🟡 Metrics will plateau - will trigger OPTIMIZE",
        "pivot-needed": "🔴 Repeated failures - will trigger PIVOT (asks you!)",
        "vendor-choice": "🟡 Hypothesis needs vendor - will ask you to choose",
    }

    console.print()
    panel_content = (
        "[bold magenta]🚀 ThousandHand Demo Mode[/bold magenta]\n\n"
        "This simulation shows the Four Loops in action:\n"
        "  [cyan]IMAGINATION[/cyan] → Generate hypotheses\n"
        "  [yellow]INTENT[/yellow] → Make decisions\n"
        "  [green]WORK[/green] → Execute tasks\n"
        "  [blue]EXECUTION[/blue] → Track metrics\n\n"
        f"Speed: {speed}x | Chaos: {'ON' if include_chaos else 'OFF'}\n"
    )
    if scenario:
        panel_content += f"Scenario: {scenario_desc.get(scenario, scenario)}\n"
    panel_content += "\n[dim]All components are mocked - no API calls or real changes[/dim]"

    console.print(Panel(panel_content, border_style="magenta"))
    console.print()

    # State for callbacks
    cycle_start_time = [time.time()]

    def on_cycle_start(cycle: int):
        cycle_start_time[0] = time.time()
        console.print(f"[bold cyan]━━━ Cycle {cycle} ━━━[/bold cyan]")
        console.print()

    def on_cycle_end(cycle: int, result: dict):
        console.print(f"  [cyan]✓[/cyan] Generated {result['hypotheses_generated']} hypotheses")
        console.print(f"  [yellow]✓[/yellow] Approved {result['hypotheses_approved']} hypotheses")
        if result['hypotheses_escalated'] > 0:
            console.print(f"  [yellow]?[/yellow] Escalated {result['hypotheses_escalated']} for human decision")
        console.print(f"  [green]✓[/green] Executed {result['tasks_executed']} tasks "
                     f"({result['tasks_succeeded']} success, {result['tasks_failed']} failed)")
        console.print()
        time.sleep(0.3 / speed)  # Brief pause between cycles

    def on_progress_update(current: float, target: float):
        progress = (current / target) * 100 if target > 0 else 0

        # Progress bar
        bar_width = 30
        filled = int(bar_width * progress / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        # Color based on progress
        if progress >= 75:
            color = "green"
        elif progress >= 50:
            color = "yellow"
        elif progress >= 25:
            color = "cyan"
        else:
            color = "white"

        console.print(f"  [bold]Dashboard:[/bold]")
        console.print(f"    Revenue: [bold {color}]${current:,.0f}[/bold {color}] / ${target:,.0f}")
        console.print(f"    Progress: [{color}]{bar}[/{color}] {progress:.1f}%")
        console.print()

        if progress >= 100:
            console.print("[bold green]🎉 NORTH STAR REACHED! 🎉[/bold green]")
            console.print()

    # Phase names and their display messages (for loading indicators)
    phase_messages = {
        "reflection": "[magenta]REFLECTION:[/magenta] Analyzing system state...",
        "imagination": "[cyan]IMAGINATION:[/cyan] Generating hypotheses...",
        "intent": "[yellow]INTENT:[/yellow] Evaluating and deciding...",
        "work": "[green]WORK:[/green] Creating tasks...",
        "execution": "[blue]EXECUTION:[/blue] Executing tasks...",
    }

    def on_phase_start(phase: str):
        """Show loading indicator when phase starts."""
        import sys
        msg = phase_messages.get(phase, f"Running {phase}...")
        console.print(f"  ⟳ {msg}", end="")
        sys.stdout.flush()

    def on_phase_end(phase: str):
        """Clear loading indicator when phase ends."""
        console.print(" ✓")

    def on_vendor_selection_needed(prompt: str, options: list) -> str:
        """Ask user to select a vendor/technology in demo mode."""
        from rich.prompt import Prompt
        from rich.table import Table

        console.print()
        console.print(f"[bold yellow]🔧 Decision Needed[/bold yellow]")
        console.print(f"  {prompt}")
        console.print()

        # Display options as a table
        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
        table.add_column("#", style="dim", width=3)
        table.add_column("Option", style="bold")
        table.add_column("Description", style="dim")

        for i, opt in enumerate(options, 1):
            table.add_row(str(i), opt.get("name", "Unknown"), opt.get("description", ""))

        console.print(table)
        console.print()

        # Get user choice
        valid_choices = [str(i) for i in range(1, len(options) + 1)]
        choice = Prompt.ask("Select option", choices=valid_choices, default="1")

        selected = options[int(choice) - 1]
        selected_id = selected.get("id", selected.get("name", "unknown").lower())

        console.print(f"  [green]✓[/green] Selected: {selected.get('name', selected_id)}")
        console.print()

        return selected_id

    def on_pivot_decision_needed(context: dict) -> dict:
        """
        Ask user for pivot decision.

        Returns dict with:
          - decision: "continue" | "pivot_market" | "pivot_product" | "reduce_scope"
          - action: What to do next
          - updates: Any foundation doc updates needed
        """
        from rich.prompt import Prompt, Confirm

        console.print()
        console.print(Panel(
            "[bold red]⚠️ PIVOT Decision Required[/bold red]\n\n"
            f"The system has detected repeated failures:\n"
            f"  • Failure rate: {context.get('failure_rate', 0):.0%}\n"
            f"  • Consecutive failures: {context.get('consecutive_failures', 0)}\n"
            f"  • Current strategy: {context.get('current_strategy', 'Unknown')}\n\n"
            "The REFLECTION loop recommends considering a pivot.\n\n"
            "[dim]Choose wisely - pivots require updating your foundation documents.[/dim]",
            border_style="red",
        ))
        console.print()

        options = [
            ("1", "Continue + Augment", "Add new hypothesis to current strategy", "continue"),
            ("2", "Pivot: New Market", "Update north_star.md with new target audience", "pivot_market"),
            ("3", "Pivot: New Product", "Update oracle.md with new product vision", "pivot_product"),
            ("4", "Reduce Scope", "Update north_star.md with smaller goal", "reduce_scope"),
        ]

        for num, label, desc, _ in options:
            console.print(f"  [{num}] [bold]{label}[/bold] - {desc}")
        console.print()

        choice = Prompt.ask("Your decision", choices=["1", "2", "3", "4"], default="1")
        selected = options[int(choice) - 1]
        decision = selected[3]

        console.print(f"  [green]✓[/green] Decision: {selected[1]}")
        console.print()

        result = {"decision": decision, "action": None, "updates": {}}

        # Handle CONTINUE - suggest augment
        if decision == "continue":
            console.print(Panel(
                "[bold yellow]AUGMENT Mode[/bold yellow]\n\n"
                "The system will generate new hypotheses that:\n"
                "  • Address the specific failure patterns observed\n"
                "  • Try alternative approaches within current strategy\n"
                "  • Focus on quick wins to build momentum\n\n"
                "No foundation changes needed - continuing with current docs.",
                border_style="yellow",
            ))
            result["action"] = "augment"

        # Handle PIVOT decisions - need to update foundation docs
        elif decision in ["pivot_market", "pivot_product", "reduce_scope"]:
            if decision == "pivot_market":
                doc_to_update = "north_star.md"
                prompt_text = "Describe your NEW target market/customer segment"
                example = "e.g., 'Small business owners instead of enterprise'"
            elif decision == "pivot_product":
                doc_to_update = "oracle.md"
                prompt_text = "Describe your NEW product vision"
                example = "e.g., 'A simpler tool focused on one core feature'"
            else:  # reduce_scope
                doc_to_update = "north_star.md"
                prompt_text = "Describe your NEW (smaller) goal"
                example = "e.g., '$100K ARR instead of $1M' or '100 customers instead of 1000'"

            console.print(Panel(
                f"[bold cyan]Foundation Update Required[/bold cyan]\n\n"
                f"To pivot, you need to update: [bold]{doc_to_update}[/bold]\n\n"
                f"{prompt_text}\n"
                f"[dim]{example}[/dim]",
                border_style="cyan",
            ))
            console.print()

            new_direction = Prompt.ask("New direction")

            if Confirm.ask(f"Update {doc_to_update} with this new direction?", default=True):
                result["updates"] = {
                    "doc": doc_to_update,
                    "new_direction": new_direction,
                    "pivot_type": decision,
                }
                result["action"] = "update_foundation_and_restart"

                console.print()
                console.print(Panel(
                    f"[bold green]✓ Pivot Confirmed[/bold green]\n\n"
                    f"Next steps:\n"
                    f"  1. Update {doc_to_update} with: \"{new_direction[:50]}...\"\n"
                    f"  2. Run [bold]1kh run cycle --fresh[/bold] to start fresh\n"
                    f"  3. New hypotheses will be generated for the new direction\n\n"
                    "[dim]The system will stop after this cycle to let you make the updates.[/dim]",
                    border_style="green",
                ))
            else:
                console.print("[yellow]Pivot cancelled - continuing current approach[/yellow]")
                result["decision"] = "continue"
                result["action"] = "augment"

        return result

    # Create and run the demo runner
    runner = create_demo_runner(
        project_path=path,
        speed=speed,
        max_cycles=max_cycles or 100,
        include_chaos=include_chaos,
        on_cycle_start=on_cycle_start,
        on_cycle_end=on_cycle_end,
        on_progress_update=on_progress_update,
        on_phase_start=on_phase_start,
        on_phase_end=on_phase_end,
        on_vendor_selection_needed=on_vendor_selection_needed,
        on_pivot_decision_needed=on_pivot_decision_needed,
        scenario=scenario,
    )

    console.print("[bold cyan]Starting simulation...[/bold cyan]")
    console.print()

    try:
        import asyncio
        summary = asyncio.run(runner.run())
    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Demo interrupted by user[/yellow]")
        summary = runner._build_summary()

    # Final summary
    console.print()
    console.print(Panel(
        _format_runner_summary(summary),
        title="[bold]Demo Summary[/bold]",
        border_style="magenta" if summary.get("target_reached") else "yellow",
    ))


def _run_local(path: Path, threshold: float, auto: bool, max_cycles: int, fresh: bool = False, verbose: bool = False):
    """
    Run with real Claude but no Temporal.

    Good for development and testing with real API.
    """
    import asyncio
    from core.runner import create_local_runner
    from core.dashboard import Dashboard

    # Handle --fresh flag
    if fresh:
        dashboard = Dashboard(path)
        dashboard.event_log.clear()

        # Clear run state (cycle count, etc.)
        run_state_path = path / ".1kh" / "state" / "run_state.json"
        if run_state_path.exists():
            run_state_path.unlink()

        # Also clear old HTML reports
        reports_dir = path / ".1kh" / "reports"
        if reports_dir.exists():
            for f in reports_dir.glob("cycle_*.html"):
                f.unlink()

        console.print("[yellow]✓ Cleared previous reports, metrics, and cycle state - starting fresh[/yellow]")
        console.print()

    console.print()
    console.print(Panel(
        "[bold green]🔧 ThousandHand Local Mode[/bold green]\n\n"
        "Running with:\n"
        "  [green]✓[/green] Real Claude API\n"
        "  [green]✓[/green] CLI prompts for human decisions\n"
        "  [yellow]✗[/yellow] No Temporal orchestration\n\n"
        f"Approval threshold: {threshold:.0%}\n"
        f"Max cycles: {max_cycles or 'unlimited'}\n"
        f"Verbose: {'ON' if verbose else 'OFF'}\n\n"
        "[dim]API calls will be made - tokens will be consumed[/dim]",
        border_style="green",
    ))
    console.print()

    if not auto:
        from rich.prompt import Confirm
        if not Confirm.ask("Proceed with real Claude API calls?", default=True):
            console.print("[yellow]Cancelled[/yellow]")
            return

    # Phase status object for spinner management
    phase_status = {"current": None}

    def on_cycle_start(cycle: int):
        console.print(f"[bold cyan]━━━ Cycle {cycle} ━━━[/bold cyan]")
        console.print()

    def on_cycle_end(cycle: int, result: dict):
        console.print(f"  [cyan]✓[/cyan] Generated {result['hypotheses_generated']} hypotheses")
        console.print(f"  [yellow]✓[/yellow] Approved {result['hypotheses_approved']} hypotheses")
        if result['hypotheses_escalated'] > 0:
            console.print(f"  [yellow]?[/yellow] Escalated {result['hypotheses_escalated']} for human decision")
        console.print(f"  [green]✓[/green] Executed {result['tasks_executed']} tasks "
                     f"({result['tasks_succeeded']} success, {result['tasks_failed']} failed)")

        if verbose:
            console.print()
            console.print(f"    [dim]Revenue this cycle: +${result['revenue_delta']:,.0f}[/dim]")
            console.print(f"    [dim]Signups this cycle: +{result['signups_delta']}[/dim]")
        console.print()

    def on_progress_update(current: float, target: float):
        progress = (current / target) * 100 if target > 0 else 0
        bar_width = 30
        filled = int(bar_width * progress / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        color = "green" if progress >= 75 else "yellow" if progress >= 50 else "cyan" if progress >= 25 else "white"

        console.print(f"  Revenue: [bold {color}]${current:,.0f}[/bold {color}] / ${target:,.0f}")
        console.print(f"  Progress: [{color}]{bar}[/{color}] {progress:.1f}%")
        console.print()

    def on_hypothesis_generated(hyp: dict):
        if verbose:
            feas = hyp.get("feasibility", 0)
            align = hyp.get("north_star_alignment", 0)
            score = feas * 0.4 + align * 0.6
            status = "✓" if score >= 0.65 else "?" if score >= 0.4 else "✗"
            console.print(f"    [{status}] {hyp.get('id')}: {hyp.get('description', 'Unknown')[:50]}... "
                         f"[dim](score={score:.0%})[/dim]")

    def on_task_executed(task: dict, result):
        if verbose:
            if result.success:
                console.print(f"    [green]✓[/green] {task.get('id')}: +{result.metrics_delta.get('signups', 0)} signups, "
                             f"+${result.metrics_delta.get('revenue', 0)} revenue")
            else:
                console.print(f"    [red]✗[/red] {task.get('id')}: {result.errors[0] if result.errors else 'Failed'}")

    # Phase names and their display messages
    phase_messages = {
        "reflection": "[magenta]REFLECTION:[/magenta] Analyzing system state and trajectory...",
        "imagination": "[cyan]IMAGINATION:[/cyan] Generating hypotheses with Claude...",
        "intent": "[yellow]INTENT:[/yellow] Evaluating and deciding...",
        "work": "[green]WORK:[/green] Creating tasks from hypotheses...",
        "execution": "[blue]EXECUTION:[/blue] Executing tasks and measuring outcomes...",
    }

    def on_phase_start(phase: str):
        """Show loading spinner when phase starts."""
        import sys
        msg = phase_messages.get(phase, f"Running {phase}...")
        # We use a simple print with spinner indicator since Status() is sync-only
        console.print(f"  ⟳ {msg}", end="")
        sys.stdout.flush()  # Ensure immediate display

    def on_phase_end(phase: str):
        """Clear loading indicator when phase ends."""
        # Move to new line and show completion
        console.print(" ✓")

    def on_report_generated(report_path):
        """Notify when report is generated."""
        console.print(f"  [dim]📊 Report: {report_path.name}[/dim]")

    def on_vendor_selection_needed(prompt: str, options: list) -> str:
        """Ask user to select a vendor/technology when needed."""
        from rich.prompt import Prompt
        from rich.table import Table

        console.print()
        console.print(f"[bold yellow]🔧 Decision Needed[/bold yellow]")
        console.print(f"  {prompt}")
        console.print()

        # Display options as a table
        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
        table.add_column("#", style="dim", width=3)
        table.add_column("Option", style="bold")
        table.add_column("Description", style="dim")

        for i, opt in enumerate(options, 1):
            table.add_row(str(i), opt.get("name", "Unknown"), opt.get("description", ""))

        console.print(table)
        console.print()

        # Get user choice
        valid_choices = [str(i) for i in range(1, len(options) + 1)]
        choice = Prompt.ask(
            "Select option",
            choices=valid_choices,
            default="1"
        )

        selected = options[int(choice) - 1]
        selected_id = selected.get("id", selected.get("name", "unknown").lower())

        console.print(f"  [green]✓[/green] Selected: {selected.get('name', selected_id)}")
        console.print()

        return selected_id

    # Create runner with all callbacks
    runner = create_local_runner(
        project_path=path,
        console=console,
        on_cycle_start=on_cycle_start,
        on_cycle_end=on_cycle_end,
        on_progress_update=on_progress_update,
        on_hypothesis_generated=on_hypothesis_generated if verbose else None,
        on_task_executed=on_task_executed if verbose else None,
        on_phase_start=on_phase_start,
        on_phase_end=on_phase_end,
        on_report_generated=on_report_generated,
        on_vendor_selection_needed=on_vendor_selection_needed,
        generate_reports=True,
    )

    # Override config if provided
    if threshold:
        runner.config.approval_threshold = threshold
    if max_cycles:
        runner.config.max_cycles = max_cycles

    console.print("[bold green]Starting local run...[/bold green]")
    console.print()

    try:
        summary = asyncio.run(runner.run())
    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Run interrupted by user[/yellow]")
        summary = runner._build_summary()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Check your ANTHROPIC_API_KEY is set[/dim]")
        return

    # Final summary
    console.print()
    console.print(Panel(
        _format_runner_summary(summary),
        title="[bold]Run Summary[/bold]",
        border_style="green" if summary.get("target_reached") else "yellow",
    ))


def _format_runner_summary(summary: dict) -> str:
    """Format summary from CycleRunner."""
    lines = []

    if summary.get("target_reached"):
        lines.append("[bold green]✓ North Star Achieved![/bold green]")
        lines.append("")
        lines.append(f"  Final Revenue: [bold]${summary['final_revenue']:,.0f}[/bold]")
        lines.append(f"  Target: ${summary['target_revenue']:,.0f}")
    else:
        lines.append(f"[yellow]Progress: {summary['progress_pct']:.1f}%[/yellow]")
        lines.append("")
        lines.append(f"  Current Revenue: [bold]${summary['final_revenue']:,.0f}[/bold]")
        lines.append(f"  Remaining: ${summary['target_revenue'] - summary['final_revenue']:,.0f}")

    lines.append("")
    lines.append("[bold]Statistics:[/bold]")
    lines.append(f"  Cycles completed: {summary['cycles_completed']}")
    lines.append(f"  Hypotheses generated: {summary['hypotheses_total']}")
    lines.append(f"  Tasks executed: {summary['tasks_total']}")
    lines.append(f"  Human escalations: {summary['escalations_total']}")
    lines.append(f"  Task failures: {summary['failures']}")

    lines.append("")
    lines.append("[bold]Metrics:[/bold]")
    metrics = summary.get("metrics", {})
    lines.append(f"  Total signups: {metrics.get('signups', 0):.0f}")
    lines.append(f"  Success rate: {summary['success_rate'] * 100:.0f}%")

    # Time simulation
    if summary.get("time_estimate"):
        lines.append("")
        lines.append("[bold]Time Estimate:[/bold]")
        lines.append(f"  Simulated time: [cyan]{summary['time_estimate']}[/cyan]")
        lines.append(f"  [dim]({summary['days_per_cycle']} days per cycle × {summary['cycles_completed']} cycles)[/dim]")

    # Pivot required
    if summary.get("pivot_required"):
        lines.append("")
        lines.append("[bold red]⚠️ PIVOT CONFIRMED[/bold red]")
        updates = summary.get("pivot_updates", {})
        if updates.get("doc"):
            lines.append(f"  Update required: [bold]{updates['doc']}[/bold]")
            lines.append(f"  New direction: {updates.get('new_direction', 'See above')[:60]}...")
        lines.append("")
        lines.append("[bold]Next steps:[/bold]")
        lines.append("  1. Edit your foundation document with the new direction")
        lines.append("  2. Run [bold cyan]1kh run cycle --fresh[/bold cyan] to start fresh")

    return "\n".join(lines)


def _run_demo(path: Path, speed: float, max_cycles: int, include_chaos: bool):
    """
    Run interactive demo showing $0 → North Star progression.

    This uses mock components to simulate the full cycle without
    burning Claude API tokens or making real changes.
    """
    import time
    import random
    from rich.live import Live
    from rich.layout import Layout
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

    # Import mocks and core
    from core.dashboard import Dashboard, EventType
    from tests.mocks.execution import ScenarioExecutor, ProgressionSimulator
    from tests.mocks.human import (
        MockHumanSimple,
        MockHumanChaotic,
        ChaoticBehavior,
        EscalationManager,
        EscalationType,
    )
    from core.conversation import ConversationManager, ImpasseHandler

    console.print()
    console.print(Panel(
        "[bold magenta]🚀 ThousandHand Demo Mode[/bold magenta]\n\n"
        "This simulation shows the Four Loops in action:\n"
        "  [cyan]IMAGINATION[/cyan] → Generate hypotheses\n"
        "  [yellow]INTENT[/yellow] → Make decisions\n"
        "  [green]WORK[/green] → Execute tasks\n"
        "  [blue]EXECUTION[/blue] → Track metrics\n\n"
        f"Speed: {speed}x | Chaos: {'ON' if include_chaos else 'OFF'}\n\n"
        "[dim]All components are mocked - no API calls or real changes[/dim]",
        border_style="magenta",
    ))
    console.print()

    # Initialize components
    dashboard = Dashboard(path)
    dashboard.set_north_star("$1M ARR", target_value=1_000_000)

    # Choose human mock
    if include_chaos:
        human = MockHumanChaotic(
            behavior=random.choice([
                ChaoticBehavior.SPARSE,
                ChaoticBehavior.CONTRADICTORY,
                ChaoticBehavior.DELAYED,
            ]),
            severity=0.3,  # 30% chaotic
            recovery_after=5,
        )
        console.print("[yellow]⚠ Chaotic human enabled - expect some turbulence![/yellow]")
    else:
        human = MockHumanSimple(patterns={
            "conflict_resolution": "prioritize_first",
            "approval_request": "always_approve",
            "guidance_request": "provide_default",
            "error_recovery": "retry",
        })

    esc_manager = EscalationManager(path, human=human, dashboard=dashboard)
    conv_manager = ConversationManager(path)
    executor = ScenarioExecutor(path, dashboard)

    # Simulation state
    cycle = 0
    hypotheses_total = 0
    tasks_total = 0
    escalations_total = 0
    failures = 0

    # Scenario weights (happy path weighted higher)
    scenarios = [
        ("success_small", 0.3),
        ("success_large", 0.25),
        ("partial_success", 0.2),
        ("failure_transient", 0.15),
        ("blocked", 0.07),
        ("failure_permanent", 0.03),
    ]

    def pick_scenario():
        r = random.random()
        cumulative = 0
        for scenario, weight in scenarios:
            cumulative += weight
            if r <= cumulative:
                return scenario
        return "success_small"

    # Calculate delay based on speed
    base_delay = 0.5 / speed

    console.print()
    console.print("[bold cyan]Starting simulation...[/bold cyan]")
    console.print()

    target_reached = False
    max_cycles = max_cycles or 100  # Safety limit

    try:
        while cycle < max_cycles and not target_reached:
            cycle += 1

            # =====================================================
            # IMAGINATION Phase
            # =====================================================
            console.print(f"[bold cyan]━━━ Cycle {cycle} ━━━[/bold cyan]")
            console.print()

            with console.status("[cyan]IMAGINATION: Generating hypotheses...[/cyan]"):
                time.sleep(base_delay * 2)

            # Generate 2-4 mock hypotheses per cycle
            num_hypotheses = random.randint(2, 4)
            hypotheses = []
            for i in range(num_hypotheses):
                hyp = {
                    "id": f"hyp-{cycle:03d}-{i+1}",
                    "description": random.choice([
                        "Implement email marketing automation",
                        "Add social proof to landing page",
                        "Create referral program",
                        "Optimize checkout flow",
                        "Launch content marketing campaign",
                        "Build partnership integrations",
                        "Improve onboarding experience",
                        "Add premium tier pricing",
                    ]),
                    "feasibility": random.uniform(0.5, 0.95),
                    "north_star_alignment": random.uniform(0.6, 0.98),
                }
                hypotheses.append(hyp)
                hypotheses_total += 1

            console.print(f"  [cyan]✓[/cyan] Generated {len(hypotheses)} hypotheses")

            # Log to dashboard
            for hyp in hypotheses:
                dashboard.log_event(
                    EventType.HYPOTHESIS_CREATED,
                    metadata={"id": hyp["id"], "desc": hyp["description"][:50]},
                )

            time.sleep(base_delay)

            # =====================================================
            # INTENT Phase
            # =====================================================
            with console.status("[yellow]INTENT: Evaluating and deciding...[/yellow]"):
                time.sleep(base_delay)

            approved = []
            escalated = []

            for hyp in hypotheses:
                score = hyp["feasibility"] * 0.4 + hyp["north_star_alignment"] * 0.6

                if score >= 0.65:
                    approved.append(hyp)
                    dashboard.log_event(EventType.HYPOTHESIS_ACCEPTED, metadata={"id": hyp["id"]})
                elif score >= 0.4:
                    # Needs human input
                    escalated.append(hyp)
                    escalations_total += 1

            if approved:
                console.print(f"  [yellow]✓[/yellow] Approved {len(approved)} hypotheses")

            if escalated:
                console.print(f"  [yellow]?[/yellow] Escalating {len(escalated)} for human decision")

                # Create escalations
                for hyp in escalated:
                    esc = esc_manager.create_escalation(
                        type=EscalationType.APPROVAL_REQUEST,
                        summary=f"Approve: {hyp['description'][:40]}?",
                        context={"hypothesis_id": hyp["id"]},
                    )

                # Process with human mock
                responses = esc_manager.process_pending()
                for resp in responses:
                    if resp.action == "approve":
                        # Find and approve the hypothesis
                        for hyp in escalated:
                            if hyp not in approved:
                                approved.append(hyp)
                                dashboard.log_event(EventType.HYPOTHESIS_ACCEPTED, metadata={"id": hyp["id"]})
                                break

                if include_chaos and not responses:
                    console.print(f"    [red]⚠ Human unresponsive - some hypotheses blocked[/red]")

            time.sleep(base_delay)

            # =====================================================
            # WORK Phase
            # =====================================================
            if not approved:
                console.print(f"  [dim]No approved hypotheses - skipping WORK[/dim]")
                time.sleep(base_delay)
                continue

            with console.status("[green]WORK: Creating and executing tasks...[/green]"):
                time.sleep(base_delay)

            tasks_this_cycle = 0
            for hyp in approved[:2]:  # Limit to 2 per cycle for demo
                # Create mock task
                task = {
                    "id": f"task-{cycle:03d}-{tasks_this_cycle+1}",
                    "hypothesis_id": hyp["id"],
                    "description": f"Execute: {hyp['description'][:30]}",
                }
                tasks_total += 1
                tasks_this_cycle += 1

                dashboard.log_event(EventType.TASK_CREATED, task_id=task["id"])

                # Execute with scenario
                scenario = pick_scenario()
                executor.queue_scenario(scenario)
                outcome = executor.execute(task, hyp)

                if outcome.success:
                    dashboard.log_event(EventType.TASK_COMPLETED, task_id=task["id"])

                    # Log metrics from outcome
                    if outcome.metrics_delta.get("revenue"):
                        dashboard.log_event(
                            EventType.REVENUE,
                            value=outcome.metrics_delta["revenue"],
                            metadata={"source": "demo", "task_id": task["id"]},
                        )
                    if outcome.metrics_delta.get("signups"):
                        dashboard.log_event(
                            EventType.SIGNUP,
                            value=outcome.metrics_delta["signups"],
                            metadata={"task_id": task["id"]},
                        )
                else:
                    dashboard.log_event(
                        EventType.TASK_FAILED,
                        task_id=task["id"],
                        metadata={"errors": outcome.errors[:1]},
                    )
                    failures += 1

            console.print(f"  [green]✓[/green] Executed {tasks_this_cycle} tasks")
            time.sleep(base_delay)

            # =====================================================
            # EXECUTION / Dashboard Update
            # =====================================================
            state = dashboard.compute_state()

            # Format currency
            revenue = state.north_star.current_value
            target = state.north_star.target_value
            progress = state.north_star.progress_pct

            # Progress bar
            bar_width = 30
            filled = int(bar_width * progress / 100)
            bar = "█" * filled + "░" * (bar_width - filled)

            # Color based on progress
            if progress >= 75:
                color = "green"
            elif progress >= 50:
                color = "yellow"
            elif progress >= 25:
                color = "cyan"
            else:
                color = "white"

            console.print()
            console.print(f"  [bold]Dashboard:[/bold]")
            console.print(f"    Revenue: [bold {color}]${revenue:,.0f}[/bold {color}] / ${target:,.0f}")
            console.print(f"    Progress: [{color}]{bar}[/{color}] {progress:.1f}%")
            console.print(f"    Signups: {state.metrics_lifetime.get('signups', 0):.0f}")
            console.print(f"    Tasks: {state.tasks_completed} completed, {state.tasks_failed} failed")
            console.print()

            # Check if target reached
            if progress >= 100:
                target_reached = True
                console.print("[bold green]🎉 NORTH STAR REACHED! 🎉[/bold green]")
                console.print()

            # Log cycle completion
            dashboard.log_event(EventType.CYCLE_COMPLETED, metadata={"cycle": cycle})

            time.sleep(base_delay)

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Demo interrupted by user[/yellow]")

    # =====================================================
    # Final Summary
    # =====================================================
    console.print()
    console.print(Panel(
        _format_demo_summary(
            dashboard, cycle, hypotheses_total, tasks_total,
            escalations_total, failures, target_reached
        ),
        title="[bold]Demo Summary[/bold]",
        border_style="magenta" if target_reached else "yellow",
    ))


def _format_demo_summary(
    dashboard,
    cycles: int,
    hypotheses: int,
    tasks: int,
    escalations: int,
    failures: int,
    target_reached: bool,
) -> str:
    """Format the final demo summary."""
    state = dashboard.compute_state()
    revenue = state.north_star.current_value
    target = state.north_star.target_value
    progress = state.north_star.progress_pct

    lines = []

    if target_reached:
        lines.append("[bold green]✓ North Star Achieved![/bold green]")
        lines.append("")
        lines.append(f"  Final Revenue: [bold]${revenue:,.0f}[/bold]")
        lines.append(f"  Target: ${target:,.0f}")
    else:
        lines.append(f"[yellow]Progress: {progress:.1f}%[/yellow]")
        lines.append("")
        lines.append(f"  Current Revenue: [bold]${revenue:,.0f}[/bold]")
        lines.append(f"  Remaining: ${target - revenue:,.0f}")

    lines.append("")
    lines.append("[bold]Statistics:[/bold]")
    lines.append(f"  Cycles completed: {cycles}")
    lines.append(f"  Hypotheses generated: {hypotheses}")
    lines.append(f"  Tasks executed: {tasks}")
    lines.append(f"  Human escalations: {escalations}")
    lines.append(f"  Task failures: {failures}")

    lines.append("")
    lines.append("[bold]Metrics:[/bold]")
    lines.append(f"  Total signups: {state.metrics_lifetime.get('signups', 0):.0f}")
    lines.append(f"  Success rate: {(tasks - failures) / max(tasks, 1) * 100:.0f}%")

    lines.append("")
    lines.append("[dim]This was a simulation using mocked components.[/dim]")
    lines.append("[dim]No actual API calls or changes were made.[/dim]")

    return "\n".join(lines)
