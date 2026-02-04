"""Hook event types for Claude Code hooks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class HookEventType(StrEnum):
    """Available Claude Code hook event types."""

    # User interaction hooks
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    """Triggered when user submits a prompt."""

    # Tool lifecycle hooks
    PRE_TOOL_USE = "PreToolUse"
    """Triggered before a tool is executed. Can block or modify input."""

    POST_TOOL_USE = "PostToolUse"
    """Triggered after a tool completes. Can run cleanup/validation."""

    # Session hooks
    STOP = "Stop"
    """Triggered when Claude finishes responding."""

    NOTIFICATION = "Notification"
    """Triggered when Claude needs user input."""

    SESSION_START = "SessionStart"
    """Triggered when session starts or resumes."""

    # Context hooks
    PRE_COMPACT = "PreCompact"
    """Triggered before context compaction."""

    # Subagent hooks
    SUBAGENT_STOP = "SubagentStop"
    """Triggered when a subagent completes its task."""

    # Permission hooks
    PERMISSION_REQUEST = "PermissionRequest"
    """Triggered when a tool requests permission."""


@dataclass
class HookEvent:
    hook_event: str
    hook_name: str
    command: str | None = None
    tool_use_id: str | None = None
    parent_tool_use_id: str | None = None
    timestamp: str | None = None
    entry_index: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)
