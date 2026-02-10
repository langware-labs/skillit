"""Pytest fixtures for hook testing."""

import pytest
from tests.test_utils import HookTestProjectEnvironment


@pytest.fixture(scope="function")
def isolated_hook_env():
    """Provides a clean test environment with plugin installed at project scope."""
    env = HookTestProjectEnvironment()
    env.install_plugin()
    yield env
    env.cleanup()
