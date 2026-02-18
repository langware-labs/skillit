"""ClaudeToolResultTranscriptEntry — user entry containing a tool_result."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from .base import ClaudeTranscriptEntryFsRecord, _truncate


@dataclass(repr=False)
class ClaudeToolResultTranscriptEntry(ClaudeTranscriptEntryFsRecord):
    """A user transcript entry that carries a tool result."""

    def __post_init__(self):
        if not self.type:
            self.type = "transcript_entry:tool_result"
        if self.entry_uuid:
            self.id = self.entry_uuid

    # -- tool_result block (first one in content) --

    @property
    def _result_block(self) -> dict:
        for block in self.message.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                return block
        return {}

    @property
    def tool_use_id(self) -> str:
        return self._result_block.get("tool_use_id", "")

    @property
    def content(self) -> str:
        """The text content returned by the tool."""
        raw = self._result_block.get("content", "")
        if isinstance(raw, str):
            return raw
        if isinstance(raw, list):
            parts = []
            for block in raw:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "\n".join(parts)
        return str(raw)

    @property
    def tool_use_result(self) -> dict:
        """Extra tool result metadata from the envelope (filePath, patch, etc.)."""
        return self.raw_json.get("toolUseResult") or {}

    @property
    def file_path(self) -> str:
        return self.tool_use_result.get("filePath", "")

    # -- summary --

    @property
    def is_error(self) -> bool:
        return self._result_block.get("is_error", False)

    @property
    def summary(self) -> str:
        prefix = "ERROR tool_result: " if self.is_error else "tool_result: "
        return prefix + _truncate(self.content, 120)

    @classmethod
    def from_jsonl_entry(cls, raw: dict) -> Self:
        return cls(**cls._base_kwargs(raw))


def _is_tool_result_entry(raw: dict) -> bool:
    """Check if a raw JSONL dict is a user entry with a tool_result block."""
    if raw.get("type") != "user":
        return False
    for block in (raw.get("message") or {}).get("content") or []:
        if isinstance(block, dict) and block.get("type") == "tool_result":
            return True
    return False
