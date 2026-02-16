"""Shared skill-creation lifecycle — create and complete skill-creation task + agentic process."""

from __future__ import annotations

from dataclasses import dataclass

import plugin_records
from fs_store import FsRecordRef, ResourceType, SyncOperation
from fs_store.record_types import RecordType
from plugin_records import skillit_records
from utils.log import skill_log
from network.notify import send_entity_sync
from records import (
    AgenticProcess,
    ProcessorStatus,
    RelationshipRecord,
    TaskResource,
    TaskStatus,
    TaskType,
)


@dataclass
class SkillCreationResources:
    task: TaskResource
    process: AgenticProcess
    relationship: RelationshipRecord


def start_skill_creation(session_id: str) -> SkillCreationResources | None:
    """Create a skill-creation TaskResource with a child AgenticProcess and sync both to FlowPad.

    Hierarchy: session → task → agentic_process.

    Returns:
        SkillCreationResources if session_id is valid, None otherwise.
    """
    if not session_id:
        skill_log("No session_id provided, skipping skill creation start")
        return None
    session = skillit_records.get_session(session_id)
    if session is None:
        skill_log(f"Session {session_id} not found, skipping skill creation start")
        session = skillit_records.create_session(session_id)

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


def complete_skill_creation(resources: SkillCreationResources, session_id: str) -> None:
    """Mark the skill-creation task as done and sync update to FlowPad."""
    resources.task.status = TaskStatus.DONE
    resources.process.state = ProcessorStatus.COMPLETE

    from plugin_records.skillit_records import skillit_records
    session = skillit_records.get_session(session_id)
    resources.task.save_to(session.record_dir)

    send_entity_sync(SyncOperation.UPDATE, resources.task.to_dict())
    send_entity_sync(SyncOperation.UPDATE, resources.process.to_dict())
