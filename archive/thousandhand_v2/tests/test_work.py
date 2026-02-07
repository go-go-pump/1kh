"""
Tests for temporal/activities/work.py - Task creation and execution.

These tests verify:
1. Tasks are created correctly from hypotheses
2. Resource locking is applied during execution
3. Locks are released after completion (success or failure)
4. Blocked tasks are queued properly
5. Queue is processed after task completion
"""
import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.mocks.claude_client import MockAnthropicClient, MOCK_RESPONSES


# =============================================================================
# Task Creation Tests
# =============================================================================

class TestTaskCreation:
    """Test create_task activity."""

    def _get_foundation_docs(self):
        """Helper to create foundation docs for tests."""
        oracle = {"values": ["Quality"], "never_do": [], "always_do": []}
        context = {"budget": 100, "skills": ["Python"]}
        return oracle, context

    @pytest.mark.asyncio
    async def test_creates_task_from_hypothesis(self, temp_project):
        """Should create a task from a hypothesis."""
        from temporal.activities.work import create_task

        oracle, context = self._get_foundation_docs()

        hypothesis = {
            "id": "hyp-001",
            "description": "Build authentication system",
            "touches_resources": [
                {"type": "file", "identifier": "src/auth.py", "access": "write"},
            ],
        }

        mock_client = MockAnthropicClient(response_key="work_task_creation")

        with patch('anthropic.Anthropic', return_value=mock_client):
            task = await create_task(
                project_path=str(temp_project),
                hypothesis=hypothesis,
                oracle=oracle,
                context=context,
            )

        assert task is not None
        assert "id" in task
        assert "description" in task
        assert "hypothesis_id" in task
        assert task["hypothesis_id"] == "hyp-001"

    @pytest.mark.asyncio
    async def test_task_inherits_resources_from_hypothesis(self, temp_project):
        """Task should inherit resource declarations if not specified."""
        from temporal.activities.work import create_task

        oracle, context = self._get_foundation_docs()

        hypothesis = {
            "id": "hyp-002",
            "description": "Modify API",
            "touches_resources": [
                {"type": "file", "identifier": "src/api.py", "access": "write"},
                {"type": "api", "identifier": "external.com", "access": "read"},
            ],
        }

        # Response doesn't include resources
        mock_client = MockAnthropicClient(custom_response='''
```json
{
  "description": "Update API endpoint",
  "task_type": "build",
  "acceptance_criteria": ["Endpoint works"],
  "estimated_minutes": 30,
  "requires_human": false
}
```
''')

        with patch('anthropic.Anthropic', return_value=mock_client):
            task = await create_task(
                project_path=str(temp_project),
                hypothesis=hypothesis,
                oracle=oracle,
                context=context,
            )

        # Should have inherited from hypothesis
        assert "touches_resources" in task
        assert len(task["touches_resources"]) == 2

    @pytest.mark.asyncio
    async def test_task_includes_own_resources(self, temp_project):
        """Task should use its own resources if specified."""
        from temporal.activities.work import create_task

        oracle, context = self._get_foundation_docs()

        hypothesis = {
            "id": "hyp-003",
            "description": "Build feature",
            "touches_resources": [
                {"type": "file", "identifier": "src/old.py", "access": "write"},
            ],
        }

        mock_client = MockAnthropicClient(response_key="work_task_creation")

        with patch('anthropic.Anthropic', return_value=mock_client):
            task = await create_task(
                project_path=str(temp_project),
                hypothesis=hypothesis,
                oracle=oracle,
                context=context,
            )

        # Should have task-specific resources from mock response
        assert "touches_resources" in task

    @pytest.mark.asyncio
    async def test_task_has_required_fields(self, temp_project):
        """Created task should have all required fields."""
        from temporal.activities.work import create_task

        oracle, context = self._get_foundation_docs()

        hypothesis = {
            "id": "hyp-004",
            "description": "Test task",
        }

        mock_client = MockAnthropicClient(response_key="work_task_creation")

        with patch('anthropic.Anthropic', return_value=mock_client):
            task = await create_task(
                project_path=str(temp_project),
                hypothesis=hypothesis,
                oracle=oracle,
                context=context,
            )

        # Required fields
        assert "id" in task
        assert "description" in task
        assert "task_type" in task
        assert "status" in task
        assert task["status"] == "pending"


