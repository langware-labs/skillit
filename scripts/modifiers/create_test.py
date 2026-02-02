"""
Create Test Modifier
Analyzes the conversation transcript to generate reproducible test steps as a skill.
Triggered by 'skillit create test' keyword.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from claude_utils import invoke_skill_creation, PLUGIN_DIR
from log import skill_log

INSTRUCTIONS_FILE = PLUGIN_DIR / "create_test_instructions.md"


def handle_create_test(prompt: str, data: dict) -> dict:
    """
    Handle the 'skillit create test' keyword.
    Delegates to a new Claude session to analyze transcript and create a skill.
    """
    transcript_path = data.get("transcript_path", "")
    cwd = data.get("cwd", "")
    session_id = data.get("session_id", "")

    skill_log(f"create_test: Processing transcript at {transcript_path}")

    result = invoke_skill_creation(INSTRUCTIONS_FILE, transcript_path, cwd, session_id)

    return {
        "continue": False,
        "stopReason": f"Creating skill in new Claude session.\nSkill session: {result.skill_session_id}\nSkills directory: {result.skills_dir}{result.ad}",
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"Creating skill.\nSkill session: {result.skill_session_id}\nSkills directory: {result.skills_dir}{result.ad}"
        }
    }
