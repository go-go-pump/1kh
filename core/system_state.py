"""
System State - Tracks what's actually built in the system.

This is the "reality check" layer that knows:
- What components exist (product, payment, channel, etc.)
- Their current status (planned, building, live)
- What's missing for the system to function

Used by:
- REFLECTION to check completeness
- EXECUTOR to generate realistic metrics
- DASHBOARD to show system status
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger("1kh.system_state")


# =============================================================================
# System Mode
# =============================================================================

class SystemMode(str, Enum):
    """What type of system is being built."""
    BUSINESS = "business"  # Revenue-focused (default)
    SYSTEM = "system"      # Custom KPI (internal tools, POCs, etc.)


# =============================================================================
# Component Status
# =============================================================================

class ComponentStatus(str, Enum):
    """Status of a system component."""
    MISSING = "missing"      # Not defined, not planned
    PLANNED = "planned"      # Defined but not started
    BUILDING = "building"    # Work in progress
    LIVE = "live"            # Deployed and functional
    BROKEN = "broken"        # Was live, now broken


# =============================================================================
# Business Components (for BUSINESS mode)
# =============================================================================

@dataclass
class BusinessComponent:
    """A component required for a viable business."""
    name: str
    category: str  # "product", "payment", "channel", "fulfillment", "support"
    status: ComponentStatus = ComponentStatus.MISSING
    description: str = ""
    details: dict = field(default_factory=dict)
    hypothesis_ids: list[str] = field(default_factory=list)  # Which hypotheses built this
    task_ids: list[str] = field(default_factory=list)  # Which tasks built this
    live_since: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "status": self.status.value,
            "description": self.description,
            "details": self.details,
            "hypothesis_ids": self.hypothesis_ids,
            "task_ids": self.task_ids,
            "live_since": self.live_since.isoformat() if self.live_since else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BusinessComponent":
        return cls(
            name=data["name"],
            category=data["category"],
            status=ComponentStatus(data.get("status", "missing")),
            description=data.get("description", ""),
            details=data.get("details", {}),
            hypothesis_ids=data.get("hypothesis_ids", []),
            task_ids=data.get("task_ids", []),
            live_since=datetime.fromisoformat(data["live_since"]) if data.get("live_since") else None,
        )


# =============================================================================
# Default Business Components
# =============================================================================

def get_default_business_components() -> list[BusinessComponent]:
    """
    Get the default components required for a viable business.

    These are the MINIMUM components needed for revenue to flow.
    """
    return [
        BusinessComponent(
            name="Product",
            category="product",
            description="The thing you sell (course, SaaS, service, etc.)",
        ),
        BusinessComponent(
            name="Payment",
            category="payment",
            description="How customers pay you (Stripe, PayPal, etc.)",
        ),
        BusinessComponent(
            name="Channel",
            category="channel",
            description="How customers find you (content, ads, referrals, etc.)",
        ),
        BusinessComponent(
            name="Fulfillment",
            category="fulfillment",
            description="How customers receive value (delivery, access, etc.)",
        ),
    ]


# =============================================================================
# System State
# =============================================================================

@dataclass
class SystemState:
    """
    Complete state of what's built in the system.

    This is persisted to disk and updated as work completes.
    """
    mode: SystemMode = SystemMode.BUSINESS
    components: list[BusinessComponent] = field(default_factory=list)
    custom_kpis: dict[str, Any] = field(default_factory=dict)  # For SYSTEM mode

    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Hypothesis/Task tracking
    active_hypotheses: list[dict] = field(default_factory=list)
    completed_hypotheses: list[dict] = field(default_factory=list)
    active_tasks: list[dict] = field(default_factory=list)
    completed_tasks: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "components": [c.to_dict() for c in self.components],
            "custom_kpis": self.custom_kpis,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "active_hypotheses": self.active_hypotheses,
            "completed_hypotheses": self.completed_hypotheses,
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SystemState":
        return cls(
            mode=SystemMode(data.get("mode", "business")),
            components=[BusinessComponent.from_dict(c) for c in data.get("components", [])],
            custom_kpis=data.get("custom_kpis", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            active_hypotheses=data.get("active_hypotheses", []),
            completed_hypotheses=data.get("completed_hypotheses", []),
            active_tasks=data.get("active_tasks", []),
            completed_tasks=data.get("completed_tasks", []),
        )

    # =========================================================================
    # Completeness Checks
    # =========================================================================

    def get_component(self, category: str) -> Optional[BusinessComponent]:
        """Get component by category."""
        for c in self.components:
            if c.category == category:
                return c
        return None

    def is_component_live(self, category: str) -> bool:
        """Check if a component is live."""
        comp = self.get_component(category)
        return comp is not None and comp.status == ComponentStatus.LIVE

    def get_missing_components(self) -> list[BusinessComponent]:
        """Get components that are missing or not started."""
        return [c for c in self.components if c.status == ComponentStatus.MISSING]

    def get_building_components(self) -> list[BusinessComponent]:
        """Get components currently being built."""
        return [c for c in self.components if c.status == ComponentStatus.BUILDING]

    def get_live_components(self) -> list[BusinessComponent]:
        """Get components that are live."""
        return [c for c in self.components if c.status == ComponentStatus.LIVE]

    def completeness_score(self) -> float:
        """
        Calculate system completeness (0.0 to 1.0).

        For BUSINESS mode, requires all core components.
        """
        if not self.components:
            return 0.0

        live_count = len(self.get_live_components())
        return live_count / len(self.components)

    def can_generate_revenue(self) -> tuple[bool, list[str]]:
        """
        Check if the system can generate revenue.

        Returns (can_generate, list_of_blockers)
        """
        if self.mode != SystemMode.BUSINESS:
            return True, []  # Non-business mode doesn't need revenue

        blockers = []

        # Must have product
        if not self.is_component_live("product"):
            blockers.append("No product is live")

        # Must have payment
        if not self.is_component_live("payment"):
            blockers.append("No payment system is live")

        # Should have channel (can scrape by with organic)
        if not self.is_component_live("channel"):
            # Not a hard blocker, but severely limits revenue
            pass

        return len(blockers) == 0, blockers

    def get_revenue_capability(self) -> str:
        """
        Get a description of current revenue capability.
        """
        can_rev, blockers = self.can_generate_revenue()

        if not can_rev:
            return f"BLOCKED: {'; '.join(blockers)}"

        has_channel = self.is_component_live("channel")

        if has_channel:
            return "FULL: Product + Payment + Channel all live"
        else:
            return "LIMITED: Product + Payment live, but no marketing channel"


# =============================================================================
# System State Manager
# =============================================================================

class SystemStateManager:
    """
    Manages system state persistence and updates.
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.state_file = self.project_path / ".1kh" / "system_state.json"
        self._state: Optional[SystemState] = None

    def load(self) -> SystemState:
        """Load system state from disk, or create default."""
        if self._state is not None:
            return self._state

        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self._state = SystemState.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load system state: {e}")
                self._state = self._create_default()
        else:
            self._state = self._create_default()

        return self._state

    def save(self):
        """Save system state to disk."""
        if self._state is None:
            return

        self._state.updated_at = datetime.utcnow()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._state.to_dict(), indent=2))

    def _create_default(self) -> SystemState:
        """Create default system state for business mode."""
        return SystemState(
            mode=SystemMode.BUSINESS,
            components=get_default_business_components(),
        )

    def clear(self):
        """Clear system state (for fresh starts)."""
        self._state = self._create_default()
        self.save()

    # =========================================================================
    # Component Updates
    # =========================================================================

    def update_component(
        self,
        category: str,
        status: ComponentStatus = None,
        description: str = None,
        details: dict = None,
        hypothesis_id: str = None,
        task_id: str = None,
    ):
        """Update a component's status and details."""
        state = self.load()
        comp = state.get_component(category)

        if comp is None:
            logger.warning(f"Component not found: {category}")
            return

        if status is not None:
            comp.status = status
            if status == ComponentStatus.LIVE and comp.live_since is None:
                comp.live_since = datetime.utcnow()

        if description is not None:
            comp.description = description

        if details is not None:
            comp.details.update(details)

        if hypothesis_id and hypothesis_id not in comp.hypothesis_ids:
            comp.hypothesis_ids.append(hypothesis_id)

        if task_id and task_id not in comp.task_ids:
            comp.task_ids.append(task_id)

        self.save()

    def add_custom_component(
        self,
        name: str,
        category: str,
        description: str = "",
    ) -> BusinessComponent:
        """Add a custom component to track."""
        state = self.load()

        comp = BusinessComponent(
            name=name,
            category=category,
            description=description,
        )
        state.components.append(comp)
        self.save()

        return comp

    # =========================================================================
    # Hypothesis/Task Tracking
    # =========================================================================

    def add_hypothesis(self, hypothesis: dict):
        """Track a new hypothesis."""
        state = self.load()
        state.active_hypotheses.append({
            **hypothesis,
            "added_at": datetime.utcnow().isoformat(),
        })
        self.save()

    def complete_hypothesis(self, hypothesis_id: str, success: bool = True):
        """Mark hypothesis as completed."""
        state = self.load()

        for i, hyp in enumerate(state.active_hypotheses):
            if hyp.get("id") == hypothesis_id:
                hyp["completed_at"] = datetime.utcnow().isoformat()
                hyp["success"] = success
                state.completed_hypotheses.append(hyp)
                state.active_hypotheses.pop(i)
                break

        self.save()

    def add_task(self, task: dict):
        """Track a new task."""
        state = self.load()
        state.active_tasks.append({
            **task,
            "added_at": datetime.utcnow().isoformat(),
        })
        self.save()

    def complete_task(self, task_id: str, success: bool = True, result: dict = None):
        """Mark task as completed."""
        state = self.load()

        for i, task in enumerate(state.active_tasks):
            if task.get("id") == task_id:
                task["completed_at"] = datetime.utcnow().isoformat()
                task["success"] = success
                if result:
                    task["result"] = result
                state.completed_tasks.append(task)
                state.active_tasks.pop(i)
                break

        self.save()

    # =========================================================================
    # Inference from Tasks
    # =========================================================================

    def infer_component_from_task(self, task: dict) -> Optional[str]:
        """
        Infer which component a task relates to based on description.

        Returns category name or None.
        """
        desc = task.get("description", "").lower()

        # Payment keywords
        if any(kw in desc for kw in ["stripe", "payment", "checkout", "billing", "pricing"]):
            return "payment"

        # Channel keywords
        if any(kw in desc for kw in ["youtube", "blog", "content", "marketing", "seo", "ads", "email", "newsletter"]):
            return "channel"

        # Fulfillment keywords
        if any(kw in desc for kw in ["delivery", "access", "onboarding", "welcome", "enrollment"]):
            return "fulfillment"

        # Product keywords (default if building something)
        if any(kw in desc for kw in ["build", "create", "implement", "feature", "product"]):
            return "product"

        return None

    def auto_update_from_task(self, task: dict, success: bool):
        """
        Automatically update component status based on completed task.
        """
        if not success:
            return

        category = self.infer_component_from_task(task)
        if category is None:
            return

        state = self.load()
        comp = state.get_component(category)

        if comp is None:
            return

        # Progress the component status
        if comp.status == ComponentStatus.MISSING:
            comp.status = ComponentStatus.BUILDING
        elif comp.status == ComponentStatus.PLANNED:
            comp.status = ComponentStatus.BUILDING
        # Don't auto-promote to LIVE - that should be explicit or after validation

        comp.task_ids.append(task.get("id", "unknown"))
        self.save()

    # =========================================================================
    # Summary for Display
    # =========================================================================

    def get_summary(self) -> dict:
        """Get summary for display in dashboard/CLI."""
        state = self.load()

        return {
            "mode": state.mode.value,
            "completeness": state.completeness_score(),
            "can_generate_revenue": state.can_generate_revenue()[0],
            "revenue_capability": state.get_revenue_capability(),
            "components": [
                {
                    "name": c.name,
                    "category": c.category,
                    "status": c.status.value,
                    "description": c.description,
                }
                for c in state.components
            ],
            "active_hypotheses": len(state.active_hypotheses),
            "completed_hypotheses": len(state.completed_hypotheses),
            "active_tasks": len(state.active_tasks),
            "completed_tasks": len(state.completed_tasks),
        }
