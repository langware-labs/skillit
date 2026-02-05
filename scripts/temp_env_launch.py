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


def full_env_launch_claude(prompt: str | None = None, terminal: bool = True):
    env = HookTestEnvironment()
    env.install_plugin()
    env.load_all_user_rules()
    print(f"Environment set up at: {env.path}")
    env.launch_claude(prompt,terminal)
    return env

def run_last_activation():
    """Install plugin, load rules, and run the last activation."""
    env = HookTestEnvironment(clean=False)
    env.install_plugin()
    env.load_all_user_rules()
    env.run_last_activation()

if __name__ == "__main__":
    # print(full_env_launch_claude("List my jira tickets", terminal=False))
    run_last_activation()