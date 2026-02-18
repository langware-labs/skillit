"""ClaudeMcpServerFsRecord — represents a configured MCP server.

Source: ~/.claude/mcp.json (user-level), .mcp.json or .claude/mcp.json (project-level)
Each server has a command, args, optional env vars, and a scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fs_store import FsRecord, RecordType


@dataclass
class ClaudeMcpServerFsRecord(FsRecord):
    """An MCP server configuration.

    Mapped from ``mcp.json`` ``mcpServers.<name>`` entries.
    """

    server_name: str = ""
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    scope: str = "user"

    def __post_init__(self):
        if not self.type:
            self.type = "mcp_server"
        if self.server_name:
            self.id = f"{self.scope}:{self.server_name}"
            if not self.name:
                self.name = self.server_name
