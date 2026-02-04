"""
Mock implementations for testing.

These mocks allow testing without:
- Burning API tokens (Claude API)
- Connecting to Temporal Cloud
- Making real network requests
- Waiting for real execution
"""
from .claude_client import MockAnthropicClient, MOCK_RESPONSES
from .execution import (
    MockExecutor,
    ScenarioExecutor,
    ProgressionSimulator,
    ExecutionOutcome,
    MetricProgression,
)
from .human import (
    MockHumanSimple,
    MockHumanNuanced,
    MockHumanChaotic,
    ChaoticBehavior,
    EscalationManager,
    Escalation,
    EscalationType,
    HumanResponse,
)

__all__ = [
    # Claude mock
    "MockAnthropicClient",
    "MOCK_RESPONSES",
    # Execution mock
    "MockExecutor",
    "ScenarioExecutor",
    "ProgressionSimulator",
    "ExecutionOutcome",
    "MetricProgression",
    # Human mock
    "MockHumanSimple",
    "MockHumanNuanced",
    "MockHumanChaotic",
    "ChaoticBehavior",
    "EscalationManager",
    "Escalation",
    "EscalationType",
    "HumanResponse",
]
