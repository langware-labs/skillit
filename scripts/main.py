#!/usr/bin/env python3
"""
Skillit - Main Entry Point
Routes prompts to appropriate skill modifiers based on keyword matching.
"""
import json
import re
import sys

from log import skill_log
from notify import send_skill_notification

# =============================================================================
# MODIFIER IMPORTS
# =============================================================================

from modifiers.analyzer import handle_analyze
from modifiers.create_test import handle_create_test
from modifiers.test import handle_test
from memory import create_rule_engine

# =============================================================================
# KEYWORD MAPPINGS
# Order matters - more specific patterns should come first
# =============================================================================

KEYWORD_MAPPINGS = [
    ("skillit:create-test", handle_create_test),
    ("skillit:test", handle_test),
    ("skillit", handle_analyze),
]

# =============================================================================
# MAIN LOGIC
# =============================================================================

def find_matching_modifier(prompt: str):
    """
    Find the first matching modifier for the prompt.
    Returns (handler_function, matched_keyword) or (None, None).

    Matches keywords that are:
    - Standalone (not inside file paths like /path/to/skillit/file.txt)
    - Optionally prefixed with / as a command (e.g., /skillit create test)
    """
    for keyword, handler in KEYWORD_MAPPINGS:
        # Match keyword at start (with optional /), or preceded by whitespace
        # But not inside a path (where it would have / on both sides)
        pattern = r'(?:^/?|(?<=[/\s]))' + re.escape(keyword) + r'(?![/\\])'
        if re.search(pattern, prompt, re.IGNORECASE):
            return handler, keyword

    return None, None


def _evaluate_file_rules(data: dict) -> dict:
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
        "cwd": project_dir,
    }

    # Get transcript if available (for now, empty list)
    # TODO: Load transcript from JSONL if needed
    transcript: list = []

    result = engine.evaluate_rules(hooks_data, transcript)

    # Handle exit code if set
    exit_code = result.pop("_exit_code", None)
    if exit_code == 2:
        skill_log(f"Rule requested exit code 2 (block)")

    # Remove internal metadata for output
    result.pop("_triggered_rules", None)
    result.pop("_chain_requests", None)

    return result


def main():
    skill_log(" skillit ".center(60, "="))
    skill_log("Hook triggered: UserPromptSubmit")

    # Read input from stdin
    try:
        data = json.load(sys.stdin)
        skill_log(f"Input received: {json.dumps(data)}")
    except json.JSONDecodeError as e:
        skill_log(f"ERROR: Invalid JSON input: {e}")
        sys.exit(1)

    prompt = data.get("prompt", "")
    skill_log(f"Prompt: {prompt}")

    # Evaluate file-based rules from .flow/skill_rules/
    file_rules_output = _evaluate_file_rules(data)
    if file_rules_output:
        skill_log(f"File rules triggered: {json.dumps(file_rules_output)}")

    handler, matched_keyword = find_matching_modifier(prompt)
    if handler:
        skill_log(f"Keyword matched: '{matched_keyword}', invoking handler {handler.__name__}")
        # Send notification to FlowPad backend (fire-and-forget)
        send_skill_notification(
            skill_name="skillit",
            matched_keyword=matched_keyword,
            prompt=prompt,
            handler_name=handler.__name__,
            folder_path=data.get("cwd", ""),
        )
        result = handler(prompt, data)

        if result:
            # Merge file rules output
            if file_rules_output:
                result = _merge_hook_outputs(file_rules_output, result)
            skill_log(f"Handler result: {json.dumps(result)}")
            print(json.dumps(result))
        else:
            skill_log("Handler returned no result")
            # Still emit file rules output if triggered
            if file_rules_output:
                print(json.dumps(file_rules_output))
    else:
        skill_log("No keyword matched, passing through unchanged")
        if file_rules_output:
            print(json.dumps(file_rules_output))

    skill_log("Hook completed")
    sys.exit(0)


def _merge_hook_outputs(base: dict, overlay: dict) -> dict:
    """Merge two hook output dicts, combining contexts and respecting blocks.

    Args:
        base: Base output dict (from file rules).
        overlay: Overlay output dict (from handler).

    Returns:
        Merged output dict.
    """
    result = overlay.copy()

    # Merge hookSpecificOutput
    if "hookSpecificOutput" in base:
        if "hookSpecificOutput" not in result:
            result["hookSpecificOutput"] = {}

        base_hso = base["hookSpecificOutput"]
        result_hso = result["hookSpecificOutput"]

        # Combine additionalContext
        if "additionalContext" in base_hso:
            if "additionalContext" in result_hso:
                result_hso["additionalContext"] = (
                    base_hso["additionalContext"] + "\n\n" + result_hso["additionalContext"]
                )
            else:
                result_hso["additionalContext"] = base_hso["additionalContext"]

        # Block takes priority
        if base_hso.get("permissionDecision") == "deny":
            result_hso["permissionDecision"] = "deny"
            if "permissionDecisionReason" in base_hso:
                result_hso["permissionDecisionReason"] = base_hso["permissionDecisionReason"]

    # Decision block takes priority
    if base.get("decision") == "block":
        result["decision"] = "block"
        if "reason" in base:
            result["reason"] = base["reason"]

    return result


if __name__ == "__main__":
    main()
