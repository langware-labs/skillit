"""A typed collection of ResourceRecords backed by JSONL, flat files, or folders."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, TypeVar

from .resource_record import ResourceRecord, parse_record_stem
from .storage_layout import StorageLayout

T = TypeVar("T", bound=ResourceRecord)

_RECORD_JSON = "record.json"


@dataclass
class ResourceRecordList:
    """Ordered collection of records persisted to disk.

    ``storage_layout`` controls how individual records are stored:

    * ``LIST_ITEM`` – all records in one JSONL file (``list_path`` is the file).
    * ``FILE``      – one ``<type>-@<uid>.json`` file per record inside ``list_path/``.
    * ``FOLDER``    – one ``<type>-@<uid>/record.json`` directory per record inside ``list_path/``.

    All lookups use the record's ``uid`` property.

    When ``list_path`` is omitted the collection path is computed as
    ``records_path / <record_type>``, where *records_path* defaults to
    ``~/.flow/records`` (the ``RECORDS_PATH`` constant from ``utils.conf``).
    The record type is inferred from ``record_class``.
    """

    list_path: Path | None = None
    record_class: type[ResourceRecord] = field(default=ResourceRecord)
    storage_layout: StorageLayout = field(default=StorageLayout.LIST_ITEM)
    records_path: Path | None = None
    _records: list[ResourceRecord] = field(default_factory=list, init=False, repr=False)
    _loaded: bool = field(default=False, init=False, repr=False)

    def __post_init__(self):
        if self.list_path is None:
            record_type = self.record_class().type
            if not record_type:
                raise ValueError(
                    "list_path is required when record_class has no default type"
                )
            base = self.records_path
            if base is None:
                from utils.conf import RECORDS_PATH
                base = RECORDS_PATH
            self.list_path = base / record_type

    # -- Persistence --

    def load(self) -> list[ResourceRecord]:
        """Read all records from disk into memory."""
        loader = {
            StorageLayout.LIST_ITEM: self._load_jsonl,
            StorageLayout.FILE: self._load_files,
            StorageLayout.FOLDER: self._load_folders,
        }
        self._records = loader[self.storage_layout]()
        self._loaded = True
        return list(self._records)

    def save(self) -> None:
        """Persist all in-memory records to disk."""
        saver = {
            StorageLayout.LIST_ITEM: self._save_jsonl,
            StorageLayout.FILE: self._save_files,
            StorageLayout.FOLDER: self._save_folders,
        }
        saver[self.storage_layout]()

    # -- CRUD --

    def create(self, record_or_dict: ResourceRecord | dict) -> ResourceRecord:
        """Add a new record. Accepts a ResourceRecord instance or a raw dict."""
        self._ensure_loaded()
        if isinstance(record_or_dict, dict):
            record = self.record_class.from_dict(record_or_dict)
        else:
            record = record_or_dict
        if self._find(record.uid) is not None:
            raise ValueError(f"Record with uid {record.uid!r} already exists")
        self._records.append(record)
        return record

    def get(self, uid: str) -> ResourceRecord | None:
        """Look up a record by uid."""
        self._ensure_loaded()
        return self._find(uid)

    def update(self, uid: str, data: dict[str, Any]) -> ResourceRecord:
        """Update fields on an existing record. Returns the updated record."""
        self._ensure_loaded()
        record = self._find(uid)
        if record is None:
            raise KeyError(f"No record with uid {uid!r}")
        known_fields = {f.name for f in record.__dataclass_fields__.values()}
        for key, value in data.items():
            if key in known_fields:
                setattr(record, key, value)
            else:
                record.extra[key] = value
        return record

    def delete(self, uid: str) -> bool:
        """Remove a record by uid. Returns True if found and removed."""
        self._ensure_loaded()
        before = len(self._records)
        self._records = [r for r in self._records if r.uid != uid]
        return len(self._records) < before

    # -- Collection access --

    @property
    def records(self) -> list[ResourceRecord]:
        self._ensure_loaded()
        return list(self._records)

    def __iter__(self) -> Iterator[ResourceRecord]:
        self._ensure_loaded()
        return iter(self._records)

    def __len__(self) -> int:
        self._ensure_loaded()
        return len(self._records)

    # -- LIST_ITEM backend (JSONL) --

    def _load_jsonl(self) -> list[ResourceRecord]:
        if not self.list_path.exists():
            return []
        records: list[ResourceRecord] = []
        with open(self.list_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                records.append(self.record_class.from_dict(data))
        return records

    def _save_jsonl(self) -> None:
        self.list_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.list_path, "w", encoding="utf-8") as fh:
            for record in self._records:
                fh.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    # -- FILE backend (<type>-@<uid>.json) --

    def _load_files(self) -> list[ResourceRecord]:
        if not self.list_path.is_dir():
            return []
        records: list[ResourceRecord] = []
        for fp in sorted(self.list_path.glob("*-@*.json")):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            records.append(self.record_class.from_dict(data))
        return records

    def _save_files(self) -> None:
        self.list_path.mkdir(parents=True, exist_ok=True)
        existing = {fp.stem for fp in self.list_path.glob("*-@*.json")}
        current_stems: set[str] = set()
        for record in self._records:
            current_stems.add(record.stem)
            fp = self.list_path / f"{record.stem}.json"
            fp.write_text(
                json.dumps(record.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        for orphan in existing - current_stems:
            (self.list_path / f"{orphan}.json").unlink(missing_ok=True)

    # -- FOLDER backend (<type>-@<uid>/record.json) --

    def _load_folders(self) -> list[ResourceRecord]:
        if not self.list_path.is_dir():
            return []
        records: list[ResourceRecord] = []
        for entry in sorted(self.list_path.iterdir()):
            if not entry.is_dir() or "-@" not in entry.name:
                continue
            rj = entry / _RECORD_JSON
            if not rj.exists():
                continue
            try:
                data = json.loads(rj.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            rec = self.record_class.from_dict(data)
            rec.path = str(entry)
            records.append(rec)
        return records

    def _save_folders(self) -> None:
        self.list_path.mkdir(parents=True, exist_ok=True)
        existing = {
            entry.name
            for entry in self.list_path.iterdir()
            if entry.is_dir() and "-@" in entry.name
        }
        current_stems: set[str] = set()
        for record in self._records:
            current_stems.add(record.stem)
            rec_dir = self.list_path / record.stem
            rec_dir.mkdir(parents=True, exist_ok=True)
            record.path = str(rec_dir)
            (rec_dir / _RECORD_JSON).write_text(
                json.dumps(record.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        # Clean up orphaned directories (only remove record.json, leave dir if non-empty)
        import shutil
        for orphan in existing - current_stems:
            shutil.rmtree(self.list_path / orphan, ignore_errors=True)

    # -- Internals --

    def _find(self, uid: str) -> ResourceRecord | None:
        for r in self._records:
            if r.uid == uid:
                return r
        return None

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()
