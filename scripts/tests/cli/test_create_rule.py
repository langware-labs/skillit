from pathlib import Path

from agent_manager import SubAgent, get_subagent_launch_prompt
from analysis import start_new_analysis, complete_analysis
from log import skill_log_print
from tests.test_utils import TestPluginProjectEnvironment, ClaudeTranscript, LaunchMode, make_env

TRANSCRIPT_PATH = Path(__file__).parent / "unit" / "resources" / "jira_acli_fail.jsonl"


def analyze_hook(env: TestPluginProjectEnvironment, mode: LaunchMode = LaunchMode.HEADLESS) -> str:
    """Build the analysis prompt from the transcript and launch the analyzer.

    Returns:
        The analysis output text (stdout from the analyzer subagent).
    """
    session_id = env.session_id

    # Create "In Progress" task + agentic process and reflect to FlowPad
    resources = start_new_analysis(session_id)

    transcript = ClaudeTranscript.load(TRANSCRIPT_PATH)
    prompt_transcript_entry = transcript.get_entries("user")[0]

    prompt = prompt_transcript_entry["message"]["content"]
    data = {
        "hookEvent": "UserPromptSubmit",
        "prompt": prompt,
        "cwd": prompt_transcript_entry["cwd"],
        "transcript_path": str(transcript.path),
    }
    instruction = f"user requested to analyze: {prompt}"
    context_add = get_subagent_launch_prompt(SubAgent.ANALYZE, instruction, data)
    assert isinstance(context_add, str)
    assert "skillit-analyzer" in context_add

    result = env.launch_claude(context_add, mode=mode)
    assert result.returncode == 0

    # Update task + process to "Done" and reflect to FlowPad
    complete_analysis(resources, session_id)

    return result.stdout


def classify_analysis(env: TestPluginProjectEnvironment, mode: LaunchMode = LaunchMode.HEADLESS) -> str:
    """Classify the issues found during analysis.

    Args:
        env: The test environment (session is resumed automatically).
        mode: Launch mode for claude.

    Returns:
        The classification output text.
    """
    transcript = ClaudeTranscript.load(TRANSCRIPT_PATH)
    prompt = transcript.get_entries("user")[0]["message"]["content"]

    instruction = f"user original request: {prompt}"
    all_rules_index = env.all_rules.rules_index
    data = {"known_rules": all_rules_index}
    context_add = get_subagent_launch_prompt(SubAgent.CLASSIFY, instruction, data)

    result = env.launch_claude(context_add, mode=mode)
    assert result.returncode == 0
    return result.stdout


def create_rule(env: TestPluginProjectEnvironment, mode: LaunchMode = LaunchMode.HEADLESS) -> str | None:
    transcript = ClaudeTranscript.load(TRANSCRIPT_PATH)
    prompt = transcript.get_entries("user")[0]["message"]["content"]

    instruction = f"user original request: {prompt}"
    context_add = get_subagent_launch_prompt(SubAgent.CREATE, instruction, {})

    result = env.launch_claude(context_add, mode=mode)
    if mode == LaunchMode.INTERACTIVE:
        return None
    assert result.returncode == 0
    return result.stdout


def test_create_rule():
    """End-to-end: analyze transcript, classify issues, create rule."""
    env = make_env()
    env.install_plugin()
    env._fork = True
    print(f"Environment set up at: {env.path}")
    # analysis = analyze_hook(env, mode=LaunchMode.INTERACTIVE)
    # analysis = analyze_hook(env, mode=LaunchMode.HEADLESS)
    env._resume_session_id = '53058fd8-a437-4532-853a-e0bc4f98f87f'
    classification = classify_analysis(env, mode=LaunchMode.INTERACTIVE)
    return
    env._resume_session_id ='ecc0171f-80d7-4fed-a694-cc3c481ddb94'
    rule_output = create_rule(env, mode=LaunchMode.INTERACTIVE)
    print("=== Rule Creation ===")
    print(rule_output)

def test_create_rule_complete():
    """End-to-end: analyze transcript, classify issues, create rule."""
    env = make_env()
    env._clean = False  # Prevent cleanup so files persist for inspection
    print(f"Environment set up at: {env.path}")
    print(f"Rules will be created at: {env.path}/.flow/skill_rules")
    print(f"session: {env.session_id}")
    # Run all steps in headless mode for automatic completion
    analyze_hook(env, mode=LaunchMode.HEADLESS)
    classify_analysis(env, mode=LaunchMode.HEADLESS)
    rule_output = create_rule(env, mode=LaunchMode.INTERACTIVE)
    print("=== Rule Creation ===")
    print(rule_output)
    print(f"\n>>> Files preserved at: {env.path}")
    print(f">>> Check for created rules at: {env.path}/.flow/skill_rules")

def test_notify_mcp():
    """End-to-end: analyze transcript, classify issues, create rule."""
    env = make_env()
    env.loadMcp()
    result = env.launch_claude("use skillit mcp to parse the tag: <flow-started_generating_skill>Testing MCP flow tag</flow-started_generating_skill>")
    skill_log_print()
    assert result.returncode == 0
    assert 'flow' in result.stdout.lower()
