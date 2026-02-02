#!/usr/bin/env python3
"""
Skillit - Session Start Handler
Handles the SessionStart hook event from Claude Code.

Called when a new Claude Code session begins.
"""
import json
import sys

from log import skill_log
from session_events import on_session_start
from global_state import plugin_config


def main():
    version = plugin_config.get("version", "unknown")
    banner = f" skillit v{version} "
    skill_log(banner.center(60, "="))
    skill_log("Hook triggered: SessionStart")

    # Read input from stdin
    try:
        data = json.load(sys.stdin)
        skill_log(f"SessionStart input: {json.dumps(data)}")
    except json.JSONDecodeError as e:
        skill_log(f"ERROR: Invalid JSON input: {e}")
        # Continue with empty data - we still want to trigger the event
        data = {}

    # Trigger session start event
    on_session_start(data)

    skill_log("SessionStart hook completed")
    sys.exit(0)


if __name__ == "__main__":
    main()
