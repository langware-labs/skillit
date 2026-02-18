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
from utils.log import skill_log

from records.skill_record import SkillRecord


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
        if entity.get("status") != ResourceStatus.NEW:
            skill_log(f"on_update: status is {entity.get('status')!r}, not 'new' — skipping")
            return

        task_id = f"skill-creation-{session_id}"
        try:
            from fs_store import FsRecord

            session_record = FsRecord.init_record(session.record_dir / "record.json")
            if "task" not in session_record:
                skill_log(f"on_update: 'task' key not found in session record — skipping")
                return

            task_data = session_record["task"]
            task = TaskResource.from_dict(task_data)
            if not task.children_refs:
                skill_log(f"on_update: task has no children_refs — skipping")
                return

            process_ref = task.children_refs[0]
            if process_ref.id not in session_record:
                skill_log(f"on_update: process {process_ref.id} not found in session record — skipping")
                return
            process_data = session_record[process_ref.id]
            process = AgenticProcess.from_dict(process_data)

            rel_id = f"child:task:{task_id}:agentic_process:{process_ref.id}"
            if rel_id not in session_record:
                skill_log(f"on_update: relationship {rel_id} not found in session record — skipping")
                return

            task.status = TaskStatus.DONE
            process.state = ProcessorStatus.COMPLETE
            task.save_to(session.record_dir)

            send_entity_sync(SyncOperation.UPDATE, task.to_dict())
            send_entity_sync(SyncOperation.UPDATE, process.to_dict())
            skill_log("Skill created.")

            output_dir = session.output_dir
            scope = entity.get("recommended_scope", "user")
            skill_log(f"Copying skills for session {session_id} (scope={scope}) from {output_dir}")
            copied = 0
            for child in output_dir.iterdir():
                has_skill_md = child.is_dir() and (child / "SKILL.md").exists()
                skill_log(f"  checking {child.name}: is_dir={child.is_dir()}, has_SKILL.md={has_skill_md}")
                if has_skill_md:
                    skill = SkillRecord.init_record(child)
                    if scope == "project" and session.cwd:
                        dest = skill.copy_to_project(session.cwd)
                    else:
                        if scope == "project":
                            skill_log(f"  WARNING: project scope requested but session has no cwd, falling back to user scope")
                        dest = skill.copy_to_claude_user_home()
                    copied += 1
                    skill_log(f"  Copied skill '{skill.name}' from {child} to {dest}")
            if copied == 0:
                skill_log(f"No skills found to copy in {output_dir} for session {session_id}")

            skill_log(f"Completed skill creation task for session {session_id}")
        except Exception as e:
            skill_log(f"Failed to complete skill creation task: {e}")


skill_creation_handler = SkillCreationHandler()
