"""TypeId helpers for filesystem entities."""

from __future__ import annotations

import re

from flowpad.hub.api.identifier import type_uuid_pattern
from flowpad.hub.api.type_id import type_id_str as _type_id_str


def type_id_str(entity_type: str, entity_id: str) -> str:
    return _type_id_str(entity_type, entity_id)


def looks_like_typeid(value: str) -> bool:
    return re.fullmatch(type_uuid_pattern, value) is not None
