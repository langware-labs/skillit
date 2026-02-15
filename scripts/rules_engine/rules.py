"""Rules evaluation — evaluate file-based rules from .flow/skill_rules/."""

from utils.log import skill_log
from memory import create_rule_engine


def evaluate_rules(data: dict) -> dict:
    """Evaluate file-based rules from .flow/skill_rules/.

    Args:
        data: The hook input data.

    Returns:
        Hook output dict from triggered rules, or empty dict if no triggers.
    """
    project_dir = data.get("cwd")
    engine = create_rule_engine(project_dir=project_dir)

    # Build hooks_data from input
    hooks_data = {
        "hookEvent": data.get("hookEvent") or data.get("hook_event") or data.get("hook_event_name") or "UserPromptSubmit",
        "hookName": data.get("hookName") or data.get("hook_name") or "",
        "prompt": data.get("prompt") or data.get("command") or "",
        "tool_name": data.get("toolName") or data.get("tool_name"),
        "tool_input": data.get("toolInput") or data.get("tool_input"),
        "toolUseID": data.get("toolUseID") or data.get("tool_use_id"),
        "parentToolUseID": data.get("parentToolUseID") or data.get("parent_tool_use_id"),
        "timestamp": data.get("timestamp"),
        "session_id": data.get("session_id", ""),
        "cwd": project_dir,
    }

    # Get transcript if available (for now, empty list)
    # TODO: Load transcript from JSONL if needed
    transcript: list = []

    result = engine.evaluate_rules(hooks_data, transcript)

    # Handle exit code if set
    exit_code = result.pop("_exit_code", None)
    if exit_code == 2:
        skill_log("Rule requested exit code 2 (block)")

    # Remove internal metadata for output
    result.pop("_triggered_rules", None)
    result.pop("_chain_requests", None)

    return result
