"""
Tests for core/resources.py - Resource locking and conflict detection.

This is critical infrastructure that prevents "spaghetti code" from
competing hypotheses. These tests ensure:

1. Resources correctly identify conflicts
2. Locks are acquired and released properly
3. Queue processing works correctly
4. Conflict detection catches overlapping hypotheses
5. Execution ordering minimizes conflicts
"""
import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta

# Import the module under test
from core.resources import (
    Resource,
    ResourceType,
    ResourceDeclaration,
    ResourceLock,
    ResourceQueue,
    LockStatus,
    detect_hypothesis_conflicts,
    suggest_execution_order,
)


# =============================================================================
# Resource Matching Tests
# =============================================================================

class TestResourceMatching:
    """Test Resource.matches() logic."""

    def test_same_file_write_conflicts(self, sample_resources):
        """Two write operations on same file should conflict."""
        r1 = sample_resources["file_write"]
        r2 = Resource(
            type=ResourceType.FILE,
            identifier="src/main.py",
            access="write",
        )
        assert r1.matches(r2) is True

    def test_read_read_no_conflict(self, sample_resources):
        """Two read operations on same file should NOT conflict."""
        r1 = sample_resources["file_read"]
        r2 = Resource(
            type=ResourceType.FILE,
            identifier="src/main.py",
            access="read",
        )
        assert r1.matches(r2) is False

    def test_read_write_no_conflict(self, sample_resources):
        """Read + Write on same file should NOT conflict for locking.

        Our model: reads don't acquire locks, so they never block.
        Only write-write conflicts matter for resource locking.
        """
        r1 = sample_resources["file_read"]
        r2 = sample_resources["file_write"]
        # In our locking model, reads don't participate in locking at all
        # A read never blocks a write, and a write never blocks a read
        # (This is a simplification - in practice we might want read/write locks)
        assert r1.matches(r2) is False  # Read doesn't block write
        assert r2.matches(r1) is False  # Write doesn't block read

    def test_different_files_no_conflict(self, sample_resources):
        """Different files should not conflict."""
        r1 = sample_resources["file_write"]
        r2 = sample_resources["file_other"]
        assert r1.matches(r2) is False

    def test_glob_matches_file(self, sample_resources):
        """Glob pattern should match files in pattern."""
        glob = sample_resources["glob_src"]
        file = sample_resources["file_write"]
        assert glob.matches(file) is True

    def test_glob_no_match_outside_pattern(self, sample_resources):
        """Glob should not match files outside pattern."""
        glob = sample_resources["glob_src"]
        outside = Resource(
            type=ResourceType.FILE,
            identifier="lib/other.py",
            access="write",
        )
        assert glob.matches(outside) is False

    def test_different_types_no_conflict(self, sample_resources):
        """Different resource types should not conflict."""
        file = sample_resources["file_write"]
        api = sample_resources["api_stripe"]
        assert file.matches(api) is False

    def test_lock_key_only_for_writes(self, sample_resources):
        """Lock key should be empty for read access."""
        read = sample_resources["file_read"]
        write = sample_resources["file_write"]
        assert read.lock_key == ""
        assert write.lock_key != ""
        assert write.lock_key == "file:src/main.py"


# =============================================================================
# ResourceDeclaration Tests
# =============================================================================

