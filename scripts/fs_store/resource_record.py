"""Base resource record — pure data contract for unified resource management (stdlib only).

No filesystem I/O here; see ``FsRecord`` for persistence.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, TypeVar

from .fs_record_ref import FsRecordRef
from .scope import Scope

T = TypeVar("T", bound="ResourceRecord")

# Naming convention: <type>-@<uid>
_NAME_SEP = "-@"


def record_stem(record_type: str, uid: str) -> str:
    """Build the canonical stem used for file / folder names."""
    return f"{record_type}{_NAME_SEP}{uid}"


def parse_record_stem(stem: str) -> tuple[str, str]:
    """Parse a ``<type>-@<uid>`` stem into (type, uid)."""
    if _NAME_SEP not in stem:
        raise ValueError(f"Invalid record stem: {stem!r}")
    record_type, uid = stem.split(_NAME_SEP, 1)
    return record_type, uid


@dataclass
class ResourceRecord:
    """Base record shared by file-system, database, and cloud entities.

    Pure data contract — serialization only, no I/O.
    Doubles as a key-value store via dict-style access on ``extra``.
    """

    # Which field serves as the unique identifier.
    # Subclasses can override (e.g. uid_field_name = "entity_id").
    uid_field_name: ClassVar[str] = "id"

    @property
    def uid(self) -> str:
        """Return the value of the field designated as the unique id."""
        return getattr(self, self.uid_field_name)

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    name: str = ""

    # Audit
    created_at: datetime | None = None
    modified_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None

    # Scope and location
    scope: Scope | str = Scope.USER
    source_file: str | None = None
    path: str | None = None

    # Cloud sync link
    entity_id: str | None = None

    # Extra fields (replaces Pydantic extra="allow")
    extra: dict = field(default_factory=dict)

    # Relationships (flat refs, never embedded objects)
    children_refs: list[FsRecordRef] = field(default_factory=list)
    parent_ref: FsRecordRef | None = None

    # -- Naming helpers --

    @property
    def stem(self) -> str:
        """Canonical ``<type>-@<uid>`` stem for this record."""
        return record_stem(self.type, self.uid)

    # -- Key-value access --

    def __getitem__(self, key: str) -> Any:
        known = {f.name for f in self.__dataclass_fields__.values()}
        if key in known:
            return getattr(self, key)
        return self.extra[key]

    def __setitem__(self, key: str, value: Any) -> None:
        known = {f.name for f in self.__dataclass_fields__.values()}
        if key in known:
            setattr(self, key, value)
        else:
            self.extra[key] = value

    def __delitem__(self, key: str) -> None:
        if key not in self.extra:
            raise KeyError(key)
        del self.extra[key]

    def __contains__(self, key: str) -> bool:
        known = {f.name for f in self.__dataclass_fields__.values()}
        return key in known or key in self.extra

    def keys(self) -> list[str]:
        """All field names + extra keys."""
        known = [f.name for f in self.__dataclass_fields__.values() if f.name != "extra"]
        return known + list(self.extra.keys())

    # -- Serialization --

    def to_dict(self) -> dict:
        """Serialize to a plain dict."""
        def _convert(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, Enum):
                return obj.value
            return obj

        data = asdict(self)
        result = {}
        for key, value in data.items():
            if key in ("extra", "children_refs", "parent_ref"):
                continue
            result[key] = _convert(value)
        # Merge extra fields at the top level
        for key, value in data.get("extra", {}).items():
            result[key] = _convert(value)
        # Serialize children refs
        if self.children_refs:
            result["children"] = [c.to_dict() for c in self.children_refs]
        # Serialize parent ref
        if self.parent_ref is not None:
            result["parent"] = self.parent_ref.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> ResourceRecord:
        """Deserialize from a plain dict."""
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        kwargs: dict[str, Any] = {}
        extra: dict[str, Any] = {}

        for key, value in data.items():
            if key in ("children", "children_refs", "parent", "parent_ref", "parent_id"):
                continue  # handled below
            elif key in known_fields and key != "extra":
                kwargs[key] = value
            else:
                extra[key] = value

        # Deserialize children as FsRecordRef
        raw_children = data.get("children", [])
        if raw_children:
            kwargs["children_refs"] = [FsRecordRef.from_dict(c) for c in raw_children]

        # Deserialize parent ref (new format: dict, old format: parent_id string)
        raw_parent = data.get("parent")
        if isinstance(raw_parent, dict):
            kwargs["parent_ref"] = FsRecordRef.from_dict(raw_parent)
        elif "parent_id" in data and data["parent_id"] is not None:
            kwargs["parent_ref"] = FsRecordRef(id=data["parent_id"], type="")

        # Coerce scope to Scope enum when possible
        if "scope" in kwargs and isinstance(kwargs["scope"], str):
            try:
                kwargs["scope"] = Scope(kwargs["scope"])
            except ValueError:
                pass  # keep as raw string

        # Coerce datetime strings
        for dt_field in ("created_at", "modified_at"):
            val = kwargs.get(dt_field)
            if isinstance(val, str):
                kwargs[dt_field] = datetime.fromisoformat(val)

        # Merge any explicit extra from data with overflow keys
        if "extra" in data and isinstance(data["extra"], dict):
            extra.update(data["extra"])
        kwargs["extra"] = extra

        return cls(**kwargs)
