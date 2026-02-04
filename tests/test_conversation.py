"""
Tests for Conversation Manager and Layer 2b edge cases.

These tests verify:
1. Context persistence across API calls
2. Retry/timeout policies
3. Impasse handling
4. Chaotic human behavior handling
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.conversation import (
    ConversationManager,
    ConversationThread,
    Message,
    MessageRole,
    RetryPolicy,
    TimeoutPolicy,
    InteractionPolicy,
    ImpasseHandler,
    AlternativePath,
)
from core.dashboard import Dashboard, EventType
from tests.mocks.human import (
    MockHumanChaotic,
    ChaoticBehavior,
    MockHumanSimple,
    EscalationManager,
    Escalation,
    EscalationType,
)


@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    path = Path(tempfile.mkdtemp())
    (path / ".1kh").mkdir(parents=True, exist_ok=True)
    yield path
    shutil.rmtree(path, ignore_errors=True)


# =============================================================================
# Conversation Manager Tests
# =============================================================================

class TestConversationManager:
    """Tests for ConversationManager context persistence."""

    def test_create_thread(self, temp_project):
        """Should create a new conversation thread."""
        manager = ConversationManager(temp_project)

        thread = manager.create_thread(
            escalation_id="esc-001",
            original_ask="Approve $500 ad spend?",
        )

        assert thread.thread_id.startswith("thread-")
        assert thread.escalation_id == "esc-001"
        assert thread.original_ask == "Approve $500 ad spend?"
        assert thread.status == "active"

    def test_add_exchange(self, temp_project):
        """Should add human/claude exchange to thread."""
        manager = ConversationManager(temp_project)
        thread = manager.create_thread("esc-001", "What's the budget?")

        manager.add_exchange(
            thread.thread_id,
            human_message="Around $500",
            claude_response="Got it. Should I proceed with $500 budget?",
            extracted_facts={"budget": 500},
        )

        updated = manager.get_thread(thread.thread_id)
        assert len(updated.messages) == 2
        assert updated.messages[0].role == MessageRole.USER
        assert updated.messages[1].role == MessageRole.ASSISTANT
        assert updated.key_facts["budget"] == 500

    def test_get_context_for_claude(self, temp_project):
        """Should build proper context for Claude API call."""
        manager = ConversationManager(temp_project)
        thread = manager.create_thread(
            "esc-001",
            "Approve deployment?",
            initial_context={"env": "production"},
        )

        manager.add_exchange(
            thread.thread_id,
            "yes",
            "Confirmed. Proceeding with production deployment.",
        )

        context = manager.get_context_for_claude(thread.thread_id)

        # Should have system context + conversation
        assert len(context) >= 2
        # First message should contain original ask
        assert "Approve deployment?" in context[0]["content"]
        # Should include key facts
        assert "production" in context[0]["content"]

    def test_thread_persistence(self, temp_project):
        """Should persist and reload thread from disk."""
        manager1 = ConversationManager(temp_project)
        thread = manager1.create_thread("esc-001", "Test persistence")
        manager1.add_exchange(thread.thread_id, "Hello", "Hi there")
        thread_id = thread.thread_id

        # Create new manager (simulates restart)
        manager2 = ConversationManager(temp_project)
        reloaded = manager2.get_thread(thread_id)

        assert reloaded is not None
        assert reloaded.escalation_id == "esc-001"
        assert len(reloaded.messages) == 2

    def test_mark_resolved(self, temp_project):
        """Should mark thread as resolved."""
        manager = ConversationManager(temp_project)
        thread = manager.create_thread("esc-001", "Test")

        manager.mark_resolved(thread.thread_id, resolution="Approved by user")

        updated = manager.get_thread(thread.thread_id)
        assert updated.status == "resolved"
        assert updated.key_facts["resolution"] == "Approved by user"

    def test_mark_stalled(self, temp_project):
        """Should mark thread as stalled."""
        manager = ConversationManager(temp_project)
        thread = manager.create_thread("esc-001", "Test")

        manager.mark_stalled(thread.thread_id, reason="User unresponsive")

        updated = manager.get_thread(thread.thread_id)
        assert updated.status == "stalled"
        assert updated.key_facts["stall_reason"] == "User unresponsive"

    def test_attempt_counting(self, temp_project):
        """Should count human message attempts."""
        manager = ConversationManager(temp_project)
        thread = manager.create_thread("esc-001", "Test")

        manager.add_human_message(thread.thread_id, "First try")
        manager.add_human_message(thread.thread_id, "Second try")
        manager.add_human_message(thread.thread_id, "Third try")

        updated = manager.get_thread(thread.thread_id)
        assert updated.attempt_count == 3

    def test_summarization_trigger(self, temp_project):
        """Should trigger summarization when history gets long."""
        policy = InteractionPolicy(summarize_after=4, max_history_messages=6)
        manager = ConversationManager(temp_project, policy=policy)
        thread = manager.create_thread("esc-001", "Test summary")

        # Add enough messages to trigger summarization
        for i in range(5):
            manager.add_exchange(
                thread.thread_id,
                f"Human message {i}",
                f"Claude response {i}",
            )

        updated = manager.get_thread(thread.thread_id)
        # Should have summary and fewer messages
        assert updated.summary != ""
        assert len(updated.messages) < 10


# =============================================================================
# Retry Policy Tests
# =============================================================================

class TestRetryPolicy:
    """Tests for retry policy logic."""

    def test_should_retry_within_limit(self):
        """Should allow retry within max attempts."""
        policy = RetryPolicy(max_attempts=3)
        assert policy.should_retry(0) is True
        assert policy.should_retry(1) is True
        assert policy.should_retry(2) is True
        assert policy.should_retry(3) is False

    def test_backoff_progression(self):
        """Should return increasing backoff times."""
        policy = RetryPolicy(backoff_seconds=[60, 300, 900])
        assert policy.get_backoff(0) == 60
        assert policy.get_backoff(1) == 300
        assert policy.get_backoff(2) == 900
        assert policy.get_backoff(5) == 900  # Caps at last value


# =============================================================================
# Timeout Policy Tests
# =============================================================================

class TestTimeoutPolicy:
    """Tests for timeout policy logic."""

    def test_is_timed_out(self):
        """Should detect timeout correctly."""
        policy = TimeoutPolicy(wait_duration=timedelta(hours=1))

        recent = datetime.utcnow() - timedelta(minutes=30)
        old = datetime.utcnow() - timedelta(hours=2)

        assert policy.is_timed_out(recent) is False
        assert policy.is_timed_out(old) is True

    def test_reminder_scheduling(self):
        """Should schedule reminders correctly."""
        policy = TimeoutPolicy(reminder_intervals=[
            timedelta(hours=1),
            timedelta(hours=4),
        ])

        last_activity = datetime.utcnow()

        next1 = policy.get_next_reminder(last_activity, 0)
        assert next1 == last_activity + timedelta(hours=1)

        next2 = policy.get_next_reminder(last_activity, 1)
        assert next2 == last_activity + timedelta(hours=4)

        next3 = policy.get_next_reminder(last_activity, 2)
        assert next3 is None  # No more reminders


class TestConversationManagerTimeout:
    """Tests for timeout handling in ConversationManager."""

    def test_check_timeout_active(self, temp_project):
        """Should detect timeout on active thread."""
        policy = InteractionPolicy(
            timeout=TimeoutPolicy(wait_duration=timedelta(seconds=1))
        )
        manager = ConversationManager(temp_project, policy=policy)
        thread = manager.create_thread("esc-001", "Test")

        # Immediately - not timed out
        is_timeout, action = manager.check_timeout(thread.thread_id)
        assert is_timeout is False

        # Artificially age the thread
        thread.last_activity = datetime.utcnow() - timedelta(seconds=5)
        manager._save_thread(thread)

        is_timeout, action = manager.check_timeout(thread.thread_id)
        assert is_timeout is True
        assert action == "stall"

    def test_should_retry_respects_policy(self, temp_project):
        """Should respect retry policy limits."""
        policy = InteractionPolicy(retry=RetryPolicy(max_attempts=2))
        manager = ConversationManager(temp_project, policy=policy)
        thread = manager.create_thread("esc-001", "Test")

        # First attempt
        assert manager.should_retry(thread.thread_id) is True

        # Simulate attempts
        thread.attempt_count = 2
        manager._save_thread(thread)

        assert manager.should_retry(thread.thread_id) is False


# =============================================================================
# Impasse Handler Tests
# =============================================================================

class TestImpasseHandler:
    """Tests for impasse handling and alternative paths."""

    def test_find_alternatives_basic(self, temp_project):
        """Should find basic alternatives for stalled thread."""
        manager = ConversationManager(temp_project)
        thread = manager.create_thread("esc-001", "Need budget approval")
        handler = ImpasseHandler(temp_project, manager)

        alternatives = handler.find_alternatives(thread.thread_id)

        assert len(alternatives) >= 2
        actions = [a.action for a in alternatives]
        assert "retry_different" in actions
        assert "defer" in actions

    def test_find_alternatives_with_key_facts(self, temp_project):
        """Should offer proceed_partial when we have some info."""
        manager = ConversationManager(temp_project)
        thread = manager.create_thread(
            "esc-001",
            "Need budget approval",
            initial_context={"partial_budget": 250},
        )
        handler = ImpasseHandler(temp_project, manager)

        alternatives = handler.find_alternatives(thread.thread_id)

        actions = [a.action for a in alternatives]
        assert "proceed_partial" in actions

    def test_format_impasse_message(self, temp_project):
        """Should format readable impasse message."""
        manager = ConversationManager(temp_project)
        thread = manager.create_thread("esc-001", "Need approval")
        thread.attempt_count = 3
        thread.status = "stalled"
        manager._save_thread(thread)

        handler = ImpasseHandler(temp_project, manager)
        alternatives = handler.find_alternatives(thread.thread_id)
        message = handler.format_impasse_message(thread.thread_id, alternatives)

        assert "Impasse Detected" in message
        assert "Need approval" in message
        assert "Attempts made: 3" in message
        assert "Risk:" in message


# =============================================================================
# Chaotic Human Tests
# =============================================================================

class TestMockHumanChaotic:
    """Tests for chaotic human behavior simulation."""

    def test_sparse_responses(self, temp_project):
        """Sparse human gives one-word answers."""
        human = MockHumanChaotic(behavior=ChaoticBehavior.SPARSE, seed=42)
        escalation = Escalation(
            id="esc-001",
            type=EscalationType.APPROVAL_REQUEST,
            summary="Deploy to production?",
        )

        response = human.respond(escalation)

        assert response is not None
        assert response.action == "unclear"
        assert response.feedback in MockHumanChaotic.SPARSE_RESPONSES

    def test_unresponsive_returns_none(self, temp_project):
        """Unresponsive human never answers (triggers timeout)."""
        human = MockHumanChaotic(behavior=ChaoticBehavior.UNRESPONSIVE)
        escalation = Escalation(
            id="esc-001",
            type=EscalationType.APPROVAL_REQUEST,
            summary="Deploy?",
        )

        response = human.respond(escalation)

        assert response is None

    def test_hostile_responses(self, temp_project):
        """Hostile human is actively unhelpful."""
        human = MockHumanChaotic(behavior=ChaoticBehavior.HOSTILE, seed=42)
        escalation = Escalation(
            id="esc-001",
            type=EscalationType.GUIDANCE_REQUEST,
            summary="Which approach?",
        )

        response = human.respond(escalation)

        assert response.action == "hostile"
        assert response.feedback in MockHumanChaotic.HOSTILE_RESPONSES

    def test_contradictory_flip_flops(self, temp_project):
        """Contradictory human changes mind between responses."""
        human = MockHumanChaotic(behavior=ChaoticBehavior.CONTRADICTORY, seed=42)
        escalation = Escalation(
            id="esc-001",
            type=EscalationType.APPROVAL_REQUEST,
            summary="Proceed?",
        )

        response1 = human.respond(escalation)
        response2 = human.respond(escalation)

        # Should contradict themselves
        assert response1.action != response2.action or "changed my mind" in (response2.feedback or "")

    def test_off_topic_responses(self, temp_project):
        """Off-topic human answers wrong question."""
        human = MockHumanChaotic(behavior=ChaoticBehavior.OFF_TOPIC, seed=42)
        escalation = Escalation(
            id="esc-001",
            type=EscalationType.BUDGET_EXCEEDED,
            summary="We've exceeded budget by $200",
        )

        response = human.respond(escalation)

        assert response.action == "off_topic"
        # Response should be irrelevant to budget
        assert "budget" not in response.feedback.lower()

    def test_recovery_after_n_attempts(self, temp_project):
        """Human recovers and becomes cooperative after N attempts."""
        human = MockHumanChaotic(
            behavior=ChaoticBehavior.HOSTILE,
            recovery_after=3,
            seed=42,
        )
        escalation = Escalation(
            id="esc-001",
            type=EscalationType.APPROVAL_REQUEST,
            summary="Approve?",
        )

        # First 3 responses are chaotic
        for _ in range(3):
            response = human.respond(escalation)
            assert response.action == "hostile"

        # 4th response should be cooperative
        response = human.respond(escalation)
        assert response.action == "approve"

    def test_severity_reduces_chaos(self, temp_project):
        """Lower severity means less chaotic behavior."""
        human = MockHumanChaotic(
            behavior=ChaoticBehavior.HOSTILE,
            severity=0.0,  # Never chaotic
            seed=42,
        )
        escalation = Escalation(
            id="esc-001",
            type=EscalationType.APPROVAL_REQUEST,
            summary="Approve?",
        )

        response = human.respond(escalation)

        # Should be cooperative even though behavior is HOSTILE
        assert response.action != "hostile"


# =============================================================================
# Integration Tests - Chaotic Human + System Policies
# =============================================================================

class TestChaoticHumanWithPolicies:
    """Tests for system behavior when handling chaotic humans."""

    def test_retry_on_sparse_response(self, temp_project):
        """System should retry when getting sparse responses."""
        policy = InteractionPolicy(retry=RetryPolicy(max_attempts=3))
        manager = ConversationManager(temp_project, policy=policy)
        human = MockHumanChaotic(behavior=ChaoticBehavior.SPARSE, seed=42)

        thread = manager.create_thread("esc-001", "Need detailed approval")

        # Simulate retry loop
        attempts = 0
        while manager.should_retry(thread.thread_id):
            escalation = Escalation(
                id="esc-001",
                type=EscalationType.APPROVAL_REQUEST,
                summary="Please provide detailed approval",
            )
            response = human.respond(escalation)

            # Record attempt
            manager.add_human_message(thread.thread_id, response.feedback)
            attempts += 1

            if response.action != "unclear":
                break

        assert attempts <= 3  # Respects max_attempts

    def test_timeout_on_unresponsive(self, temp_project):
        """System should timeout when human is unresponsive."""
        policy = InteractionPolicy(
            timeout=TimeoutPolicy(
                wait_duration=timedelta(seconds=1),
                on_timeout="stall",
            )
        )
        manager = ConversationManager(temp_project, policy=policy)
        human = MockHumanChaotic(behavior=ChaoticBehavior.UNRESPONSIVE)

        thread = manager.create_thread("esc-001", "Need response")

        # Simulate waiting
        thread.last_activity = datetime.utcnow() - timedelta(seconds=5)
        manager._save_thread(thread)

        is_timeout, action = manager.check_timeout(thread.thread_id)

        assert is_timeout is True
        assert action == "stall"

    def test_impasse_triggers_alternatives(self, temp_project):
        """Stalled thread should trigger alternative path finding."""
        manager = ConversationManager(temp_project)
        human = MockHumanChaotic(behavior=ChaoticBehavior.HOSTILE, seed=42)
        handler = ImpasseHandler(temp_project, manager)

        thread = manager.create_thread("esc-001", "Need approval for X")

        # Simulate failed attempts
        for i in range(3):
            escalation = Escalation(
                id="esc-001",
                type=EscalationType.APPROVAL_REQUEST,
                summary="Please approve",
            )
            response = human.respond(escalation)
            manager.add_exchange(
                thread.thread_id,
                response.feedback,
                "I understand you're frustrated. Let me try asking differently.",
            )

        # Mark as stalled
        manager.mark_stalled(thread.thread_id, "Human uncooperative")

        # Find alternatives
        alternatives = handler.find_alternatives(thread.thread_id)

        assert len(alternatives) >= 2
        assert any(a.action == "defer" for a in alternatives)

    def test_full_escalation_flow_with_chaotic_human(self, temp_project):
        """Full flow: escalation → chaotic response → retry → impasse → alternatives."""
        dashboard = Dashboard(temp_project)
        dashboard.set_north_star("$1M ARR", target_value=1000000)

        # Chaotic human that recovers
        human = MockHumanChaotic(
            behavior=ChaoticBehavior.SPARSE,
            recovery_after=2,
            seed=42,
        )

        esc_manager = EscalationManager(temp_project, human=human, dashboard=dashboard)
        conv_manager = ConversationManager(temp_project)
        impasse_handler = ImpasseHandler(temp_project, conv_manager)

        # Create escalation
        escalation = esc_manager.create_escalation(
            type=EscalationType.APPROVAL_REQUEST,
            summary="Approve $500 for ads?",
        )

        # Create conversation thread
        thread = conv_manager.create_thread(
            escalation.id,
            escalation.summary,
        )

        # Attempt loop
        resolved = False
        for attempt in range(5):
            responses = esc_manager.process_pending()

            if not responses:
                break

            response = responses[0]
            conv_manager.add_exchange(
                thread.thread_id,
                response.feedback or response.action,
                f"Attempt {attempt + 1}: Received '{response.action}'",
            )

            if response.action in ["approve", "reject"]:
                resolved = True
                conv_manager.mark_resolved(thread.thread_id)
                break

            # Re-queue escalation for retry
            esc_manager.pending_escalations.append(escalation)

        # Should have resolved after human recovered
        assert resolved is True
        assert conv_manager.get_thread(thread.thread_id).status == "resolved"
