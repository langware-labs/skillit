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
from records.skill_record import SkillRecord


class SkillitRecords:
    """Manages skillit record collections with lazy initialization."""

    def __init__(self, records_path: Path | None = None):
        self._records_path = records_path
        self._config: SkillitConfig | None = None
        self._sessions: ResourceRecordList | None = None
        self._skills: ResourceRecordList | None = None

    def _get_records_path(self) -> Path:
        if self._records_path is not None:
            return self._records_path
        from utils.conf import RECORDS_PATH
        return RECORDS_PATH

    @property
    def config(self) -> SkillitConfig:
        if self._config is None:
            path = self._get_records_path() / "skillit_config" / "record.json"
            self._config = SkillitConfig.load_record(path)
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

    @property
    def skills(self) -> ResourceRecordList:
        if self._skills is None:
            self._skills = ResourceRecordList(
                record_class=SkillRecord,
                records_path=self._get_records_path(),
                storage_layout=StorageLayout.FOLDER,
            )
        return self._skills

    def get_skill(self, skill_id: str) -> SkillRecord | None:
        """Get a skill by ID, or None if it doesn't exist."""
        return self.skills.get(skill_id)

    def create_skill(self, skill_name: str, **kwargs) -> SkillRecord:
        """Create a new skill record with the given name."""
        skill = SkillRecord(skill_name=skill_name, **kwargs)
        self.skills.save(skill)
        return skill

    # -- Entity CRUD entry point --

    def entity_crud(self, session_id: str, crud: str, entity: dict) -> str:
        """Main entry point for CRUD operations on entity records.

        Called by the MCP tool. Resolves the session, then dispatches
        to the appropriate action method.

        Args:
            session_id: The claude session ID.
            crud: "create", "read", "update", or "delete".
            entity: Dict with at least "type" (and "id" for read/update/delete).

        Returns:
            Result message string.
        """
        session = self._get_or_create_session(session_id)
        record_type = entity.get("type")

        if crud == "create":
            return self._entity_create(session, record_type, entity)
        elif crud == "read":
            return self._entity_read(session, record_type, entity)
        elif crud == "update":
            return self._entity_update(session, record_type, entity)
        elif crud == "delete":
            return self._entity_delete(session, record_type, entity)
        else:
            return f"Error: unknown CRUD operation '{crud}'"

    def _entity_create(self, session: SkillitSession, record_type: str, entity: dict) -> str:
        raise NotImplementedError

    def _entity_read(self, session: SkillitSession, record_type: str, entity: dict) -> str:
        raise NotImplementedError

    def _entity_update(self, session: SkillitSession, record_type: str, entity: dict) -> str:
        raise NotImplementedError

    def _entity_delete(self, session: SkillitSession, record_type: str, entity: dict) -> str:
        raise NotImplementedError

    # -- Session helpers --

    def _get_or_create_session(self, session_id: str) -> SkillitSession:
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id)
        return session

    def reset(self) -> None:
        """Clear cached instances so the next access re-loads from disk."""
        self._config = None
        self._sessions = None
        self._skills = None

    def get_session(self, claude_session_id: str) -> SkillitSession | None:
        """Get a session by ID, or None if it doesn't exist."""
        session = self.sessions.get(claude_session_id)
        return session

    def create_session(self, claude_session_id: str) -> SkillitSession | None:
        """Create a new session with the given ID.

        Raises if a session with that ID already exists.
        """
        session = SkillitSession(session_id=claude_session_id)
        self.sessions.save(session)
        return session



skillit_records = SkillitRecords()
