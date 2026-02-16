"""UserPromptSubmit hook handler — keyword routing, modifier invocation, analysis trigger."""

import json
import re

from hook_handlers.analysis import start_new_analysis
from utils.log import skill_log
from modifiers.analyze_and_create_activation_rules import handle_analyze
from modifiers.create_test import handle_create_test
from modifiers.test import handle_test
from network.notify import send_skill_activation

# =============================================================================
# KEYWORD MAPPINGS
# Order matters - more specific patterns should come first
# =============================================================================

KEYWORD_MAPPINGS = [
    ("skillit:create-test", handle_create_test),
    ("skillit:test", handle_test),
    ("skillit", handle_analyze),
]


def find_matching_modifier(prompt: str):
    """
    Find the first matching modifier for the prompt.
    Returns (handler_function, matched_keyword) or (None, None).

    Matches keywords that are:
    - The first word in the prompt (leading whitespace ignored)
    - Optionally prefixed with / as a command (e.g., /skillit create test)
    - Not inside file paths like /path/to/skillit/file.txt
    """
    for keyword, handler in KEYWORD_MAPPINGS:
        # Match keyword only at the start of the prompt (ignoring leading whitespace),
        # optionally prefixed with /
        pattern = r'^\s*/?'+ re.escape(keyword) + r'(?![/\\])'
        if re.search(pattern, prompt, re.IGNORECASE):
            return handler, keyword

    return None, None


def _send_analysis_task_created(data: dict) -> None:
    """Create a TaskResource and send task_created event to FlowPad."""
    session_id = data.get("session_id", "")
    if not session_id:
        skill_log("No session_id in hook data, skipping task_created event")
        return
    start_new_analysis(session_id)


def handle(data: dict, rules_output: dict) -> dict | None:
    """Handle UserPromptSubmit — keyword routing + rules merge."""
    from main import _merge_hook_outputs

    prompt = data.get("prompt", "")
    handler, matched_keyword = find_matching_modifier(prompt)

    if not handler:
        skill_log("No keyword matched, passing through unchanged")
        return rules_output or None

    skill_log(f"Keyword matched: '{matched_keyword}', invoking handler {handler.__name__}")
    send_skill_activation(
        skill_name="skillit",
        matched_keyword=matched_keyword,
        prompt=prompt,
        handler_name=handler.__name__,
        folder_path=data.get("cwd", ""),
    )
    result = handler(prompt, data)

    # Send task_created for analysis handler
    if handler is handle_analyze:
        _send_analysis_task_created(data)

    if result:
        if rules_output:
            result = _merge_hook_outputs(rules_output, result)
        skill_log(f"Handler result: {json.dumps(result)}")
        return result
    else:
        skill_log("Handler returned no result")
        return rules_output or None
