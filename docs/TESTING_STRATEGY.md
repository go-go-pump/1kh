# ThousandHand Testing Strategy

## Overview

Testing is organized into three tiers:

| Tier | Focus | API Calls | Speed | Purpose |
|------|-------|-----------|-------|---------|
| **Unit** | Individual functions | None | Fast | Validate logic in isolation |
| **Integration** | Module interactions | Mocked | Medium | Validate component wiring |
| **E2E Smoke** | Full demo flows | None | Fast | Validate user-facing behavior |

---

## Tier 1: Unit Tests (Fast, No API)

### Module Coverage Goals

| Module | Key Functions to Test | Priority |
|--------|----------------------|----------|
| `core/reflection.py` | Completeness check, trajectory analysis, recommendations | HIGH |
| `core/hypothesis.py` | Vendor detection, preference loading, two-level split | HIGH |
| `core/runner.py` | Cycle state management, phase callbacks | HIGH |
| `core/dashboard.py` | Event logging, state computation, metrics | MEDIUM |
| `core/report.py` | HTML generation, data formatting | LOW |

### Example Unit Tests

```python
# tests/unit/test_reflection.py
def test_missing_payment_blocks_revenue():
    """System without payment should report can_generate_revenue=False."""
    engine = ReflectionEngine(project_path, mock_dashboard_no_payment)
    result = engine._check_completeness()

    assert result.can_generate_revenue == False
    assert "payment" in str(result.blockers).lower()

def test_stalled_trajectory_detected():
    """Plateau in metrics should be detected."""
    engine = ReflectionEngine(project_path, mock_dashboard_stalled)
    result = engine._analyze_trajectory()

    assert result.trend == "plateau"
    assert result.stall_cycles >= 2

def test_pivot_recommendation_on_failures():
    """Repeated failures should trigger pivot recommendation."""
    engine = ReflectionEngine(project_path, mock_dashboard_failures)
    result = engine.reflect(cycle_number=5)

    pivots = [r for r in result.recommendations if r.type == "pivot"]
    assert len(pivots) == 1
    assert pivots[0].needs_human_decision == True
```

```python
# tests/unit/test_hypothesis.py
def test_vendor_detection_payment():
    """Payment category should be detected from hypothesis."""
    hyp = {"description": "Enable payment processing", "category": "payment"}
    manager = HypothesisManager(project_path)

    assert manager.needs_implementation_decision(hyp) == True

def test_preference_loading_simple_format():
    """Simple preference format should work."""
    # preferences.json: {"payment": "stripe"}
    manager = PreferencesManager(project_path)
    pref = manager.get_preference("payment")

    assert pref.preferred == "stripe"

def test_preference_loading_full_format():
    """Full preference format should work."""
    # preferences.json: {"payment": {"preferred": "stripe", "reason": "..."}}
    manager = PreferencesManager(project_path)
    pref = manager.get_preference("payment")

    assert pref.preferred == "stripe"
    assert pref.reason is not None
```

---

## Tier 2: Integration Tests (Mocked API)

### Scenario-Based Testing

These test complete flows with all modules wired together but using mocks for external services.

```python
# tests/integration/test_augment_flow.py
async def test_missing_payment_triggers_augment():
    """When payment is missing, AUGMENT recommendation should guide hypotheses."""
    runner = create_demo_runner(project_path, scenario="missing-payment")

    # Run one cycle
    await runner._run_single_cycle()

    # Check reflection detected the issue
    assert runner._last_reflection["completeness"]["can_generate_revenue"] == False

    # Check hypotheses were guided to fix it
    hyps = runner.deps.dashboard.get_hypotheses()
    payment_hyps = [h for h in hyps if "payment" in h.description.lower()]
    assert len(payment_hyps) >= 1

async def test_stalled_triggers_optimize():
    """When metrics plateau, OPTIMIZE recommendation should appear."""
    runner = create_demo_runner(project_path, scenario="stalled")

    # Run several cycles to trigger stall detection
    for _ in range(4):
        await runner._run_single_cycle()

    # Check optimization recommendation
    recs = runner._last_reflection.get("recommendations", [])
    optimize_recs = [r for r in recs if r.get("type") == "optimize"]
    assert len(optimize_recs) >= 1

async def test_pivot_asks_human():
    """When repeated failures occur, PIVOT should ask human."""
    decisions_made = []

    def mock_pivot_callback(context):
        decisions_made.append(context)
        return "pivot_market"

    runner = create_demo_runner(
        project_path,
        scenario="pivot-needed",
        on_pivot_decision_needed=mock_pivot_callback,
    )

    # Run enough cycles to trigger pivot
    for _ in range(3):
        await runner._run_single_cycle()

    assert len(decisions_made) >= 1
    assert decisions_made[0]["consecutive_failures"] >= 3

async def test_vendor_selection_asks_user():
    """When hypothesis needs vendor, callback should be invoked."""
    selections_made = []

    def mock_vendor_callback(prompt, options):
        selections_made.append({"prompt": prompt, "options": options})
        return "stripe"

    runner = create_demo_runner(
        project_path,
        scenario="vendor-choice",
        on_vendor_selection_needed=mock_vendor_callback,
    )

    await runner._run_single_cycle()

    assert len(selections_made) >= 1
    assert "payment" in selections_made[0]["prompt"].lower()
```

