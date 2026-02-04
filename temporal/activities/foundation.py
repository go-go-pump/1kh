"""
Foundation Activities - Read the core documents that guide the system.

These activities read the human-authored foundation documents:
- oracle.md: Values and hard boundaries
- north-star.md: Objectives and success metrics
- context.md: Resources and constraints
- seeds.json: Initial hypotheses to explore
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from temporalio import activity

# Logger for when running outside Temporal context
logger = logging.getLogger("1kh.foundation")


def _safe_log_info(msg: str):
    """Log info whether in activity context or not."""
    try:
        activity.logger.info(msg)
    except RuntimeError:
        logger.info(msg)


def _safe_log_warning(msg: str):
    """Log warning whether in activity context or not."""
    try:
        activity.logger.warning(msg)
    except RuntimeError:
        logger.warning(msg)


def _safe_log_error(msg: str):
    """Log error whether in activity context or not."""
    try:
        activity.logger.error(msg)
    except RuntimeError:
        logger.error(msg)


@dataclass
class FoundationContext:
    """Holds paths and state for foundation activities."""
    project_path: Path


@activity.defn
async def read_oracle(project_path: str) -> dict:
    """
    Read the oracle.md file and return structured data.

    Returns:
        dict with keys: values, never_do, always_do
    """
    _safe_log_info(f"Reading oracle from {project_path}")

    oracle_path = Path(project_path) / "oracle.md"
    if not oracle_path.exists():
        _safe_log_warning("oracle.md not found")
        return {"values": [], "never_do": [], "always_do": []}

    content = oracle_path.read_text()

    # Parse markdown sections
    result = {
        "values": [],
        "never_do": [],
        "always_do": [],
        "raw": content,
    }

    current_section = None
    for line in content.split("\n"):
        line = line.strip()

        if line.startswith("## Values"):
            current_section = "values"
        elif line.startswith("## We Will Never"):
            current_section = "never_do"
        elif line.startswith("## We Will Always"):
            current_section = "always_do"
        elif line.startswith("##"):
            current_section = None
        elif line.startswith("- ") and current_section:
            result[current_section].append(line[2:])

    return result


@activity.defn
async def read_north_star(project_path: str) -> dict:
    """
    Read the north-star.md file and return structured data.

    Returns:
        dict with keys: objectives, success_metrics, full_description
    """
    _safe_log_info(f"Reading north-star from {project_path}")

    ns_path = Path(project_path) / "north-star.md"
    if not ns_path.exists():
        _safe_log_warning("north-star.md not found")
        return {"objectives": [], "success_metrics": [], "full_description": ""}

    content = ns_path.read_text()

    result = {
        "objectives": [],
        "success_metrics": [],
        "full_description": "",
        "raw": content,
    }

    current_section = None
    description_lines = []

    for line in content.split("\n"):
        stripped = line.strip()

        if stripped.startswith("### Full Description"):
            current_section = "description"
        elif stripped.startswith("### Extracted Objectives"):
            current_section = "objectives"
            # Save accumulated description
            result["full_description"] = "\n".join(description_lines).strip()
        elif stripped.startswith("## Success Metrics"):
            current_section = "metrics"
        elif stripped.startswith("##") or stripped.startswith("###"):
            current_section = None
        elif current_section == "description":
            description_lines.append(line)
        elif stripped.startswith("- ") and current_section == "objectives":
            result["objectives"].append(stripped[2:])
        elif stripped.startswith("- ") and current_section == "metrics":
            result["success_metrics"].append(stripped[2:])

    return result


@activity.defn
async def read_context(project_path: str) -> dict:
    """
    Read the context.md file and return structured data.

    Returns:
        dict with keys: constraints, assets, skills, budget, time
    """
    _safe_log_info(f"Reading context from {project_path}")

    ctx_path = Path(project_path) / "context.md"
    if not ctx_path.exists():
        _safe_log_warning("context.md not found")
        return {"constraints": [], "assets": [], "skills": []}

    content = ctx_path.read_text()

    result = {
        "constraints": [],
        "assets": [],
        "skills": [],
        "budget_monthly": None,
        "budget_total": None,
        "time_weekly_hours": None,
        "raw": content,
    }

    current_section = None
    for line in content.split("\n"):
        stripped = line.strip()

        # Parse budget lines
        if stripped.startswith("**Monthly Budget:**"):
            try:
                result["budget_monthly"] = float(stripped.split("$")[1].strip())
            except (IndexError, ValueError):
                pass
        elif stripped.startswith("**Total Budget:**"):
            try:
                result["budget_total"] = float(stripped.split("$")[1].strip())
            except (IndexError, ValueError):
                pass
        elif stripped.startswith("**Time Available:**"):
            try:
                result["time_weekly_hours"] = float(stripped.split(":")[1].split("hours")[0].strip())
            except (IndexError, ValueError):
                pass

        # Track sections
        if stripped.startswith("## Existing Assets"):
            current_section = "assets"
        elif stripped.startswith("## Skills"):
            current_section = "skills"
        elif stripped.startswith("## Constraints"):
            current_section = "constraints"
        elif stripped.startswith("##"):
            current_section = None
        elif stripped.startswith("- ") and current_section:
            result[current_section].append(stripped[2:])

    return result


@activity.defn
async def read_seeds(project_path: str) -> list:
    """
    Read the seeds.json file and return the list of initial hypotheses.

    Returns:
        list of seed dictionaries
    """
    _safe_log_info(f"Reading seeds from {project_path}")

    seeds_path = Path(project_path) / ".1kh" / "seeds.json"
    if not seeds_path.exists():
        _safe_log_warning("seeds.json not found")
        return []

    try:
        return json.loads(seeds_path.read_text())
    except json.JSONDecodeError as e:
        _safe_log_error(f"Failed to parse seeds.json: {e}")
        return []
