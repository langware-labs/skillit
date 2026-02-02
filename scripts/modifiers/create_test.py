"""
Create Test Modifier
Analyzes the conversation transcript to generate reproducible test steps as a skill.
Triggered by 'skillit create test' keyword.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from claude_utils import invoke_claude
from log import skill_log

SCRIPT_DIR = Path(__file__).parent.resolve()
PLUGIN_DIR = SCRIPT_DIR.parent.parent
INSTRUCTIONS_FILE = PLUGIN_DIR / "create_test_instructions.md"


def handle_create_test(prompt: str, data: dict) -> dict:
    """
    Handle the 'skillit create test' keyword.
    Delegates to a new Claude session to analyze transcript and create a skill.
    """
    transcript_path = data.get("transcript_path", "")
    cwd = data.get("cwd", "")

    skill_log(f"create_test: Processing transcript at {transcript_path}")

    instructions_path = str(INSTRUCTIONS_FILE)
    skills_dir = Path(cwd) / ".claude" / "skills"

    # Build the prompt for Claude to analyze transcript and create the skill
    analysis_prompt = (
        f"Run the instructions at {instructions_path} with:\n"
        f"- transcript_path: {transcript_path}\n"
        f"- skills_dir: {skills_dir}\n"
        f"- cwd: {cwd}"
    )

    # Open new terminal with Claude to analyze and create the skill
    invoke_claude(analysis_prompt, working_dir=cwd)

    return {
        "continue": False,
        "stopReason": f"Creating test skill in new Claude session.\nSkills directory: {skills_dir}",
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"Creating test skill.\nSkills directory: {skills_dir}"
        }
    }
