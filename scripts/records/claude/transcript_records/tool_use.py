"""ClaudeToolTranscriptEntry — assistant entry containing a tool_use call."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Self

from .base import ClaudeTranscriptEntryFsRecord, _truncate


@dataclass(repr=False)
class ClaudeToolTranscriptEntry(ClaudeTranscriptEntryFsRecord):
    """An assistant transcript entry that invokes a tool."""

    def __post_init__(self):
        if not self.type:
            self.type = "transcript_entry:tool_use"
        if self.entry_uuid:
            self.id = self.entry_uuid

    # -- tool_use block (first one in content) --

    @property
    def _tool_block(self) -> dict:
        for block in self.message.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                return block
        return {}

    @property
    def tool_name(self) -> str:
        return self._tool_block.get("name", "")

    @property
    def tool_use_id(self) -> str:
        return self._tool_block.get("id", "")

    @property
    def tool_input(self) -> dict:
        return self._tool_block.get("input") or {}

    # -- envelope fields --

    @property
    def model(self) -> str:
        return self.message.get("model", "")

    @property
    def request_id(self) -> str:
        return self.raw_json.get("requestId", "")

    # -- Tools that should show full input values (no truncation) --
    _FULL_INPUT_TOOLS: ClassVar[set[str]] = {"Read", "Write", "TaskCreate"}

    # -- summary --

    @property
    def summary(self) -> str:
        inp = self.tool_input
        name = self.tool_name
        full = name in self._FULL_INPUT_TOOLS
        if inp:
            parts = []
            for k, v in inp.items():
                s = str(v)
                if not full and len(s) > 120:
                    s = s[:120] + "..."
                parts.append(f"{k}={s}")
            args = ", ".join(parts)
        else:
            args = ""
        line = f"{name}({args})"
        if full:
            return "tool: " + line
        return "tool: " + _truncate(line)

    @classmethod
    def from_jsonl_entry(cls, raw: dict) -> Self:
        return cls(**cls._base_kwargs(raw))


def _is_tool_use_entry(raw: dict) -> bool:
    """Check if a raw JSONL dict is an assistant entry with a tool_use block."""
    if raw.get("type") != "assistant":
        return False
    for block in (raw.get("message") or {}).get("content") or []:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            return True
    return False
