import time

from hook_handlers.analysis import start_new_analysis, complete_analysis
from utils.log import skill_log_print, skill_log_clear
from plugin_records.skillit_records import skillit_records
from tests.test_utils import LaunchMode, make_env
from tests.cli.shared import analyze_hook


def test_mcp_session_id_injection():
    """Verify that SESSION_START hook injects session ID into context."""
    env = make_env()
    env.install_plugin()
    skill_log_clear()

    # Trigger a prompt to activate SESSION_START
    result = env.prompt("what is the session id ? ", verbose=False)
    assert result.returncode == 0
    assert env.session_id in result.stdout, "session_id should be included in the prompt response"

    # Verify session was created in skillit_records
    session = skillit_records.get_session(env.session_id)
    assert session.session_id == env.session_id
    skill_log_print()

def test_mcp_session_flow_context_usage():
    """Verify that flow_context MCP tool stores and retrieves values via skillit_records."""
    env = make_env()
    env.install_plugin()
    skill_log_clear()

    # Trigger a prompt to activate SESSION_START
    result = env.launch_claude("use the skillit mcp and store the value of 1566 into key 'the key' into the flow_context", mode=LaunchMode.HEADLESS)
    print(f"\n **********************\n Prompt result: {result.stdout} \n **********************\n")
    assert result.returncode == 0
    assert "1566" in result.stdout, "Claude should confirm the value was stored"

    # Verify session was created with the key-value pair
    session = skillit_records.get_session(env.session_id)
    assert session.session_id == env.session_id
    assert "the key" in session
    assert session["the key"] == "1566"

    # Write a timestamp directly via skillit_records
    timestamp = str(int(time.time()))
    session["the key"] = timestamp
    session.save()

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

def test_task_reactivity():
    """Test task creation and status update webhooks without LLM processing.

    This test verifies that:
    1. Task CREATE webhook is sent and processed by FlowPad
    2. After 2 seconds, task UPDATE webhook is sent
    3. FlowPad receives and processes both webhooks reactively
    """
    env = make_env()
    env.install_plugin()
    skill_log_clear()

    session_id = env.session_id
    print(f"\n[TEST] Starting task reactivity test for session {session_id}")

    # Step 1: Send task CREATE webhook
    print(f"[TEST] Sending task CREATE webhook...")
    resources = start_new_analysis(session_id)
    assert resources is not None
    assert resources.task is not None
    print(f"[TEST] ✓ Task created: {resources.task.id}")

    # Step 2: Wait 2 seconds to simulate processing
    print(f"[TEST] Waiting 2 seconds...")
    time.sleep(2)

    # Step 3: Send task UPDATE webhook (mark as DONE)
    print(f"[TEST] Sending task UPDATE webhook...")
    complete_analysis(resources, session_id)
    print(f"[TEST] ✓ Task completed: {resources.task.id}")

    # Verify the output directory was created
    session = skillit_records.get_session(session_id)
    output_dir = session.output_dir
    assert output_dir.exists(), "Output directory should exist"
    print(f"[TEST] ✓ Output directory exists: {output_dir}")

    print(f"[TEST] Task reactivity test complete!")
    skill_log_print()


def test_output_dir():
    """End-to-end: analyze transcript, classify issues, create rule."""
    env = make_env()
    env.install_plugin()
    skill_log_clear()
    analyze_hook(env, mode=LaunchMode.HEADLESS)
    session = skillit_records.get_session(env.session_id)
    output_dir = session.output_dir
    assert output_dir.exists()
    assert any(output_dir.iterdir()), "Output directory should not be empty"
    analysis_doc = output_dir / "analysis.md"
    assert analysis_doc.exists(), "Analysis output file should exist"
    skill_log_print()
