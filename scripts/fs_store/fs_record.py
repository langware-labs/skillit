"""Filesystem-backed ResourceRecord with JSON file I/O."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from .resource_record import ResourceRecord

T = TypeVar("T", bound="FsRecord")


@dataclass
class FsRecord(ResourceRecord):
    """A ResourceRecord that can persist itself to a JSON file.

    Adds ``from_json`` / ``to_json`` / ``persist`` on top of the base
    data-contract class.  The ``parent`` and ``children`` properties
    resolve refs to live records loaded from disk.
    """

    # -- Live relationship properties --

    @property
    def parent(self) -> FsRecord | None:
        """Load the parent record from disk via parent_ref.record_path."""
        if self.parent_ref is None or not self.parent_ref.record_path:
            return None
        p = Path(self.parent_ref.record_path)
        if not p.exists():
            return None
        return FsRecord.from_json(p)

    @property
    def children(self) -> list[FsRecord]:
        """Load child records from disk via each ref's record_path."""
        result: list[FsRecord] = []
        for ref in self.children_refs:
            if not ref.record_path:
                continue
            p = Path(ref.record_path)
            if not p.exists():
                continue
            result.append(FsRecord.from_json(p))
        return result

    @classmethod
    def from_json(cls, path: str | Path) -> FsRecord:
        """Load a record from a JSON file, or create a new one if missing."""
        p = Path(path)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            rec = cls.from_dict(data)
        else:
            rec = cls()
        rec.source_file = str(p)
        return rec

    def to_json(self, path: str | Path | None = None, indent: int = 2) -> None:
        """Write this record to a JSON file."""
        p = Path(path or self.source_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(self.to_dict(), indent=indent, ensure_ascii=False),
            encoding="utf-8",
        )
        self.source_file = str(p)

    def persist(self) -> None:
        """Save to ``source_file``. Convenience wrapper around ``to_json``."""
        if not self.source_file:
            raise ValueError("source_file not set; use to_json(path) first")
        self.to_json()
