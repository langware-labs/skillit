"""ClaudeProjectFsRecord — represents a Claude Code project directory.

Source: ~/.claude/projects/<encoded-path>/
The directory name is the URL-encoded absolute path of the working directory.
Contains .jsonl session files and optional subdirectories (subagents, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fs_store import FsRecord, RecordType, StorageLayout
from records.claude import ClaudeSessionFsRecord


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
            self.type = RecordType.PROJECT
        self.storage_layout = StorageLayout.FOLDER
        if self.encoded_path:
            self.id = self.encoded_path
            if not self.name:
                self.name = self.real_path or self.encoded_path

    @property
    def sessions(self) -> list[ClaudeSessionFsRecord]:
        """Return all sessions in this project as ``ClaudeSessionFsRecord``."""

        project_dir = Path(self.path or self.source_file) if (self.path or self.source_file) else None
        if not project_dir or not project_dir.is_dir():
            return []
        return [
            ClaudeSessionFsRecord.from_jsonl(f)
            for f in sorted(project_dir.glob("*.jsonl"))
        ]