class TestResourceDeclaration:
    """Test ResourceDeclaration conflict detection."""

    def test_declarations_conflict_on_same_file(self, sample_resources):
        """Declarations writing same file should conflict."""
        d1 = ResourceDeclaration(
            task_id="task-1",
            resources=[sample_resources["file_write"]],
        )
        d2 = ResourceDeclaration(
            task_id="task-2",
            resources=[
                Resource(
                    type=ResourceType.FILE,
                    identifier="src/main.py",
                    access="write",
                )
            ],
        )
        conflicts = d1.conflicts_with(d2)
        assert len(conflicts) == 1

    def test_declarations_no_conflict_different_files(self, sample_resources):
        """Declarations writing different files should not conflict."""
        d1 = ResourceDeclaration(
            task_id="task-1",
            resources=[sample_resources["file_write"]],
        )
        d2 = ResourceDeclaration(
            task_id="task-2",
            resources=[sample_resources["file_other"]],
        )
        conflicts = d1.conflicts_with(d2)
        assert len(conflicts) == 0

    def test_get_write_resources(self, sample_resources):
        """get_write_resources should filter to only writes."""
        decl = ResourceDeclaration(
            task_id="task-1",
            resources=[
                sample_resources["file_read"],
                sample_resources["file_write"],
                sample_resources["file_other"],
            ],
        )
        writes = decl.get_write_resources()
        assert len(writes) == 2
        assert all(r.access == "write" for r in writes)

    def test_serialization_roundtrip(self, sample_resources):
        """Declaration should serialize and deserialize correctly."""
        original = ResourceDeclaration(
            task_id="task-1",
            resources=[
                sample_resources["file_write"],
                sample_resources["api_stripe"],
            ],
        )
        as_dict = original.to_dict()
        restored = ResourceDeclaration.from_dict(as_dict)

        assert restored.task_id == original.task_id
        assert len(restored.resources) == len(original.resources)
        assert restored.resources[0].identifier == original.resources[0].identifier


# =============================================================================
# ResourceQueue Tests
# =============================================================================

class TestResourceQueue:
    """Test ResourceQueue locking behavior."""

    def test_acquire_empty_queue(self, resource_queue, sample_resources):
        """Should acquire locks when queue is empty."""
        decl = ResourceDeclaration(
            task_id="task-1",
            resources=[sample_resources["file_write"]],
        )
        result = resource_queue.acquire(decl)
        assert result is True

    def test_acquire_blocks_on_conflict(self, resource_queue, sample_resources):
        """Second task should be blocked when resource is locked."""
        # First task acquires
        d1 = ResourceDeclaration(
            task_id="task-1",
            resources=[sample_resources["file_write"]],
        )
        resource_queue.acquire(d1)

        # Second task tries same resource
        d2 = ResourceDeclaration(
            task_id="task-2",
            resources=[
                Resource(
                    type=ResourceType.FILE,
                    identifier="src/main.py",
                    access="write",
                )
            ],
        )
        can_acquire, blockers = resource_queue.can_acquire(d2)
        assert can_acquire is False
        assert "task-1" in blockers

    def test_release_frees_resource(self, resource_queue, sample_resources):
        """After release, resource should be available."""
        decl = ResourceDeclaration(
            task_id="task-1",
            resources=[sample_resources["file_write"]],
        )
        resource_queue.acquire(decl)
        resource_queue.release("task-1")

        # Now task-2 should be able to acquire
        d2 = ResourceDeclaration(
            task_id="task-2",
            resources=[sample_resources["file_write"]],
        )
        can_acquire, _ = resource_queue.can_acquire(d2)
        assert can_acquire is True

    def test_enqueue_adds_to_queue(self, resource_queue, sample_resources):
        """Blocked task should be added to queue."""
        # First task acquires
        d1 = ResourceDeclaration(
            task_id="task-1",
            resources=[sample_resources["file_write"]],
        )
        resource_queue.acquire(d1)

        # Second task should be enqueued
        d2 = ResourceDeclaration(
            task_id="task-2",
            resources=[sample_resources["file_write"]],
        )
        resource_queue.enqueue(d2)

        status = resource_queue.get_queue_status()
        assert len(status) == 1
        assert status[0]["task_id"] == "task-2"

    def test_process_queue_starts_waiting_tasks(self, resource_queue, sample_resources):
        """After release, process_queue should start waiting tasks."""
        # Task 1 acquires
        d1 = ResourceDeclaration(
            task_id="task-1",
            resources=[sample_resources["file_write"]],
        )
        resource_queue.acquire(d1)

        # Task 2 enqueued
        d2 = ResourceDeclaration(
            task_id="task-2",
            resources=[sample_resources["file_write"]],
        )
        resource_queue.enqueue(d2)

        # Release task 1
        resource_queue.release("task-1")

        # Process queue
        started = resource_queue.process_queue()
        assert "task-2" in started

        # Queue should be empty now
        assert len(resource_queue.get_queue_status()) == 0

    def test_multiple_independent_tasks_can_run(self, resource_queue, sample_resources):
        """Tasks on different resources should both be able to run."""
        d1 = ResourceDeclaration(
            task_id="task-1",
            resources=[sample_resources["file_write"]],
        )
        d2 = ResourceDeclaration(
            task_id="task-2",
            resources=[sample_resources["file_other"]],
        )

        result1 = resource_queue.acquire(d1)
        result2 = resource_queue.acquire(d2)

        assert result1 is True
        assert result2 is True

    def test_state_persists_to_disk(self, resource_queue, sample_resources, temp_project):
        """Locks should persist across queue instances."""
        decl = ResourceDeclaration(
            task_id="task-1",
            resources=[sample_resources["file_write"]],
        )
        resource_queue.acquire(decl)

        # Create new queue instance
        new_queue = ResourceQueue(temp_project)
        locks = new_queue.get_active_locks()

        assert len(locks) == 1
        assert locks[0]["holder"] == "task-1"

    def test_glob_conflict_detection(self, resource_queue, sample_resources):
        """Glob patterns should conflict with matching files."""
        # Acquire glob lock
        d1 = ResourceDeclaration(
            task_id="task-1",
            resources=[sample_resources["glob_src"]],
        )
        resource_queue.acquire(d1)

        # Try to acquire file within glob
        d2 = ResourceDeclaration(
            task_id="task-2",
            resources=[sample_resources["file_write"]],  # src/main.py
        )
        can_acquire, blockers = resource_queue.can_acquire(d2)

        assert can_acquire is False
        assert "task-1" in blockers


