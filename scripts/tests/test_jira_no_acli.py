"""Test jira prompt behavior with and without jira_context rule."""

from tests.test_utils import gen_rule


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
    generated_rule = gen_rule(
        name="jira_context_gen",
        trigger_keywords=["jira", "ticket"],
        action_type="add_context",
        action_content="Use acli to work with jira tickets.",
    )
    isolated_hook_env.load_rule(str(generated_rule.rule_path))
    result = isolated_hook_env.prompt("how do can i list mi jira tickets")
    assert result.returncode == 0
    assert result.hook_output_contains("acli")
