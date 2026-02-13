"""Claude-specific filesystem entities."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import Field

from ...fs.fs_entity import FsEntity
from ...fs.fs_record import FsRecord


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


class HookResource(FsEntity):
    type: str = Field(default="hook")
    event_type: str = Field(default="")
    matcher: str = Field(default="*")
    command: str = Field(default="")
    hook_type: str = Field(default="command")


class McpServerResource(FsEntity):
    type: str = Field(default="mcp_server")
    command: str = Field(default="")
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)


class CommandResource(FsEntity):
    type: str = Field(default="command")


class AgentResource(FsEntity):
    type: str = Field(default="agent")


class SkillResource(FsEntity):
    type: str = Field(default="skill")
    usage_count: int = Field(default=0)


class TaskResource(FsRecord):
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
