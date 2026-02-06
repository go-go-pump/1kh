"""
Forecast Engine - Business simulation without real execution.

This module enables users to simulate their business trajectory:
- Preview journey, estimate costs/timeline, identify risks
- Run Monte Carlo simulations with different human behaviors
- Replay past forecasts with different inputs

Modes:
    | Mode     | Flag          | Claude    | Human      | Use Case                    |
    |----------|---------------|-----------|------------|-----------------------------|
    | Mock     | --mock        | Mocked    | Mocked     | Fast testing, no tokens     |
    | Live     | (default)     | Real API  | Simulated  | First run, captures trace   |
    | Replay   | --replay <id> | Cached    | Configurable | Re-run with different inputs |
    | Scenario | --runs N      | Cached    | Randomized | Monte Carlo distribution    |

Configurable Variables:
    - human_quality: perfect, good, mediocre, poor
    - human_delay_hours: 1, 4, 24, 72, 168
    - market_response: optimistic, realistic, pessimistic
    - execution_variance: 0.0 - 1.0
    - chaos_level: none, low, medium, high
    - human_selection: optimal, random, worst
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
import re
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any

logger = logging.getLogger("1kh.forecast")


# =============================================================================
# Foundation Context (Project Grounding)
# =============================================================================

@dataclass
class FoundationContext:
    """
    Parsed foundation documents for grounding simulations.

    Extracts key information from oracle.md, north-star.md, context.md
    to generate contextually relevant hypotheses and metrics.
    """
    # System classification
    system_type: Optional[str] = None  # "BUSINESS SYSTEM" or "USER SYSTEM"
    north_star_type: Optional[str] = None  # "REVENUE", "USERS", etc.
    utility_subtype: Optional[str] = None  # For USER systems: "MULTI_TENANT", etc.

    # Extracted objectives
    objectives: list[str] = field(default_factory=list)
    success_metrics: list[str] = field(default_factory=list)

    # Values and constraints
    values: list[str] = field(default_factory=list)
    never_do: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    # Raw descriptions for hypothesis generation
    project_description: str = ""
    primary_objective: str = ""

    @classmethod
    def load(cls, project_path: Path) -> "FoundationContext":
        """Load and parse foundation documents from project."""
        ctx = cls()

        # Try different foundation locations
        foundation_dirs = [
            project_path / "foundation",
            project_path,  # Some projects have docs in root
        ]

        for foundation_dir in foundation_dirs:
            if (foundation_dir / "north-star.md").exists():
                ctx._parse_north_star(foundation_dir / "north-star.md")
            if (foundation_dir / "oracle.md").exists():
                ctx._parse_oracle(foundation_dir / "oracle.md")
            if (foundation_dir / "context.md").exists():
                ctx._parse_context(foundation_dir / "context.md")

        return ctx

    def _parse_north_star(self, filepath: Path):
        """Parse north-star.md for objectives and system type."""
        try:
            content = filepath.read_text()

            # Extract system type
            match = re.search(r'\*\*System Type:\*\*\s*(.+)', content)
            if match:
                self.system_type = match.group(1).strip()

            # Extract north star type
            match = re.search(r'\*\*North Star Type:\*\*\s*(.+)', content)
            if match:
                self.north_star_type = match.group(1).strip()

            # Extract utility subtype for USER systems
            match = re.search(r'\*\*Utility Subtype:\*\*\s*(.+)', content)
            if match:
                self.utility_subtype = match.group(1).strip()

            # Extract primary objective - try multiple formats
            # Format 1: "## Primary Objective" with bullet points
            match = re.search(r'## Primary Objective\s*\n\n((?:- .+\n?)+)', content)
            if match:
                objectives_text = match.group(1)
                self.objectives = [
                    line.strip('- ').strip()
                    for line in objectives_text.strip().split('\n')
                    if line.strip().startswith('-')
                ]
                if self.objectives:
                    self.primary_objective = self.objectives[0][:200]
                    self.project_description = " ".join(self.objectives)[:1000]

            # Format 2: "### Extracted Objectives" (legacy)
            if not self.objectives:
                match = re.search(r'### Extracted Objectives\s*\n\n((?:- .+\n?)+)', content)
                if match:
                    objectives_text = match.group(1)
                    self.objectives = [
                        line.strip('- ').strip()
                        for line in objectives_text.strip().split('\n')
                        if line.strip().startswith('-')
                    ]

            # Format 3: "### Full Description" (legacy)
            if not self.project_description:
                match = re.search(r'### Full Description\s*\n\n(.+?)(?=\n###|\n## |$)', content, re.DOTALL)
                if match:
                    self.project_description = match.group(1).strip()[:1000]
                    self.primary_objective = self.project_description[:200]

            # Extract success metrics
            match = re.search(r'## Success Metrics\s*\n\n((?:- .+\n?)+)', content)
            if match:
                metrics_text = match.group(1)
                self.success_metrics = [
                    line.strip('- ').strip()
                    for line in metrics_text.strip().split('\n')
                    if line.strip().startswith('-')
                ]

        except Exception as e:
            logger.warning(f"Failed to parse north-star.md: {e}")

    def _parse_oracle(self, filepath: Path):
        """Parse oracle.md for values and constraints."""
        try:
            content = filepath.read_text()

            # Extract values
            match = re.search(r'## Values\s*\n\n((?:- .+\n?)+)', content)
            if match:
                values_text = match.group(1)
                self.values = [
                    line.strip('- ').strip()
                    for line in values_text.strip().split('\n')
                    if line.strip().startswith('-')
                ]

            # Extract "never do"
            match = re.search(r'## We Will Never\s*\n\n((?:- .+\n?)+)', content)
            if match:
                never_text = match.group(1)
                self.never_do = [
                    line.strip('- ').strip()
                    for line in never_text.strip().split('\n')
                    if line.strip().startswith('-')
                ]

        except Exception as e:
            logger.warning(f"Failed to parse oracle.md: {e}")

    def _parse_context(self, filepath: Path):
        """Parse context.md for constraints."""
        try:
            content = filepath.read_text()

            # Extract constraints
            match = re.search(r'## Constraints\s*\n\n((?:- .+\n?)+)', content)
            if match:
                constraints_text = match.group(1)
                self.constraints = [
                    line.strip('- ').strip()
                    for line in constraints_text.strip().split('\n')
                    if line.strip().startswith('-')
                ]

        except Exception as e:
            logger.warning(f"Failed to parse context.md: {e}")

    def is_business_system(self) -> bool:
        """Check if this is a business system."""
        return self.system_type and "BUSINESS" in self.system_type.upper()

    def is_user_system(self) -> bool:
        """Check if this is a user/utility system."""
        return self.system_type and "USER" in self.system_type.upper()

    def get_mock_hypotheses(self, cycle: int, max_count: int = 3) -> list[dict]:
        """
        Generate mock hypotheses grounded in actual project objectives.

        Returns hypotheses that relate to the real foundation docs.
        Priority:
        1. Success metrics (specific features to build)
        2. Primary objectives (high-level goals)
        3. Generic system-appropriate hypotheses (fallback)
        """
        hypotheses = []
        used_descriptions = set()

        # Priority 1: Use success metrics as hypotheses (these are concrete features)
        if self.success_metrics:
            # Rotate through metrics based on cycle
            start_idx = (cycle * max_count) % len(self.success_metrics)
            for i in range(max_count):
                idx = (start_idx + i) % len(self.success_metrics)
                metric = self.success_metrics[idx]

                # Skip if we've used this description
                if metric in used_descriptions:
                    continue
                used_descriptions.add(metric)

                # Convert metric to hypothesis description
                if metric.lower().startswith("successfully "):
                    desc = metric[13:]  # Remove "Successfully "
                else:
                    desc = metric

                hyp = {
                    "id": f"hyp-{cycle:03d}-{i+1}",
                    "description": f"Implement: {desc[:80]}",
                    "feasibility": random.uniform(0.65, 0.95),
                    "north_star_alignment": random.uniform(0.75, 0.99),
                    "estimated_effort": random.choice(["small", "medium", "large"]),
                    "category": "feature",
                    "source": "success_metric",
                }
                hypotheses.append(hyp)

        # Priority 2: Use objectives if we need more hypotheses
        if len(hypotheses) < max_count and self.objectives:
            for i, objective in enumerate(self.objectives):
                if len(hypotheses) >= max_count:
                    break
                if objective in used_descriptions:
                    continue
                used_descriptions.add(objective)

                hyp = {
                    "id": f"hyp-{cycle:03d}-{len(hypotheses)+1}",
                    "description": f"Progress: {objective[:80]}",
                    "feasibility": random.uniform(0.6, 0.90),
                    "north_star_alignment": random.uniform(0.8, 0.99),
                    "estimated_effort": random.choice(["medium", "large"]),
                    "category": "objective",
                    "source": "foundation",
                }
                hypotheses.append(hyp)

        # Priority 3: Fall back to system-appropriate generic hypotheses
        if len(hypotheses) < max_count:
            if self.is_user_system():
                descriptions = [
                    "Add comprehensive error handling and recovery",
                    "Implement health checks and monitoring",
                    "Set up automated testing pipeline",
                    "Add request rate limiting and throttling",
                    "Implement graceful degradation",
                    "Add metrics and observability",
                    "Create API documentation",
                    "Implement caching layer",
                ]
            else:
                descriptions = [
                    "Acquire initial customers through outreach",
                    "Set up payment processing integration",
                    "Build landing page with clear value prop",
                    "Create user onboarding flow",
                    "Implement customer feedback collection",
                    "Set up analytics and conversion tracking",
                    "Create email nurture sequence",
                    "Build referral mechanism",
                ]

            # Rotate through descriptions based on cycle
            start_idx = (cycle * max_count) % len(descriptions)
            for i in range(len(descriptions)):
                if len(hypotheses) >= max_count:
                    break
                idx = (start_idx + i) % len(descriptions)
                desc = descriptions[idx]
                if desc in used_descriptions:
                    continue
                used_descriptions.add(desc)

                hyp = {
                    "id": f"hyp-{cycle:03d}-{len(hypotheses)+1}",
                    "description": desc,
                    "feasibility": random.uniform(0.5, 0.90),
                    "north_star_alignment": random.uniform(0.6, 0.95),
                    "estimated_effort": random.choice(["small", "medium", "large"]),
                    "category": "general",
                    "source": "default",
                }
                hypotheses.append(hyp)

        return hypotheses

    def get_metric_types(self) -> dict:
        """
        Get appropriate metric types for this system.

        Returns dict with metric names and base values.
        """
        if self.is_user_system():
            # Infrastructure/utility metrics
            return {
                "uptime": {"base": 99.0, "unit": "%", "target": 99.9},
                "latency_p95": {"base": 200, "unit": "ms", "target": 100},
                "error_rate": {"base": 2.0, "unit": "%", "target": 0.1},
                "requests_handled": {"base": 1000, "unit": "req/day", "growth": 1.2},
                "success_rate": {"base": 95.0, "unit": "%", "target": 99.5},
            }
        else:
            # Business metrics
            return {
                "revenue": {"base": 100, "unit": "$", "growth": 1.15},
                "signups": {"base": 10, "unit": "users", "growth": 1.1},
                "conversions": {"base": 1, "unit": "customers", "growth": 1.1},
                "page_views": {"base": 100, "unit": "views", "growth": 1.2},
            }


# =============================================================================
# Forecast Variables (Configurable Parameters)
# =============================================================================

@dataclass
class ForecastVariables:
    """Configurable simulation parameters."""
    # Human behavior
    human_quality: str = "good"  # perfect, good, mediocre, poor
    human_delay_hours: int = 4   # 1, 4, 24, 72, 168
    human_selection: str = "optimal"  # optimal, random, worst

    # Market conditions
    market_response: str = "realistic"  # optimistic, realistic, pessimistic

    # Execution
    execution_variance: float = 0.0  # 0.0 - 1.0
    chaos_level: str = "none"  # none, low, medium, high

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ForecastVariables":
        return cls(**data)

    def get_human_approve_rate(self) -> float:
        """Convert human_quality to approval rate."""
        rates = {
            "perfect": 1.0,
            "good": 0.9,
            "mediocre": 0.7,
            "poor": 0.5,
        }
        return rates.get(self.human_quality, 0.9)

    def get_market_multiplier(self) -> float:
        """Convert market_response to metric multiplier."""
        multipliers = {
            "optimistic": 1.3,
            "realistic": 1.0,
            "pessimistic": 0.7,
        }
        return multipliers.get(self.market_response, 1.0)

    def get_chaos_failure_rate(self) -> float:
        """Convert chaos_level to additional failure rate."""
        rates = {
            "none": 0.0,
            "low": 0.1,
            "medium": 0.2,
            "high": 0.4,
        }
        return rates.get(self.chaos_level, 0.0)


# =============================================================================
# Forecast Manifest (Trace Metadata)
# =============================================================================

@dataclass
class ForecastManifest:
    """Metadata for a forecast trace."""
    trace_id: str
    created_at: str
    mode: str  # "mock", "live", "replay"
    variables: dict
    foundation_hash: str  # Hash of foundation docs for drift detection
    foundation_files: dict[str, str]  # filename -> hash
    cycles_completed: int = 0
    outcome: Optional[dict] = None
    parent_trace_id: Optional[str] = None  # For replays

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ForecastManifest":
        return cls(**data)

    @classmethod
    def create(
        cls,
        mode: str,
        variables: ForecastVariables,
        foundation_hash: str,
        foundation_files: dict[str, str],
        parent_trace_id: Optional[str] = None,
    ) -> "ForecastManifest":
        """Create a new manifest."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        trace_id = f"trace_{timestamp}"
        return cls(
            trace_id=trace_id,
            created_at=datetime.utcnow().isoformat(),
            mode=mode,
            variables=variables.to_dict(),
            foundation_hash=foundation_hash,
            foundation_files=foundation_files,
            parent_trace_id=parent_trace_id,
        )


