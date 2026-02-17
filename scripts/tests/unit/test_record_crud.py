"""Tests for SkillitRecords.entity_crud dispatch."""

import json
import shutil
import uuid
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
    loaded = SkillRecord.init_record(path)
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

    SkillRecord.init_record({"id": "s1", "name": "lint-fix"}, skill_dir)
    loaded = SkillRecord.init_record(skill_dir)

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

    record_json = skill_dir / "record.json"
    if record_json.exists():
        record_json.unlink()
    assert not record_json.exists()

    loaded = SkillRecord.init_record(skill_dir)
    assert record_json.exists()
    payload = json.loads(record_json.read_text(encoding="utf-8"))
    assert payload["id"] == "lint-fix"
    assert payload["name"] == "lint-fix"
    assert loaded.id == "lint-fix"
    assert loaded.name == "lint-fix"

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
    skill = SkillRecord.init_record(
        {
            "id": "acli-jira-subcommand-syntax",
            "name": "acli-jira-subcommand-syntax",
            "status": "active",
        },
        skill_dir,
    )
    assert skill is not None
    assert (skill_dir / "record.json").exists()
    loaded_skill = SkillRecord.init_record(skill_dir)
    assert loaded_skill.id == skill.id
    assert loaded_skill.name == "acli-jira-subcommand-syntax"
    child_record_text_before = (skill_dir / "record.json").read_text(encoding="utf-8")
    restored.add_child(loaded_skill)
    child_record_text_after = (skill_dir / "record.json").read_text(encoding="utf-8")
    assert child_record_text_after == child_record_text_before

    restored_skill = restored.get_children_by_type(RecordType.SKILL)[0]
    assert restored_skill.id == skill.id
    assert restored_skill.name == skill.name


def test_skill_copy_to_claude_user_home(tmp_path):
    skill_name = f"skillit-home-copy-{uuid.uuid4().hex[:8]}"
    skill_dir = tmp_path / skill_name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        (
            "---\n"
            f"name: {skill_name}\n"
            "description: >\n"
            "  Copy this skill to Claude user home for global usage.\n"
            "---\n\n"
            "# Home Copy Skill\n"
        ),
        encoding="utf-8",
    )

    source_record_json = skill_dir / "record.json"
    if source_record_json.exists():
        source_record_json.unlink()
    assert not source_record_json.exists()

    local_skill = SkillRecord.init_record(skill_dir)
    assert source_record_json.exists()
    source_payload = json.loads(source_record_json.read_text(encoding="utf-8"))
    assert source_payload["id"] == skill_name
    assert source_payload["name"] == skill_name
    assert local_skill.id == skill_name
    assert local_skill.name == skill_name

    home_skill_dir = Path.home() / ".claude" / "skills" / skill_name
    if home_skill_dir.exists():
        shutil.rmtree(home_skill_dir)

    try:
        copied_path = local_skill.copy_to_claude_user_home()
        assert copied_path == home_skill_dir
        assert (home_skill_dir / "SKILL.md").exists()

        home_record_json = home_skill_dir / "record.json"
        if home_record_json.exists():
            home_record_json.unlink()
        assert not home_record_json.exists()

        loaded_from_home = SkillRecord.init_record(home_skill_dir)
        assert home_record_json.exists()
        home_payload = json.loads(home_record_json.read_text(encoding="utf-8"))
        assert home_payload["id"] == skill_name
        assert home_payload["name"] == skill_name
        assert loaded_from_home.id == skill_name
        assert loaded_from_home.name == skill_name
    finally:
        if home_skill_dir.exists():
            shutil.rmtree(home_skill_dir)

    # missing lines:"
    # task
    # sync
