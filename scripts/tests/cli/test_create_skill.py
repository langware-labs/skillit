"""CLI test: run /skillit:create-skill and verify skill is created and copied to ~/.claude/skills/."""

from pathlib import Path

from utils.log import skill_log_print, skill_log_clear
from plugin_records.skillit_records import skillit_records
from tests.test_utils import TestPluginProjectEnvironment, LaunchMode, make_env


def test_create_skill_cli():
    """Run /skillit:create-skill via claude -p and verify the skill lands in ~/.claude/skills/.

    This test exercises the full end-to-end flow:
    1. Claude receives the /skillit:create-skill command
    2. The skillit-creator agent analyzes the request
    3. The agent calls flow_entity_crud MCP to create the skill entity
    4. The agent copies the skill template to the session output dir and fills it in
    5. The agent signals completion via flow_tag (skill_ready)
    6. skill_creation_handler.on_update copies the skill to ~/.claude/skills/
    """
    env = make_env()
    env.install_plugin()
    env.loadMcp()
    skill_log_clear()

    prompt = "/skillit:create-skill use acli to handle jira related stuff"
    result = env.prompt(prompt, timeout=600)
    assert result.returncode == 0

    skill_log = result.skill_log
    skill_log_print()

    # --- (1) Verify a skill was created ---
    # The MCP entity_crud create should have been called
    assert "entity_crud" in skill_log, (
        f"MCP entity_crud was not called. skill.log:\n{skill_log}"
    )

    # The session should exist
    session = skillit_records.get_session(env.session_id)
    assert session is not None, "Session should have been created"

    # The session output dir should contain at least one skill folder with SKILL.md
    output_dir = session.output_dir
    skill_folders = [
        d for d in output_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    ]
    assert len(skill_folders) > 0, (
        f"No skill folders found in output dir {output_dir}. "
        f"Contents: {list(output_dir.iterdir()) if output_dir.exists() else 'dir missing'}"
    )

    created_skill_name = skill_folders[0].name
    print(f"Skill created: {created_skill_name}")
    print(f"Skill folder: {skill_folders[0]}")

    # --- (2) Verify the skill is available in ~/.claude/skills/ ---
    claude_skills_dir = Path.home() / ".claude" / "skills"
    user_skill_dir = claude_skills_dir / created_skill_name

    assert user_skill_dir.exists(), (
        f"Skill '{created_skill_name}' not found in {claude_skills_dir}. "
        f"Available skills: {list(claude_skills_dir.iterdir()) if claude_skills_dir.exists() else 'dir missing'}. "
        f"skill.log:\n{skill_log}"
    )
    assert (user_skill_dir / "SKILL.md").exists(), (
        f"SKILL.md missing from {user_skill_dir}"
    )

    print(f"Skill available at: {user_skill_dir}")
    print(f"SKILL.md content preview:")
    print((user_skill_dir / "SKILL.md").read_text()[:500])
