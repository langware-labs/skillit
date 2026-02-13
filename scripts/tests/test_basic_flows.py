import time
from pathlib import Path
import json

from agent_manager import SubAgent, get_subagent_launch_prompt
from conf import get_session_dir, get_session_output_dir
from log import skill_log_print, skill_log_clear
from fs_store import SyncOperation
from notify import send_task_sync
from task_resource import TaskResource, TaskStatus, TaskType
from fs_store import FsRecord
from tests.test_utils import TestPluginProjectEnvironment, ClaudeTranscript, LaunchMode, make_env

TRANSCRIPT_PATH = Path(__file__).parent / "unit" / "resources" / "jira_acli_fail.jsonl"


def analyze_hook(env: TestPluginProjectEnvironment, mode: LaunchMode = LaunchMode.HEADLESS) -> str:
    """Build the analysis prompt from the transcript and launch the analyzer.

    Returns:
        The analysis output text (stdout from the analyzer subagent).
    """
    session_id = env.session_id
    output_dir = get_session_output_dir(session_id)

    # Create "In Progress" task and reflect to FlowPad
    task = TaskResource(
        id=f"analysis-{session_id}",
        title="Analyzing session",
        status=TaskStatus.IN_PROGRESS,
        task_type=TaskType.ANALYSIS,
        tags=["analysis", "skillit"],
        metadata={
            "session_id": session_id,
            "output_dir": str(output_dir),
            "analysisPath": str(output_dir / "analysis.md"),
            "analysisJsonPath": str(output_dir / "analysis.json"),
        },
    )
    task.save_to(get_session_dir(session_id))
    send_task_sync(SyncOperation.CREATE, task.to_dict())

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

    # Update task to "Done" and reflect to FlowPad
    task.status = TaskStatus.DONE
    task.save_to(get_session_dir(session_id))
    send_task_sync(SyncOperation.UPDATE, task.to_dict())

    return result.stdout


def test_mcp_session_id_injection():
    """Verify that SESSION_START hook injects session ID into context."""
    env = make_env()
    env.install_plugin()
    skill_log_clear()

    # Trigger a prompt to activate SESSION_START
    result = env.prompt("what is the session id ? ", verbose=False)
    assert result.returncode == 0
    assert env.session_id in result.stdout, "session_id should be included in the prompt response"
    # Verify context file was created by the hook in session dir (not output dir)
    session_dir = get_session_dir(env.session_id)
    context_file = session_dir / "record.json"
    assert context_file.exists(), "record.json should be created by SESSION_START hook"

    # Verify it contains session_id
    with open(context_file) as f:
        data = json.load(f)
    assert "session_id" in data
    assert data["session_id"] == env.session_id
    skill_log_print()

def test_mcp_session_flow_context_usage():
    """Verify that SESSION_START hook injects session ID into context."""
    env = make_env()
    env.install_plugin()
    skill_log_clear()

    # Trigger a prompt to activate SESSION_START
    result = env.launch_claude("use the skillit mcp and store the value of 1566 into key 'the key' into the flow_context", mode=LaunchMode.HEADLESS)
    print(f"\n **********************\n Prompt result: {result.stdout} \n **********************\n")
    assert result.returncode == 0
    assert env.session_id in result.stdout, "session_id should be included in the prompt response"
    # Verify context file was created by the hook in session dir (not output dir)
    session_dir = get_session_dir(env.session_id)
    context_file = session_dir / "record.json"
    assert context_file.exists(), "record.json should be created by SESSION_START hook"

    # Verify it contains session_id
    with open(context_file) as f:
        data = json.load(f)
    assert "session_id" in data
    assert data["session_id"] == env.session_id
    assert "the key" in data
    assert data["the key"] == "1566"

    # Write a timestamp directly using ResourceRecord
    timestamp = str(int(time.time()))
    session_dir = get_session_dir(env.session_id)
    context_file = session_dir / "record.json"
    store = FsRecord.from_json(context_file)
    store["the key"] = timestamp
    store.persist()

    # Second launch (resumes session): ask Claude to retrieve the value via MCP
    instruction = (
        f'Use the skillit MCP flow_context tool to get the value of key="the key". '
    )
    result = env.launch_claude(instruction, mode=LaunchMode.HEADLESS)
    assert result.returncode == 0

    # Verify Claude returned the timestamp
    assert timestamp in result.stdout, (
        f"Expected timestamp {timestamp} in model response, got: {result.stdout}"
    )
    skill_log_print()

def test_output_dir():
    """End-to-end: analyze transcript, classify issues, create rule."""
    env = make_env()
    env.install_plugin()
    skill_log_clear()
    analyze_hook(env, mode=LaunchMode.HEADLESS)
    output_dir = get_session_output_dir(env.session_id)
    assert output_dir.exists()
    assert any(output_dir.iterdir()), "Output directory should not be empty"
    analysis_doc = output_dir / "analysis.md"
    assert analysis_doc.exists(), "Analysis output file should exist"
    skill_log_print()


