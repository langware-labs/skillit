"""Simple test environment for hook testing."""

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# Re-export gen_rule and GeneratedRule from rule_generator
from memory.rule_engine.rule_generator import GeneratedRule, gen_rule
from memory.rule_engine.engine import RulesPackage

TEMP_DIR = Path("/tmp/skillit_test")
SKILLIT_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class SampleTranscript:
    """Sample transcript with path and entries."""

    path: Path
    entries: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls, transcript_path: Path) -> "SampleTranscript":
        """Load transcript from a JSONL file."""
        entries = []
        if transcript_path.exists():
            with open(transcript_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        return cls(path=transcript_path, entries=entries)

    def __iter__(self):
        """Allow iteration over entries."""
        return iter(self.entries)

    def __len__(self):
        """Return number of entries."""
        return len(self.entries)


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

    @property
    def path(self) -> Path:
        """Return the environment's root path."""
        return self.temp_dir

    @property
    def project_rules(self) -> RulesPackage:
        """Return the project rules package."""
        rules_path = self.temp_dir / ".flow" / "skill_rules"
        rules_path.mkdir(parents=True, exist_ok=True)
        return RulesPackage(path=rules_path, source="project")

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
