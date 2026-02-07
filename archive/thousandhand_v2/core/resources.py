"""
Resource Management for ThousandHand.

This module handles:
1. Resource declarations - what files/APIs/services a task will touch
2. Resource locking - prevent concurrent access to same resources
3. Conflict detection - identify competing hypotheses early

Resources are things that can only be modified by one task at a time:
- Files in the project
- External APIs (limited by rate limits or state)
- Database tables/collections
- Deployment slots
- Human attention (for tasks requiring human input)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
import hashlib

logger = logging.getLogger("1kh.resources")


class ResourceType(str, Enum):
    """Types of resources that can be declared."""
    FILE = "file"           # Source code, config files, docs
    FILE_GLOB = "file_glob" # Pattern like "src/**/*.py"
    API = "api"             # External API endpoint
    DATABASE = "database"   # Database table or collection
    SERVICE = "service"     # External service (Stripe, AWS, etc.)
    DEPLOYMENT = "deployment"  # Deployment target (staging, prod)
    HUMAN = "human"         # Requires human attention
    BUDGET = "budget"       # Spending money


class LockStatus(str, Enum):
    """Status of a resource lock."""
    AVAILABLE = "available"
    LOCKED = "locked"
    QUEUED = "queued"       # Waiting for lock


@dataclass
class Resource:
    """
    A resource that a task will touch.

    Examples:
        Resource(type=ResourceType.FILE, identifier="src/main.py", access="write")
        Resource(type=ResourceType.API, identifier="stripe.com/v1/customers", access="write")
        Resource(type=ResourceType.FILE_GLOB, identifier="temporal/activities/*.py", access="write")
    """
    type: ResourceType
    identifier: str  # File path, API endpoint, service name, etc.
    access: str = "read"  # "read" or "write" - only write locks block

    @property
    def lock_key(self) -> str:
        """Unique key for this resource (only write access needs locking)."""
        if self.access == "read":
            return ""  # Reads don't need locks
        return f"{self.type.value}:{self.identifier}"

    def matches(self, other: "Resource") -> bool:
        """
        Check if this resource conflicts with another for locking purposes.

        Conflict rules:
        - Two reads NEVER conflict (multiple readers OK)
        - Read + Write NEVER conflict (in our simplified model, reads don't lock)
        - Two WRITES on the same resource DO conflict

        This means only write-write on the same resource returns True.
        """
        # Only write-write conflicts matter for locking
        if self.access != "write" or other.access != "write":
            return False

        # Both are writes - check if they target the same resource

        # Handle glob patterns (FILE_GLOB can match FILE)
        if self.type == ResourceType.FILE_GLOB or other.type == ResourceType.FILE_GLOB:
            # One is a glob, check if they're both file-related
            self_is_file = self.type in (ResourceType.FILE, ResourceType.FILE_GLOB)
            other_is_file = other.type in (ResourceType.FILE, ResourceType.FILE_GLOB)
            if not (self_is_file and other_is_file):
                return False

            from fnmatch import fnmatch
            # Determine which is the glob and which is the file
            if self.type == ResourceType.FILE_GLOB and other.type == ResourceType.FILE_GLOB:
                # Both are globs - check if they could overlap (conservative: assume yes if any overlap possible)
                # For now, just check if either matches the other's pattern
                return fnmatch(self.identifier, other.identifier) or fnmatch(other.identifier, self.identifier)
            elif self.type == ResourceType.FILE_GLOB:
                return fnmatch(other.identifier, self.identifier)
            else:
                return fnmatch(self.identifier, other.identifier)

        # Non-glob: types must match exactly
        if self.type != other.type:
            return False

        # Exact identifier match
        return self.identifier == other.identifier


@dataclass
class ResourceDeclaration:
    """
    A complete declaration of resources for a task or hypothesis.

    Tasks MUST declare what they'll touch BEFORE execution.
    This enables conflict detection and prevents spaghetti code.
    """
    task_id: str  # or hypothesis_id
    resources: list[Resource] = field(default_factory=list)
    declared_at: datetime = field(default_factory=datetime.utcnow)

    def get_write_resources(self) -> list[Resource]:
        """Get only resources that require write access."""
        return [r for r in self.resources if r.access == "write"]

    def conflicts_with(self, other: "ResourceDeclaration") -> list[tuple[Resource, Resource]]:
        """
        Find conflicts between this declaration and another.

        Returns list of (our_resource, their_resource) tuples that conflict.
        """
        conflicts = []
        for our_res in self.get_write_resources():
            for their_res in other.get_write_resources():
                if our_res.matches(their_res):
                    conflicts.append((our_res, their_res))
        return conflicts

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "resources": [
                {"type": r.type.value, "identifier": r.identifier, "access": r.access}
                for r in self.resources
            ],
            "declared_at": self.declared_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResourceDeclaration":
        return cls(
            task_id=data["task_id"],
            resources=[
                Resource(
                    type=ResourceType(r["type"]),
                    identifier=r["identifier"],
                    access=r.get("access", "read"),
                )
                for r in data.get("resources", [])
            ],
            declared_at=datetime.fromisoformat(data["declared_at"]) if "declared_at" in data else datetime.utcnow(),
        )


@dataclass
class ResourceLock:
    """
    An active lock on a resource.
    """
    resource: Resource
    holder_task_id: str
    acquired_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # None = held until released

    def to_dict(self) -> dict:
        return {
            "resource": {
                "type": self.resource.type.value,
                "identifier": self.resource.identifier,
                "access": self.resource.access,
            },
            "holder_task_id": self.holder_task_id,
            "acquired_at": self.acquired_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class ResourceQueue:
    """
    Manages resource locks and task queuing.

    Key principles:
    1. Tasks MUST declare resources before execution
    2. Only one task can hold a write lock on a resource
    3. Tasks wait in queue if resources are locked
    4. Sequential execution prevents merge conflicts
    """

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.state_file = project_path / ".1kh" / "resource_locks.json"
        self._locks: dict[str, ResourceLock] = {}
        self._queue: list[ResourceDeclaration] = []
        self._load_state()

    def _load_state(self):
        """Load lock state from disk."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self._locks = {}
                for lock_key, lock_data in data.get("locks", {}).items():
                    resource = Resource(
                        type=ResourceType(lock_data["resource"]["type"]),
                        identifier=lock_data["resource"]["identifier"],
                        access=lock_data["resource"]["access"],
                    )
                    self._locks[lock_key] = ResourceLock(
                        resource=resource,
                        holder_task_id=lock_data["holder_task_id"],
                        acquired_at=datetime.fromisoformat(lock_data["acquired_at"]),
                        expires_at=datetime.fromisoformat(lock_data["expires_at"]) if lock_data.get("expires_at") else None,
                    )
                self._queue = [
                    ResourceDeclaration.from_dict(d)
                    for d in data.get("queue", [])
                ]
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load resource state: {e}")
                self._locks = {}
                self._queue = []

    def _save_state(self):
        """Save lock state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "locks": {k: v.to_dict() for k, v in self._locks.items()},
            "queue": [d.to_dict() for d in self._queue],
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.state_file.write_text(json.dumps(data, indent=2))

    def can_acquire(self, declaration: ResourceDeclaration) -> tuple[bool, list[str]]:
        """
        Check if a task can acquire all its declared resources.

        Returns:
            (can_acquire, list of blocking task IDs)
        """
        blocking_tasks = set()

        for resource in declaration.get_write_resources():
            lock_key = resource.lock_key
            if lock_key in self._locks:
                lock = self._locks[lock_key]
                # Check if lock expired
                if lock.expires_at and datetime.utcnow() > lock.expires_at:
                    continue  # Lock expired, can acquire
                if lock.holder_task_id != declaration.task_id:
                    blocking_tasks.add(lock.holder_task_id)

            # Also check for glob conflicts
            for existing_key, existing_lock in self._locks.items():
                if existing_lock.holder_task_id == declaration.task_id:
                    continue
                if resource.matches(existing_lock.resource):
                    if existing_lock.expires_at and datetime.utcnow() > existing_lock.expires_at:
                        continue
                    blocking_tasks.add(existing_lock.holder_task_id)

        return len(blocking_tasks) == 0, list(blocking_tasks)

    def acquire(self, declaration: ResourceDeclaration) -> bool:
        """
        Attempt to acquire locks for all declared resources.

        Returns True if successful, False if blocked.
        """
        can_acquire, blockers = self.can_acquire(declaration)
        if not can_acquire:
            logger.info(f"Task {declaration.task_id} blocked by: {blockers}")
            return False

        # Acquire all locks
        for resource in declaration.get_write_resources():
            lock_key = resource.lock_key
            self._locks[lock_key] = ResourceLock(
                resource=resource,
                holder_task_id=declaration.task_id,
            )

        self._save_state()
        logger.info(f"Task {declaration.task_id} acquired {len(declaration.get_write_resources())} locks")
        return True

    def release(self, task_id: str):
        """
        Release all locks held by a task.
        """
        released = []
        for lock_key in list(self._locks.keys()):
            if self._locks[lock_key].holder_task_id == task_id:
                released.append(lock_key)
                del self._locks[lock_key]

        if released:
            self._save_state()
            logger.info(f"Task {task_id} released {len(released)} locks")

    def enqueue(self, declaration: ResourceDeclaration):
        """Add a task to the queue if it can't acquire immediately."""
        can_acquire, _ = self.can_acquire(declaration)
        if can_acquire:
            self.acquire(declaration)
        else:
            self._queue.append(declaration)
            self._save_state()
            logger.info(f"Task {declaration.task_id} added to queue (position {len(self._queue)})")

    def process_queue(self) -> list[str]:
        """
        Process the queue and start tasks that can now run.

        Returns list of task IDs that were started.
        """
        started = []
        remaining_queue = []

        for declaration in self._queue:
            can_acquire, _ = self.can_acquire(declaration)
            if can_acquire:
                self.acquire(declaration)
                started.append(declaration.task_id)
            else:
                remaining_queue.append(declaration)

        self._queue = remaining_queue
        if started:
            self._save_state()

        return started

    def get_active_locks(self) -> list[dict]:
        """Get all active locks for display."""
        return [
            {
                "resource": lock.resource.identifier,
                "type": lock.resource.type.value,
                "holder": lock.holder_task_id,
                "acquired_at": lock.acquired_at.isoformat(),
            }
            for lock in self._locks.values()
        ]

    def get_queue_status(self) -> list[dict]:
        """Get queue status for display."""
        return [
            {
                "task_id": d.task_id,
                "resources": len(d.resources),
                "write_resources": len(d.get_write_resources()),
                "declared_at": d.declared_at.isoformat(),
            }
            for d in self._queue
        ]


def detect_hypothesis_conflicts(
    hypotheses: list[dict],
) -> dict[str, list[dict]]:
    """
    Detect conflicts between hypotheses based on their declared resources.

    This is called during IMAGINATION/INTENT to flag competing hypotheses
    BEFORE they become tasks.

    Returns:
        Dict mapping hypothesis ID to list of conflicts:
        {
            "hyp-001": [
                {"with": "hyp-002", "resources": ["src/api.py"]},
            ]
        }
    """
    conflicts = {}

    for i, hyp1 in enumerate(hypotheses):
        hyp1_id = hyp1.get("id", f"hyp-{i}")
        hyp1_resources = hyp1.get("touches_resources", [])

        if not hyp1_resources:
            continue

        for j, hyp2 in enumerate(hypotheses):
            if j <= i:  # Skip self and already-checked pairs
                continue

            hyp2_id = hyp2.get("id", f"hyp-{j}")
            hyp2_resources = hyp2.get("touches_resources", [])

            if not hyp2_resources:
                continue

            # Find overlapping write resources
            overlapping = []
            for r1 in hyp1_resources:
                if r1.get("access") != "write":
                    continue
                for r2 in hyp2_resources:
                    if r2.get("access") != "write":
                        continue
                    if r1.get("identifier") == r2.get("identifier"):
                        overlapping.append(r1.get("identifier"))
                    # Check glob patterns
                    if r1.get("type") == "file_glob" or r2.get("type") == "file_glob":
                        from fnmatch import fnmatch
                        glob = r1.get("identifier") if r1.get("type") == "file_glob" else r2.get("identifier")
                        path = r2.get("identifier") if r1.get("type") == "file_glob" else r1.get("identifier")
                        if fnmatch(path, glob):
                            overlapping.append(f"{glob} ↔ {path}")

            if overlapping:
                if hyp1_id not in conflicts:
                    conflicts[hyp1_id] = []
                if hyp2_id not in conflicts:
                    conflicts[hyp2_id] = []

                conflicts[hyp1_id].append({
                    "with": hyp2_id,
                    "resources": overlapping,
                })
                conflicts[hyp2_id].append({
                    "with": hyp1_id,
                    "resources": overlapping,
                })

    return conflicts


def suggest_execution_order(
    hypotheses: list[dict],
    conflicts: dict[str, list[dict]],
) -> list[str]:
    """
    Suggest an execution order that minimizes conflicts.

    Uses a simple greedy approach:
    1. Start with hypothesis that has most dependencies (others depend on it)
    2. Add hypotheses that don't conflict with already-added ones
    3. Repeat until all added

    Returns ordered list of hypothesis IDs.
    """
    if not hypotheses:
        return []

    # Build dependency graph
    remaining = {h.get("id", f"hyp-{i}"): h for i, h in enumerate(hypotheses)}
    ordered = []

    # Score each hypothesis by how many others depend on it
    def blocker_score(hyp_id: str) -> int:
        hyp = remaining.get(hyp_id, {})
        blocks = hyp.get("blocks", [])
        return len(blocks)

    while remaining:
        # Find hypothesis with highest blocker score that doesn't conflict with ordered
        best = None
        best_score = -1

        for hyp_id in remaining:
            # Check if this conflicts with already-ordered items
            has_conflict = False
            for ordered_id in ordered:
                if hyp_id in conflicts and any(c["with"] == ordered_id for c in conflicts[hyp_id]):
                    has_conflict = True
                    break

            score = blocker_score(hyp_id)
            if not has_conflict and score > best_score:
                best = hyp_id
                best_score = score

        if best is None:
            # All remaining have conflicts, just take the first one
            best = next(iter(remaining))

        ordered.append(best)
        del remaining[best]

    return ordered
