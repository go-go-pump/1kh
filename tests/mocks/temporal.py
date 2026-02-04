"""
Mock Temporal components for testing.

Allows testing workflows and activities without running Temporal server.
"""
from unittest.mock import MagicMock, AsyncMock
from functools import wraps


class MockActivity:
    """Mock for temporalio.activity module."""

    def __init__(self):
        self._heartbeats = []
        self._logs = []

    def heartbeat(self, detail=None):
        """Record heartbeat."""
        self._heartbeats.append(detail)

    @property
    def logger(self):
        """Return mock logger."""
        logger = MagicMock()
        logger.info = lambda msg: self._logs.append(("info", msg))
        logger.error = lambda msg: self._logs.append(("error", msg))
        logger.warning = lambda msg: self._logs.append(("warning", msg))
        logger.debug = lambda msg: self._logs.append(("debug", msg))
        return logger

    def defn(self, func):
        """Mock @activity.defn decorator - just return the function."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper

    def get_heartbeats(self):
        """Get recorded heartbeats for assertions."""
        return self._heartbeats

    def get_logs(self):
        """Get recorded logs for assertions."""
        return self._logs

    def reset(self):
        """Reset recorded data."""
        self._heartbeats = []
        self._logs = []


class MockWorkflow:
    """Mock for temporalio.workflow module."""

    def __init__(self):
        self._logs = []

    @property
    def logger(self):
        """Return mock logger."""
        logger = MagicMock()
        logger.info = lambda msg: self._logs.append(("info", msg))
        logger.error = lambda msg: self._logs.append(("error", msg))
        return logger

    def defn(self, cls):
        """Mock @workflow.defn decorator."""
        return cls

    def run(self, func):
        """Mock @workflow.run decorator."""
        return func

    def query(self, func):
        """Mock @workflow.query decorator."""
        return func

    def signal(self, func):
        """Mock @workflow.signal decorator."""
        return func

    class unsafe:
        @staticmethod
        def imports_passed_through():
            """Mock context manager for imports."""
            class NullContext:
                def __enter__(self):
                    return None
                def __exit__(self, *args):
                    pass
            return NullContext()


# Global instances for easy patching
mock_activity = MockActivity()
mock_workflow = MockWorkflow()


def patch_temporal():
    """
    Context manager to patch Temporal imports.

    Usage:
        with patch_temporal():
            from temporal.activities.work import execute_task
            # Activities will use mocks
    """
    from unittest.mock import patch
    import sys

    # Create mock modules
    mock_temporalio = MagicMock()
    mock_temporalio.activity = mock_activity
    mock_temporalio.workflow = mock_workflow

    return patch.dict(sys.modules, {
        'temporalio': mock_temporalio,
        'temporalio.activity': mock_activity,
        'temporalio.workflow': mock_workflow,
    })
