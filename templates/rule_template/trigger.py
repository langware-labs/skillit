"""Trigger template - define evaluate() function returning Action.

This module provides a template for creating activation rule triggers.
The evaluate() function is called by the rule engine and should return
Action(s) when the rule should trigger, or None when it should not.

Available Action types:
- Action(type="add_context", params={"content": "..."})
- Action(type="block", params={"reason": "..."})
- Action(type="allow", params={"reason": "..."})
- Action(type="modify_input", params={"updates": {...}})
- Action(type="stderr", params={"message": "..."})
- Action(type="chain_rule", params={"rule_name": "..."})
"""

from memory.rule_engine.trigger_executor import Action


def evaluate(hooks_data: dict, transcript: list) -> Action | list[Action] | None:
    """Evaluate hook data and return Action(s) if triggered.

    Args:
        hooks_data: Current hook event data containing:
            - hook_event_name: "PreToolUse", "PostToolUse", "UserPromptSubmit", etc.
            - tool_name: Tool name (for tool events)
            - tool_input: Tool parameters (for tool events)
            - tool_response: Tool response (for PostToolUse only)
            - prompt: User prompt (for UserPromptSubmit)
        transcript: Conversation history (optional use)

    Returns:
        Action, list of Actions, or None if no trigger
    """
    # Get hook event type
    hook_event = hooks_data.get("hook_event_name", "")

    # Extract relevant text based on event type
    if hook_event == "UserPromptSubmit":
        text = hooks_data.get("prompt", "")
    elif hook_event in ("PreToolUse", "PostToolUse"):
        tool_input = hooks_data.get("tool_input", {})
        text = tool_input.get("command", "") or tool_input.get("file_path", "")
    else:
        text = ""

    # Check trigger condition
    # TODO: Replace with your actual condition
    if "your_keyword" not in text.lower():
        return None  # No trigger

    # Return action(s) when triggered
    return Action(
        type="add_context",
        params={"content": "Your context message here"},
    )
