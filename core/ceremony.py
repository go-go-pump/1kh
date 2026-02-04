"""
Initial Ceremony - The structured onboarding process.

Orchestrates Phases 2-7 of project initialization:
    Phase 2: Listening - Capture raw input
    Phase 3: Probing - Ask clarifying questions (uses Claude)
    Phase 4: Structuring - Present categorized understanding
    Phase 4.5: Architecture Preview - Explain what will be built
    Phase 5: Committing - Write foundation documents
    Phase 6: Connecting - Validate API keys
    Phase 7: Finalize - Complete ceremony
"""

import json
import os
from pathlib import Path
from typing import Optional
import uuid

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.status import Status

from core.models import (
    CeremonyState,
    Oracle,
    NorthStar,
    Context,
    Seed,
    Preferences,
    CommunicationChannel,
    SystemType,
    NorthStarType,
    UtilitySubtype,
    UTILITY_SUBTYPE_METRICS,
)
from core.claude_client import ClaudeClient


class InitialCeremony:
    """
    Orchestrates the Initial Ceremony for a new ThousandHand project.
    """

    def __init__(self, project_path: Path, project_name: str, console: Console):
        self.project_path = project_path
        self.project_name = project_name
        self.console = console
        self.claude = ClaudeClient(project_path=project_path)
        self.state_file = project_path / ".1kh" / "state" / "ceremony_state.json"

    def run_phases_2_through_4(self) -> CeremonyState:
        """
        Run the listening, probing, and structuring phases.
        Returns the ceremony state ready for committing.
        """
        # Check for resumed state
        state = self._load_state()
        if state and state.phase >= 2:
            self.console.print("[dim]Resuming from previous session...[/dim]")
        else:
            state = CeremonyState(
                project_path=str(self.project_path),
                project_name=self.project_name,
            )

        # Phase 2: Listening
        if state.phase < 2:
            state = self._phase_2_listening(state)
            self._save_state(state)

        # Phase 2.5: System Type Detection (BIZ vs USER)
        if state.system_type is None and state.raw_input:
            state = self._phase_2_5_system_type_detection(state)
            self._save_state(state)

        # Phase 3: Probing (multiple rounds)
        if state.phase < 3:
            state = self._phase_3_probing(state)
            self._save_state(state)

        # Phase 4: Structuring
        if state.phase < 4:
            state = self._phase_4_structuring(state)
            self._save_state(state)

        # Phase 4.5: Architecture Preview
        self._phase_4_5_architecture_preview()

        # Phase 4.6: North Star Type Confirmation
        state = self._phase_4_6_north_star_confirmation(state)
        self._save_state(state)

        # Phase 4.7: Utility Subtype Detection (for USER systems with utility north star)
        if (state.system_type == SystemType.USER and
            state.north_star and
            state.north_star.north_star_type == NorthStarType.UTILITY):
            state = self._phase_4_7_utility_subtype_detection(state)
            self._save_state(state)

        return state

    def _phase_2_listening(self, state: CeremonyState) -> CeremonyState:
        """Capture raw, unstructured input from the human."""
        self.console.print()
        self.console.print("[dim]Phase 2: Listening[/dim]")
        self.console.print()
        self.console.print(
            "Tell me what you want to build. Be as specific or vague as you like.\n"
            "Include all the details - I'll save everything and ask follow-ups.\n"
        )
        self.console.print("[dim]Paste or type your input. Type 'DONE' on its own line when finished.[/dim]")
        self.console.print()

        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break

            # Check for termination signal (case-insensitive, trimmed)
            if line.strip().upper() == "DONE":
                break

            lines.append(line)

        state.raw_input = "\n".join(lines)
        state.phase = 2

        # Show what was captured
        self.console.print()
        self.console.print(f"[green]✓[/green] Captured {len(lines)} lines of input.")
        self.console.print("[dim]Your full input will be saved to raw_input.md[/dim]")

        return state

    def _phase_2_5_system_type_detection(self, state: CeremonyState) -> CeremonyState:
        """Detect whether this is a BIZ or USER system."""
        self.console.print()
        self.console.print("[dim]Phase 2.5: Understanding Your Goals[/dim]")
        self.console.print()

        # Use Claude to detect system type
        with Status("[bold blue]Analyzing project type...", console=self.console):
            detection = self.claude.detect_system_type(state.raw_input)

        system_type = detection.get("system_type", "user")
        confidence = detection.get("confidence", 0.5)
        reasoning = detection.get("reasoning", "")
        suggested_ns_type = detection.get("suggested_north_star_type", "utility")
        key_signals = detection.get("key_signals", [])

        # Present detection to user
        if system_type == "biz":
            self.console.print(Panel(
                "[bold cyan]I detected this as a BUSINESS SYSTEM[/bold cyan]\n\n"
                f"[dim]Reasoning: {reasoning}[/dim]\n"
                f"[dim]Key signals: {', '.join(key_signals) if key_signals else 'general business indicators'}[/dim]\n\n"
                "[bold]What this means:[/bold]\n"
                "• Primary goal: Generate revenue/profit for you (the owner)\n"
                "• Hypothesis-driven: We'll test business assumptions\n"
                "• Metrics focus: Revenue, conversion, customer acquisition\n"
                "• North Star type: Likely revenue or profit-based",
                title="System Type Detection",
                border_style="green",
            ))
        else:
            self.console.print(Panel(
                "[bold cyan]I detected this as a USER SYSTEM[/bold cyan]\n\n"
                f"[dim]Reasoning: {reasoning}[/dim]\n"
                f"[dim]Key signals: {', '.join(key_signals) if key_signals else 'utility-focused indicators'}[/dim]\n\n"
                "[bold]What this means:[/bold]\n"
                "• Primary goal: Provide utility/value to users (possibly yourself)\n"
                "• Feature-driven: We'll build toward a capability checklist\n"
                "• Metrics focus: User satisfaction, completeness, learning\n"
                "• Hypothesis-driven approach is OPTIONAL until you want external users",
                title="System Type Detection",
                border_style="blue",
            ))

        self.console.print()

        # Confirm or override
        choices = ["biz", "user"]
        current_choice = "biz" if system_type == "biz" else "user"

        self.console.print("[bold]Is this correct?[/bold]")
        self.console.print("  [dim]biz[/dim]  = I'm building to make money (revenue, profit, customers)")
        self.console.print("  [dim]user[/dim] = I'm building for utility (personal tool, hobby, learning, open source)")
        self.console.print()

        confirmed = Prompt.ask(
            "System type",
            choices=choices,
            default=current_choice,
        )

        # Store in state
        state.system_type = SystemType.BIZ if confirmed == "biz" else SystemType.USER

        # Store suggested north star type for later
        state.preferences.custom["suggested_north_star_type"] = suggested_ns_type

        self.console.print()
        if confirmed == "biz":
            self.console.print("[green]✓[/green] Confirmed as BUSINESS SYSTEM - will use hypothesis-driven approach")
        else:
            self.console.print("[green]✓[/green] Confirmed as USER SYSTEM - will use feature-driven approach")

        return state

    def _phase_3_probing(self, state: CeremonyState) -> CeremonyState:
        """Ask clarifying questions using Claude - multiple rounds."""
        self.console.print()
        self.console.print("[dim]Phase 3: Probing[/dim]")
        self.console.print()

        all_answers = state.preferences.custom.get("probing_answers", {})
        round_num = 1
        max_rounds = 3

        while round_num <= max_rounds:
            self.console.print(f"[bold]Round {round_num} of {max_rounds}[/bold]")
            self.console.print("[dim]Answer each question. Type 'skip' to skip, 'DONE' to finish probing.[/dim]")
            self.console.print()

            # Generate questions with loading indicator (tailored to system type)
            system_type_str = state.system_type.value if state.system_type else "user"
            with Status("[bold blue]Generating questions...", console=self.console):
                questions = self.claude.generate_probing_questions(
                    raw_input=state.raw_input,
                    existing_answers=all_answers,
                    system_type=system_type_str,
                )

            if not questions:
                self.console.print("[dim]No more questions needed.[/dim]")
                break

            done_early = False
            for i, question in enumerate(questions, 1):
                self.console.print(f"[bold]{i}.[/bold] {question}")
                answer = Prompt.ask("   →", default="")

                # Check for early termination
                if answer.strip().upper() == "DONE":
                    self.console.print("[dim]Finishing probing.[/dim]")
                    done_early = True
                    break

                # Allow skipping
                if answer.strip().lower() != "skip" and answer.strip():
                    all_answers[question] = answer

                self.console.print()

            if done_early:
                break

            # Ask if they want another round
            if round_num < max_rounds:
                self.console.print()
                if not Confirm.ask("Want me to probe deeper with more questions?", default=False):
                    break

            round_num += 1

        # Store answers in state for structuring
        state.context = Context(constraints=[])
        state.phase = 3
        state.preferences.custom["probing_answers"] = all_answers

        self.console.print()
        self.console.print(f"[green]✓[/green] Collected {len(all_answers)} answers.")

        return state

    def _phase_4_structuring(self, state: CeremonyState) -> CeremonyState:
        """Present categorized understanding for human review."""
        self.console.print()
        self.console.print("[dim]Phase 4: Structuring[/dim]")
        self.console.print()

        # Use Claude to structure the input with loading indicator
        with Status("[bold blue]Analyzing and structuring your input...", console=self.console):
            structured = self.claude.structure_input(
                raw_input=state.raw_input,
                probing_answers=state.preferences.custom.get("probing_answers", {}),
            )

        # Present to human
        self.console.print("Here's what I understand:\n")

        self.console.print("[bold cyan]ORACLE (Your Values):[/bold cyan]")
        for value in structured.get("oracle_values", []):
            self.console.print(f"  • {value}")
        self.console.print()

        self.console.print("[bold cyan]ORACLE (Will Never Do):[/bold cyan]")
        never_do = structured.get("oracle_never_do", [])
        if never_do:
            for item in never_do:
                self.console.print(f"  • {item}")
        else:
            self.console.print("  [dim](none specified)[/dim]")
        self.console.print()

        self.console.print("[bold cyan]NORTH STAR (Objectives):[/bold cyan]")
        for obj in structured.get("north_star_objectives", []):
            # Truncate long objectives for display but keep full version
            display = obj[:200] + "..." if len(obj) > 200 else obj
            self.console.print(f"  • {display}")
        self.console.print()

        self.console.print("[bold cyan]SUCCESS METRICS:[/bold cyan]")
        metrics = structured.get("success_metrics", [])
        if metrics:
            for m in metrics:
                self.console.print(f"  • {m}")
        else:
            self.console.print("  [dim](to be defined)[/dim]")
        self.console.print()

        self.console.print("[bold cyan]CONTEXT (Resources & Constraints):[/bold cyan]")
        for ctx in structured.get("context_items", [])[:10]:  # Show max 10 for readability
            display = ctx[:150] + "..." if len(ctx) > 150 else ctx
            self.console.print(f"  • {display}")
        if len(structured.get("context_items", [])) > 10:
            self.console.print(f"  [dim]... and {len(structured['context_items']) - 10} more[/dim]")
        self.console.print()

        self.console.print("[bold cyan]SEEDS (Initial Hypotheses):[/bold cyan]")
        for seed in structured.get("seeds", [])[:5]:  # Show max 5
            display = seed[:150] + "..." if len(seed) > 150 else seed
            self.console.print(f"  • {display}")
        if len(structured.get("seeds", [])) > 5:
            self.console.print(f"  [dim]... and {len(structured['seeds']) - 5} more[/dim]")
        self.console.print()

        # Important note about editing
        self.console.print(Panel(
            "[bold]Note:[/bold] This is a summary. Your complete input is preserved.\n"
            "After the ceremony, you can edit the foundation docs directly:\n"
            "  • oracle.md - Your values and boundaries\n"
            "  • north-star.md - Your objectives\n"
            "  • context.md - Resources and constraints\n"
            "  • .1kh/raw_input.md - Your original input (read-only reference)",
            title="Editing Your Foundation",
            border_style="blue",
        ))
        self.console.print()

        # Confirm or edit
        if Confirm.ask("Does this general direction look right?"):
            # Populate state from structured data
            state.oracle = Oracle(
                values=structured.get("oracle_values", []),
                never_do=structured.get("oracle_never_do", []),
            )
            state.north_star = NorthStar(
                objectives=[{"description": obj} for obj in structured.get("north_star_objectives", [])],
                success_metrics=structured.get("success_metrics", []),
            )
            state.context = Context(
                constraints=structured.get("context_items", []),
            )
            state.seeds = [
                Seed(id=f"seed-{uuid.uuid4().hex[:8]}", description=s)
                for s in structured.get("seeds", [])
            ]
            state.phase = 4
        else:
            # Allow re-probing
            self.console.print("[yellow]Let's gather more information.[/yellow]")
            state.phase = 2  # Go back to probing
            return self._phase_3_probing(state)

        return state

    def _phase_4_5_architecture_preview(self):
        """Explain what will be built - set expectations."""
        self.console.print()
        self.console.print("[dim]Phase 4.5: Architecture Preview[/dim]")
        self.console.print()

        self.console.print(Panel(
            "[bold]What ThousandHand Will Build For You[/bold]\n\n"
            "Once autonomous operation is enabled, 1KH will:\n\n"
            "[cyan]1. IMAGINATION Loop[/cyan]\n"
            "   • Generate hypotheses for achieving your North Star\n"
            "   • Estimate what's feasible given your context\n"
            "   • Recommend paths forward or ask for guidance\n\n"
            "[cyan]2. INTENT Loop[/cyan]\n"
            "   • Make strategic decisions (which paths to pursue)\n"
            "   • Observe outcomes and adapt\n"
            "   • Prune approaches that aren't working\n\n"
            "[cyan]3. WORK Loop[/cyan]\n"
            "   • Break decisions into concrete tasks\n"
            "   • Manage task queue and priorities\n"
            "   • Track progress toward objectives\n\n"
            "[cyan]4. EXECUTION (via Claude Code)[/cyan]\n"
            "   • Build actual workflows and integrations\n"
            "   • Deploy and test solutions\n"
            "   • Collect metrics and report outcomes\n\n"
            "[dim]Learn more: See FOUNDATION.md and docs/TEMPORAL_SETUP.md[/dim]",
            title="How 1KH Works",
            border_style="green",
        ))

        self.console.print()
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")

    def _phase_4_6_north_star_confirmation(self, state: CeremonyState) -> CeremonyState:
        """Confirm North Star type based on system type and objectives."""
        self.console.print()
        self.console.print("[dim]Phase 4.6: North Star Confirmation[/dim]")
        self.console.print()

        # Get suggested type from earlier detection
        suggested = state.preferences.custom.get("suggested_north_star_type", "utility")

        # Map to NorthStarType enum value
        ns_type_map = {
            "revenue": NorthStarType.REVENUE,
            "profit": NorthStarType.PROFIT,
            "users": NorthStarType.USERS,
            "engagement": NorthStarType.ENGAGEMENT,
            "utility": NorthStarType.UTILITY,
            "learning": NorthStarType.LEARNING,
            "portfolio": NorthStarType.PORTFOLIO,
            "custom": NorthStarType.CUSTOM,
        }

        # Present options based on system type
        if state.system_type == SystemType.BIZ:
            self.console.print("[bold]What's your primary success metric?[/bold]")
            self.console.print()
            self.console.print("  [cyan]revenue[/cyan]     = Hit a revenue target ($X ARR, $Y MRR)")
            self.console.print("  [cyan]profit[/cyan]      = Hit a profit target (margin, net income)")
            self.console.print("  [cyan]users[/cyan]       = Reach N active users/customers")
            self.console.print("  [cyan]engagement[/cyan]  = Achieve usage metrics (time, sessions)")
            self.console.print("  [cyan]custom[/cyan]      = Something else (you'll define)")
            self.console.print()

            choices = ["revenue", "profit", "users", "engagement", "custom"]
            default = suggested if suggested in choices else "revenue"
        else:
            self.console.print("[bold]What does success look like for you?[/bold]")
            self.console.print()
            self.console.print("  [cyan]utility[/cyan]     = Working tool that solves the problem")
            self.console.print("  [cyan]learning[/cyan]    = Skill development, understanding")
            self.console.print("  [cyan]portfolio[/cyan]   = Demonstrable work to show others")
            self.console.print("  [cyan]users[/cyan]       = Other people using and benefiting")
            self.console.print("  [cyan]custom[/cyan]      = Something else (you'll define)")
            self.console.print()

            choices = ["utility", "learning", "portfolio", "users", "custom"]
            default = suggested if suggested in choices else "utility"

        selected = Prompt.ask(
            "North Star type",
            choices=choices,
            default=default,
        )

        # Update North Star with type
        if state.north_star:
            state.north_star.north_star_type = ns_type_map.get(selected, NorthStarType.CUSTOM)
        else:
            state.north_star = NorthStar(
                north_star_type=ns_type_map.get(selected, NorthStarType.CUSTOM)
            )

        self.console.print()
        self.console.print(f"[green]✓[/green] North Star type set to: [bold]{selected.upper()}[/bold]")

        # Give context on what this means
        if selected == "revenue":
            self.console.print("[dim]   → Hypotheses will be scored by revenue potential[/dim]")
            self.console.print("[dim]   → REFLECTION will track revenue progress[/dim]")
        elif selected == "users":
            self.console.print("[dim]   → Hypotheses will be scored by user acquisition potential[/dim]")
            self.console.print("[dim]   → REFLECTION will track user growth[/dim]")
        elif selected == "utility":
            self.console.print("[dim]   → Work will be driven by feature completeness[/dim]")
            self.console.print("[dim]   → Hypothesis-testing is optional[/dim]")
        elif selected == "learning":
            self.console.print("[dim]   → Focus on skill development and understanding[/dim]")
            self.console.print("[dim]   → Progress measured by what you've learned[/dim]")

        return state

    def _phase_4_7_utility_subtype_detection(self, state: CeremonyState) -> CeremonyState:
        """Detect utility subtype and suggest appropriate metrics for USER systems."""
        self.console.print()
        self.console.print("[dim]Phase 4.7: Utility Type Detection[/dim]")
        self.console.print()

        # Use Claude to detect utility subtype
        with Status("[bold blue]Analyzing utility type...", console=self.console):
            detection = self.claude.detect_utility_subtype(state.raw_input)

        suggested_subtype = detection.get("utility_subtype", "poc")
        confidence = detection.get("confidence", 0.5)
        reasoning = detection.get("reasoning", "")

        # Map to enum
        subtype_map = {
            # General
            "poc": UtilitySubtype.POC,
            "internal_tool": UtilitySubtype.INTERNAL_TOOL,
            "custom": UtilitySubtype.CUSTOM,
            # Infrastructure
            "multi_tenant": UtilitySubtype.MULTI_TENANT,
            "orchestrator": UtilitySubtype.ORCHESTRATOR,
            "api_gateway": UtilitySubtype.API_GATEWAY,
            "auth_service": UtilitySubtype.AUTH_SERVICE,
            "monitoring": UtilitySubtype.MONITORING,
            # Data
            "data_pipeline": UtilitySubtype.DATA_PIPELINE,
            "search": UtilitySubtype.SEARCH,
            "migration": UtilitySubtype.MIGRATION,
            "scraper": UtilitySubtype.SCRAPER,
            # Compute
            "scheduler": UtilitySubtype.SCHEDULER,
            "automation": UtilitySubtype.AUTOMATION,
            "ml_model": UtilitySubtype.ML_MODEL,
            "simulator": UtilitySubtype.SIMULATOR,
            # Developer
            "library": UtilitySubtype.LIBRARY,
            "cli": UtilitySubtype.CLI,
            "webhook_handler": UtilitySubtype.WEBHOOK_HANDLER,
            # Content
            "content_generator": UtilitySubtype.CONTENT_GENERATOR,
            "notification": UtilitySubtype.NOTIFICATION,
        }

        detected_subtype = subtype_map.get(suggested_subtype, UtilitySubtype.POC)
        subtype_info = UTILITY_SUBTYPE_METRICS.get(detected_subtype, UTILITY_SUBTYPE_METRICS[UtilitySubtype.POC])

        # Present detection
        self.console.print(Panel(
            f"[bold cyan]Detected Utility Type: {detected_subtype.value.upper()}[/bold cyan]\n\n"
            f"[dim]{subtype_info['description']}[/dim]\n\n"
            f"[dim]Reasoning: {reasoning}[/dim]\n\n"
            f"[bold]Primary KPI:[/bold] {subtype_info['primary_kpi']}\n\n"
            "[bold]Suggested Metrics:[/bold]",
            title="Utility Type Analysis",
            border_style="blue",
        ))

        for metric in subtype_info.get("suggested_metrics", []):
            self.console.print(f"  • {metric}")

        self.console.print()

        if subtype_info.get("hypothesis_driven"):
            self.console.print("[dim]This utility type benefits from hypothesis-driven improvement.[/dim]")
        else:
            self.console.print("[dim]This utility type is primarily feature-driven.[/dim]")

        self.console.print()

        # Confirm or override
        self.console.print("[bold]Select utility type:[/bold]")
        self.console.print()
        self.console.print("[dim]─── Infrastructure ───[/dim]")
        self.console.print("  [cyan]multi_tenant[/cyan]    = Shared service - reliability, tenant isolation")
        self.console.print("  [cyan]orchestrator[/cyan]    = Service manager - config, visibility")
        self.console.print("  [cyan]api_gateway[/cyan]     = Integration/routing - latency, error rate")
        self.console.print("  [cyan]auth_service[/cyan]    = Identity/access - auth speed, security")
        self.console.print("  [cyan]monitoring[/cyan]      = Observability - alert accuracy, freshness")
        self.console.print()
        self.console.print("[dim]─── Data ───[/dim]")
        self.console.print("  [cyan]data_pipeline[/cyan]   = ETL/streaming - throughput, accuracy")
        self.console.print("  [cyan]search[/cyan]          = Indexing/retrieval - query speed, relevance")
        self.console.print("  [cyan]migration[/cyan]       = Data/schema migration - zero loss, speed")
        self.console.print("  [cyan]scraper[/cyan]         = Data collection - success rate, freshness")
        self.console.print()
        self.console.print("[dim]─── Compute ───[/dim]")
        self.console.print("  [cyan]scheduler[/cyan]       = Event-driven - timing, throughput")
        self.console.print("  [cyan]automation[/cyan]      = Workflow - success rate, error handling")
        self.console.print("  [cyan]ml_model[/cyan]        = Machine learning - accuracy, inference speed")
        self.console.print("  [cyan]simulator[/cyan]       = Testing/modeling - accuracy, speed")
        self.console.print()
        self.console.print("[dim]─── Developer ───[/dim]")
        self.console.print("  [cyan]library[/cyan]         = SDK/API - developer experience")
        self.console.print("  [cyan]cli[/cyan]             = Command line tool - execution success")
        self.console.print("  [cyan]webhook_handler[/cyan] = Event ingestion - processing latency")
        self.console.print()
        self.console.print("[dim]─── Content ───[/dim]")
        self.console.print("  [cyan]content_generator[/cyan] = AI/media content - quality, speed")
        self.console.print("  [cyan]notification[/cyan]    = Alerts/messaging - delivery rate")
        self.console.print()
        self.console.print("[dim]─── General ───[/dim]")
        self.console.print("  [cyan]poc[/cyan]             = Proof of concept - 'IT JUST WORKS'")
        self.console.print("  [cyan]internal_tool[/cyan]   = Productivity - task completion, time saved")
        self.console.print("  [cyan]custom[/cyan]          = Something else (you'll define)")
        self.console.print()

        choices = [
            # Infrastructure
            "multi_tenant", "orchestrator", "api_gateway", "auth_service", "monitoring",
            # Data
            "data_pipeline", "search", "migration", "scraper",
            # Compute
            "scheduler", "automation", "ml_model", "simulator",
            # Developer
            "library", "cli", "webhook_handler",
            # Content
            "content_generator", "notification",
            # General
            "poc", "internal_tool", "custom"
        ]

        selected = Prompt.ask(
            "Utility type",
            choices=choices,
            default=suggested_subtype if suggested_subtype in choices else "poc",
        )

        final_subtype = subtype_map.get(selected, UtilitySubtype.CUSTOM)
        final_info = UTILITY_SUBTYPE_METRICS.get(final_subtype, UTILITY_SUBTYPE_METRICS[UtilitySubtype.CUSTOM])

        # Update state
        if state.north_star:
            state.north_star.utility_subtype = final_subtype

            # Ask if they want to use suggested metrics
            self.console.print()
            if final_info.get("suggested_metrics") and Confirm.ask(
                "Use suggested metrics as starting point?", default=True
            ):
                # Merge suggested metrics with any existing ones
                existing = set(state.north_star.success_metrics)
                for metric in final_info["suggested_metrics"]:
                    if metric not in existing:
                        state.north_star.success_metrics.append(metric)
                self.console.print(f"[green]✓[/green] Added {len(final_info['suggested_metrics'])} suggested metrics")
                self.console.print("[dim]   You can edit these in north-star.md after ceremony completes.[/dim]")
            else:
                self.console.print("[dim]You can define your own metrics in north-star.md[/dim]")

        self.console.print()
        self.console.print(f"[green]✓[/green] Utility type set to: [bold]{selected.upper()}[/bold]")
        self.console.print(f"[dim]   Primary KPI: {final_info['primary_kpi']}[/dim]")

        return state

    def commit_foundation(self, state: CeremonyState) -> None:
        """Write foundation documents to the project."""
        # FIRST: Save raw input (this is the most important - don't lose user's words)
        raw_input_path = self.project_path / ".1kh" / "raw_input.md"
        raw_input_content = self._generate_raw_input_md(state)
        raw_input_path.write_text(raw_input_content)

        # Write oracle.md
        oracle_path = self.project_path / "oracle.md"
        oracle_content = self._generate_oracle_md(state.oracle)
        oracle_path.write_text(oracle_content)

        # Write north-star.md
        ns_path = self.project_path / "north-star.md"
        ns_content = self._generate_north_star_md(state.north_star, state.raw_input, state.system_type)
        ns_path.write_text(ns_content)

        # Write context.md
        ctx_path = self.project_path / "context.md"
        ctx_content = self._generate_context_md(state.context, state.preferences.custom.get("probing_answers", {}))
        ctx_path.write_text(ctx_content)

        # Write seeds.json
        seeds_path = self.project_path / ".1kh" / "seeds.json"
        seeds_data = [s.model_dump() for s in state.seeds]
        seeds_path.write_text(json.dumps(seeds_data, indent=2, default=str))

        # Write preferences.json
        prefs_path = self.project_path / ".1kh" / "preferences.json"
        prefs_path.write_text(state.preferences.model_dump_json(indent=2))

        state.phase = 5
        self._save_state(state)

    def connect_services(self, state: CeremonyState) -> bool:
        """Validate existing API keys (already collected in Phase 1.5)."""
        env_path = self.project_path / ".1kh" / ".env"

        # Load existing keys
        existing_keys = self._load_env_keys(env_path)

        # Check required keys are present
        required_keys = [
            ("ANTHROPIC_API_KEY", "Claude API"),
            ("TEMPORAL_CLOUD_API_KEY", "Temporal Cloud"),
        ]

        all_valid = True
        for key_name, display_name in required_keys:
            if existing_keys.get(key_name):
                self.console.print(f"  [green]✓[/green] {display_name}: configured")
                state.api_keys_collected[key_name] = True
            else:
                self.console.print(f"  [yellow]![/yellow] {display_name}: not configured")
                state.api_keys_collected[key_name] = False
                # Temporal is optional for now (can run without autonomous mode)
                if key_name == "ANTHROPIC_API_KEY":
                    all_valid = False

        self.console.print()

        # Communication preference
        self.console.print("[bold]How should I send you updates?[/bold]")
        self.console.print("[dim]  cli   = Check status via '1kh status' and '1kh escalations'[/dim]")
        self.console.print("[dim]  email = Get daily digest and urgent escalations via email[/dim]")
        self.console.print("[dim]  sms   = Get urgent escalations via SMS (requires Twilio)[/dim]")
        self.console.print("[dim]  slack = Get updates in a Slack channel (requires setup)[/dim]")
        self.console.print()

        channel = Prompt.ask(
            "Channel",
            choices=["email", "cli", "sms", "slack"],
            default="cli",
        )
        state.preferences.communication_channel = CommunicationChannel(channel)

        if channel == "email":
            email = Prompt.ask("Your email address")
            state.preferences.custom["email"] = email
        elif channel == "cli":
            self.console.print()
            self.console.print("[dim]With CLI mode, you'll check in manually:[/dim]")
            self.console.print("[dim]  • '1kh status'      - See tree health and progress[/dim]")
            self.console.print("[dim]  • '1kh escalations' - See items needing your input[/dim]")
            self.console.print("[dim]  • '1kh logs'        - See decision history[/dim]")

        state.phase = 6
        self._save_state(state)

        return all_valid

    def _load_env_keys(self, env_path: Path) -> dict:
        """Load keys from .env file."""
        keys = {}
        if not env_path.exists():
            return keys
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                if value.strip():
                    keys[key.strip()] = value.strip()
        return keys

    def ignite(self, state: CeremonyState) -> None:
        """
        Finalize setup and explain next steps clearly.
        """
        self.console.print()
        self.console.print("[yellow]⚠ Autonomous mode not yet implemented.[/yellow]")
        self.console.print()
        self.console.print("[bold]What's Ready Now:[/bold]")
        self.console.print("  [green]✓[/green] Foundation documents (oracle.md, north-star.md, context.md)")
        self.console.print("  [green]✓[/green] Raw input preserved (.1kh/raw_input.md)")
        self.console.print("  [green]✓[/green] Seeds captured (.1kh/seeds.json)")
        self.console.print("  [green]✓[/green] API keys configured (.1kh/.env)")
        self.console.print()

        self.console.print(Panel(
            "[bold]Your Immediate Next Steps:[/bold]\n\n"
            "1. [cyan]Review your foundation docs[/cyan]\n"
            f"   • {self.project_path}/oracle.md\n"
            "     Your values and hard boundaries (what the system will NEVER do)\n"
            f"   • {self.project_path}/north-star.md\n"
            "     Your objectives and success metrics (what we're building toward)\n"
            f"   • {self.project_path}/context.md\n"
            "     Your resources, constraints, and background info\n\n"
            "2. [cyan]Check your raw input was captured[/cyan]\n"
            f"   View: {self.project_path}/.1kh/raw_input.md\n"
            "   This preserves everything you typed verbatim.\n\n"
            "3. [cyan]Start the worker (when ready)[/cyan]\n"
            "   Run: [bold]1kh worker start[/bold]\n"
            "   This connects to Temporal and begins autonomous operation.\n\n"
            "[dim]Questions? See docs/TEMPORAL_SETUP.md[/dim]",
            title="Next Steps",
            border_style="green",
        ))

        state.phase = 7
        self._save_state(state)

    # ========================================================================
    # Helpers
    # ========================================================================

    def _save_state(self, state: CeremonyState) -> None:
        """Persist ceremony state for resume capability."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(state.model_dump_json(indent=2))

    def _load_state(self) -> Optional[CeremonyState]:
        """Load ceremony state if it exists."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                return CeremonyState(**data)
            except Exception:
                return None
        return None

    def _generate_raw_input_md(self, state: CeremonyState) -> str:
        """Generate raw_input.md - preserves the user's original words."""
        lines = [
            "# Raw Input",
            "",
            "*This file preserves your original input exactly as you typed it.*",
            "*It's here for reference - the system uses the structured docs for operation.*",
            "",
            "---",
            "",
            "## Original Input (Phase 2: Listening)",
            "",
            state.raw_input or "(no input captured)",
            "",
            "---",
            "",
            "## Probing Q&A (Phase 3)",
            "",
        ]

        probing_answers = state.preferences.custom.get("probing_answers", {})
        if probing_answers:
            for question, answer in probing_answers.items():
                lines.append(f"**Q: {question}**")
                lines.append(f"A: {answer}")
                lines.append("")
        else:
            lines.append("(no probing answers captured)")

        lines.extend([
            "",
            "---",
            f"*Captured during Initial Ceremony for project: {state.project_name}*",
        ])

        return "\n".join(lines)

    def _generate_oracle_md(self, oracle: Oracle) -> str:
        """Generate oracle.md content."""
        lines = [
            "# Oracle",
            "",
            "These are the immutable values and principles for this project.",
            "ThousandHand will NEVER violate these.",
            "",
            "> **Edit this file** to refine your values. The system reads this on every decision.",
            "",
            "## Values",
            "",
        ]
        for value in oracle.values:
            lines.append(f"- {value}")

        if oracle.never_do:
            lines.extend(["", "## We Will Never", ""])
            for item in oracle.never_do:
                lines.append(f"- {item}")
        else:
            lines.extend([
                "",
                "## We Will Never",
                "",
                "- (Add boundaries here - things the system should never do)",
            ])

        if oracle.always_do:
            lines.extend(["", "## We Will Always", ""])
            for item in oracle.always_do:
                lines.append(f"- {item}")

        lines.extend([
            "",
            "---",
            f"*Version: {oracle.version}*",
            f"*Created: {oracle.created_at.isoformat()}*",
        ])

        return "\n".join(lines)

    def _generate_north_star_md(self, north_star: NorthStar, raw_input: str = "", system_type: SystemType = None) -> str:
        """Generate north-star.md content - includes full description."""
        lines = [
            "# North Star",
            "",
            "These are the measurable, time-bound objectives we're working toward.",
            "",
            "> **Edit this file** to adjust your goals. Be specific about what success looks like.",
            "",
        ]

        # Add system type and north star type metadata
        if system_type:
            system_label = "BUSINESS SYSTEM" if system_type == SystemType.BIZ else "USER SYSTEM"
            lines.extend([
                f"**System Type:** {system_label}",
                "",
            ])

        if north_star.north_star_type:
            lines.extend([
                f"**North Star Type:** {north_star.north_star_type.value.upper()}",
                "",
            ])

        # Add utility subtype for USER systems
        if north_star.utility_subtype:
            subtype_info = UTILITY_SUBTYPE_METRICS.get(
                north_star.utility_subtype,
                {"description": "Custom utility type", "primary_kpi": "User-defined"}
            )
            lines.extend([
                f"**Utility Subtype:** {north_star.utility_subtype.value.upper()}",
                f"*{subtype_info['description']}*",
                "",
                f"**Primary KPI:** {subtype_info['primary_kpi']}",
                "",
            ])

        lines.extend([
            "## Primary Objective",
            "",
        ])

        # Include the full raw input as context
        if raw_input:
            lines.append("### Full Description")
            lines.append("")
            lines.append(raw_input)
            lines.append("")
            lines.append("### Extracted Objectives")
            lines.append("")

        for obj in north_star.objectives:
            desc = obj.get("description", str(obj))
            lines.append(f"- {desc}")

        if north_star.success_metrics:
            lines.extend(["", "## Success Metrics", ""])
            for metric in north_star.success_metrics:
                lines.append(f"- {metric}")
        else:
            lines.extend([
                "",
                "## Success Metrics",
                "",
                "- (Define how you'll measure success)",
            ])

        if north_star.deadline:
            lines.extend(["", f"**Deadline:** {north_star.deadline.isoformat()}", ""])

        lines.extend([
            "",
            "---",
            f"*Version: {north_star.version}*",
            f"*Created: {north_star.created_at.isoformat()}*",
        ])

        return "\n".join(lines)

    def _generate_context_md(self, context: Context, probing_answers: dict = None) -> str:
        """Generate context.md content - includes probing Q&A."""
        lines = [
            "# Context",
            "",
            "These are the constraints and resources for this project.",
            "",
            "> **Edit this file** to update your resources and constraints.",
            "",
        ]

        if context.budget_monthly:
            lines.append(f"**Monthly Budget:** ${context.budget_monthly}")
        if context.budget_total:
            lines.append(f"**Total Budget:** ${context.budget_total}")
        if context.time_weekly_hours:
            lines.append(f"**Time Available:** {context.time_weekly_hours} hours/week")

        if context.existing_assets:
            lines.extend(["", "## Existing Assets", ""])
            for asset in context.existing_assets:
                lines.append(f"- {asset}")

        if context.skills:
            lines.extend(["", "## Skills", ""])
            for skill in context.skills:
                lines.append(f"- {skill}")

        if context.constraints:
            lines.extend(["", "## Constraints & Details", ""])
            for constraint in context.constraints:
                lines.append(f"- {constraint}")

        # Include probing answers as additional context
        if probing_answers:
            lines.extend(["", "## From Probing Questions", ""])
            for question, answer in probing_answers.items():
                lines.append(f"**{question}**")
                lines.append(f"{answer}")
                lines.append("")

        return "\n".join(lines)
