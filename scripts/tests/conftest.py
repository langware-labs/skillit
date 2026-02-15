"""Pytest fixtures for hook testing."""

import pytest

from utils.log import skill_log, skill_log_print, skill_log_clear
from tests.test_utils import TestPluginProjectEnvironment


@pytest.fixture(scope="function")
def isolated_hook_env():
    """Provides a clean test environment with plugin installed at project scope."""
    env = TestPluginProjectEnvironment()
    skill_log_clear()
    env.install_plugin()
    print(f"Test environment set up at: {env.path}")
    yield env
    skill_log_print()
    env.cleanup()
