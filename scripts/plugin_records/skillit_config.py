"""SkillitConfig — a typed record for global skillit configuration."""

from __future__ import annotations

from dataclasses import dataclass

from fs_store import FsRecord, SkillitRecordType


@dataclass
class SkillitConfig(FsRecord):
    """Persistent configuration record.

    Stored at ``~/.flow/records/skillit_config/record.json``.
    """

    user_rules_enabled: bool = True

    def __post_init__(self):
        if not self.type:
            self.type = SkillitRecordType.SKILLIT_CONFIG
        if not self.name:
            self.name = "skillit_config"
