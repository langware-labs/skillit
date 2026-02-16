"""Tests for SkillitRecords.entity_crud dispatch."""

import shutil
from pathlib import Path

import pytest

from fs_store.record_types import RecordType
from plugin_records.skillit_records import SkillitRecords
from records.skill_record import SkillRecord


def test_entity_crud_creates_session_and_skill(tmp_path):
    mgr = SkillitRecords(records_path=tmp_path)
    assert mgr.get_session("s1") is None
    result = mgr.entity_crud("s1", "create", {"type": RecordType.SKILL, "name": "x"})
    assert "Created" in result
    assert mgr.get_session("s1") is not None


def test_entity_crud_unknown_op_returns_error(tmp_path):
    mgr = SkillitRecords(records_path=tmp_path)
    result = mgr.entity_crud("s1", "drop", {"type": RecordType.SKILL})
    assert "Error" in result


def test_skill_record_save_and_read(tmp_path):
    path = tmp_path / "skill-@s1" / "record.json"
    path.parent.mkdir(parents=True)
    SkillRecord(id="s1", name="lint-fix", status="active").save_record_json(path)
    loaded = SkillRecord.load_record(path)
    assert loaded.name == "lint-fix"
    assert loaded.status == "active"
    assert loaded.type == RecordType.SKILL


def test_skill_record_dynamic_props_from_yaml_file(tmp_path):
    skill_dir = tmp_path / "skill-@s1"
    skill_dir.mkdir(parents=True)
    (skill_dir / "skill.yaml").write_text(
        "owner: platform\npriority: 3\nenabled: true\n",
        encoding="utf-8",
    )

    SkillRecord.init({"id": "s1", "name": "lint-fix"}, skill_dir)
    loaded = SkillRecord.load_record(skill_dir)

    assert loaded.owner == "platform"
    assert loaded.priority == 3
    assert loaded.enabled is True


def test_skill_record_dynamic_props_from_skill_md_frontmatter(tmp_path):
    skill_dir = tmp_path / "skill-@s1"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        (
            "---\n"
            "name: lint-fix\n"
            "description: >\n"
            "  Linting fixes and formatting guidance.\n"
            "category: quality\n"
            "---\n\n"
            "# Skill\n"
        ),
        encoding="utf-8",
    )

    SkillRecord.init({"id": "s1", "name": "lint-fix"}, skill_dir)
    loaded = SkillRecord.load_record(skill_dir)

    assert loaded.category == "quality"
    assert "Linting fixes" in str(loaded.yaml_fields.get("description"))


@pytest.mark.parametrize(
    "session_id,relative_session_dir",
    [
        (
            "d7dd8377-c888-40e5-98ea-899ed95c7eeb",
            "scripts/tests/unit/resources/skillit_session-@d7dd8377-c888-40e5-98ea-899ed95c7eeb",
        )
    ],
)
def test_session_restore(tmp_path, session_id, relative_session_dir):
    source_dir = Path(relative_session_dir)
    if not source_dir.exists():
        source_dir = Path(__file__).resolve().parents[3] / relative_session_dir
    assert source_dir.exists(), f"fixture not found: {source_dir}"

    session_root = tmp_path / "skillit_session"
    restored_session_dir = session_root / source_dir.name
    shutil.copytree(source_dir, restored_session_dir)

    mgr = SkillitRecords(records_path=tmp_path)
    restored = mgr.get_session(session_id)
    assert restored is not None
    assert restored.id == session_id
    assert restored.session_id == session_id
    assert restored.record_dir == restored_session_dir

    output_dir = restored.output_dir
    assert output_dir == restored_session_dir / "output"
    assert (output_dir / "analysis.md").exists()
    skill_dir = output_dir / "acli-jira-subcommand-syntax"
    assert skill_dir.exists()
    skill = SkillRecord.init(
        {
            "id": "acli-jira-subcommand-syntax",
            "name": "acli-jira-subcommand-syntax",
            "status": "active",
        },
        skill_dir,
    )
    assert skill is not None
    assert (skill_dir / "record.json").exists()
    loaded_skill = SkillRecord.load_record(skill_dir)
    assert loaded_skill.id == skill.id
    assert loaded_skill.name == "acli-jira-subcommand-syntax"
