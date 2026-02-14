"""Relationship record type for graph edge synchronization."""

from __future__ import annotations

from dataclasses import dataclass

from fs_store import FsRecord, FsRecordRef


class RelationshipType:
    CHILD = "child"


@dataclass
class RelationshipRecord(FsRecord):
    """A first-class relationship record between two resource refs."""

    from_ref: FsRecordRef | dict | None = None
    to_ref: FsRecordRef | dict | None = None

    def __post_init__(self):
        if not self.type:
            self.type = RelationshipType.CHILD
        if isinstance(self.from_ref, dict):
            self.from_ref = FsRecordRef.from_dict(self.from_ref)
        if isinstance(self.to_ref, dict):
            self.to_ref = FsRecordRef.from_dict(self.to_ref)

    def to_dict(self) -> dict:
        """Serialize with FsRecordRef compact shape (omit null record_path)."""
        data = super().to_dict()
        if isinstance(self.from_ref, FsRecordRef):
            data["from_ref"] = self.from_ref.to_dict()
        if isinstance(self.to_ref, FsRecordRef):
            data["to_ref"] = self.to_ref.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> RelationshipRecord:
        """Deserialize and normalize ref fields into FsRecordRef."""
        rel = super().from_dict(data)
        if isinstance(rel.from_ref, dict):
            rel.from_ref = FsRecordRef.from_dict(rel.from_ref)
        if isinstance(rel.to_ref, dict):
            rel.to_ref = FsRecordRef.from_dict(rel.to_ref)
        return rel

    @staticmethod
    def make_id(rel_type: str, from_ref: FsRecordRef, to_ref: FsRecordRef) -> str:
        """Deterministic ID for the relationship edge."""
        return f"{rel_type}:{from_ref.type}:{from_ref.id}:{to_ref.type}:{to_ref.id}"

    @classmethod
    def child(cls, from_ref: FsRecordRef, to_ref: FsRecordRef) -> RelationshipRecord:
        """Create a canonical parent->child edge record."""
        rel_type = RelationshipType.CHILD
        return cls(
            id=cls.make_id(rel_type, from_ref, to_ref),
            type=rel_type,
            from_ref=from_ref,
            to_ref=to_ref,
        )