# =============================================================================
# Forecast Outcome (Final Results)
# =============================================================================

@dataclass
class ForecastOutcome:
    """Final results of a forecast run."""
    target_reached: bool
    cycles_completed: int
    final_revenue: float  # For BIZ systems: revenue, for USER: features completed
    target_revenue: float  # For BIZ systems: revenue target, for USER: total features
    time_estimate: str  # "4-6 months"
    estimated_api_cost: float
    human_decisions_required: int
    risk_level: str  # "low", "medium", "high"
    success_rate: float  # 0.0 - 1.0
    progress_pct: float
    total_hypotheses: int = 0
    total_tasks: int = 0
    total_failures: int = 0
    simulated_days: int = 0
    # System type for display purposes
    system_type: str = "BUSINESS SYSTEM"
    north_star_type: str = "REVENUE"
    primary_metric_label: str = "Revenue"
    primary_metric_unit: str = "$"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ForecastOutcome":
        return cls(**data)


# =============================================================================
# Sensitivity Analysis Results
# =============================================================================

@dataclass
class SensitivityResult:
    """Results from varying one variable in sensitivity analysis."""
    variable_name: str
    variable_values: list[Any]
    outcomes: list[dict]  # Aggregated outcome per value
    baseline_value: Any

    # Computed impact metrics
    success_rate_range: tuple[float, float]  # (min, max)
    success_rate_delta: float                # max - min
    cycles_range: tuple[int, int]
    cycles_delta: int

    def sensitivity_score(self) -> float:
        """0-1 score for how sensitive outcomes are to this variable."""
        return self.success_rate_delta

    def to_dict(self) -> dict:
        return {
            "variable_name": self.variable_name,
            "variable_values": self.variable_values,
            "outcomes": self.outcomes,
            "baseline_value": self.baseline_value,
            "success_rate_range": list(self.success_rate_range),
            "success_rate_delta": self.success_rate_delta,
            "cycles_range": list(self.cycles_range),
            "cycles_delta": self.cycles_delta,
        }


