"""Launch a visible terminal in the HookTestEnvironment temp folder."""

from tests.test_utils.hook_environment import HookTestEnvironment, SKILLIT_ROOT
from terminal import open_terminal

SKILLIT_AGENT = SKILLIT_ROOT / "agents" / "skillit-agent.md"


def simple_terminal_launch():
    """Launch a terminal in a temporary HookTestEnvironment."""
    env = HookTestEnvironment()
    env.load_agent("skillit-agent")
    open_terminal(env.path)

def claude_system_prompt():
    """Launch a terminal with the skillit agent as CLAUDE.md system prompt."""
    env = HookTestEnvironment()
    env.load_system_prompt(SKILLIT_AGENT)
    print(f"Environment set up at: {env.path}")
    open_terminal(env.path)

def full_env_launch():
    """Install the plugin at project scope, load rules, and open a terminal."""
    env = HookTestEnvironment()
    env.install_plugin()
    env.load_all_user_rules()
    print(f"Environment set up at: {env.path}")
    open_terminal(env.path)


def full_env_launch_claude():
    """Launch claude with agent, all rules, and --dangerously-skip-permissions."""
    env = HookTestEnvironment()
    env.install_plugin()
    env.load_all_user_rules()
    print(f"Environment set up at: {env.path}")
    open_terminal(env.path, command="claude --dangerously-skip-permissions")


if __name__ == "__main__":
    full_env_launch_claude()
