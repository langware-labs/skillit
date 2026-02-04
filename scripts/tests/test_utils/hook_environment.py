"""Simple test environment for hook testing."""

import json
import shutil
import subprocess
from pathlib import Path

TEMP_DIR = Path("/tmp/skillit_test")
SKILLIT_ROOT = Path(__file__).resolve().parents[3]


class PromptResult:
    """Result from running a prompt."""

    def __init__(self, returncode: int, stdout: str):
        self.returncode = returncode
        self.stdout = stdout

    def response_contains(self, text: str) -> bool:
        return text.lower() in self.stdout.lower()

    def response_not_contains(self, text: str) -> bool:
        return text.lower() not in self.stdout.lower()


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

    def load_skill(self, skill_path: str) -> None:
        """Copy a skill into the env's .flow/skill_rules folder."""
        skill_src = Path(skill_path).expanduser()
        rules_dir = self.temp_dir / ".flow" / "skill_rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

        skill_name = skill_src.name
        shutil.copytree(skill_src, rules_dir / skill_name)

    def prompt(self, text: str) -> PromptResult:
        """Run claude -p with the prompt, print output, return result."""
        result = subprocess.run(
            ["claude", "-p", text],
            cwd=str(self.temp_dir),
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        return PromptResult(result.returncode, result.stdout)

    def cleanup(self):
        """Remove temp folder."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
