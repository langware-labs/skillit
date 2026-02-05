"""Simple test environment for hook testing."""

import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path

from memory.rule_engine.engine import RulesPackage, RuleEngine

TEMP_DIR = Path(tempfile.gettempdir()) / "skillit_test"
SKILLIT_ROOT = Path(__file__).resolve().parents[3]


def open_terminal(
    cwd: str | Path,
    command: str | None = None,
    env: dict[str, str] | None = None,
) -> None:
    """Open a visible terminal window at the given directory.

    Args:
        cwd: Directory to open the terminal in.
        command: Optional command to run in the new terminal.
        env: Optional environment variables for the child process.
    """
    cwd = str(cwd)

    # Build an export prefix so the new shell inherits custom env vars
    export_prefix = ""
    if env:
        inherited = {k: v for k, v in env.items() if k not in os.environ or os.environ[k] != v}
        if inherited:
            if sys.platform == "win32":
                export_prefix = " && ".join(f"set {k}={v}" for k, v in inherited.items()) + " && "
            else:
                export_prefix = " ".join(f"export {k}={shlex.quote(v)};" for k, v in inherited.items()) + " "

    if sys.platform == "darwin":
        inner = f"{export_prefix}cd {cwd} && {command}" if command else f"{export_prefix}cd {cwd}"
        script = (
            'tell application "Terminal"\n'
            f'    do script "{inner}"\n'
            '    activate\n'
            'end tell'
        )
        subprocess.run(["osascript", "-e", script])
    elif sys.platform == "win32":
        inner = f"{export_prefix}cd /d {cwd} && {command}" if command else f"{export_prefix}cd /d {cwd}"
        subprocess.Popen(["cmd", "/c", "start", "cmd", "/K", inner])
    else:
        shell_cmd = f"{export_prefix}cd {cwd} && {command}; exec $SHELL" if command else f"{export_prefix}cd {cwd} && $SHELL"
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


class _TeeIO(io.StringIO):
    """StringIO that also forwards writes to a second stream (e.g. the real stdout)."""

    def __init__(self, terminal: io.TextIOBase | None = None):
        super().__init__()
        self._terminal = terminal

    def write(self, s: str) -> int:
        if self._terminal:
            self._terminal.write(s)
            self._terminal.flush()
        return super().write(s)


