#!/usr/bin/env python3
"""Skillit MCP Server — exposes tools for reporting and notifications."""
import sys
from pathlib import Path

from log import skill_log

sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
from notify import send_flow_tag, xml_str_to_flow_data_dict
from conf import get_session_dir
from fs_store import FsRecord

mcp = FastMCP("skillit")

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
def flow_context(session_id: str, action: str, key: str, value: str = None) -> str:
    """Manage session-specific context storage using key-value pairs.

    This tool provides persistent storage for each session. All operations require
    the session_id to ensure data isolation between sessions.

    Args:
        session_id: The session ID (provided in context at session start)
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
    # Validate inputs
    if not session_id:
        return "Error: session_id is required"

    if action not in ("get", "set"):
        return f"Error: action must be 'get' or 'set', got '{action}'"

    if not key:
        return "Error: key is required"

    # Get session directory and initialize store
    try:
        session_dir = get_session_dir(session_id)
        store_path = session_dir / "record.json"
        store = FsRecord.from_json(store_path)
    except Exception as e:
        return f"Error initializing context store: {e}"

    # Perform action
    if action == "set":
        if value is None:
            return "Error: value is required for 'set' action"
        try:
            store[key] = value
            store.persist()
            return f"Context set: {key} = {value}"
        except Exception as e:
            return f"Error setting context: {e}"

    else:  # action == "get"
        try:
            if key not in store:
                return f"Key '{key}' not found in session context"
            return str(store[key])
        except Exception as e:
            return f"Error getting context: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
