"""
Create Test Modifier
Returns instructions for the current Claude session to launch a Task subagent
that analyzes the conversation and generates reproducible test steps as a skill.
Triggered by 'skillit create test' keyword.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from claude_utils import (  # noqa: E402
    build_subagent_instructions,
    get_skills_dir,
    PLUGIN_DIR,
)
from log import skill_log

INSTRUCTIONS_FILE = PLUGIN_DIR / "create_test_instructions.md"


def handle_create_test(prompt: str, data: dict) -> dict:
    """
    Handle the 'skillit:create-test' keyword.
    Returns instructions for the current Claude session to launch a Task subagent
    that analyzes the conversation and creates activation rules.
    """
    cwd = data.get("cwd", "")
    skill_log(f"create_test: Preparing subagent instructions for cwd={cwd}")

    skills_dir = get_skills_dir(cwd)

    instructions = build_subagent_instructions(
        instructions_file=INSTRUCTIONS_FILE,
        skills_dir=skills_dir,
        cwd=cwd,
    )

    return instructions
