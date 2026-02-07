"""
Global configuration management for ThousandHand.

Manages:
- Known projects and their locations
- Last active project
- Global preferences

Config location: ~/.1kh/config.json
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# Global config lives in user's home directory
GLOBAL_CONFIG_DIR = Path.home() / ".1kh"
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.json"


def get_global_config() -> dict:
    """Load global config, creating if needed."""
    if not GLOBAL_CONFIG_FILE.exists():
        return {
            "version": "0.1.0",
            "projects": {},
            "last_active_project": None,
            "created_at": datetime.now().isoformat(),
        }

    try:
        return json.loads(GLOBAL_CONFIG_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return {
            "version": "0.1.0",
            "projects": {},
            "last_active_project": None,
            "created_at": datetime.now().isoformat(),
        }


def save_global_config(config: dict) -> None:
    """Save global config."""
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    GLOBAL_CONFIG_FILE.write_text(json.dumps(config, indent=2, default=str))


def register_project(path: Path, name: str, phase: int = 0) -> None:
    """Register a project in global config."""
    config = get_global_config()

    path_str = str(path.resolve())
    config["projects"][path_str] = {
        "name": name,
        "path": path_str,
        "phase": phase,
        "registered_at": datetime.now().isoformat(),
        "last_accessed": datetime.now().isoformat(),
    }
    config["last_active_project"] = path_str

    save_global_config(config)


def update_project_phase(path: Path, phase: int) -> None:
    """Update a project's current phase."""
    config = get_global_config()
    path_str = str(path.resolve())

    if path_str in config["projects"]:
        config["projects"][path_str]["phase"] = phase
        config["projects"][path_str]["last_accessed"] = datetime.now().isoformat()
        config["last_active_project"] = path_str
        save_global_config(config)


def set_last_active_project(path: Path) -> None:
    """Set the last active project."""
    config = get_global_config()
    path_str = str(path.resolve())

    if path_str in config["projects"]:
        config["projects"][path_str]["last_accessed"] = datetime.now().isoformat()
        config["last_active_project"] = path_str
        save_global_config(config)


def get_known_projects() -> list[dict]:
    """Get list of known projects, sorted by last accessed."""
    config = get_global_config()
    projects = list(config.get("projects", {}).values())

    # Filter out projects that no longer exist
    valid_projects = []
    for proj in projects:
        proj_path = Path(proj["path"])
        if proj_path.exists() and (proj_path / ".1kh").exists():
            valid_projects.append(proj)

    # Sort by last accessed, most recent first
    valid_projects.sort(
        key=lambda p: p.get("last_accessed", ""),
        reverse=True,
    )

    return valid_projects


def get_last_active_project() -> Optional[dict]:
    """Get the last active project if it still exists."""
    config = get_global_config()
    last_path = config.get("last_active_project")

    if not last_path:
        return None

    proj_path = Path(last_path)
    if proj_path.exists() and (proj_path / ".1kh").exists():
        return config["projects"].get(last_path)

    return None


def remove_project(path: Path) -> None:
    """Remove a project from tracking (doesn't delete files)."""
    config = get_global_config()
    path_str = str(path.resolve())

    if path_str in config["projects"]:
        del config["projects"][path_str]

    if config.get("last_active_project") == path_str:
        config["last_active_project"] = None

    save_global_config(config)


def get_project_phase_description(phase: int) -> str:
    """Get human-readable description of a phase."""
    phases = {
        0: "Not started",
        1: "Grounding (directory setup)",
        2: "Listening (capturing input)",
        3: "Probing (clarifying questions)",
        4: "Structuring (organizing understanding)",
        5: "Committing (writing foundation docs)",
        6: "Connecting (API keys)",
        7: "Igniting (deploying loops)",
        8: "Running",
    }
    return phases.get(phase, f"Phase {phase}")
