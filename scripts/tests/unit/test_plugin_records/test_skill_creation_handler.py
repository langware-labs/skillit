"""Tests for SkillCreationHandler — the full skill creation → copy-to-home flow.

Covers:
- on_create creates a TaskResource + AgenticProcess + RelationshipRecord
- on_update (triggered by flow_tag skill_ready) marks them complete
- on_update scans output_dir for skill folders and copies to ~/.claude/skills/
- entity_crud("update") doesn't raise and lets handlers fire
- get_children_by_type returns properly-typed SkillRecord instances
"""

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from flow_sdk.fs_store import FsRecordRef, RecordType
from plugin_records.crud_handlers.skill_creation_handler import (
    SkillCreationHandler,
    skill_creation_handler,
)
from plugin_records.skillit_records import SkillitRecords
from plugin_records.skillit_session import SkillitSession
from flow_sdk.fs_records.skill_record import SkillRecord


@pytest.fixture
def records_env(tmp_path):
    """Create an isolated SkillitRecords environment with a session and skill in output_dir."""
    records_path = tmp_path / "records"
    records_path.mkdir()
    mgr = SkillitRecords(records_path=records_path)

    session_id = "test-session-123"
    session = mgr.create_session(session_id)

    # Create a skill folder in the session output dir with SKILL.md
    # (simulates what the skillit-creator agent does)
    skill_name = "my-test-skill"
    skill_dir = session.output_dir / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-test-skill\ndescription: A test skill\n---\n# Test Skill\n"
    )

    # Also register the skill in the global skills collection and as session child
    skill = SkillRecord(id=skill_name, name=skill_name, description="A test skill")
    mgr.skills.save(skill)
    skill_ref = FsRecordRef.from_record(skill)
    session.add_child(skill_ref)

    return {
        "mgr": mgr,
        "session_id": session_id,
        "session": session,
        "skill_name": skill_name,
        "skill_dir": skill_dir,
        "records_path": records_path,
        "tmp_path": tmp_path,
    }


class TestOnCreate:
    """Test that on_create properly creates task/process/relationship resources."""

    @patch("plugin_records.crud_handlers.skill_creation_handler.send_entity_sync")
    def test_on_create_returns_resources(self, mock_sync, records_env):
        session = records_env["session"]
        session_id = records_env["session_id"]

        result = skill_creation_handler.on_create(
            session_id, session, RecordType.SKILL, {"type": "skill", "name": "test"}
        )

        assert result is not None
        assert result.task is not None
        assert result.process is not None
        assert result.relationship is not None

    @patch("plugin_records.crud_handlers.skill_creation_handler.send_entity_sync")
    def test_on_create_skips_without_session_id(self, mock_sync, records_env):
        session = records_env["session"]

        result = skill_creation_handler.on_create(
            None, session, RecordType.SKILL, {"type": "skill"}
        )

        assert result is None
        mock_sync.assert_not_called()

    @patch("plugin_records.crud_handlers.skill_creation_handler.send_entity_sync")
    def test_on_create_syncs_entities(self, mock_sync, records_env):
        session = records_env["session"]
        session_id = records_env["session_id"]

        skill_creation_handler.on_create(
            session_id, session, RecordType.SKILL, {"type": "skill", "name": "test"}
        )

        # Should sync task, process, and relationship
        assert mock_sync.call_count == 3


