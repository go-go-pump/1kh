"""
Mock Human Response Layer for testing.

Two levels:
1. Simple: Configurable patterns (always_approve, prioritize_first, etc.)
2. Nuanced: Scenario-based with delays, mistakes, and edge cases
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Callable, Any
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.dashboard import Dashboard, EventType


class EscalationType(str, Enum):
    """Types of escalations that require human response."""
    CONFLICT_RESOLUTION = "conflict_resolution"  # Two hypotheses conflict
    APPROVAL_REQUEST = "approval_request"  # Task needs approval
    GUIDANCE_REQUEST = "guidance_request"  # Low confidence, need direction
    BUDGET_EXCEEDED = "budget_exceeded"  # Cost limit reached
    ERROR_RECOVERY = "error_recovery"  # Task failed, decide what to do
    CUSTOM = "custom"


@dataclass
class Escalation:
    """An escalation requiring human input."""
    id: str
    type: EscalationType
    summary: str
    context: dict = field(default_factory=dict)
    options: list[str] = field(default_factory=list)
    default_option: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HumanResponse:
    """A human's response to an escalation."""
    escalation_id: str
    action: str  # The chosen action
    feedback: Optional[str] = None  # Additional context
    responded_at: datetime = field(default_factory=datetime.utcnow)
    response_time_seconds: float = 0  # How long human took


# =============================================================================
# Simple Mock Human (Layer 2a)
# =============================================================================

class MockHumanSimple:
    """
    Simple mock human with configurable patterns.

    Good for deterministic testing where you want predictable responses.

    Usage:
        human = MockHumanSimple(patterns={
            "conflict_resolution": "prioritize_first",
            "approval_requests": "always_approve",
        })
        response = human.respond(escalation)
    """

    # Predefined pattern handlers
    PATTERNS = {
        # Conflict resolution
        "prioritize_first": lambda esc: HumanResponse(
            escalation_id=esc.id,
            action="select",
            feedback=f"Prioritize {esc.options[0] if esc.options else 'first option'}",
        ),
        "prioritize_highest_score": lambda esc: HumanResponse(
            escalation_id=esc.id,
            action="select",
            feedback="Select highest scored option",
        ),
        "reject_both": lambda esc: HumanResponse(
            escalation_id=esc.id,
            action="reject",
            feedback="Reject both conflicting options",
        ),

        # Approval
        "always_approve": lambda esc: HumanResponse(
            escalation_id=esc.id,
            action="approve",
        ),
        "always_reject": lambda esc: HumanResponse(
            escalation_id=esc.id,
            action="reject",
            feedback="Not approved",
        ),
        "approve_if_low_risk": lambda esc: HumanResponse(
            escalation_id=esc.id,
            action="approve" if esc.context.get("risk", "high") == "low" else "reject",
        ),

        # Guidance
        "provide_default": lambda esc: HumanResponse(
            escalation_id=esc.id,
            action="select",
            feedback=esc.default_option or "Use default approach",
        ),
        "provide_empty": lambda esc: HumanResponse(
            escalation_id=esc.id,
            action="skip",
        ),
        "ask_clarification": lambda esc: HumanResponse(
            escalation_id=esc.id,
            action="clarify",
            feedback="Please provide more details",
        ),

        # Error recovery
        "retry": lambda esc: HumanResponse(
            escalation_id=esc.id,
            action="retry",
        ),
        "abandon": lambda esc: HumanResponse(
            escalation_id=esc.id,
            action="abandon",
            feedback="Give up on this approach",
        ),
        "try_alternative": lambda esc: HumanResponse(
            escalation_id=esc.id,
            action="alternative",
            feedback="Try a different approach",
        ),
    }

    def __init__(
        self,
        patterns: dict[str, str] = None,
        response_delay: float = 0,
    ):
        """
        Initialize with pattern configuration.

        patterns: Dict mapping EscalationType to pattern name
            e.g., {"conflict_resolution": "prioritize_first"}
        response_delay: Simulated delay in seconds (0 for instant)
        """
        self.patterns = patterns or {
            "conflict_resolution": "prioritize_first",
            "approval_request": "always_approve",
            "guidance_request": "provide_default",
            "error_recovery": "retry",
        }
        self.response_delay = response_delay
        self.response_history: list[HumanResponse] = []

    def respond(self, escalation: Escalation) -> HumanResponse:
        """Respond to an escalation using configured pattern."""
        start = time.time()

        if self.response_delay > 0:
            time.sleep(self.response_delay)

        # Get pattern for this escalation type
        pattern_name = self.patterns.get(
            escalation.type.value,
            "provide_default"  # fallback
        )

        # Get handler
        handler = self.PATTERNS.get(pattern_name)
        if not handler:
            handler = self.PATTERNS["provide_default"]

        response = handler(escalation)
        response.response_time_seconds = time.time() - start

        self.response_history.append(response)
        return response


