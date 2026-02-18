"""ClaudePluginFsRecord — represents an installed Claude Code plugin.

Source: ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/
Plugins are cached by marketplace, plugin name, and commit hash version.
Enablement state is in ~/.claude/settings.json under ``enabledPlugins``.
"""

from __future__ import annotations

from dataclasses import dataclass

from fs_store import FsRecord, RecordType


@dataclass
class ClaudePluginFsRecord(FsRecord):
    """An installed Claude Code plugin.

    Mapped from ``~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/``.
    """

    plugin_name: str = ""
    marketplace: str = ""
    version_hash: str = ""
    enabled: bool = False
    plugin_path: str = ""

    def __post_init__(self):
        if not self.type:
            self.type = "plugin"
        if self.plugin_name and self.marketplace:
            self.id = f"{self.plugin_name}@{self.marketplace}"
            if not self.name:
                self.name = self.plugin_name
