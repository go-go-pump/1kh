"""
Conversation Manager - Context persistence for stateless Claude API.

Each API call to Claude is stateless. This module manages conversation
history so Claude can maintain coherent multi-turn interactions with humans.

Key concepts:
- Each escalation/interaction has its own conversation thread
- Recent messages kept at full fidelity
- Older messages get summarized to save tokens
- Key facts extracted and persisted for quick reference
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any
from enum import Enum
import uuid

logger = logging.getLogger("1kh.conversation")


# =============================================================================
# Data Models
# =============================================================================

class MessageRole(str, Enum):
    USER = "user"          # Human's message
    ASSISTANT = "assistant" # Claude's message
    SYSTEM = "system"       # System context


@dataclass
class Message:
    """A single message in a conversation."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    def to_api_format(self) -> dict:
        """Format for Claude API."""
        return {"role": self.role.value, "content": self.content}

    def to_dict(self) -> dict:
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ConversationThread:
    """A conversation thread for a single escalation/interaction."""
    thread_id: str
    escalation_id: str
    original_ask: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    messages: list[Message] = field(default_factory=list)
    summary: str = ""  # Rolling summary of older messages
    key_facts: dict = field(default_factory=dict)  # Extracted structured data
    status: str = "active"  # active, resolved, stalled, abandoned
    attempt_count: int = 0
    last_activity: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, role: MessageRole, content: str, metadata: dict = None):
        """Add a message to the thread."""
        msg = Message(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(msg)
        self.last_activity = datetime.utcnow()
        if role == MessageRole.USER:
            self.attempt_count += 1

    def to_dict(self) -> dict:
        return {
            "thread_id": self.thread_id,
            "escalation_id": self.escalation_id,
            "original_ask": self.original_ask,
            "created_at": self.created_at.isoformat(),
            "messages": [m.to_dict() for m in self.messages],
            "summary": self.summary,
            "key_facts": self.key_facts,
            "status": self.status,
            "attempt_count": self.attempt_count,
            "last_activity": self.last_activity.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationThread":
        thread = cls(
            thread_id=data["thread_id"],
            escalation_id=data["escalation_id"],
            original_ask=data["original_ask"],
            created_at=datetime.fromisoformat(data["created_at"]),
            summary=data.get("summary", ""),
            key_facts=data.get("key_facts", {}),
            status=data.get("status", "active"),
            attempt_count=data.get("attempt_count", 0),
            last_activity=datetime.fromisoformat(data.get("last_activity", data["created_at"])),
        )
        thread.messages = [Message.from_dict(m) for m in data.get("messages", [])]
        return thread


# =============================================================================
# Retry and Timeout Policies
# =============================================================================

@dataclass
class RetryPolicy:
    """Policy for retrying failed/stalled interactions."""
    max_attempts: int = 3
    backoff_seconds: list[int] = field(default_factory=lambda: [60, 300, 900])  # 1m, 5m, 15m

    def should_retry(self, attempt_count: int) -> bool:
        return attempt_count < self.max_attempts

    def get_backoff(self, attempt_count: int) -> int:
        """Get backoff duration in seconds for this attempt."""
        if attempt_count >= len(self.backoff_seconds):
            return self.backoff_seconds[-1]
        return self.backoff_seconds[attempt_count]


@dataclass
class TimeoutPolicy:
    """Policy for handling unresponsive humans."""
    wait_duration: timedelta = field(default_factory=lambda: timedelta(hours=24))
    reminder_intervals: list[timedelta] = field(default_factory=lambda: [
        timedelta(hours=1),
        timedelta(hours=4),
        timedelta(hours=12),
    ])
    on_timeout: str = "stall"  # "stall", "auto_proceed", "escalate", "abandon"
    auto_proceed_default: Optional[str] = None  # Default action if auto_proceed

    def is_timed_out(self, last_activity: datetime) -> bool:
        return datetime.utcnow() - last_activity > self.wait_duration

    def get_next_reminder(self, last_activity: datetime, reminders_sent: int) -> Optional[datetime]:
        """Get when to send next reminder, if any."""
        if reminders_sent >= len(self.reminder_intervals):
            return None
        return last_activity + self.reminder_intervals[reminders_sent]


@dataclass
class InteractionPolicy:
    """Combined policy for human interactions."""
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    timeout: TimeoutPolicy = field(default_factory=TimeoutPolicy)
    max_history_messages: int = 10  # Keep last N messages at full fidelity
    summarize_after: int = 6  # Summarize when history exceeds this


# =============================================================================
# Conversation Manager
# =============================================================================

class ConversationManager:
    """
    Manages conversation context for ongoing human interactions.

    Responsibilities:
    - Store/retrieve conversation threads
    - Build context for Claude API calls
    - Summarize old history to save tokens
    - Track key facts extracted from conversations
    - Apply retry/timeout policies
    """

    def __init__(
        self,
        project_path: Path,
        policy: InteractionPolicy = None,
        claude_client = None,  # For summarization calls
    ):
        self.project_path = Path(project_path)
        self.policy = policy or InteractionPolicy()
        self.claude_client = claude_client

        # Storage
        self.threads_dir = self.project_path / ".1kh" / "conversations"
        self.threads_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self._threads: dict[str, ConversationThread] = {}

    def create_thread(
        self,
        escalation_id: str,
        original_ask: str,
        initial_context: dict = None,
    ) -> ConversationThread:
        """Create a new conversation thread for an escalation."""
        thread = ConversationThread(
            thread_id=f"thread-{uuid.uuid4().hex[:8]}",
            escalation_id=escalation_id,
            original_ask=original_ask,
            key_facts=initial_context or {},
        )

        self._threads[thread.thread_id] = thread
        self._save_thread(thread)

        logger.info(f"Created conversation thread {thread.thread_id} for escalation {escalation_id}")
        return thread

    def get_thread(self, thread_id: str) -> Optional[ConversationThread]:
        """Get a thread by ID."""
        if thread_id in self._threads:
            return self._threads[thread_id]

        # Try loading from disk
        thread_file = self.threads_dir / f"{thread_id}.json"
        if thread_file.exists():
            with open(thread_file, "r") as f:
                data = json.load(f)
            thread = ConversationThread.from_dict(data)
            self._threads[thread_id] = thread
            return thread

        return None

    def get_thread_by_escalation(self, escalation_id: str) -> Optional[ConversationThread]:
        """Get the active thread for an escalation."""
        # Check cache first
        for thread in self._threads.values():
            if thread.escalation_id == escalation_id and thread.status == "active":
                return thread

        # Scan disk
        for thread_file in self.threads_dir.glob("thread-*.json"):
            with open(thread_file, "r") as f:
                data = json.load(f)
            if data.get("escalation_id") == escalation_id and data.get("status") == "active":
                thread = ConversationThread.from_dict(data)
                self._threads[thread.thread_id] = thread
                return thread

        return None

    def add_exchange(
        self,
        thread_id: str,
        human_message: str,
        claude_response: str,
        extracted_facts: dict = None,
    ):
        """Record a human message and Claude's response."""
        thread = self.get_thread(thread_id)
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")

        thread.add_message(MessageRole.USER, human_message)
        thread.add_message(MessageRole.ASSISTANT, claude_response)

        if extracted_facts:
            thread.key_facts.update(extracted_facts)

        # Check if we need to summarize
        if len(thread.messages) > self.policy.summarize_after:
            self._maybe_summarize(thread)

        self._save_thread(thread)

    def add_human_message(self, thread_id: str, content: str):
        """Add just a human message (before Claude responds)."""
        thread = self.get_thread(thread_id)
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")

        thread.add_message(MessageRole.USER, content)
        self._save_thread(thread)

    def add_claude_message(self, thread_id: str, content: str, extracted_facts: dict = None):
        """Add Claude's response."""
        thread = self.get_thread(thread_id)
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")

        thread.add_message(MessageRole.ASSISTANT, content)

        if extracted_facts:
            thread.key_facts.update(extracted_facts)

        if len(thread.messages) > self.policy.summarize_after:
            self._maybe_summarize(thread)

        self._save_thread(thread)

    def get_context_for_claude(self, thread_id: str) -> list[dict]:
        """
        Build the messages array for a Claude API call.

        Structure:
        1. System message with original ask, key facts, summary
        2. Recent messages at full fidelity
        """
        thread = self.get_thread(thread_id)
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")

        messages = []

        # System context
        system_parts = [
            f"You are handling an escalation for ThousandHand.",
            f"",
            f"Original request: {thread.original_ask}",
        ]

        if thread.key_facts:
            system_parts.append(f"Key facts established: {json.dumps(thread.key_facts, indent=2)}")

        if thread.summary:
            system_parts.append(f"")
            system_parts.append(f"Summary of earlier conversation:")
            system_parts.append(thread.summary)

        system_parts.append(f"")
        system_parts.append(f"Interaction attempt: {thread.attempt_count}")

        messages.append({
            "role": "user",
            "content": "\n".join(system_parts) + "\n\n---\n\nPlease continue the conversation:"
        })

        # Recent messages (last N)
        recent = thread.messages[-self.policy.max_history_messages:]
        for msg in recent:
            messages.append(msg.to_api_format())

        return messages

    def get_simple_context(self, thread_id: str) -> dict:
        """Get a simple context dict for logging/debugging."""
        thread = self.get_thread(thread_id)
        if not thread:
            return {}

        return {
            "thread_id": thread.thread_id,
            "escalation_id": thread.escalation_id,
            "original_ask": thread.original_ask,
            "attempt_count": thread.attempt_count,
            "message_count": len(thread.messages),
            "key_facts": thread.key_facts,
            "status": thread.status,
            "has_summary": bool(thread.summary),
        }

    def mark_resolved(self, thread_id: str, resolution: str = None):
        """Mark a thread as resolved."""
        thread = self.get_thread(thread_id)
        if thread:
            thread.status = "resolved"
            if resolution:
                thread.key_facts["resolution"] = resolution
            self._save_thread(thread)

    def mark_stalled(self, thread_id: str, reason: str = None):
        """Mark a thread as stalled (needs intervention)."""
        thread = self.get_thread(thread_id)
        if thread:
            thread.status = "stalled"
            if reason:
                thread.key_facts["stall_reason"] = reason
            self._save_thread(thread)

    def mark_abandoned(self, thread_id: str, reason: str = None):
        """Mark a thread as abandoned."""
        thread = self.get_thread(thread_id)
        if thread:
            thread.status = "abandoned"
            if reason:
                thread.key_facts["abandon_reason"] = reason
            self._save_thread(thread)

    def check_timeout(self, thread_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if a thread has timed out.

        Returns:
            (is_timed_out, action_to_take)
        """
        thread = self.get_thread(thread_id)
        if not thread or thread.status != "active":
            return False, None

        if self.policy.timeout.is_timed_out(thread.last_activity):
            return True, self.policy.timeout.on_timeout

        return False, None

    def should_retry(self, thread_id: str) -> bool:
        """Check if we should retry this interaction."""
        thread = self.get_thread(thread_id)
        if not thread:
            return False
        return self.policy.retry.should_retry(thread.attempt_count)

    def get_all_active_threads(self) -> list[ConversationThread]:
        """Get all active conversation threads."""
        threads = []
        for thread_file in self.threads_dir.glob("thread-*.json"):
            with open(thread_file, "r") as f:
                data = json.load(f)
            if data.get("status") == "active":
                thread = ConversationThread.from_dict(data)
                self._threads[thread.thread_id] = thread
                threads.append(thread)
        return threads

    def get_stalled_threads(self) -> list[ConversationThread]:
        """Get all stalled threads that might need alternative paths."""
        threads = []
        for thread_file in self.threads_dir.glob("thread-*.json"):
            with open(thread_file, "r") as f:
                data = json.load(f)
            if data.get("status") == "stalled":
                thread = ConversationThread.from_dict(data)
                threads.append(thread)
        return threads

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    def _save_thread(self, thread: ConversationThread):
        """Persist thread to disk."""
        thread_file = self.threads_dir / f"{thread.thread_id}.json"
        with open(thread_file, "w") as f:
            json.dump(thread.to_dict(), f, indent=2)

    def _maybe_summarize(self, thread: ConversationThread):
        """Summarize older messages if history is getting long."""
        if len(thread.messages) <= self.policy.summarize_after:
            return

        # Messages to summarize (all but the most recent few)
        keep_recent = self.policy.max_history_messages // 2
        to_summarize = thread.messages[:-keep_recent]

        if not to_summarize:
            return

        # Build summary (with or without Claude)
        if self.claude_client:
            thread.summary = self._summarize_with_claude(thread, to_summarize)
        else:
            thread.summary = self._summarize_simple(thread, to_summarize)

        # Remove summarized messages
        thread.messages = thread.messages[-keep_recent:]

        logger.info(f"Summarized {len(to_summarize)} messages in thread {thread.thread_id}")

    def _summarize_simple(self, thread: ConversationThread, messages: list[Message]) -> str:
        """Simple summarization without Claude (for testing/fallback)."""
        existing = thread.summary + "\n\n" if thread.summary else ""

        summary_parts = [existing.strip(), "Additional context:"]
        for msg in messages:
            role = "Human" if msg.role == MessageRole.USER else "Assistant"
            # Truncate long messages
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            summary_parts.append(f"- {role}: {content}")

        return "\n".join(summary_parts)

    def _summarize_with_claude(self, thread: ConversationThread, messages: list[Message]) -> str:
        """Use Claude to create a concise summary."""
        conversation_text = "\n".join([
            f"{'Human' if m.role == MessageRole.USER else 'Assistant'}: {m.content}"
            for m in messages
        ])

        existing_context = ""
        if thread.summary:
            existing_context = f"Previous summary:\n{thread.summary}\n\n"

        prompt = f"""Summarize this conversation excerpt concisely. Focus on:
1. Key decisions made
2. Information provided by the human
3. Outstanding questions or blockers

{existing_context}New messages to summarize:
{conversation_text}

Provide a brief summary (2-4 sentences):"""

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.warning(f"Failed to summarize with Claude: {e}")
            return self._summarize_simple(thread, messages)


# =============================================================================
# Impasse Handler
# =============================================================================

@dataclass
class AlternativePath:
    """An alternative path when human interaction stalls."""
    description: str
    hypothesis_id: Optional[str]
    action: str  # "retry_different", "skip", "workaround", "defer"
    trade_offs: str
    risk_level: str  # "low", "medium", "high"


class ImpasseHandler:
    """
    Handles situations where human interaction has stalled.

    When we can't make progress with a human, this finds alternatives:
    - Different approach that doesn't need this input
    - Safe default to proceed with
    - Escalation to different human
    - Graceful deferral
    """

    def __init__(self, project_path: Path, conversation_manager: ConversationManager):
        self.project_path = Path(project_path)
        self.conversation_manager = conversation_manager

    def find_alternatives(self, thread_id: str) -> list[AlternativePath]:
        """
        Find alternative paths forward when stuck.

        This is a simplified version - in production this would
        query the hypothesis space and find workarounds.
        """
        thread = self.conversation_manager.get_thread(thread_id)
        if not thread:
            return []

        alternatives = []

        # Always offer retry with simplified ask
        alternatives.append(AlternativePath(
            description="Retry with a simpler, more specific question",
            hypothesis_id=None,
            action="retry_different",
            trade_offs="May get partial information",
            risk_level="low",
        ))

        # If we have enough key facts, offer to proceed with what we have
        if thread.key_facts:
            alternatives.append(AlternativePath(
                description=f"Proceed with information gathered so far: {list(thread.key_facts.keys())}",
                hypothesis_id=None,
                action="proceed_partial",
                trade_offs="Missing some inputs, may need adjustment later",
                risk_level="medium",
            ))

        # Offer to defer
        alternatives.append(AlternativePath(
            description="Defer this task and work on something else",
            hypothesis_id=None,
            action="defer",
            trade_offs="This hypothesis blocked until human available",
            risk_level="low",
        ))

        # Offer to skip (if not critical)
        alternatives.append(AlternativePath(
            description="Skip this step and proceed without human input",
            hypothesis_id=None,
            action="skip",
            trade_offs="May miss important context or make suboptimal decisions",
            risk_level="high",
        ))

        return alternatives

    def format_impasse_message(self, thread_id: str, alternatives: list[AlternativePath]) -> str:
        """Format a message to present to the system/human about the impasse."""
        thread = self.conversation_manager.get_thread(thread_id)
        if not thread:
            return "Thread not found"

        lines = [
            f"🚧 Impasse Detected",
            f"",
            f"Original request: {thread.original_ask}",
            f"Attempts made: {thread.attempt_count}",
            f"Status: {thread.status}",
            f"",
            f"Possible alternatives:",
        ]

        for i, alt in enumerate(alternatives, 1):
            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}[alt.risk_level]
            lines.append(f"")
            lines.append(f"{i}. {alt.description}")
            lines.append(f"   {risk_emoji} Risk: {alt.risk_level}")
            lines.append(f"   Trade-offs: {alt.trade_offs}")

        return "\n".join(lines)
