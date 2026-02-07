"""
REFLECTION Engine - Trajectory analysis and pivot detection.

The REFLECTION loop asks:
- "Are we on a realistic trajectory to hit our goal?"
- "Is the system complete enough to function?"
- "Do we need to AUGMENT (add pieces), OPTIMIZE (do better), or PIVOT (change direction)?"

This is the feedback loop that connects EXECUTION back to FOUNDATION.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Any

from core.system_state import SystemStateManager, ComponentStatus, SystemMode
from core.dashboard import Dashboard, EventType

logger = logging.getLogger("1kh.reflection")


# =============================================================================
# Recommendation Types
# =============================================================================

class RecommendationType(str, Enum):
    """Type of recommendation from REFLECTION."""
    AUGMENT = "augment"    # Add missing component (auto-approvable)
    OPTIMIZE = "optimize"  # Improve existing component (auto-approvable)
    PIVOT = "pivot"        # Change core direction (requires human)
    CONTINUE = "continue"  # Stay the course


class TrustLevel(str, Enum):
    """User trust level for auto-approval."""
    MANUAL = "manual"        # Every decision requires approval
    GUIDED = "guided"        # Auto-accept AUGMENT, prompt for PIVOT
    AUTONOMOUS = "autonomous"  # Auto-accept everything within Oracle bounds


# =============================================================================
# Recommendations
# =============================================================================

@dataclass
class Recommendation:
    """A recommendation from REFLECTION."""
    type: RecommendationType
    title: str
    description: str
    rationale: str
    priority: int = 1  # 1 = highest priority
    component_category: Optional[str] = None  # Which component this affects
    suggested_hypotheses: list[dict] = field(default_factory=list)
    requires_human: bool = False  # True for PIVOT

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "priority": self.priority,
            "component_category": self.component_category,
            "suggested_hypotheses": self.suggested_hypotheses,
            "requires_human": self.requires_human,
        }


@dataclass
class TrajectoryAnalysis:
    """Analysis of current trajectory toward goal."""
    current_value: float
    target_value: float
    velocity_per_cycle: float  # Average change per cycle
    velocity_trend: str  # "accelerating", "steady", "decelerating", "stalled"
    cycles_to_goal: Optional[int]  # Estimated cycles to reach goal (None if unrealistic)
    time_to_goal: Optional[str]  # Human-readable estimate
    confidence: float  # 0-1 confidence in estimate
    is_realistic: bool  # True if we can reasonably reach goal
    warning: Optional[str] = None


@dataclass
class CompletenessAnalysis:
    """Analysis of system completeness."""
    score: float  # 0-1 completeness
    can_generate_revenue: bool
    blockers: list[str]
    missing_components: list[str]
    building_components: list[str]
    live_components: list[str]


@dataclass
class ReflectionResult:
    """Complete result from a REFLECTION cycle."""
    timestamp: datetime
    cycle_number: int

    # Analyses
    completeness: CompletenessAnalysis
    trajectory: TrajectoryAnalysis

    # Recommendations
    recommendations: list[Recommendation]

    # Overall assessment
    status: str  # "healthy", "warning", "critical"
    summary: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cycle_number": self.cycle_number,
            "completeness": {
                "score": self.completeness.score,
                "can_generate_revenue": self.completeness.can_generate_revenue,
                "blockers": self.completeness.blockers,
                "missing_components": self.completeness.missing_components,
                "building_components": self.completeness.building_components,
                "live_components": self.completeness.live_components,
            },
            "trajectory": {
                "current_value": self.trajectory.current_value,
                "target_value": self.trajectory.target_value,
                "velocity_per_cycle": self.trajectory.velocity_per_cycle,
                "velocity_trend": self.trajectory.velocity_trend,
                "cycles_to_goal": self.trajectory.cycles_to_goal,
                "time_to_goal": self.trajectory.time_to_goal,
                "confidence": self.trajectory.confidence,
                "is_realistic": self.trajectory.is_realistic,
                "warning": self.trajectory.warning,
            },
            "recommendations": [r.to_dict() for r in self.recommendations],
            "status": self.status,
            "summary": self.summary,
        }


# =============================================================================
# REFLECTION Engine
# =============================================================================

class ReflectionEngine:
    """
    The REFLECTION loop engine.

    Analyzes system state and trajectory, generates recommendations.
    """

    def __init__(
        self,
        project_path: Path,
        dashboard: Dashboard = None,
        system_state: SystemStateManager = None,
    ):
        self.project_path = Path(project_path)
        self.dashboard = dashboard or Dashboard(project_path)
        self.system_state = system_state or SystemStateManager(project_path)

        # Reflection history
        self.history_file = self.project_path / ".1kh" / "reflection_history.json"
        self._history: list[dict] = []

    def reflect(self, cycle_number: int = 0) -> ReflectionResult:
        """
        Perform a full REFLECTION cycle.

        Returns analysis and recommendations.
        """
        logger.info(f"Starting REFLECTION at cycle {cycle_number}")

        # 1. Analyze system completeness
        completeness = self._analyze_completeness()

        # 2. Analyze trajectory
        trajectory = self._analyze_trajectory()

        # 3. Generate recommendations
        recommendations = self._generate_recommendations(completeness, trajectory)

        # 4. Determine overall status
        status = self._determine_status(completeness, trajectory, recommendations)

        # 5. Generate summary
        summary = self._generate_summary(completeness, trajectory, recommendations, status)

        result = ReflectionResult(
            timestamp=datetime.utcnow(),
            cycle_number=cycle_number,
            completeness=completeness,
            trajectory=trajectory,
            recommendations=recommendations,
            status=status,
            summary=summary,
        )

        # Save to history
        self._save_to_history(result)

        return result

    def _analyze_completeness(self) -> CompletenessAnalysis:
        """Analyze system completeness."""
        state = self.system_state.load()

        can_rev, blockers = state.can_generate_revenue()

        return CompletenessAnalysis(
            score=state.completeness_score(),
            can_generate_revenue=can_rev,
            blockers=blockers,
            missing_components=[c.name for c in state.get_missing_components()],
            building_components=[c.name for c in state.get_building_components()],
            live_components=[c.name for c in state.get_live_components()],
        )

    def _analyze_trajectory(self) -> TrajectoryAnalysis:
        """Analyze trajectory toward goal."""
        dashboard_state = self.dashboard.compute_state()

        current = dashboard_state.north_star.current_value
        target = dashboard_state.north_star.target_value
        cycle_count = dashboard_state.cycle_count

        # Calculate velocity (revenue per cycle)
        if cycle_count > 0:
            velocity = current / cycle_count
        else:
            velocity = 0

        # Determine velocity trend by looking at recent vs older revenue
        events = self.dashboard.event_log.read_by_type(EventType.REVENUE)
        velocity_trend = self._calculate_velocity_trend(events, cycle_count)

        # Estimate cycles to goal
        if velocity > 0:
            remaining = target - current
            cycles_needed = int(remaining / velocity)

            # Adjust for acceleration/deceleration
            if velocity_trend == "accelerating":
                cycles_needed = int(cycles_needed * 0.6)  # Faster
            elif velocity_trend == "decelerating":
                cycles_needed = int(cycles_needed * 1.5)  # Slower
        else:
            cycles_needed = None

        # Determine if realistic
        is_realistic = cycles_needed is not None and cycles_needed < 1000

        # Human-readable time estimate (rough: 1 cycle ~ 1 day of focused work)
        if cycles_needed is not None:
            if cycles_needed < 7:
                time_estimate = f"~{cycles_needed} days"
            elif cycles_needed < 30:
                time_estimate = f"~{cycles_needed // 7} weeks"
            elif cycles_needed < 365:
                time_estimate = f"~{cycles_needed // 30} months"
            else:
                time_estimate = f"~{cycles_needed // 365} years"
        else:
            time_estimate = "Unable to estimate"

        # Warning if trajectory is problematic
        warning = None
        if cycles_needed is None:
            warning = "No progress detected - revenue velocity is zero"
        elif cycles_needed > 500:
            warning = f"At current rate, goal would take {time_estimate} - consider pivoting"
        elif velocity_trend == "decelerating":
            warning = "Revenue velocity is slowing down"

        # Confidence based on data points
        confidence = min(1.0, cycle_count / 10)  # More cycles = more confidence

        return TrajectoryAnalysis(
            current_value=current,
            target_value=target,
            velocity_per_cycle=velocity,
            velocity_trend=velocity_trend,
            cycles_to_goal=cycles_needed,
            time_to_goal=time_estimate,
            confidence=confidence,
            is_realistic=is_realistic,
            warning=warning,
        )

    def _calculate_velocity_trend(self, events: list, cycle_count: int) -> str:
        """Calculate if velocity is accelerating, steady, or decelerating."""
        if len(events) < 4:
            return "insufficient_data"

        # Split events into first half and second half
        mid = len(events) // 2
        first_half = events[:mid]
        second_half = events[mid:]

        first_total = sum(e.value for e in first_half)
        second_total = sum(e.value for e in second_half)

        if len(first_half) > 0 and len(second_half) > 0:
            first_avg = first_total / len(first_half)
            second_avg = second_total / len(second_half)

            ratio = second_avg / first_avg if first_avg > 0 else 1

            if ratio > 1.2:
                return "accelerating"
            elif ratio < 0.8:
                return "decelerating"
            else:
                return "steady"

        return "steady"

    def _generate_recommendations(
        self,
        completeness: CompletenessAnalysis,
        trajectory: TrajectoryAnalysis,
    ) -> list[Recommendation]:
        """Generate recommendations based on analysis."""
        recommendations = []

        # Priority 1: Missing critical components
        if not completeness.can_generate_revenue:
            for blocker in completeness.blockers:
                if "payment" in blocker.lower():
                    recommendations.append(Recommendation(
                        type=RecommendationType.AUGMENT,
                        title="Add Payment System",
                        description="Integrate a payment processor (Stripe, PayPal, etc.) to collect revenue",
                        rationale="Cannot generate revenue without a way to collect payments",
                        priority=1,
                        component_category="payment",
                        suggested_hypotheses=[
                            {
                                "description": "Integrate Stripe checkout for one-time payments",
                                "feasibility": 0.9,
                                "north_star_alignment": 1.0,
                            },
                            {
                                "description": "Add PayPal as alternative payment method",
                                "feasibility": 0.85,
                                "north_star_alignment": 0.8,
                            },
                        ],
                    ))

                if "product" in blocker.lower():
                    recommendations.append(Recommendation(
                        type=RecommendationType.AUGMENT,
                        title="Define Product",
                        description="Create or define the core product/service offering",
                        rationale="Cannot sell without a product",
                        priority=1,
                        component_category="product",
                        suggested_hypotheses=[
                            {
                                "description": "Build MVP version of core product",
                                "feasibility": 0.7,
                                "north_star_alignment": 1.0,
                            },
                        ],
                    ))

        # Priority 2: Missing channel (important but not blocking)
        if "Channel" in completeness.missing_components:
            recommendations.append(Recommendation(
                type=RecommendationType.AUGMENT,
                title="Add Marketing Channel",
                description="Set up a channel to acquire customers",
                rationale="Organic growth is slow - need active acquisition",
                priority=2,
                component_category="channel",
                suggested_hypotheses=[
                    {
                        "description": "Start content marketing (blog + YouTube)",
                        "feasibility": 0.8,
                        "north_star_alignment": 0.9,
                    },
                    {
                        "description": "Set up email marketing with lead magnet",
                        "feasibility": 0.85,
                        "north_star_alignment": 0.85,
                    },
                    {
                        "description": "Launch paid advertising (Google/Meta Ads)",
                        "feasibility": 0.75,
                        "north_star_alignment": 0.8,
                    },
                ],
            ))

        # Priority 3: Trajectory issues
        if not trajectory.is_realistic and completeness.can_generate_revenue:
            # System is complete but trajectory is bad - might need to pivot
            recommendations.append(Recommendation(
                type=RecommendationType.PIVOT,
                title="Consider Strategic Pivot",
                description="Current trajectory is not realistic - consider changing approach",
                rationale=trajectory.warning or "Goal is too far at current velocity",
                priority=3,
                requires_human=True,
                suggested_hypotheses=[
                    {
                        "description": "Analyze competitor strategies and identify gaps",
                        "feasibility": 0.9,
                        "north_star_alignment": 0.7,
                    },
                    {
                        "description": "Research alternative target audiences",
                        "feasibility": 0.8,
                        "north_star_alignment": 0.6,
                    },
                ],
            ))

        # Priority 4: Optimization if on track but could be better
        if trajectory.is_realistic and trajectory.velocity_trend == "decelerating":
            recommendations.append(Recommendation(
                type=RecommendationType.OPTIMIZE,
                title="Optimize Growth Rate",
                description="Revenue velocity is slowing - optimize existing channels",
                rationale="Deceleration detected - need to reinvigorate growth",
                priority=4,
                suggested_hypotheses=[
                    {
                        "description": "A/B test pricing to find optimal price point",
                        "feasibility": 0.85,
                        "north_star_alignment": 0.9,
                    },
                    {
                        "description": "Optimize conversion funnel to reduce drop-off",
                        "feasibility": 0.8,
                        "north_star_alignment": 0.85,
                    },
                ],
            ))

        # If all is well, recommend continuing
        if not recommendations:
            recommendations.append(Recommendation(
                type=RecommendationType.CONTINUE,
                title="Continue Current Strategy",
                description="System is on track - keep executing",
                rationale=f"Trajectory is healthy with {trajectory.time_to_goal} to goal",
                priority=5,
            ))

        # Sort by priority
        recommendations.sort(key=lambda r: r.priority)

        return recommendations

    def _determine_status(
        self,
        completeness: CompletenessAnalysis,
        trajectory: TrajectoryAnalysis,
        recommendations: list[Recommendation],
    ) -> str:
        """Determine overall system status."""
        # Critical if can't generate revenue
        if not completeness.can_generate_revenue:
            return "critical"

        # Critical if trajectory is unrealistic
        if not trajectory.is_realistic:
            return "critical"

        # Warning if decelerating or missing non-critical components
        if trajectory.velocity_trend == "decelerating":
            return "warning"

        if completeness.score < 0.75:
            return "warning"

        # Healthy otherwise
        return "healthy"

    def _generate_summary(
        self,
        completeness: CompletenessAnalysis,
        trajectory: TrajectoryAnalysis,
        recommendations: list[Recommendation],
        status: str,
    ) -> str:
        """Generate human-readable summary."""
        lines = []

        # Status header
        if status == "critical":
            lines.append("⚠️  CRITICAL: Immediate action required")
        elif status == "warning":
            lines.append("⚡ WARNING: Some issues need attention")
        else:
            lines.append("✅ HEALTHY: On track")

        lines.append("")

        # Completeness
        lines.append(f"System Completeness: {completeness.score:.0%}")
        if not completeness.can_generate_revenue:
            lines.append(f"  ❌ Cannot generate revenue: {', '.join(completeness.blockers)}")
        else:
            lines.append("  ✓ Revenue generation enabled")

        lines.append("")

        # Trajectory
        lines.append(f"Progress: ${trajectory.current_value:,.0f} / ${trajectory.target_value:,.0f}")
        lines.append(f"Velocity: ${trajectory.velocity_per_cycle:,.0f}/cycle ({trajectory.velocity_trend})")

        if trajectory.time_to_goal:
            lines.append(f"Estimated time to goal: {trajectory.time_to_goal}")

        if trajectory.warning:
            lines.append(f"  ⚠️  {trajectory.warning}")

        lines.append("")

        # Top recommendations
        if recommendations:
            lines.append("Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                icon = "🔧" if rec.type == RecommendationType.AUGMENT else \
                       "📈" if rec.type == RecommendationType.OPTIMIZE else \
                       "🔄" if rec.type == RecommendationType.PIVOT else "➡️"
                lines.append(f"  {i}. {icon} {rec.title}")

        return "\n".join(lines)

    def _save_to_history(self, result: ReflectionResult):
        """Save reflection result to history."""
        self._load_history()
        self._history.append(result.to_dict())

        # Keep last 100 reflections
        if len(self._history) > 100:
            self._history = self._history[-100:]

        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.write_text(json.dumps(self._history, indent=2))

    def _load_history(self):
        """Load reflection history."""
        if self.history_file.exists():
            try:
                self._history = json.loads(self.history_file.read_text())
            except json.JSONDecodeError:
                self._history = []
        else:
            self._history = []

    # =========================================================================
    # Auto-accept Logic
    # =========================================================================

    def filter_recommendations_by_trust(
        self,
        recommendations: list[Recommendation],
        trust_level: TrustLevel,
    ) -> tuple[list[Recommendation], list[Recommendation]]:
        """
        Split recommendations into auto-accept and needs-approval.

        Returns (auto_accept, needs_approval)
        """
        if trust_level == TrustLevel.MANUAL:
            # Everything needs approval
            return [], recommendations

        elif trust_level == TrustLevel.GUIDED:
            # Auto-accept AUGMENT and OPTIMIZE, prompt for PIVOT
            auto = [r for r in recommendations if r.type in (
                RecommendationType.AUGMENT,
                RecommendationType.OPTIMIZE,
                RecommendationType.CONTINUE,
            )]
            manual = [r for r in recommendations if r.type == RecommendationType.PIVOT]
            return auto, manual

        else:  # AUTONOMOUS
            # Auto-accept everything (PIVOT still flagged but accepted)
            return recommendations, []

    def apply_recommendations(
        self,
        recommendations: list[Recommendation],
    ) -> list[dict]:
        """
        Apply recommendations by generating hypotheses.

        Returns list of generated hypotheses.
        """
        generated_hypotheses = []

        for rec in recommendations:
            if rec.type == RecommendationType.CONTINUE:
                continue  # Nothing to do

            for hyp in rec.suggested_hypotheses:
                hyp_id = f"hyp-ref-{len(generated_hypotheses)+1:03d}"
                generated_hypotheses.append({
                    "id": hyp_id,
                    "description": hyp["description"],
                    "feasibility": hyp.get("feasibility", 0.7),
                    "north_star_alignment": hyp.get("north_star_alignment", 0.8),
                    "source": "reflection",
                    "recommendation_type": rec.type.value,
                    "component_category": rec.component_category,
                })

                # Update system state to track this
                if rec.component_category:
                    self.system_state.update_component(
                        rec.component_category,
                        status=ComponentStatus.PLANNED,
                        hypothesis_id=hyp_id,
                    )

        return generated_hypotheses
