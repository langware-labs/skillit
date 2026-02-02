"""Type registry for filesystem entities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from .fs_entity import FsEntity


class TypeRegistry:
    def __init__(self) -> None:
        self._types: dict[str, Type["FsEntity"]] = {}

    def register(self, entity_type: str, cls: Type["FsEntity"]) -> None:
        if entity_type:
            self._types[entity_type] = cls

    def get(self, entity_type: str) -> Type["FsEntity"] | None:
        return self._types.get(entity_type)

    def items(self) -> dict[str, Type["FsEntity"]]:
        return dict(self._types)


# Global registry
registry = TypeRegistry()
