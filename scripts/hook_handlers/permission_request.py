"""PermissionRequest hook handler — auto-allow tools when skillit-creator is active."""

import json

from utils.conf import SKILLIT_HOME
from utils.log import skill_log

ACTIVE_FLAG = SKILLIT_HOME / "creator_active"

ALLOWED_TOOLS = {"Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch", "WebSearch", "Task"}


def handle(data: dict, rules_output: dict) -> dict | None:
    """Handle PermissionRequest — auto-allow tools if skillit-creator is running."""
    tool_name = data.get("tool_name", "")

    if not ACTIVE_FLAG.exists():
        skill_log(f"permission_request: no active creator, passing through for {tool_name}")
        return rules_output or None

    if tool_name not in ALLOWED_TOOLS:
        skill_log(f"permission_request: tool {tool_name} not in allowed list, passing through")
        return rules_output or None

    skill_log(f"permission_request: AUTO-ALLOWING {tool_name} for active skillit-creator")
    return {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {
                "behavior": "allow"
            }
        }
    }