@dataclass
class InteractionResult:
    """Results from two-variable interaction analysis."""
    var1_name: str
    var1_values: list[Any]
    var2_name: str
    var2_values: list[Any]

    # 2D grid of outcomes [var2_idx][var1_idx]
    outcomes_grid: list[list[dict]]

    # Interaction analysis
    interaction_strength: float  # 0 = additive, 1 = strong interaction
    has_interaction: bool

    def to_dict(self) -> dict:
        return {
            "var1_name": self.var1_name,
            "var1_values": self.var1_values,
            "var2_name": self.var2_name,
            "var2_values": self.var2_values,
            "outcomes_grid": self.outcomes_grid,
            "interaction_strength": self.interaction_strength,
            "has_interaction": self.has_interaction,
        }


# =============================================================================
# Trace Manager
# =============================================================================

class TraceManager:
    """
    Manages forecast traces on disk.

    Trace Structure:
        .1kh/forecasts/
        ├── trace_20260205_143000/
        │   ├── manifest.json
        │   ├── foundation_snapshot/
        │   │   ├── oracle.md
        │   │   ├── north-star.md
        │   │   └── context.md
        │   ├── claude_cache/
        │   │   ├── index.json
        │   │   └── cycle_001_imagination_001.json
        │   ├── human_decisions/
        │   ├── events.jsonl
        │   └── outcome.json
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.forecasts_dir = self.project_path / ".1kh" / "forecasts"
        self.forecasts_dir.mkdir(parents=True, exist_ok=True)

    def create_trace(
        self,
        mode: str,
        variables: ForecastVariables,
        parent_trace_id: Optional[str] = None,
    ) -> Path:
        """
        Create a new forecast trace.

        Returns: Path to trace directory
        """
        # Compute foundation hash
        foundation_hash, foundation_files = self._hash_foundation()

        # Create manifest
        manifest = ForecastManifest.create(
            mode=mode,
            variables=variables,
            foundation_hash=foundation_hash,
            foundation_files=foundation_files,
            parent_trace_id=parent_trace_id,
        )

        # Create trace directory
        trace_dir = self.forecasts_dir / manifest.trace_id
        trace_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (trace_dir / "claude_cache").mkdir(exist_ok=True)
        (trace_dir / "human_decisions").mkdir(exist_ok=True)
        (trace_dir / "foundation_snapshot").mkdir(exist_ok=True)

        # Snapshot foundation docs
        self._snapshot_foundation(trace_dir / "foundation_snapshot")

        # Write manifest
        manifest_path = trace_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2))

        logger.info(f"Created forecast trace: {manifest.trace_id}")
        return trace_dir

    def get_trace(self, trace_id: str) -> Optional[Path]:
        """Get trace directory by ID."""
        trace_dir = self.forecasts_dir / trace_id
        if trace_dir.exists():
            return trace_dir
        return None

    def get_manifest(self, trace_id: str) -> Optional[ForecastManifest]:
        """Get manifest for a trace."""
        trace_dir = self.get_trace(trace_id)
        if not trace_dir:
            return None

        manifest_path = trace_dir / "manifest.json"
        if not manifest_path.exists():
            return None

        try:
            data = json.loads(manifest_path.read_text())
            return ForecastManifest.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to load manifest: {e}")
            return None

    def update_manifest(self, trace_id: str, updates: dict):
        """Update manifest fields."""
        trace_dir = self.get_trace(trace_id)
        if not trace_dir:
            return

        manifest_path = trace_dir / "manifest.json"
        if not manifest_path.exists():
            return

        data = json.loads(manifest_path.read_text())
        data.update(updates)
        manifest_path.write_text(json.dumps(data, indent=2))

    def save_outcome(self, trace_id: str, outcome: ForecastOutcome):
        """Save outcome to trace."""
        trace_dir = self.get_trace(trace_id)
        if not trace_dir:
            return

        outcome_path = trace_dir / "outcome.json"
        outcome_path.write_text(json.dumps(outcome.to_dict(), indent=2))

        # Also update manifest
        self.update_manifest(trace_id, {
            "outcome": outcome.to_dict(),
            "cycles_completed": outcome.cycles_completed,
        })

    def list_traces(self) -> list[dict]:
        """List all traces with summary info."""
        traces = []
        for trace_dir in sorted(self.forecasts_dir.iterdir(), reverse=True):
            if not trace_dir.is_dir():
                continue

            manifest = self.get_manifest(trace_dir.name)
            if not manifest:
                continue

            # Get outcome if available
            outcome_path = trace_dir / "outcome.json"
            outcome = None
            if outcome_path.exists():
                try:
                    outcome = json.loads(outcome_path.read_text())
                except json.JSONDecodeError:
                    pass

            traces.append({
                "trace_id": manifest.trace_id,
                "created_at": manifest.created_at,
                "mode": manifest.mode,
                "cycles_completed": manifest.cycles_completed,
                "outcome": outcome,
                "variables": manifest.variables,
            })

        return traces

    def check_foundation_drift(self, trace_id: str) -> list[str]:
        """
        Check if foundation has changed since trace was created.

        Returns: List of changed files (empty if no drift)
        """
        manifest = self.get_manifest(trace_id)
        if not manifest:
            return ["manifest_not_found"]

        current_hash, current_files = self._hash_foundation()

        changed = []
        for filename, old_hash in manifest.foundation_files.items():
            new_hash = current_files.get(filename, "missing")
            if old_hash != new_hash:
                changed.append(filename)

        # Check for new files
        for filename in current_files:
            if filename not in manifest.foundation_files:
                changed.append(f"{filename} (new)")

        return changed

    def delete_trace(self, trace_id: str) -> bool:
        """Delete a trace."""
        trace_dir = self.get_trace(trace_id)
        if trace_dir and trace_dir.exists():
            shutil.rmtree(trace_dir)
            logger.info(f"Deleted trace: {trace_id}")
            return True
        return False

    def _hash_foundation(self) -> tuple[str, dict[str, str]]:
        """Compute hash of foundation documents."""
        foundation_dir = self.project_path / "foundation"
        files_to_hash = ["oracle.md", "north-star.md", "context.md"]

        file_hashes = {}
        combined = ""

        for filename in files_to_hash:
            filepath = foundation_dir / filename
            if filepath.exists():
                content = filepath.read_text()
                file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                file_hashes[filename] = file_hash
                combined += file_hash

        overall_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]
        return overall_hash, file_hashes

    def _snapshot_foundation(self, snapshot_dir: Path):
        """Copy foundation docs to snapshot directory."""
        foundation_dir = self.project_path / "foundation"
        files_to_copy = ["oracle.md", "north-star.md", "context.md"]

        for filename in files_to_copy:
            src = foundation_dir / filename
            if src.exists():
                dst = snapshot_dir / filename
                shutil.copy2(src, dst)


# =============================================================================
# Simulated Human Responder
# =============================================================================

class SimulatedHumanResponder:
    """
    Simulates human responses based on ForecastVariables.

    Used in forecast mode to simulate human decisions without prompts.
    """

    def __init__(self, variables: ForecastVariables, seed: int = None):
        self.variables = variables
        self.rng = random.Random(seed)
        self.decisions_made = 0
        self.decisions_log: list[dict] = []

    def request_decision(
        self,
        escalation_type: str,
        summary: str,
        options: list[str],
        context: dict,
    ) -> dict:
        """Simulate a human decision."""
        self.decisions_made += 1

        # Determine action based on human_quality
        approve_rate = self.variables.get_human_approve_rate()

        if self.rng.random() < approve_rate:
            # Select option based on human_selection
            if self.variables.human_selection == "optimal":
                action = options[0] if options else "approve"
            elif self.variables.human_selection == "worst":
                action = options[-1] if options else "reject"
            else:  # random
                action = self.rng.choice(options) if options else "approve"
        else:
            action = "reject"

        decision = {"action": action, "feedback": f"Simulated: {action}"}

        # Log the decision
        self.decisions_log.append({
            "decision_number": self.decisions_made,
            "escalation_type": escalation_type,
            "summary": summary[:100],
            "options": options,
            "result": decision,
        })

        return decision

    def request_approval(self, summary: str, details: dict) -> bool:
        """Simulate approval request."""
        self.decisions_made += 1
        approve_rate = self.variables.get_human_approve_rate()
        approved = self.rng.random() < approve_rate

        self.decisions_log.append({
            "decision_number": self.decisions_made,
            "escalation_type": "approval_request",
            "summary": summary[:100],
            "result": {"approved": approved},
        })

        return approved

    def save_decisions(self, output_dir: Path):
        """Save decisions log to file."""
        output_path = output_dir / "decisions.json"
        output_path.write_text(json.dumps(self.decisions_log, indent=2))


# =============================================================================
# Simulated Executor
# =============================================================================

class SimulatedExecutor:
    """
    Executor that simulates task outcomes based on ForecastVariables.

    Applies market conditions, chaos, and foundation-appropriate metrics.
    """

    def __init__(
        self,
        project_path: Path,
        dashboard: Any,
        variables: ForecastVariables,
        seed: int = None,
        foundation: Optional[FoundationContext] = None,
    ):
        self.project_path = project_path
        self.dashboard = dashboard
        self.variables = variables
        self.foundation = foundation
        self.rng = random.Random(seed)
        self.execution_count = 0
        self.successes = 0

    def execute(self, task: dict, hypothesis: dict = None):
        """Execute task with simulated outcomes."""
        from core.runner import ExecutionResult
        from core.dashboard import EventType

        self.execution_count += 1
        task_id = task.get("id", f"task-{self.execution_count}")
        hypothesis_id = hypothesis.get("id") if hypothesis else None

        # Log start
        self.dashboard.log_event(
            EventType.TASK_STARTED,
            task_id=task_id,
            hypothesis_id=hypothesis_id,
        )

        # Determine success/failure
        base_failure_rate = 0.15
        chaos_failure = self.variables.get_chaos_failure_rate()
        variance_failure = self.variables.execution_variance * 0.2
        total_failure_rate = base_failure_rate + chaos_failure + variance_failure

        success = self.rng.random() > total_failure_rate

        if success:
            self.successes += 1
            return self._generate_success(task, task_id, hypothesis_id)
        else:
            return self._generate_failure(task, task_id, hypothesis_id)

    def _generate_success(self, task: dict, task_id: str, hypothesis_id: str):
        """Generate successful outcome with foundation-appropriate metrics."""
        from core.runner import ExecutionResult
        from core.dashboard import EventType

        # Base metrics with market multiplier
        multiplier = self.variables.get_market_multiplier()
        growth_mult = 1.1 ** (self.successes - 1)  # Growth over time
        noise = 1 + self.rng.uniform(-0.3, 0.3)

        metrics_delta = {}

        # Use foundation-appropriate metrics
        if self.foundation and self.foundation.is_user_system():
            # USER SYSTEM: Infrastructure metrics
            # Improve uptime, reduce latency, handle more requests
            uptime_improvement = 0.1 * multiplier * noise  # Small improvements
            latency_reduction = 5 * multiplier * noise  # ms reduction
            requests_increase = int(100 * multiplier * growth_mult * noise)

            metrics_delta = {
                "uptime_improvement": uptime_improvement,
                "latency_reduction": latency_reduction,
                "requests_handled": requests_increase,
            }

            # Log infrastructure metrics
            self.dashboard.log_event(
                EventType.UPTIME_CHECK,
                value=1,  # Success
                task_id=task_id,
                hypothesis_id=hypothesis_id,
                metadata={"uptime_improvement": uptime_improvement},
            )
            self.dashboard.log_event(
                EventType.LATENCY_SAMPLE,
                value=max(50, 200 - latency_reduction * self.successes),  # Improving latency
                task_id=task_id,
                hypothesis_id=hypothesis_id,
            )

            # Still track some revenue for north star (services can bill)
            revenue = 50 * multiplier * growth_mult * noise
            metrics_delta["revenue"] = revenue
            self.dashboard.log_event(EventType.REVENUE, value=revenue, task_id=task_id, hypothesis_id=hypothesis_id)

        else:
            # BUSINESS SYSTEM: Business metrics
            base_signups = 10 * multiplier * growth_mult
            base_revenue = 100 * multiplier * growth_mult

            signups = int(base_signups * noise)
            revenue = base_revenue * noise

            metrics_delta = {"signups": signups, "revenue": revenue}

            # Log business metrics
            self.dashboard.log_event(EventType.SIGNUP, value=signups, task_id=task_id, hypothesis_id=hypothesis_id)
            self.dashboard.log_event(EventType.REVENUE, value=revenue, task_id=task_id, hypothesis_id=hypothesis_id)

        self.dashboard.log_event(EventType.TASK_COMPLETED, task_id=task_id, hypothesis_id=hypothesis_id)

        return ExecutionResult(
            success=True,
            task_id=task_id,
            hypothesis_id=hypothesis_id,
            result_text=f"Task {task_id} completed",
            duration_seconds=60,
            metrics_delta=metrics_delta,
        )

    def _generate_failure(self, task: dict, task_id: str, hypothesis_id: str):
        """Generate failure outcome with foundation-appropriate errors."""
        from core.runner import ExecutionResult
        from core.dashboard import EventType

        # Use foundation-appropriate error messages
        if self.foundation and self.foundation.is_user_system():
            errors = [
                "Service timeout exceeded",
                "Upstream dependency unavailable",
                "Resource limit reached",
                "Integration test failed",
                "Deployment rollback triggered",
            ]
        else:
            errors = [
                "Customer acquisition blocked",
                "Payment processing failed",
                "Conversion funnel issue",
                "Third-party API rate limited",
            ]

        error = self.rng.choice(errors)

        self.dashboard.log_event(
            EventType.TASK_FAILED,
            task_id=task_id,
            hypothesis_id=hypothesis_id,
            metadata={"error": error},
        )

        return ExecutionResult(
            success=False,
            task_id=task_id,
            hypothesis_id=hypothesis_id,
            result_text=f"Task {task_id} failed: {error}",
            errors=[error],
            needs_human=False,
        )


# =============================================================================
# Forecast Runner
# =============================================================================

class ForecastRunner:
    """
    Runs forecast simulations.

    Uses CycleRunner internally via composition, not inheritance.
    Operates silently (no interactive output) for fast batch processing.
    """

    def __init__(
        self,
        project_path: Path,
        mode: str,  # "mock", "live", "replay"
        variables: ForecastVariables,
        max_cycles: int = 50,
        trace_id: Optional[str] = None,  # For replay mode
        seed: int = None,
        on_cycle_complete: Optional[Callable[[int, dict], None]] = None,
        foundation: Optional[FoundationContext] = None,
    ):
        self.project_path = Path(project_path)
        self.mode = mode
        self.variables = variables
        self.max_cycles = max_cycles
        self.trace_id = trace_id
        self.seed = seed or random.randint(0, 1000000)
        self.on_cycle_complete = on_cycle_complete

        # Load foundation context for grounded simulation
        self.foundation = foundation or FoundationContext.load(project_path)

        # Initialize trace manager
        self.trace_manager = TraceManager(project_path)

        # State
        self.trace_dir: Optional[Path] = None
        self.human_responder: Optional[SimulatedHumanResponder] = None
        self.api_cost_estimate = 0.0

    async def run(self) -> ForecastOutcome:
        """
        Run the forecast simulation.

        Returns: ForecastOutcome with final results
        """
        from core.runner import CycleRunner, RunnerConfig, RunnerMode, Dependencies
        from core.dashboard import Dashboard
        from core.claude_cache import CachedClaudeClient, CacheMode, ClaudeCache

        # Create or load trace
        if self.mode == "replay" and self.trace_id:
            self.trace_dir = self.trace_manager.get_trace(self.trace_id)
            if not self.trace_dir:
                raise ValueError(f"Trace not found: {self.trace_id}")

            # Check for foundation drift
            drift = self.trace_manager.check_foundation_drift(self.trace_id)
            if drift:
                logger.warning(f"Foundation drift detected: {drift}")
        else:
            self.trace_dir = self.trace_manager.create_trace(
                mode=self.mode,
                variables=self.variables,
            )
            self.trace_id = self.trace_dir.name

        # Set up components based on mode
        dashboard = Dashboard(self.project_path)
        dashboard.event_log.log_file = self.trace_dir / "events.jsonl"  # Write to trace

        # Set north star based on foundation context (system type)
        if self.foundation.is_user_system():
            # USER SYSTEM: Track features completed or service metrics
            num_metrics = len(self.foundation.success_metrics) or 8
            dashboard.set_north_star(f"{num_metrics} features", target_value=num_metrics)
        else:
            # BUSINESS SYSTEM: Track revenue
            dashboard.set_north_star("$1M ARR", target_value=1_000_000)

        # Create simulated human responder
        self.human_responder = SimulatedHumanResponder(self.variables, seed=self.seed)

        # Set up Claude client based on mode
        if self.mode == "mock":
            cache_mode = CacheMode.MOCK
            claude_client = CachedClaudeClient(
                cache_dir=self.trace_dir / "claude_cache",
                mode=cache_mode,
            )
        elif self.mode == "live":
            cache_mode = CacheMode.CAPTURE
            claude_client = CachedClaudeClient(
                cache_dir=self.trace_dir / "claude_cache",
                mode=cache_mode,
            )
        else:  # replay
            cache_mode = CacheMode.REPLAY
            claude_client = CachedClaudeClient(
                cache_dir=self.trace_dir / "claude_cache",
                mode=cache_mode,
            )

        # Create executor with foundation context
        executor = SimulatedExecutor(
            project_path=self.project_path,
            dashboard=dashboard,
            variables=self.variables,
            seed=self.seed,
            foundation=self.foundation,
        )

        # Create runner config
        config = RunnerConfig(
            mode=RunnerMode.DEMO,  # Use demo mode for mock behavior
            project_path=self.project_path,
            max_cycles=self.max_cycles,
            demo_speed=100,  # Fast
            demo_delay_base=0,  # No delays
        )

        # Create dependencies
        deps = Dependencies(
            claude_client=claude_client,
            human_responder=self.human_responder,
            executor=executor,
            dashboard=dashboard,
        )

        # Create and run the cycle runner
        runner = CycleRunner(config, deps)
        runner.clear_run_state()  # Start fresh

        # Pass foundation context for grounded mock hypotheses
        runner._foundation = self.foundation

        # Run cycles
        summary = await runner.run()

        # Calculate API cost estimate
        self.api_cost_estimate = claude_client.get_usage_stats().get("estimated_cost", 0.0)

        # Build outcome
        outcome = self._build_outcome(summary, runner)

        # Save outcome
        self.trace_manager.save_outcome(self.trace_id, outcome)

        # Save human decisions
        if self.human_responder:
            self.human_responder.save_decisions(self.trace_dir / "human_decisions")

        return outcome

    def _build_outcome(self, summary: dict, runner) -> ForecastOutcome:
        """Build ForecastOutcome from runner summary."""
        # Determine risk level
        success_rate = summary.get("success_rate", 0.5)
        if success_rate >= 0.8:
            risk_level = "low"
        elif success_rate >= 0.6:
            risk_level = "medium"
        else:
            risk_level = "high"

        # Time estimate based on cycles and days_per_cycle
        simulated_days = summary.get("simulated_days", 0)
        months = simulated_days / 30
        if months < 2:
            time_estimate = f"{int(simulated_days / 7)}-{int(simulated_days / 7) + 2} weeks"
        elif months < 12:
            time_estimate = f"{int(months)}-{int(months) + 2} months"
        else:
            time_estimate = f"{int(months / 12)}-{int(months / 12) + 1} years"

        # Determine metric labels based on system type
        if self.foundation.is_user_system():
            system_type = "USER SYSTEM"
            north_star_type = self.foundation.north_star_type or "UTILITY"
            primary_metric_label = "Features Completed"
            primary_metric_unit = ""
            # For USER systems, use feature count as "revenue" metric
            num_features = len(self.foundation.success_metrics) or 8
            final_value = summary.get("tasks_total", 0)  # Features completed
            target_value = num_features
        else:
            system_type = "BUSINESS SYSTEM"
            north_star_type = self.foundation.north_star_type or "REVENUE"
            primary_metric_label = "Revenue"
            primary_metric_unit = "$"
            final_value = summary.get("final_revenue", 0)
            target_value = summary.get("target_revenue", 1_000_000)

        # Calculate target_reached based on actual values (not summary which may be wrong)
        target_reached = final_value >= target_value if target_value > 0 else False

        # Calculate progress percentage
        if target_value > 0:
            progress_pct = min(100.0, (final_value / target_value) * 100)
        else:
            progress_pct = summary.get("progress_pct", 0)

        return ForecastOutcome(
            target_reached=target_reached,
            cycles_completed=summary.get("cycles_completed", 0),
            final_revenue=final_value,
            target_revenue=target_value,
            time_estimate=time_estimate,
            estimated_api_cost=self.api_cost_estimate,
            human_decisions_required=self.human_responder.decisions_made if self.human_responder else 0,
            risk_level=risk_level,
            success_rate=success_rate,
            progress_pct=progress_pct,
            total_hypotheses=summary.get("hypotheses_total", 0),
            total_tasks=summary.get("tasks_total", 0),
            total_failures=summary.get("failures", 0),
            simulated_days=simulated_days,
            system_type=system_type,
            north_star_type=north_star_type,
            primary_metric_label=primary_metric_label,
            primary_metric_unit=primary_metric_unit,
        )


# =============================================================================
# Scenario Runner (Monte Carlo)
# =============================================================================

class ScenarioRunner:
    """
    Runs multiple simulations with randomization for Monte Carlo analysis.

    Aggregates results to show distribution of outcomes.
    """

    def __init__(
        self,
        project_path: Path,
        variables: ForecastVariables,
        num_runs: int = 100,
        max_cycles: int = 50,
        trace_id: Optional[str] = None,  # Use cached responses from this trace
        on_run_complete: Optional[Callable[[int, ForecastOutcome], None]] = None,
        foundation: Optional[FoundationContext] = None,
    ):
        self.project_path = Path(project_path)
        self.variables = variables
        self.num_runs = num_runs
        self.max_cycles = max_cycles
        self.trace_id = trace_id
        self.on_run_complete = on_run_complete
        self.foundation = foundation or FoundationContext.load(project_path)

    async def run(self) -> dict:
        """
        Run multiple simulations.

        Returns: Aggregated statistics
        """
        outcomes: list[ForecastOutcome] = []

        for i in range(self.num_runs):
            seed = random.randint(0, 1000000)

            # Randomize some variables for Monte Carlo
            varied_vars = ForecastVariables(
                human_quality=random.choice(["perfect", "good", "mediocre"]),
                human_delay_hours=random.choice([1, 4, 24]),
                human_selection=random.choice(["optimal", "random"]),
                market_response=random.choice(["optimistic", "realistic", "pessimistic"]),
                execution_variance=random.uniform(0, 0.3),
                chaos_level=random.choice(["none", "low"]),
            )

            runner = ForecastRunner(
                project_path=self.project_path,
                mode="mock" if not self.trace_id else "replay",
                variables=varied_vars,
                max_cycles=self.max_cycles,
                trace_id=self.trace_id,
                seed=seed,
                foundation=self.foundation,
            )

            try:
                outcome = await runner.run()
                outcomes.append(outcome)

                if self.on_run_complete:
                    self.on_run_complete(i + 1, outcome)
            except Exception as e:
                logger.warning(f"Run {i+1} failed: {e}")

        return self._aggregate_results(outcomes)

    def _aggregate_results(self, outcomes: list[ForecastOutcome]) -> dict:
        """Aggregate results from all runs."""
        if not outcomes:
            return {"error": "No successful runs"}

        # Success rate
        successes = sum(1 for o in outcomes if o.target_reached)
        success_rate = successes / len(outcomes)

        # Cycles distribution
        cycles = [o.cycles_completed for o in outcomes]
        avg_cycles = sum(cycles) / len(cycles)
        min_cycles = min(cycles)
        max_cycles = max(cycles)

        # Revenue distribution
        revenues = [o.final_revenue for o in outcomes]
        avg_revenue = sum(revenues) / len(revenues)

        # Time estimate (mode/median)
        times = [o.simulated_days for o in outcomes]
        median_days = sorted(times)[len(times) // 2]

        return {
            "num_runs": len(outcomes),
            "success_rate": success_rate,
            "successes": successes,
            "failures": len(outcomes) - successes,
            "cycles": {
                "average": avg_cycles,
                "min": min_cycles,
                "max": max_cycles,
            },
            "revenue": {
                "average": avg_revenue,
                "min": min(revenues),
                "max": max(revenues),
            },
            "time": {
                "median_days": median_days,
                "estimate": f"{int(median_days / 30)}-{int(median_days / 30) + 2} months",
            },
            "risk_distribution": {
                "low": sum(1 for o in outcomes if o.risk_level == "low"),
                "medium": sum(1 for o in outcomes if o.risk_level == "medium"),
                "high": sum(1 for o in outcomes if o.risk_level == "high"),
            },
        }


# =============================================================================
# Idea Templates for Exploration
# =============================================================================

# Templates for generating diverse business/service ideas
IDEA_TEMPLATES = {
    "USER": [
        # Infrastructure
        {"name": "API Gateway", "subtype": "GATEWAY", "description": "Unified API gateway for microservices", "metrics": ["Route requests to services", "Handle authentication", "Rate limiting", "Request logging"]},
        {"name": "Auth Service", "subtype": "AUTHENTICATION", "description": "Centralized authentication and authorization", "metrics": ["User login/logout", "OAuth integration", "Session management", "Role-based access"]},
        {"name": "Message Queue", "subtype": "MESSAGE_QUEUE", "description": "Async message processing system", "metrics": ["Publish messages", "Subscribe to topics", "Dead letter handling", "Message replay"]},
        {"name": "Cache Layer", "subtype": "CACHE", "description": "Distributed caching service", "metrics": ["Get/set operations", "TTL management", "Cache invalidation", "Cluster sync"]},
        {"name": "Search Service", "subtype": "SEARCH", "description": "Full-text search engine", "metrics": ["Index documents", "Query search", "Faceted results", "Autocomplete"]},
        # Data
        {"name": "Data Pipeline", "subtype": "ETL", "description": "ETL pipeline for analytics", "metrics": ["Extract from sources", "Transform data", "Load to warehouse", "Schedule jobs"]},
        {"name": "Event Store", "subtype": "EVENT_SOURCING", "description": "Event sourcing database", "metrics": ["Append events", "Replay events", "Snapshots", "Projections"]},
        {"name": "File Storage", "subtype": "STORAGE", "description": "Object storage service", "metrics": ["Upload files", "Download files", "Generate signed URLs", "Lifecycle policies"]},
        # Compute
        {"name": "Job Scheduler", "subtype": "SCHEDULER", "description": "Distributed job scheduling", "metrics": ["Schedule jobs", "Retry failed jobs", "Job dependencies", "Monitoring"]},
        {"name": "Serverless Runtime", "subtype": "FAAS", "description": "Function-as-a-service platform", "metrics": ["Deploy functions", "Auto-scaling", "Cold start optimization", "Logging"]},
        {"name": "ML Inference", "subtype": "ML_SERVING", "description": "ML model serving platform", "metrics": ["Load models", "Run inference", "A/B testing", "Model versioning"]},
        # Developer Tools
        {"name": "Feature Flags", "subtype": "FEATURE_FLAGS", "description": "Feature flag management", "metrics": ["Create flags", "Target users", "Rollout percentages", "Analytics"]},
        {"name": "Config Service", "subtype": "CONFIG", "description": "Centralized configuration", "metrics": ["Store configs", "Version history", "Environment separation", "Hot reload"]},
        {"name": "Secret Manager", "subtype": "SECRETS", "description": "Secrets management", "metrics": ["Store secrets", "Rotate keys", "Access audit", "Integration"]},
        # Multi-tenant
        {"name": "Notification Hub", "subtype": "MULTI_TENANT", "description": "Multi-channel notification service", "metrics": ["Send email", "Send SMS", "Push notifications", "Delivery tracking"]},
        {"name": "Billing Service", "subtype": "MULTI_TENANT", "description": "Usage-based billing platform", "metrics": ["Track usage", "Generate invoices", "Payment processing", "Subscription management"]},
        {"name": "Analytics Platform", "subtype": "MULTI_TENANT", "description": "Product analytics service", "metrics": ["Track events", "Build funnels", "Cohort analysis", "Dashboards"]},
        {"name": "CMS API", "subtype": "HEADLESS_CMS", "description": "Headless content management", "metrics": ["Create content", "API delivery", "Media handling", "Localization"]},
    ],
    "BIZ": [
        {"name": "SaaS Starter", "north_star": "REVENUE", "description": "B2B SaaS product", "metrics": ["User signups", "Trial conversions", "Monthly revenue", "Churn reduction"]},
        {"name": "Marketplace", "north_star": "GMV", "description": "Two-sided marketplace", "metrics": ["Seller onboarding", "Buyer acquisition", "Transaction volume", "Take rate"]},
        {"name": "Subscription Box", "north_star": "REVENUE", "description": "Physical subscription product", "metrics": ["Subscriber growth", "Box fulfillment", "Retention rate", "Referrals"]},
        {"name": "Course Platform", "north_star": "STUDENTS", "description": "Online education", "metrics": ["Course creation", "Student enrollment", "Completion rate", "Reviews"]},
        {"name": "Newsletter Biz", "north_star": "SUBSCRIBERS", "description": "Paid newsletter", "metrics": ["Subscriber growth", "Open rates", "Paid conversions", "Sponsorships"]},
        {"name": "Agency", "north_star": "REVENUE", "description": "Service agency", "metrics": ["Client acquisition", "Project delivery", "Recurring retainers", "Referrals"]},
        {"name": "E-commerce", "north_star": "REVENUE", "description": "Direct-to-consumer brand", "metrics": ["Product launches", "Traffic growth", "Conversion rate", "AOV increase"]},
        {"name": "Mobile App", "north_star": "USERS", "description": "Consumer mobile app", "metrics": ["App downloads", "DAU/MAU", "In-app purchases", "Retention"]},
        {"name": "API Product", "north_star": "API_CALLS", "description": "Developer API product", "metrics": ["Developer signups", "API adoption", "Usage growth", "Enterprise deals"]},
        {"name": "Community", "north_star": "MEMBERS", "description": "Paid community", "metrics": ["Member signups", "Engagement rate", "Events hosted", "Renewals"]},
    ],
}


@dataclass
class IdeaForecastResult:
    """Result from forecasting a single idea."""
    idea_name: str
    system_type: str
    subtype: str
    description: str

    # Forecast results
    success_rate: float
    avg_cycles: float
    time_estimate: str
    risk_level: str

    # Aggregated from runs
    num_runs: int
    outcomes: list[dict]

    def to_dict(self) -> dict:
        return {
            "idea_name": self.idea_name,
            "system_type": self.system_type,
            "subtype": self.subtype,
            "description": self.description,
            "success_rate": self.success_rate,
            "avg_cycles": self.avg_cycles,
            "time_estimate": self.time_estimate,
            "risk_level": self.risk_level,
            "num_runs": self.num_runs,
        }


class IdeaExplorer:
    """
    Explore multiple business/service ideas through forecasting.

    Generates diverse ideas and simulates each to find best candidates.
    """

    def __init__(
        self,
        num_user_ideas: int = 10,
        num_biz_ideas: int = 5,
        runs_per_idea: int = 3,
        max_cycles: int = 20,
        variables: ForecastVariables = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
    ):
        self.num_user_ideas = num_user_ideas
        self.num_biz_ideas = num_biz_ideas
        self.runs_per_idea = runs_per_idea
        self.max_cycles = max_cycles
        self.variables = variables or ForecastVariables()
        self.on_progress = on_progress

    def generate_ideas(self) -> list[dict]:
        """Generate a diverse set of ideas from templates."""
        ideas = []

        # Sample USER ideas
        user_templates = IDEA_TEMPLATES["USER"]
        user_sample = random.sample(user_templates, min(self.num_user_ideas, len(user_templates)))
        for t in user_sample:
            ideas.append({
                "name": t["name"],
                "system_type": "USER SYSTEM",
                "subtype": t.get("subtype", "GENERAL"),
                "description": t["description"],
                "metrics": t["metrics"],
            })

        # Sample BIZ ideas
        biz_templates = IDEA_TEMPLATES["BIZ"]
        biz_sample = random.sample(biz_templates, min(self.num_biz_ideas, len(biz_templates)))
        for t in biz_sample:
            ideas.append({
                "name": t["name"],
                "system_type": "BUSINESS SYSTEM",
                "subtype": t.get("north_star", "REVENUE"),
                "description": t["description"],
                "metrics": t["metrics"],
            })

        return ideas

    async def explore(self, ideas: list[dict] = None) -> list[IdeaForecastResult]:
        """
        Run forecasts on multiple ideas and rank them.

        Args:
            ideas: Optional list of ideas (generates if not provided)

        Returns:
            List of IdeaForecastResult sorted by success rate
        """
        if ideas is None:
            ideas = self.generate_ideas()

        results = []
        total = len(ideas)

        for i, idea in enumerate(ideas):
            if self.on_progress:
                self.on_progress(idea["name"], i + 1, total)

            result = await self._forecast_idea(idea)
            results.append(result)

        # Sort by success rate (best first)
        results.sort(key=lambda r: r.success_rate, reverse=True)
        return results

    async def _forecast_idea(self, idea: dict) -> IdeaForecastResult:
        """Run forecast for a single idea."""
        import tempfile
        import shutil

        # Create temporary project with synthetic foundation
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create foundation directory
            foundation_dir = project_path / "foundation"
            foundation_dir.mkdir(parents=True)

            # Write synthetic north-star.md
            north_star_content = f"""# North Star

