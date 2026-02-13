#!/usr/bin/env python3
"""
Test Runner for Skillit Plugin
Invokes main.py exactly as Claude Code does - same command, env vars, and stdin format.

Usage:
    python test.py                     # Test with default "skillit:test"
    python test.py "skillit:test"      # Test with custom prompt
    python test.py --all               # Run full test suite
    python test.py --transcript        # Test with real transcript
    python test.py --notify            # Test notification module
    python test.py --activation        # Test activation rules module
"""
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from glob import glob
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# =============================================================================
# CONFIGURATION - Match hooks.json exactly
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
PLUGIN_DIR = SCRIPT_DIR.parent
STATE_FILE = PLUGIN_DIR / "global_state.json"


def reset_cooldown():
    """Reset the cooldown state to allow the next test to run immediately."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({}, f)
    except Exception:
        pass

# The exact command from hooks.json
HOOK_COMMAND = 'python "$CLAUDE_PLUGIN_ROOT/scripts/main.py"'


def invoke_main(prompt: str, verbose: bool = True) -> dict:
    """
    Invoke main.py exactly as Claude Code does.

    From hooks.json:
        "command": "python \"$CLAUDE_PLUGIN_ROOT/scripts/main.py\""

    Claude Code:
    1. Sets environment variables
    2. Runs the command through shell (for $CLAUDE_PLUGIN_ROOT expansion)
    3. Pipes JSON to stdin
    4. Reads JSON from stdout
    """

    # Generate session info like Claude Code does
    session_id = str(uuid.uuid4())

    # Build stdin payload - exact format from Claude Code logs
    stdin_payload = {
        "session_id": session_id,
        "cwd": str(PLUGIN_DIR),
        "permission_mode": "default",
        "hook_event_name": "UserPromptSubmit",
        "prompt": prompt
    }

    # Set environment variables exactly as Claude Code does
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_DIR)
    env["CLAUDE_PROJECT_DIR"] = str(PLUGIN_DIR)

    if verbose:
        print("=" * 60)
        print("INVOKING MAIN.PY (exactly as Claude Code does)")
        print("=" * 60)
        print()
        print(f"Command: {HOOK_COMMAND}")
        print(f"  -> Expands to: python \"{PLUGIN_DIR}/scripts/main.py\"")
        print()
        print("Environment:")
        print(f"  CLAUDE_PLUGIN_ROOT={PLUGIN_DIR}")
        print(f"  CLAUDE_PROJECT_DIR={PLUGIN_DIR}")
        print()
        print("-" * 60)

    # Execute the EXACT command from hooks.json through shell
    # This ensures $CLAUDE_PLUGIN_ROOT is expanded just like Claude Code does
    result = subprocess.run(
        HOOK_COMMAND,
        shell=True,  # Required for env var expansion
        input=json.dumps(stdin_payload),
        capture_output=True,
        text=True,
        env=env
    )

    if verbose:
        print(f"Exit code: {result.returncode}")
        print()
        if result.stdout:
            print("Stdout:")
            try:
                parsed = json.loads(result.stdout)
                if isinstance(parsed, dict):
                    context = parsed.get("hookSpecificOutput", {}).get("additionalContext", "")
                    print()
                    print(context)
                    print()
                else:
                    print(f"  {result.stdout}")
            except json.JSONDecodeError:
                print(f"  {result.stdout}")
        else:
            print("Stdout: (empty - no modifier matched)")
        if result.stderr:
            print(f"\nStderr:\n  {result.stderr}")
        print()

    # Parse response
    response = {}
    if result.stdout:
        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass

    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "response": response
    }


class TestServerHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves health checks and captures webhook requests."""
    received = []

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        TestServerHandler.received.append(json.loads(body.decode()))
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def _start_test_server(port: int) -> HTTPServer:
    """Start a test HTTP server and write a server.json port file for discovery."""
    server = HTTPServer(("127.0.0.1", port), TestServerHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    TestServerHandler.received.clear()

    # Write server.json so discover_flowpad() finds our test server
    from flowpad_discovery import get_flowpad_data_dir
    data_dir = get_flowpad_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    port_file = data_dir / "server.json"

    # Back up existing port file
    backup = None
    if port_file.exists():
        backup = port_file.read_text()

    port_file.write_text(json.dumps({
        "port": port,
        "webhook_path": "/api/v1/webhook/listen",
        "health_path": "/health",
    }))

    return server, port_file, backup


def _stop_test_server(server: HTTPServer, port_file: Path, backup: str | None) -> None:
    """Stop test server and restore the original port file."""
    server.shutdown()
    if backup is not None:
        port_file.write_text(backup)
    elif port_file.exists():
        port_file.unlink()


def test_notifications():
    """Test notify.py with a real test server and real discovery."""
    print("\n" + "=" * 60)
    print("NOTIFICATION TEST")
    print("=" * 60 + "\n")

    port = 18765
    server, port_file, backup = _start_test_server(port)
    print(f"Test server: http://127.0.0.1:{port}/webhook")

    try:
        # Run notification through real discovery pipeline
        result = subprocess.run(
            ["python", "-c", f"""
import sys; sys.path.insert(0, "{SCRIPT_DIR}")
import os
os.environ["FLOWPAD_EXECUTION_SCOPE"] = '[{{"type": "flow", "id": "test-123"}}]'

from notify import get_flowpad_status, send_skill_activation
from flowpad_discovery import FlowpadStatus

status = get_flowpad_status()
if status != FlowpadStatus.RUNNING:
    print("FAIL:flowpad_status=" + status)
    sys.exit(1)

success = send_skill_activation(
    skill_name="skillit",
    matched_keyword="test-keyword",
    prompt="test prompt",
    handler_name="test_handler",
    folder_path="/tmp/test"
)
print("QUEUED:" + str(success))
import time; time.sleep(0.5)
"""],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"stderr: {result.stderr[:200]}")
        time.sleep(0.3)

        if TestServerHandler.received:
            notif = TestServerHandler.received[0]["webhook_payload"]["notification"]
            print(f"✓ Notification received: skill={notif['skill_name']}, handler={notif['handler_name']}")
            passed = True
        else:
            print("✗ No notification received")
            passed = False
    finally:
        _stop_test_server(server, port_file, backup)

    print(f"\n>>> {'PASS' if passed else 'FAIL'}")


def test_with_transcript():
    """Test skillit with a real transcript file."""
    # Find the most recent transcript in the user's Claude projects directory
    claude_projects = Path.home() / ".claude" / "projects"
    transcripts = glob(str(claude_projects / "*" / "*.jsonl"))
    if not transcripts:
        print("No transcripts found!")
        return

    # Sort by modification time, get most recent
    transcripts.sort(key=os.path.getmtime, reverse=True)
    transcript_path = transcripts[0]

    print("\n" + "=" * 60)
    print("TESTING WITH REAL TRANSCRIPT")
    print("=" * 60)
    print(f"\nUsing: {transcript_path}")
    print(f"Size: {os.path.getsize(transcript_path)} bytes\n")

    # Read transcript content
    with open(transcript_path, "r") as f:
        transcript_content = f.read()

    invoke_main(f"{transcript_content}\n/skillit why is it slow?")


def test_activation_rules():
    """Test activation rules with a real test server and real discovery."""
    print("\n" + "=" * 60)
    print("ACTIVATION RULES TEST")
    print("=" * 60 + "\n")

    port = 18766
    server, port_file, backup = _start_test_server(port)
    print(f"Test server: http://127.0.0.1:{port}/webhook")

    try:
        # Test 1: No ad when server is running
        print("\nTest 1: No ad when Flowpad is running")
        print("-" * 40)

        result = subprocess.run(
            ["python", "-c", f"""
import sys; sys.path.insert(0, "{SCRIPT_DIR}")
from notify import get_flowpad_status
from flowpad_discovery import FlowpadStatus
from activation_rules import get_ad_if_needed

status = get_flowpad_status()
if status != FlowpadStatus.RUNNING:
    print("FAIL:flowpad_status=" + status)
    sys.exit(1)

ad = get_ad_if_needed()
print("AD_EMPTY:" + str(ad == ""))
"""],
            capture_output=True, text=True
        )
        test1_passed = "AD_EMPTY:True" in result.stdout
        print(f"{'✓' if test1_passed else '✗'} No ad returned when Flowpad is running")
        if result.stderr:
            print(f"  stderr: {result.stderr[:200]}")
        print(f">>> {'PASS' if test1_passed else 'FAIL'}\n")

        # Test 2: Activation event sent to server
        print("Test 2: Activation event sent to backend")
        print("-" * 40)

        TestServerHandler.received.clear()
        result = subprocess.run(
            ["python", "-c", f"""
import sys; sys.path.insert(0, "{SCRIPT_DIR}")
from notify import get_flowpad_status, send_skill_event
from flowpad_discovery import FlowpadStatus

status = get_flowpad_status()
if status != FlowpadStatus.RUNNING:
    print("FAIL:flowpad_status=" + status)
    sys.exit(1)

success = send_skill_event("skill_ready", {{"skill_name": "test-skill", "session_id": "test-123"}})
print("SENT:" + str(success))
import time; time.sleep(0.5)
"""],
            capture_output=True, text=True
        )
        time.sleep(0.3)

        if TestServerHandler.received:
            event = TestServerHandler.received[0]["webhook_payload"]["event"]
            test2_passed = event["type"] == "skill_ready"
            print(f"{'✓' if test2_passed else '✗'} Notification received: type={event['type']}")
        else:
            print("✗ No notification received")
            if result.stderr:
                print(f"  stderr: {result.stderr[:200]}")
            test2_passed = False
        print(f">>> {'PASS' if test2_passed else 'FAIL'}\n")

    finally:
        _stop_test_server(server, port_file, backup)

    # Summary
    all_passed = test1_passed and test2_passed
    print("=" * 60)
    print(f"ACTIVATION RULES: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 60)


def run_tests():
    """Run test suite."""
    # Test cases: (prompt, expected_modifier, expected_text_in_output)
    tests = [
        ("skillit", "analyze_and_create_activation_rules", "Create Activation Rule Skill"),
        ("skillit:test", "test", "Create Activation Rule Skill"),
        ("skillit create test for showing current time", "create_test", "Create Activation Rule Skill"),
        ("hello world", None, None),
    ]

    print("\n" + "=" * 60)
    print("TEST SUITE")
    print("=" * 60 + "\n")

    results = []
    for prompt, expected_modifier, expected_text in tests:
        reset_cooldown()  # Clear cooldown state before each test
        print(f"### Prompt: \"{prompt}\"")
        print(f"### Expected: {expected_modifier or 'no match'}\n")

        result = invoke_main(prompt, verbose=True)

        # Use stdout directly as the output to check
        output = result.get("stdout", "")

        if expected_text:
            passed = result["exit_code"] == 0 and expected_text in output
        else:
            passed = result["exit_code"] == 0 and not result["stdout"].strip()

        status = "PASS" if passed else "FAIL"
        results.append((prompt, expected_modifier, status))
        print(f">>> {status}")
        print("-" * 60 + "\n")

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for prompt, modifier, status in results:
        icon = "✓" if status == "PASS" else "✗"
        print(f"  {icon} \"{prompt}\" -> {modifier or 'none'} [{status}]")

    passed = sum(1 for _, _, s in results if s == "PASS")
    print(f"\n  {passed}/{len(results)} passed")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            run_tests()
            test_notifications()
            test_activation_rules()
        elif sys.argv[1] == "--transcript":
            test_with_transcript()
        elif sys.argv[1] == "--notify":
            test_notifications()
        elif sys.argv[1] == "--activation":
            test_activation_rules()
        else:
            invoke_main(" ".join(sys.argv[1:]))
    else:
        invoke_main("skillit:test")
