"""Base filesystem record implementing the ApiResource contract."""

from __future__ import annotations

from ..api import ResourceRecord
from .type_helpers import type_id_str


class FsRecord(ResourceRecord):
    @property
    def typeid(self) -> str:
        return type_id_str(self.type, self.id)
