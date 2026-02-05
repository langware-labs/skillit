"""Tests for plugin installation via HookTestEnvironment."""

import json
from pathlib import Path

from tests.test_utils import PromptResult
from tests.test_utils.hook_environment import HookTestEnvironment, SKILLIT_ROOT
from plugin_manager import SkillitPluginManager


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


def test_patch_installs_new_version():
    """Bumping the patch version and reinstalling should update the cache."""
    plugin_mgr = SkillitPluginManager()
    old_version = plugin_mgr.version
    new_version = plugin_mgr.patch()
    print(f"old_version={old_version}, new_version={new_version}")
    assert new_version != old_version

    env = HookTestEnvironment()
    env.install_plugin()

    result:PromptResult = env.launch_claude('use the skillit sugagent  and ask for its version, make sure to invoken it', False)
    assert new_version in result.stdout

def test_activation_dump():
    """Bumping the patch version and reinstalling should update the cache."""
    env = HookTestEnvironment()
    print(f"env path: {env.path}")
    env.install_plugin()
    env.dump_activations= True
    no_secret_result:PromptResult = env.launch_claude('is 42', False)
    assert env.dump_file is not None
    assert env.dump_file.exists()


def test_secret_word_install():
    """Bumping the patch version and reinstalling should update the cache."""
    env = HookTestEnvironment()
    print(f"env path: {env.path}")
    env.install_plugin()
    no_secret_result:PromptResult = env.launch_claude('is 42', False)

    assert '443216' not in no_secret_result.stdout
    env.load_rule("secret_word")
    secret_result: PromptResult = env.launch_claude('skillit, is 42', False)
    assert '443216' in secret_result.stdout