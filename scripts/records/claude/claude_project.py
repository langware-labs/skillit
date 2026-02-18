"""ClaudeProjectFsRecord — represents a Claude Code project directory.

Source: ~/.claude/projects/<encoded-path>/
The directory name is the URL-encoded absolute path of the working directory.
Contains .jsonl session files and optional subdirectories (subagents, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass

from fs_store import FsRecord, RecordType


@dataclass
class ClaudeProjectFsRecord(FsRecord):
    """A Claude Code project — a working directory with associated sessions.

    Mapped from ``~/.claude/projects/<encoded-cwd>/``.
    """

    encoded_path: str = ""
    real_path: str = ""
    session_count: int = 0

    def __post_init__(self):
        if not self.type:
            self.type = RecordType.SESSION  # project container
        if self.encoded_path:
            self.id = self.encoded_path
            if not self.name:
                self.name = self.real_path or self.encoded_path
