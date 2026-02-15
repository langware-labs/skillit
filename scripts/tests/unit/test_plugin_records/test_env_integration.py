"""Tests for TestPluginProjectEnvironment.user_rules_enabled proxy."""

import json

from tests.test_utils.hook_environment import TestPluginProjectEnvironment


class TestEnvUserRulesEnabled:
    def test_defaults_to_true(self):
        env = TestPluginProjectEnvironment(dump=False)
        assert env.user_rules_enabled is True

    def test_setter_changes_value(self):
        env = TestPluginProjectEnvironment(dump=False)
        env.user_rules_enabled = False
        assert env.user_rules_enabled is False

    def test_change_persists_to_disk(self):
        env = TestPluginProjectEnvironment(dump=False)
        env.user_rules_enabled = False
        fp = env.temp_dir / ".flow" / "records" / "skillit_config" / "record.json"
        assert fp.exists()
        data = json.loads(fp.read_text())
        assert data["user_rules_enabled"] is False
