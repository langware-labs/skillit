"""SkillitConfig — a typed record for global skillit configuration."""

from __future__ import annotations

from typing import Any, ClassVar

from flow_sdk.fs_store import Record, SkillitRecordType


class SkillitConfig(Record):
    """Persistent configuration record.

    Stored at ``~/.flow/records/skillit_config/record.json``.
    """

    _record_type: ClassVar[str] = str(SkillitRecordType.SKILLIT_CONFIG)

    def __init__(self, **kwargs: Any):
        kwargs.setdefault("type", SkillitRecordType.SKILLIT_CONFIG)
        kwargs.setdefault("name", "skillit_config")
        kwargs.setdefault("user_rules_enabled", True)
        super().__init__(**kwargs)
