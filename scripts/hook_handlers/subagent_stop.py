"""SubagentStop hook handler — trigger skill installation when a skillit agent finishes."""

from pathlib import Path

from fs_store import ResourceStatus
from fs_store.record_types import RecordType
from plugin_records.crud_handlers.skill_creation_handler import SkillCreationHandler
from plugin_records.skillit_records import skillit_records
from utils.log import skill_log


def _get_ready_skill_folders(output_dir: Path) -> list[str]:
    """Return folder names of ready skills (directories containing SKILL.md)."""
    if not output_dir.exists():
        return []
    return [
        child.name
        for child in output_dir.iterdir()
        if child.is_dir() and (child / "SKILL.md").exists()
    ]


def handle(data: dict, rules_output: dict) -> dict | None:
    """Handle SubagentStop — delegate to SkillCreationHandler.on_update to install skills."""
    agent_type = data.get("agent_type", "")
    skill_log(f"subagent_stop: agent_type={agent_type}")

    if agent_type != "skillit:skillit-creator":
        skill_log(f"subagent_stop: ignoring agent_type={agent_type!r}, not skillit-creator")
        return rules_output or None

    session_id = data.get("session_id", "")
    if not session_id:
        skill_log("subagent_stop: no session_id, skipping")
        return rules_output or None

    session = skillit_records.get_session(session_id)
    if session is None:
        skill_log(f"subagent_stop: session {session_id} not found, skipping")
        return rules_output or None

    output_dir = session.output_dir
    skill_folders = _get_ready_skill_folders(output_dir)
    if not skill_folders:
        skill_log(f"subagent_stop: no ready skills in {output_dir}, skipping (agent likely still in progress)")
        return rules_output or None

    for folder_name in skill_folders:
        entity = {"type": RecordType.SKILL, "status": ResourceStatus.NEW, "folder_name": folder_name}
        SkillCreationHandler.on_update(session_id, session, RecordType.SKILL, entity)

    return rules_output or None
