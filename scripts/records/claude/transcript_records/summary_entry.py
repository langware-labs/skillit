"""ClaudeSummaryTranscriptEntry — summary entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Self

from .base import ClaudeTranscriptEntryFsRecord, _truncate


@dataclass(repr=False)
class ClaudeSummaryTranscriptEntry(ClaudeTranscriptEntryFsRecord):
    """A summary transcript entry (session auto-summary).

    Uses ``leafUuid`` as the uid since these entries have no ``uuid``.
    """

    uid_mapping: ClassVar[str] = "leafUuid"

    def __post_init__(self):
        if not self.type:
            self.type = "transcript_entry:summary"
        if self.entry_uuid:
            self.id = self.entry_uuid

    @property
    def leaf_uuid(self) -> str:
        return self.raw_json.get("leafUuid", "")

    @property
    def summary_text(self) -> str:
        return self.raw_json.get("summary", "")

    @property
    def summary(self) -> str:
        return "summary: " + _truncate(self.summary_text)

    @classmethod
    def from_jsonl_entry(cls, raw: dict) -> Self:
        return cls(**cls._base_kwargs(raw))
