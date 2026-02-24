"""Shared constants and helpers for CLI tests."""

from pathlib import Path

from subagents.agent_manager import SubAgent, get_subagent_launch_prompt
from hook_handlers.analysis import start_new_analysis, complete_analysis
from tests.test_utils import TestPluginProjectEnvironment, ClaudeTranscript, LaunchMode

TRANSCRIPT_PATH = Path(__file__).parent.parent / "unit" / "resources" / "jira_acli_fail.jsonl"
ACLI_SESSION_ID = "d7dd8377-c888-40e5-98ea-899ed95c7eeb"
LONG_SESSION_ID = "af0b46a4-9eba-43ec-874a-0c83606c0295"


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


def create_skill(env: TestPluginProjectEnvironment, mode: LaunchMode = LaunchMode.HEADLESS) -> str | None:
    """Create a skill from the conversation transcript.

    Args:
        env: The test environment (session is resumed automatically).
        mode: Launch mode for claude.

    Returns:
        The classification output text, or None if in interactive mode.
    """
    transcript = ClaudeTranscript.load(TRANSCRIPT_PATH)
    prompt_transcript_entry = transcript.get_entries("user")[0]

    prompt = prompt_transcript_entry["message"]["content"]
    instruction = f"Create a skill from this conversation where the user requested: {prompt}"
    all_rules_index = env.all_rules.rules_index
    data = {
        "known_rules": all_rules_index,
        "transcript_path": str(transcript.path),
        "cwd": prompt_transcript_entry.get("cwd", str(env.path)),
    }
    context_add = get_subagent_launch_prompt(SubAgent.SKILL_CREATOR, instruction, data)

    result = env.launch_claude(context_add, mode=mode)
    if mode == LaunchMode.INTERACTIVE:
        return None
    assert result.returncode == 0
    return result.stdout
