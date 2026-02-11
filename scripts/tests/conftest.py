"""Pytest fixtures for hook testing."""

import pytest
from tests.test_utils import TestPluginProjectEnvironment


@pytest.fixture(scope="function")
def isolated_hook_env():
    """Provides a clean test environment with plugin installed at project scope."""
    env = TestPluginProjectEnvironment()
    env.install_plugin()
    yield env
    env.cleanup()
