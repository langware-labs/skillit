"""Tests for SkillitConfig record."""

import json

from fs_store import SkillitRecordType
from plugin_records.skillit_config import SkillitConfig


class TestDefaults:
    def test_user_rules_enabled_defaults_true(self):
        c = SkillitConfig()
        assert c.user_rules_enabled is True

    def test_type_defaults_to_skillit_config(self):
        c = SkillitConfig()
        assert c.type == SkillitRecordType.SKILLIT_CONFIG

    def test_name_defaults_to_skillit_config(self):
        c = SkillitConfig()
        assert c.name == "skillit_config"


class TestJsonRoundTrip:
    def test_round_trip(self, tmp_path):
        fp = tmp_path / "config.json"
        c = SkillitConfig(user_rules_enabled=False)
        c.to_json(fp)
        loaded = SkillitConfig.from_json(fp)
        assert loaded.user_rules_enabled is False
        assert loaded.type == SkillitRecordType.SKILLIT_CONFIG

    def test_from_json_missing_file_creates_defaults(self, tmp_path):
        fp = tmp_path / "missing.json"
        c = SkillitConfig.from_json(fp)
        assert c.user_rules_enabled is True
        assert c.type == SkillitRecordType.SKILLIT_CONFIG
        assert c.source_file == str(fp)

    def test_fs_sync_auto_persist(self, tmp_path):
        fp = tmp_path / "config.json"
        c = SkillitConfig.from_json(fp)
        c.to_json(fp)
        c.fs_sync = True
        c.user_rules_enabled = False
        data = json.loads(fp.read_text())
        assert data["user_rules_enabled"] is False
