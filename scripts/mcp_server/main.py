#!/usr/bin/env python3
"""Skillit MCP Server — exposes tools for reporting and notifications."""
import json
import sys
from pathlib import Path

# Add scripts/ to sys.path before any local imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.log import skill_log

from fastmcp import FastMCP
from network.notify import send_flow_tag, xml_str_to_flow_data_dict
from mcp_server import session_store, known_rules_store

mcp = FastMCP("skillit")

_STORES = {
    "known_rules": known_rules_store,
}
_DEFAULT_STORE = session_store


@mcp.tool()
def flow_entity_crud(claude_session_id: str, crud: str, entity_json: str) -> str:
    """Perform a CRUD operation on a flow entity record.

    Call this whenever you create, read, update, or delete a flow entity
    (skill, task, rule, artifact, session, etc.).

    Args:
        claude_session_id: The session ID (provided in context at session start).
        crud: The operation — "create", "read", "update", or "delete".
        entity_json: JSON string with at least a "type" field, plus "id" for
            read/update/delete.

    Returns:
        Result message string.
    """
    from plugin_records.skillit_records import skillit_records

    skill_log(f"MCP entity_crud: {crud} | session={claude_session_id}")
    if not claude_session_id:
        skill_log("MCP entity_crud ERROR: empty session ID")
        return "Error: session ID is required"
    session = skillit_records.get_session(claude_session_id)
    if session is None:
        # TODO - hack - fix this
        skill_log(f"MCP entity_crud: session {claude_session_id} not found, creating it")
        session = skillit_records.create_session(claude_session_id)
    skill_log(f"MCP entity_crud OK, session found: {claude_session_id}, output dir {session.output_dir}")
    try:
        entity_dict = json.loads(entity_json)
    except json.JSONDecodeError as e:
        skill_log(f"MCP entity_crud ERROR: invalid JSON for entity - {e} {entity_json}")
        return f"Error: invalid JSON — {e}"

    return skillit_records.entity_crud(
        session_id=claude_session_id,
        crud=crud,
        entity=entity_dict,
    )

@mcp.tool()
def flow_tag(flow_tag_xml: str, claude_session_id: str = None) -> str:
    """Call this whenever you encounter a <flow-[type]> tag in the flow XML. The outer xml of the tag will be passed as flow_tag_xml.

    Use this to report progress. Event types include:
    - started_generating_skill
    - skill_ready

    Args:
        flow_tag_xml: The outer XML string of the flow tag.
        claude_session_id: The session ID (provided in context at session start).

    Returns:
        Confirmation string with the received flow tag.
    """
    skill_log(f"MCP Received flow tag: {flow_tag_xml}")

    try:
        flow_data = xml_str_to_flow_data_dict(flow_tag_xml)
    except (ValueError, Exception) as e:
        skill_log(f"MCP flow tag parse error: {e}")
        return f"Error parsing flow tag: {e}"

    skill_log(f"MCP parsed flow data: {flow_data}")

    # Complete skill creation task when skill is ready
    element_type = flow_data.get('element_type', '')
    if element_type == 'skill_ready' and claude_session_id:
        from plugin_records.crud_handlers.skill_creation_handler import skill_creation_handler
        from plugin_records.skillit_records import skillit_records

        session = skillit_records.get_session(claude_session_id)
        if session:
            skill_creation_handler.on_update(
                claude_session_id, session, "skill", {"status": "new"}
            )

    success = send_flow_tag(flow_data)

    status = "sent" if success else "skipped (FlowPad unavailable)"
    return f"Flow tag {flow_data.get('element_type', 'unknown')}: {status}"


@mcp.tool()
def flow_context(claude_session_id: str, action: str, key: str, value: str = None) -> str:
    """Manage session-specific context storage using key-value pairs.

    This tool provides persistent storage for each session. All operations require
    the session_id to ensure data isolation between sessions.

    Args:
        claude_session_id: The session ID (provided in context at session start)
        action: Operation to perform - "get" or "set"
        key: The context key to get or set
        value: The value to set (required for "set" action, ignored for "get")

    Returns:
        For "get": The stored value or an error message if key not found
        For "set": Confirmation message

    Examples:
        flow_context(session_id="abc-123", action="set", key="theme", value="dark")
        flow_context(session_id="abc-123", action="get", key="theme")
    """
    if not claude_session_id:
        return "Error: session_id is required"
    if action not in ("get", "set"):
        return f"Error: action must be 'get' or 'set', got '{action}'"
    if not key:
        return "Error: key is required"
    if action == "set" and value is None:
        return "Error: value is required for 'set' action"

    store = _STORES.get(key, _DEFAULT_STORE)

    try:
        if action == "set":
            return store.set(claude_session_id, key, value)
        else:
            return store.get(claude_session_id, key)
    except Exception as e:
        skill_log(f"MCP ERROR: {action} context ERROR {e}")
        return f"Error {action}ing context: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