class HookTestEnvironment:
    """Self-contained test environment with project-level hooks."""

    DUMP_FILENAME = "stdin_dump.jsonl"

    def __init__(self, dump: bool = True, clean=True):
        self.temp_dir = TEMP_DIR
        self._env_vars: dict[str, str] = {}
        self._dump_activations = False
        self._clean = clean
        if dump:
            self.dump_activations = True
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

    # ------------------------------------------------------------------
    # Environment variable helpers
    # ------------------------------------------------------------------

    def env_set(self, key: str, value: str) -> None:
        """Set an environment variable to be passed to child processes.

        Works cross-platform — the variable is stored internally and
        merged into the subprocess environment at launch time.

        Args:
            key: Environment variable name.
            value: Environment variable value.
        """
        self._env_vars[key] = value

    def env_unset(self, key: str) -> None:
        """Remove a previously set environment variable.

        Args:
            key: Environment variable name.
        """
        self._env_vars.pop(key, None)

    def _build_env(self) -> dict[str, str]:
        """Return a copy of os.environ merged with custom env vars."""
        env = os.environ.copy()
        env.update(self._env_vars)
        return env

    @property
    def dump_activations(self) -> bool:
        """Whether stdin dumping is enabled for hook invocations."""
        return self._dump_activations

    @dump_activations.setter
    def dump_activations(self, value: bool) -> None:
        self._dump_activations = value
        if value:
            dump_path = self.temp_dir / ".flow" / self.DUMP_FILENAME
            self.env_set("SKILLIT_DUMP_STDIN", str(dump_path))
        else:
            self.env_unset("SKILLIT_DUMP_STDIN")

    @property
    def dump_file(self) -> Path | None:
        """Return the path to the stdin dump file, or None if dumping is off."""
        if not self._dump_activations:
            return None
        return self.temp_dir / ".flow" / self.DUMP_FILENAME

    def _setup(self):
        """Create a clean temp folder."""
        if self.temp_dir.exists() and self._clean:
            shutil.rmtree(self.temp_dir)

        self.temp_dir.mkdir(parents=True, exist_ok=True)

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
        """Build templates and enable the skillit plugin at project scope.

        Renders templates (so agents carry the current version), ensures the
        marketplace is registered, then enables with ``--scope project``.
        """
        from plugin_manager import SkillitPluginManager
        SkillitPluginManager().build()

        plugin_name, marketplace_name, _ = self._read_plugin_meta()

        # Ensure marketplace points at the local repo
        subprocess.run(
            ["claude", "plugin", "marketplace", "remove", marketplace_name],
            capture_output=True,
        )
        rel_path = os.path.relpath(SKILLIT_ROOT, os.getcwd())
        local_path = f"./{rel_path.replace(os.sep, '/')}"
        subprocess.run(
            ["claude", "plugin", "marketplace", "add", local_path],
            check=True,
        )

        # Install plugin
        plugin_ref = f"{plugin_name}@{marketplace_name}"
        subprocess.run(
            ["claude", "plugin", "install", plugin_ref, "--scope", "project"],
            cwd=str(self.temp_dir),
            check=True,
        )

        # Enable plugin at project scope (may already be enabled after install)
        result = subprocess.run(
            ["claude", "plugin", "enable", plugin_name, "--scope", "project"],
            cwd=str(self.temp_dir),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 and "already enabled" not in result.stderr:
            raise RuntimeError(
                f"'claude plugin enable {plugin_name} --scope project' failed "
                f"(exit {result.returncode}): {result.stderr}"
            )

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
        """Copy a rule into the env's .flow/skill_rules folder.

        Args:
            rule_path: Full path to a rule directory, or a simple name
                       that will be resolved from tests/unit/sample_rules/.
        """
        rule_src = Path(rule_path).expanduser()
        if not rule_src.exists():
            # Try resolving as a sample rule name
            sample = Path(__file__).resolve().parent.parent / "unit" / "sample_rules" / rule_path
            if sample.exists():
                rule_src = sample
            else:
                raise FileNotFoundError(f"Rule not found: {rule_path}")

        rules_dir = self.temp_dir / ".flow" / "skill_rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(rule_src, rules_dir / rule_src.name)

    def load_all_user_rules(self) -> None:
        """Copy all rules from ~/.flow/skill_rules/ into the env."""
        user_rules = Path.home() / ".flow" / "skill_rules"
        if not user_rules.exists():
            return
        rules_dir = self.temp_dir / ".flow" / "skill_rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        for rule_dir in user_rules.iterdir():
            if rule_dir.is_dir() and (rule_dir / "trigger.py").exists():
                shutil.copytree(rule_dir, rules_dir / rule_dir.name, dirs_exist_ok=True)

    def _plugin_skill_log_path(self) -> Path | None:
        """Return the path to skill.log."""
        from conf import LOG_FILE
        return LOG_FILE

    def prompt(self, text: str, verbose: bool = True, timeout: int = 120) -> PromptResult:
        """Run claude -p with the prompt and return the result.

        Args:
            text: The prompt to send.
            verbose: Stream stdout to the console as it arrives (default True).
            timeout: Maximum seconds to wait for claude to finish (default 120).
        """
        import time

        # Clear skill.log in the plugin cache before running
        log_path = self._plugin_skill_log_path()
        if log_path and log_path.exists():
            log_path.unlink()

        proc = subprocess.Popen(
            ["claude", "-p", text, "--dangerously-skip-permissions"],
            cwd=str(self.temp_dir),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self._build_env(),
        )

        stdout_parts: list[str] = []
        deadline = time.monotonic() + timeout

        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    proc.kill()
                    proc.wait()
                    return PromptResult(1, "".join(stdout_parts), skill_log="[timed out]")

                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if line:
                    stdout_parts.append(line)
                    if verbose:
                        print(line, end="", flush=True)
        except Exception:
            proc.kill()
            proc.wait()
            raise

        returncode = proc.returncode

        skill_log = ""
        if log_path and log_path.exists():
            skill_log = log_path.read_text()

        return PromptResult(returncode, "".join(stdout_parts), skill_log)

    # ------------------------------------------------------------------
    # Launch helpers
    # ------------------------------------------------------------------

    def open_terminal(self, command: str | None = None) -> None:
        """Open a new terminal window in this environment.

        Args:
            command: Optional command to run in the terminal.
        """
        open_terminal(self.temp_dir, command=command, env=self._build_env())

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
            self.open_terminal(command=f"claude --dangerously-skip-permissions -p '{prompt}'")
        else:
            self.open_terminal(command="claude --dangerously-skip-permissions")
        return None

    def run_last_activation(self) -> PromptResult:
        """Re-run main.py with the last dumped stdin, in-process.

        Calls ``main.main()`` directly in the current Python process so
        that breakpoints set in main.py (or any code it calls) are hit
        by the debugger.

        Returns:
            PromptResult with captured stdout and skill log.

        Raises:
            FileNotFoundError: If the dump file does not exist.
            ValueError: If the dump file is empty.
        """
        dump = self.dump_file
        if dump is None or not dump.exists():
            raise FileNotFoundError(
                f"No dump file found at {dump}. "
                "Run a prompt with dump_activations=True first."
            )
        print(f"Re-running last activation from dump: {dump}")

        lines = [line for line in dump.read_text().splitlines() if line.strip()]
        if not lines:
            raise ValueError(f"Dump file is empty: {dump}")
        last_entry = lines[-1]

        # Save state we're about to mutate
        old_stdin = sys.stdin
        old_cwd = os.getcwd()
        saved_env: dict[str, str | None] = {}

        stdout_buf = _TeeIO(sys.stdout)
        exit_code = 0

        try:
            # Apply env vars to the real os.environ (so main.py sees them)
            for key, value in self._env_vars.items():
                saved_env[key] = os.environ.get(key)
                os.environ[key] = value

            os.chdir(str(self.temp_dir))
            sys.stdin = io.StringIO(last_entry)

            from main import main  # noqa: import here so debugger resolves it

            with redirect_stdout(stdout_buf):
                try:
                    main()
                except SystemExit as exc:
                    exit_code = exc.code if isinstance(exc.code, int) else 0
        finally:
            # Restore everything
            sys.stdin = old_stdin
            os.chdir(old_cwd)
            for key, orig in saved_env.items():
                if orig is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = orig

        log_path = self._plugin_skill_log_path()
        skill_log_text = ""
        if log_path and log_path.exists():
            skill_log_text = log_path.read_text()

        return PromptResult(exit_code, stdout_buf.getvalue(), skill_log_text)

    def cleanup(self):
        """Remove temp folder."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
