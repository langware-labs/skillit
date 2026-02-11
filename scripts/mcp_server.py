#!/usr/bin/env python3
"""Skillit MCP Server — exposes tools for reporting and notifications."""
import datetime
import sys
from pathlib import Path

from log import skill_log

sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
from notify import send_activation_event

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
    start_time = datetime.datetime.now()

    success = send_activation_event("mcp_notification", flow_tag_xml)
    #duration_ms = (datetime.datetime.now() - start_time).total_seconds() * 1000
    #result = f"Time {duration_ms:.0f}ms : Emitted event '{event_type}' with context {context}" if success else f"Failed to emit event '{event_type}' (FlowPad unavailable)"
    result = f"Received flow tag: {flow_tag_xml}"

    return result

if __name__ == "__main__":
    mcp.run(transport="stdio")
