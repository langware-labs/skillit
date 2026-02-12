from pathlib import Path
import json

from agent_manager import SubAgent, get_subagent_launch_prompt
from conf import get_session_output_dir
from log import skill_log_print, skill_log_clear
from tests.test_utils import TestPluginProjectEnvironment, ClaudeTranscript, LaunchMode, make_env

TRANSCRIPT_PATH = Path(__file__).parent / "unit" / "resources" / "jira_acli_fail.jsonl"


def analyze_hook(env: TestPluginProjectEnvironment, mode: LaunchMode = LaunchMode.HEADLESS) -> str:
    """Build the analysis prompt from the transcript and launch the analyzer.

    Returns:
        The analysis output text (stdout from the analyzer subagent).
    """
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
    return result.stdout


def test_output_dir():
    """End-to-end: analyze transcript, classify issues, create rule."""
    env = make_env()
    skill_log_clear()
    analyze_hook(env, mode=LaunchMode.HEADLESS)
    output_dir = get_session_output_dir(env.session_id)
    assert output_dir.exists()
    assert any(output_dir.iterdir()), "Output directory should not be empty"
    analysis_doc = output_dir / "analysis.md"
    assert analysis_doc.exists(), "Analysis output file should exist"
    skill_log_print()


def test_mcp_session_id_injection():
    """Verify that SESSION_START hook injects session ID into context."""
    env = make_env()
    env.load_rule("session-context-init")  # Deploy the hook rule
    env.loadMcp()
    skill_log_clear()

    # Trigger a prompt to activate SESSION_START
    result = env.prompt("test session initialization", verbose=False)
    assert result.returncode == 0

    # Verify context file was created by the hook
    output_dir = get_session_output_dir(env.session_id)
    context_file = output_dir / "flow_context.json"
    assert context_file.exists(), "flow_context.json should be created by SESSION_START hook"

    # Verify it contains session_id
    with open(context_file) as f:
        data = json.load(f)
    assert "session_id" in data
    assert data["session_id"] == env.session_id
    skill_log_print()


def test_flow_context_storage():
    """Verify MCP tool can read/write values to session storage."""
    env = make_env()
    env.load_rule("session-context-init")
    env.loadMcp()
    skill_log_clear()

    # Create instruction that uses the MCP tool
    instruction = """
    Use the skillit MCP server's flow_context tool to:
    1. Set a value: key="test_key", value="test_value"
    2. Get the value back to verify it was stored

    The session_id should be available in your context.
    """

    result = env.prompt(instruction, verbose=True, timeout=60)
    assert result.returncode == 0

    # Verify the value was actually stored in the JSON file
    output_dir = get_session_output_dir(env.session_id)
    context_file = output_dir / "flow_context.json"

    assert context_file.exists()
    with open(context_file) as f:
        data = json.load(f)

    assert "test_key" in data
    assert data["test_key"] == "test_value"

    # Verify Claude successfully retrieved the value
    assert "test_value" in result.stdout.lower()
    skill_log_print()


def test_flow_context_get_nonexistent_key():
    """Verify proper error handling for nonexistent keys."""
    env = make_env()
    env.load_rule("session-context-init")
    env.loadMcp()
    skill_log_clear()

    instruction = """
    Use the skillit MCP flow_context tool to get a key that doesn't exist:
    key="nonexistent_key"
    """

    result = env.prompt(instruction, verbose=False, timeout=60)
    assert result.returncode == 0
    assert "not found" in result.stdout.lower()
    skill_log_print()



