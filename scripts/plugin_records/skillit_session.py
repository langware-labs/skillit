"""SkillitSession — a typed record for agent sessions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fs_store import FsRecord, SkillitRecordType


@dataclass
class SkillitSession(FsRecord):
    """An agent session backed by FsRecord.

    Each session is stored as
    ``~/.flow/records/skillit_session/skillit_session-@<id>/record.json``
    using the FOLDER storage layout.
    """

    session_id: str = ""

    def __post_init__(self):
        if not self.type:
            self.type = SkillitRecordType.SKILLIT_SESSION
        if self.session_id:
            self.id = self.session_id
            if not self.name:
                self.name = self.session_id

    # -- Convenience helpers --

    @classmethod
    def load_session(cls, session_dir: Path) -> SkillitSession:
        """Load (or create) the session record from a session directory."""
        record_path = session_dir / "record.json"
        base = FsRecord.from_json(record_path)
        return cls.from_dict(base.to_dict())
