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
        """Complete skill-creation task when the skill status is updated to 'done'."""
        if entity.get("status") != "done":
            return

        task_id = f"skill-creation-{session_id}"
        try:
            task = TaskResource.load_from(session.record_dir, task_id)
            if not task or not task.children_refs:
                return

            process_ref = task.children_refs[0]
            process = AgenticProcess.load_from(session.record_dir, process_ref.id)

            rel_id = f"child:task:{task_id}:agentic_process:{process_ref.id}"
            relationship = RelationshipRecord.load_from(session.record_dir, rel_id)

            if not process or not relationship:
                return

            task.status = TaskStatus.DONE
            process.state = ProcessorStatus.COMPLETE
            task.save_to(session.record_dir)

            send_entity_sync(SyncOperation.UPDATE, task.to_dict())
            send_entity_sync(SyncOperation.UPDATE, process.to_dict())
            
            skills: list[SkillRecord] = session.get_children_by_type(RecordType.SKILL)
            for skill in skills:
                skill.copy_to_claude_user_home()
            
            skill_log(f"Completed skill creation task for session {session_id}")
        except Exception as e:
            skill_log(f"Failed to complete skill creation task: {e}")


skill_creation_handler = SkillCreationHandler()
