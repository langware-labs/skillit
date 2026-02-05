#!/usr/bin/env python3
"""
Skillit - Notification Module
Sends skill activation notifications to FlowPad backend via webhook.

Similar to flow_trace, but for skill-level notifications rather than instruction traces.
"""

import json
import os
import sys
import threading
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Optional

from flowpad_discovery import FlowpadStatus, discover_flowpad
from log import skill_log


@dataclass
class SkillNotification:
    """Skill notification payload."""

    skill_name: str
    matched_keyword: str
    prompt: str
    handler_name: str
    folder_path: str  # Working directory where skill output is generated


def _send_request(url: str, data: bytes, headers: dict, skill_name: str) -> None:
    """Send HTTP request in background thread (fire-and-forget)."""
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                skill_log(f"Notification sent: skill={skill_name}")
            else:
                body = response.read().decode("utf-8")
                skill_log(f"HTTP {response.status}: {body}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        skill_log(f"HTTP {e.code}: {body}")
    except Exception as e:
        skill_log(f"Request failed: {e}")


def get_report_url() -> Optional[str]:
    """Discover Flowpad server and return webhook URL.

    Returns:
        Webhook URL if Flowpad is running, None otherwise.
    """
    result = discover_flowpad()
    if result.status == FlowpadStatus.RUNNING and result.server_info:
        return result.server_info.url
    return None


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
    report_url = get_report_url()
    execution_scope = os.environ.get("FLOWPAD_EXECUTION_SCOPE")

    if not report_url:
        skill_log("Notification skipped: Flowpad not running")
        return False

    # Parse execution_scope (defaults to empty array if not set)
    try:
        scope_list = json.loads(execution_scope) if execution_scope else []
    except json.JSONDecodeError:
        scope_list = []

    # Build notification
    notification = SkillNotification(
        skill_name=skill_name,
        matched_keyword=matched_keyword,
        prompt=prompt,
        handler_name=handler_name,
        folder_path=folder_path,
    )

    # Wrap with webhook metadata (similar to flow_trace structure)
    flow_value = {
        "webhook_type": "skill_notification",
        "execution_scope": scope_list,
        "notification": asdict(notification),
    }

    payload = {
        "attributes": {"element-type": "webhook", "data-type": "object"},
        "flow_value": flow_value,
    }

    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    # Fire-and-forget: send in daemon thread
    thread = threading.Thread(
        target=_send_request,
        args=(report_url, data, headers, skill_name),
        daemon=True,
    )
    thread.start()

    return True


if __name__ == "__main__":
    # CLI interface for testing
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
