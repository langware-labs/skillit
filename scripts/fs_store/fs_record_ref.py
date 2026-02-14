"""Lightweight reference to an FsRecord — id, type, and optional record_path."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FsRecordRef:
    """Flat reference to a record. Never embeds the full record data."""

    id: str
    type: str
    record_path: str | None = None

    def to_dict(self) -> dict:
        """Serialize to a plain dict, omitting record_path when None."""
        d: dict = {"id": self.id, "type": self.type}
        if self.record_path is not None:
            d["record_path"] = self.record_path
        return d

    @classmethod
    def from_dict(cls, data: dict) -> FsRecordRef:
        """Deserialize from a dict. Extra keys are silently ignored (backward compat)."""
        return cls(
            id=data["id"],
            type=data.get("type", ""),
            record_path=data.get("record_path"),
        )

    @classmethod
    def from_record(cls, record: object) -> FsRecordRef:
        """Build a ref from any record with uid/type attrs (duck-typed to avoid circular imports)."""
        return cls(
            id=record.uid,  # type: ignore[attr-defined]
            type=record.type,  # type: ignore[attr-defined]
            record_path=getattr(record, "source_file", None),
        )
