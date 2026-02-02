"""Replay transcript records and emit hook events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

from .hooks import HookEvent


@dataclass
class TranscriptReplay:
    transcript_record: Iterable[dict[str, Any]] | str | Path
    start_index: int = 0
    limit: int | None = None

    def __iter__(self) -> Iterator[HookEvent]:
        entries = self._load_entries()
        end_index = None if self.limit is None else self.start_index + self.limit
        for idx, entry in enumerate(entries):
            if idx < self.start_index:
                continue
            if end_index is not None and idx >= end_index:
                break
            hook_event = _entry_to_hook_event(entry, idx)
            if hook_event is not None:
                yield hook_event

    def _load_entries(self) -> Iterable[dict[str, Any]]:
        if isinstance(self.transcript_record, (str, Path)):
            path = Path(self.transcript_record)
            return _load_jsonl(path)
        return self.transcript_record


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not path.exists():
        return entries
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return entries
    return entries


def _entry_to_hook_event(entry: dict[str, Any], index: int) -> HookEvent | None:
    if entry.get("type") != "progress":
        return None
    data = entry.get("data", {})
    if data.get("type") != "hook_progress":
        return None
    return HookEvent(
        hook_event=str(data.get("hookEvent", "")),
        hook_name=str(data.get("hookName", "")),
        command=data.get("command"),
        tool_use_id=entry.get("toolUseID"),
        parent_tool_use_id=entry.get("parentToolUseID"),
        timestamp=entry.get("timestamp"),
        entry_index=index,
        raw=entry,
    )
