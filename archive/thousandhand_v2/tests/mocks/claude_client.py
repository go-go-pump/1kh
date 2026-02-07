"""
Mock Anthropic Claude client for testing.

This allows us to:
1. Test without burning API tokens
2. Get deterministic responses for assertions
3. Simulate various response scenarios (errors, timeouts, etc.)

Usage:
    from tests.mocks import MockAnthropicClient, MOCK_RESPONSES

    # Use a predefined response
    client = MockAnthropicClient(response_key="imagination_hypotheses")
    response = client.messages.create(...)

    # Use a custom response
    client = MockAnthropicClient(custom_response="Hello!")
    response = client.messages.create(...)

    # Simulate an error
    client = MockAnthropicClient(error=anthropic.APIError("Rate limited"))
    with pytest.raises(anthropic.APIError):
        client.messages.create(...)
"""
from dataclasses import dataclass, field
from typing import Optional, Any
import json


# =============================================================================
# Predefined Mock Responses
# =============================================================================

MOCK_RESPONSES = {
    # Imagination loop - hypothesis generation
    "imagination_hypotheses": '''Based on the foundation documents, here are comprehensive hypotheses:

```json
{
  "hypotheses": [
    {
      "id": "hyp-test-001",
      "description": "Build a CLI tool for task management",
      "rationale": "Users need a simple interface to interact with the system",
      "serves_objectives": ["Build a reliable test system"],
      "objective_mapping": "CLI enables direct user interaction with core features",
      "estimated_effort": "medium",
      "estimated_hours": 16,
      "feasibility": 0.85,
      "north_star_alignment": 0.9,
      "depends_on": [],
      "blocks": ["hyp-test-002"],
      "risks": ["Scope creep in CLI features"],
      "assumptions": ["Users prefer CLI over GUI"],
      "touches_resources": [
        {"type": "file", "identifier": "cli/main.py", "access": "write"},
        {"type": "file", "identifier": "cli/commands/*.py", "access": "write"}
      ],
      "status": "proposed"
    },
    {
      "id": "hyp-test-002",
      "description": "Add configuration file support",
      "rationale": "Users want to customize behavior without code changes",
      "serves_objectives": ["Build a reliable test system"],
      "objective_mapping": "Config files enable user customization",
      "estimated_effort": "small",
      "estimated_hours": 8,
      "feasibility": 0.95,
      "north_star_alignment": 0.7,
      "depends_on": ["hyp-test-001"],
      "blocks": [],
      "risks": ["Config format confusion"],
      "assumptions": ["YAML is acceptable format"],
      "touches_resources": [
        {"type": "file", "identifier": "core/config.py", "access": "write"}
      ],
      "status": "proposed"
    }
  ]
}
```
''',

    # Imagination loop - hypothesis evaluation
    # Note: The code expects nested structure with {score, reasoning} for feasibility/alignment
    "imagination_evaluation": '''After deep evaluation of the hypothesis:

```json
{
  "feasibility": {
    "score": 0.82,
    "reasoning": "The team has the skills and resources to build this. Main challenge is time estimation."
  },
  "north_star_alignment": {
    "score": 0.92,
    "reasoning": "Directly addresses user interaction needs. High impact on adoption."
  },
  "oracle_compliance": {
    "compliant": true,
    "notes": "No violations of core values detected."
  },
  "risks": [
    {"risk": "Scope creep in CLI features", "severity": "medium", "mitigation": "Strict feature prioritization"},
    {"risk": "Cross-platform compatibility", "severity": "low", "mitigation": "Use cross-platform libraries"}
  ],
  "updated_estimates": {
    "effort": "medium",
    "hours": 20
  },
  "evaluation_notes": "Strong alignment with objectives. Main risk is scope management."
}
```
''',

    # Work loop - task creation
    "work_task_creation": '''Based on the hypothesis, here is the task breakdown:

```json
{
  "description": "Implement basic CLI structure with Typer framework",
  "task_type": "build",
  "acceptance_criteria": [
    "CLI responds to --help flag",
    "Basic command structure in place",
    "Entry point configured in pyproject.toml"
  ],
  "estimated_minutes": 45,
  "requires_human": false,
  "human_reason": null,
  "touches_resources": [
    {"type": "file", "identifier": "cli/main.py", "access": "write"},
    {"type": "file", "identifier": "pyproject.toml", "access": "write"}
  ]
}
```
''',

    # Work loop - task execution (research)
    "work_research_result": '''## Research Summary

Based on my analysis, here are the key findings:

### Current State
- The codebase uses Python 3.10+
- Typer is already installed as a dependency
- Basic CLI structure exists but needs expansion

### Recommendations
1. Follow the existing command pattern in `cli/commands/`
2. Add comprehensive help text for discoverability
3. Include shell completion support

### Sources
- Internal codebase analysis
- Typer documentation best practices
''',

    # Work loop - task execution (build)
    "work_build_result": '''## Implementation Plan

### Files to Create/Modify

1. **cli/commands/new_feature.py**
```python
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def run():
    console.print("[green]Feature executed![/green]")
```

2. **cli/main.py** - Add import and register

### Dependencies
- No new dependencies required

### Testing Approach
- Unit tests for command logic
- Integration tests for CLI invocation
''',

    # Error scenarios
    "empty_response": "",

    "malformed_json": '''Here is the result:
```json
{
  "hypotheses": [
    {"id": "broken", description: missing quotes}
  ]
}
```
''',

    # Simple acknowledgments
    "simple_ack": "I understand. I'll proceed with the task.",

    "thinking": "Let me think about this carefully...\n\nAfter consideration, I believe the best approach is to start with the core functionality and iterate from there.",
}


