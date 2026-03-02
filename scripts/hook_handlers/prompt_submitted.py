"""UserPromptSubmit hook handler — keyword routing, subagent instructions, analysis trigger."""

import json
import re

from skillit_events import send_skill_activation
from utils.claude_utils import build_subagent_instructions, get_skill_rules_dir, get_skills_dir
from utils.conf import PLUGIN_DIR
from utils.log import skill_log

from hook_handlers.analysis import start_new_analysis

# =============================================================================
# KEYWORD MAPPINGS
# Order matters - more specific patterns should come first.
# Each entry: (keyword, instructions_file, target_dir_fn, triggers_analysis)
# =============================================================================

KEYWORD_MAPPINGS = [
    ("skillit:create-test", PLUGIN_DIR / "create_test_instructions.md", get_skills_dir, False),
    ("skillit:test", PLUGIN_DIR / "analyze_and_create_activation_rules.md", get_skill_rules_dir, True),
]


def find_matching_keyword(prompt: str):
    """Find the first matching keyword entry for the prompt.

    Returns the matching (keyword, instructions_file, target_dir_fn, triggers_analysis)
    tuple, or None.

    Matches keywords that are:
    - The first word in the prompt (leading whitespace ignored)
    - Optionally prefixed with / as a command (e.g., /skillit:test)
    - Not inside file paths like /path/to/skillit/file.txt
    """
    for entry in KEYWORD_MAPPINGS:
        keyword = entry[0]
        pattern = r'^\s*/?' + re.escape(keyword) + r'(?![/\\])'
        if re.search(pattern, prompt, re.IGNORECASE):
            return entry
    return None


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
    match = find_matching_keyword(prompt)

    if not match:
        skill_log("No keyword matched, passing through unchanged")
        return rules_output or None

    keyword, instructions_file, target_dir_fn, triggers_analysis = match
    cwd = data.get("cwd", "")

    skill_log(f"Keyword matched: '{keyword}'")
    send_skill_activation(
        skill_name="skillit",
        matched_keyword=keyword,
        prompt=prompt,
        handler_name=keyword,
        folder_path=cwd,
    )

    result = build_subagent_instructions(
        instructions_file=instructions_file,
        cwd=cwd,
        target_dir=target_dir_fn(cwd),
    )

    if triggers_analysis:
        _send_analysis_task_created(data)

    if result:
        if rules_output:
            result = _merge_hook_outputs(rules_output, result)
        skill_log(f"Handler result: {json.dumps(result)}")
        return result
    else:
        skill_log("Handler returned no result")
        return rules_output or None