**System Type:** {idea['system_type']}
**North Star Type:** {idea.get('subtype', 'GENERAL')}
**Utility Subtype:** {idea.get('subtype', 'GENERAL')}

## Primary Objective

- {idea['description']}

## Success Metrics

"""
            for metric in idea.get("metrics", []):
                north_star_content += f"- {metric}\n"

            (foundation_dir / "north-star.md").write_text(north_star_content)

            # Write minimal oracle.md
            oracle_content = """# Oracle

## Values
- Build reliable systems
- Ship quickly
- Learn from feedback
"""
            (foundation_dir / "oracle.md").write_text(oracle_content)

            # Create .1kh directory
            (project_path / ".1kh").mkdir(exist_ok=True)

            # Run multiple forecasts
            outcomes = []
            for run in range(self.runs_per_idea):
                seed = random.randint(0, 1000000)
                foundation = FoundationContext.load(project_path)

                runner = ForecastRunner(
                    project_path=project_path,
                    mode="mock",
                    variables=self.variables,
                    max_cycles=self.max_cycles,
                    seed=seed,
                    foundation=foundation,
                )

                try:
                    outcome = await runner.run()
                    outcomes.append(outcome)
                except Exception as e:
                    logger.warning(f"Forecast failed for {idea['name']}: {e}")

        # Aggregate results
        if not outcomes:
            return IdeaForecastResult(
                idea_name=idea["name"],
                system_type=idea["system_type"],
                subtype=idea.get("subtype", "GENERAL"),
                description=idea["description"],
                success_rate=0.0,
                avg_cycles=0,
                time_estimate="Unknown",
                risk_level="high",
                num_runs=0,
                outcomes=[],
            )

        # Use average task success rate from individual runs (more nuanced than binary target_reached)
        # This reflects how well tasks execute, not just whether target was hit
        avg_task_success = sum(o.success_rate for o in outcomes) / len(outcomes)

        # Also track target achievement rate
        target_rate = sum(1 for o in outcomes if o.target_reached) / len(outcomes)

        # Combined score: weight task success (60%) + target achievement (40%)
        # This gives credit for progress even if target not hit
        success_rate = (avg_task_success * 0.6) + (target_rate * 0.4)

        avg_cycles = sum(o.cycles_completed for o in outcomes) / len(outcomes)

        # Determine risk level based on combined success
        if success_rate >= 0.7:
            risk_level = "low"
        elif success_rate >= 0.5:
            risk_level = "medium"
        else:
            risk_level = "high"

        # Time estimate
        avg_days = sum(o.simulated_days for o in outcomes) / len(outcomes)
        if avg_days < 30:
            time_estimate = f"{int(avg_days / 7)}-{int(avg_days / 7) + 1} weeks"
        else:
            time_estimate = f"{int(avg_days / 30)}-{int(avg_days / 30) + 1} months"

        return IdeaForecastResult(
            idea_name=idea["name"],
            system_type=idea["system_type"],
            subtype=idea.get("subtype", "GENERAL"),
            description=idea["description"],
            success_rate=success_rate,
            avg_cycles=avg_cycles,
            time_estimate=time_estimate,
            risk_level=risk_level,
            num_runs=len(outcomes),
            outcomes=[o.to_dict() for o in outcomes],
        )


# =============================================================================
# Sensitivity Runner
# =============================================================================

class SensitivityRunner:
    """
    Systematic sensitivity analysis for forecast variables.

    Analyzes which variables have the biggest impact on outcomes by
    varying them one at a time and measuring the effect.
    """

    # Variable definitions with all possible values
    VARIABLE_DEFINITIONS = {
        "human_quality": ["perfect", "good", "mediocre", "poor"],
        "market_response": ["optimistic", "realistic", "pessimistic"],
        "chaos_level": ["none", "low", "medium", "high"],
        "execution_variance": [0.0, 0.25, 0.5, 0.75, 1.0],
        "human_selection": ["optimal", "random", "worst"],
    }

    def __init__(
        self,
        project_path: Path,
        baseline: ForecastVariables,
        runs_per_value: int = 5,
        max_cycles: int = 30,
        foundation: Optional[FoundationContext] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
    ):
        """
        Initialize sensitivity runner.

        Args:
            project_path: Path to the project
            baseline: Baseline variable values to start from
            runs_per_value: Number of Monte Carlo runs per variable value
            max_cycles: Maximum cycles per simulation
            foundation: Optional foundation context (loaded if not provided)
            on_progress: Optional callback (variable_name, current, total)
        """
        self.project_path = Path(project_path)
        self.baseline = baseline
        self.runs_per_value = runs_per_value
        self.max_cycles = max_cycles
        self.foundation = foundation or FoundationContext.load(project_path)
        self.on_progress = on_progress

    async def analyze_variable(
        self,
        variable_name: str,
        values: list[Any] = None,
    ) -> SensitivityResult:
        """
        Analyze impact of varying one variable.

        Args:
            variable_name: Name of the variable to analyze
            values: Optional list of values to test (uses defaults if not provided)

        Returns:
            SensitivityResult with impact metrics
        """
        if variable_name not in self.VARIABLE_DEFINITIONS:
            raise ValueError(f"Unknown variable: {variable_name}")

        values = values or self.VARIABLE_DEFINITIONS.get(variable_name, [])
        outcomes = []

        for i, value in enumerate(values):
            # Create modified variables
            modified_dict = self.baseline.to_dict()
            modified_dict[variable_name] = value
            modified = ForecastVariables.from_dict(modified_dict)

            # Run Monte Carlo for this value
            aggregated = await self._run_for_value(modified)
            outcomes.append(aggregated)

            if self.on_progress:
                self.on_progress(variable_name, i + 1, len(values))

        return self._build_sensitivity_result(
            variable_name,
            values,
            outcomes,
            getattr(self.baseline, variable_name),
        )

    async def analyze_all(
        self,
        variables: list[str] = None,
    ) -> dict[str, SensitivityResult]:
        """
        Analyze all variables one at a time.

        Args:
            variables: Optional list of variables to analyze (all if not provided)

        Returns:
            Dict mapping variable name to SensitivityResult
        """
        variables = variables or list(self.VARIABLE_DEFINITIONS.keys())
        results = {}

        for var_name in variables:
            results[var_name] = await self.analyze_variable(var_name)

        return results

    async def analyze_interaction(
        self,
        var1_name: str,
        var2_name: str,
    ) -> InteractionResult:
        """
        Analyze interaction between two variables.

        Runs simulations for all combinations of two variables to
        detect synergistic or antagonistic effects.

        Args:
            var1_name: First variable name
            var2_name: Second variable name

        Returns:
            InteractionResult with 2D grid and interaction metrics
        """
        if var1_name not in self.VARIABLE_DEFINITIONS:
            raise ValueError(f"Unknown variable: {var1_name}")
        if var2_name not in self.VARIABLE_DEFINITIONS:
            raise ValueError(f"Unknown variable: {var2_name}")

        var1_values = self.VARIABLE_DEFINITIONS[var1_name]
        var2_values = self.VARIABLE_DEFINITIONS[var2_name]

        outcomes_grid = []
        total = len(var1_values) * len(var2_values)
        current = 0

        for val2 in var2_values:
            row = []
            for val1 in var1_values:
                modified_dict = self.baseline.to_dict()
                modified_dict[var1_name] = val1
                modified_dict[var2_name] = val2
                modified = ForecastVariables.from_dict(modified_dict)

                aggregated = await self._run_for_value(modified)
                row.append(aggregated)

                current += 1
                if self.on_progress:
                    self.on_progress(f"{var1_name} x {var2_name}", current, total)

            outcomes_grid.append(row)

        return self._build_interaction_result(
            var1_name, var1_values,
            var2_name, var2_values,
            outcomes_grid,
        )

    async def _run_for_value(self, variables: ForecastVariables) -> dict:
        """Run multiple simulations for a variable configuration."""
        outcomes: list[ForecastOutcome] = []

        for run_idx in range(self.runs_per_value):
            seed = random.randint(0, 1000000)

            runner = ForecastRunner(
                project_path=self.project_path,
                mode="mock",
                variables=variables,
                max_cycles=self.max_cycles,
                seed=seed,
                foundation=self.foundation,
            )

            try:
                outcome = await runner.run()
                outcomes.append(outcome)
            except Exception as e:
                logger.warning(f"Run failed: {e}")

        return self._aggregate_outcomes(outcomes)

    def _aggregate_outcomes(self, outcomes: list[ForecastOutcome]) -> dict:
        """Aggregate multiple outcomes into summary statistics."""
        if not outcomes:
            return {
                "success_rate": 0.0,
                "cycles_avg": 0,
                "num_runs": 0,
            }

        success_rate = sum(1 for o in outcomes if o.target_reached) / len(outcomes)
        cycles_avg = sum(o.cycles_completed for o in outcomes) / len(outcomes)

        return {
            "success_rate": success_rate,
            "cycles_avg": cycles_avg,
            "cycles_min": min(o.cycles_completed for o in outcomes),
            "cycles_max": max(o.cycles_completed for o in outcomes),
            "num_runs": len(outcomes),
        }

    def _build_sensitivity_result(
        self,
        name: str,
        values: list[Any],
        outcomes: list[dict],
        baseline_value: Any,
    ) -> SensitivityResult:
        """Compute impact metrics from outcomes."""
        success_rates = [o.get("success_rate", 0.0) for o in outcomes]
        cycles_avgs = [o.get("cycles_avg", 0) for o in outcomes]

        min_sr = min(success_rates) if success_rates else 0.0
        max_sr = max(success_rates) if success_rates else 0.0
        min_cycles = int(min(cycles_avgs)) if cycles_avgs else 0
        max_cycles = int(max(cycles_avgs)) if cycles_avgs else 0

        return SensitivityResult(
            variable_name=name,
            variable_values=values,
            outcomes=outcomes,
            baseline_value=baseline_value,
            success_rate_range=(min_sr, max_sr),
            success_rate_delta=max_sr - min_sr,
            cycles_range=(min_cycles, max_cycles),
            cycles_delta=max_cycles - min_cycles,
        )

    def _build_interaction_result(
        self,
        var1_name: str,
        var1_values: list[Any],
        var2_name: str,
        var2_values: list[Any],
        outcomes_grid: list[list[dict]],
    ) -> InteractionResult:
        """
        Compute interaction metrics from 2D outcomes grid.

        Measures interaction strength by comparing actual outcomes
        to expected additive effects.
        """
        # Extract success rates from grid
        success_grid = [
            [cell.get("success_rate", 0.0) for cell in row]
            for row in outcomes_grid
        ]

        # Compute row and column means
        row_means = [sum(row) / len(row) for row in success_grid]
        col_means = [
            sum(success_grid[r][c] for r in range(len(success_grid))) / len(success_grid)
            for c in range(len(success_grid[0]))
        ]
        grand_mean = sum(row_means) / len(row_means) if row_means else 0.0

        # Compute interaction as deviation from additive model
        total_deviation = 0.0
        count = 0
        for r, row in enumerate(success_grid):
            for c, val in enumerate(row):
                # Expected value under additive model
                expected = grand_mean + (row_means[r] - grand_mean) + (col_means[c] - grand_mean)
                deviation = abs(val - expected)
                total_deviation += deviation
                count += 1

        # Normalize interaction strength to 0-1
        avg_deviation = total_deviation / count if count > 0 else 0.0
        # Scale: 0.1 deviation ~ weak, 0.3+ ~ strong
        interaction_strength = min(1.0, avg_deviation / 0.3)
        has_interaction = interaction_strength > 0.2

        return InteractionResult(
            var1_name=var1_name,
            var1_values=var1_values,
            var2_name=var2_name,
            var2_values=var2_values,
            outcomes_grid=outcomes_grid,
            interaction_strength=interaction_strength,
            has_interaction=has_interaction,
        )
