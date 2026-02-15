"""Tests for SkillitRecords manager."""

import json

from plugin_records.skillit_config import SkillitConfig
from plugin_records.skillit_session import SkillitSession
from plugin_records.skillit_records import SkillitRecords


class TestConfig:
    def test_config_lazy_creates_with_fs_sync(self, tmp_path):
        mgr = SkillitRecords(records_path=tmp_path)
        cfg = mgr.config
        assert isinstance(cfg, SkillitConfig)
        assert cfg.fs_sync is True

    def test_config_is_cached(self, tmp_path):
        mgr = SkillitRecords(records_path=tmp_path)
        assert mgr.config is mgr.config

    def test_config_loads_existing_file(self, tmp_path):
        cfg_dir = tmp_path / "skillit_config"
        cfg_dir.mkdir(parents=True)
        fp = cfg_dir / "record.json"
        fp.write_text(json.dumps({
            "user_rules_enabled": False,
            "type": "skillit_config",
            "name": "skillit_config",
        }))
        mgr = SkillitRecords(records_path=tmp_path)
        assert mgr.config.user_rules_enabled is False

    def test_config_changes_persist_to_disk(self, tmp_path):
        mgr = SkillitRecords(records_path=tmp_path)
        mgr.config.user_rules_enabled = False
        fp = tmp_path / "skillit_config" / "record.json"
        data = json.loads(fp.read_text())
        assert data["user_rules_enabled"] is False

    def test_reset_clears_cache(self, tmp_path):
        mgr = SkillitRecords(records_path=tmp_path)
        cfg1 = mgr.config
        mgr.reset()
        cfg2 = mgr.config
        assert cfg1 is not cfg2


class TestSessions:
    def test_sessions_collection_works(self, tmp_path):
        mgr = SkillitRecords(records_path=tmp_path)
        s = mgr.sessions.create(SkillitSession(session_id="s1"))
        assert s.session_id == "s1"
        found = mgr.sessions.get("s1")
        assert found is not None

    def test_sessions_is_cached(self, tmp_path):
        mgr = SkillitRecords(records_path=tmp_path)
        assert mgr.sessions is mgr.sessions
