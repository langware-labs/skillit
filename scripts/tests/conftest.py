"""Pytest fixtures for hook testing."""

import pytest
from tests.test_utils import HookTestEnvironment


@pytest.fixture
def isolated_hook_env():
    """Provides a clean test environment with plugin installed at project scope."""
    env = HookTestEnvironment()
    env.install_plugin()
    yield env
    env.cleanup()
