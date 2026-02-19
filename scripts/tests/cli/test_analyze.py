from pathlib import Path

from flow_sdk.fs_records.claude import ClaudeRootFsRecord
from subagents.agent_manager import SubAgent, get_subagent_launch_prompt
from tests.test_utils import TestPluginProjectEnvironment, ClaudeTranscript, LaunchMode, make_env

TRANSCRIPT_PATH = Path(__file__).parent.parent / "unit" / "resources" / "jira_acli_fail.jsonl"
LONG_SESSION_ID = "af0b46a4-9eba-43ec-874a-0c83606c0295"


def create_skill(env: TestPluginProjectEnvironment, mode: LaunchMode = LaunchMode.HEADLESS) -> str | None:
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


DEBUG_FILE = Path(__file__).parent / "analyze_debug.log"


def test_analyze():
    env = make_env()
    env.debug_file = DEBUG_FILE
    env.install_plugin()
    claude = ClaudeRootFsRecord.default()
    session = claude.get_session(LONG_SESSION_ID)
    assert session is not None, f"Session {LONG_SESSION_ID} not found"
    print(f"Session found: {session.session_id}")
    env.launch_claude(f"Launch skillit analyzer and Analyze the session {LONG_SESSION_ID}", mode=LaunchMode.INTERACTIVE)
