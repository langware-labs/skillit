"""Record type constants used across the fs_store layer."""

from enum import StrEnum


class RecordType(StrEnum):
    SESSION = "session"
    TASK = "task"
    RULE = "rule"
    SKILL = "skill"
    LOG = "log"
