"""Task resource types for analysis lifecycle events.

Standalone module with no FlowPad SDK dependency — safe to import from
hooks, tests, and the main entry point.
"""

from __future__ import annotations

import json
import uuid
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskEventType(StrEnum):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"


class TaskStatus(StrEnum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class TaskType(StrEnum):
    TASK = "Task"
    ANALYSIS = "analysis"


class TaskResource(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(default="task")
    title: str = Field(default="")
    description: str = Field(default="")
    status: str = Field(default=TaskStatus.TO_DO)
    task_type: str = Field(default=TaskType.TASK)
    priority: str | None = Field(default=None)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def save_to(self, path: Path) -> None:
        """Write task JSON to a specific path."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.model_dump(mode="json"), indent=2))
