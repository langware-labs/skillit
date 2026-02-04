"""Simple test environment for hook testing."""

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

TEMP_DIR = Path("/tmp/skillit_test")
SKILLIT_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class GeneratedRule:
    """A generated rule with its path."""
    rule_path: Path
    name: str


def gen_rule(
    name: str,
    trigger_keywords: list[str],
    action_type: str,
    action_content: str,
) -> GeneratedRule:
    """Generate a rule folder with trigger.py and rule.md.

    Args:
        name: Rule name (used for folder name)
        trigger_keywords: Keywords that trigger the rule
        action_type: Action type ("add_context", "block", etc.)
        action_content: Content for the action (context text or reason)

    Returns:
        GeneratedRule with rule_path pointing to generated folder
    """
    rule_dir = Path(tempfile.mkdtemp(prefix=f"rule_{name}_"))

    # Generate trigger.py
    keywords_check = " or ".join(
        f'_contains("{kw}", prompt)' for kw in trigger_keywords
    )

    trigger_code = f'''"""Generated trigger for {name}."""

from memory.rule_engine.trigger_executor import Action


def _contains(substring: str, text: str) -> bool:
    if not text or not substring:
        return False
    return substring.lower() in text.lower()


def evaluate(hooks_data: dict, transcript: list) -> Action | list[Action] | None:
    prompt = hooks_data.get("prompt", "") or hooks_data.get("command", "")

    if {keywords_check}:
        return Action(
            type="{action_type}",
            params={{"content": """{action_content}"""}}
        )

    return None
'''
    (rule_dir / "trigger.py").write_text(trigger_code)

    # Generate rule.md
    rule_md = f'''---
name: {name}
description: Generated rule for testing
---

## Triggers

Keywords: {", ".join(trigger_keywords)}

## Actions

- `{action_type}`: {action_content[:50]}...
'''
    (rule_dir / "rule.md").write_text(rule_md)

    return GeneratedRule(rule_path=rule_dir, name=name)


class PromptResult:
    """Result from running a prompt."""

    def __init__(self, returncode: int, stdout: str, skill_log: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.skill_log = skill_log

    def response_contains(self, text: str) -> bool:
        return text.lower() in self.stdout.lower()

    def response_not_contains(self, text: str) -> bool:
        return text.lower() not in self.stdout.lower()

    def hook_output_contains(self, text: str) -> bool:
        """Check if the hook output (skill.log) contains the text."""
        return text.lower() in self.skill_log.lower()


class HookTestEnvironment:
    """Self-contained test environment with project-level hooks."""

    def __init__(self):
        self.temp_dir = TEMP_DIR
        self._setup()

    def _setup(self):
        """Create temp folder with scripts and project hooks config."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

        self.temp_dir.mkdir(parents=True)

        # Copy scripts
        shutil.copytree(
            SKILLIT_ROOT / "scripts",
            self.temp_dir / "scripts",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
        )

        # Create .claude/settings.json with project-level hooks
        claude_dir = self.temp_dir / ".claude"
        claude_dir.mkdir()

        settings = {
            "hooks": {
                "UserPromptSubmit": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 ./scripts/main.py"
                            }
                        ]
                    }
                ]
            }
        }
        (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2))

    def load_rule(self, rule_path: str) -> None:
        """Copy a rule into the env's .flow/skill_rules folder."""
        rule_src = Path(rule_path).expanduser()
        rules_dir = self.temp_dir / ".flow" / "skill_rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

        rule_name = rule_src.name
        shutil.copytree(rule_src, rules_dir / rule_name)

    def prompt(self, text: str) -> PromptResult:
        """Run claude -p with the prompt, print output, return result."""
        # Clear skill.log before running
        skill_log_path = self.temp_dir / "skill.log"
        if skill_log_path.exists():
            skill_log_path.unlink()

        result = subprocess.run(
            ["claude", "-p", text],
            cwd=str(self.temp_dir),
            capture_output=True,
            text=True,
        )
        print(result.stdout)

        # Read skill.log
        skill_log = ""
        if skill_log_path.exists():
            skill_log = skill_log_path.read_text()

        return PromptResult(result.returncode, result.stdout, skill_log)

    def cleanup(self):
        """Remove temp folder."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