# =============================================================================
# Nuanced Mock Human (Layer 2b)
# =============================================================================

class MockHumanNuanced:
    """
    Nuanced mock human with realistic behaviors.

    Simulates:
    - Variable response times
    - Occasional mistakes
    - Clarification requests
    - Mood/fatigue effects
    - Context-dependent decisions

    Good for stress testing and edge case discovery.
    """

    def __init__(
        self,
        base_response_delay: float = 2.0,
        behaviors: dict = None,
        seed: int = None,
    ):
        """
        Initialize nuanced human simulation.

        behaviors:
            - typo_rate: Probability of typo in feedback (0-1)
            - misunderstand_rate: Probability of misunderstanding (0-1)
            - delay_variance: Variance in response time (0-1)
            - abandon_rate: Probability of not responding (0-1)
            - fatigue_after: Number of responses before fatigue kicks in
        """
        self.base_delay = base_response_delay
        self.behaviors = behaviors or {
            "typo_rate": 0.05,
            "misunderstand_rate": 0.1,
            "delay_variance": 0.5,
            "abandon_rate": 0.02,
            "fatigue_after": 10,
        }
        self.rng = random.Random(seed)
        self.response_count = 0
        self.response_history: list[HumanResponse] = []
        self.scenario_overrides: dict[str, dict] = {}

    def set_scenario_response(self, scenario: str, response_config: dict):
        """
        Override response for a specific scenario.

        scenario: Identifier like "first_escalation", "after_failure", etc.
        response_config: {"action": "approve", "feedback": "..."}
        """
        self.scenario_overrides[scenario] = response_config

    def respond(
        self,
        escalation: Escalation,
        scenario: str = None,
    ) -> Optional[HumanResponse]:
        """
        Respond to escalation with nuanced behavior.

        May return None if human "abandons" (doesn't respond).
        """
        self.response_count += 1

        # Check for abandonment
        if self.rng.random() < self.behaviors["abandon_rate"]:
            return None  # Human never responds

        # Calculate response delay with variance
        variance = self.behaviors["delay_variance"]
        delay = self.base_delay * (1 + self.rng.uniform(-variance, variance))

        # Apply fatigue (slower after many responses)
        if self.response_count > self.behaviors["fatigue_after"]:
            fatigue_factor = 1 + (self.response_count - self.behaviors["fatigue_after"]) * 0.1
            delay *= fatigue_factor

        # Simulate delay (optional for testing)
        # time.sleep(delay)

        # Check for scenario override
        if scenario and scenario in self.scenario_overrides:
            override = self.scenario_overrides[scenario]
            return HumanResponse(
                escalation_id=escalation.id,
                action=override.get("action", "approve"),
                feedback=override.get("feedback"),
                response_time_seconds=delay,
            )

        # Generate response based on escalation type
        response = self._generate_response(escalation)
        response.response_time_seconds = delay

        # Apply misunderstanding
        if self.rng.random() < self.behaviors["misunderstand_rate"]:
            response = self._apply_misunderstanding(response, escalation)

        # Apply typos
        if response.feedback and self.rng.random() < self.behaviors["typo_rate"]:
            response.feedback = self._add_typo(response.feedback)

        self.response_history.append(response)
        return response

    def _generate_response(self, escalation: Escalation) -> HumanResponse:
        """Generate a response based on escalation type."""
        if escalation.type == EscalationType.CONFLICT_RESOLUTION:
            # Usually pick the first/higher-scored option
            action = "select"
            if escalation.options:
                feedback = f"Go with {self.rng.choice(escalation.options)}"
            else:
                feedback = "Proceed with the first option"

        elif escalation.type == EscalationType.APPROVAL_REQUEST:
            # Approve most of the time, but sometimes reject
            if self.rng.random() < 0.85:
                action = "approve"
                feedback = None
            else:
                action = "reject"
                feedback = "Not comfortable with this approach"

        elif escalation.type == EscalationType.GUIDANCE_REQUEST:
            # Provide guidance or ask for more info
            if self.rng.random() < 0.7:
                action = "guide"
                feedback = "Focus on the core functionality first"
            else:
                action = "clarify"
                feedback = "What are the alternatives?"

        elif escalation.type == EscalationType.ERROR_RECOVERY:
            # Retry, abandon, or try alternative
            choice = self.rng.choice(["retry", "retry", "alternative", "abandon"])
            action = choice
            feedback = {
                "retry": "Let's try again",
                "alternative": "Try a different approach",
                "abandon": "This isn't working, move on",
            }.get(choice)

        elif escalation.type == EscalationType.BUDGET_EXCEEDED:
            # Usually pause or adjust
            if self.rng.random() < 0.6:
                action = "pause"
                feedback = "Let's pause and review spending"
            else:
                action = "increase"
                feedback = "Increase budget by 20%"

        else:
            # Default
            action = escalation.default_option or "acknowledge"
            feedback = None

        return HumanResponse(
            escalation_id=escalation.id,
            action=action,
            feedback=feedback,
        )

    def _apply_misunderstanding(
        self,
        response: HumanResponse,
        escalation: Escalation,
    ) -> HumanResponse:
        """Modify response to simulate misunderstanding."""
        # Misunderstanding often means wrong action
        wrong_actions = {
            "approve": "reject",
            "reject": "approve",
            "retry": "abandon",
            "select": "clarify",
        }

        response.action = wrong_actions.get(response.action, response.action)
        response.feedback = (response.feedback or "") + " (misunderstood the question)"
        return response

    def _add_typo(self, text: str) -> str:
        """Add a typo to text."""
        if len(text) < 5:
            return text

        typo_types = ["swap", "double", "missing"]
        typo = self.rng.choice(typo_types)

        pos = self.rng.randint(1, len(text) - 2)

        if typo == "swap" and pos < len(text) - 1:
            text = text[:pos] + text[pos+1] + text[pos] + text[pos+2:]
        elif typo == "double":
            text = text[:pos] + text[pos] + text[pos:]
        elif typo == "missing":
            text = text[:pos] + text[pos+1:]

        return text


