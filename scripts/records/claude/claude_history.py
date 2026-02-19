"""ClaudeHistoryFsRecord — the global prompt history at ~/.claude/history.jsonl."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from fs_store import FsRecord


_DEFAULT_HISTORY_PATH = Path.home() / ".claude" / "history.jsonl"


@dataclass
class ClaudeHistoryFsRecord(FsRecord):
    """The global Claude Code prompt history.

    Each child is a ``ClaudeHistoryEntryFsRecord`` — one prompt the user sent.
    """

    history_path: str = ""

    def __post_init__(self):
        if not self.type:
            self.type = "history"
        if not self.history_path:
            self.history_path = str(_DEFAULT_HISTORY_PATH)
        if not self.name:
            self.name = "history"

    @property
    def entries(self) -> list:
        """Return all history entries as ``ClaudeHistoryEntryFsRecord``."""
        from .claude_history_entry import ClaudeHistoryEntryFsRecord

        path = Path(self.history_path)
        if not path.is_file():
            return []
        result = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError:
                    continue
                result.append(ClaudeHistoryEntryFsRecord.from_dict_entry(raw))
        result.sort(key=lambda e: e.timestamp_ms)
        return result

    @classmethod
    def default(cls) -> Self:
        """Return the history record for the default Claude installation."""
        return cls(history_path=str(_DEFAULT_HISTORY_PATH))
