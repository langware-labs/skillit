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

# =============================================================================
# MODIFIER IMPORTS
# =============================================================================

from modifiers.analyzer import handle_analyze
from modifiers.test import handle_test

# =============================================================================
# KEYWORD MAPPINGS
# Order matters - more specific patterns should come first
# =============================================================================

KEYWORD_MAPPINGS = [
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

    Uses word boundary matching to avoid triggering on keywords
    that appear inside file paths (e.g., /path/to/skillit/file.txt).
    """
    for keyword, handler in KEYWORD_MAPPINGS:
        # Use word boundaries to match standalone keywords, not path components
        pattern = r'(?<![/\\])' + re.escape(keyword) + r'(?![/\\])'
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
