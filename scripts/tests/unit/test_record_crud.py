"""Tests for SkillitRecords.entity_crud — session CRUD operations."""

import json

from plugin_records.skillit_skill import SkillitSkill


def test_skill_record_save_and_read(tmp_path):
    record_path = tmp_path / "skill-@s1" / "record.json"
    record_path.parent.mkdir(parents=True)

    skill = SkillitSkill(
        id="s1",
        skill_name="lint-fix",
        description="Auto-fix lint errors",
        version="1.0",
        author="alice",
        status="active",
    )
    skill.to_json(record_path)

    loaded = SkillitSkill.from_json(record_path)

    assert loaded.id == "s1"
    assert loaded.skill_name == "lint-fix"
    assert loaded.description == "Auto-fix lint errors"
    assert loaded.version == "1.0"
    assert loaded.author == "alice"
    assert loaded.status == "active"
    assert loaded.type == "skill"
