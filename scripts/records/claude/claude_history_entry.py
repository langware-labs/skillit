"""ClaudeHistoryEntryFsRecord — a single prompt from ~/.claude/history.jsonl."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Self

from fs_store import FsRecord


@dataclass(repr=False)
class ClaudeHistoryEntryFsRecord(FsRecord):
    """One prompt entry from the global Claude Code history."""

    display: str = ""
    timestamp_ms: int = 0
    project: str = ""
    session_id: str = ""

    def __post_init__(self):
        if not self.type:
            self.type = "history_entry"
        if not self.name:
            self.name = self.display[:80] if self.display else ""

    def __repr__(self) -> str:
        return f"ClaudeHistoryEntryFsRecord: {self.display[:80]}"

    @property
    def timestamp_dt(self) -> datetime | None:
        if not self.timestamp_ms:
            return None
        return datetime.fromtimestamp(self.timestamp_ms / 1000, tz=timezone.utc)

    @property
    def time_ago(self) -> str:
        """Human-friendly relative time like '3 hours ago', '2 days ago'."""
        dt = self.timestamp_dt
        if dt is None:
            return ""
        delta = datetime.now(tz=timezone.utc) - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        if days < 30:
            return f"{days}d ago"
        months = days // 30
        if months < 12:
            return f"{months}mo ago"
        years = days // 365
        return f"{years}y ago"

    @classmethod
    def from_dict_entry(cls, raw: dict) -> Self:
        """Create from a parsed history.jsonl line."""
        return cls(
            display=raw.get("display", ""),
            timestamp_ms=raw.get("timestamp", 0),
            project=raw.get("project", ""),
            session_id=raw.get("sessionId", ""),
            raw_json=raw,
        )
