"""Skill-creation lifecycle handler — triggered by entity_crud CRUD events."""

from __future__ import annotations

from dataclasses import dataclass

from fs_store import FsRecordRef, ResourceType, SyncOperation
from fs_store.record_types import RecordType
from network.notify import send_entity_sync
from records import (
    AgenticProcess,
    ProcessorStatus,
    RelationshipRecord,
    TaskResource,
    TaskStatus,
    TaskType,
)
from records.skill_record import SkillRecord
from utils.log import skill_log


@dataclass
class SkillCreationResources:
    task: TaskResource
    process: AgenticProcess
    relationship: RelationshipRecord


class SkillCreationHandler:
    record_type = RecordType.SKILL

    @staticmethod
    def on_create(session_id, session, record_type, entity):
        """Create a skill-creation TaskResource with a child AgenticProcess and sync both to FlowPad."""
        if not session_id:
            skill_log("No session_id provided, skipping skill creation start")
            return None

        output_dir = session.output_dir
        task_id = f"skill-creation-{session_id}"

        task = TaskResource(
            id=task_id,
            title="Creating skill",
            status=TaskStatus.IN_PROGRESS,
            task_type=TaskType.SKILL_CREATION,
            tags=["skill-creation", "skillit"],
            metadata={
                "session_id": session_id,
                "output_dir": str(output_dir),
            },
        )

        process = AgenticProcess(
            state=ProcessorStatus.RUNNING,
            worker_id=session_id,
            parent_ref=FsRecordRef(id=task_id, type=RecordType.TASK),
        )
        child_ref = FsRecordRef.from_record(process)
        relationship = RelationshipRecord.child(
            from_ref=FsRecordRef(id=task_id, type=RecordType.TASK),
            to_ref=child_ref,
        )

        task.children_refs = [child_ref]
        task.save_to(session.record_dir)

        send_entity_sync(SyncOperation.CREATE, task.to_dict())
        send_entity_sync(SyncOperation.CREATE, process.to_dict())
        send_entity_sync(SyncOperation.CREATE, relationship.to_dict(), ResourceType.RELATIONSHIP)

        return SkillCreationResources(task=task, process=process, relationship=relationship)

    @staticmethod
    def on_update(session_id, session, record_type, entity):
        """Complete skill-creation task when the skill status is updated to 'new'."""
        skill_log(f"SkillCreationHandler on_update called for session {session_id}, record_type {record_type}, status {entity.get('status')}")
        if entity.get("status") != "new":
            return

        task_id = f"skill-creation-{session_id}"

        # Update task status in the session record for FlowPad sync
        skill_log(f"Updating task {task_id} status to DONE for session {session_id}")
        try:
            from fs_store import FsRecord as _FsRecord

            record_path = session.record_dir / "record.json"
            if record_path.exists():
                session_rec = _FsRecord.init_record(record_path)
                task_data = session_rec.extra.get("task")
                if task_data:
                    task = TaskResource.from_dict(task_data)
                    task.status = TaskStatus.DONE
                    session_rec["task"] = task.to_dict()
                    session_rec.save()
                    send_entity_sync(SyncOperation.UPDATE, task.to_dict())
        except Exception as e:
            skill_log(f"Could not update task status for {task_id}: {e}")

        # Mark the child agentic process as complete
        skill_log(f"Marking child process of task {task_id} as COMPLETE for session {session_id}")
        try:
            task = TaskResource.load_from(session.record_dir, task_id)
            if task and task.children_refs:
                process_ref = task.children_refs[0]
                process = AgenticProcess.load_from(session.record_dir, process_ref.id)
                if process:
                    process.state = ProcessorStatus.COMPLETE
                    send_entity_sync(SyncOperation.UPDATE, process.to_dict())
        except Exception as e:
            skill_log(f"Could not update process state for {task_id}: {e}")

        # Copy skills from the session output directory to ~/.claude/skills/
        skill_log(f"Copying skills for session {session_id} from {session.output_dir} to Claude user home")
        try:
            output_dir = session.output_dir
            copied = 0
            for child in output_dir.iterdir():
                if child.is_dir() and (child / "SKILL.md").exists():
                    skill = SkillRecord.init_record(child)
                    dest = skill.copy_to_claude_user_home()
                    copied += 1
                    skill_log(f"Copied skill '{skill.name}' to {dest}")

            skill_log(f"Completed skill creation for session {session_id} ({copied} skill(s) copied)")
        except Exception as e:
            skill_log(f"Failed to copy skills for session {session_id}: {e}")


skill_creation_handler = SkillCreationHandler()
