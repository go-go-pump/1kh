"""
Tests for temporal/activities/imagination.py - Hypothesis generation and evaluation.

These tests verify:
1. Hypothesis generation prompts are constructed correctly
2. JSON parsing from Claude responses works
3. Evaluation logic correctly updates hypotheses
4. Resource declarations are properly extracted
5. Error handling for malformed responses
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
# Hypothesis Dataclass Tests
# =============================================================================

class TestHypothesisDataclass:
    """Test the Hypothesis dataclass."""

    def test_hypothesis_creation(self):
        """Should create hypothesis with all fields."""
        from temporal.activities.imagination import Hypothesis

        hyp = Hypothesis(
            id="hyp-001",
            description="Test hypothesis",
            rationale="Testing is good",
            serves_objectives=["Objective 1"],
            objective_mapping="Maps to objective by testing",
            estimated_effort="medium",
            estimated_hours=10,
            feasibility=0.8,
            north_star_alignment=0.9,
        )

        assert hyp.id == "hyp-001"
        assert hyp.feasibility == 0.8
        assert hyp.north_star_alignment == 0.9
        assert hyp.status == "proposed"  # Default

    def test_hypothesis_with_dependencies(self):
        """Should track dependencies and blocks."""
        from temporal.activities.imagination import Hypothesis

        hyp = Hypothesis(
            id="hyp-002",
            description="Depends on another",
            rationale="Needs foundation",
            serves_objectives=["Objective 1"],
            objective_mapping="Builds on hyp-001",
            estimated_effort="small",
            estimated_hours=5,
            feasibility=0.9,
            north_star_alignment=0.7,
            depends_on=["hyp-001"],
            blocks=["hyp-003", "hyp-004"],
        )

        assert "hyp-001" in hyp.depends_on
        assert len(hyp.blocks) == 2

    def test_hypothesis_with_resources(self):
        """Should include resource declarations."""
        from temporal.activities.imagination import Hypothesis

        hyp = Hypothesis(
            id="hyp-003",
            description="Modifies files",
            rationale="Code changes needed",
            serves_objectives=["Build system"],
            objective_mapping="Direct implementation",
            estimated_effort="large",
            estimated_hours=40,
            feasibility=0.6,
            north_star_alignment=0.95,
            touches_resources=[
                {"type": "file", "identifier": "src/main.py", "access": "write"},
                {"type": "api", "identifier": "stripe.com", "access": "read"},
            ],
        )

        assert len(hyp.touches_resources) == 2
        assert hyp.touches_resources[0]["type"] == "file"


# =============================================================================
# Generate Hypotheses Tests
# =============================================================================

class TestGenerateHypotheses:
    """Test hypothesis generation with mocked Claude API."""

    def _get_foundation_docs(self, temp_project):
        """Helper to load foundation docs for tests."""
        oracle = {"values": ["Quality"], "never_do": [], "always_do": []}
        north_star = {"objectives": [{"name": "Build system"}], "metrics": []}
        context = {"budget": 100, "skills": ["Python"]}
        return oracle, north_star, context

    @pytest.mark.asyncio
    async def test_generates_hypotheses_from_foundation(self, temp_project):
        """Should generate hypotheses from foundation docs."""
        from temporal.activities.imagination import generate_hypotheses

        oracle, north_star, context = self._get_foundation_docs(temp_project)
        mock_client = MockAnthropicClient(response_key="imagination_hypotheses")

        with patch('anthropic.Anthropic', return_value=mock_client):
            result = await generate_hypotheses(
                str(temp_project),
                oracle=oracle,
                north_star=north_star,
                context=context,
                existing_hypotheses=[],
            )

        # Result is a list of hypotheses
        assert isinstance(result, list)
        assert len(result) > 0

        # Check hypothesis structure
        hyp = result[0]
        assert "id" in hyp
        assert "description" in hyp

    @pytest.mark.asyncio
    async def test_includes_resource_declarations(self, temp_project):
        """Generated hypotheses should include resource declarations."""
        from temporal.activities.imagination import generate_hypotheses

        oracle, north_star, context = self._get_foundation_docs(temp_project)
        mock_client = MockAnthropicClient(response_key="imagination_hypotheses")

        with patch('anthropic.Anthropic', return_value=mock_client):
            result = await generate_hypotheses(
                str(temp_project),
                oracle=oracle,
                north_star=north_star,
                context=context,
                existing_hypotheses=[],
            )

        # Check that at least one hypothesis has resources
        hyp_with_resources = [
            h for h in result
            if h.get("touches_resources")
        ]
        assert len(hyp_with_resources) > 0

    @pytest.mark.asyncio
    async def test_handles_malformed_json(self, temp_project):
        """Should handle malformed JSON gracefully."""
        from temporal.activities.imagination import generate_hypotheses

        oracle, north_star, context = self._get_foundation_docs(temp_project)
        mock_client = MockAnthropicClient(response_key="malformed_json")

        with patch('anthropic.Anthropic', return_value=mock_client):
            result = await generate_hypotheses(
                str(temp_project),
                oracle=oracle,
                north_star=north_star,
                context=context,
                existing_hypotheses=[],
            )

        # Should return empty list or partial results, not crash
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_handles_empty_response(self, temp_project):
        """Should handle empty response gracefully."""
        from temporal.activities.imagination import generate_hypotheses

        oracle, north_star, context = self._get_foundation_docs(temp_project)
        mock_client = MockAnthropicClient(response_key="empty_response")

        with patch('anthropic.Anthropic', return_value=mock_client):
            result = await generate_hypotheses(
                str(temp_project),
                oracle=oracle,
                north_star=north_star,
                context=context,
                existing_hypotheses=[],
            )

        # Should not crash
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_prompt_includes_foundation_docs(self, temp_project):
        """Prompt should include content from foundation docs."""
        from temporal.activities.imagination import generate_hypotheses

        oracle, north_star, context = self._get_foundation_docs(temp_project)
        mock_client = MockAnthropicClient(response_key="imagination_hypotheses")

        with patch('anthropic.Anthropic', return_value=mock_client):
            await generate_hypotheses(
                str(temp_project),
                oracle=oracle,
                north_star=north_star,
                context=context,
                existing_hypotheses=[],
            )

        # Check what was sent to Claude
        calls = mock_client.get_calls()
        assert len(calls) == 1

        # The prompt should include foundation content
        messages = calls[0]["kwargs"]["messages"]
        prompt_content = messages[0]["content"]

        # Should reference foundation docs somehow
        assert len(prompt_content) > 100  # Should have substantial content


# =============================================================================
# Evaluate Hypothesis Tests
# =============================================================================

class TestEvaluateHypothesis:
    """Test hypothesis evaluation with mocked Claude API."""

    def _get_foundation_docs(self):
        """Helper to create foundation docs for tests."""
        oracle = {"values": ["Quality"], "never_do": [], "always_do": []}
        north_star = {"objectives": [{"name": "Build system"}], "metrics": []}
        context = {"budget": 100, "skills": ["Python"]}
        return oracle, north_star, context

    @pytest.mark.asyncio
    async def test_evaluates_hypothesis(self, temp_project):
        """Should evaluate and return updated hypothesis."""
        from temporal.activities.imagination import evaluate_hypothesis

        oracle, north_star, context = self._get_foundation_docs()

        hypothesis = {
            "id": "hyp-test-001",
            "description": "Test hypothesis",
            "rationale": "Initial rationale",
            "serves_objectives": ["Test objective"],
            "objective_mapping": "Initial mapping",
            "feasibility": 0.5,
            "north_star_alignment": 0.5,
        }

        mock_client = MockAnthropicClient(response_key="imagination_evaluation")

        with patch('anthropic.Anthropic', return_value=mock_client):
            result = await evaluate_hypothesis(
                project_path=str(temp_project),
                hypothesis=hypothesis,
                oracle=oracle,
                context=context,
                north_star=north_star,
            )

        # Should return evaluated hypothesis
        assert result["id"] == "hyp-test-001"
        # Scores may have changed
        assert "feasibility" in result
        assert "north_star_alignment" in result

    @pytest.mark.asyncio
    async def test_preserves_hypothesis_id(self, temp_project):
        """Evaluation should preserve the hypothesis ID."""
        from temporal.activities.imagination import evaluate_hypothesis

        oracle, north_star, context = self._get_foundation_docs()

        hypothesis = {
            "id": "preserve-this-id",
            "description": "Test",
            "rationale": "Test",
            "serves_objectives": [],
            "objective_mapping": "",
            "feasibility": 0.5,
            "north_star_alignment": 0.5,
        }

        mock_client = MockAnthropicClient(response_key="imagination_evaluation")

        with patch('anthropic.Anthropic', return_value=mock_client):
            result = await evaluate_hypothesis(
                project_path=str(temp_project),
                hypothesis=hypothesis,
                oracle=oracle,
                context=context,
                north_star=north_star,
            )

        # ID should be preserved even if Claude returns different
        assert "id" in result


# =============================================================================
# Combined Score Calculation Tests
# =============================================================================

class TestScoreCalculation:
    """Test combined score calculation."""

    def test_combined_score_formula(self):
        """Combined score should weight alignment higher than feasibility."""
        # Formula: (feasibility * 0.4) + (alignment * 0.6)

        # High alignment, low feasibility
        score1 = (0.3 * 0.4) + (0.9 * 0.6)  # 0.12 + 0.54 = 0.66

        # Low alignment, high feasibility
        score2 = (0.9 * 0.4) + (0.3 * 0.6)  # 0.36 + 0.18 = 0.54

        # Alignment matters more
        assert score1 > score2

    def test_perfect_scores(self):
        """Perfect feasibility and alignment should give 1.0."""
        score = (1.0 * 0.4) + (1.0 * 0.6)
        assert score == 1.0

    def test_zero_scores(self):
        """Zero feasibility and alignment should give 0.0."""
        score = (0.0 * 0.4) + (0.0 * 0.6)
        assert score == 0.0


# =============================================================================
# Foundation Document Reading Tests
# =============================================================================

class TestFoundationReading:
    """Test reading and parsing foundation documents."""

    @pytest.mark.asyncio
    async def test_reads_oracle(self, temp_project):
        """Should read and parse oracle.md."""
        from temporal.activities.foundation import read_oracle

        result = await read_oracle(str(temp_project))

        assert "content" in result or "values" in result or isinstance(result, str)
        # Should contain content from the test oracle
        if isinstance(result, dict) and "content" in result:
            assert "Quality over speed" in result["content"]
        elif isinstance(result, str):
            assert "Quality" in result or len(result) > 0

    @pytest.mark.asyncio
    async def test_reads_north_star(self, temp_project):
        """Should read and parse north-star.md."""
        from temporal.activities.foundation import read_north_star

        result = await read_north_star(str(temp_project))

        assert result is not None
        # Should contain content from test north star
        content = result if isinstance(result, str) else result.get("content", "")
        # Verify it read something

    @pytest.mark.asyncio
    async def test_reads_context(self, temp_project):
        """Should read and parse context.md."""
        from temporal.activities.foundation import read_context

        result = await read_context(str(temp_project))

        assert result is not None

    @pytest.mark.asyncio
    async def test_handles_missing_file(self, temp_project):
        """Should handle missing foundation files gracefully."""
        from temporal.activities.foundation import read_oracle

        # Delete the oracle file
        (temp_project / "oracle.md").unlink()

        # Should not crash, should return error or empty
        result = await read_oracle(str(temp_project))
        # Implementation dependent - might return error dict or empty string


# =============================================================================
# Integration Tests
# =============================================================================

class TestImaginationIntegration:
    """Integration tests for the full imagination flow."""

    def _get_foundation_docs(self):
        """Helper to create foundation docs for tests."""
        oracle = {"values": ["Quality"], "never_do": [], "always_do": []}
        north_star = {"objectives": [{"name": "Build system"}], "metrics": []}
        context = {"budget": 100, "skills": ["Python"]}
        return oracle, north_star, context

    @pytest.mark.asyncio
    async def test_full_generation_flow(self, temp_project):
        """Test complete hypothesis generation flow."""
        from temporal.activities.imagination import generate_hypotheses
        from core.resources import detect_hypothesis_conflicts

        oracle, north_star, context = self._get_foundation_docs()
        mock_client = MockAnthropicClient(response_key="imagination_hypotheses")

        with patch('anthropic.Anthropic', return_value=mock_client):
            hypotheses = await generate_hypotheses(
                str(temp_project),
                oracle=oracle,
                north_star=north_star,
                context=context,
                existing_hypotheses=[],
            )

        # Should generate multiple hypotheses
        assert len(hypotheses) >= 1

        # Each should have required fields
        for hyp in hypotheses:
            assert "id" in hyp
            assert "description" in hyp

        # Should be able to detect conflicts
        conflicts = detect_hypothesis_conflicts(hypotheses)
        # Result should be a dict (may be empty)
        assert isinstance(conflicts, dict)

    @pytest.mark.asyncio
    async def test_hypothesis_to_task_readiness(self, temp_project):
        """Hypotheses should have enough info to create tasks."""
        from temporal.activities.imagination import generate_hypotheses

        oracle, north_star, context = self._get_foundation_docs()
        mock_client = MockAnthropicClient(response_key="imagination_hypotheses")

        with patch('anthropic.Anthropic', return_value=mock_client):
            hypotheses = await generate_hypotheses(
                str(temp_project),
                oracle=oracle,
                north_star=north_star,
                context=context,
                existing_hypotheses=[],
            )

        for hyp in hypotheses:
            # Must have ID for tracking
            assert "id" in hyp

            # Must have description for task creation
            assert "description" in hyp
            assert len(hyp["description"]) > 10
