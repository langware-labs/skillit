"""Skillit test environment -- thin wrapper over SDK's ClaudeProjectEnvManager."""

from pathlib import Path
import shutil

from flow_sdk.claude_env import (
    ClaudeProjectEnvManager,
    LaunchMode,
    PromptResult,
    ClaudeTranscript,
    open_terminal,
)
from subagents.agent_manager import SubAgent
from utils.log import skill_log_clear

SKILLIT_ROOT = Path(__file__).resolve().parents[3]

# Sample rules directory used by load_rule fallback
_SAMPLE_RULES_DIR = Path(__file__).resolve().parent.parent / "unit" / "sample_rules"


class TestPluginProjectEnvironment(ClaudeProjectEnvManager):
    """Skillit-specific test env -- adds plugin records and agent resolution."""

    def __init__(self, dump: bool = True, **kwargs):
        super().__init__(plugin_root=SKILLIT_ROOT, dump=dump, **kwargs)
        self._skillit_records = None

    @property
    def skillit_records(self):
        if self._skillit_records is None:
            from plugin_records.skillit_records import SkillitRecords

            self._skillit_records = SkillitRecords(
                records_path=self._root / ".flow" / "records"
            )
        return self._skillit_records

    @property
    def user_rules_enabled(self) -> bool:
        return self.skillit_records.config.user_rules_enabled

    @user_rules_enabled.setter
    def user_rules_enabled(self, value: bool) -> None:
        self.skillit_records.config.user_rules_enabled = value

    def load_agent(self, agent_name) -> None:
        """Resolve agent from SKILLIT_ROOT/agents/."""
        name = str(agent_name)
        agent_src = SKILLIT_ROOT / "agents" / f"{name}.md"
        if not agent_src.exists():
            agent_src = SKILLIT_ROOT / "agents" / name
            if not agent_src.exists():
                raise FileNotFoundError(f"Agent not found: {agent_src}")

        agents_dir = self._root / ".claude" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(agent_src, agents_dir / f"{name}.md")

    def load_rule(self, rule_path: str) -> None:
        """Copy a rule into the env's .flow/skill_rules folder.

        Falls back to tests/unit/sample_rules/ if *rule_path* is a name.
        """
        rule_src = Path(rule_path).expanduser()
        if not rule_src.exists():
            sample = _SAMPLE_RULES_DIR / rule_path
            if sample.exists():
                rule_src = sample
            else:
                raise FileNotFoundError(f"Rule not found: {rule_path}")
        rules_dir = self._root / ".flow" / "skill_rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(rule_src, rules_dir / rule_src.name)

    def _hook_log_path(self) -> Path | None:
        """Override: point to skillit's skill.log."""
        from utils.conf import LOG_FILE

        return LOG_FILE

    def _pre_install_plugin(self) -> None:
        """Override: bump version and render templates before install."""
        from utils.plugin_manager import SkillitPluginManager

        mgr = SkillitPluginManager()
        mgr.patch()
        mgr.build()

    def run_last_activation(self) -> PromptResult:
        from main import main

        return super().run_last_activation(main_fn=main)


def make_env() -> TestPluginProjectEnvironment:
    """Create a test environment with all required agents loaded."""
    env = TestPluginProjectEnvironment()
    env.load_agent(SubAgent.MAIN_AGENT)
    env.load_agent(SubAgent.ANALYZE)
    skill_log_clear()
    return env