# =============================================================================
# Chaotic Mock Human (Layer 2b - Edge Cases)
# =============================================================================

class ChaoticBehavior(str, Enum):
    """Types of chaotic/problematic human behaviors."""
    SPARSE = "sparse"               # One-word answers
    CONTRADICTORY = "contradictory" # Says yes then no
    UNRESPONSIVE = "unresponsive"   # Never responds (timeout)
    OFF_TOPIC = "off_topic"         # Answers wrong question
    HOSTILE = "hostile"             # Actively unhelpful
    CONFUSED = "confused"           # Misunderstands everything
    DELAYED = "delayed"             # Takes forever to respond
    FLIP_FLOP = "flip_flop"         # Changes mind mid-conversation


class MockHumanChaotic:
    """
    Chaotic mock human for testing system-level resilience.

    Unlike MockHumanNuanced (which adds realistic noise), this mock
    exhibits PROBLEMATIC behaviors to test retry/timeout/escalation logic.

    Usage:
        human = MockHumanChaotic(behavior=ChaoticBehavior.SPARSE)
        response = human.respond(escalation)  # Returns "ok" or "sure"

        human = MockHumanChaotic(behavior=ChaoticBehavior.UNRESPONSIVE)
        response = human.respond(escalation)  # Returns None (timeout)
    """

    # Sparse response templates
    SPARSE_RESPONSES = ["ok", "sure", "yes", "no", "fine", "whatever", "idk", "maybe", "k"]

    # Hostile response templates
    HOSTILE_RESPONSES = [
        "figure it out yourself",
        "why are you asking me",
        "this is stupid",
        "just do whatever",
        "stop bothering me",
        "I don't care",
    ]

    # Off-topic response templates
    OFF_TOPIC_RESPONSES = [
        "Did you see the game last night?",
        "I'm having lunch right now",
        "Can we talk about this later?",
        "What's the weather like?",
        "Sorry, what were we discussing?",
    ]

    def __init__(
        self,
        behavior: ChaoticBehavior,
        severity: float = 1.0,  # 0.0-1.0, how extreme the behavior is
        seed: int = None,
        recovery_after: int = 0,  # Become cooperative after N attempts (0 = never)
    ):
        """
        Initialize chaotic human.

        behavior: The problematic behavior to exhibit
        severity: How extreme (1.0 = always chaotic, 0.5 = 50% chaotic)
        recovery_after: Start behaving normally after N responses (0 = never)
        """
        self.behavior = behavior
        self.severity = severity
        self.recovery_after = recovery_after
        self.rng = random.Random(seed)
        self.response_count = 0
        self.response_history: list[HumanResponse] = []

        # For contradictory behavior: track previous responses
        self._previous_action: Optional[str] = None

    def respond(self, escalation: Escalation) -> Optional[HumanResponse]:
        """
        Respond to escalation with chaotic behavior.

        Returns None for unresponsive behavior (simulates timeout).
        """
        self.response_count += 1

        # Check for recovery
        if self.recovery_after > 0 and self.response_count > self.recovery_after:
            return self._cooperative_response(escalation)

        # Check if we exhibit chaotic behavior this time
        if self.rng.random() > self.severity:
            return self._cooperative_response(escalation)

        # Apply chaotic behavior
        response = self._chaotic_response(escalation)
        if response:
            self.response_history.append(response)
        return response

    def _chaotic_response(self, escalation: Escalation) -> Optional[HumanResponse]:
        """Generate a chaotic response based on behavior type."""

        if self.behavior == ChaoticBehavior.UNRESPONSIVE:
            return None  # Never responds - system should timeout

        if self.behavior == ChaoticBehavior.DELAYED:
            # Return response but with very long delay
            response = self._cooperative_response(escalation)
            if response:
                response.response_time_seconds = self.rng.uniform(3600, 86400)  # 1h to 24h
            return response

        if self.behavior == ChaoticBehavior.SPARSE:
            return HumanResponse(
                escalation_id=escalation.id,
                action="unclear",
                feedback=self.rng.choice(self.SPARSE_RESPONSES),
            )

        if self.behavior == ChaoticBehavior.HOSTILE:
            return HumanResponse(
                escalation_id=escalation.id,
                action="hostile",
                feedback=self.rng.choice(self.HOSTILE_RESPONSES),
            )

        if self.behavior == ChaoticBehavior.OFF_TOPIC:
            return HumanResponse(
                escalation_id=escalation.id,
                action="off_topic",
                feedback=self.rng.choice(self.OFF_TOPIC_RESPONSES),
            )

        if self.behavior == ChaoticBehavior.CONTRADICTORY:
            # Contradict previous response
            if self._previous_action == "approve":
                action = "reject"
                feedback = "Actually, wait, no. I changed my mind."
            elif self._previous_action == "reject":
                action = "approve"
                feedback = "Hmm, on second thought, go ahead."
            else:
                action = self.rng.choice(["approve", "reject"])
                feedback = "Let me think... " + ("yes" if action == "approve" else "no")

            self._previous_action = action
            return HumanResponse(
                escalation_id=escalation.id,
                action=action,
                feedback=feedback,
            )

        if self.behavior == ChaoticBehavior.FLIP_FLOP:
            # Change mind within the same response
            return HumanResponse(
                escalation_id=escalation.id,
                action="unclear",
                feedback="Yes, do it. Actually no. Wait, maybe. Let me think. Yes. No, wait.",
            )

        if self.behavior == ChaoticBehavior.CONFUSED:
            # Respond to a different question entirely
            wrong_responses = [
                ("approve", "The budget looks fine to me"),  # Wrong context
                ("select", "I pick option C"),               # Non-existent option
                ("guidance", "Make sure to update the README"),  # Irrelevant
                ("clarify", "What project is this for again?"),  # Lost context
            ]
            action, feedback = self.rng.choice(wrong_responses)
            return HumanResponse(
                escalation_id=escalation.id,
                action=action,
                feedback=feedback,
            )

        # Fallback
        return self._cooperative_response(escalation)

    def _cooperative_response(self, escalation: Escalation) -> HumanResponse:
        """Generate a normal, cooperative response."""
        if escalation.type == EscalationType.APPROVAL_REQUEST:
            return HumanResponse(
                escalation_id=escalation.id,
                action="approve",
                feedback="Looks good, proceed.",
            )
        elif escalation.type == EscalationType.CONFLICT_RESOLUTION:
            choice = escalation.options[0] if escalation.options else "first option"
            return HumanResponse(
                escalation_id=escalation.id,
                action="select",
                feedback=f"Go with {choice}",
            )
        else:
            return HumanResponse(
                escalation_id=escalation.id,
                action="acknowledge",
                feedback="Understood, proceed as you see fit.",
            )

    def get_behavior_stats(self) -> dict:
        """Get stats about chaotic behavior exhibited."""
        chaotic_count = sum(
            1 for r in self.response_history
            if r.action in ["unclear", "hostile", "off_topic"]
        )
        return {
            "total_responses": self.response_count,
            "chaotic_responses": chaotic_count,
            "behavior": self.behavior.value,
            "severity": self.severity,
            "recovered": self.recovery_after > 0 and self.response_count > self.recovery_after,
        }


