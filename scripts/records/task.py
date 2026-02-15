"""Task resource types for analysis lifecycle events.

Standalone module with no FlowPad SDK dependency — safe to import from
hooks, tests, and the main entry point.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from fs_store import FsRecord, RecordType


class TaskStatus(StrEnum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class TaskType(StrEnum):
    TASK = "Task"
    ANALYSIS = "analysis"


@dataclass
class TaskResource(FsRecord):
    """A task record backed by FsRecord (replaces the former Pydantic model)."""

    title: str = ""
    description: str = ""
    status: str = field(default=TaskStatus.TO_DO)
    task_type: str = field(default=TaskType.TASK)
    priority: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.type:
            self.type = RecordType.TASK

    def save_to(self, session_dir: Path) -> None:
        """Save this task into the unified session record at session_dir/record.json."""
        record_path = session_dir / "record.json"
        session = FsRecord.from_json(record_path)
        session["task"] = self.to_dict()
        session.save()
