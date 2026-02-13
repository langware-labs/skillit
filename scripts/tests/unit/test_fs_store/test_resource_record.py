"""Tests for ResourceRecord – pure data contract: serialization, uid, key-value access, naming, children."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime

import pytest

from fs_store import ResourceRecord, Scope
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
# Children (nested records)
# ---------------------------------------------------------------------------

class TestChildren:
    def test_no_children_by_default(self):
        r = ResourceRecord()
        assert r.children == []

    def test_add_children(self):
        parent = ResourceRecord(id="p", type="folder", name="parent")
        child1 = ResourceRecord(id="c1", type="file", name="child1")
        child2 = ResourceRecord(id="c2", type="file", name="child2")
        parent.children = [child1, child2]
        assert len(parent.children) == 2
        assert parent.children[0].uid == "c1"

    def test_to_dict_excludes_empty_children(self):
        r = ResourceRecord(id="no-kids")
        d = r.to_dict()
        assert "children" not in d

    def test_to_dict_includes_children(self):
        parent = ResourceRecord(id="p", type="folder")
        parent.children = [
            ResourceRecord(id="c1", type="file", name="a"),
            ResourceRecord(id="c2", type="file", name="b"),
        ]
        d = parent.to_dict()
        assert "children" in d
        assert len(d["children"]) == 2
        assert d["children"][0]["id"] == "c1"
        assert d["children"][1]["name"] == "b"

    def test_from_dict_with_children(self):
        data = {
            "id": "p",
            "type": "folder",
            "children": [
                {"id": "c1", "type": "file", "name": "a"},
                {"id": "c2", "type": "file", "name": "b"},
            ],
        }
        r = ResourceRecord.from_dict(data)
        assert len(r.children) == 2
        assert r.children[0].id == "c1"
        assert r.children[1].name == "b"

    def test_from_dict_no_children_key(self):
        r = ResourceRecord.from_dict({"id": "solo"})
        assert r.children == []

    def test_children_round_trip(self):
        parent = ResourceRecord(id="p", type="folder", scope=Scope.PROJECT)
        parent.children = [
            ResourceRecord(
                id="c1", type="file", name="child",
                created_at=datetime(2025, 6, 1),
                extra={"tag": "v"},
            ),
        ]
        d = parent.to_dict()
        r2 = ResourceRecord.from_dict(d)
        assert len(r2.children) == 1
        c = r2.children[0]
        assert c.id == "c1"
        assert isinstance(c.created_at, datetime)
        assert c.extra["tag"] == "v"

    def test_deeply_nested_children(self):
        grandchild = ResourceRecord(id="gc", type="leaf")
        child = ResourceRecord(id="c", type="node", children=[grandchild])
        root = ResourceRecord(id="r", type="root", children=[child])

        d = root.to_dict()
        assert d["children"][0]["children"][0]["id"] == "gc"

        r2 = ResourceRecord.from_dict(d)
        assert r2.children[0].children[0].uid == "gc"

    def test_children_in_subclass(self):
        child = CloudRecord(entity_id="ce-1", type="cloud")
        parent = CloudRecord(entity_id="pe-1", type="cloud", children=[child])
        d = parent.to_dict()
        r2 = CloudRecord.from_dict(d)
        assert len(r2.children) == 1
        assert r2.children[0].uid == "ce-1"
