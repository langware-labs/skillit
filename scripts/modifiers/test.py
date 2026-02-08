"""
Test Modifier
Returns instructions for the current Claude session to launch a Task subagent
that analyzes the conversation and creates activation rules. Triggered by 'skillit:test'.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from claude_utils import (  # noqa: E402
    PLUGIN_DIR,
    build_subagent_instructions,
    get_skills_dir,
)

INSTRUCTIONS_FILE = PLUGIN_DIR / "analyze_transcript.md"


def handle_test(prompt: str, data: dict) -> dict:
    """
    Return instructions for the current Claude session to launch a Task subagent
    that analyzes the conversation and creates activation rules.
    """
    cwd = data.get("cwd", "")
    skills_dir = get_skills_dir(cwd)

    return build_subagent_instructions(
        instructions_file=INSTRUCTIONS_FILE,
        skills_dir=skills_dir,
        cwd=cwd,
    )
