"""A typed collection of FsRecords backed by flat files or folders.

Every operation goes directly to disk — no in-memory list, no bulk load.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Iterator

from .fs_record import FsRecord
from .resource_record import record_stem
from .storage_layout import StorageLayout

_RECORD_JSON = "record.json"


@dataclass
class ResourceRecordList:
    """Typed collection of records persisted to disk.

    ``storage_layout`` controls how individual records are stored:

    * ``FILE``   – one ``<type>-@<uid>.json`` file per record inside ``list_path/``.
    * ``FOLDER`` – one ``<type>-@<uid>/record.json`` directory per record inside ``list_path/``.

    All operations read/write individual files directly — there is no
    bulk ``load()`` or in-memory cache.

    When ``list_path`` is omitted the collection path is computed as
    ``records_path / <record_type>``, where *records_path* defaults to
    ``~/.flow/records`` (the ``RECORDS_PATH`` constant from ``utils.conf``).
    The record type is inferred from ``record_class``.
    """

    list_path: Path | None = None
    record_class: type[FsRecord] = field(default=FsRecord)
    storage_layout: StorageLayout = field(default=StorageLayout.FOLDER)
    records_path: Path | None = None

    def __post_init__(self):
        self._record_type = self.record_class().type
        if self.list_path is None:
            if not self._record_type:
                raise ValueError(
                    "list_path is required when record_class has no default type"
                )
            base = self.records_path
            if base is None:
                from utils.conf import RECORDS_PATH
                base = RECORDS_PATH
            self.list_path = base / self._record_type

    # -- Path helpers --

    def _record_file(self, uid: str, record_type: str | None = None) -> Path:
        """Return the on-disk path for a record with the given uid."""
        rtype = record_type or self._record_type
        stem = record_stem(rtype, uid)
        if self.storage_layout == StorageLayout.FOLDER:
            return self.list_path / stem / _RECORD_JSON
        return self.list_path / f"{stem}.json"

    # -- CRUD --

    def get(self, uid: str) -> FsRecord | None:
        """Read a single record from disk by uid."""
        fp = self._record_file(uid)
        if not fp.exists():
            return None
        rec = self.record_class.from_json(fp)
        if self.storage_layout == StorageLayout.FOLDER:
            rec.path = str(fp.parent)
        return rec

    def create(self, record: FsRecord | dict) -> FsRecord:
        """Persist a new record to disk. Raises if uid already exists."""
        if isinstance(record, dict):
            record = self.record_class.from_dict(record)
        fp = self._record_file(record.uid, record.type)
        if fp.exists():
            raise ValueError(f"Record with uid {record.uid!r} already exists")
        self._write(record, fp)
        return record

    def save(self, record: FsRecord) -> None:
        """Persist a record to disk (create or overwrite)."""
        fp = self._record_file(record.uid, record.type)
        self._write(record, fp)

    def update(self, uid: str, data: dict[str, Any]) -> FsRecord:
        """Read a record, apply field updates, and persist. Raises if missing."""
        record = self.get(uid)
        if record is None:
            raise KeyError(f"No record with uid {uid!r}")
        known_fields = {f.name for f in fields(record)}
        for key, value in data.items():
            if key in known_fields:
                setattr(record, key, value)
            else:
                record.extra[key] = value
        self.save(record)
        return record

    def delete(self, uid: str) -> bool:
        """Remove a record from disk. Returns True if it existed."""
        fp = self._record_file(uid)
        if not fp.exists():
            return False
        if self.storage_layout == StorageLayout.FOLDER:
            shutil.rmtree(fp.parent, ignore_errors=True)
        else:
            fp.unlink(missing_ok=True)
        return True

    # -- Collection access (lazy iteration from disk) --

    def __iter__(self) -> Iterator[FsRecord]:
        """Iterate all records, reading each from disk one at a time."""
        if not self.list_path or not self.list_path.is_dir():
            return
        if self.storage_layout == StorageLayout.FOLDER:
            for entry in sorted(self.list_path.iterdir()):
                if not entry.is_dir() or "-@" not in entry.name:
                    continue
                rj = entry / _RECORD_JSON
                if not rj.exists():
                    continue
                try:
                    rec = self.record_class.from_json(rj)
                    rec.path = str(entry)
                    yield rec
                except (json.JSONDecodeError, OSError):
                    continue
        else:
            for fp in sorted(self.list_path.glob("*-@*.json")):
                try:
                    yield self.record_class.from_json(fp)
                except (json.JSONDecodeError, OSError):
                    continue

    def __len__(self) -> int:
        """Count records on disk without loading them."""
        if not self.list_path or not self.list_path.is_dir():
            return 0
        if self.storage_layout == StorageLayout.FOLDER:
            return sum(
                1 for e in self.list_path.iterdir()
                if e.is_dir() and "-@" in e.name and (e / _RECORD_JSON).exists()
            )
        return sum(1 for _ in self.list_path.glob("*-@*.json"))

    @property
    def records(self) -> list[FsRecord]:
        """Return all records as a list (reads every file from disk)."""
        return list(self)

    # -- Internal --

    def _write(self, record: FsRecord, fp: Path) -> None:
        """Write a single record to its file path."""
        fp.parent.mkdir(parents=True, exist_ok=True)
        if self.storage_layout == StorageLayout.FOLDER:
            record.path = str(fp.parent)
        record.to_json(fp)
