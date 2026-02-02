"""
Test Modifier
Opens a persistent terminal window running Claude Code when 'skillit:test' is detected.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from claude_utils import invoke_skill_creation, PLUGIN_DIR

INSTRUCTIONS_FILE = PLUGIN_DIR / "analyze_transcript.md"


def handle_test(prompt: str, data: dict) -> dict:
    """
    Open a terminal window running Claude Code to analyze transcript and create a skill.
    """
    transcript_path = data.get("transcript_path", "")
    cwd = data.get("cwd", "")
    session_id = data.get("session_id", "")

    result = invoke_skill_creation(INSTRUCTIONS_FILE, transcript_path, cwd, session_id)

    return {
        "continue": False,
        "stopReason": f"Creating skill from transcript.\nSkill session: {result.skill_session_id}\nSkills directory: {result.skills_dir}{result.ad}",
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"skillit:test triggered - creating skill.\nSkill session: {result.skill_session_id}\nSkills directory: {result.skills_dir}{result.ad}"
        }
    }
