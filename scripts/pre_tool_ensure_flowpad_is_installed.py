#!/usr/bin/env python3
"""PreToolUse hook — blocks skillit skill/task calls when flow executable is missing."""
import json
import shutil
import sys


def _is_skillit_call(tool_name, tool_input):
    """Check if this tool call targets a skillit skill, agent, or MCP tool."""
    if tool_name == "Skill":
        return tool_input.get("skill", "").startswith("skillit:")
    if tool_name == "Task":
        return tool_input.get("subagent_type", "").startswith("skillit:")
    if tool_name.startswith("mcp__plugin_skillit_flow_sdk__"):
        return True
    return False


def main():
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        sys.exit(0)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if not _is_skillit_call(tool_name, tool_input):
        sys.exit(0)

    if not shutil.which("flow"):
        sys.stdout.write(json.dumps({
            "decision": "block",
            "reason": "flowpad is not installed (missing: flow). Install with: pip install flowpad"
        }) + "\n")
        sys.stdout.flush()

    sys.exit(0)


if __name__ == "__main__":
    main()
