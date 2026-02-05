"""Test jira prompt behavior with and without jira_context rule."""

from pathlib import Path

from memory.rule_engine.rule_generator import gen_rule

from memory import RuleEngine, ActivationRule
from tests.test_utils import ClaudeTranscript


# Path to sample transcript
TRANSCRIPT_PATH = Path(__file__).parent / "unit" / "resources" / "transcript.jsonl"


def test_jira_no_acli(isolated_hook_env):
    """Jira prompt should not suggest acli when no jira_context rule is present."""
    result = isolated_hook_env.prompt("how do can i list mi jira tickets")
    assert result.returncode == 0
    assert result.response_not_contains("acli")


def test_jira_with_acli(isolated_hook_env):
    """Jira prompt should inject acli context when jira_context rule is loaded."""
    isolated_hook_env.load_rule("~/.flow/skill_rules/jira_context")
    result = isolated_hook_env.prompt("how do can i list mi jira tickets")
    assert result.returncode == 0
    assert result.hook_output_contains("acli")


def test_jira_with_acli_gen_rule(isolated_hook_env):
    """Jira prompt should inject acli context when generated rule is loaded."""
    # Load transcript from resources as a dataclass
    transcript = ClaudeTranscript.load(TRANSCRIPT_PATH)

    # Hook data structure using real paths from the environment
    # Uses camelCase format consistent with main.py
    hooks_data = {
        "hookEvent": "UserPromptSubmit",
        "session_id": "test-session-123",
        "prompt": "how do can i list my jira tickets",
        "cwd": str(isolated_hook_env.path),
        "transcript_path": str(transcript.path),
    }
    rule: ActivationRule =RuleEngine.gen_rule(
        hooks_data=hooks_data,
        transcript=transcript,
        name="jira_context_gen",
    )
    print(f"Generated Rule {rule.name} : {rule.path}\n")
    rule_engine:RuleEngine = isolated_hook_env.rule_engine
    # Generate rule directly into project_rules directory
    rule_engine.load_rule(rule)
    # Rule is generated directly in project_rules, no need to load separately
    result = isolated_hook_env.prompt("how do can i list mi jira tickets")
    assert result.returncode == 0
    assert result.hook_output_contains("acli")
