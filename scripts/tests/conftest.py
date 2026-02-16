"""Pytest fixtures for hook testing."""

import sys
import pytest

from plugin_records import skillit_records
from utils.log import skill_log, skill_log_print, skill_log_clear
from tests.test_utils import TestPluginProjectEnvironment


@pytest.fixture(scope="session", autouse=True)
def configure_utf8_output():
    """Configure stdout/stderr to use UTF-8 encoding on Windows.

    This is needed to handle emojis in print statements when running tests.
    """
    if sys.platform == "win32":
        # Reconfigure stdout and stderr to use UTF-8 encoding
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")


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
