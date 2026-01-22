"""
Test Modifier
Opens a persistent terminal window running Claude Code when 'skillit:test' is detected.
"""
import subprocess
import platform
import shlex
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PLUGIN_DIR = SCRIPT_DIR.parent.parent
INSTRUCTIONS_FILE = PLUGIN_DIR / "analyze_transcript.md"


def invoke_claude(prompt: str) -> None:
    """
    Open a persistent terminal window and run Claude Code with the given prompt.

    Args:
        prompt: The prompt to send to Claude Code
    """
    system = platform.system()
    escaped_prompt = shlex.quote(prompt)

    if system == "Darwin":  # macOS
        script = f'''
        tell application "Terminal"
            activate
            do script "clear; claude {escaped_prompt}"
        end tell
        '''
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

    elif system == "Linux":
        cmd = f"clear; claude {escaped_prompt}; exec bash"
        terminals = [
            ["gnome-terminal", "--", "bash", "-c", cmd],
            ["xterm", "-e", f"bash -c '{cmd}'"],
            ["konsole", "-e", "bash", "-c", cmd],
        ]
        for term_cmd in terminals:
            try:
                subprocess.Popen(
                    term_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                break
            except FileNotFoundError:
                continue

    elif system == "Windows":
        subprocess.Popen(
            ["cmd", "/k", f"cls && claude {escaped_prompt}"],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            start_new_session=True
        )


def handle_test(prompt: str, data: dict) -> dict:
    """
    Open a terminal window running Claude Code with instructions from skillit.md.
    """
    instructions_path = str(INSTRUCTIONS_FILE)
    invoke_claude(f"run the instructions at {instructions_path}")

    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"skillit:test triggered - opened Claude to run instructions from {instructions_path}"
        }
    }
