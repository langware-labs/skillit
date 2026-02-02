"""Filesystem-backed entity implementation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar, Iterable, TypeVar

from pydantic import ValidationError

from ..api import Scope
from .fs_record import FsRecord
from .fs_storage import FsStorage
from .scope_resolver import ScopeResolver
from .type_helpers import looks_like_typeid, type_id_str

EntityType = TypeVar("EntityType", bound="FsEntity")


class FsEntity(FsRecord):
    _storage: ClassVar[FsStorage | None] = None
    _resolver: ClassVar[ScopeResolver | None] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        try:
            from .type_registry import registry

            registry.register(cls.get_type(), cls)
        except Exception:
            # Registry is optional in minimal contexts
            pass

    @classmethod
    def get_type(cls) -> str:
        default_type = getattr(cls, "type", None)
        if isinstance(default_type, str) and default_type:
            return default_type
        return cls.__name__.lower()

    @classmethod
    def _ensure_storage(cls) -> FsStorage:
        if cls._storage is None:
            cls._storage = FsStorage(cls._resolver or ScopeResolver())
        return cls._storage

    @classmethod
    def _resolve_scope_value(cls, scope: Scope | str | None) -> str:
        if scope is None:
            return Scope.USER.value
        return scope.value if isinstance(scope, Scope) else str(scope)

    @classmethod
    def _coerce_typeid(cls, eid: str) -> str:
        if looks_like_typeid(eid):
            return eid
        return type_id_str(cls.get_type(), eid)

    def save(self: EntityType) -> EntityType:
        storage = self._ensure_storage()
        now = datetime.now(timezone.utc)
        if not self.created_at:
            self.created_at = now
        self.modified_at = now
        if not self.type:
            self.type = self.get_type()

        scope_value = self._resolve_scope_value(self.scope)
        entity_dir = storage.entity_dir(scope_value, self.typeid)
        self.path = str(entity_dir)
        self.source_file = str(storage.entity_json_path(entity_dir))

        storage.write(entity_dir, self.model_dump(mode="json"))
        return self

    def delete(self) -> bool:
        storage = self._ensure_storage()
        scope_value = self._resolve_scope_value(self.scope)
        entity_dir = storage.entity_dir(scope_value, self.typeid)
        return storage.delete(entity_dir)

    @classmethod
    def _load_from_dir(cls: type[EntityType], entity_dir) -> EntityType | None:
        storage = cls._ensure_storage()
        data = storage.read(entity_dir)
        if not data:
            return None
        try:
            return cls.model_validate(data)
        except ValidationError:
            return None

    @classmethod
    def get_by_id(cls: type[EntityType], eid: str, scope: Scope | str | None = None) -> EntityType | None:
        storage = cls._ensure_storage()
        typeid = cls._coerce_typeid(eid)
        for root in storage.resolver.roots_for_scope(scope):
            entity_dir = root / typeid
            if entity_dir.exists():
                return cls._load_from_dir(entity_dir)
        return None

    @classmethod
    def _iter_entity_dirs(cls, scope: Scope | str | None = None) -> Iterable:
        storage = cls._ensure_storage()
        for root in storage.resolver.roots_for_scope(scope):
            if not root.exists():
                continue
            for entry in root.iterdir():
                if entry.is_dir():
                    yield entry

    @classmethod
    def get_all(
        cls: type[EntityType],
        scope: Scope | str | None = None,
        limit: int = 0,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> list[EntityType]:
        items: list[EntityType] = []
        entity_type = cls.get_type()
        for entity_dir in cls._iter_entity_dirs(scope):
            storage = cls._ensure_storage()
            data = storage.read(entity_dir)
            if not data:
                continue

            if cls is not FsEntity and data.get("type") != entity_type:
                continue

            target_cls: type[FsEntity] = cls
            if cls is FsEntity:
                try:
                    from .type_registry import registry

                    target_cls = registry.get(data.get("type", "")) or cls
                except Exception:
                    target_cls = cls

            try:
                item = target_cls.model_validate(data)
            except ValidationError:
                continue
            if filters:
                if any(item.model_dump().get(k) != v for k, v in filters.items()):
                    continue
            items.append(item)  # type: ignore[arg-type]
        if offset:
            items = items[offset:]
        if limit and limit > 0:
            items = items[:limit]
        return items

    @classmethod
    def get_one(cls: type[EntityType], **filters) -> EntityType | None:
        items = cls.get_all(filters=filters, limit=2)
        if not items:
            return None
        if len(items) > 1:
            raise ValueError("Multiple entities matched filters")
        return items[0]