# =============================================================================
# Escalation Manager (for integration)
# =============================================================================

class EscalationManager:
    """
    Manages escalations and routes to human (mock or real).

    Integrates with Dashboard for event logging.
    """

    def __init__(
        self,
        project_path: Path,
        human: MockHumanSimple | MockHumanNuanced = None,
        dashboard: Dashboard = None,
    ):
        self.project_path = project_path
        self.human = human or MockHumanSimple()
        self.dashboard = dashboard or Dashboard(project_path)
        self.pending_escalations: list[Escalation] = []
        self.resolved_escalations: list[tuple[Escalation, HumanResponse]] = []
        self._escalation_counter = 0

    def create_escalation(
        self,
        type: EscalationType,
        summary: str,
        context: dict = None,
        options: list[str] = None,
        default_option: str = None,
    ) -> Escalation:
        """Create and queue a new escalation."""
        self._escalation_counter += 1
        escalation = Escalation(
            id=f"esc-{self._escalation_counter:04d}",
            type=type,
            summary=summary,
            context=context or {},
            options=options or [],
            default_option=default_option,
        )

        self.pending_escalations.append(escalation)

        # Log event
        self.dashboard.log_event(
            EventType.ESCALATION_CREATED,
            metadata={
                "escalation_id": escalation.id,
                "type": escalation.type.value,
                "summary": summary,
            },
        )

        return escalation

    def process_pending(self, scenario: str = None) -> list[HumanResponse]:
        """Process all pending escalations."""
        responses = []

        for escalation in self.pending_escalations[:]:  # Copy to allow removal
            if isinstance(self.human, MockHumanNuanced):
                response = self.human.respond(escalation, scenario=scenario)
            else:
                response = self.human.respond(escalation)

            if response:
                self.resolved_escalations.append((escalation, response))
                self.pending_escalations.remove(escalation)
                responses.append(response)

                # Log resolution
                self.dashboard.log_event(
                    EventType.ESCALATION_RESOLVED,
                    metadata={
                        "escalation_id": escalation.id,
                        "action": response.action,
                        "response_time": response.response_time_seconds,
                    },
                )

                # Log human decision
                self.dashboard.log_event(
                    EventType.HUMAN_DECISION,
                    metadata={
                        "escalation_id": escalation.id,
                        "decision": response.action,
                        "feedback": response.feedback,
                    },
                )

        return responses

    def get_pending_count(self) -> int:
        """Get number of pending escalations."""
        return len(self.pending_escalations)

    def get_resolution_stats(self) -> dict:
        """Get statistics on escalation resolution."""
        if not self.resolved_escalations:
            return {"total": 0, "avg_response_time": 0}

        total = len(self.resolved_escalations)
        avg_time = sum(
            r.response_time_seconds
            for _, r in self.resolved_escalations
        ) / total

        actions = {}
        for _, r in self.resolved_escalations:
            actions[r.action] = actions.get(r.action, 0) + 1

        return {
            "total": total,
            "avg_response_time": avg_time,
            "actions": actions,
        }
