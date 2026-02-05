"""Settings - load settings from various sources."""

from utils import (
    CLAUDE_HOME,
    CLAUDE_PROJECT,
    HOME,
    load_json,
)


def get_user_settings() -> dict | None:
    """Get ~/.claude/settings.json"""
    return load_json(CLAUDE_HOME / "settings.json")


def get_project_settings() -> dict | None:
    """Get .claude/settings.json"""
    return load_json(CLAUDE_PROJECT / "settings.json")


def get_project_local_settings() -> dict | None:
    """Get .claude/settings.local.json"""
    return load_json(CLAUDE_PROJECT / "settings.local.json")


def get_legacy_settings() -> dict | None:
    """Get ~/.claude.json"""
    return load_json(HOME / ".claude.json")


def get_all_settings() -> dict:
    """Get all settings from all sources."""
    return {
        "user": get_user_settings(),
        "project": get_project_settings(),
        "project_local": get_project_local_settings(),
        "legacy": get_legacy_settings(),
    }
