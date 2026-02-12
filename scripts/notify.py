#!/usr/bin/env python3
"""
Skillit - Notification Module
Single gateway for all FlowPad server communication.

Handles service discovery, webhook sending, and rate limiting.
All other modules should go through notify.py for server interaction.
"""

import html
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Optional

from flowpad_discovery import (
    FlowpadStatus,  # re-exported for consumers (e.g., activation_rules)
    discover_flowpad,
    is_webhook_rate_limited,
    record_webhook_failure,
)
from log import skill_log


class WebhookType(StrEnum):
    SKILL_NOTIFICATION = "skill_notification"
    SKILLIT_LOG = "skillit_log"
    ACTIVATION_RULES = "activation_rules"
    AGENT_HOOK = "agent_hook"
    INSTRUCTION_TRACE = "instruction_trace"
    MCP_WEBHOOK = "mcp_webhook"


@dataclass
class SkillNotification:
    """Skill notification payload."""

    skill_name: str
    matched_keyword: str
    prompt: str
    handler_name: str
    folder_path: str  # Working directory where skill output is generated


# ---------------------------------------------------------------------------
# Service discovery
# ---------------------------------------------------------------------------

def get_flowpad_status() -> str:
    """Get current Flowpad status.

    Returns:
        One of FlowpadStatus constants: RUNNING, INSTALLED_NOT_RUNNING, NOT_INSTALLED.
    """
    return discover_flowpad().status


def _get_report_url() -> Optional[str]:
    """Discover Flowpad server and return webhook URL.

    Returns:
        Webhook URL if Flowpad is running, None otherwise.
    """
    result = discover_flowpad()
    if result.status == FlowpadStatus.RUNNING and result.server_info:
        return result.server_info.url
    return None


# ---------------------------------------------------------------------------
# Low-level transport
# ---------------------------------------------------------------------------

