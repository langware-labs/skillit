"""Filesystem-backed ResourceRecord with JSON file I/O."""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, TypeVar

from .fs_record_ref import FsRecordRef
from .resource_record import ResourceRecord

T = TypeVar("T", bound="FsRecord")


_FS_SYNC_SKIP = frozenset({"fs_sync", "source_file", "path"})
_RECORD_JSON = "record.json"


@dataclass
class FsRecord(ResourceRecord):
    """A ResourceRecord that can persist itself to a JSON file.

    Adds ``from_json`` / ``to_json`` / ``persist`` on top of the base
    data-contract class.  The ``parent`` and ``children`` properties
    resolve refs to live records loaded from disk.

    """

    fs_sync: bool = field(default=False, repr=False)

    def __setattr__(self, name: str, value):
        super().__setattr__(name, value)
        if (
            name not in _FS_SYNC_SKIP
            and not name.startswith("_")
            and getattr(self, "fs_sync", False)
            and getattr(self, "source_file", None)
        ):
            self.save()

    def __setitem__(self, key: str, value):
        known = {f.name for f in fields(self)}
        super().__setitem__(key, value)
        if key not in known and self.fs_sync and self.source_file:
            self.save()

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.pop("fs_sync", None)
        return d

    @property
    def record_dir(self) -> Path | None:
        """The directory containing this record on disk."""
        if self.path:
            return Path(self.path)
        if self.source_file:
            return Path(self.source_file).parent
        return None

    @property
    def output_dir(self) -> Path:
        """The output subdirectory for this record. Creates it if needed."""
        d = self.record_dir
        if d is None:
            raise ValueError("No path or source_file set")
        out = d / "output"
        out.mkdir(parents=True, exist_ok=True)
        return out

    # -- Live relationship properties --

    @property
    def parent(self) -> FsRecord | None:
        """Load the parent record from disk via parent_ref.record_path."""
        if self.parent_ref is None or not self.parent_ref.record_path:
            return None
        p = Path(self.parent_ref.record_path)
        if not p.exists():
            return None
        return FsRecord.init_record(p)

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
            result.append(FsRecord.init_record(p))
        return result

    def get_chidren_by_type(self, type: str) -> list[FsRecord]:
        """Load child records from disk and keep only records of the requested type."""
        result: list[FsRecord] = []
        for ref in self.children_refs:
            if not ref.record_path:
                continue
            p = Path(ref.record_path)
            if not p.exists():
                continue
            child = FsRecord.init_record(p)
            if child.type == type:
                result.append(child)
        return result

    def add_child(self, child: FsRecord | FsRecordRef) -> FsRecordRef:
        """Append a child ref to this record without creating/modifying child files."""
        ref = child if isinstance(child, FsRecordRef) else FsRecordRef.from_record(child)
        if not any(existing.id == ref.id and existing.type == ref.type for existing in self.children_refs):
            self.children_refs.append(ref)
            if self.source_file:
                self.save()
        return ref

    @classmethod
    def init(
        cls: type[T],
        data: dict[str, Any],
        path: str | Path,
        indent: int = 2,
    ) -> T:
        """Backward-compatible alias for ``init_record(data, path)``."""
        return cls.init_record(data, path, indent=indent)

    @classmethod
    def init_record(
        cls: type[T],
        path_or_data: str | Path | dict[str, Any],
        path: str | Path | None = None,
        indent: int = 2,
    ) -> T:
        """Initialize or load a record.

        Forms:
        - ``init_record(path)`` -> load from ``path`` (or create empty in-memory record if missing)
        - ``init_record(data, path)`` -> create folder-layout record at ``path/record.json``
        """
        if isinstance(path_or_data, dict):
            if path is None:
                raise ValueError("path is required when initializing from data")
            p = Path(path)
            if p.name == _RECORD_JSON:
                folder = p.parent
            elif p.suffix == ".json":
                folder = p.parent / p.stem
            else:
                folder = p

            record_file = folder / _RECORD_JSON
            rec = cls.from_dict(path_or_data)
            rec.path = str(folder)
            rec.save_record_json(record_file, indent=indent)
            return rec

        p = Path(path_or_data)
        if p.is_dir():
            p = p / _RECORD_JSON
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            rec = cls.from_dict(data)
        else:
            rec = cls()
        rec.source_file = str(p)
        return rec

    def save_record_json(self, path: str | Path | None = None, indent: int = 2) -> None:
        """Write this record to a JSON file."""
        p = Path(path or self.source_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(self.to_dict(), indent=indent, ensure_ascii=False),
            encoding="utf-8",
        )
        self.source_file = str(p)

    def save(self) -> None:
        """Save to ``source_file``."""
        if not self.source_file:
            raise ValueError("source_file not set; use to_json(path) first")
        self.save_record_json()

    def open(self) -> None:
        """Open this record's folder in the native OS file explorer."""
        folder = self.record_dir
        if folder is None:
            raise ValueError("No path or source_file set")
        system = platform.system()
        if system == "Darwin":
            subprocess.Popen(["open", str(folder)])
        elif system == "Windows":
            subprocess.Popen(["explorer", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
