#!/usr/bin/env python3
"""
Skillit - Activation Rules Module
Handles activation lifecycle events and Flowpad ad display.

Server communication is delegated to notify.py.
"""

import json
import sys

from config import FLOWPAD_APP_URI_SCHEME
from log import skill_log
from notify import FlowpadStatus, get_flowpad_status, send_activation_event

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


def get_ad_if_needed() -> str:
    """Return appropriate message based on Flowpad status.

    Returns:
        - Empty string if Flowpad is running
        - Launch prompt if installed but not running
        - Install ad if not installed
    """
    status = get_flowpad_status()

    if status == FlowpadStatus.RUNNING:
        return ""

    if status == FlowpadStatus.INSTALLED_NOT_RUNNING:
        return FLOWPAD_LAUNCH_PROMPT

    return FLOWPAD_INSTALL_AD


def handle_activation_event(event_type: str, context: dict = None) -> None:
    """Handle an activation event (start or skill ready).

    Sends notification to Flowpad (fire-and-forget).

    Args:
        event_type: "started_generating_skill" or "skill_ready"
        context: Optional context data
    """
    skill_log(f"Handling activation event: {event_type}")

    queued = send_activation_event(event_type, context)

    # Note: Ad display is handled by the agent via _get_ad_section() in claude_utils.py
    if not queued:
        skill_log("Notification failed - agent will show ad in final summary")


def on_skill_started(skill_name: str, session_id: str = "", cwd: str = "") -> None:
    """Called when a skill creation session starts.

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
    """Called when a spawned skill creation session completes.

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
