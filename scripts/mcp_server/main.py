#!/usr/bin/env python3
"""Skillit MCP Server — exposes tools for reporting and notifications."""
import json
import sys
from pathlib import Path

from fs_store import FsRecord
from mcp_server.session_store import get_session_record
from utils.log import skill_log

sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
from network.notify import send_flow_tag, xml_str_to_flow_data_dict
from mcp_server import session_store, known_rules_store

mcp = FastMCP("skillit")

_STORES = {
    "known_rules": known_rules_store,
}
_DEFAULT_STORE = session_store


@mcp.tool()
def flow_entity_crud(claude_session_id, crud: str, entity_json: str,record_path:str) -> str:
    session = get_session_record(claude_session_id)
    entity = json.loads(entity_json)
    record_type = entity.get("type", None)
    record_class = FsRecord.get_class()
    record = record_class(path)
    if crud == "create":
        record.update_from_dict(entity)
        record.save()
        session.add_child_ref(record)
        session.save()
        return f"Created {record_type} record with path {record.path}"
    elif crud == "update":
        if not record.path:
            return f"Error: record_path is required for update"
        if not Path(record.path).exists():
            return f"Error: record_path {record.path} does not exist for update"
        record.update_from_dict(entity)
        record.save()
        return f"Updated {record_type} record at path {record.path}"
    elif crud == "delete":
        if not record.path:
            return f"Error: record_path is required for delete"
        if not Path(record.path).exists():
            return f"Error: record_path {record.path} does not exist for delete"
        Path(record.path).unlink()
        session.remove_child_ref(record)
        session.save()
        return f"Deleted {record_type} record at path {record.path}"
    else:
        return f"Error: unknown CRUD operation '{crud}'"

@mcp.tool()
def flow_tag(flow_tag_xml: str) -> str:
    """Call this whenever you encounter a <flow-[type]> tag in the flow XML. The outer xml of the tag will be passed as flow_tag_xml.

    Use this to report progress. Event types include:
    - started_generating_skill
    - skill_ready

    Args:
        flow_tag_xml: The outer XML string of the flow tag.

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
