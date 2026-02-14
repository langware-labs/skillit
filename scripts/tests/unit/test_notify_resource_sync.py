"""Tests for notify resource sync envelope fields."""

import json

import notify
from fs_store import ResourceType, SyncOperation


def _setup_notify_monkeypatch(monkeypatch):
    captured: dict = {}

    monkeypatch.setattr(notify, "is_webhook_rate_limited", lambda: False)
    monkeypatch.setattr(notify, "_get_report_url", lambda: "http://localhost:9999/hook")

    def _capture(url: str, data: bytes, log_context: str):
        captured["url"] = url
        captured["data"] = data
        captured["log_context"] = log_context

    monkeypatch.setattr(notify, "_send_fire_and_forget", _capture)
    return captured


def test_send_resource_sync_includes_resource_type(monkeypatch):
    captured = _setup_notify_monkeypatch(monkeypatch)

    queued = notify.send_resource_sync(
        type="task",
        id="task-1",
        operation=SyncOperation.CREATE,
        data={"id": "task-1", "type": "task"},
        resource_type=ResourceType.ENTITY,
    )

    assert queued is True
    payload = json.loads(captured["data"].decode("utf-8"))
    webhook_payload = payload["webhook_payload"]
    assert webhook_payload["resource_type"] == "entity"
    assert webhook_payload["type"] == "task"
    assert webhook_payload["operation"] == "create"


def test_send_relationship_sync_uses_relationship_resource_type(monkeypatch):
    captured = _setup_notify_monkeypatch(monkeypatch)

    queued = notify.send_relationship_sync(
        operation=SyncOperation.CREATE,
        relationship_data={
            "id": "child:task:task-1:agentic_process:proc-1",
            "type": "child",
            "from_ref": {"id": "task-1", "type": "task"},
            "to_ref": {"id": "proc-1", "type": "agentic_process"},
        },
    )

    assert queued is True
    payload = json.loads(captured["data"].decode("utf-8"))
    webhook_payload = payload["webhook_payload"]
    assert webhook_payload["resource_type"] == "relationship"
    assert webhook_payload["type"] == "child"
    assert webhook_payload["operation"] == "create"
    assert webhook_payload["data"]["from_ref"]["id"] == "task-1"
    assert webhook_payload["data"]["to_ref"]["id"] == "proc-1"
