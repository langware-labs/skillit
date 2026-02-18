"""ClaudeMdFsRecord — represents a CLAUDE.md instruction file.

Source: CLAUDE.md, CLAUDE.local.md, .claude/CLAUDE.md at project or user level.
These are instruction files that provide context and rules to Claude Code sessions.
"""

from __future__ import annotations

from dataclasses import dataclass

from fs_store import FsRecord, RecordType


@dataclass
class ClaudeMdFsRecord(FsRecord):
    """A CLAUDE.md instruction file.

    Mapped from ``CLAUDE.md``, ``CLAUDE.local.md``, or ``.claude/CLAUDE.md``.
    """

    filename: str = ""
    content: str = ""
    scope: str = "project"
    file_path: str = ""

    def __post_init__(self):
        if not self.type:
            self.type = "claude_md"
        if self.file_path:
            self.id = self.file_path
            if not self.name:
                self.name = self.filename or self.file_path
