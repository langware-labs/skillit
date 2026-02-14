"""Test jira prompt behavior with and without jira_context rule."""

from pathlib import Path

from tests.test_utils import ClaudeTranscript, TestPluginProjectEnvironment

# Path to sample transcript
TRANSCRIPT_PATH = Path(__file__).parent / "unit" / "resources" / "simple_jira_request_transcript.jsonl"


def test_jira_no_acli(isolated_hook_env):
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
    """handle_analyze returns subagent instructions for rule creation."""
    from modifiers.analyze_and_create_activation_rules import handle_analyze

    transcript = ClaudeTranscript.load(TRANSCRIPT_PATH)
    data = {
        "hookEvent": "UserPromptSubmit",
        "prompt": "skillit",
        "cwd": str(isolated_hook_env.path),
        "transcript_path": str(transcript.path),
    }
    result = handle_analyze("skillit", data)

    # handle_analyze returns a string with subagent instructions
    assert isinstance(result, str)
    assert "Task subagent" in result or "subagent" in result
    assert "activation rules" in result.lower()
    assert "analyze_and_create_activation_rules" in result or "Skillit Analysis" in result
