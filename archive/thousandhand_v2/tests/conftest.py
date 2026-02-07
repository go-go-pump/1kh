"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest and provides:
1. Common fixtures for all tests
2. Mock configurations
3. Temporary project setup/teardown
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch
import tempfile
import shutil

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Project Fixtures - Create temporary 1KH projects for testing
# =============================================================================

@pytest.fixture
def temp_project(tmp_path):
    """
    Create a temporary 1KH project structure.

    Provides a fully initialized project with:
    - oracle.md
    - north-star.md
    - context.md
    - .1kh/ directory with config

    Yields the project path, cleans up after test.
    """
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    # Create .1kh directory
    kh_dir = project_path / ".1kh"
    kh_dir.mkdir()

    # Create foundation docs
    (project_path / "oracle.md").write_text("""# Oracle - Test Project

## Values
- Quality over speed
- Test everything

## Never Do
- Ship untested code
- Ignore errors

## Always Do
- Write tests first
- Document decisions
""")

    (project_path / "north-star.md").write_text("""# North Star - Test Project

## Primary Objective
Build a reliable test system

## Success Metrics
- 100% test coverage on critical paths
- Zero production bugs from tested code

## Deadline
2025-12-31
""")

    (project_path / "context.md").write_text("""# Context - Test Project

## Budget
- Monthly: $100
- Total: $500

## Time
- Weekly hours: 10

## Skills
- Python
- Testing
- API design

## Constraints
- Must run offline
- No external dependencies for core logic
""")

    # Create config
    config = {
        "project_name": "test-project",
        "created_at": datetime.utcnow().isoformat(),
        "version": "0.1.0",
    }
    (kh_dir / "config.json").write_text(json.dumps(config, indent=2))

    # Create .env with fake API key
    (kh_dir / ".env").write_text("ANTHROPIC_API_KEY=test-key-not-real\n")

    yield project_path

    # Cleanup is automatic with tmp_path


@pytest.fixture
def temp_project_with_hypotheses(temp_project):
    """
    Create a temp project with pre-generated hypotheses.

    Useful for testing INTENT and WORK loops.
    """
    hyp_dir = temp_project / ".1kh" / "hypotheses"
    hyp_dir.mkdir(parents=True)

    hypotheses = [
        {
            "id": "hyp-001",
            "description": "Build user authentication system",
            "rationale": "Users need to log in",
            "serves_objectives": ["Build a reliable test system"],
            "objective_mapping": "Auth enables user-specific features",
            "estimated_effort": "medium",
            "estimated_hours": 20,
            "feasibility": 0.8,
            "north_star_alignment": 0.9,
            "depends_on": [],
            "blocks": ["hyp-002"],
            "risks": ["Security vulnerabilities"],
            "assumptions": ["Users have email addresses"],
            "touches_resources": [
                {"type": "file", "identifier": "src/auth/login.py", "access": "write"},
                {"type": "file", "identifier": "src/auth/session.py", "access": "write"},
                {"type": "database", "identifier": "users_table", "access": "write"},
            ],
            "status": "proposed",
        },
        {
            "id": "hyp-002",
            "description": "Build user profile page",
            "rationale": "Users want to see their info",
            "serves_objectives": ["Build a reliable test system"],
            "objective_mapping": "Profiles show user data",
            "estimated_effort": "small",
            "estimated_hours": 8,
            "feasibility": 0.9,
            "north_star_alignment": 0.7,
            "depends_on": ["hyp-001"],
            "blocks": [],
            "risks": ["UI complexity"],
            "assumptions": ["Auth system exists"],
            "touches_resources": [
                {"type": "file", "identifier": "src/ui/profile.py", "access": "write"},
            ],
            "status": "proposed",
        },
        {
            "id": "hyp-003",
            "description": "Refactor authentication to use OAuth",
            "rationale": "Better security with OAuth",
            "serves_objectives": ["Build a reliable test system"],
            "objective_mapping": "OAuth is more secure",
            "estimated_effort": "large",
            "estimated_hours": 40,
            "feasibility": 0.6,
            "north_star_alignment": 0.8,
            "depends_on": [],
            "blocks": [],
            "risks": ["Breaking existing auth"],
            "assumptions": ["OAuth provider available"],
            "touches_resources": [
                {"type": "file", "identifier": "src/auth/login.py", "access": "write"},
                {"type": "api", "identifier": "oauth.provider.com", "access": "read"},
            ],
            "status": "proposed",
        },
    ]

    (hyp_dir / "hypotheses.json").write_text(json.dumps(hypotheses, indent=2))

    return temp_project, hypotheses


