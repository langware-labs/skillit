"""SkillitRecords — central manager for skillit record collections.

Provides lazy access to:
- ``config``   — singleton ``SkillitConfig`` with live fs_sync
- ``sessions`` — ``ResourceRecordList`` of ``SkillitSession`` records

Usage::

    from plugin_records.skillit_records import skillit_records

    print(skillit_records.config.user_rules_enabled)
    skillit_records.config.user_rules_enabled = False  # auto-persists
"""

from __future__ import annotations

from pathlib import Path

from fs_store import ResourceRecordList, StorageLayout

from .skillit_config import SkillitConfig
from .skillit_session import SkillitSession


class SkillitRecords:
    """Manages skillit record collections with lazy initialization."""

    def __init__(self, records_path: Path | None = None):
        self._records_path = records_path
        self._config: SkillitConfig | None = None
        self._sessions: ResourceRecordList | None = None

    def _get_records_path(self) -> Path:
        if self._records_path is not None:
            return self._records_path
        from utils.conf import RECORDS_PATH
        return RECORDS_PATH

    @property
    def config(self) -> SkillitConfig:
        if self._config is None:
            path = self._get_records_path() / "skillit_config" / "record.json"
            self._config = SkillitConfig.from_json(path)
            self._config.fs_sync = True
        return self._config

    @property
    def sessions(self) -> ResourceRecordList:
        if self._sessions is None:
            self._sessions = ResourceRecordList(
                record_class=SkillitSession,
                records_path=self._get_records_path(),
                storage_layout=StorageLayout.FOLDER,
            )
        return self._sessions

    def reset(self) -> None:
        """Clear cached instances so the next access re-loads from disk."""
        self._config = None
        self._sessions = None


skillit_records = SkillitRecords()
