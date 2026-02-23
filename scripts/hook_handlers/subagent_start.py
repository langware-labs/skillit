"""SubagentStart hook handler — set flag when skillit-creator starts."""

from utils.conf import SKILLIT_HOME
from utils.log import skill_log

ACTIVE_FLAG = SKILLIT_HOME / "creator_active"


def handle(data: dict, rules_output: dict) -> dict | None:
    """Handle SubagentStart — write flag file so PermissionRequest hook can auto-allow."""
    agent_type = data.get("agent_type", "")
    skill_log(f"subagent_start: agent_type={agent_type}")

    if agent_type != "skillit:skillit-creator":
        skill_log(f"subagent_start: ignoring agent_type={agent_type!r}, not skillit-creator")
        return rules_output or None

    session_id = data.get("session_id", "")
    SKILLIT_HOME.mkdir(parents=True, exist_ok=True)
    ACTIVE_FLAG.write_text(session_id, encoding="utf-8")
    skill_log(f"subagent_start: creator_active flag set for session {session_id}")

    return rules_output or None