# =============================================================================
# Task Execution with Resource Locking Tests
# =============================================================================

class TestTaskExecutionWithLocking:
    """Test execute_task with resource locking."""

    @pytest.mark.asyncio
    async def test_acquires_locks_before_execution(self, temp_project):
        """Should acquire resource locks before executing."""
        from temporal.activities.work import execute_task
        from core.resources import ResourceQueue

        task = {
            "id": "task-001",
            "description": "Build something",
            "task_type": "research",
            "touches_resources": [
                {"type": "file", "identifier": "src/main.py", "access": "write"},
            ],
            "acceptance_criteria": ["Done"],
        }

        oracle = {"values": [], "never_do": [], "always_do": []}

        mock_client = MockAnthropicClient(response_key="work_research_result")

        with patch('anthropic.Anthropic', return_value=mock_client):
            result = await execute_task(
                project_path=str(temp_project),
                task=task,
                oracle=oracle,
            )

        # Task should complete
        assert result["status"] == "completed"

        # Locks should be released after completion
        queue = ResourceQueue(temp_project)
        locks = queue.get_active_locks()
        assert len(locks) == 0

    @pytest.mark.asyncio
    async def test_blocked_when_resource_locked(self, temp_project):
        """Should return blocked status if resources are locked."""
        from temporal.activities.work import execute_task
        from core.resources import ResourceQueue, ResourceDeclaration, Resource, ResourceType

        # Pre-lock the resource
        queue = ResourceQueue(temp_project)
        blocking_decl = ResourceDeclaration(
            task_id="blocker-task",
            resources=[
                Resource(
                    type=ResourceType.FILE,
                    identifier="src/main.py",
                    access="write",
                )
            ],
        )
        queue.acquire(blocking_decl)

        # Try to execute task that needs same resource
        task = {
            "id": "task-blocked",
            "description": "Want same resource",
            "task_type": "build",
            "touches_resources": [
                {"type": "file", "identifier": "src/main.py", "access": "write"},
            ],
            "acceptance_criteria": [],
        }

        oracle = {}

        result = await execute_task(
            project_path=str(temp_project),
            task=task,
            oracle=oracle,
        )

        assert result["status"] == "blocked"
        assert "blocked_by" in result
        assert "blocker-task" in result["blocked_by"]

    @pytest.mark.asyncio
    async def test_releases_locks_on_failure(self, temp_project):
        """Should release locks even if task fails."""
        from temporal.activities.work import execute_task
        from core.resources import ResourceQueue

        task = {
            "id": "task-will-fail",
            "description": "This will fail",
            "task_type": "build",
            "touches_resources": [
                {"type": "file", "identifier": "src/fail.py", "access": "write"},
            ],
            "acceptance_criteria": [],
        }

        oracle = {}

        # Use mock that raises exception
        mock_client = MockAnthropicClient()
        mock_client.set_error(Exception("API Error"))

        with patch('anthropic.Anthropic', return_value=mock_client):
            result = await execute_task(
                project_path=str(temp_project),
                task=task,
                oracle=oracle,
            )

        # Task should be failed
        assert result["status"] == "failed"

        # But locks should be released
        queue = ResourceQueue(temp_project)
        locks = queue.get_active_locks()
        # Should not have a lock for this task
        task_locks = [l for l in locks if l["holder"] == "task-will-fail"]
        assert len(task_locks) == 0

    @pytest.mark.asyncio
    async def test_processes_queue_after_completion(self, temp_project):
        """Should process queue after releasing locks."""
        from temporal.activities.work import execute_task
        from core.resources import ResourceQueue, ResourceDeclaration, Resource, ResourceType

        # Set up: task-1 has the lock, task-2 is queued
        queue = ResourceQueue(temp_project)

        # Simulate task-2 waiting
        waiting_decl = ResourceDeclaration(
            task_id="task-waiting",
            resources=[
                Resource(
                    type=ResourceType.FILE,
                    identifier="src/shared.py",
                    access="write",
                )
            ],
        )
        # First, lock it
        queue.acquire(ResourceDeclaration(
            task_id="task-running",
            resources=[
                Resource(
                    type=ResourceType.FILE,
                    identifier="src/shared.py",
                    access="write",
                )
            ],
        ))
        # Then enqueue waiter
        queue.enqueue(waiting_decl)

        # Verify queue has waiting task
        queue_status = queue.get_queue_status()
        assert len(queue_status) == 1

        # Now release and process
        queue.release("task-running")
        started = queue.process_queue()

        assert "task-waiting" in started

    @pytest.mark.asyncio
    async def test_task_requiring_human_releases_locks(self, temp_project):
        """Tasks requiring human should release locks."""
        from temporal.activities.work import execute_task
        from core.resources import ResourceQueue

        task = {
            "id": "task-human",
            "description": "Needs human",
            "task_type": "build",
            "requires_human": True,
            "human_reason": "Approval needed",
            "touches_resources": [
                {"type": "file", "identifier": "src/sensitive.py", "access": "write"},
            ],
            "acceptance_criteria": [],
        }

        oracle = {}

        result = await execute_task(
            project_path=str(temp_project),
            task=task,
            oracle=oracle,
        )

        assert result["status"] == "blocked"
        assert "escalation_reason" in result

        # Locks should be released
        queue = ResourceQueue(temp_project)
        locks = queue.get_active_locks()
        task_locks = [l for l in locks if l["holder"] == "task-human"]
        assert len(task_locks) == 0


