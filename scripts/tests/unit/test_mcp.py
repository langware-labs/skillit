"""Tests for MCP server tools."""

import json

from fs_store.record_types import RecordType
from mcp_server.main import flow_entity_crud
from plugin_records.skillit_records import SkillitRecords

# FastMCP wraps decorated functions into FunctionTool objects;
# .fn holds the original callable.
_crud = flow_entity_crud.fn

# Real transaction payload from a PreToolUse hook event.
_REAL_ENTITY_JSON = '{"type": "skill", "name": "acli-jira-correct-syntax", "description": "Corrects acli (Atlassian CLI) command syntax. Use when the user asks to run acli commands or interact with Jira, Confluence, or Bitbucket via the CLI. The current acli version uses subcommands (e.g., workitem search) instead of the deprecated --action flag.", "path": "output/acli-jira-correct-syntax"}'
_REAL_SESSION_ID = "d7dd8377-c888-40e5-98ea-899ed95c7eeb"


def test_flow_entity_crud_invalid_json():
    result = _crud("s1", "create", "not-json")
    assert "Error" in result


def test_flow_entity_crud_unknown_op():
    result = _crud("s1", "drop", json.dumps({"type": "skill"}))
    assert "Error" in result


def test_flow_entity_crud_dispatches(monkeypatch):
    from plugin_records.skillit_records import skillit_records

    calls = []
    monkeypatch.setattr(
        skillit_records, "entity_crud",
        lambda **kwargs: calls.append(kwargs) or "ok",
    )
    result = _crud("s1", "create", json.dumps({"type": "skill", "name": "x"}))
    assert result == "ok"
    assert calls[0] == {"session_id": "s1", "crud": "create", "entity": {"type": "skill", "name": "x"}}


def test_flow_entity_crud_create_skill(tmp_path, monkeypatch):
    import sys
    mod = sys.modules["plugin_records.skillit_records"]

    mgr = SkillitRecords(records_path=tmp_path)
    monkeypatch.setattr(mod, "skillit_records", mgr)

    result = _crud(_REAL_SESSION_ID, "create", _REAL_ENTITY_JSON)
    assert "Created" in result

    skill = mgr.get_skill("acli-jira-correct-syntax")
    assert skill is not None
    assert skill.name == "acli-jira-correct-syntax"
    assert skill.description.startswith("Corrects acli")
    assert skill.type == RecordType.SKILL
