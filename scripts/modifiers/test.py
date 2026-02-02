"""
Test Modifier
Opens a persistent terminal window running Claude Code when 'skillit:test' is detected.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from claude_utils import invoke_claude

SCRIPT_DIR = Path(__file__).parent.resolve()
PLUGIN_DIR = SCRIPT_DIR.parent.parent
INSTRUCTIONS_FILE = PLUGIN_DIR / "analyze_transcript.md"


def handle_test(prompt: str, data: dict) -> dict:
    """
    Open a terminal window running Claude Code with instructions from skillit.md.
    """
    instructions_path = str(INSTRUCTIONS_FILE)
    invoke_claude(f"run the instructions at {instructions_path}")

    return {
        "continue": False,
        "stopReason": f"Opened new Claude session to run instructions from {instructions_path}",
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"skillit:test triggered - opened Claude to run instructions from {instructions_path}"
        }
    }
