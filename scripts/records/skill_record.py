"""SkillitSkill — a typed record for skills managed by skillit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fs_store import FsRecord, RecordType


@dataclass
class SkillRecord(FsRecord):
    """A skill record backed by FsRecord.

    Each skill is stored as
    ``~/.flow/records/skill/skill-@<id>/record.json``
    using the FOLDER storage layout.
    """

    name: str = ""
    description: str = ""
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.type:
            self.type = RecordType.SKILL
        if self.name and not self.name:
            self.name = self.name