### Business vs Non-Business Focus

```python
# tests/integration/test_business_flows.py
"""Tests focused on BUSINESS outcomes."""

async def test_revenue_generation_path():
    """Complete path from $0 to revenue."""
    runner = create_demo_runner(project_path, max_cycles=10)
    summary = await runner.run()

    assert summary["current_revenue"] > 0
    assert summary["tasks_succeeded"] > 0

async def test_north_star_progress():
    """Progress toward north star is tracked."""
    runner = create_demo_runner(project_path, max_cycles=20)
    summary = await runner.run()

    assert summary["progress_pct"] > 0

# tests/integration/test_technical_flows.py
"""Tests focused on TECHNICAL correctness."""

async def test_cycle_state_persistence():
    """Run state should persist across runs."""
    runner1 = create_demo_runner(project_path, max_cycles=3)
    await runner1.run()

    # Create new runner, should resume
    runner2 = create_demo_runner(project_path, max_cycles=3)
    assert runner2.cycle_count == 3  # Resumed from previous

async def test_callbacks_called_in_order():
    """Callbacks should be called in correct phase order."""
    phase_order = []

    def track_phase(phase):
        phase_order.append(phase)

    runner = create_demo_runner(
        project_path,
        max_cycles=1,
        on_phase_start=track_phase,
    )
    await runner.run()

    expected = ["reflection", "imagination", "intent", "work", "execution"]
    assert phase_order == expected
```

---

## Tier 3: E2E Smoke Tests (Demo Mode)

These are CLI-level tests that verify the full user experience.

```python
# tests/e2e/test_demo_smoke.py
import subprocess

def test_demo_runs_without_error():
    """Demo mode should complete without crashing."""
    result = subprocess.run(
        ["1kh", "run", "cycle", "--demo", "--max", "3", "--fresh"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0
    assert "Demo Summary" in result.stdout
    assert "Cycles completed: 3" in result.stdout

def test_scenario_missing_payment():
    """Missing payment scenario should show AUGMENT."""
    result = subprocess.run(
        ["1kh", "run", "cycle", "--demo", "--scenario", "missing-payment", "--max", "2"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0
    # Should mention payment in output
    assert "payment" in result.stdout.lower()

def test_fresh_clears_state():
    """--fresh should clear previous state."""
    # Run once
    subprocess.run(["1kh", "run", "cycle", "--demo", "--max", "2"])

    # Run with fresh
    result = subprocess.run(
        ["1kh", "run", "cycle", "--demo", "--max", "1", "--fresh"],
        capture_output=True,
        text=True,
    )

    assert "Cleared previous data" in result.stdout
    assert "Cycle 1" in result.stdout  # Should start from 1, not 3
```

---

## Running Tests

```bash
# All unit tests (fast)
pytest tests/unit/ -v

# All integration tests (medium)
pytest tests/integration/ -v

# All e2e smoke tests
pytest tests/e2e/ -v

# With coverage
pytest tests/ --cov=core --cov=cli --cov-report=html

# Specific module coverage
pytest tests/unit/test_reflection.py --cov=core/reflection --cov-report=term-missing
```

---

## Coverage Goals

| Module | Target | Rationale |
|--------|--------|-----------|
| `core/reflection.py` | 90%+ | Critical for system self-awareness |
| `core/hypothesis.py` | 90%+ | Critical for decision-making |
| `core/runner.py` | 80%+ | Complex orchestration |
| `core/dashboard.py` | 70%+ | State management |
| `cli/commands/run.py` | 60%+ | User interface |

---

## Next Steps

1. **Immediate**: Run demo scenarios to verify they work
2. **Short-term**: Write unit tests for reflection and hypothesis modules
3. **Medium-term**: Add integration tests for scenario flows
4. **Before Temporal**: Complete e2e smoke tests for all demo scenarios
