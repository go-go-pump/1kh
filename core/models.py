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


class UtilitySubtype(str, Enum):
    """
    Subtype of USER SYSTEM utility.

    Different utility types naturally gravitate toward different KPIs.
    This helps the system suggest appropriate metrics early.

    Organized by category:
    - Infrastructure: MULTI_TENANT, ORCHESTRATOR, API_GATEWAY, AUTH_SERVICE, MONITORING
    - Data: DATA_PIPELINE, SEARCH, MIGRATION, SCRAPER
    - Compute: SCHEDULER, AUTOMATION, ML_MODEL, SIMULATOR
    - Developer: LIBRARY, CLI, WEBHOOK_HANDLER
    - Content: CONTENT_GENERATOR, NOTIFICATION
    - General: POC, INTERNAL_TOOL, CUSTOM
    """
    # General
    POC = "poc"                          # Proof of concept - "IT JUST WORKS"
    INTERNAL_TOOL = "internal_tool"      # Productivity - task completion, time saved
    CUSTOM = "custom"                    # User-defined

    # Infrastructure
    MULTI_TENANT = "multi_tenant"        # Shared service - reliability, isolation
    ORCHESTRATOR = "orchestrator"        # Service manager - config, visibility
    API_GATEWAY = "api_gateway"          # Integration/routing - latency, error rate
    AUTH_SERVICE = "auth_service"        # Identity/access - auth latency, security
    MONITORING = "monitoring"            # Observability - alert accuracy, freshness

    # Data
    DATA_PIPELINE = "data_pipeline"      # ETL/streaming - throughput, accuracy
    SEARCH = "search"                    # Indexing/retrieval - query latency, relevance
    MIGRATION = "migration"              # Data/schema migration - zero loss, duration
    SCRAPER = "scraper"                  # Data collection - success rate, freshness

    # Compute
    SCHEDULER = "scheduler"              # Event-driven - timing, throughput
    AUTOMATION = "automation"            # Workflow - success rate, error handling
    ML_MODEL = "ml_model"                # Machine learning - accuracy, inference latency
    SIMULATOR = "simulator"              # Testing/modeling - accuracy, speed

    # Developer
    LIBRARY = "library"                  # SDK/API - clarity, integration ease
    CLI = "cli"                          # Command line tool - execution success, speed
    WEBHOOK_HANDLER = "webhook_handler"  # Event ingestion - processing latency, retry

    # Content
    CONTENT_GENERATOR = "content_generator"  # AI/media content - quality, generation time
    NOTIFICATION = "notification"        # Alerts/messaging - delivery rate, latency