# =============================================================================
# Claude API Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_claude_response():
    """
    Factory fixture to create mock Claude API responses.

    Usage:
        def test_something(mock_claude_response):
            response = mock_claude_response("Hello, world!")
            assert response.content[0].text == "Hello, world!"
    """
    def _create_response(text: str, stop_reason: str = "end_turn"):
        response = MagicMock()
        content_block = MagicMock()
        content_block.text = text
        response.content = [content_block]
        response.stop_reason = stop_reason
        response.usage = MagicMock(input_tokens=100, output_tokens=50)
        return response

    return _create_response


@pytest.fixture
def mock_anthropic_client(mock_claude_response):
    """
    Create a mock Anthropic client that returns predefined responses.

    By default returns a simple acknowledgment. Use set_response() to
    customize what Claude "says" for specific tests.

    Usage:
        def test_imagination(mock_anthropic_client):
            # Set up what Claude should "respond" with
            mock_anthropic_client.set_response('''
            ```json
            {"hypotheses": [...]}
            ```
            ''')

            # Now run your code that calls Anthropic API
            result = generate_hypotheses(...)
    """
    client = MagicMock()

    # Default response
    default_text = "I understand. How can I help?"
    client._response_text = default_text

    def set_response(text: str):
        client._response_text = text

    client.set_response = set_response

    def create_message(**kwargs):
        return mock_claude_response(client._response_text)

    client.messages.create = MagicMock(side_effect=create_message)

    return client


@pytest.fixture
def patch_anthropic(mock_anthropic_client):
    """
    Patch the Anthropic client globally for a test.

    Usage:
        def test_something(patch_anthropic):
            patch_anthropic.set_response("Custom response")
            # Any code that imports Anthropic will get the mock
    """
    with patch('anthropic.Anthropic', return_value=mock_anthropic_client):
        yield mock_anthropic_client


# =============================================================================
# Resource Testing Fixtures
# =============================================================================

@pytest.fixture
def resource_queue(temp_project):
    """
    Create a ResourceQueue for testing.
    """
    from core.resources import ResourceQueue
    return ResourceQueue(temp_project)


@pytest.fixture
def sample_resources():
    """
    Provide sample Resource objects for testing.
    """
    from core.resources import Resource, ResourceType

    return {
        "file_write": Resource(
            type=ResourceType.FILE,
            identifier="src/main.py",
            access="write",
        ),
        "file_read": Resource(
            type=ResourceType.FILE,
            identifier="src/main.py",
            access="read",
        ),
        "file_other": Resource(
            type=ResourceType.FILE,
            identifier="src/utils.py",
            access="write",
        ),
        "glob_src": Resource(
            type=ResourceType.FILE_GLOB,
            identifier="src/*.py",
            access="write",
        ),
        "api_stripe": Resource(
            type=ResourceType.API,
            identifier="stripe.com/v1/customers",
            access="write",
        ),
        "database": Resource(
            type=ResourceType.DATABASE,
            identifier="users_table",
            access="write",
        ),
    }


# =============================================================================
# Async Testing Support
# =============================================================================

@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Environment Helpers
# =============================================================================

@pytest.fixture(autouse=True)
def clean_environment():
    """
    Ensure clean environment for each test.

    - Removes any 1KH-specific env vars that might leak between tests
    - Resets any global state
    """
    # Store original env
    original_env = os.environ.copy()

    # Remove any 1KH env vars
    for key in list(os.environ.keys()):
        if key.startswith("1KH_") or key.startswith("TEMPORAL_"):
            del os.environ[key]

    yield

    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


# =============================================================================
# Logging Helpers
# =============================================================================

@pytest.fixture
def capture_logs(caplog):
    """
    Capture log output for assertions.

    Usage:
        def test_logging(capture_logs):
            # Do something that logs
            some_function()

            assert "Expected message" in capture_logs.text
    """
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog
