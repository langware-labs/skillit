#!/usr/bin/env python3
"""
Skillit - Main Entry Point
Routes prompts to appropriate skill modifiers based on keyword matching.
"""
import json
import re
import sys

from global_state import is_within_cooldown, update_invocation_time, COOLDOWN_SECONDS, plugin_config
from log import skill_log
from notify import send_skill_notification

# =============================================================================
# MODIFIER IMPORTS
# =============================================================================

from modifiers.analyzer import handle_analyze
from modifiers.create_test import handle_create_test
from modifiers.test import handle_test

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


def main():
    version = plugin_config.get("version", "unknown")
    banner = f" skillit v{version} "
    skill_log(banner.center(60, "="))
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

    handler, matched_keyword = find_matching_modifier(prompt)
    if handler:
        skill_log(f"Keyword matched: '{matched_keyword}', invoking handler {handler.__name__}")
    # Safety check: prevent recursive activation
    if is_within_cooldown():
        skill_log(f"BLOCKED: Within {COOLDOWN_SECONDS}s cooldown period, skipping to prevent recursion")
        sys.exit(0)
    if handler:
        update_invocation_time()
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
            skill_log(f"Handler result: {json.dumps(result)}")
            print(json.dumps(result))
        else:
            skill_log("Handler returned no result")
    else:
        skill_log("No keyword matched, passing through unchanged")

    skill_log("Hook completed")
    sys.exit(0)


if __name__ == "__main__":
    main()
