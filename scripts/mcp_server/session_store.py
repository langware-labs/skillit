"""Session store — get/set context on the SkillitSession record."""

from utils.log import skill_log


def _get_session(claude_session_id: str):
    from plugin_records.skillit_records import skillit_records
    session = skillit_records.get_session(claude_session_id)
    if session is None:
        session = skillit_records.create_session(claude_session_id)
    return session


def get(claude_session_id: str, key: str) -> str:
    session = _get_session(claude_session_id)
    skill_log(f"MCP: Getting context for session {claude_session_id}: {key}")
    if key not in session:
        skill_log(f"MCP: Get context key '{key}' not found")
        return f"Key '{key}' not found in session context"
    val = str(session[key])
    skill_log(f"MCP: Get context read record key:{key}, value: {val}")
    return val


def set(claude_session_id: str, key: str, value: str) -> str:
    session = _get_session(claude_session_id)
    skill_log(f"MCP: Setting context for session {claude_session_id}: {key} = {value}")
    session[key] = value
    session.save()
    skill_log(f"MCP: Set context with {value}")
    return f"Context set: {key} = {value}"
