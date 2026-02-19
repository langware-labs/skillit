"""Tests for the type registry — explicit registration of record types."""

import plugin_records  # noqa: F401 — triggers type_registry registrations

from flow_sdk.fs_store import type_registry
from flow_sdk.fs_store.record_types import RecordType, SkillitRecordType
from flow_sdk.fs_records.skill_record import SkillRecord
from plugin_records.skillit_session import SkillitSession
from plugin_records.skillit_config import SkillitConfig


def test_skill_record_registered():
    assert type_registry.get(RecordType.SKILL) is SkillRecord


def test_skillit_session_registered():
    assert type_registry.get(SkillitRecordType.SKILLIT_SESSION) is SkillitSession


def test_skillit_config_registered():
    assert type_registry.get(SkillitRecordType.SKILLIT_CONFIG) is SkillitConfig


def test_get_unknown_returns_none():
    assert type_registry.get("nonexistent") is None


def test_contains():
    assert RecordType.SKILL in type_registry
    assert "nonexistent" not in type_registry


def test_get_all_types():
    all_types = type_registry.get_all_types()
    assert RecordType.SKILL in all_types
    assert SkillitRecordType.SKILLIT_SESSION in all_types
    assert SkillitRecordType.SKILLIT_CONFIG in all_types


def test_get_returns_correct_class():
    cls = type_registry.get(RecordType.SKILL)
    record = cls(id="test-1")
    assert record.type == RecordType.SKILL
