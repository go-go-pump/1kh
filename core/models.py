"""
Core data models for ThousandHand.

These models represent the key data structures used throughout the system.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class BranchStatus(str, Enum):
    """Status of a branch in the tree."""
    PROPOSED = "proposed"
    BUILDING = "building"
    ACTIVE = "active"
    HEALTHY = "healthy"
    UNDERPERFORMING = "underperforming"
    FAILING = "failing"
    PRUNE_PENDING = "prune_pending"
    PRUNED = "pruned"
    ARCHIVED = "archived"


class TaskType(str, Enum):
    """Types of tasks that can be executed."""
    EXPLORE = "explore"
    BUILD = "build"
    TEST = "test"
    PRUNE = "prune"


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class EscalationTier(str, Enum):
    """Urgency tier for escalations."""
    BLOCKING = "blocking"  # System waits for response
    ADVISORY = "advisory"  # Wants input, has default
    FYI = "fyi"  # Informational only


class HypothesisStatus(str, Enum):
    """Status of a hypothesis."""
    PROPOSED = "proposed"
    BUILDING = "building"
    TESTABLE = "testable"
    MEASURING = "measuring"
    EVALUATING = "evaluating"
    VALIDATED = "validated"
    INVALIDATED = "invalidated"
    PIVOT_SYSTEM = "pivot_system"
    PIVOT_HYPOTHESIS = "pivot_hypothesis"
    RETIRED = "retired"
    OPERATIONALIZED = "operationalized"


class CommunicationChannel(str, Enum):
    """Preferred communication channels."""
    CLI = "cli"
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"


class SystemType(str, Enum):
    """
    Type of system being built.

    BIZ = Maximizing owner satisfaction (revenue, profit, KPIs)
    USER = Maximizing user utility/fulfillment

    A USER SYSTEM can exist without a BIZ SYSTEM (open source, hobby).
    A BIZ SYSTEM cannot exist without at least one USER SYSTEM.
    """
    BIZ = "biz"      # Business system - revenue/profit driven
    USER = "user"    # User system - utility/value driven


class NorthStarType(str, Enum):
    """
    Type of North Star objective.

    Determines what kind of metrics and hypothesis generation is appropriate.
    """
    REVENUE = "revenue"          # $X ARR, $Y MRR, etc.
    PROFIT = "profit"            # $X profit margin
    USERS = "users"              # N active users
    ENGAGEMENT = "engagement"    # Time spent, sessions, etc.
    UTILITY = "utility"          # Feature completeness, user satisfaction
    LEARNING = "learning"        # Personal skill development
    PORTFOLIO = "portfolio"      # Demonstrable work/showcase
    CUSTOM = "custom"            # User-defined metric


# ============================================================================
# Foundation Models (from Initial Ceremony)
# ============================================================================

class Oracle(BaseModel):
    """
    Immutable values and principles.
    The system will NEVER violate these.
    """
    version: str = "1.0"
    values: list[str] = Field(default_factory=list)
    never_do: list[str] = Field(default_factory=list)
    always_do: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NorthStar(BaseModel):
    """
    Measurable, time-bound objectives.
    What success looks like.
    """
    version: str = "1.0"
    north_star_type: Optional[NorthStarType] = None  # What KIND of goal
    objectives: list[dict[str, Any]] = Field(default_factory=list)
    deadline: Optional[datetime] = None
    success_metrics: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Context(BaseModel):
    """
    Constraints and resources.
    What we have to work with.
    """
    budget_monthly: Optional[float] = None
    budget_total: Optional[float] = None
    time_weekly_hours: Optional[float] = None
    existing_assets: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class Seed(BaseModel):
    """
    A hunch or idea to be explored.
    Becomes a hypothesis after IMAGINATION processes it.
    """
    id: str
    description: str
    source: str = "human"  # or "system"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Preferences(BaseModel):
    """
    Soft constraints that influence decisions.
    """
    communication_channel: CommunicationChannel = CommunicationChannel.EMAIL
    update_frequency: str = "daily"
    risk_tolerance: str = "medium"  # low, medium, high
    custom: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Ceremony State (for Initial Ceremony)
# ============================================================================

class CeremonyState(BaseModel):
    """
    State tracked during the Initial Ceremony.
    """
    project_path: str
    project_name: str
    phase: int = 0
    raw_input: str = ""
    system_type: Optional[SystemType] = None  # BIZ or USER system
    oracle: Optional[Oracle] = None
    north_star: Optional[NorthStar] = None
    context: Optional[Context] = None
    seeds: list[Seed] = Field(default_factory=list)
    preferences: Preferences = Field(default_factory=Preferences)
    api_keys_collected: dict[str, bool] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Runtime Models
# ============================================================================

class Hypothesis(BaseModel):
    """
    A testable belief about how to achieve North Star.
    """
    id: str
    statement: str
    north_star_ref: str
    oracle_alignment: list[str] = Field(default_factory=list)
    expected_outcomes: dict[str, Any] = Field(default_factory=dict)
    minimum_viable_outcome: dict[str, Any] = Field(default_factory=dict)
    requirements: list[dict[str, Any]] = Field(default_factory=list)
    viability_score: float = 0.0
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    experiment_start: Optional[datetime] = None
    experiment_duration_days: int = 30
    current_pivot: int = 0
    max_pivots: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Task(BaseModel):
    """
    A unit of work to be executed.
    """
    id: str
    type: TaskType
    description: str
    hypothesis_id: Optional[str] = None
    branch_id: Optional[str] = None
    requirements: list[str] = Field(default_factory=list)
    assigned_to: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    dependencies: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class Branch(BaseModel):
    """
    A set of workflows pursuing a specific hypothesis.
    """
    id: str
    name: str
    hypothesis_id: str
    workflows: list[str] = Field(default_factory=list)
    status: BranchStatus = BranchStatus.PROPOSED
    planted_at: datetime = Field(default_factory=datetime.utcnow)
    expected_fruit: dict[str, Any] = Field(default_factory=dict)
    actual_fruit: dict[str, Any] = Field(default_factory=dict)
    last_fruit_check: Optional[datetime] = None
    prune_reason: Optional[str] = None
    prune_blocked_by: list[str] = Field(default_factory=list)
    prune_deadline: Optional[datetime] = None


class Capability(BaseModel):
    """
    Something the system knows how to do.
    """
    id: str
    name: str
    confidence: float = 0.0
    proven_by: list[str] = Field(default_factory=list)
    attempted: list[str] = Field(default_factory=list)
    last_validated: Optional[datetime] = None
    failure_notes: Optional[str] = None
    workarounds: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class Escalation(BaseModel):
    """
    A request for human input.
    """
    id: str
    tier: EscalationTier
    source_loop: str
    summary: str
    context: dict[str, Any] = Field(default_factory=dict)
    options: list[dict[str, Any]] = Field(default_factory=list)
    default_if_no_response: Optional[str] = None
    default_after_hours: int = 48
    created_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None
    response: Optional[str] = None


class TreeState(BaseModel):
    """
    The current state of the entire system.
    """
    tree_id: str
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    oracle_version: str = "1.0"
    north_star_version: str = "1.0"
    roots_health: str = "unknown"
    trunk_health: str = "unknown"
    branches: list[Branch] = Field(default_factory=list)
    fruit_summary: dict[str, Any] = Field(default_factory=dict)
    soil: dict[str, Any] = Field(default_factory=dict)


class CapabilityRegistry(BaseModel):
    """
    What the system knows how to do.
    """
    capabilities: list[Capability] = Field(default_factory=list)
    decay_policy: dict[str, Any] = Field(
        default_factory=lambda: {
            "unused_days_before_confidence_decay": 30,
            "decay_rate_per_month": 0.10,
        }
    )
