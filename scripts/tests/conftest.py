"""Pytest fixtures for hook testing."""

import pytest
from tests.test_utils import HookTestEnvironment


@pytest.fixture
def isolated_hook_env():
    """Provides a clean test environment with plugin copied to temp folder."""
    env = HookTestEnvironment()
    yield env
    env.cleanup()
