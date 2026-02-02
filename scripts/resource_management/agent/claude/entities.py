"""Claude-specific filesystem entities."""

from __future__ import annotations

from pydantic import Field

from ...fs.fs_entity import FsEntity


class HookResource(FsEntity):
    type: str = Field(default="hook")
    event_type: str = Field(default="")
    matcher: str = Field(default="*")
    command: str = Field(default="")
    hook_type: str = Field(default="command")


class McpServerResource(FsEntity):
    type: str = Field(default="mcp_server")
    command: str = Field(default="")
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)


class CommandResource(FsEntity):
    type: str = Field(default="command")


class AgentResource(FsEntity):
    type: str = Field(default="agent")


class SkillResource(FsEntity):
    type: str = Field(default="skill")
    usage_count: int = Field(default=0)
