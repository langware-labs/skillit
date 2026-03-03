"""SkillitSession — a typed record for agent sessions."""

from __future__ import annotations

from typing import Any, ClassVar

from flow_sdk.fs_store import Record, SkillitRecordType


class SkillitSession(Record):
    """An agent session backed by Record.

    Each session is stored as
    ``~/.flow/records/skillit_session/skillit_session-@<id>/record.json``
    using the FOLDER storage layout.
    """

    _record_type: ClassVar[str] = str(SkillitRecordType.SKILLIT_SESSION)

    def __init__(self, **kwargs: Any):
        session_id = kwargs.get("session_id", "")
        kwargs.setdefault("type", SkillitRecordType.SKILLIT_SESSION)
        if session_id:
            kwargs.setdefault("id", session_id)
            kwargs.setdefault("name", session_id)
        super().__init__(**kwargs)
