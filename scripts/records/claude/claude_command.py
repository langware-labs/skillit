"""ClaudeCommandFsRecord — represents a custom slash command.

Source: ~/.claude/commands/<name>.md (user-level) or .claude/commands/<name>.md (project-level)
Each file is a markdown prompt template invoked via /<name>.
"""

from __future__ import annotations

from dataclasses import dataclass

from fs_store import FsRecord, RecordType


@dataclass
class ClaudeCommandFsRecord(FsRecord):
    """A custom Claude Code slash command.

    Mapped from ``commands/<name>.md``.
    """

    command_name: str = ""
    content: str = ""
    scope: str = "user"

    def __post_init__(self):
        if not self.type:
            self.type = "command"
        if self.command_name:
            self.id = f"{self.scope}:{self.command_name}"
            if not self.name:
                self.name = self.command_name
