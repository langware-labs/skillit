"""Test jira prompt behavior with and without jira_context skill."""


def test_jira_no_acli(isolated_hook_env):
    """Jira prompt should not suggest acli when no jira_context rule is present."""
    result = isolated_hook_env.prompt("how do can i list mi jira tickets")
    assert result.returncode == 0
    assert result.response_not_contains("acli")


def test_jira_with_acli(isolated_hook_env):
    """Jira prompt should suggest acli when jira_context rule is loaded."""
    isolated_hook_env.load_skill("~/.flow/skill_rules/jira_context")
    result = isolated_hook_env.prompt("how do can i list mi jira tickets")
    assert result.returncode == 0
    assert result.response_contains("acli")
