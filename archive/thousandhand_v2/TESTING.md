# ThousandHand (1KH) Testing Guide

## Quick Start

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core --cov=temporal --cov-report=term-missing

# Run specific test categories
pytest tests/test_dashboard.py -v           # Dashboard tests
pytest tests/test_resources.py -v           # Resource locking tests
pytest tests/test_cycle_e2e.py -v           # End-to-end cycle tests
```

## Test Structure

```
tests/
├── conftest.py                  # Shared fixtures
├── mocks/
│   ├── __init__.py             # Export all mocks
│   ├── claude_client.py        # MockAnthropicClient
│   ├── execution.py            # MockExecutor, ScenarioExecutor, ProgressionSimulator
│   ├── human.py                # MockHumanSimple, MockHumanNuanced, EscalationManager
│   └── temporal.py             # MockTemporalClient, MockWorkflow
├── test_cycle_e2e.py           # Layer 2a end-to-end tests
├── test_dashboard.py           # Dashboard/event log tests
├── test_imagination.py         # Hypothesis generation tests
├── test_intent.py              # INTENT loop tests
├── test_resources.py           # Resource locking tests
├── test_work.py                # Task execution tests
└── TEST_SCENARIOS.md           # Coverage matrix documentation
```

## Mock Components

### MockAnthropicClient
Simulates Claude API without burning tokens:

```python
from tests.mocks import MockAnthropicClient, MOCK_RESPONSES

# Use predefined responses
mock = MockAnthropicClient(response_key="imagination_hypotheses")

# Use custom response
mock = MockAnthropicClient(custom_response="Custom JSON response")

# Simulate errors
mock = MockAnthropicClient()
mock.set_error(Exception("API rate limit exceeded"))

# Inspect calls
calls = mock.get_calls()  # List of {messages, model, response}
```

### MockExecutor / ScenarioExecutor
Simulates task execution with realistic outcomes:

```python
from core.dashboard import Dashboard
from tests.mocks import MockExecutor, ScenarioExecutor

dashboard = Dashboard(project_path)

# Random success/failure based on rate
executor = MockExecutor(project_path, dashboard, success_rate=0.8)
outcome = executor.execute(task, hypothesis)

# Deterministic scenarios
executor = ScenarioExecutor(project_path, dashboard)
executor.queue_scenario("success_large")   # High revenue
executor.queue_scenario("failure_transient")  # Transient error
outcome = executor.execute(task)
```

Available scenarios:
- `success_small` - Minor metrics improvement
- `success_large` - Major metrics improvement
- `failure_transient` - Retryable error
- `failure_permanent` - Fatal error
- `partial_success` - Mixed results
- `blocked` - Needs human intervention

### MockHumanSimple / MockHumanNuanced
Simulates human responses to escalations:

```python
from tests.mocks import MockHumanSimple, MockHumanNuanced, EscalationManager

# Simple: Configurable patterns
human = MockHumanSimple(patterns={
    "conflict_resolution": "prioritize_first",
    "approval_request": "always_approve",
    "guidance_request": "provide_default",
})

# Nuanced: Realistic behaviors
human = MockHumanNuanced(behaviors={
    "typo_rate": 0.05,
    "misunderstand_rate": 0.1,
    "delay_variance": 0.5,
    "abandon_rate": 0.02,
})

# Use with EscalationManager
manager = EscalationManager(project_path, human=human, dashboard=dashboard)
manager.create_escalation(
    type=EscalationType.APPROVAL_REQUEST,
    summary="Deploy to production?",
)
responses = manager.process_pending()
```

### ProgressionSimulator
Simulates multi-cycle runs to reach North Star:

```python
from tests.mocks import ProgressionSimulator

simulator = ProgressionSimulator(
    project_path,
    north_star_target=10000,  # $10K MRR
    cycles_to_reach=20,        # Expected cycles
)

# Run 3 cycles
for _ in range(3):
    result = simulator.simulate_cycle()
    print(f"Revenue: ${result['total_revenue']}")

# Run until target reached
history = simulator.run_to_completion(max_cycles=50)
```

## Test Layers

| Layer | Claude | Human | Dashboard | Execution | Purpose |
|-------|--------|-------|-----------|-----------|---------|
| 1     | Mock   | N/A   | N/A       | N/A       | Unit tests |
| 2a    | Mock   | Mock (simple) | Mock (fixed) | Mock | Deterministic E2E |
| 2b    | Mock   | Mock (nuanced) | Mock (events) | Mock | Edge cases |
| 3     | Real   | Mock  | Mock      | Mock      | Claude integration |
| 4     | Real   | Real  | Mock      | Mock      | Human verification |

## Running Layer 2a Tests

```bash
# All Layer 2a tests
pytest tests/test_cycle_e2e.py -v

# Happy paths only
pytest tests/test_cycle_e2e.py::TestHappyPaths -v

# Sad paths only
pytest tests/test_cycle_e2e.py::TestSadPaths -v

# Human interaction tests
pytest tests/test_cycle_e2e.py::TestHumanInteraction -v

# Full integration
pytest tests/test_cycle_e2e.py::TestFullCycleIntegration -v
```

## Standalone Test Runner

For environments with limited Python stdlib, use the standalone runner:

```bash
python run_tests.py
```

This bypasses pytest and runs core tests directly.

## Adding New Tests

### Happy Path Test
```python
@pytest.mark.asyncio
async def test_h_new_scenario(self, temp_project):
    """
    H[N]: Description of happy path scenario.
    """
    from temporal.activities.imagination import generate_hypotheses

    mock_claude = MockAnthropicClient(response_key="imagination_hypotheses")
    with patch('anthropic.Anthropic', return_value=mock_claude):
        hypotheses = await generate_hypotheses(...)

    assert len(hypotheses) > 0
```

### Sad Path Test
```python
def test_s_new_failure(self, temp_project):
    """
    S[N]: Description of failure scenario.
    """
    dashboard = Dashboard(temp_project)
    executor = ScenarioExecutor(temp_project, dashboard)
    executor.queue_scenario("failure_transient")

    outcome = executor.execute(task)
    assert outcome.success is False
```

### Human Interaction Test
```python
def test_hi_new_interaction(self, temp_project):
    """
    HI[N]: Description of human interaction.
    """
    human = MockHumanSimple(patterns={"approval_request": "always_reject"})
    manager = EscalationManager(temp_project, human=human)

    manager.create_escalation(...)
    responses = manager.process_pending()

    assert responses[0].action == "reject"
```