# =============================================================================
# Hypothesis Conflict Detection Tests
# =============================================================================

class TestHypothesisConflictDetection:
    """Test detect_hypothesis_conflicts() function."""

    def test_detects_overlapping_resources(self):
        """Should detect when hypotheses write to same file."""
        hypotheses = [
            {
                "id": "hyp-001",
                "description": "Build auth",
                "touches_resources": [
                    {"type": "file", "identifier": "src/auth.py", "access": "write"},
                ],
            },
            {
                "id": "hyp-002",
                "description": "Refactor auth",
                "touches_resources": [
                    {"type": "file", "identifier": "src/auth.py", "access": "write"},
                ],
            },
        ]
        conflicts = detect_hypothesis_conflicts(hypotheses)

        assert "hyp-001" in conflicts
        assert "hyp-002" in conflicts
        assert any(c["with"] == "hyp-002" for c in conflicts["hyp-001"])

    def test_no_conflict_different_resources(self):
        """Should not detect conflict for different resources."""
        hypotheses = [
            {
                "id": "hyp-001",
                "description": "Build auth",
                "touches_resources": [
                    {"type": "file", "identifier": "src/auth.py", "access": "write"},
                ],
            },
            {
                "id": "hyp-002",
                "description": "Build API",
                "touches_resources": [
                    {"type": "file", "identifier": "src/api.py", "access": "write"},
                ],
            },
        ]
        conflicts = detect_hypothesis_conflicts(hypotheses)
        assert len(conflicts) == 0

    def test_read_access_no_conflict(self):
        """Read-only access should not cause conflicts."""
        hypotheses = [
            {
                "id": "hyp-001",
                "description": "Read config",
                "touches_resources": [
                    {"type": "file", "identifier": "config.py", "access": "read"},
                ],
            },
            {
                "id": "hyp-002",
                "description": "Also read config",
                "touches_resources": [
                    {"type": "file", "identifier": "config.py", "access": "read"},
                ],
            },
        ]
        conflicts = detect_hypothesis_conflicts(hypotheses)
        assert len(conflicts) == 0

    def test_empty_resources_no_conflict(self):
        """Hypotheses without resources should not conflict."""
        hypotheses = [
            {"id": "hyp-001", "description": "Research task"},
            {"id": "hyp-002", "description": "Another research"},
        ]
        conflicts = detect_hypothesis_conflicts(hypotheses)
        assert len(conflicts) == 0

    def test_glob_pattern_conflict(self):
        """Should detect glob pattern conflicts."""
        hypotheses = [
            {
                "id": "hyp-001",
                "description": "Refactor all activities",
                "touches_resources": [
                    {"type": "file_glob", "identifier": "temporal/activities/*.py", "access": "write"},
                ],
            },
            {
                "id": "hyp-002",
                "description": "Update imagination activity",
                "touches_resources": [
                    {"type": "file", "identifier": "temporal/activities/imagination.py", "access": "write"},
                ],
            },
        ]
        conflicts = detect_hypothesis_conflicts(hypotheses)

        # Should detect the glob conflict
        assert len(conflicts) > 0


