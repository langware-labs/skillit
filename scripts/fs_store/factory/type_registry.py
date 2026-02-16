"""Type registry — maps record type strings to their Python classes.

Explicit registration of the known record types.
Use ``type_registry.get(RecordType.SKILL)`` to look up a class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fs_store.fs_record import FsRecord


class TypeRegistry:
    """Maps type name strings to FsRecord subclasses."""

    def __init__(self):
        self._types: dict[str, type[FsRecord]] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        from fs_store.record_types import RecordType, SkillitRecordType
        from records.skill_record import SkillRecord
        from plugin_records.skillit_session import SkillitSession
        from plugin_records.skillit_config import SkillitConfig

        self._types[RecordType.SKILL] = SkillRecord
        self._types[SkillitRecordType.SKILLIT_SESSION] = SkillitSession
        self._types[SkillitRecordType.SKILLIT_CONFIG] = SkillitConfig

    def register(self, type_name: str, cls: type[FsRecord]) -> None:
        """Register a record class under a type name."""
        if type_name:
            self._types[type_name] = cls

    def get(self, type_name: str) -> type[FsRecord] | None:
        """Look up a record class by type name, or None if unknown."""
        self._ensure_loaded()
        return self._types.get(type_name)

    def get_all_types(self) -> list[str]:
        """Return all registered type name strings."""
        self._ensure_loaded()
        return list(self._types.keys())

    def __contains__(self, type_name: str) -> bool:
        self._ensure_loaded()
        return type_name in self._types

    def __len__(self) -> int:
        self._ensure_loaded()
        return len(self._types)


type_registry = TypeRegistry()