def _send_fire_and_forget(url: str, data: bytes, log_context: str) -> None:
    """Send HTTP POST in a detached subprocess that survives parent exit."""
    script = (
        "import urllib.request, sys; "
        "req = urllib.request.Request(sys.argv[1], data=sys.stdin.buffer.read(), "
        "headers={'Content-Type': 'application/json'}, method='POST'); "
        "urllib.request.urlopen(req, timeout=10)"
    )
    try:
        proc = subprocess.Popen(
            [sys.executable, "-c", script, url],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        proc.stdin.write(data)
        proc.stdin.close()
        skill_log(f"Notification dispatched to {url}:\n {log_context}")
    except Exception as e:
        skill_log(f"Failed to dispatch notification: {e}")
        record_webhook_failure()


# ---------------------------------------------------------------------------
# Generic webhook sender
# ---------------------------------------------------------------------------

def _get_execution_scope() -> list:
    """Parse FLOWPAD_EXECUTION_SCOPE from environment."""
    execution_scope = os.environ.get("FLOWPAD_EXECUTION_SCOPE")
    try:
        return json.loads(execution_scope) if execution_scope else []
    except json.JSONDecodeError:
        return []


def xml_str_to_flow_data_dict(xml_str: str) -> dict:
    """Parse a flow-* XML string into a flow-data-compatible dict.

    Extracts minimal fields: element_type, index, created_time, data_type, flow_value.

    Example:
        xml_str_to_flow_data_dict('<flow-chat i="5" t="2026-01-01" data-type="string">Hello</flow-chat>')
        # {"element_type": "chat", "index": 5, "created_time": "2026-01-01",
        #  "data_type": "string", "flow_value": "Hello"}

    Args:
        xml_str: XML string like '<flow-{type} attr="val">content</flow-{type}>'

    Returns:
        Dict with element_type, data_type, flow_value, and optional index/created_time.

    Raises:
        ValueError: If xml_str contains no flow-* element.
    """
    root = ET.fromstring(xml_str)
    tag = root.tag

    if not tag.startswith("flow-"):
        raise ValueError(f"Expected a flow-* element, got <{tag}>")

    element_type = tag[5:]

    attribs = dict(root.attrib)
    data_type = attribs.get("data-type", "string")

    # Content is the text inside the element
    content = root.text or ""

    # Parse flow_value based on data_type
    if data_type in ("object", "json", "entity") and content.strip():
        try:
            flow_value = json.loads(html.unescape(content))
        except (json.JSONDecodeError, ValueError):
            flow_value = html.unescape(content)
    else:
        flow_value = html.unescape(content) if content else ""

    result = {
        "element_type": element_type,
        "data_type": data_type,
        "flow_value": flow_value,
    }

    if "i" in attribs:
        result["index"] = int(attribs["i"])
    if "t" in attribs:
        result["created_time"] = attribs["t"]

    return result


def send_webhook_event(webhook_type: WebhookType, webhook_payload: dict | str, log_context: str) -> bool:
    """Send a webhook to FlowPad (fire-and-forget).

    Handles discovery, rate limiting, and envelope wrapping.

    Args:
        webhook_type: A WebhookType enum value.
        webhook_payload: Type-specific payload dict.
        log_context: Context string for logging.

    Returns:
        True if notification was queued, False if skipped.
    """
    if is_webhook_rate_limited():
        skill_log(f"Notification skipped: rate-limited ({log_context})")
        return False

    report_url = _get_report_url()
    print(f"[notify] webhook url: {report_url} | type: {webhook_type} | {log_context}")
    if not report_url:
        skill_log(f"Notification skipped: Flowpad not running ({log_context})")
        return False

    payload = {
        "webhook_type": webhook_type,
        "webhook_payload": webhook_payload,
    }

    data = json.dumps(payload).encode("utf-8")

    _send_fire_and_forget(report_url, data, log_context)
    return True


# ---------------------------------------------------------------------------
# Typed convenience senders
# ---------------------------------------------------------------------------

def send_skill_notification(
    skill_name: str,
    matched_keyword: str,
    prompt: str,
    handler_name: str,
    folder_path: str,
) -> bool:
    """Send skill activation notification to FlowPad (fire-and-forget).

    Args:
        skill_name: Name of the skill being invoked
        matched_keyword: The keyword that triggered the skill
        prompt: The user prompt that triggered activation
        handler_name: Name of the handler function being called
        folder_path: Working directory where skill output is generated

    Returns:
        True if notification was queued, False if Flowpad not running
    """
    notification = SkillNotification(
        skill_name=skill_name,
        matched_keyword=matched_keyword,
        prompt=prompt,
        handler_name=handler_name,
        folder_path=folder_path,
    )
    return send_webhook_event(
        webhook_type=WebhookType.SKILL_NOTIFICATION,
        webhook_payload={
            "notification": asdict(notification),
            "execution_scope": _get_execution_scope(),
        },
        log_context=f"skill={skill_name}",
    )


def send_skillit_notification(event_type: str, context: dict | str = None) -> bool:
    """Send a skillit log event to FlowPad (fire-and-forget).

    Args:
        event_type: Type of event (e.g., "skill_matched", "hook_triggered").
        context: Optional additional context.

    Returns:
        True if notification was queued, False if Flowpad not running.
    """
    return send_webhook_event(
        webhook_type=WebhookType.SKILLIT_LOG,
        webhook_payload={
            "event": {
                "type": event_type,
                "context": context or {},
            },
        },
        log_context=f"skillit_log={event_type}",
    )

def send_activation_event(event_type: str, context: dict = None) -> bool:
    """Send activation rules event to FlowPad (fire-and-forget).

    Args:
        event_type: Type of event (e.g., "started_generating_skill", "skill_ready").
        context: Optional additional context (session_id, skill_name, etc.).

    Returns:
        True if notification was queued, False if Flowpad not running.
    """
    return send_webhook_event(
        webhook_type=WebhookType.ACTIVATION_RULES,
        webhook_payload={
            "event": {
                "type": event_type,
                "context": context or {},
            },
            "execution_scope": _get_execution_scope(),
        },
        log_context=f"event={event_type}",
    )



def send_hello_skillit_notification(context: dict = None) -> bool:
    """Send a hello skillit event to FlowPad (fire-and-forget).

    Args:
        context: Optional additional context.

    Returns:
        True if notification was queued, False if Flowpad not running.
    """
    return send_skillit_notification("hello_skillit", context)

def main():
    if len(sys.argv) < 3:
        print("Usage: python notify.py <skill_name> <matched_keyword> [prompt] [handler_name] [folder_path]")
        print()
        print("Example:")
        print('  python notify.py "skillit" "skillit" "analyse this" "handle_analyze" "/home/user/project"')
        sys.exit(1)

    skill_name = sys.argv[1]
    matched_keyword = sys.argv[2]
    prompt = sys.argv[3] if len(sys.argv) > 3 else ""
    handler_name = sys.argv[4] if len(sys.argv) > 4 else "unknown"
    folder_path = sys.argv[5] if len(sys.argv) > 5 else ""

    success = send_skill_notification(skill_name, matched_keyword, prompt, handler_name, folder_path)
    if success:
        print(f"Notification queued for skill: {skill_name}")
        import time
        time.sleep(0.5)  # Allow daemon thread to send
    else:
        print("Notification skipped (env vars not set)")

if __name__ == "__main__":
    # CLI interface for testing
    send_hello_skillit_notification()
    # main() # Uncomment to test skill notification with CLI args

