"""
Fixing Modifier
Opens a new Claude Code terminal to analyze the current session transcript and create a skill.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from claude_utils import invoke_skill_creation, PLUGIN_DIR  # noqa: E402

INSTRUCTIONS_FILE = PLUGIN_DIR / "analyze_transcript.md"


def handle_analyze(prompt: str, data: dict) -> dict:
    """
    Open a new Claude Code terminal to analyze the current session transcript and create a skill.

    The hook input data contains:
    - session_id: Current session UUID
    - transcript_path: Full path to the session's JSONL transcript file
    - cwd: Current working directory
    """
    transcript_path = data.get("transcript_path", "")
    cwd = data.get("cwd", "")
    session_id = data.get("session_id", "")

    result = invoke_skill_creation(INSTRUCTIONS_FILE, transcript_path, cwd, session_id)

    return {
        "continue": False,
        "stopReason": f"Creating skill from transcript analysis.\nSkill session: {result.skill_session_id}\nSkills directory: {result.skills_dir}{result.ad}",
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"Creating skill from transcript.\nSkill session: {result.skill_session_id}\nSkills directory: {result.skills_dir}{result.ad}"
        }
    }
