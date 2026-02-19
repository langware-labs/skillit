"""ClaudePrLinkTranscriptEntry — pr-link entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Self

from .base import ClaudeTranscriptEntryFsRecord


@dataclass(repr=False)
class ClaudePrLinkTranscriptEntry(ClaudeTranscriptEntryFsRecord):
    """A pr-link transcript entry.

    Uses ``sessionId`` as the uid since these entries have no ``uuid``.
    """

    uid_mapping: ClassVar[str] = "sessionId"

    def __post_init__(self):
        if not self.type:
            self.type = "transcript_entry:pr_link"
        if self.entry_uuid:
            self.id = self.entry_uuid

    @property
    def pr_number(self) -> int:
        return self.raw_json.get("prNumber", 0)

    @property
    def pr_url(self) -> str:
        return self.raw_json.get("prUrl", "")

    @property
    def pr_repository(self) -> str:
        return self.raw_json.get("prRepository", "")

    @property
    def summary(self) -> str:
        return f"PR #{self.pr_number} — {self.pr_url}"

    @classmethod
    def from_jsonl_entry(cls, raw: dict) -> Self:
        return cls(**cls._base_kwargs(raw))
