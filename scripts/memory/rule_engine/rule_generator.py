"""LLM-based rule generator for creating trigger.py and rule.md files."""

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memory.types.claude import HookData


@dataclass
class GeneratedRule:
    """A generated rule with its path."""

    rule_path: Path
    name: str


RULE_GENERATION_PROMPT = '''You are generating a Claude Code hook rule.

Given the following hook data and transcript, generate a rule that:
1. Triggers when similar conditions are met
2. Performs the specified action

## Hook Data
```json
{hook_data_json}
```

## Transcript
```json
{transcript_json}
```

## Rule Requirements
- Name: {name}
- Action Type: {action_type}
- Action Content: {action_content}

Generate two files:

### trigger.py
Create a Python trigger script that:
- Has an `evaluate(hooks_data: dict, transcript: list)` function
- Returns `Action(type="{action_type}", params={action_params})` when triggered
- Returns `None` when not triggered
- Uses the hook data pattern to determine when to trigger

The trigger should detect patterns similar to the provided hook data.

### rule.md
Create a markdown file with YAML frontmatter containing:
- name: {name}
- description: A brief description of what this rule does

---

Respond ONLY with valid JSON in this exact format:
```json
{{
  "trigger_py": "# Python code here...",
  "rule_md": "---\\nname: {name}\\n..."
}}
```
'''


def _build_action_params(action_type: str, action_content: str) -> dict[str, Any]:
    """Build action params dict based on action type."""
    if action_type == "add_context":
        return {"content": action_content}
    elif action_type == "block":
        return {"reason": action_content}
    elif action_type == "allow":
        return {"reason": action_content}
    elif action_type == "modify_input":
        return {"updates": action_content}
    else:
        return {"content": action_content}


def _hook_data_to_dict(hook_data: HookData | dict) -> dict[str, Any]:
    """Convert HookData to dict if needed.

    Uses camelCase format consistent with main.py.
    """
    if isinstance(hook_data, dict):
        return hook_data
    # Convert dataclass to dict using camelCase (consistent with main.py)
    return {
        "hookEvent": hook_data.hook_event_name,
        "session_id": hook_data.session_id,
        "tool_name": hook_data.tool_name,
        "tool_input": hook_data.tool_input,
        "tool_response": hook_data.tool_response,
        "prompt": hook_data.prompt,
        "message": hook_data.message,
        "cwd": hook_data.cwd,
    }


def gen_rule(
    hooks_data: HookData | dict,
    transcript: list[dict],
    name: str,
    output_dir: Path | str | None = None,
    action_type: str = "add_context",
    action_content: str = "",
) -> GeneratedRule:
    """Generate a rule using Claude LLM.

    Args:
        hooks_data: Hook data that exemplifies when the rule should trigger.
        transcript: Conversation transcript for context.
        name: Rule name (used for folder name).
        output_dir: Directory to create the rule in. If None, uses temp directory.
        action_type: Action type ("add_context", "block", etc.).
        action_content: Content for the action (context text or reason).

    Returns:
        GeneratedRule with rule_path pointing to generated folder.
    """
    hooks_data_dict = _hook_data_to_dict(hooks_data)
    action_params = _build_action_params(action_type, action_content)

    # Build the prompt
    prompt = RULE_GENERATION_PROMPT.format(
        hook_data_json=json.dumps(hooks_data_dict, indent=2),
        transcript_json=json.dumps(transcript[:5] if transcript else [], indent=2),
        name=name,
        action_type=action_type,
        action_content=action_content,
        action_params=json.dumps(action_params),
    )

    # Call Claude CLI to generate the rule
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI failed: {result.stderr}")

    # Parse the response - it may be wrapped in JSON or just text
    response_text = result.stdout.strip()

    # Try to extract JSON from the response
    try:
        # First try direct JSON parse
        response_data = json.loads(response_text)
        # If it's claude's JSON output format, extract the result
        if "result" in response_data:
            response_text = response_data["result"]
            # Try to find JSON in the result text
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            response_data = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to find JSON block in the response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
            response_data = json.loads(json_text)
        elif "{" in response_text:
            # Try to find raw JSON
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_text = response_text[json_start:json_end]
            response_data = json.loads(json_text)
        else:
            raise ValueError(f"Could not parse LLM response as JSON: {response_text[:500]}")

    # Create rule directory
    if output_dir:
        rule_dir = Path(output_dir) / name
        rule_dir.mkdir(parents=True, exist_ok=True)
    else:
        rule_dir = Path(tempfile.mkdtemp(prefix=f"rule_{name}_"))

    # Write trigger.py
    trigger_code = response_data.get("trigger_py", "")
    if not trigger_code:
        raise ValueError("LLM did not generate trigger_py")
    (rule_dir / "trigger.py").write_text(trigger_code)

    # Write rule.md
    rule_md = response_data.get("rule_md", "")
    if not rule_md:
        raise ValueError("LLM did not generate rule_md")
    (rule_dir / "rule.md").write_text(rule_md)

    return GeneratedRule(rule_path=rule_dir, name=name)
