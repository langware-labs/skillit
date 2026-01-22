"""
Fixing Modifier
Opens a new Claude Code terminal to analyze the current session transcript.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from claude_utils import invoke_claude

SCRIPT_DIR = Path(__file__).parent.resolve()
PLUGIN_DIR = SCRIPT_DIR.parent.parent
INSTRUCTIONS_FILE = PLUGIN_DIR / "analyze_transcript.md"


def handle_analyze(prompt: str, data: dict) -> dict:
    """
    Open a new Claude Code terminal to analyze the current session transcript.

    The hook input data contains:
    - session_id: Current session UUID
    - transcript_path: Full path to the session's JSONL transcript file
    - cwd: Current working directory
    """
    session_id = data.get("session_id", "unknown")
    transcript_path = data.get("transcript_path", "")
    cwd = data.get("cwd", "")

    instructions_path = str(INSTRUCTIONS_FILE)

    # Build the prompt to run instructions with transcript as input
    analysis_prompt = f"run the instructions at {instructions_path} with the transcript file {transcript_path} as input"

    # Open new terminal with Claude to analyze, in the same working directory
    invoke_claude(analysis_prompt, working_dir=cwd)

    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"Opened new Claude terminal.\nInstructions: {instructions_path}\nTranscript: {transcript_path}"
        }
    }
