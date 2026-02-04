"""Execute trigger.py subprocess and parse results."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from log import skill_log


@dataclass
class Action:
    """Represents an action to be executed by the action executor."""

    type: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, **self.params}


@dataclass
class TriggerResult:
    """Result from executing a trigger.py script."""

    trigger: bool = False
    reason: str = ""
    entry_id: str | None = None
    actions: list[Action] = field(default_factory=list)
    rule_name: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger": self.trigger,
            "reason": self.reason,
            "entry_id": self.entry_id,
            "actions": [a.to_dict() for a in self.actions],
            "rule_name": self.rule_name,
            "error": self.error,
        }


def execute_trigger(
    rule_path: Path,
    hooks_data: dict[str, Any],
    transcript: list[dict[str, Any]],
    timeout: float = 5.0,
) -> TriggerResult:
    """Execute a trigger.py script and parse its output.

    Args:
        rule_path: Path to the rule directory containing trigger.py.
        hooks_data: Current hook event data.
        transcript: List of parsed transcript entries.
        timeout: Maximum execution time in seconds.

    Returns:
        TriggerResult with parsed output or error information.
    """
    trigger_file = rule_path / "trigger.py"
    rule_name = rule_path.name

    if not trigger_file.exists():
        return TriggerResult(
            rule_name=rule_name,
            error=f"trigger.py not found at {trigger_file}",
        )

    # Prepare input data
    input_data = {
        "hooks_data": hooks_data,
        "transcript": transcript,
    }

    try:
        # Run trigger.py as subprocess
        result = subprocess.run(
            [sys.executable, str(trigger_file)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(rule_path),
        )

        # Parse output
        stdout = result.stdout
        stderr = result.stderr

        if stderr:
            skill_log(f"[{rule_name}] stderr: {stderr}")

        # Check for non-zero exit (but not exit 2, which is a valid blocking signal)
        if result.returncode != 0 and result.returncode != 2:
            return TriggerResult(
                rule_name=rule_name,
                error=f"trigger.py exited with code {result.returncode}: {stderr}",
            )

        # Handle exit code 2 as a blocking signal
        if result.returncode == 2:
            return TriggerResult(
                trigger=True,
                rule_name=rule_name,
                reason=stderr or "Blocked by trigger (exit code 2)",
                actions=[Action(type="block", params={"reason": stderr or "Blocked by trigger"})],
            )

        # Parse <trigger-result> tags
        return _parse_trigger_output(stdout, rule_name)

    except subprocess.TimeoutExpired:
        return TriggerResult(
            rule_name=rule_name,
            error=f"trigger.py timed out after {timeout}s",
        )
    except json.JSONDecodeError as e:
        return TriggerResult(
            rule_name=rule_name,
            error=f"Invalid JSON in trigger.py output: {e}",
        )
    except Exception as e:
        return TriggerResult(
            rule_name=rule_name,
            error=f"Error executing trigger.py: {e}",
        )


def _parse_trigger_output(stdout: str, rule_name: str) -> TriggerResult:
    """Parse the <trigger-result> output from trigger.py.

    Args:
        stdout: The stdout from the trigger.py subprocess.
        rule_name: Name of the rule for error reporting.

    Returns:
        Parsed TriggerResult.
    """
    # Extract content between <trigger-result> tags
    pattern = r"<trigger-result>\s*(.*?)\s*</trigger-result>"
    match = re.search(pattern, stdout, re.DOTALL)

    if not match:
        # No trigger-result tags found, treat as no trigger
        return TriggerResult(rule_name=rule_name, trigger=False)

    json_str = match.group(1).strip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return TriggerResult(
            rule_name=rule_name,
            error=f"Invalid JSON in <trigger-result>: {e}",
        )

    # Parse actions
    actions: list[Action] = []
    for action_data in data.get("actions", []):
        if isinstance(action_data, dict):
            action_type = action_data.pop("type", "unknown")
            actions.append(Action(type=action_type, params=action_data))

    return TriggerResult(
        trigger=bool(data.get("trigger", False)),
        reason=str(data.get("reason", "")),
        entry_id=data.get("entry_id"),
        actions=actions,
        rule_name=rule_name,
    )


def execute_all_triggers(
    rules: list[dict[str, Any]],
    hooks_data: dict[str, Any],
    transcript: list[dict[str, Any]],
    timeout: float = 5.0,
) -> list[TriggerResult]:
    """Execute all triggers and collect results.

    Args:
        rules: List of rule metadata dicts from discover_rules().
        hooks_data: Current hook event data.
        transcript: List of parsed transcript entries.
        timeout: Maximum execution time per trigger.

    Returns:
        List of TriggerResult objects for rules that triggered (trigger=True).
    """
    results: list[TriggerResult] = []

    for rule in rules:
        rule_path = rule.get("path")
        if not rule_path:
            continue

        result = execute_trigger(
            rule_path=Path(rule_path),
            hooks_data=hooks_data,
            transcript=transcript,
            timeout=timeout,
        )

        if result.error:
            skill_log(f"[{result.rule_name}] Error: {result.error}")
        elif result.trigger:
            skill_log(f"[{result.rule_name}] Triggered: {result.reason}")
            results.append(result)

    return results
