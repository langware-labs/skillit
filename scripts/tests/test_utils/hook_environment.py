"""Simple test environment for hook testing."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# Re-export gen_rule and GeneratedRule from rule_generator
from memory.rule_engine.rule_generator import GeneratedRule, gen_rule
from memory.rule_engine.engine import RulesPackage, RuleEngine

TEMP_DIR = Path(tempfile.gettempdir()) / "skillit_test"
SKILLIT_ROOT = Path(__file__).resolve().parents[3]


def open_terminal(cwd: str | Path, command: str | None = None) -> None:
    """Open a visible terminal window at the given directory.

    Args:
        cwd: Directory to open the terminal in.
        command: Optional command to run in the new terminal.
    """
    cwd = str(cwd)

    if sys.platform == "darwin":
        if command:
            script = (
                'tell application "Terminal"\n'
                f'    do script "cd {cwd} && {command}"\n'
                '    activate\n'
                'end tell'
            )
        else:
            script = (
                'tell application "Terminal"\n'
                f'    do script "cd {cwd}"\n'
                '    activate\n'
                'end tell'
            )
        subprocess.run(["osascript", "-e", script])
    elif sys.platform == "win32":
        if command:
            subprocess.Popen(["cmd", "/c", "start", "cmd", "/K", f"cd /d {cwd} && {command}"])
        else:
            subprocess.Popen(["cmd", "/c", "start", "cmd", "/K", f"cd /d {cwd}"])
    else:
        shell_cmd = f"cd {cwd} && {command}; exec $SHELL" if command else f"cd {cwd} && $SHELL"
        for term in ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]:
            try:
                if term == "gnome-terminal":
                    if command:
                        subprocess.Popen([term, "--working-directory", cwd, "--", "bash", "-c", shell_cmd])
                    else:
                        subprocess.Popen([term, "--working-directory", cwd])
                elif term == "konsole":
                    if command:
                        subprocess.Popen([term, "--workdir", cwd, "-e", "bash", "-c", shell_cmd])
                    else:
                        subprocess.Popen([term, "--workdir", cwd])
                else:
                    subprocess.Popen([term, "-e", f"cd {cwd} && $SHELL"])
                return
            except FileNotFoundError:
                continue
        raise RuntimeError("No supported terminal emulator found")


@dataclass
class ClaudeTranscript:
    """Sample transcript with path and entries."""

    path: Path
    entries: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls, transcript_path: Path) -> "ClaudeTranscript":
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

    @property
    def rule_engine(self) -> RuleEngine:
        """Return RuleEngine for this environment."""
        return RuleEngine(project_dir=str(self.temp_dir))

    def _setup(self):
        """Create a clean temp folder."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

        self.temp_dir.mkdir(parents=True)

    @staticmethod
    def _read_plugin_meta() -> tuple[str, str, str]:
        """Read plugin name, marketplace name, and version from source."""
        plugin_meta = json.loads(
            (SKILLIT_ROOT / ".claude-plugin" / "plugin.json").read_text()
        )
        marketplace_meta = json.loads(
            (SKILLIT_ROOT / ".claude-plugin" / "marketplace.json").read_text()
        )
        return plugin_meta["name"], marketplace_meta["name"], plugin_meta["version"]

    def install_plugin(self) -> None:
        """Build templates and install the skillit plugin at project scope.

        Renders templates (so agents carry the current version), ensures the
        marketplace is registered, then installs with ``--scope project``.
        """
        from plugin_manager import SkillitPluginManager
        SkillitPluginManager().build()

        plugin_name, marketplace_name, _ = self._read_plugin_meta()
        plugin_ref = f"{plugin_name}@{marketplace_name}"

        # Ensure marketplace points at the local repo
        subprocess.run(
            ["claude", "plugin", "marketplace", "remove", marketplace_name],
            capture_output=True,
        )
        # Use relative path with ./ prefix for cross-platform compatibility
        # The marketplace add command expects: owner/repo, https://..., or ./path
        rel_path = os.path.relpath(SKILLIT_ROOT, os.getcwd())
        local_path = f"./{rel_path.replace(os.sep, '/')}"
        subprocess.run(
            ["claude", "plugin", "marketplace", "add", local_path],
            check=True,
        )

        # Install at project scope (writes into <temp_dir>/.claude/settings.json)
        subprocess.run(
            ["claude", "plugin", "install", plugin_ref, "--scope", "project"],
            cwd=str(self.temp_dir),
            check=True,
        )

        # Write explicit hooks into settings.json so they fire during claude -p
        plugin_root = self._plugin_cache_dir()
        # Use forward slashes for cross-platform JSON compatibility
        plugin_root_str = plugin_root.as_posix()
        hooks_json_path = plugin_root / "hooks" / "hooks.json"
        if hooks_json_path.exists():
            hooks_config = json.loads(hooks_json_path.read_text())
            # Resolve plugin root placeholders to the actual cache path
            raw = json.dumps(hooks_config["hooks"])
            raw = raw.replace("%CLAUDE_PLUGIN_ROOT%", plugin_root_str)
            raw = raw.replace("$CLAUDE_PLUGIN_ROOT", plugin_root_str)
            resolved_hooks = json.loads(raw)
        else:
            resolved_hooks = {
                "UserPromptSubmit": [{
                    "hooks": [{
                        "type": "command",
                        "command": f"python {plugin_root_str}/scripts/main.py"
                    }]
                }]
            }

        settings_path = self.temp_dir / ".claude" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
        settings["hooks"] = resolved_hooks
        settings_path.write_text(json.dumps(settings, indent=2))

    def _plugin_cache_dir(self) -> Path:
        """Return the plugin cache directory."""
        plugin_name, marketplace_name, version = self._read_plugin_meta()
        return (
            Path.home() / ".claude" / "plugins" / "cache"
            / marketplace_name / plugin_name / version
        )

    def installed_plugin_version(self) -> str | None:
        """Return the version of the plugin installed in the cache, or None."""
        cache_dir = self._plugin_cache_dir()
        cached_plugin_json = cache_dir / ".claude-plugin" / "plugin.json"
        if not cached_plugin_json.exists():
            return None
        return json.loads(cached_plugin_json.read_text()).get("version")

    def load_system_prompt(self, file_path: str | Path) -> None:
        """Copy file content into the env's CLAUDE.md.

        Args:
            file_path: Path to the file whose content becomes CLAUDE.md.
        """
        src = Path(file_path).expanduser()
        if not src.exists():
            raise FileNotFoundError(f"System prompt file not found: {src}")
        shutil.copy2(src, self.temp_dir / "CLAUDE.md")

    def load_agent(self, agent_name: str) -> None:
        """Copy an agent .md file into the env's .claude/agents/ folder.

        Args:
            agent_name: Name of the agent (without .md extension) from the agents/ dir.
        """
        agent_src = SKILLIT_ROOT / "agents" / f"{agent_name}.md"
        if not agent_src.exists():
            raise FileNotFoundError(f"Agent not found: {agent_src}")

        agents_dir = self.temp_dir / ".claude" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(agent_src, agents_dir / f"{agent_name}.md")

    def load_rule(self, rule_path: str) -> None:
        """Copy a rule into the env's .flow/skill_rules folder."""
        rule_src = Path(rule_path).expanduser()
        rules_dir = self.temp_dir / ".flow" / "skill_rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

        rule_name = rule_src.name
        shutil.copytree(rule_src, rules_dir / rule_name)

    def load_all_user_rules(self) -> None:
        """Copy all rules from ~/.flow/skill_rules/ into the env."""
        user_rules = Path.home() / ".flow" / "skill_rules"
        if not user_rules.exists():
            return
        rules_dir = self.temp_dir / ".flow" / "skill_rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        for rule_dir in user_rules.iterdir():
            if rule_dir.is_dir() and (rule_dir / "trigger.py").exists():
                shutil.copytree(rule_dir, rules_dir / rule_dir.name)

    def _plugin_skill_log_path(self) -> Path | None:
        """Return the path to skill.log inside the installed plugin cache."""
        try:
            return self._plugin_cache_dir() / "skill.log"
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            return None

    def prompt(self, text: str, verbose: bool = False) -> PromptResult:
        """Run claude -p with the prompt and return the result.

        Args:
            text: The prompt to send.
            verbose: Print stdout to the console when True.
        """
        # Clear skill.log in the plugin cache before running
        log_path = self._plugin_skill_log_path()
        if log_path and log_path.exists():
            log_path.unlink()

        result = subprocess.run(
            ["claude", "-p", text],
            cwd=str(self.temp_dir),
            capture_output=True,
            text=True,
        )
        if verbose:
            print(result.stdout)

        skill_log = ""
        if log_path and log_path.exists():
            skill_log = log_path.read_text()

        return PromptResult(result.returncode, result.stdout, skill_log)

    # ------------------------------------------------------------------
    # Launch helpers
    # ------------------------------------------------------------------

    def open_terminal(self, command: str | None = None) -> None:
        """Open a new terminal window in this environment.

        Args:
            command: Optional command to run in the terminal.
        """
        open_terminal(self.temp_dir, command=command)

    def launch_claude(
        self,
        prompt: str | None = None,
        terminal: bool = True,
    ) -> PromptResult | None:
        """Launch claude in this environment.

        Args:
            prompt: When provided, run non-interactively with ``claude -p``
                    and return the result.  When *None*, open an interactive
                    session.
            terminal: Open a new terminal window.  When *False* with a
                      *prompt*, run in-process and return stdout only
                      (useful for tests).
        """
        if prompt and not terminal:
            return self.prompt(prompt)

        if prompt:
            self.open_terminal(command=f"claude -p '{prompt}'")
        else:
            self.open_terminal(command="claude --dangerously-skip-permissions")
        return None

    def cleanup(self):
        """Remove temp folder."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
