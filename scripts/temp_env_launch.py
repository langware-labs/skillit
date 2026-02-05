"""Launch a visible terminal in the HookTestEnvironment temp folder."""

from tests.test_utils.hook_environment import HookTestEnvironment, SKILLIT_ROOT

SKILLIT_AGENT = SKILLIT_ROOT / "agents" / "skillit-agent.md"


def simple_terminal_launch():
    """Launch a terminal in a temporary HookTestEnvironment."""
    env = HookTestEnvironment()
    env.load_agent("skillit-agent")
    env.open_terminal()


def claude_system_prompt():
    """Launch a terminal with the skillit agent as CLAUDE.md system prompt."""
    env = HookTestEnvironment()
    env.load_system_prompt(SKILLIT_AGENT)
    print(f"Environment set up at: {env.path}")
    env.open_terminal()


def full_env_launch():
    """Install the plugin at project scope, load rules, and open a terminal."""
    env = HookTestEnvironment()
    env.install_plugin()
    env.load_all_user_rules()
    print(f"Environment set up at: {env.path}")
    env.open_terminal()


def full_env_launch_claude(prompt: str | None = None):
    """Install plugin, load rules, and launch claude.

    Args:
        prompt: Optional prompt to run non-interactively with ``claude -p``.
                When omitted, opens an interactive claude session.
    """
    env = HookTestEnvironment()
    env.install_plugin()
    env.load_all_user_rules()
    print(f"Environment set up at: {env.path}")
    env.launch_claude(prompt=prompt)


if __name__ == "__main__":
    full_env_launch()
