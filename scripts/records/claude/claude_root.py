"""ClaudeRootFsRecord — the root of all Claude Code projects.

Represents ``~/.claude/projects/`` and provides access to all projects
and sessions across the entire Claude installation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from fs_store import FsRecord

if TYPE_CHECKING:
    from .claude_project import ClaudeProjectFsRecord

_DEFAULT_PROJECTS_DIR = Path.home() / ".claude" / "projects"


@dataclass
class ClaudeRootFsRecord(FsRecord):
    """Root record for the Claude Code installation.

    Children are ``ClaudeProjectFsRecord`` instances (one per project dir).
    """

    projects_dir: str = ""

    def __post_init__(self):
        if not self.type:
            self.type = "claude_root"
        if not self.projects_dir:
            self.projects_dir = str(_DEFAULT_PROJECTS_DIR)
        if not self.name:
            self.name = "claude_root"

    @property
    def _projects_path(self) -> Path:
        return Path(self.projects_dir)

    @property
    def projects(self) -> list[ClaudeProjectFsRecord]:
        """Return all project directories as ``ClaudeProjectFsRecord``."""
        from .claude_project import ClaudeProjectFsRecord

        if not self._projects_path.is_dir():
            return []
        result = []
        for d in sorted(self._projects_path.iterdir()):
            if not d.is_dir():
                continue
            encoded = d.name
            real = "/" + encoded.lstrip("-").replace("-", "/")
            session_count = sum(1 for f in d.glob("*.jsonl"))
            result.append(ClaudeProjectFsRecord(
                encoded_path=encoded,
                real_path=real,
                session_count=session_count,
                source_file=str(d),
            ))
        return result

    @property
    def history(self):
        """Return the global prompt history record."""
        from .claude_history import ClaudeHistoryFsRecord
        return ClaudeHistoryFsRecord.default()

    def get_session(self, session_id: str):
        """Find a session by ID across all projects.

        Returns a ``ClaudeSessionFsRecord`` or ``None``.
        """
        from .claude_session import ClaudeSessionFsRecord

        if not self._projects_path.is_dir():
            return None
        for project_dir in self._projects_path.iterdir():
            if not project_dir.is_dir():
                continue
            jsonl = project_dir / f"{session_id}.jsonl"
            if jsonl.is_file():
                return ClaudeSessionFsRecord.from_jsonl(jsonl)
        return None

    @classmethod
    def default(cls) -> ClaudeRootFsRecord:
        """Return the root record for the default Claude installation."""
        return cls(projects_dir=str(_DEFAULT_PROJECTS_DIR))
