"""Pytest fixtures for hook testing."""

import pytest

from plugin_records import skillit_records
from utils.log import skill_log, skill_log_print, skill_log_clear
from tests.test_utils import TestPluginProjectEnvironment


@pytest.fixture(scope="function")
def isolated_hook_env():
    """Provides a clean test environment with plugin installed at project scope."""
    env = TestPluginProjectEnvironment()
    skillit_records.config.user_rules_enabled = False
    skill_log_clear()
    env.install_plugin()
    print(f"Test environment set up at: {env.path}")
    yield env
    skillit_records.config.user_rules_enabled = True
    skill_log_print()
    env.cleanup()
