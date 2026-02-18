"""ClaudePlanFsRecord — represents a saved Claude Code session plan.

Source: ~/.claude/plans/<slug>.md
Markdown files containing implementation plans generated during plan mode.
"""

from __future__ import annotations

from dataclasses import dataclass

from fs_store import FsRecord, RecordType


@dataclass
class ClaudePlanFsRecord(FsRecord):
    """A saved Claude Code session plan.

    Mapped from ``~/.claude/plans/<slug>.md``.
    """

    slug: str = ""
    content: str = ""

    def __post_init__(self):
        if not self.type:
            self.type = "plan"
        if self.slug:
            self.id = self.slug
            if not self.name:
                self.name = self.slug
