"""Minimal test to verify MCP server connectivity."""
import subprocess
import time
from pathlib import Path
from tests.test_utils import make_env, LaunchMode

DEBUG_FILE = Path(__file__).parent / "mcp_debug.log"


def test_mcp_connect():
    """Headless test — call flow_ping and verify result."""
    env = make_env()
    env.install_plugin()

    cmd = [
        "claude", "-p", "call the flow_ping tool and return its result",
        "--dangerously-skip-permissions",
        "--debug-file", str(DEBUG_FILE),
        *env._session_args(),
    ]
    if env._mcp_config_path:
        cmd.extend(["--mcp-config", str(env._mcp_config_path)])

    print(f"\nRunning: {' '.join(cmd)}")
    print(f"CWD: {env.temp_dir}")

    result = subprocess.run(
        cmd,
        cwd=str(env.temp_dir),
        capture_output=True,
        text=True,
        timeout=60,
        env=env._build_env(),
    )

    print(f"\nExit code: {result.returncode}")
    print(f"Stdout: {result.stdout[:2000]}")
    if result.stderr:
        print(f"Stderr: {result.stderr[:2000]}")

    _print_mcp_lines()


def test_mcp_interactive():
    """Interactive launch with 30s timeout and debug file."""
    env = make_env()
    env.install_plugin()

    debug_file = Path(__file__).parent / "mcp_interactive_debug.log"
    debug_file.unlink(missing_ok=True)

    prompt = "say hi and list all available MCP tools"

    cmd = [
        "claude", "-p", prompt,
        "--dangerously-skip-permissions",
        "--debug-file", str(debug_file),
        *env._session_args(),
    ]

    print(f"\nRunning: {' '.join(cmd)}")
    print(f"CWD: {env.temp_dir}")

    proc = subprocess.Popen(
        cmd,
        cwd=str(env.temp_dir),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env._build_env(),
    )

    stdout_parts = []
    deadline = time.monotonic() + 30

    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                proc.kill()
                proc.wait()
                print("\n[TIMED OUT after 30s]")
                break
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if line:
                stdout_parts.append(line)
                print(line, end="")
    except Exception as e:
        proc.kill()
        print(f"\nError: {e}")

    print(f"\nExit code: {proc.returncode}")
    print(f"Stdout: {''.join(stdout_parts)[:2000]}")

    if debug_file.exists():
        debug_text = debug_file.read_text()
        mcp_lines = [l for l in debug_text.splitlines() if "MCP" in l or "mcp" in l.lower()]
        print(f"\n--- MCP debug lines ({len(mcp_lines)}) ---")
        for line in mcp_lines[:50]:
            print(line)
    else:
        print("\nNo debug file created")


def _print_mcp_lines():
    if DEBUG_FILE.exists():
        debug_text = DEBUG_FILE.read_text()
        mcp_lines = [l for l in debug_text.splitlines() if "MCP" in l or "mcp" in l.lower()]
        print(f"\n--- MCP debug lines ({len(mcp_lines)}) ---")
        for line in mcp_lines[:50]:
            print(line)
    else:
        print("\nNo debug file created")
