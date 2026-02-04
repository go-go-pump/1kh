"""
1kh init - The Initial Ceremony

This command orchestrates Phases 0-7 of project initialization:
    Phase 0: Awakening - CLI launched
    Phase 1: Grounding - Select project directory, scaffold structure
    Phase 1.5: Keys - Collect essential API keys (deterministic, no AI needed)
    Phase 2: Listening - Capture raw input
    Phase 3: Probing - Ask clarifying questions (requires Claude)
    Phase 4: Structuring - Present categorized understanding
    Phase 5: Committing - Write foundation documents
    Phase 6: Connecting - Validate connections, collect optional integrations
    Phase 7: Igniting - Deploy loops and begin
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.table import Table

from core.ceremony import InitialCeremony
from core.models import CeremonyState
from core.config import (
    get_known_projects,
    get_last_active_project,
    register_project,
    update_project_phase,
    set_last_active_project,
    get_project_phase_description,
)

app = typer.Typer()
console = Console()


# Required keys - need these to function
REQUIRED_KEYS = {
    "ANTHROPIC_API_KEY": {
        "name": "Anthropic (Claude)",
        "description": "Powers all AI reasoning. Required for any intelligent behavior.",
        "url": "https://console.anthropic.com/account/keys",
        "required": True,
    },
}

# Optional keys - can add later
OPTIONAL_KEYS = {
    "TEMPORAL_CLOUD_API_KEY": {
        "name": "Temporal Cloud",
        "description": "Orchestrates loops and workflows. Required for autonomous operation.",
        "url": "https://cloud.temporal.io/settings/api-keys",
        "required": False,
    },
    "TEMPORAL_NAMESPACE": {
        "name": "Temporal Namespace",
        "description": "Your Temporal Cloud namespace (e.g., 'your-namespace.a1b2c3').",
        "url": None,
        "required": False,
    },
    "TEMPORAL_ADDRESS": {
        "name": "Temporal Address",
        "description": "Your Temporal Cloud address (e.g., 'your-namespace.a1b2c3.tmprl.cloud:7233').",
        "url": None,
        "required": False,
    },
}


@app.callback(invoke_without_command=True)
def init_project(
    path: Optional[Path] = typer.Argument(
        None,
        help="Directory for the new project. If not provided, will check for existing projects.",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name", "-n",
        help="Project name. Defaults to directory name.",
    ),
    skip_keys: bool = typer.Option(
        False,
        "--skip-keys",
        help="Skip API key setup (for testing or if keys already exist).",
    ),
    new: bool = typer.Option(
        False,
        "--new",
        help="Force creation of a new project (skip project selection).",
    ),
):
    """
    Start or resume a ThousandHand project.

    If existing projects are found, offers to resume. Use --new to force a new project.
    """
    console.print()
    console.print(Panel.fit(
        "[bold green]ThousandHand[/bold green] - Initial Ceremony",
        subtitle="Let's build something together",
    ))
    console.print()

    # Phase 0: Awakening - Check for existing projects
    console.print("[dim]Phase 0: Awakening[/dim]")

    # If path provided explicitly, use that
    if path:
        project_path = path.resolve()
        project_name = name or project_path.name
        is_new_project = not (project_path / ".1kh").exists()
    elif new:
        # Force new project flow
        project_path, project_name, is_new_project = _select_or_create_project(force_new=True)
    else:
        # Check for existing projects
        project_path, project_name, is_new_project = _select_or_create_project(force_new=False)

    if name:
        project_name = name

    console.print()
    console.print(f"Project: [bold]{project_name}[/bold]")
    console.print(f"Location: [dim]{project_path}[/dim]")
    console.print()

    if is_new_project:
        # New project - run full ceremony
        _run_new_project_ceremony(project_path, project_name, skip_keys)
    else:
        # Existing project - resume from where we left off
        _resume_project_ceremony(project_path, project_name, skip_keys)


def _select_or_create_project(force_new: bool = False) -> tuple[Path, str, bool]:
    """
    Check for existing projects and let user select or create new.
    Returns (path, name, is_new_project).
    """
    if force_new:
        return _get_new_project_path(), "", True

    known_projects = get_known_projects()
    last_active = get_last_active_project()

    if not known_projects:
        console.print("No existing projects found.")
        console.print()
        return _get_new_project_path(), "", True

    # Show existing projects
    console.print("Found existing projects:\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=3)
    table.add_column("Project", style="cyan")
    table.add_column("Status")
    table.add_column("Path", style="dim")

    for i, proj in enumerate(known_projects, 1):
        is_last = proj.get("path") == (last_active or {}).get("path")
        marker = " [green]← last[/green]" if is_last else ""
        phase_desc = get_project_phase_description(proj.get("phase", 0))
        table.add_row(
            str(i),
            proj.get("name", "Unknown") + marker,
            phase_desc,
            proj.get("path", ""),
        )

    console.print(table)
    console.print()

    # Offer choices
    console.print("Options:")
    console.print("  • Enter a [bold]number[/bold] to resume that project")
    console.print("  • Enter [bold]n[/bold] or [bold]new[/bold] to create a new project")
    console.print("  • Press [bold]Enter[/bold] to resume the last active project")
    console.print()

    choice = Prompt.ask(
        "Your choice",
        default="1" if last_active else "n",
    ).strip().lower()

    if choice in ("n", "new"):
        return _get_new_project_path(), "", True

    # Try to parse as number
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(known_projects):
            proj = known_projects[idx]
            return Path(proj["path"]), proj.get("name", ""), False
    except ValueError:
        pass

    # Default to last active or first project
    if last_active:
        return Path(last_active["path"]), last_active.get("name", ""), False
    elif known_projects:
        proj = known_projects[0]
        return Path(proj["path"]), proj.get("name", ""), False

    return _get_new_project_path(), "", True


def _get_new_project_path() -> Path:
    """Prompt for new project directory."""
    console.print()
    console.print("Where should this project live?")
    console.print("[dim]Enter a path or '.' for current directory[/dim]")

    while True:
        path_str = Prompt.ask("Project directory", default=".")
        path = Path(path_str).resolve()

        if path.exists() and not path.is_dir():
            console.print("[red]Path exists but is not a directory.[/red]")
            continue

        if not path.exists():
            if Confirm.ask(f"Create directory {path}?"):
                path.mkdir(parents=True)
            else:
                continue

        return path


def _run_new_project_ceremony(project_path: Path, project_name: str, skip_keys: bool):
    """Run the full ceremony for a new project."""
    project_name = project_name or project_path.name

    # Phase 1: Grounding - Scaffold
    console.print("[dim]Phase 1: Grounding[/dim]")

    # Check if directory already has a 1KH project
    if (project_path / ".1kh").exists():
        if not Confirm.ask("This directory already has a 1KH project. Reinitialize?"):
            raise typer.Exit(0)

    # Create directory structure
    _scaffold_project(project_path)

    # Register project globally
    register_project(project_path, project_name, phase=1)

    # Continue with rest of ceremony
    _continue_ceremony_from_phase(project_path, project_name, skip_keys, from_phase=1)


def _resume_project_ceremony(project_path: Path, project_name: str, skip_keys: bool):
    """Resume ceremony for existing project."""
    project_name = project_name or project_path.name

    # Load state to see where we left off
    state_file = project_path / ".1kh" / "state" / "ceremony_state.json"

    if state_file.exists():
        import json
        try:
            state_data = json.loads(state_file.read_text())
            current_phase = state_data.get("phase", 0)
        except (json.JSONDecodeError, IOError):
            current_phase = 0
    else:
        current_phase = 1  # Has .1kh but no state = stuck at phase 1

    console.print(f"[dim]Resuming from: {get_project_phase_description(current_phase)}[/dim]")
    console.print()

    # Update last accessed
    set_last_active_project(project_path)

    # Continue from where we left off
    _continue_ceremony_from_phase(project_path, project_name, skip_keys, from_phase=current_phase)


def _continue_ceremony_from_phase(
    project_path: Path,
    project_name: str,
    skip_keys: bool,
    from_phase: int,
):
    """Continue the ceremony from a specific phase."""
    env_path = project_path / ".1kh" / ".env"

    # Phase 1.5: Keys (if not done yet or no anthropic key)
    if from_phase < 2:
        console.print()
        console.print("[dim]Phase 1.5: Keys[/dim]")

        if skip_keys:
            console.print("[yellow]Skipping key setup (--skip-keys flag).[/yellow]")
        else:
            _setup_api_keys(project_path, env_path)

    # Check if we can proceed with AI-powered phases
    anthropic_key = _get_key_from_env(env_path, "ANTHROPIC_API_KEY")
    if not anthropic_key:
        console.print()
        console.print("[yellow]⚠ No Anthropic API key configured.[/yellow]")
        console.print("The next phases require Claude for intelligent probing.")
        console.print()
        console.print("Options:")
        console.print(f"  1. Add your key to: [bold]{env_path}[/bold]")
        console.print("  2. Set ANTHROPIC_API_KEY environment variable")
        console.print("  3. Re-run [bold]1kh init[/bold] after adding the key")
        console.print()
        raise typer.Exit(1)

    # Phase 2-4: Listening, Probing, Structuring (handled by ceremony)
    ceremony = InitialCeremony(project_path, project_name, console)

    try:
        state = ceremony.run_phases_2_through_4()
        update_project_phase(project_path, state.phase)
    except KeyboardInterrupt:
        console.print("\n[yellow]Ceremony interrupted. Your progress has been saved.[/yellow]")
        console.print(f"Resume with: [bold]1kh init[/bold]")
        raise typer.Exit(0)

    # Phase 5: Committing
    console.print()
    console.print("[dim]Phase 5: Committing[/dim]")
    ceremony.commit_foundation(state)
    console.print("[green]Foundation documents written.[/green]")
    update_project_phase(project_path, 5)

    # Phase 6: Connecting
    console.print()
    console.print("[dim]Phase 6: Connecting[/dim]")
    if not ceremony.connect_services(state):
        console.print("[yellow]Some connections failed. You can retry with:[/yellow]")
        console.print(f"  [bold]1kh init[/bold]")
        update_project_phase(project_path, 6)
        raise typer.Exit(1)
    update_project_phase(project_path, 6)

    # Phase 7: Finalize
    console.print()
    console.print("[dim]Phase 7: Finalize[/dim]")
    if Confirm.ask("Finalize setup and complete the Initial Ceremony?"):
        ceremony.ignite(state)
        update_project_phase(project_path, 7)
        console.print()
        console.print(Panel.fit(
            "[bold green]Initial Ceremony Complete![/bold green]\n\n"
            "Your foundation is set. Review your docs:\n"
            f"  • {project_path}/oracle.md\n"
            f"  • {project_path}/north-star.md\n"
            f"  • {project_path}/context.md\n\n"
            "[dim]Autonomous operation (Temporal) coming soon.[/dim]",
            title="ThousandHand Setup Complete",
        ))
    else:
        console.print("[yellow]Finalization skipped. When ready, run:[/yellow]")
        console.print(f"  [bold]1kh init[/bold]")


def _scaffold_project(path: Path) -> None:
    """Create the basic project structure."""
    dirs = [
        ".1kh/logs/decisions",
        ".1kh/state",
        ".1kh/escalations",
        "artifacts/workflows",
        "artifacts/documents",
    ]

    for dir_path in dirs:
        (path / dir_path).mkdir(parents=True, exist_ok=True)

    # Create .gitignore
    gitignore = path / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            "# 1KH\n"
            ".1kh/.env\n"
            ".1kh/state/*.json\n"
            "\n"
            "# Python\n"
            "__pycache__/\n"
            "*.pyc\n"
            ".venv/\n"
        )

    # Create empty .env file with template
    env_path = path / ".1kh" / ".env"
    if not env_path.exists():
        env_path.write_text(
            "# ThousandHand API Keys\n"
            "# This file is gitignored - safe to store secrets here\n"
            "\n"
            "# Required: Powers all AI reasoning\n"
            "ANTHROPIC_API_KEY=\n"
            "\n"
            "# Required for autonomous operation (Temporal Cloud):\n"
            "TEMPORAL_CLOUD_API_KEY=\n"
            "TEMPORAL_NAMESPACE=\n"
            "TEMPORAL_ADDRESS=\n"
            "\n"
            "# Optional integrations (add as needed):\n"
            "# SENDGRID_API_KEY=\n"
            "# TWILIO_ACCOUNT_SID=\n"
            "# TWILIO_AUTH_TOKEN=\n"
        )

    console.print("[green]Project structure created.[/green]")


def _setup_api_keys(project_path: Path, env_path: Path) -> None:
    """Interactive API key setup."""
    console.print("Before we begin the intelligent phases, I need API keys.")
    console.print()

    # Show where keys will be stored
    console.print(f"Keys will be stored in: [bold]{env_path}[/bold]")
    console.print("[dim]This file is gitignored. You can also edit it directly.[/dim]")
    console.print()

    # Load existing keys
    existing_keys = _load_env_file(env_path)

    # Show status table
    table = Table(title="API Key Status", show_header=True)
    table.add_column("Service", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Required", justify="center")

    all_keys = {**REQUIRED_KEYS, **OPTIONAL_KEYS}
    for key_name, key_info in all_keys.items():
        has_key = bool(existing_keys.get(key_name))
        status = "[green]✓ Set[/green]" if has_key else "[dim]Not set[/dim]"
        required = "[red]Yes[/red]" if key_info["required"] else "[dim]No[/dim]"
        table.add_row(key_info["name"], status, required)

    console.print(table)
    console.print()

    # Check if required keys are already set
    required_set = all(
        existing_keys.get(k) for k in REQUIRED_KEYS.keys()
    )

    if required_set:
        console.print("[green]All required keys are configured.[/green]")
        if not Confirm.ask("Update or add keys?", default=False):
            return

    # Prompt for required keys
    console.print()
    console.print("[bold]Required Keys[/bold]")
    console.print("These are needed for 1KH to function:")
    console.print()

    updated_keys = dict(existing_keys)

    for key_name, key_info in REQUIRED_KEYS.items():
        current = existing_keys.get(key_name, "")
        masked = _mask_key(current) if current else "[dim]not set[/dim]"

        console.print(f"[cyan]{key_info['name']}[/cyan]")
        console.print(f"  {key_info['description']}")
        if key_info.get("url"):
            console.print(f"  Get one at: [link={key_info['url']}]{key_info['url']}[/link]")
        console.print(f"  Current: {masked}")

        new_value = Prompt.ask(
            "  Enter key (or press Enter to keep current)",
            default="",
            show_default=False,
        )

        if new_value:
            updated_keys[key_name] = new_value
            console.print("  [green]Updated.[/green]")
        elif not current:
            console.print("  [yellow]Skipped (will need to set before AI phases).[/yellow]")

        console.print()

    # Ask about optional keys
    if Confirm.ask("Configure optional keys now?", default=False):
        console.print()
        console.print("[bold]Optional Keys[/bold]")
        console.print("These enable autonomous operation (can add later):")
        console.print()

        for key_name, key_info in OPTIONAL_KEYS.items():
            current = existing_keys.get(key_name, "")
            masked = _mask_key(current) if current else "[dim]not set[/dim]"

            console.print(f"[cyan]{key_info['name']}[/cyan]")
            console.print(f"  {key_info['description']}")
            if key_info.get("url"):
                console.print(f"  Get one at: [link={key_info['url']}]{key_info['url']}[/link]")
            console.print(f"  Current: {masked}")

            new_value = Prompt.ask(
                "  Enter key (or press Enter to skip)",
                default="",
                show_default=False,
            )

            if new_value:
                updated_keys[key_name] = new_value
                console.print("  [green]Updated.[/green]")

            console.print()

    # Save updated keys
    _save_env_file(env_path, updated_keys)
    console.print(f"[green]Keys saved to {env_path}[/green]")


def _load_env_file(env_path: Path) -> dict[str, str]:
    """Load key-value pairs from .env file."""
    result = {}
    if not env_path.exists():
        return result

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if value:  # Only include if value is non-empty
                result[key] = value

    return result


def _save_env_file(env_path: Path, keys: dict[str, str]) -> None:
    """Save keys to .env file, preserving comments."""
    lines = [
        "# ThousandHand API Keys",
        "# This file is gitignored - safe to store secrets here",
        "",
        "# Required: Powers all AI reasoning",
        f"ANTHROPIC_API_KEY={keys.get('ANTHROPIC_API_KEY', '')}",
        "",
        "# Required for autonomous operation (Temporal Cloud):",
        f"TEMPORAL_CLOUD_API_KEY={keys.get('TEMPORAL_CLOUD_API_KEY', '')}",
        f"TEMPORAL_NAMESPACE={keys.get('TEMPORAL_NAMESPACE', '')}",
        f"TEMPORAL_ADDRESS={keys.get('TEMPORAL_ADDRESS', '')}",
        "",
        "# Optional integrations (add as needed):",
        "# SENDGRID_API_KEY=",
        "# TWILIO_ACCOUNT_SID=",
        "# TWILIO_AUTH_TOKEN=",
    ]

    # Add any extra keys that aren't in our template
    known_keys = set(REQUIRED_KEYS.keys()) | set(OPTIONAL_KEYS.keys())
    extra_keys = {k: v for k, v in keys.items() if k not in known_keys}

    if extra_keys:
        lines.append("")
        lines.append("# Additional keys:")
        for k, v in extra_keys.items():
            lines.append(f"{k}={v}")

    env_path.write_text("\n".join(lines) + "\n")


def _get_key_from_env(env_path: Path, key_name: str) -> Optional[str]:
    """Get a specific key, checking file first then environment."""
    # Check file first
    keys = _load_env_file(env_path)
    if keys.get(key_name):
        return keys[key_name]

    # Fall back to environment
    return os.environ.get(key_name)


def _mask_key(key: str) -> str:
    """Mask a key for display, showing first 4 and last 4 chars."""
    if len(key) <= 12:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"
