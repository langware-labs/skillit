"""Tests for FsRecord – filesystem I/O (from_json / to_json / persist)."""

import json

import pytest

from fs_store import FsRecord, ResourceRecord, Scope


# ---------------------------------------------------------------------------
# from_json / to_json
# ---------------------------------------------------------------------------

class TestJsonIO:
    def test_to_json_creates_file(self, tmp_path):
        r = FsRecord(id="1", name="test")
        fp = tmp_path / "rec.json"
        r.to_json(fp)
        assert fp.exists()
        data = json.loads(fp.read_text())
        assert data["id"] == "1"

    def test_from_json_existing(self, tmp_path):
        fp = tmp_path / "rec.json"
        fp.write_text(json.dumps({"id": "x", "name": "loaded"}))
        r = FsRecord.from_json(fp)
        assert r.id == "x"
        assert r.name == "loaded"
        assert r.source_file == str(fp)

    def test_from_json_missing_creates_new(self, tmp_path):
        fp = tmp_path / "missing.json"
        r = FsRecord.from_json(fp)
        assert r.source_file == str(fp)
        assert r.id  # auto-generated uuid

    def test_round_trip_json_file(self, tmp_path):
        fp = tmp_path / "rt.json"
        r = FsRecord(id="rt", type="session", name="s1",
                      scope=Scope.PROJECT, extra={"k": "v"})
        r.to_json(fp)
        r2 = FsRecord.from_json(fp)
        assert r2.id == "rt"
        assert r2.scope == Scope.PROJECT
        assert r2.extra["k"] == "v"

    def test_to_json_creates_parent_dirs(self, tmp_path):
        fp = tmp_path / "a" / "b" / "rec.json"
        r = FsRecord(id="nested")
        r.to_json(fp)
        assert fp.exists()

    def test_to_json_defaults_to_source_file(self, tmp_path):
        fp = tmp_path / "auto.json"
        r = FsRecord(id="auto")
        r.to_json(fp)  # sets source_file
        r["tag"] = "updated"
        r.to_json()  # should write to same path
        data = json.loads(fp.read_text())
        assert data["tag"] == "updated"


# ---------------------------------------------------------------------------
# persist
# ---------------------------------------------------------------------------

class TestPersist:
    def test_persist(self, tmp_path):
        fp = tmp_path / "rec.json"
        r = FsRecord.from_json(fp)
        r["key"] = "val"
        r.persist()
        assert fp.exists()
        data = json.loads(fp.read_text())
        assert data["key"] == "val"

    def test_persist_without_source_file_raises(self):
        r = FsRecord()
        r.source_file = None
        with pytest.raises(ValueError):
            r.persist()


# ---------------------------------------------------------------------------
# Children + JSON file round-trip
# ---------------------------------------------------------------------------

class TestChildrenFileIO:
    def test_children_json_file_round_trip(self, tmp_path):
        fp = tmp_path / "nested.json"
        parent = FsRecord(id="p", type="session")
        parent.children = [
            ResourceRecord(id="c1", type="step", name="s1"),
            ResourceRecord(id="c2", type="step", name="s2"),
        ]
        parent.to_json(fp)

        loaded = FsRecord.from_json(fp)
        assert len(loaded.children) == 2
        assert loaded.children[0].name == "s1"


# ---------------------------------------------------------------------------
# FsRecord is a ResourceRecord
# ---------------------------------------------------------------------------

class TestInheritance:
    def test_isinstance(self):
        r = FsRecord(id="x")
        assert isinstance(r, ResourceRecord)

    def test_to_dict_works(self):
        r = FsRecord(id="x", name="fs", extra={"k": "v"})
        d = r.to_dict()
        assert d["id"] == "x"
        assert d["k"] == "v"

    def test_from_dict_works(self):
        r = FsRecord.from_dict({"id": "x", "name": "loaded"})
        assert r.id == "x"
        assert isinstance(r, FsRecord)

    def test_kv_access(self):
        r = FsRecord()
        r["foo"] = "bar"
        assert r["foo"] == "bar"
        assert "foo" in r
