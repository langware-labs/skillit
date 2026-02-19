"""ClaudeCustomTitleTranscriptEntry — custom-title entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Self

from .base import ClaudeTranscriptEntryFsRecord, _truncate


@dataclass(repr=False)
class ClaudeCustomTitleTranscriptEntry(ClaudeTranscriptEntryFsRecord):
    """A custom-title transcript entry.

    Uses ``sessionId`` as the uid since these entries have no ``uuid``.
    """

    uid_mapping: ClassVar[str] = "sessionId"

    def __post_init__(self):
        if not self.type:
            self.type = "transcript_entry:custom_title"
        if self.entry_uuid:
            self.id = self.entry_uuid

    @property
    def custom_title(self) -> str:
        return self.raw_json.get("customTitle", "")

    @property
    def summary(self) -> str:
        return "title: " + _truncate(self.custom_title)

    @classmethod
    def from_jsonl_entry(cls, raw: dict) -> Self:
        return cls(**cls._base_kwargs(raw))