# =============================================================================
# Execution Order Tests
# =============================================================================

class TestExecutionOrder:
    """Test suggest_execution_order() function."""

    def test_suggests_order_for_conflicts(self):
        """Should return all hypotheses in some order."""
        hypotheses = [
            {"id": "hyp-001", "blocks": ["hyp-002"]},
            {"id": "hyp-002", "blocks": []},
            {"id": "hyp-003", "blocks": []},
        ]
        conflicts = {}
        order = suggest_execution_order(hypotheses, conflicts)

        assert len(order) == 3
        assert set(order) == {"hyp-001", "hyp-002", "hyp-003"}

    def test_blockers_come_first(self):
        """Hypotheses that block others should come first."""
        hypotheses = [
            {"id": "hyp-001", "blocks": []},
            {"id": "hyp-002", "blocks": ["hyp-001", "hyp-003"]},
            {"id": "hyp-003", "blocks": []},
        ]
        conflicts = {}
        order = suggest_execution_order(hypotheses, conflicts)

        # hyp-002 blocks the most, should be first
        assert order[0] == "hyp-002"

    def test_empty_list_returns_empty(self):
        """Empty input should return empty output."""
        order = suggest_execution_order([], {})
        assert order == []

    def test_handles_conflicting_hypotheses(self):
        """Should still produce order even with conflicts."""
        hypotheses = [
            {"id": "hyp-001", "blocks": []},
            {"id": "hyp-002", "blocks": []},
        ]
        conflicts = {
            "hyp-001": [{"with": "hyp-002", "resources": ["src/main.py"]}],
            "hyp-002": [{"with": "hyp-001", "resources": ["src/main.py"]}],
        }
        order = suggest_execution_order(hypotheses, conflicts)

        # Should return both, in some order
        assert len(order) == 2
        assert set(order) == {"hyp-001", "hyp-002"}


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_release_nonexistent_task(self, resource_queue):
        """Releasing non-existent task should not error."""
        resource_queue.release("nonexistent-task")
        # Should not raise

    def test_acquire_same_task_twice(self, resource_queue, sample_resources):
        """Same task acquiring twice should succeed (idempotent)."""
        decl = ResourceDeclaration(
            task_id="task-1",
            resources=[sample_resources["file_write"]],
        )
        result1 = resource_queue.acquire(decl)
        result2 = resource_queue.acquire(decl)

        assert result1 is True
        assert result2 is True

    def test_corrupted_state_file(self, temp_project, sample_resources):
        """Should handle corrupted state file gracefully."""
        state_file = temp_project / ".1kh" / "resource_locks.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("not valid json {{{")

        # Should not crash, just start fresh
        queue = ResourceQueue(temp_project)
        decl = ResourceDeclaration(
            task_id="task-1",
            resources=[sample_resources["file_write"]],
        )
        result = queue.acquire(decl)
        assert result is True

    def test_unknown_resource_type_in_hypothesis(self):
        """Should handle unknown resource types in hypotheses."""
        hypotheses = [
            {
                "id": "hyp-001",
                "touches_resources": [
                    {"type": "unknown_type", "identifier": "foo", "access": "write"},
                ],
            },
        ]
        # Should not crash
        conflicts = detect_hypothesis_conflicts(hypotheses)
        # Just returns empty since can't match unknown types
        assert isinstance(conflicts, dict)
