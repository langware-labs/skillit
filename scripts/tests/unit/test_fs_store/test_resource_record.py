"""Tests for ResourceRecord – pure data contract: serialization, uid, key-value access, naming, children."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime

import pytest

from fs_store import FsRecordRef, ResourceRecord, Scope
from fs_store.resource_record import parse_record_stem, record_stem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class CloudRecord(ResourceRecord):
    uid_field_name = "entity_id"
    entity_id: str = field(default_factory=lambda: f"cloud-{uuid.uuid4().hex[:6]}")


# ---------------------------------------------------------------------------
# uid / uid_field_name
# ---------------------------------------------------------------------------

class TestUid:
    def test_default_uid_is_id(self):
        r = ResourceRecord(id="abc")
        assert r.uid == "abc"
        assert r.uid_field_name == "id"

    def test_subclass_custom_uid(self):
        cr = CloudRecord(entity_id="eid-42")
        assert cr.uid_field_name == "entity_id"
        assert cr.uid == "eid-42"

    def test_uid_reflects_field_value(self):
        r = ResourceRecord()
        original = r.uid
        r.id = "changed"
        assert r.uid == "changed"
        assert r.uid != original


# ---------------------------------------------------------------------------
# Stem / naming convention
# ---------------------------------------------------------------------------

class TestStemNaming:
    def test_record_stem_format(self):
        assert record_stem("session", "abc123") == "session-@abc123"

    def test_parse_record_stem(self):
        typ, uid = parse_record_stem("rule-@def456")
        assert typ == "rule"
        assert uid == "def456"

    def test_parse_record_stem_with_extra_separator(self):
        typ, uid = parse_record_stem("my-type-@uid-with-dashes")
        assert typ == "my-type"
        assert uid == "uid-with-dashes"

    def test_parse_record_stem_invalid(self):
        with pytest.raises(ValueError):
            parse_record_stem("no_separator_here")

    def test_stem_property(self):
        r = ResourceRecord(id="xyz", type="hook")
        assert r.stem == "hook-@xyz"

    def test_stem_custom_uid(self):
        cr = CloudRecord(type="cloud", entity_id="eid-1")
        assert cr.stem == "cloud-@eid-1"


# ---------------------------------------------------------------------------
# Serialization: to_dict / from_dict
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_to_dict_basic(self):
        r = ResourceRecord(id="1", type="t", name="n")
        d = r.to_dict()
        assert d["id"] == "1"
        assert d["type"] == "t"
        assert d["name"] == "n"
        assert "extra" not in d

    def test_to_dict_datetime_iso(self):
        dt = datetime(2025, 1, 15, 12, 0, 0)
        r = ResourceRecord(created_at=dt)
        d = r.to_dict()
        assert d["created_at"] == "2025-01-15T12:00:00"

    def test_to_dict_scope_enum_value(self):
        r = ResourceRecord(scope=Scope.PROJECT)
        assert r.to_dict()["scope"] == "project"

    def test_to_dict_extra_merged(self):
        r = ResourceRecord(extra={"custom": 42})
        d = r.to_dict()
        assert d["custom"] == 42
        assert "extra" not in d

    def test_from_dict_round_trip(self):
        r = ResourceRecord(
            id="1", type="t", name="n",
            scope=Scope.PROJECT,
            created_at=datetime(2025, 6, 1),
            extra={"tag": "v"},
        )
        d = r.to_dict()
        r2 = ResourceRecord.from_dict(d)
        assert r2.id == "1"
        assert r2.scope == Scope.PROJECT
        assert isinstance(r2.created_at, datetime)
        assert r2.extra["tag"] == "v"

    def test_from_dict_unknown_keys_to_extra(self):
        r = ResourceRecord.from_dict({"name": "x", "foo": "bar", "baz": 1})
        assert r.name == "x"
        assert r.extra == {"foo": "bar", "baz": 1}

    def test_from_dict_scope_coercion(self):
        r = ResourceRecord.from_dict({"scope": "local"})
        assert r.scope == Scope.LOCAL

    def test_from_dict_scope_unknown_string(self):
        r = ResourceRecord.from_dict({"scope": "custom_scope"})
        assert r.scope == "custom_scope"

    def test_from_dict_datetime_string_coercion(self):
        r = ResourceRecord.from_dict({"created_at": "2025-03-01T10:00:00"})
        assert isinstance(r.created_at, datetime)
        assert r.created_at.year == 2025

    def test_subclass_from_dict(self):
        cr = CloudRecord.from_dict({"entity_id": "eid-9", "name": "svc"})
        assert cr.uid == "eid-9"
        assert cr.name == "svc"


# ---------------------------------------------------------------------------
# Key-value access
# ---------------------------------------------------------------------------

class TestKeyValueAccess:
    def test_getitem_known_field(self):
        r = ResourceRecord(name="hello")
        assert r["name"] == "hello"

    def test_getitem_extra(self):
        r = ResourceRecord(extra={"custom": 99})
        assert r["custom"] == 99

    def test_getitem_missing_raises(self):
        r = ResourceRecord()
        with pytest.raises(KeyError):
            r["nonexistent"]

    def test_setitem_known_field(self):
        r = ResourceRecord()
        r["name"] = "updated"
        assert r.name == "updated"

    def test_setitem_extra(self):
        r = ResourceRecord()
        r["custom_key"] = "custom_val"
        assert r.extra["custom_key"] == "custom_val"

    def test_delitem(self):
        r = ResourceRecord(extra={"k": "v"})
        del r["k"]
        assert "k" not in r.extra

    def test_delitem_known_field_raises(self):
        r = ResourceRecord()
        with pytest.raises(KeyError):
            del r["name"]

    def test_contains_known(self):
        r = ResourceRecord()
        assert "name" in r
        assert "id" in r

    def test_contains_extra(self):
        r = ResourceRecord(extra={"tag": 1})
        assert "tag" in r
        assert "missing" not in r

    def test_keys(self):
        r = ResourceRecord(extra={"x": 1, "y": 2})
        k = r.keys()
        assert "id" in k
        assert "name" in k
        assert "x" in k
        assert "y" in k
        assert "extra" not in k


# ---------------------------------------------------------------------------
# Children refs (FsRecordRef list)
# ---------------------------------------------------------------------------

class TestChildrenRefs:
    def test_no_children_by_default(self):
        r = ResourceRecord()
        assert r.children_refs == []

    def test_add_children_refs(self):
        parent = ResourceRecord(id="p", type="folder", name="parent")
        parent.children_refs = [
            FsRecordRef(id="c1", type="file"),
            FsRecordRef(id="c2", type="file"),
        ]
        assert len(parent.children_refs) == 2
        assert parent.children_refs[0].id == "c1"

    def test_to_dict_excludes_empty_children(self):
        r = ResourceRecord(id="no-kids")
        d = r.to_dict()
        assert "children" not in d

    def test_to_dict_includes_children(self):
        parent = ResourceRecord(id="p", type="folder")
        parent.children_refs = [
            FsRecordRef(id="c1", type="file"),
            FsRecordRef(id="c2", type="file"),
        ]
        d = parent.to_dict()
        assert "children" in d
        assert len(d["children"]) == 2
        assert d["children"][0]["id"] == "c1"

    def test_from_dict_with_children(self):
        data = {
            "id": "p",
            "type": "folder",
            "children": [
                {"id": "c1", "type": "file"},
                {"id": "c2", "type": "file"},
            ],
        }
        r = ResourceRecord.from_dict(data)
        assert len(r.children_refs) == 2
        assert isinstance(r.children_refs[0], FsRecordRef)
        assert r.children_refs[0].id == "c1"

    def test_from_dict_no_children_key(self):
        r = ResourceRecord.from_dict({"id": "solo"})
        assert r.children_refs == []

    def test_children_round_trip(self):
        parent = ResourceRecord(id="p", type="folder", scope=Scope.PROJECT)
        parent.children_refs = [
            FsRecordRef(id="c1", type="file", record_path="/tmp/c1.json"),
        ]
        d = parent.to_dict()
        r2 = ResourceRecord.from_dict(d)
        assert len(r2.children_refs) == 1
        c = r2.children_refs[0]
        assert isinstance(c, FsRecordRef)
        assert c.id == "c1"
        assert c.record_path == "/tmp/c1.json"

    def test_children_refs_are_flat(self):
        """Children are FsRecordRef — they don't embed full record data."""
        parent = ResourceRecord(id="p", type="folder")
        parent.children_refs = [FsRecordRef(id="c", type="file")]
        d = parent.to_dict()
        child_dict = d["children"][0]
        assert set(child_dict.keys()) == {"id", "type"}

    def test_children_with_record_path(self):
        ref = FsRecordRef(id="c", type="file", record_path="/data/c.json")
        parent = ResourceRecord(id="p", children_refs=[ref])
        d = parent.to_dict()
        assert d["children"][0]["record_path"] == "/data/c.json"


