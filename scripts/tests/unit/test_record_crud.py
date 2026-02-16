"""Tests for SkillitRecords.entity_crud dispatch."""

import pytest

from records.skill_record import SkillRecord
from plugin_records.skillit_records import SkillitRecords


def test_entity_crud_creates_session_and_dispatches(tmp_path):
    mgr = SkillitRecords(records_path=tmp_path)
    assert mgr.get_session("s1") is None
    with pytest.raises(NotImplementedError):
        mgr.entity_crud("s1", "create", {"type": "skill", "skill_name": "x"})
    assert mgr.get_session("s1") is not None


def test_entity_crud_unknown_op_returns_error(tmp_path):
    mgr = SkillitRecords(records_path=tmp_path)
    result = mgr.entity_crud("s1", "drop", {"type": "skill"})
    assert "Error" in result


def test_skill_record_save_and_read(tmp_path):
    path = tmp_path / "skill-@s1" / "record.json"
    path.parent.mkdir(parents=True)
    SkillRecord(id="s1", name="lint-fix", status="active").save_record_json(path)
    loaded = SkillRecord.load_record(path)
    assert loaded.name == "lint-fix"
    assert loaded.status == "active"
    assert loaded.type == "skill"
