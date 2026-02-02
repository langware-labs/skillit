#!/usr/bin/env python3
"""
Skillit - Session Events Module
Handles session start and skill ready events.

Actions:
1. Try to call "listen" action on backend
2. If listen fails/unavailable, show Flowpad ad
"""

import json
import os
import sys
import urllib.error
import urllib.request

from log import skill_log

# Flowpad ad text (shown when listen action fails)
FLOWPAD_AD = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   📱  Try Flowpad - Your AI Workflow Companion                   ║
║                                                                  ║
║   Build, automate, and streamline your workflows with AI.        ║
║   Download now at: https://flowpad.ai                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""


def is_listen_available() -> bool:
    """Check if the listen backend is available (env var is set)."""
    return bool(os.environ.get("AGENT_HOOKS_REPORT_URL"))


def get_ad_if_needed() -> str:
    """Return the ad text if listen is not available, empty string otherwise."""
    if is_listen_available():
        return ""
    return FLOWPAD_AD


def send_listen_notification(event_type: str, context: dict = None) -> bool:
    """
    Send "listen" event notification to FlowPad backend.

    Args:
        event_type: Type of event ("session_start" or "skill_ready")
        context: Optional additional context (session_id, skill_name, etc.)

    Returns:
        True if notification was sent successfully, False otherwise
    """
    report_url = os.environ.get("AGENT_HOOKS_REPORT_URL")
    execution_scope = os.environ.get("FLOWPAD_EXECUTION_SCOPE")

    if not report_url:
        skill_log("Listen notification skipped: AGENT_HOOKS_REPORT_URL not set")
        return False

    # Parse execution_scope (defaults to empty array if not set)
    try:
        scope_list = json.loads(execution_scope) if execution_scope else []
    except json.JSONDecodeError:
        scope_list = []

    # Build listen notification payload
    flow_value = {
        "webhook_type": "listen",
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
                skill_log(f"Listen notification sent: event={event_type}")
                return True
            else:
                body = response.read().decode("utf-8")
                skill_log(f"Listen notification failed - HTTP {response.status}: {body}")
                return False
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        skill_log(f"Listen notification failed - HTTP {e.code}: {body}")
        return False
    except urllib.error.URLError as e:
        skill_log(f"Listen notification failed - URL error: {e.reason}")
        return False
    except Exception as e:
        skill_log(f"Listen notification failed - Exception: {e}")
        return False


def show_flowpad_ad() -> None:
    """Display Flowpad promotional message to terminal."""
    skill_log("Showing Flowpad ad")
    print(FLOWPAD_AD)


def handle_session_event(event_type: str, context: dict = None) -> None:
    """
    Handle a session event (start or skill ready).

    Priority: Try listen action first, show ad if it fails.

    Args:
        event_type: "session_start" or "skill_ready"
        context: Optional context data
    """
    skill_log(f"Handling session event: {event_type}")

    # Try listen action first
    listen_success = send_listen_notification(event_type, context)

    # Show ad if listen failed or was unavailable
    if not listen_success:
        show_flowpad_ad()


def on_session_start(data: dict) -> None:
    """
    Called when a Claude Code session starts.

    Args:
        data: Session data from SessionStart hook (session_id, cwd, etc.)
    """
    context = {
        "session_id": data.get("session_id", ""),
        "cwd": data.get("cwd", ""),
    }
    handle_session_event("session_start", context)


def on_skill_started(skill_name: str, skill_session_id: str = "", cwd: str = "") -> None:
    """
    Called when a skill creation session starts.
    Reports the skill_name that will be created.

    Args:
        skill_name: Name of the skill being created
        skill_session_id: Unique ID for this skill creation session
        cwd: Working directory
    """
    context = {
        "skill_name": skill_name,
        "skill_session_id": skill_session_id,
        "cwd": cwd,
    }
    handle_session_event("started_generating_skill", context)


def on_skill_ready(skill_name: str, skill_session_id: str = "", cwd: str = "") -> None:
    """
    Called when a spawned skill creation session completes.

    Args:
        skill_name: Name of the skill that was created
        skill_session_id: Unique ID for this skill creation session
        cwd: Working directory
    """
    context = {
        "skill_name": skill_name,
        "skill_session_id": skill_session_id,
        "cwd": cwd,
    }
    handle_session_event("skill_ready", context)


if __name__ == "__main__":
    # CLI interface for testing/direct invocation
    if len(sys.argv) < 2:
        print("Usage: python session_events.py <event_type> [context_json]")
        print()
        print("Event types: session_start, started_generating_skill, skill_ready")
        print()
        print("Examples:")
        print('  python session_events.py session_start')
        print('  python session_events.py started_generating_skill \'{"skill_name": "my-skill", "skill_session_id": "abc-123"}\'')
        print('  python session_events.py skill_ready \'{"skill_name": "my-skill", "skill_session_id": "abc-123"}\'')
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
            skill_session_id=context.get("skill_session_id", ""),
            cwd=context.get("cwd", "")
        )
    elif event_type == "skill_ready":
        on_skill_ready(
            skill_name=context.get("skill_name", ""),
            skill_session_id=context.get("skill_session_id", ""),
            cwd=context.get("cwd", "")
        )
    else:
        handle_session_event(event_type, context)
