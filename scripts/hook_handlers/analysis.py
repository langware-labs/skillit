"""Shared analysis lifecycle — create and complete analysis task + agentic process."""

from __future__ import annotations

from dataclasses import dataclass

import plugin_records
from fs_store import FsRecordRef, SyncOperation
from fs_store.record_types import RecordType
from plugin_records import skillit_records
from utils.log import skill_log
from network.notify import send_process_sync, send_relationship_sync, send_task_sync
from records import (
    AgenticProcess,
    ProcessorStatus,
    RelationshipRecord,
    TaskResource,
    TaskStatus,
    TaskType,
)


@dataclass
class AnalysisResources:
    task: TaskResource
    process: AgenticProcess
    relationship: RelationshipRecord


def start_new_analysis(session_id: str) -> AnalysisResources | None:
    """Create an analysis TaskResource with a child AgenticProcess and sync both to FlowPad.

    Hierarchy: session → task → agentic_process.

    Returns:
        AnalysisResources if session_id is valid, None otherwise.
    """
    if not session_id:
        skill_log("No session_id provided, skipping analysis start")
        return None
    session = skillit_records.get_session(session_id)
    if session is None:
        skill_log(f"Session {session_id} not found, skipping analysis start")
        session = skillit_records.create_session(session_id)

    output_dir = session.output_dir
    task_id = f"analysis-{session_id}"

    task = TaskResource(
        id=task_id,
        title="Analyzing session",
        status=TaskStatus.IN_PROGRESS,
        task_type=TaskType.ANALYSIS,
        tags=["analysis", "skillit"],
        metadata={
            "session_id": session_id,
            "output_dir": str(output_dir),
            "analysisPath": str(output_dir / "analysis.md"),
            "analysisJsonPath": str(output_dir / "analysis.json"),
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

    send_task_sync(SyncOperation.CREATE, task.to_dict())
    send_process_sync(SyncOperation.CREATE, process.to_dict())
    send_relationship_sync(SyncOperation.CREATE, relationship.to_dict())

    return AnalysisResources(task=task, process=process, relationship=relationship)


def complete_analysis(resources: AnalysisResources, session_id: str) -> None:
    """Mark the analysis task and process as done and sync updates to FlowPad."""
    resources.task.status = TaskStatus.DONE
    resources.process.state = ProcessorStatus.COMPLETE

    from plugin_records.skillit_records import skillit_records
    session = skillit_records.get_session(session_id)
    resources.task.save_to(session.record_dir)

    send_task_sync(SyncOperation.UPDATE, resources.task.to_dict())
    send_process_sync(SyncOperation.UPDATE, resources.process.to_dict())
