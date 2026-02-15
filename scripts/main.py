#!/usr/bin/env python3
"""
Skillit - Main Entry Point
Thin dispatcher: reads stdin, evaluates rules, routes to hook handlers.
"""
import json
import os
import sys
from pathlib import Path

from hook_handlers import prompt_submitted, session_start
from utils.log import skill_log
from network.notify import send_skill_event
from rules_engine.rules import evaluate_rules


def _emit_hook_output(output: dict) -> None:
    """Emit hook output to stdout in the format Claude Code expects.

    For context-only output (additionalContext with no blocking decision),
    emits plain text to stdout. Claude Code adds plain text stdout directly
    to Claude's context and shows it in the transcript, making it more
    prominent than JSON additionalContext which is "added more discretely".

    For blocking or structured output, emits JSON.

    Args:
        output: Hook output dict from rule engine or handler.
    """
    if not output:
        return

    hso = output.get("hookSpecificOutput", {})
    additional_context = hso.get("additionalContext")
    is_blocking = (
        output.get("decision") == "block"
        or hso.get("permissionDecision") == "deny"
    )

    if is_blocking or not additional_context:
        # Blocking or structured output: emit as JSON
        json_str = json.dumps(output)
        skill_log(f"Emitting JSON output ({len(json_str)} chars): {json_str[:300]}...")
        sys.stdout.write(json_str + "\n")
    else:
        # Context-only: emit as plain text (more prominent in Claude's view)
        skill_log(f"Emitting plain text context ({len(additional_context)} chars): {additional_context[:200]}...")
        sys.stdout.write(additional_context + "\n")
    sys.stdout.flush()


def _dump_stdin(raw: str) -> None:
    """Write raw stdin content to the path specified by SKILLIT_DUMP_STDIN."""
    dump_path = os.environ.get("SKILLIT_DUMP_STDIN")
    if not dump_path:
        return
    try:
        path = Path(dump_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(raw)
            f.write("\n")
        skill_log(f"Dumped stdin to {dump_path}")
    except Exception as e:
        skill_log(f"ERROR: Failed to dump stdin: {e}")


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


def main():
    skill_log(" skillit ".center(60, "="))

    # Read input from stdin
    try:
        raw = sys.stdin.read()
        _dump_stdin(raw)
        if not raw or not raw.strip():
          ERROR_MSG = "ERROR: No input received on stdin"
          skill_log(ERROR_MSG)
          sys.stdout.write(ERROR_MSG + "\n")
          sys.exit(1)
        data = json.loads(raw)
        skill_log(f"Input received: {json.dumps(data)}")
    except json.JSONDecodeError as e:
        skill_log(f"ERROR: Invalid JSON input: {e}")
        sys.exit(1)

    # Determine hook event from stdin data
    hookEvent = data.get("hook_event_name") or data.get("hookEvent") or "UserPromptSubmit"
    data["hookEvent"] = hookEvent  # normalize for downstream

    skill_log(f"Hook triggered: {hookEvent}, path: {__file__}, pid: {os.getpid()}")
    skill_log("Working directory: " + str(os.getcwd()))
    event_context = {
        "hookEvent": hookEvent,
        "scriptPath": __file__,
        "pid": os.getpid(),
        "cwd": os.getcwd(),
    }
    send_skill_event("skillit called", event_context)

    prompt = data.get("prompt", "")
    skill_log(f"Prompt: {prompt}")

    # Evaluate file-based rules from .flow/skill_rules/
    rules_output = evaluate_rules(data)
    if rules_output:
        skill_log(f"File rules triggered: {json.dumps(rules_output)}")

    # Dispatch to handler
    if hookEvent == "UserPromptSubmit":
        output = prompt_submitted.handle(data, rules_output)
    elif hookEvent == "SessionStart":
        output = session_start.handle(data, rules_output)
    else:
        output = rules_output or None

    _emit_hook_output(output)

    skill_log("Hook completed")
    sys.exit(0)


if __name__ == "__main__":
    main()
