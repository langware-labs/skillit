"""ClaudeQueueOperationTranscriptEntry — queue-operation entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Self

from .base import ClaudeTranscriptEntryFsRecord


@dataclass(repr=False)
class ClaudeQueueOperationTranscriptEntry(ClaudeTranscriptEntryFsRecord):
    """A queue-operation transcript entry (enqueue/dequeue).

    Uses ``sessionId`` as the uid since these entries have no ``uuid``.
    """

    uid_mapping: ClassVar[str] = "sessionId"

    def __post_init__(self):
        if not self.type:
            self.type = "transcript_entry:queue_operation"
        if self.entry_uuid:
            self.id = self.entry_uuid

    @property
    def operation(self) -> str:
        return self.raw_json.get("operation", "")

    @property
    def content(self) -> str:
        return self.raw_json.get("content", "")

    @property
    def summary(self) -> str:
        op = self.operation
        if self.content:
            return f"queue: {op} — {self.content[:60]}"
        return f"queue: {op}"

    @classmethod
    def from_jsonl_entry(cls, raw: dict) -> Self:
        return cls(**cls._base_kwargs(raw))
