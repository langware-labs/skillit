"""
Test Modifier
Returns instructions for the current Claude session to launch a Task subagent
that analyzes the conversation and creates activation rules. Triggered by 'skillit:test'.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.claude_utils import (  # noqa: E402
    PLUGIN_DIR,
    build_subagent_instructions,
    get_skill_rules_dir,
)

INSTRUCTIONS_FILE = PLUGIN_DIR / "analyze_and_create_activation_rules.md"


def handle_test(prompt: str, data: dict) -> dict:
    """
    Return instructions for the current Claude session to launch a Task subagent
    that analyzes the conversation and creates activation rules.
    """
    cwd = data.get("cwd", "")
    skill_rules_dir = get_skill_rules_dir(cwd)

    return build_subagent_instructions(
        instructions_file=INSTRUCTIONS_FILE,
        cwd=cwd,
        target_dir=skill_rules_dir,
    )