# Suggested metrics for each utility subtype
UTILITY_SUBTYPE_METRICS: dict[UtilitySubtype, dict] = {
    # =========================================================================
    # GENERAL
    # =========================================================================
    UtilitySubtype.POC: {
        "category": "General",
        "description": "Proof of Concept - Binary success",
        "primary_kpi": "Feature checklist completion",
        "suggested_metrics": [
            "Core feature complete (yes/no)",
            "Demo-able to stakeholders (yes/no)",
            "Known limitations documented",
        ],
        "hypothesis_driven": False,
    },
    UtilitySubtype.INTERNAL_TOOL: {
        "category": "General",
        "description": "Internal Tool - Productivity",
        "primary_kpi": "Task completion and time saved",
        "suggested_metrics": [
            "Tasks completed per session",
            "Time saved vs manual process",
            "Error rate in task completion",
            "User satisfaction score",
        ],
        "hypothesis_driven": False,
    },
    UtilitySubtype.CUSTOM: {
        "category": "General",
        "description": "Custom utility type",
        "primary_kpi": "User-defined",
        "suggested_metrics": [],
        "hypothesis_driven": False,
    },

    # =========================================================================
    # INFRASTRUCTURE
    # =========================================================================
    UtilitySubtype.MULTI_TENANT: {
        "category": "Infrastructure",
        "description": "Multi-tenant/Shared Service - Reliability & Isolation",
        "primary_kpi": "Service reliability and tenant isolation",
        "suggested_metrics": [
            "Uptime percentage (target: 99.9%)",
            "P95 latency (target: <Xms)",
            "Zero cross-tenant data leaks",
            "Tenant onboarding time",
            "Error rate per tenant",
        ],
        "hypothesis_driven": True,
    },
    UtilitySubtype.ORCHESTRATOR: {
        "category": "Infrastructure",
        "description": "Service Manager/Orchestrator - Visibility & Control",
        "primary_kpi": "Configuration ability and system visibility",
        "suggested_metrics": [
            "Services manageable via config",
            "Dashboard visibility coverage",
            "Time to deploy new service",
            "Config change propagation time",
            "Interface response time",
        ],
        "hypothesis_driven": True,
    },
    UtilitySubtype.API_GATEWAY: {
        "category": "Infrastructure",
        "description": "API Gateway - Routing & Integration",
        "primary_kpi": "Request latency and reliability",
        "suggested_metrics": [
            "P50/P95/P99 request latency",
            "Error rate (4xx, 5xx)",
            "Rate limiting effectiveness",
            "Upstream service availability",
            "Request throughput (req/sec)",
        ],
        "hypothesis_driven": True,
    },
    UtilitySubtype.AUTH_SERVICE: {
        "category": "Infrastructure",
        "description": "Auth Service - Identity & Access",
        "primary_kpi": "Authentication speed and security",
        "suggested_metrics": [
            "Auth request latency (P95)",
            "False rejection rate",
            "Token validation speed",
            "Security audit compliance",
            "Session management accuracy",
        ],
        "hypothesis_driven": True,
    },
    UtilitySubtype.MONITORING: {
        "category": "Infrastructure",
        "description": "Monitoring/Observability - Visibility & Alerting",
        "primary_kpi": "Alert accuracy and data freshness",
        "suggested_metrics": [
            "Alert true positive rate",
            "Mean time to detect (MTTD)",
            "Dashboard load time",
            "Data lag/freshness",
            "Coverage of monitored systems",
        ],
        "hypothesis_driven": True,
    },

    # =========================================================================
    # DATA
    # =========================================================================
    UtilitySubtype.DATA_PIPELINE: {
        "category": "Data",
        "description": "Data Pipeline - Throughput & Accuracy",
        "primary_kpi": "Data throughput and accuracy",
        "suggested_metrics": [
            "Records processed per second",
            "Data accuracy rate",
            "Pipeline latency (end-to-end)",
            "Failed record handling rate",
            "Backfill completion time",
        ],
        "hypothesis_driven": True,
    },
    UtilitySubtype.SEARCH: {
        "category": "Data",
        "description": "Search Engine - Retrieval & Relevance",
        "primary_kpi": "Query speed and result relevance",
        "suggested_metrics": [
            "Query latency (P50, P95)",
            "Relevance score (precision/recall)",
            "Index freshness",
            "Query success rate",
            "Zero-result rate",
        ],
        "hypothesis_driven": True,
    },
    UtilitySubtype.MIGRATION: {
        "category": "Data",
        "description": "Migration Tool - Data Integrity & Speed",
        "primary_kpi": "Zero data loss and migration speed",
        "suggested_metrics": [
            "Data integrity (zero loss)",
            "Migration duration",
            "Rollback success rate",
            "Downtime during migration",
            "Validation pass rate",
        ],
        "hypothesis_driven": False,  # Usually one-shot
    },
    UtilitySubtype.SCRAPER: {
        "category": "Data",
        "description": "Scraper/Collector - Data Freshness & Coverage",
        "primary_kpi": "Collection success rate and freshness",
        "suggested_metrics": [
            "Scrape success rate",
            "Data freshness (time since last update)",
            "Coverage (% of target sources)",
            "Error/retry rate",
            "Rate limit compliance",
        ],
        "hypothesis_driven": True,
    },

    # =========================================================================
    # COMPUTE
    # =========================================================================
    UtilitySubtype.SCHEDULER: {
        "category": "Compute",
        "description": "Scheduler/Event-driven - Timing & Throughput",
        "primary_kpi": "Event accuracy and throughput",
        "suggested_metrics": [
            "Schedule accuracy (% on-time)",
            "Event throughput (events/sec)",
            "Queue depth / backlog",
            "Failed event retry success rate",
            "End-to-end event latency",
        ],
        "hypothesis_driven": True,
    },
    UtilitySubtype.AUTOMATION: {
        "category": "Compute",
        "description": "Automation/Workflow - Success Rate",
        "primary_kpi": "Workflow success rate and error handling",
        "suggested_metrics": [
            "Workflow success rate (%)",
            "Mean time to recovery (MTTR)",
            "Manual intervention rate",
            "End-to-end completion time",
        ],
        "hypothesis_driven": True,
    },
    UtilitySubtype.ML_MODEL: {
        "category": "Compute",
        "description": "ML Model - Accuracy & Performance",
        "primary_kpi": "Model accuracy and inference speed",
        "suggested_metrics": [
            "Model accuracy/F1/AUC (task-specific)",
            "Inference latency (P95)",
            "Training time",
            "Data drift detection",
            "Model staleness",
        ],
        "hypothesis_driven": True,
    },
    UtilitySubtype.SIMULATOR: {
        "category": "Compute",
        "description": "Simulator/Mock - Accuracy & Speed",
        "primary_kpi": "Simulation accuracy and execution speed",
        "suggested_metrics": [
            "Accuracy vs real system",
            "Simulation execution time",
            "Scenario coverage",
            "Edge case handling",
            "Reproducibility",
        ],
        "hypothesis_driven": False,  # Usually feature-driven
    },

    # =========================================================================
    # DEVELOPER
    # =========================================================================
    UtilitySubtype.LIBRARY: {
        "category": "Developer",
        "description": "Library/SDK - Developer Experience",
        "primary_kpi": "API clarity and integration ease",
        "suggested_metrics": [
            "Time to first successful API call",
            "Documentation coverage",
            "Breaking changes per release",
            "Integration test pass rate",
        ],
        "hypothesis_driven": False,
    },
    UtilitySubtype.CLI: {
        "category": "Developer",
        "description": "CLI Tool - Usability & Speed",
        "primary_kpi": "Command execution success and speed",
        "suggested_metrics": [
            "Command execution success rate",
            "Average command response time",
            "Error message clarity score",
            "Documentation/help coverage",
            "Shell completion coverage",
        ],
        "hypothesis_driven": False,
    },
    UtilitySubtype.WEBHOOK_HANDLER: {
        "category": "Developer",
        "description": "Webhook Handler - Event Processing",
        "primary_kpi": "Event processing reliability and speed",
        "suggested_metrics": [
            "Event processing latency",
            "Retry success rate",
            "Dead letter queue size",
            "Idempotency compliance",
            "Acknowledgment rate",
        ],
        "hypothesis_driven": True,
    },

    # =========================================================================
    # CONTENT
    # =========================================================================
    UtilitySubtype.CONTENT_GENERATOR: {
        "category": "Content",
        "description": "Content Generator - Quality & Speed",
        "primary_kpi": "Content quality and generation speed",
        "suggested_metrics": [
            "Content quality score",
            "Generation time",
            "Output consistency",
            "Human edit rate",
            "Rejection/redo rate",
        ],
        "hypothesis_driven": True,
    },
    UtilitySubtype.NOTIFICATION: {
        "category": "Content",
        "description": "Notification Service - Delivery & Speed",
        "primary_kpi": "Message delivery rate and latency",
        "suggested_metrics": [
            "Delivery success rate",
            "Delivery latency (P95)",
            "Bounce/failure rate",
            "Channel coverage",
            "Unsubscribe rate",
        ],
        "hypothesis_driven": True,
    },
}


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
    utility_subtype: Optional[UtilitySubtype] = None  # For USER systems: what KIND of utility
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
