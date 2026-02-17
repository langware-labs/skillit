"""Manage the skillit plugin version files."""

import json
from pathlib import Path

from utils.conf import LOG_FILE, SKILLIT_HOME
from utils.template_render import render

SKILLIT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = SKILLIT_ROOT / "templates"
AGENTS_DIR = SKILLIT_ROOT / "agents"


class SkillitPluginManager:
    """Read and bump the skillit plugin version."""

    def __init__(self):
        self._plugin_json = SKILLIT_ROOT / ".claude-plugin" / "plugin.json"
        self._marketplace_json = SKILLIT_ROOT / ".claude-plugin" / "marketplace.json"

    @property
    def version(self) -> str:
        """Return the current plugin version."""
        return json.loads(self._plugin_json.read_text())["version"]

    def _write_version(self, new_version: str) -> None:
        """Write *new_version* to both plugin.json and marketplace.json."""
        plugin = json.loads(self._plugin_json.read_text())
        plugin["version"] = new_version
        self._plugin_json.write_text(json.dumps(plugin, indent=2) + "\n")

        marketplace = json.loads(self._marketplace_json.read_text())
        for p in marketplace.get("plugins", []):
            if p["name"] == plugin["name"]:
                p["version"] = new_version
        self._marketplace_json.write_text(json.dumps(marketplace, indent=2) + "\n")

    def patch(self) -> str:
        """Bump the patch version and return the new version string."""
        major, minor, patch = (int(x) for x in self.version.split("."))
        new_version = f"{major}.{minor}.{patch + 1}"
        self._write_version(new_version)
        return new_version

    def minor(self) -> str:
        """Bump the minor version and return the new version string."""
        major, minor, _patch = (int(x) for x in self.version.split("."))
        new_version = f"{major}.{minor + 1}.0"
        self._write_version(new_version)
        return new_version

    def major(self) -> str:
        """Bump the major version and return the new version string."""
        major, _minor, _patch = (int(x) for x in self.version.split("."))
        new_version = f"{major + 1}.0.0"
        self._write_version(new_version)
        return new_version

    @staticmethod
    def clear_log() -> None:
        """Delete the skill log file if it exists."""
        if LOG_FILE.exists():
            LOG_FILE.unlink()

    @staticmethod
    def print_log() -> str:
        """Return the skill log contents (also prints to stdout)."""
        if LOG_FILE.exists():
            text = LOG_FILE.read_text()
            print(text, end="")
            return text
        print(f"No log file at {LOG_FILE}")
        return ""

    def build(self) -> None:
        """Render all templates in templates/ into agents/ with current plugin context."""
        agent_common_path = TEMPLATES_DIR / "agent_common.md"
        agent_common = agent_common_path.read_text() if agent_common_path.exists() else ""
        context = {
            "version": self.version,
            "skillit_home": str(SKILLIT_ROOT),
            "agent_common": agent_common,
        }
        AGENTS_DIR.mkdir(parents=True, exist_ok=True)
        for template_path in TEMPLATES_DIR.glob("*.md"):
            if template_path.name == "agent_common.md":
                continue
            rendered = render(template_path, context)
            (AGENTS_DIR / template_path.name).write_text(rendered)
