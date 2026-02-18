"""ClaudeFileSnapshotTranscriptEntry — file-history-snapshot entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Self

from .base import ClaudeTranscriptEntryFsRecord


@dataclass(repr=False)
class ClaudeFileSnapshotTranscriptEntry(ClaudeTranscriptEntryFsRecord):
    """A file-history-snapshot transcript entry.

    Uses ``messageId`` as the uid instead of ``uuid``.
    """

    uid_mapping: ClassVar[str] = "messageId"

    def __post_init__(self):
        if not self.type:
            self.type = "transcript_entry:file_snapshot"
        if self.entry_uuid:
            self.id = self.entry_uuid

    @property
    def message_id(self) -> str:
        return self.raw_json.get("messageId", "")

    @property
    def snapshot(self) -> dict:
        return self.raw_json.get("snapshot") or {}

    @property
    def is_snapshot_update(self) -> bool:
        return self.raw_json.get("isSnapshotUpdate", False)

    @property
    def summary(self) -> str:
        update = " (update)" if self.is_snapshot_update else ""
        return f"file snapshot{update}"

    @classmethod
    def from_jsonl_entry(cls, raw: dict) -> Self:
        return cls(**cls._base_kwargs(raw))
