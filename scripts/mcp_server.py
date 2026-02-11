#!/usr/bin/env python3
"""Skillit MCP Server — exposes tools for reporting and notifications."""
import sys
from pathlib import Path

from log import skill_log

sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
from notify import WebhookType, send_webhook_event, xml_str_to_flow_data_dict

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

    success = send_webhook_event(
        webhook_type=WebhookType.MCP_WEBHOOK,
        webhook_payload=flow_data,
        log_context=f"mcp_flow_tag={flow_data.get('element_type', 'unknown')}",
    )

    status = "sent" if success else "skipped (FlowPad unavailable)"
    return f"Flow tag {flow_data.get('element_type', 'unknown')}: {status}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
