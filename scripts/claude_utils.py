"""
Utility functions for building skill creation instructions.
"""
from pathlib import Path

# Path to the activation_rules.py script for callbacks
SCRIPTS_DIR = Path(__file__).parent.resolve()
PLUGIN_DIR = SCRIPTS_DIR.parent
ACTIVATION_RULES_SCRIPT = SCRIPTS_DIR / "activation_rules.py"


def get_skills_dir(cwd: str) -> Path:
    """Get the skills directory path for a given working directory."""
    return Path(cwd) / ".claude" / "skills"


def build_subagent_instructions(
    instructions_file: Path,
    skills_dir: Path,
    cwd: str,
) -> str:
    """
    Build instructions for Task subagent activation rules creation.

    Args:
        instructions_file: Path to the instructions .md file
        skills_dir: Path to the skills directory
        cwd: Working directory

    Returns:
        Instructions for activation rules creation
    """
    instructions_content = instructions_file.read_text()

    return f"""## Skillit: Create Activation Rule Skill

Launch a Task subagent to analyze this conversation and create activation rules.

### Use the Task tool with:
- subagent_type: "general-purpose"
- description: "Analyze conversation and create activation rules for Skillit skills."
- prompt: {instructions_content}

### Context Variables
- skills_dir: {skills_dir}
- session_id: Use ${{CLAUDE_SESSION_ID}} environment variable
- cwd: {cwd}
- activation_rules_script: {ACTIVATION_RULES_SCRIPT}

### After Task Completes
The activation rules will be created at {skills_dir}/<skill-name>/SKILL.md
You may use AskUserQuestion if clarification is needed.
"""
