"""ClaudeHookFsRecord — represents a Claude Code event hook configuration.

Source: ~/.claude/settings.json (user-level) and .claude/settings.json (project-level)
Hooks are organized by event type, each with a matcher and a list of commands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fs_store import FsRecord, RecordType


@dataclass
class ClaudeHookEntryFsRecord(FsRecord):
    """A single hook command entry within a hook event group.

    Each entry has a type (e.g. "command") and a command string.
    """

    hook_type: str = "command"
    command: str = ""

    def __post_init__(self):
        if not self.type:
            self.type = "hook_entry"


@dataclass
class ClaudeHookFsRecord(FsRecord):
    """A Claude Code event hook group.

    Mapped from ``settings.json`` ``hooks.<event>[]`` entries.
    Events: SessionStart, SessionEnd, UserPromptSubmit, PreToolUse,
    PostToolUse, Notification, Stop, SubagentStop, PreCompact,
    PermissionRequest.
    """

    event: str = ""
    matcher: str = "*"
    hooks: list[dict[str, str]] = field(default_factory=list)
    scope: str = "user"

    def __post_init__(self):
        if not self.type:
            self.type = "hook"
        if self.event:
            self.id = f"{self.scope}:{self.event}"
            if not self.name:
                self.name = self.event
