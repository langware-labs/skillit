"""Filesystem resource management exports."""

from .fs_entity import FsEntity
from .fs_record import FsRecord
from .fs_storage import FsStorage
from .scope_resolver import ScopeResolver
from .type_registry import registry as type_registry

__all__ = [
    "FsEntity",
    "FsRecord",
    "FsStorage",
    "ScopeResolver",
    "type_registry",
]
