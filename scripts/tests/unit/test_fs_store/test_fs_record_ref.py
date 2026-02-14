"""Tests for FsRecordRef — lightweight record reference."""

from fs_store import FsRecordRef, ResourceRecord


class TestConstruction:
    def test_basic(self):
        ref = FsRecordRef(id="a", type="task")
        assert ref.id == "a"
        assert ref.type == "task"
        assert ref.record_path is None

    def test_with_record_path(self):
        ref = FsRecordRef(id="b", type="session", record_path="/tmp/b.json")
        assert ref.record_path == "/tmp/b.json"


class TestToDict:
    def test_omits_none_record_path(self):
        d = FsRecordRef(id="a", type="task").to_dict()
        assert d == {"id": "a", "type": "task"}
        assert "record_path" not in d

    def test_includes_record_path_when_set(self):
        d = FsRecordRef(id="a", type="task", record_path="/p").to_dict()
        assert d == {"id": "a", "type": "task", "record_path": "/p"}


class TestFromDict:
    def test_basic(self):
        ref = FsRecordRef.from_dict({"id": "x", "type": "rule"})
        assert ref.id == "x"
        assert ref.type == "rule"

    def test_ignores_extra_keys(self):
        ref = FsRecordRef.from_dict({"id": "x", "type": "t", "name": "n", "scope": "user"})
        assert ref.id == "x"
        assert ref.type == "t"

    def test_missing_type_defaults_to_empty(self):
        ref = FsRecordRef.from_dict({"id": "x"})
        assert ref.type == ""

    def test_with_record_path(self):
        ref = FsRecordRef.from_dict({"id": "x", "type": "t", "record_path": "/p"})
        assert ref.record_path == "/p"


class TestRoundTrip:
    def test_round_trip_without_path(self):
        original = FsRecordRef(id="a", type="task")
        restored = FsRecordRef.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.record_path is None

    def test_round_trip_with_path(self):
        original = FsRecordRef(id="b", type="session", record_path="/tmp/b.json")
        restored = FsRecordRef.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.record_path == original.record_path


class TestFromRecord:
    def test_from_resource_record(self):
        record = ResourceRecord(id="r1", type="task")
        ref = FsRecordRef.from_record(record)
        assert ref.id == "r1"
        assert ref.type == "task"
        assert ref.record_path is None

    def test_from_record_with_source_file(self):
        record = ResourceRecord(id="r2", type="session", source_file="/tmp/r.json")
        ref = FsRecordRef.from_record(record)
        assert ref.record_path == "/tmp/r.json"