# ---------------------------------------------------------------------------
# Parent ref (FsRecordRef)
# ---------------------------------------------------------------------------

class TestParentRef:
    def test_parent_ref_defaults_to_none(self):
        r = ResourceRecord()
        assert r.parent_ref is None

    def test_parent_ref_round_trip(self):
        r = ResourceRecord(id="child-1", parent_ref=FsRecordRef(id="parent-1", type="task"))
        d = r.to_dict()
        assert d["parent"] == {"id": "parent-1", "type": "task"}
        r2 = ResourceRecord.from_dict(d)
        assert isinstance(r2.parent_ref, FsRecordRef)
        assert r2.parent_ref.id == "parent-1"
        assert r2.parent_ref.type == "task"

    def test_parent_ref_coexists_with_children_refs(self):
        r = ResourceRecord(
            id="mid",
            type="node",
            parent_ref=FsRecordRef(id="root", type="root"),
            children_refs=[FsRecordRef(id="leaf", type="leaf")],
        )
        d = r.to_dict()
        assert d["parent"]["id"] == "root"
        assert len(d["children"]) == 1
        r2 = ResourceRecord.from_dict(d)
        assert r2.parent_ref.id == "root"
        assert r2.children_refs[0].id == "leaf"

    def test_backward_compat_parent_id_string(self):
        """Old serialized data with parent_id string should deserialize to FsRecordRef."""
        data = {"id": "child-1", "parent_id": "parent-1"}
        r = ResourceRecord.from_dict(data)
        assert isinstance(r.parent_ref, FsRecordRef)
        assert r.parent_ref.id == "parent-1"
        assert r.parent_ref.type == ""
