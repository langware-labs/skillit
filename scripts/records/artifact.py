"""Artifact record type."""

from __future__ import annotations

from dataclasses import dataclass

from fs_store import FsRecord, RecordType


@dataclass
class Artifact(FsRecord):
    name: str = ""
    value: str = ""
    artifact_type: str = ""

    def __post_init__(self):
        if not self.type:
            self.type = RecordType.ARTIFACT
