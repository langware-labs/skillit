#!/usr/bin/env python3
"""
Test Runner for Skillit Plugin
Invokes main.py exactly as Claude Code does - same command, env vars, and stdin format.

Usage:
    python3 test.py                     # Test with default "skillit:test"
    python3 test.py "skillit:test"      # Test with custom prompt
    python3 test.py --all               # Run full test suite
    python3 test.py --transcript        # Test with real transcript
    python3 test.py --notify            # Test notification module
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
HOOK_COMMAND = 'python3 "$CLAUDE_PLUGIN_ROOT/scripts/main.py"'


def invoke_main(prompt: str, transcript_path: str = None, verbose: bool = True) -> dict:
    """
    Invoke main.py exactly as Claude Code does.

    From hooks.json:
        "command": "python3 \"$CLAUDE_PLUGIN_ROOT/scripts/main.py\""

    Claude Code:
    1. Sets environment variables
    2. Runs the command through shell (for $CLAUDE_PLUGIN_ROOT expansion)
    3. Pipes JSON to stdin
    4. Reads JSON from stdout
    """

    # Generate session info like Claude Code does
    session_id = str(uuid.uuid4())

    # Use provided transcript path or generate a fake one
    if not transcript_path:
        transcript_path = f"/tmp/skillit-test/{session_id}.jsonl"

    # Build stdin payload - exact format from Claude Code logs
    stdin_payload = {
        "session_id": session_id,
        "transcript_path": transcript_path,
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
        print(f"  -> Expands to: python3 \"{PLUGIN_DIR}/scripts/main.py\"")
        print()
        print("Environment:")
        print(f"  CLAUDE_PLUGIN_ROOT={PLUGIN_DIR}")
        print(f"  CLAUDE_PROJECT_DIR={PLUGIN_DIR}")
        print()
        print(f"Transcript: {transcript_path}")
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
                context = parsed.get("hookSpecificOutput", {}).get("additionalContext", "")
                # Print context nicely formatted
                print()
                print(context)
                print()
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


class NotificationHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture notification requests."""
    received = []

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        NotificationHandler.received.append(json.loads(body.decode()))
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def test_notifications():
    """Test notify.py module with mock server or real backend."""
    print("\n" + "=" * 60)
    print("NOTIFICATION TEST")
    print("=" * 60 + "\n")

    env = os.environ.copy()
    use_mock = "AGENT_HOOKS_REPORT_URL" not in env

    # Start mock server only if no real URL provided
    server = None
    if use_mock:
        port = 18765
        server = HTTPServer(("127.0.0.1", port), NotificationHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        NotificationHandler.received.clear()
        env["AGENT_HOOKS_REPORT_URL"] = f"http://127.0.0.1:{port}/notify"
    if "FLOWPAD_EXECUTION_SCOPE" not in env:
        env["FLOWPAD_EXECUTION_SCOPE"] = json.dumps([{"type": "flow", "id": "test-123"}])

    print(f"Using: {env['AGENT_HOOKS_REPORT_URL']}")

    # Run notify.py directly
    cmd = f'python3 "{SCRIPT_DIR}/notify.py" "skillit" "test-keyword" "test prompt" "test_handler" "/tmp/test"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    print(result.stdout)
    time.sleep(0.3)

    if use_mock:
        if NotificationHandler.received:
            notif = NotificationHandler.received[0]["flow_value"]["notification"]
            print(f"✓ Notification received: skill={notif['skill_name']}, handler={notif['handler_name']}")
            passed = True
        else:
            print("✗ No notification received")
            passed = False
        server.shutdown()
        print(f"\n>>> {'PASS' if passed else 'FAIL'}")
    else:
        print("✓ Notification sent to real backend (check server logs)")
        print("\n>>> PASS")


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

    invoke_main("skillit why is it slow?", transcript_path=transcript_path)


def run_tests():
    """Run test suite."""
    tests = [
        ("skillit fix bug", "fixing", "Opened new Claude terminal"),
        ("skillit:test", "test", "skillit:test triggered"),
        ("skillit create test for showing current time", "create_test", "Creating test skill"),
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

        context = result.get("response", {}).get("hookSpecificOutput", {}).get("additionalContext", "")

        if expected_text:
            passed = result["exit_code"] == 0 and expected_text in context
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
        elif sys.argv[1] == "--transcript":
            test_with_transcript()
        elif sys.argv[1] == "--notify":
            test_notifications()
        else:
            invoke_main(" ".join(sys.argv[1:]))
    else:
        invoke_main("skillit:test")
