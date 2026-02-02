#!/usr/bin/env python3
"""
Skillit - Main Entry Point
Routes prompts to appropriate skill modifiers based on keyword matching.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

from global_state import is_within_cooldown, update_invocation_time, COOLDOWN_SECONDS, plugin_config
from log import skill_log
from notify import send_skill_notification

# =============================================================================
# MODIFIER IMPORTS
# =============================================================================

from modifiers.analyzer import handle_analyze
from modifiers.test import handle_test
from memory.hooks import HookEvent, Memory
from memory.records import HookResponse

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


def _load_test_skills() -> list:
    skills = []
    skills_dir = Path(__file__).resolve().parent / "tests" / "test_skills"
    if not skills_dir.exists():
        return skills

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "skill.py"
        if not skill_file.exists():
            continue
        module_name = f"test_skill_{skill_dir.name}"
        spec = importlib.util.spec_from_file_location(module_name, skill_file)
        if not spec or not spec.loader:
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            skill_log(f"ERROR: Failed to load skill {skill_dir.name}: {exc}")
            continue
        build_skill = getattr(module, "build_skill", None)
        if not callable(build_skill):
            skill_log(f"ERROR: Missing build_skill() in {skill_file}")
            continue
        try:
            skills.append(build_skill())
        except Exception as exc:
            skill_log(f"ERROR: Failed to build skill {skill_dir.name}: {exc}")
    return skills


def _build_hook_event(data: dict) -> HookEvent:
    return HookEvent(
        hook_event=str(data.get("hookEvent") or data.get("hook_event") or data.get("event") or data.get("type") or ""),
        hook_name=str(data.get("hookName") or data.get("hook_name") or data.get("hookEvent") or ""),
        command=data.get("command") or data.get("prompt") or data.get("message") or data.get("input"),
        tool_use_id=data.get("toolUseID") or data.get("tool_use_id"),
        parent_tool_use_id=data.get("parentToolUseID") or data.get("parent_tool_use_id"),
        timestamp=data.get("timestamp"),
        raw=data,
    )


def _maybe_emit_memory_response(response: HookResponse, data: dict) -> None:
    if not response.results and not response.notes:
        return
    output = data.copy()
    output["memory"] = response.to_dict()
    print(json.dumps(output))


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

    memory = Memory(skills=_load_test_skills())
    hook_event = _build_hook_event(data)
    memory_response = memory.process_hook(hook_event)

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
            if memory_response.results or memory_response.notes:
                result["memory"] = memory_response.to_dict()
            skill_log(f"Handler result: {json.dumps(result)}")
            print(json.dumps(result))
        else:
            skill_log("Handler returned no result")
    else:
        skill_log("No keyword matched, passing through unchanged")
        _maybe_emit_memory_response(memory_response, data)

    skill_log("Hook completed")
    sys.exit(0)


if __name__ == "__main__":
    main()