class TestOnUpdate:
    """Test that on_update marks resources complete and copies skills."""

    @patch("plugin_records.crud_handlers.skill_creation_handler.send_entity_sync")
    def test_on_update_skips_non_done_status(self, mock_sync, records_env):
        session = records_env["session"]
        session_id = records_env["session_id"]

        skill_creation_handler.on_update(
            session_id, session, RecordType.SKILL, {"status": "creating"}
        )

        mock_sync.assert_not_called()

    @patch("plugin_records.crud_handlers.skill_creation_handler.send_entity_sync")
    def test_on_update_copies_skills_from_output_dir(self, mock_sync, records_env):
        """on_update scans output_dir for skill folders and copies them."""
        session = records_env["session"]
        session_id = records_env["session_id"]
        skill_name = records_env["skill_name"]
        tmp_path = records_env["tmp_path"]

        # Set up task in session record (as on_create does)
        skill_creation_handler.on_create(
            session_id, session, RecordType.SKILL, {"type": "skill", "name": skill_name}
        )

        # on_update with status=new should copy skills to ~/.claude/skills/
        with patch("flow_sdk.fs_records.skill_record.Path.home", return_value=tmp_path):
            skill_creation_handler.on_update(
                session_id, session, RecordType.SKILL, {"status": "new", "folder_name": skill_name}
            )

        expected_dest = tmp_path / ".claude" / "skills" / skill_name
        assert expected_dest.exists(), "Skill should be copied to user home"
        assert (expected_dest / "SKILL.md").exists()

    @patch("plugin_records.crud_handlers.skill_creation_handler.send_entity_sync")
    def test_on_update_copies_multiple_skills(self, mock_sync, records_env):
        """on_update should copy all skill folders from output_dir."""
        session = records_env["session"]
        session_id = records_env["session_id"]
        skill_name = records_env["skill_name"]
        tmp_path = records_env["tmp_path"]

        # Create a second skill in output_dir
        second_skill_dir = session.output_dir / "second-skill"
        second_skill_dir.mkdir(parents=True, exist_ok=True)
        (second_skill_dir / "SKILL.md").write_text(
            "---\nname: second-skill\ndescription: Another skill\n---\n# Second\n"
        )

        # Each skill gets its own on_create/on_update pair
        skill_creation_handler.on_create(
            session_id, session, RecordType.SKILL, {"type": "skill", "name": skill_name}
        )
        skill_creation_handler.on_create(
            session_id, session, RecordType.SKILL, {"type": "skill", "name": "second-skill"}
        )

        with patch("flow_sdk.fs_records.skill_record.Path.home", return_value=tmp_path):
            skill_creation_handler.on_update(
                session_id, session, RecordType.SKILL, {"status": "new", "folder_name": skill_name}
            )
            skill_creation_handler.on_update(
                session_id, session, RecordType.SKILL, {"status": "new", "folder_name": "second-skill"}
            )

        assert (tmp_path / ".claude" / "skills" / "my-test-skill" / "SKILL.md").exists()
        assert (tmp_path / ".claude" / "skills" / "second-skill" / "SKILL.md").exists()

    @patch("plugin_records.crud_handlers.skill_creation_handler.send_entity_sync")
    def test_on_update_ignores_non_skill_dirs(self, mock_sync, records_env):
        """Directories without SKILL.md should be ignored."""
        session = records_env["session"]
        session_id = records_env["session_id"]
        tmp_path = records_env["tmp_path"]

        # Create a non-skill directory in output_dir
        (session.output_dir / "not-a-skill").mkdir()
        (session.output_dir / "not-a-skill" / "random.txt").write_text("hello")

        # Create a regular file (not a dir)
        (session.output_dir / "analysis.json").write_text("{}")

        skill_name = records_env["skill_name"]
        skill_creation_handler.on_create(
            session_id, session, RecordType.SKILL, {"type": "skill", "name": skill_name}
        )

        with patch("flow_sdk.fs_records.skill_record.Path.home", return_value=tmp_path):
            skill_creation_handler.on_update(
                session_id, session, RecordType.SKILL, {"status": "new", "folder_name": skill_name}
            )

        # Only the real skill should be copied
        assert (tmp_path / ".claude" / "skills" / "my-test-skill").exists()
        assert not (tmp_path / ".claude" / "skills" / "not-a-skill").exists()


