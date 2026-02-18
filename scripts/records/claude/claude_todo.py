"""ClaudeTodoFsRecord — represents a Claude Code todo list from a session.

Source: ~/.claude/todos/<session-id>-agent-<session-id>.json
Each file is a JSON array of todo items with content, status, priority, and id.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fs_store import FsRecord, RecordType


@dataclass
class ClaudeTodoItemFsRecord(FsRecord):
    """A single todo item within a Claude Code session todo list.

    Mapped from entries in ``~/.claude/todos/<session-id>-agent-<session-id>.json``.
    """

    content: str = ""
    status: str = ""
    priority: str = ""

    def __post_init__(self):
        if not self.type:
            self.type = "todo_item"


@dataclass
class ClaudeTodoFsRecord(FsRecord):
    """A Claude Code session todo list.

    Mapped from ``~/.claude/todos/<session-id>-agent-<session-id>.json``.
    """

    session_id: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    completed_count: int = 0

    def __post_init__(self):
        if not self.type:
            self.type = "todo_file"
        if self.session_id:
            self.id = self.session_id
            if not self.name:
                self.name = self.session_id
