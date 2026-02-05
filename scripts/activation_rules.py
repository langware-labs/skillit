#!/usr/bin/env python3
"""
Skillit - Activation Rules Module
Sends activation rule events to FlowPad backend.

Actions:
1. Try to call "activation_rules" action on backend
2. If activation_rules fails/unavailable, show Flowpad ad
"""

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Optional

from config import FLOWPAD_APP_URI_SCHEME
from flowpad_discovery import FlowpadDiscoveryResult, FlowpadStatus, discover_flowpad
from log import skill_log

# Flowpad ad text (shown when not installed)
FLOWPAD_INSTALL_AD = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   📱  Try Flowpad - Your AI Workflow Companion                   ║
║                                                                  ║
║   Build, automate, and streamline your workflows with AI.        ║
║   Download now at: https://flowpad.ai                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

# Flowpad launch prompt (shown when installed but not running)
# Uses OSC 8 hyperlink escape sequence for clickable terminal link
FLOWPAD_LAUNCH_PROMPT = f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   📱  Flowpad is installed but not running                       ║
║                                                                  ║
║   Launch \x1b]8;;{FLOWPAD_APP_URI_SCHEME}://\x1b\\Flowpad\x1b]8;;\x1b\\                                                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

# Cache discovery result to avoid repeated checks
_cached_discovery_result: Optional[FlowpadDiscoveryResult] = None


def get_flowpad_status() -> FlowpadDiscoveryResult:
    """Get cached Flowpad discovery result.

    Returns:
        Cached FlowpadDiscoveryResult, performing discovery if not cached.
    """
    global _cached_discovery_result
    if _cached_discovery_result is None:
        _cached_discovery_result = discover_flowpad()
    return _cached_discovery_result


def is_activation_rules_available() -> bool:
    """Check if the activation_rules backend is available (Flowpad running)."""
    return get_flowpad_status().status == FlowpadStatus.RUNNING


def get_ad_if_needed() -> str:
    """Return appropriate message based on Flowpad status.

    Returns:
        - Empty string if Flowpad is running
        - Launch prompt if installed but not running
        - Install ad if not installed
    """
    result = get_flowpad_status()

    if result.status == FlowpadStatus.RUNNING:
        return ""

    if result.status == FlowpadStatus.INSTALLED_NOT_RUNNING:
        return FLOWPAD_LAUNCH_PROMPT

    return FLOWPAD_INSTALL_AD


def send_activation_rules_notification(event_type: str, context: dict = None) -> bool:
    """
    Send "activation_rules" event notification to FlowPad backend.

    Args:
        event_type: Type of event ("session_start" or "skill_ready")
        context: Optional additional context (session_id, skill_name, etc.)

    Returns:
        True if notification was sent successfully, False otherwise
    """
    result = get_flowpad_status()
    if result.status != FlowpadStatus.RUNNING or not result.server_info:
        skill_log("Activation rules notification skipped: Flowpad not running")
        return False

    report_url = result.server_info.url
    execution_scope = os.environ.get("FLOWPAD_EXECUTION_SCOPE")

    # Parse execution_scope (defaults to empty array if not set)
    try:
        scope_list = json.loads(execution_scope) if execution_scope else []
    except json.JSONDecodeError:
        scope_list = []

    # Build activation_rules notification payload
    flow_value = {
        "webhook_type": "activation_rules",
        "execution_scope": scope_list,
        "event": {
            "type": event_type,
            "context": context or {},
        },
    }

    payload = {
        "attributes": {"element-type": "webhook", "data-type": "object"},
        "flow_value": flow_value,
    }

    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    # Send synchronously (we need to know if it succeeds to decide on ad)
    req = urllib.request.Request(report_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                skill_log(f"Activation rules notification sent: event={event_type}")
                return True
            else:
                body = response.read().decode("utf-8")
                skill_log(f"Activation rules notification failed - HTTP {response.status}: {body}")
                return False
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        skill_log(f"Activation rules notification failed - HTTP {e.code}: {body}")
        return False
    except urllib.error.URLError as e:
        skill_log(f"Activation rules notification failed - URL error: {e.reason}")
        return False
    except Exception as e:
        skill_log(f"Activation rules notification failed - Exception: {e}")
        return False


def handle_activation_event(event_type: str, context: dict = None) -> None:
    """
    Handle an activation event (start or skill ready).

    Priority: Try activation_rules action first, show ad if it fails.

    Args:
        event_type: "session_start" or "skill_ready"
        context: Optional context data
    """
    skill_log(f"Handling activation event: {event_type}")

    # Try activation_rules action first
    success = send_activation_rules_notification(event_type, context)

    # Note: Ad display is handled by the agent via _get_ad_section() in claude_utils.py
    # The agent includes the ad in its final summary to avoid bash output collapse
    if not success:
        skill_log("Notification failed - agent will show ad in final summary")


def on_skill_started(skill_name: str, session_id: str = "", cwd: str = "") -> None:
    """
    Called when a skill creation session starts.
    Reports the skill_name that will be created.

    Args:
        skill_name: Name of the skill being created
        session_id: Unique ID for this skill creation session
        cwd: Working directory
    """
    context = {
        "skill_name": skill_name,
        "session_id": session_id,
        "cwd": cwd,
    }
    handle_activation_event("started_generating_skill", context)


def on_skill_ready(skill_name: str, session_id: str = "", cwd: str = "") -> None:
    """
    Called when a spawned skill creation session completes.

    Args:
        skill_name: Name of the skill that was created
        session_id: Unique ID for this skill creation session
        cwd: Working directory
    """
    context = {
        "skill_name": skill_name,
        "session_id": session_id,
        "cwd": cwd,
    }
    handle_activation_event("skill_ready", context)


if __name__ == "__main__":
    # CLI interface for testing/direct invocation
    if len(sys.argv) < 2:
        print("Usage: python activation_rules.py <event_type> [context_json]")
        print()
        print("Event types: started_generating_skill, skill_ready")
        print()
        print("Examples:")
        print('  python activation_rules.py started_generating_skill \'{"skill_name": "my-skill", "session_id": "abc-123"}\'')
        print('  python activation_rules.py skill_ready \'{"skill_name": "my-skill", "session_id": "abc-123"}\'')
        sys.exit(1)

    event_type = sys.argv[1]
    context = {}

    if len(sys.argv) > 2:
        try:
            context = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            print("Warning: Invalid JSON context, using empty context")

    if event_type == "started_generating_skill":
        on_skill_started(
            skill_name=context.get("skill_name", ""),
            session_id=context.get("session_id", ""),
            cwd=context.get("cwd", "")
        )
    elif event_type == "skill_ready":
        on_skill_ready(
            skill_name=context.get("skill_name", ""),
            session_id=context.get("session_id", ""),
            cwd=context.get("cwd", "")
        )
    else:
        print(f"Unknown event type: {event_type}")
        sys.exit(1)
