"""AgenticProcess record type for tracking processor lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from fs_store import FsRecord, RecordType


class ProcessorStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    COMPLETE = "complete"
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass
class AgenticProcess(FsRecord):
    state: str = field(default=ProcessorStatus.IDLE)
    worker_id: str | None = None

    def __post_init__(self):
        if not self.type:
            self.type = RecordType.AGENTIC_PROCESS
