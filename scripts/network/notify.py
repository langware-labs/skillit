"""Skillit-specific notification senders.

Generic notification functions live in flow_sdk.discovery.notify.
This module contains only skillit-specific senders:
  - send_skill_activation
  - send_skill_event
  - send_hello_skillit_notification
"""

import sys
import uuid

from flow_sdk.discovery.notify import send_log_event, send_resource_sync
from flow_sdk.fs_store import RecordType, SyncOperation


# ---------------------------------------------------------------------------
# Skillit-specific senders (NOT migrated to flow_sdk)
# ---------------------------------------------------------------------------

def send_skill_activation(
    skill_name: str,
    matched_keyword: str,
    prompt: str,
    handler_name: str,
    folder_path: str,
) -> bool:
    """Send skill activation event to FlowPad (fire-and-forget)."""
    return send_resource_sync(
        type=RecordType.SKILL,
        id=str(uuid.uuid4()),
        operation=SyncOperation.EVENT,
        data={
            "event_name": "skill_activated",
            "event_data": {
                "skill_name": skill_name,
                "matched_keyword": matched_keyword,
                "prompt": prompt,
                "handler_name": handler_name,
                "folder_path": folder_path,
            },
        },
        log_context=f"skill={skill_name}",
    )


def send_skill_event(event_type: str, context: dict = None) -> bool:
    """Send a skill lifecycle event to FlowPad (fire-and-forget)."""
    return send_resource_sync(
        type=RecordType.SKILL,
        id=str(uuid.uuid4()),
        operation=SyncOperation.EVENT,
        data={
            "event_name": event_type,
            "event_data": context or {},
        },
        log_context=f"event={event_type}",
    )


def send_hello_skillit_notification(context: dict = None) -> bool:
    """Send a hello skillit event to FlowPad (fire-and-forget)."""
    return send_log_event("hello_skillit", context)


def main():
    if len(sys.argv) < 3:
        print("Usage: python notify.py <skill_name> <matched_keyword> [prompt] [handler_name] [folder_path]")
        sys.exit(1)

    skill_name = sys.argv[1]
    matched_keyword = sys.argv[2]
    prompt = sys.argv[3] if len(sys.argv) > 3 else ""
    handler_name = sys.argv[4] if len(sys.argv) > 4 else "unknown"
    folder_path = sys.argv[5] if len(sys.argv) > 5 else ""

    success = send_skill_activation(skill_name, matched_keyword, prompt, handler_name, folder_path)
    if success:
        print(f"Notification queued for skill: {skill_name}")
        import time
        time.sleep(0.5)
    else:
        print("Notification skipped (env vars not set)")

if __name__ == "__main__":
    send_hello_skillit_notification()
