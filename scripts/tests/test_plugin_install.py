"""Tests for plugin installation via HookTestEnvironment."""

import json
from pathlib import Path

from tests.test_utils.hook_environment import HookTestEnvironment, SKILLIT_ROOT


def test_install_plugin_creates_project_settings():
    """Plugin install should write enabledPlugins into .claude/settings.json."""
    env = HookTestEnvironment()
    env.install_plugin()

    settings_path = env.path / ".claude" / "settings.json"
    assert settings_path.exists(), "settings.json was not created"

    settings = json.loads(settings_path.read_text())
    assert "enabledPlugins" in settings, "enabledPlugins missing from settings"
    assert any(
        "skillit" in key for key in settings["enabledPlugins"]
    ), "skillit plugin not found in enabledPlugins"


def test_installed_version_matches_source():
    """Installed (cached) plugin version should match the source plugin.json."""
    env = HookTestEnvironment()
    env.install_plugin()

    source_version = json.loads(
        (SKILLIT_ROOT / ".claude-plugin" / "plugin.json").read_text()
    )["version"]

    installed_version = env.installed_plugin_version()
    assert installed_version is not None, "Plugin not found in cache"
    assert installed_version == source_version, (
        f"Version mismatch: source={source_version}, installed={installed_version}"
    )


def test_install_plugin_caches_hooks():
    """The cached plugin should contain hooks/hooks.json."""
    env = HookTestEnvironment()
    env.install_plugin()

    plugin_name, marketplace_name, version = env._read_plugin_meta()
    cached_hooks = (
        Path.home() / ".claude" / "plugins" / "cache"
        / marketplace_name / plugin_name / version
        / "hooks" / "hooks.json"
    )
    assert cached_hooks.exists(), "hooks.json not found in plugin cache"

    hooks = json.loads(cached_hooks.read_text())
    assert "hooks" in hooks, "hooks key missing from hooks.json"
    assert "UserPromptSubmit" in hooks["hooks"], "UserPromptSubmit hook not configured"
