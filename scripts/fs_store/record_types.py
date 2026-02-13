"""Record type constants used across the fs_store layer."""

from enum import StrEnum


class RecordType(StrEnum):
    SESSION = "session"
    TASK = "task"
    RULE = "rule"
    SKILL_EVENT = "skill_event"
    SKILL_ACTIVATION = "skill_activation"
    LOG = "log"
