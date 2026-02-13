#!/usr/bin/env python3
"""
Skillit - Main Entry Point
Routes prompts to appropriate skill modifiers based on keyword matching.
"""
import json
import os
import re
import sys
from pathlib import Path

from conf import get_session_dir, get_session_output_dir
from log import skill_log
from memory import create_rule_engine
from modifiers.analyze_and_create_activation_rules import handle_analyze
from modifiers.create_test import handle_create_test
from modifiers.test import handle_test
from fs_store import SyncOperation
from notify import send_skill_activation, send_skill_event, send_task_sync
from task_resource import TaskResource, TaskStatus, TaskType

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


def _send_analysis_task_created(data: dict) -> None:
    """Create a TaskResource and send task_created event to FlowPad."""
    session_id = data.get("session_id", "")
    if not session_id:
        skill_log("No session_id in hook data, skipping task_created event")
        return

    output_dir = get_session_output_dir(session_id)
    task = TaskResource(
        id=f"analysis-{session_id}",
        title="Analyzing session",
        status=TaskStatus.IN_PROGRESS,
        task_type=TaskType.ANALYSIS,
        tags=["analysis", "skillit"],
        metadata={
            "session_id": session_id,
            "output_dir": str(output_dir),
            "analysisPath": str(output_dir / "analysis.md"),
            "analysisJsonPath": str(output_dir / "analysis.json"),
        },
    )
    task.save_to(get_session_dir(session_id))
    send_task_sync(SyncOperation.CREATE, task.to_dict())


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
    file_rules_output = _evaluate_file_rules(data)
    if file_rules_output:
        skill_log(f"File rules triggered: {json.dumps(file_rules_output)}")

    # Keyword matching only applies to UserPromptSubmit
    if hookEvent == "UserPromptSubmit":
        handler, matched_keyword = find_matching_modifier(prompt)
        if handler:
            skill_log(f"Keyword matched: '{matched_keyword}', invoking handler {handler.__name__}")
            # Send notification to FlowPad backend (fire-and-forget)
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
                # Merge file rules output
                if file_rules_output:
                    result = _merge_hook_outputs(file_rules_output, result)
                skill_log(f"Handler result: {json.dumps(result)}")
                _emit_hook_output(result)
            else:
                skill_log("Handler returned no result")
                # Still emit file rules output if triggered
                if file_rules_output:
                    _emit_hook_output(file_rules_output)
        else:
            skill_log("No keyword matched, passing through unchanged")
            if file_rules_output:
                _emit_hook_output(file_rules_output)
    else:
        # Non-UserPromptSubmit events: just emit file rules output
        if file_rules_output:
            _emit_hook_output(file_rules_output)

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