# =============================================================================
# Task Type Handling Tests
# =============================================================================

class TestTaskTypeHandling:
    """Test different task type execution."""

    @pytest.mark.asyncio
    async def test_research_task(self, temp_project):
        """Research tasks should get research-specific prompt."""
        from temporal.activities.work import execute_task

        task = {
            "id": "task-research",
            "description": "Research best practices",
            "task_type": "research",
            "touches_resources": [],
            "acceptance_criteria": ["Summary provided"],
        }

        oracle = {}
        mock_client = MockAnthropicClient(response_key="work_research_result")

        with patch('anthropic.Anthropic', return_value=mock_client):
            result = await execute_task(
                project_path=str(temp_project),
                task=task,
                oracle=oracle,
            )

        assert result["status"] == "completed"
        assert "result" in result

        # Check prompt was research-oriented
        calls = mock_client.get_calls()
        prompt = calls[0]["kwargs"]["messages"][0]["content"]
        assert "research" in prompt.lower() or "Research" in prompt

    @pytest.mark.asyncio
    async def test_build_task(self, temp_project):
        """Build tasks should get build-specific prompt."""
        from temporal.activities.work import execute_task

        task = {
            "id": "task-build",
            "description": "Build new feature",
            "task_type": "build",
            "touches_resources": [],
            "acceptance_criteria": ["Feature works"],
        }

        oracle = {}
        mock_client = MockAnthropicClient(response_key="work_build_result")

        with patch('anthropic.Anthropic', return_value=mock_client):
            result = await execute_task(
                project_path=str(temp_project),
                task=task,
                oracle=oracle,
            )

        assert result["status"] == "completed"

        # Check prompt was build-oriented
        calls = mock_client.get_calls()
        prompt = calls[0]["kwargs"]["messages"][0]["content"]
        assert "build" in prompt.lower() or "Build" in prompt


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test error handling in work activities."""

    @pytest.mark.asyncio
    async def test_handles_missing_api_key(self, temp_project):
        """Should fail gracefully if no API key."""
        from temporal.activities.work import execute_task

        # Remove the .env file
        env_file = temp_project / ".1kh" / ".env"
        if env_file.exists():
            env_file.unlink()

        task = {
            "id": "task-no-key",
            "description": "No API key",
            "task_type": "research",
            "touches_resources": [],
            "acceptance_criteria": [],
        }

        oracle = {}

        # Clear environment too
        with patch.dict('os.environ', {}, clear=True):
            result = await execute_task(
                project_path=str(temp_project),
                task=task,
                oracle=oracle,
            )

        assert result["status"] == "failed"
        assert "error" in result
        assert "API" in result["error"] or "key" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_handles_api_error(self, temp_project):
        """Should handle API errors gracefully."""
        from temporal.activities.work import execute_task

        task = {
            "id": "task-api-error",
            "description": "API will fail",
            "task_type": "research",
            "touches_resources": [],
            "acceptance_criteria": [],
        }

        oracle = {}
        mock_client = MockAnthropicClient()
        mock_client.set_error(Exception("Rate limit exceeded"))

        with patch('anthropic.Anthropic', return_value=mock_client):
            result = await execute_task(
                project_path=str(temp_project),
                task=task,
                oracle=oracle,
            )

        assert result["status"] == "failed"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_task_without_resources_still_works(self, temp_project):
        """Tasks without resource declarations should still execute."""
        from temporal.activities.work import execute_task

        task = {
            "id": "task-no-resources",
            "description": "Simple research",
            "task_type": "research",
            # No touches_resources
            "acceptance_criteria": [],
        }

        oracle = {}
        mock_client = MockAnthropicClient(response_key="work_research_result")

        with patch('anthropic.Anthropic', return_value=mock_client):
            result = await execute_task(
                project_path=str(temp_project),
                task=task,
                oracle=oracle,
            )

        assert result["status"] == "completed"


# =============================================================================
# Integration Tests
# =============================================================================

class TestWorkIntegration:
    """Integration tests for work activities."""

    def _get_foundation_docs(self):
        """Helper to create foundation docs for tests."""
        oracle = {"values": ["Quality"], "never_do": [], "always_do": []}
        context = {"budget": 100, "skills": ["Python"]}
        return oracle, context

    @pytest.mark.asyncio
    async def test_create_then_execute_flow(self, temp_project):
        """Test full create → execute flow."""
        from temporal.activities.work import create_task, execute_task

        oracle, context = self._get_foundation_docs()

        hypothesis = {
            "id": "hyp-integration",
            "description": "Integration test hypothesis",
            "touches_resources": [
                {"type": "file", "identifier": "src/test.py", "access": "write"},
            ],
        }

        mock_client = MockAnthropicClient(response_sequence=[
            MOCK_RESPONSES["work_task_creation"],
            MOCK_RESPONSES["work_build_result"],
        ])

        with patch('anthropic.Anthropic', return_value=mock_client):
            # Create task
            task = await create_task(
                project_path=str(temp_project),
                hypothesis=hypothesis,
                oracle=oracle,
                context=context,
            )

            assert task["status"] == "pending"

            # Execute task
            result = await execute_task(
                project_path=str(temp_project),
                task=task,
                oracle=oracle,
            )

            assert result["status"] == "completed"
            assert "result" in result

    @pytest.mark.asyncio
    async def test_sequential_tasks_on_same_resource(self, temp_project):
        """Sequential tasks on same resource should work."""
        from temporal.activities.work import execute_task
        from core.resources import ResourceQueue

        oracle = {}

        # Task 1
        task1 = {
            "id": "task-seq-1",
            "description": "First task",
            "task_type": "research",
            "touches_resources": [
                {"type": "file", "identifier": "src/shared.py", "access": "write"},
            ],
            "acceptance_criteria": [],
        }

        # Task 2 (same resource)
        task2 = {
            "id": "task-seq-2",
            "description": "Second task",
            "task_type": "research",
            "touches_resources": [
                {"type": "file", "identifier": "src/shared.py", "access": "write"},
            ],
            "acceptance_criteria": [],
        }

        mock_client = MockAnthropicClient(response_key="work_research_result")

        with patch('anthropic.Anthropic', return_value=mock_client):
            # Execute first
            result1 = await execute_task(
                project_path=str(temp_project),
                task=task1,
                oracle=oracle,
            )
            assert result1["status"] == "completed"

            # Execute second (should work now that first is done)
            result2 = await execute_task(
                project_path=str(temp_project),
                task=task2,
                oracle=oracle,
            )
            assert result2["status"] == "completed"

        # Both completed, no locks remaining
        queue = ResourceQueue(temp_project)
        assert len(queue.get_active_locks()) == 0
