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
import uuid
import xml.etree.ElementTree as ET
from typing import Optional

from network.flowpad_discovery import (
    FlowpadStatus,  # re-exported for consumers (e.g., activation_rules)
    discover_flowpad,
    is_webhook_rate_limited,
    record_webhook_failure,
)
from fs_store import RecordType, RefType, ResourceType, SyncOperation
from utils.log import skill_log


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
# Helpers
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


# ---------------------------------------------------------------------------
# Core resource sync sender
# ---------------------------------------------------------------------------

def send_resource_sync(
    type: str,
    id: str,
    operation: SyncOperation,
    data: dict | str,
    resource_type: ResourceType = ResourceType.ENTITY,
    ref_type: RefType = RefType.DATA,
    log_context: str = "",
) -> bool:
    """Send a resource sync event to FlowPad (fire-and-forget).

    All notifications flow through this single envelope format.
    ``execution_scope`` is always attached at the envelope level
    (auto-populated from the FLOWPAD_EXECUTION_SCOPE env var).

    Envelope wire format::

        {
            "webhook_type": "resource_sync",
            "webhook_payload": {
                "resource_type":    "entity" | "relationship",
                "type":             <RecordType>,
                "id":               <uuid>,
                "operation":        "create" | "update" | "delete" | "event",
                "ref_type":         "data" | "path",
                "data":             <payload — see below>,
                "execution_scope":  [...]
            }
        }

    For CRUD operations (create/update/delete) ``data`` is a full
    ResourceRecord dict.

    For EVENT operations ``data`` follows the standard event shape::

        {"event_name": "...", "event_data": {...}}

    Args:
        type: Entity type (e.g. "task") or relationship kind (e.g. "child").
        id: Unique identifier for the resource or event.
        operation: create / update / delete / event.
        data: Resource payload (CRUD) or event payload (EVENT).
        resource_type: Whether this sync is for an entity or a relationship.
        ref_type: Whether data is inline ("data") or a path reference ("path").
        log_context: Context string for logging.

    Returns:
        True if notification was queued, False if skipped.
    """
    if is_webhook_rate_limited():
        skill_log(f"Notification skipped: rate-limited ({log_context})")
        return False

    report_url = _get_report_url()
    ctx = log_context or f"{type}/{operation}"
    print(f"[notify] webhook url: {report_url} | type: {type} | op: {operation} | {ctx}")
    if not report_url:
        skill_log(f"Notification skipped: Flowpad not running ({ctx})")
        return False

    payload = {
        "webhook_type": "resource_sync",
        "webhook_payload": {
            "resource_type": str(resource_type),
            "type": type,
            "id": id,
            "operation": str(operation),
            "ref_type": str(ref_type),
            "data": data,
            "execution_scope": _get_execution_scope(),
        },
    }

    raw = json.dumps(payload).encode("utf-8")
    _send_fire_and_forget(report_url, raw, ctx)
    return True


# ---------------------------------------------------------------------------
# Typed convenience senders
# ---------------------------------------------------------------------------

def send_skill_activation(
    skill_name: str,
    matched_keyword: str,
    prompt: str,
    handler_name: str,
    folder_path: str,
) -> bool:
    """Send skill activation event to FlowPad (fire-and-forget).

    Args:
        skill_name: Name of the skill being invoked
        matched_keyword: The keyword that triggered the skill
        prompt: The user prompt that triggered activation
        handler_name: Name of the handler function being called
        folder_path: Working directory where skill output is generated

    Returns:
        True if notification was queued, False if Flowpad not running
    """
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


def send_log_event(event_type: str, context: dict | str = None) -> bool:
    """Send a log event to FlowPad (fire-and-forget).

    Args:
        event_type: Type of event (e.g., "skill_matched", "hook_triggered").
        context: Optional additional context.

    Returns:
        True if notification was queued, False if Flowpad not running.
    """
    return send_resource_sync(
        type=RecordType.LOG,
        id=str(uuid.uuid4()),
        operation=SyncOperation.EVENT,
        data={
            "event_name": event_type,
            "event_data": context or {},
        },
        log_context=f"log={event_type}",
    )


def send_skill_event(event_type: str, context: dict = None) -> bool:
    """Send a skill lifecycle event to FlowPad (fire-and-forget).

    Args:
        event_type: Type of event (e.g., "started_generating_skill", "skill_ready").
        context: Optional additional context (session_id, skill_name, etc.).

    Returns:
        True if notification was queued, False if Flowpad not running.
    """
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


def send_task_sync(operation: SyncOperation, task_data: dict) -> bool:
    """Send a task CRUD sync to FlowPad.

    Args:
        operation: SyncOperation.CREATE or SyncOperation.UPDATE
        task_data: Full task ResourceRecord dict (from TaskResource.to_dict())

    Returns:
        True if notification was queued, False if Flowpad not running.
    """
    task_id = task_data.get("id", str(uuid.uuid4()))
    return send_resource_sync(
        type=RecordType.TASK,
        id=task_id,
        operation=operation,
        data=task_data,
        resource_type=ResourceType.ENTITY,
        log_context=f"task {operation} id={task_id}",
    )


def send_process_sync(operation: SyncOperation, process_data: dict) -> bool:
    """Send an agentic process CRUD sync to FlowPad.

    Args:
        operation: SyncOperation.CREATE or SyncOperation.UPDATE
        process_data: Full AgenticProcess ResourceRecord dict (from AgenticProcess.to_dict())

    Returns:
        True if notification was queued, False if Flowpad not running.
    """
    process_id = process_data.get("id", str(uuid.uuid4()))
    return send_resource_sync(
        type=RecordType.AGENTIC_PROCESS,
        id=process_id,
        operation=operation,
        data=process_data,
        resource_type=ResourceType.ENTITY,
        log_context=f"process {operation} id={process_id}",
    )


def send_relationship_sync(operation: SyncOperation, relationship_data: dict) -> bool:
    """Send a relationship CRUD sync to FlowPad.

    Args:
        operation: SyncOperation.CREATE / UPDATE / DELETE.
        relationship_data: Full RelationshipRecord dict.

    Returns:
        True if notification was queued, False if Flowpad not running.
    """
    relationship_id = relationship_data.get("id", str(uuid.uuid4()))
    relationship_type = relationship_data.get("type", "relationship")
    return send_resource_sync(
        type=relationship_type,
        id=relationship_id,
        operation=operation,
        data=relationship_data,
        resource_type=ResourceType.RELATIONSHIP,
        log_context=f"relationship {operation} id={relationship_id}",
    )


def send_flow_tag(flow_data: dict) -> bool:
    """Send a flow tag event to FlowPad.

    Args:
        flow_data: Parsed flow tag dict (from xml_str_to_flow_data_dict).

    Returns:
        True if notification was queued, False if Flowpad not running.
    """
    return send_resource_sync(
        type=RecordType.SKILL,
        id=str(uuid.uuid4()),
        operation=SyncOperation.EVENT,
        data={
            "event_name": "flow_tag",
            "event_data": flow_data,
        },
        log_context=f"flow_tag={flow_data.get('element_type', 'unknown')}",
    )


def send_hello_skillit_notification(context: dict = None) -> bool:
    """Send a hello skillit event to FlowPad (fire-and-forget).

    Args:
        context: Optional additional context.

    Returns:
        True if notification was queued, False if Flowpad not running.
    """
    return send_log_event("hello_skillit", context)


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

    success = send_skill_activation(skill_name, matched_keyword, prompt, handler_name, folder_path)
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
