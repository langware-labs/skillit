"""Test trigger script for unit testing.

This trigger activates when 'test_keyword' is found in the input.
It demonstrates different action types based on hook event type.
"""

import json
import sys


def get_text_to_check(hooks_data: dict) -> str:
    """Extract the relevant text to check based on hook event type."""
    hook_event = hooks_data.get("hookEvent", hooks_data.get("hook_event_name", ""))

    if hook_event == "UserPromptSubmit":
        return hooks_data.get("prompt", "")
    elif hook_event in ("PreToolUse", "PostToolUse"):
        tool_input = hooks_data.get("tool_input", {})
        # Check command for Bash, file_path for file operations
        return str(tool_input.get("command", "")) + str(tool_input.get("file_path", ""))
    elif hook_event == "SessionStart":
        return hooks_data.get("source", "")
    elif hook_event == "Notification":
        return hooks_data.get("message", "")
    elif hook_event == "SubagentStop":
        return hooks_data.get("agent_type", "")
    else:
        # For Stop, PreCompact, PermissionRequest - check raw data
        return str(hooks_data)


def build_result(hooks_data: dict, text_to_check: str) -> dict:
    """Build the trigger result based on input analysis."""
    hook_event = hooks_data.get("hookEvent", hooks_data.get("hook_event_name", ""))

    if "test_keyword" not in text_to_check.lower():
        return {"trigger": False}

    # Check for dangerous command pattern (for block action testing)
    if hook_event == "PreToolUse" and "dangerous" in text_to_check.lower():
        return {
            "trigger": True,
            "reason": f"Dangerous command detected in {hook_event}",
            "entry_id": None,
            "actions": [
                {
                    "type": "block",
                    "reason": "Blocked dangerous command containing test_keyword",
                }
            ],
        }

    # Default: add_context action
    return {
        "trigger": True,
        "reason": f"Found test_keyword in {hook_event}",
        "entry_id": None,
        "actions": [
            {
                "type": "add_context",
                "content": f"Test context triggered by {hook_event}: test_keyword found",
            }
        ],
    }


def main():
    """Main entry point for trigger execution."""
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        result = {"trigger": False, "error": "Invalid JSON input"}
        print(f"<trigger-result>{json.dumps(result)}</trigger-result>")
        return

    hooks_data = data.get("hooks_data", {})
    # transcript = data.get("transcript", [])  # Available if needed

    text_to_check = get_text_to_check(hooks_data)
    result = build_result(hooks_data, text_to_check)

    print(f"<trigger-result>{json.dumps(result)}</trigger-result>")


if __name__ == "__main__":
    main()
