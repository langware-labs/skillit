"""
Utility functions for invoking Claude Code from Python scripts.
"""
import platform
import shlex
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from activation_rules import get_ad_if_needed

# Path to the activation_rules.py script for callbacks
SCRIPTS_DIR = Path(__file__).parent.resolve()
PLUGIN_DIR = SCRIPTS_DIR.parent
ACTIVATION_RULES_SCRIPT = SCRIPTS_DIR / "activation_rules.py"


@dataclass
class SkillCreationResult:
    """Result of invoking skill creation."""
    skills_dir: Path
    skill_session_id: str  # Unique ID for this skill creation session
    ad: str  # Empty if activation_rules is available, ad text otherwise


def get_skills_dir(cwd: str) -> Path:
    """Get the skills directory path for a given working directory."""
    return Path(cwd) / ".claude" / "skills"


def generate_skill_session_id() -> str:
    """Generate a unique session ID for skill creation tracking."""
    return str(uuid.uuid4())


def invoke_skill_creation(
    instructions_file: Path,
    transcript_path: str,
    cwd: str,
    parent_session_id: str = "",
) -> SkillCreationResult:
    """
    Invoke Claude to create a skill based on instructions and transcript.

    Claude will:
    1. Analyze the transcript and determine a meaningful skill name
    2. Call activation_rules.py to report started_generating_skill
    3. Create the skill file
    4. Call activation_rules.py to report skill_ready

    Args:
        instructions_file: Path to the instructions .md file
        transcript_path: Path to the transcript JSONL file
        cwd: Working directory where .claude/skills/ will be created
        parent_session_id: Session ID of the parent Claude session

    Returns:
        SkillCreationResult with skills_dir, skill_session_id, and ad
    """
    skills_dir = get_skills_dir(cwd)

    # Generate a unique ID for this skill creation session
    skill_session_id = generate_skill_session_id()

    # Build the prompt for Claude to analyze transcript and create the skill
    # Claude will determine the skill_name and handle reporting using skill_session_id
    analysis_prompt = (
        f"Run the instructions at {instructions_file} with:\n"
        f"- transcript_path: {transcript_path}\n"
        f"- skills_dir: {skills_dir}\n"
        f"- activation_rules_script: {ACTIVATION_RULES_SCRIPT}\n"
        f"- skill_session_id: {skill_session_id}\n"
        f"- parent_session_id: {parent_session_id}\n"
        f"- cwd: {cwd}"
    )

    invoke_claude(analysis_prompt, skill_session_id=skill_session_id, working_dir=cwd)

    return SkillCreationResult(
        skills_dir=skills_dir,
        skill_session_id=skill_session_id,
        ad=get_ad_if_needed(),
    )


def invoke_claude(prompt: str, skill_session_id: str = None, working_dir: str = None) -> None:
    """
    Open a new terminal tab and run Claude Code with the given prompt.
    Claude is expected to handle reporting via activation_rules.py directly.

    Args:
        prompt: The prompt to pass to Claude Code
        skill_session_id: Unique ID for this skill creation session
        working_dir: Optional working directory to change to before running
    """
    system = platform.system()
    escaped_prompt = shlex.quote(prompt)

    claude_cmd = f"claude --session-id {skill_session_id} --dangerously-skip-permissions --chrome {escaped_prompt}"
    if working_dir:
        base_cmd = f"cd {shlex.quote(working_dir)} && clear && {claude_cmd}"
    else:
        base_cmd = f"clear && {claude_cmd}"

    # No automatic callback - Claude will handle reporting via activation_rules.py
    cmd = base_cmd

    if system == "Darwin":  # macOS - open in new tab
        script = f'''
        tell application "Terminal"
            activate
            tell application "System Events" to keystroke "t" using command down
            delay 0.2
            do script "{cmd}" in front window
        end tell
        '''
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

    elif system == "Linux":
        # Try to open in a new tab where supported
        terminals = [
            ["gnome-terminal", "--tab", "--", "bash", "-c", f"{cmd}; exec bash"],
            ["xterm", "-e", f"bash -c '{cmd}; exec bash'"],
            ["konsole", "--new-tab", "-e", "bash", "-c", f"{cmd}; exec bash"],
        ]
        for term_cmd in terminals:
            try:
                subprocess.Popen(
                    term_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                break
            except FileNotFoundError:
                continue

    elif system == "Windows":
        # Windows Terminal supports tabs with wt command
        wt_cmd = f'wt new-tab cmd /k "{cmd.replace("clear", "cls")}"'
        try:
            subprocess.Popen(
                wt_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        except FileNotFoundError:
            # Fall back to regular cmd if Windows Terminal not available
            subprocess.Popen(
                ["cmd", "/k", cmd.replace("clear", "cls")],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                start_new_session=True
            )
