"""Skill-creation lifecycle handler — triggered by entity_crud CRUD events."""

from __future__ import annotations

from dataclasses import dataclass

from fs_store import FsRecordRef, ResourceStatus, ResourceType, SyncOperation
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
        skill_log(f"skill_creation_handler.on_create: session={session_id}, record_type={record_type}")
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

        # Also save process and relationship to session record
        session_record = session.record_dir / "record.json"
        from fs_store import FsRecord
        rec = FsRecord.init_record(session_record)
        rec[process.id] = process.to_dict()
        rec[relationship.id] = relationship.to_dict()
        rec.save()

        send_entity_sync(SyncOperation.CREATE, task.to_dict(), wait=True)
        send_entity_sync(SyncOperation.CREATE, process.to_dict(), wait=True)
        send_entity_sync(SyncOperation.CREATE, relationship.to_dict(), ResourceType.RELATIONSHIP, wait=True)

        return SkillCreationResources(task=task, process=process, relationship=relationship)

    @staticmethod
    def on_update(session_id, session, record_type, entity):
        """Complete skill-creation task when the skill status is updated to 'new'."""
        skill_log(f"SkillCreationHandler on_update called for session {session_id}, record_type {record_type}, status {entity.get('status')}")
        if entity.get("status") !=  ResourceStatus.NEW:
            return

        task_id = f"skill-creation-{session_id}"

        try:
            from fs_store import FsRecord

            session_record = FsRecord.init_record(session.record_dir / "record.json")
            if "task" not in session_record:
                return

            task_data = session_record["task"]
            task = TaskResource.from_dict(task_data)
            if not task.children_refs:
                return

            process_ref = task.children_refs[0]
            if process_ref.id not in session_record:
                return
            process_data = session_record[process_ref.id]
            process = AgenticProcess.from_dict(process_data)

            rel_id = f"child:task:{task_id}:agentic_process:{process_ref.id}"
            if rel_id not in session_record:
                return
            relationship_data = session_record[rel_id]
            relationship = RelationshipRecord.from_dict(relationship_data)

            task.status = TaskStatus.DONE
            process.state = ProcessorStatus.COMPLETE

            # Update in session record
            session_record["task"] = task.to_dict()
            session_record[process.id] = process.to_dict()
            session_record.save()

            send_entity_sync(SyncOperation.UPDATE, task.to_dict())
            send_entity_sync(SyncOperation.UPDATE, process.to_dict())
            skill_log("Skill created.")

            skill_log(f"Copying skills for session {session_id} from {session.output_dir} to Claude user home")
            output_dir = session.output_dir
            copied = 0
            for child in output_dir.iterdir():
                if child.is_dir() and (child / "SKILL.md").exists():
                    skill = SkillRecord.init_record(child)
                    dest = skill.copy_to_claude_user_home()
                    copied += 1
                    skill_log(f"Copied skill '{skill.name}' to {dest}")
            if copied == 0:
                skill_log(f"No skills found to copy for session {session_id}")

            skill_log(f"Completed skill creation task for session {session_id}")
        except Exception as e:
            skill_log(f"Failed to complete skill creation task: {e}")


skill_creation_handler = SkillCreationHandler()
