"""Tests for ResourceRecordList – CRUD + all three StorageLayout modes."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from fs_store import ResourceRecord, ResourceRecordList, StorageLayout


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class TaggedRecord(ResourceRecord):
    """Record subclass with a custom uid field for testing."""
    uid_field_name = "tag_id"
    tag_id: str = field(default="")


def _make_list(tmp_path: Path, layout: StorageLayout,
               record_class=ResourceRecord) -> ResourceRecordList:
    if layout == StorageLayout.LIST_ITEM:
        path = tmp_path / "data.jsonl"
    else:
        path = tmp_path / "store"
    return ResourceRecordList(
        list_path=path,
        record_class=record_class,
        storage_layout=layout,
    )


# ---------------------------------------------------------------------------
# Parametrize across all three layouts
# ---------------------------------------------------------------------------

ALL_LAYOUTS = [StorageLayout.LIST_ITEM, StorageLayout.FILE, StorageLayout.FOLDER]


class TestCrudAllLayouts:
    """CRUD operations that must work identically across all storage layouts."""

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_create_and_get(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        r = rl.create(ResourceRecord(id="1", type="rule", name="alpha"))
        assert r.uid == "1"
        assert rl.get("1") is r
        assert len(rl) == 1

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_create_from_dict(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        r = rl.create({"id": "d1", "type": "hook", "name": "from-dict"})
        assert r.id == "d1"
        assert r.name == "from-dict"
        assert rl.get("d1") is r

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_create_duplicate_raises(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        rl.create(ResourceRecord(id="dup", type="t"))
        with pytest.raises(ValueError, match="already exists"):
            rl.create(ResourceRecord(id="dup", type="t"))

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_get_missing_returns_none(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        assert rl.get("nope") is None

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_update(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        rl.create(ResourceRecord(id="u1", type="t", name="before"))
        updated = rl.update("u1", {"name": "after", "custom": 42})
        assert updated.name == "after"
        assert updated.extra["custom"] == 42

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_update_missing_raises(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        with pytest.raises(KeyError, match="No record"):
            rl.update("nope", {"name": "x"})

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_delete(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        rl.create(ResourceRecord(id="d1", type="t"))
        assert rl.delete("d1") is True
        assert len(rl) == 0
        assert rl.get("d1") is None

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_delete_missing_returns_false(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        assert rl.delete("ghost") is False

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_iteration(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        rl.create(ResourceRecord(id="a", type="t"))
        rl.create(ResourceRecord(id="b", type="t"))
        uids = [r.uid for r in rl]
        assert "a" in uids
        assert "b" in uids

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_records_property(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        rl.create(ResourceRecord(id="r1", type="t"))
        recs = rl.records
        assert len(recs) == 1
        assert recs[0].uid == "r1"


# ---------------------------------------------------------------------------
# Persistence round-trip per layout
# ---------------------------------------------------------------------------

class TestPersistenceRoundTrip:
    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_save_and_reload(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        rl.create(ResourceRecord(id="s1", type="session", name="first"))
        rl.create(ResourceRecord(id="s2", type="session", name="second"))
        rl.save()

        rl2 = _make_list(tmp_path, layout)
        loaded = rl2.load()
        assert len(loaded) == 2
        assert {r.uid for r in rl2} == {"s1", "s2"}

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_delete_then_save_removes_from_disk(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        rl.create(ResourceRecord(id="x1", type="t", name="keep"))
        rl.create(ResourceRecord(id="x2", type="t", name="remove"))
        rl.save()

        rl.delete("x2")
        rl.save()

        rl2 = _make_list(tmp_path, layout)
        rl2.load()
        assert len(rl2) == 1
        assert rl2.get("x1").name == "keep"
        assert rl2.get("x2") is None

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_update_then_save_persists(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        rl.create(ResourceRecord(id="u1", type="t", name="v1"))
        rl.save()

        rl.update("u1", {"name": "v2"})
        rl.save()

        rl2 = _make_list(tmp_path, layout)
        rl2.load()
        assert rl2.get("u1").name == "v2"


# ---------------------------------------------------------------------------
# Lazy loading
# ---------------------------------------------------------------------------

class TestLazyLoading:
    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_auto_loads_on_first_access(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        rl.create(ResourceRecord(id="lazy", type="t"))
        rl.save()

        rl2 = _make_list(tmp_path, layout)
        # No explicit load() — should auto-load
        assert rl2.get("lazy").uid == "lazy"

    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_load_empty(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout)
        result = rl.load()
        assert result == []
        assert len(rl) == 0


# ---------------------------------------------------------------------------
# Naming convention: <type>-@<uid>
# ---------------------------------------------------------------------------

class TestNamingConvention:
    def test_file_layout_uses_stem(self, tmp_path):
        rl = _make_list(tmp_path, StorageLayout.FILE)
        rl.create(ResourceRecord(id="abc", type="hook", name="h1"))
        rl.save()
        expected = tmp_path / "store" / "hook-@abc.json"
        assert expected.exists()

    def test_folder_layout_uses_stem(self, tmp_path):
        rl = _make_list(tmp_path, StorageLayout.FOLDER)
        rl.create(ResourceRecord(id="def", type="session", name="s1"))
        rl.save()
        expected_dir = tmp_path / "store" / "session-@def"
        assert expected_dir.is_dir()
        assert (expected_dir / "record.json").exists()

    def test_folder_record_has_path(self, tmp_path):
        rl = _make_list(tmp_path, StorageLayout.FOLDER)
        r = rl.create(ResourceRecord(id="p1", type="session"))
        rl.save()
        assert r.path == str(tmp_path / "store" / "session-@p1")

    def test_file_layout_orphan_cleanup(self, tmp_path):
        rl = _make_list(tmp_path, StorageLayout.FILE)
        rl.create(ResourceRecord(id="keep", type="t"))
        rl.create(ResourceRecord(id="gone", type="t"))
        rl.save()
        assert (tmp_path / "store" / "t-@gone.json").exists()

        rl.delete("gone")
        rl.save()
        assert not (tmp_path / "store" / "t-@gone.json").exists()
        assert (tmp_path / "store" / "t-@keep.json").exists()

    def test_folder_layout_orphan_cleanup(self, tmp_path):
        rl = _make_list(tmp_path, StorageLayout.FOLDER)
        rl.create(ResourceRecord(id="keep", type="t"))
        rl.create(ResourceRecord(id="gone", type="t"))
        rl.save()
        assert (tmp_path / "store" / "t-@gone").is_dir()

        rl.delete("gone")
        rl.save()
        assert not (tmp_path / "store" / "t-@gone").exists()
        assert (tmp_path / "store" / "t-@keep").is_dir()


# ---------------------------------------------------------------------------
# Custom uid_field_name with list
# ---------------------------------------------------------------------------

class TestCustomUidInList:
    @pytest.mark.parametrize("layout", ALL_LAYOUTS)
    def test_crud_with_custom_uid(self, tmp_path, layout):
        rl = _make_list(tmp_path, layout, record_class=TaggedRecord)
        r = rl.create(TaggedRecord(tag_id="t-1", type="tag", name="first"))
        assert r.uid == "t-1"
        assert rl.get("t-1") is r

        rl.update("t-1", {"name": "updated"})
        assert rl.get("t-1").name == "updated"

        rl.save()
        rl2 = _make_list(tmp_path, layout, record_class=TaggedRecord)
        rl2.load()
        assert rl2.get("t-1").name == "updated"

    def test_folder_layout_custom_uid_naming(self, tmp_path):
        rl = _make_list(tmp_path, StorageLayout.FOLDER, record_class=TaggedRecord)
        rl.create(TaggedRecord(tag_id="tg-99", type="tag"))
        rl.save()
        expected = tmp_path / "store" / "tag-@tg-99"
        assert expected.is_dir()

    def test_file_layout_custom_uid_naming(self, tmp_path):
        rl = _make_list(tmp_path, StorageLayout.FILE, record_class=TaggedRecord)
        rl.create(TaggedRecord(tag_id="tg-99", type="tag"))
        rl.save()
        expected = tmp_path / "store" / "tag-@tg-99.json"
        assert expected.exists()


# ---------------------------------------------------------------------------
# FOLDER layout: extra files alongside record.json
# ---------------------------------------------------------------------------

class TestFolderExtraFiles:
    def test_folder_preserves_extra_files_on_save(self, tmp_path):
        """Saving a folder-layout record should not destroy sibling files."""
        rl = _make_list(tmp_path, StorageLayout.FOLDER)
        rl.create(ResourceRecord(id="f1", type="session"))
        rl.save()

        # Simulate an output file written by the session
        rec_dir = tmp_path / "store" / "session-@f1"
        output = rec_dir / "output.txt"
        output.write_text("some output")

        # Re-save — the output file should survive
        rl.update("f1", {"name": "renamed"})
        rl.save()
        assert output.exists()
        assert output.read_text() == "some output"


# ---------------------------------------------------------------------------
# LIST_ITEM (JSONL) specific
# ---------------------------------------------------------------------------

class TestJsonlSpecific:
    def test_jsonl_file_format(self, tmp_path):
        rl = _make_list(tmp_path, StorageLayout.LIST_ITEM)
        rl.create(ResourceRecord(id="j1", type="t", name="a"))
        rl.create(ResourceRecord(id="j2", type="t", name="b"))
        rl.save()

        lines = (tmp_path / "data.jsonl").read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["id"] == "j1"
        assert json.loads(lines[1])["id"] == "j2"

    def test_jsonl_skips_bad_lines(self, tmp_path):
        fp = tmp_path / "data.jsonl"
        fp.write_text('{"id":"ok","type":"t","name":"good"}\n{bad json\n')
        rl = ResourceRecordList(
            list_path=fp,
            storage_layout=StorageLayout.LIST_ITEM,
        )
        rl.load()
        assert len(rl) == 1
        assert rl.get("ok").name == "good"
