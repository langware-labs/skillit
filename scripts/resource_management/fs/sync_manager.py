"""Cloud sync helpers for filesystem entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .fs_entity import FsEntity


class SyncStatus(str, Enum):
    SYNCED = "synced"
    LOCAL_ONLY = "local_only"
    CLOUD_ONLY = "cloud_only"
    CONFLICT = "conflict"


@dataclass
class SyncResult:
    status: SyncStatus
    entity: FsEntity | None
    cloud: dict[str, Any] | None


class SyncManager:
    """Minimal bidirectional sync helper.

    Cloud calls are expected to be implemented by a higher layer.
    """

    def get_sync_status(self, local: FsEntity | None, cloud: dict | None) -> SyncStatus:
        if local and cloud:
            if local.entity_id and cloud.get("id") == local.entity_id:
                return SyncStatus.SYNCED
            return SyncStatus.CONFLICT
        if local and not cloud:
            return SyncStatus.LOCAL_ONLY
        if cloud and not local:
            return SyncStatus.CLOUD_ONLY
        return SyncStatus.LOCAL_ONLY

    def resolve_conflict(self, local: FsEntity, cloud: dict, strategy: str = "newer_wins") -> FsEntity:
        if strategy == "local_wins":
            return local
        if strategy == "cloud_wins":
            return self._apply_cloud(local, cloud)
        if strategy == "newer_wins":
            local_time = local.modified_at or datetime.min
            cloud_time = self._parse_time(cloud.get("modified_at"))
            if cloud_time and cloud_time > local_time:
                return self._apply_cloud(local, cloud)
            return local
        return local

    def _apply_cloud(self, local: FsEntity, cloud: dict) -> FsEntity:
        for key, value in cloud.items():
            if hasattr(local, key):
                setattr(local, key, value)
        return local

    def _parse_time(self, value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None