# =============================================================================
# Mock Response Objects
# =============================================================================

@dataclass
class MockContentBlock:
    """Simulates anthropic.types.ContentBlock"""
    text: str
    type: str = "text"


@dataclass
class MockUsage:
    """Simulates anthropic.types.Usage"""
    input_tokens: int = 100
    output_tokens: int = 50


@dataclass
class MockMessage:
    """Simulates anthropic.types.Message"""
    content: list
    stop_reason: str = "end_turn"
    usage: MockUsage = field(default_factory=MockUsage)
    model: str = "claude-sonnet-4-20250514"
    id: str = "msg_mock_12345"


# =============================================================================
# Mock Client
# =============================================================================

class MockMessagesAPI:
    """Mock for client.messages"""

    def __init__(self, parent: "MockAnthropicClient"):
        self._parent = parent

    def create(self, **kwargs) -> MockMessage:
        """
        Simulate messages.create() call.

        Records the call for later inspection and returns mock response.
        """
        # Record the call
        self._parent._calls.append({
            "method": "messages.create",
            "kwargs": kwargs,
        })

        # Check for error simulation
        if self._parent._error:
            raise self._parent._error

        # Get response text
        if self._parent._custom_response is not None:
            text = self._parent._custom_response
        elif self._parent._response_key:
            text = MOCK_RESPONSES.get(
                self._parent._response_key,
                MOCK_RESPONSES["simple_ack"]
            )
        else:
            text = MOCK_RESPONSES["simple_ack"]

        # Handle response sequence (for multi-turn tests)
        if self._parent._response_sequence:
            if self._parent._sequence_index < len(self._parent._response_sequence):
                text = self._parent._response_sequence[self._parent._sequence_index]
                self._parent._sequence_index += 1

        return MockMessage(
            content=[MockContentBlock(text=text)],
            stop_reason=self._parent._stop_reason,
        )


class MockAnthropicClient:
    """
    Mock Anthropic client for testing.

    Examples:
        # Basic usage with predefined response
        client = MockAnthropicClient(response_key="imagination_hypotheses")

        # Custom response
        client = MockAnthropicClient(custom_response="Hello!")

        # Simulate error
        client = MockAnthropicClient(error=Exception("API Error"))

        # Response sequence (for multi-turn conversations)
        client = MockAnthropicClient(response_sequence=[
            "First response",
            "Second response",
        ])

        # Check what was called
        client.messages.create(model="...", messages=[...])
        assert len(client.get_calls()) == 1
        assert client.get_calls()[0]["kwargs"]["model"] == "..."
    """

    def __init__(
        self,
        response_key: Optional[str] = None,
        custom_response: Optional[str] = None,
        response_sequence: Optional[list[str]] = None,
        error: Optional[Exception] = None,
        stop_reason: str = "end_turn",
        api_key: str = "mock-api-key",
    ):
        self._response_key = response_key
        self._custom_response = custom_response
        self._response_sequence = response_sequence or []
        self._sequence_index = 0
        self._error = error
        self._stop_reason = stop_reason
        self._calls: list[dict] = []

        # Public attributes that real client has
        self.api_key = api_key

        # Sub-APIs
        self.messages = MockMessagesAPI(self)

    def get_calls(self) -> list[dict]:
        """Get list of all API calls made."""
        return self._calls.copy()

    def reset_calls(self):
        """Clear recorded calls."""
        self._calls.clear()
        self._sequence_index = 0

    def set_response(self, text: str):
        """Set a custom response for next call."""
        self._custom_response = text

    def set_response_key(self, key: str):
        """Set response to a predefined mock."""
        self._response_key = key
        self._custom_response = None

    def set_error(self, error: Exception):
        """Set an error to raise on next call."""
        self._error = error

    def clear_error(self):
        """Clear any pending error."""
        self._error = None


# =============================================================================
# Pytest Fixtures (also available here for direct import)
# =============================================================================

def create_mock_client(response_key: str = "simple_ack") -> MockAnthropicClient:
    """Factory function to create mock clients."""
    return MockAnthropicClient(response_key=response_key)


def patch_anthropic_module(mock_client: MockAnthropicClient):
    """
    Context manager to patch the anthropic module.

    Usage:
        mock = MockAnthropicClient(response_key="imagination_hypotheses")
        with patch_anthropic_module(mock):
            # Code that imports and uses Anthropic
            from anthropic import Anthropic
            client = Anthropic()  # Returns mock
    """
    from unittest.mock import patch
    return patch('anthropic.Anthropic', return_value=mock_client)
