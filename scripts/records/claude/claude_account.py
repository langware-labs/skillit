"""ClaudeAccountFsRecord — represents the Claude Code account / login state.

Source: ~/.claude.json
Contains startup stats, install method, feature gates, tips history,
and API key approval state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fs_store import FsRecord, RecordType


@dataclass
class ClaudeAccountFsRecord(FsRecord):
    """Claude Code account and login state.

    Mapped from ``~/.claude.json``.
    """

    num_startups: int = 0
    install_method: str = ""
    auto_updates: bool = False
    has_seen_tasks_hint: bool = False
    prompt_queue_use_count: int = 0
    custom_api_key_responses: dict[str, list[str]] = field(default_factory=dict)
    tips_history: dict[str, int] = field(default_factory=dict)
    cached_statsig_gates: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self):
        if not self.type:
            self.type = "account"
        if not self.id:
            self.id = "default"