class TestEntityCrudUpdate:
    """Test the entity_crud update path."""

    @patch("plugin_records.crud_handlers.skill_creation_handler.send_entity_sync")
    def test_entity_crud_create_triggers_on_create(self, mock_sync, records_env):
        """entity_crud create should trigger on_create handler."""
        mgr = records_env["mgr"]
        session_id = records_env["session_id"]

        result = mgr.entity_crud(session_id, "create", {
            "type": "skill",
            "name": "crud-test-skill",
            "description": "test",
        })

        assert "Created" in result
        # on_create should have been called (3 sync calls)
        assert mock_sync.call_count == 3

    @patch("plugin_records.crud_handlers.skill_creation_handler.send_entity_sync")
    def test_entity_crud_update_does_not_raise(self, mock_sync, records_env):
        """entity_crud update should succeed and let handlers fire."""
        mgr = records_env["mgr"]
        session_id = records_env["session_id"]
        skill_name = records_env["skill_name"]
        tmp_path = records_env["tmp_path"]

        # First create the task
        skill_creation_handler.on_create(
            session_id, records_env["session"], RecordType.SKILL,
            {"type": "skill", "name": skill_name},
        )
        mock_sync.reset_mock()

        # entity_crud("update") should not raise
        with patch("flow_sdk.fs_records.skill_record.Path.home", return_value=tmp_path):
            result = mgr.entity_crud(session_id, "update", {
                "type": "skill",
                "name": skill_name,
                "status": "new",
            })

        assert "Error" not in result
        assert "Updated" in result


class TestGetChildrenByType:
    """Test that session.get_children_by_type returns SkillRecord instances."""

    def test_get_children_returns_skill_records(self, records_env):
        """get_children_by_type should return SkillRecord, not plain FsRecord."""
        mgr = records_env["mgr"]

        # Reload session from disk to get fresh state
        session = mgr.get_session(records_env["session_id"])

        skills = session.get_children_by_type(RecordType.SKILL)

        for skill in skills:
            assert isinstance(skill, SkillRecord), (
                f"Expected SkillRecord, got {type(skill).__name__}"
            )
            assert hasattr(skill, "copy_to_claude_user_home")


class TestEndToEndSkillCopy:
    """Full end-to-end: create skill -> mark done -> verify it lands in ~/.claude/skills/."""

    @patch("plugin_records.crud_handlers.skill_creation_handler.send_entity_sync")
    def test_full_flow_via_flow_tag_path(self, mock_sync, records_env):
        """Simulate the complete flow_tag skill_ready path and verify skill is copied."""
        mgr = records_env["mgr"]
        session_id = records_env["session_id"]
        session = records_env["session"]
        skill_name = records_env["skill_name"]
        tmp_path = records_env["tmp_path"]

        # Step 1: Agent calls entity_crud to create a skill
        mgr.entity_crud(session_id, "create", {
            "type": "skill",
            "name": skill_name,
            "description": "A test skill",
            "status": "creating",
        })

        # Step 2: Reload session (simulating fresh lookup as MCP does)
        session = mgr.get_session(session_id)

        # Step 3: Simulate flow_tag skill_ready triggering on_update
        with patch("flow_sdk.fs_records.skill_record.Path.home", return_value=tmp_path):
            skill_creation_handler.on_update(
                session_id, session, RecordType.SKILL, {"status": "new", "folder_name": skill_name}
            )

        # The skill should have been copied to <tmp_path>/.claude/skills/<skill_name>/
        expected_dest = tmp_path / ".claude" / "skills" / skill_name
        assert expected_dest.exists(), f"Skill not copied to {expected_dest}"
        assert (expected_dest / "SKILL.md").exists()

    @patch("plugin_records.crud_handlers.skill_creation_handler.send_entity_sync")
    def test_full_flow_via_entity_crud_update(self, mock_sync, records_env):
        """Simulate entity_crud update path and verify skill is copied."""
        mgr = records_env["mgr"]
        session_id = records_env["session_id"]
        skill_name = records_env["skill_name"]
        tmp_path = records_env["tmp_path"]

        # Step 1: Create via entity_crud
        mgr.entity_crud(session_id, "create", {
            "type": "skill",
            "name": skill_name,
            "status": "creating",
        })

        # Step 2: Update via entity_crud (previously raised NotImplementedError)
        with patch("flow_sdk.fs_records.skill_record.Path.home", return_value=tmp_path):
            result = mgr.entity_crud(session_id, "update", {
                "type": "skill",
                "name": skill_name,
                "status": "new",
            })

        assert "Error" not in result

        expected_dest = tmp_path / ".claude" / "skills" / skill_name
        assert expected_dest.exists(), f"Skill not copied to {expected_dest}"
        assert (expected_dest / "SKILL.md").exists()
        # record.json should NOT be copied to user home
        assert not (expected_dest / "record.json").exists()
