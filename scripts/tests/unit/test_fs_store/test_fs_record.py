"""Tests for FsRecord – filesystem I/O (from_json / to_json / persist)."""

import json

import pytest

from fs_store import FsRecord, FsRecordRef, ResourceRecord, Scope
from records import TaskResource, TaskStatus, TaskType, AgenticProcess, ProcessorStatus


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
        r.save()
        assert fp.exists()
        data = json.loads(fp.read_text())
        assert data["key"] == "val"

    def test_persist_without_source_file_raises(self):
        r = FsRecord()
        r.source_file = None
        with pytest.raises(ValueError):
            r.save()


# ---------------------------------------------------------------------------
# Children + JSON file round-trip
# ---------------------------------------------------------------------------

class TestChildrenFileIO:
    def test_children_refs_json_file_round_trip(self, tmp_path):
        fp = tmp_path / "nested.json"
        parent = FsRecord(id="p", type="session")
        parent.children_refs = [
            FsRecordRef(id="c1", type="step"),
            FsRecordRef(id="c2", type="step"),
        ]
        parent.to_json(fp)

        loaded = FsRecord.from_json(fp)
        assert len(loaded.children_refs) == 2
        assert isinstance(loaded.children_refs[0], FsRecordRef)
        assert loaded.children_refs[0].id == "c1"


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


# ---------------------------------------------------------------------------
# Parent-child hierarchy with concrete record types
# ---------------------------------------------------------------------------

class TestParentChildFsRecord:
    def test_task_with_agentic_process_child_refs_round_trip(self, tmp_path):
        fp = tmp_path / "task.json"
        task = TaskResource(
            id="task-1",
            title="Analysis",
            status=TaskStatus.IN_PROGRESS,
            task_type=TaskType.ANALYSIS,
        )
        process = AgenticProcess(
            id="proc-1",
            state=ProcessorStatus.RUNNING,
            worker_id="session-1",
            parent_ref=FsRecordRef(id="task-1", type="task"),
        )
        task.children_refs = [FsRecordRef.from_record(process)]
        task.to_json(fp)

        loaded = FsRecord.from_json(fp)
        assert loaded.id == "task-1"
        assert len(loaded.children_refs) == 1
        child_ref = loaded.children_refs[0]
        assert isinstance(child_ref, FsRecordRef)
        assert child_ref.id == "proc-1"

    def test_parent_ref_persists_through_file_io(self, tmp_path):
        fp = tmp_path / "record.json"
        r = FsRecord(id="child-rec", parent_ref=FsRecordRef(id="parent-rec", type="session"))
        r.to_json(fp)

        loaded = FsRecord.from_json(fp)
        assert isinstance(loaded.parent_ref, FsRecordRef)
        assert loaded.parent_ref.id == "parent-rec"


# ---------------------------------------------------------------------------
# Live parent/children properties — resolve refs from distributed folders
# ---------------------------------------------------------------------------

class TestLiveParentProperty:
    def test_parent_returns_none_when_no_ref(self):
        r = FsRecord(id="orphan")
        assert r.parent is None

    def test_parent_returns_none_when_no_record_path(self):
        r = FsRecord(id="child", parent_ref=FsRecordRef(id="p", type="task"))
        assert r.parent is None

    def test_parent_returns_none_when_file_missing(self):
        r = FsRecord(
            id="child",
            parent_ref=FsRecordRef(id="p", type="task", record_path="/nonexistent/p.json"),
        )
        assert r.parent is None

    def test_parent_loads_from_disk(self, tmp_path):
        # Save parent in one folder
        parent_fp = tmp_path / "folder_a" / "parent.json"
        parent = FsRecord(id="p", type="task", name="Parent Task")
        parent.to_json(parent_fp)

        # Child in a different folder points to parent via record_path
        child = FsRecord(
            id="c",
            type="process",
            parent_ref=FsRecordRef(id="p", type="task", record_path=str(parent_fp)),
        )

        loaded_parent = child.parent
        assert loaded_parent is not None
        assert loaded_parent.id == "p"
        assert loaded_parent.name == "Parent Task"

    def test_parent_loaded_across_folders(self, tmp_path):
        """Parent and child live in completely separate directory trees."""
        parent_fp = tmp_path / "projects" / "alpha" / "task.json"
        child_fp = tmp_path / "workers" / "beta" / "process.json"

        parent = FsRecord(id="task-1", type="task", name="Alpha Task")
        parent.to_json(parent_fp)

        child = FsRecord(
            id="proc-1",
            type="process",
            parent_ref=FsRecordRef(id="task-1", type="task", record_path=str(parent_fp)),
        )
        child.to_json(child_fp)

        # Reload child from disk, then resolve parent
        reloaded = FsRecord.from_json(child_fp)
        live_parent = reloaded.parent
        assert live_parent is not None
        assert live_parent.id == "task-1"
        assert live_parent.name == "Alpha Task"


class TestLiveChildrenProperty:
    def test_children_empty_when_no_refs(self):
        r = FsRecord(id="leaf")
        assert r.children == []

    def test_children_skips_refs_without_record_path(self):
        r = FsRecord(
            id="p",
            children_refs=[FsRecordRef(id="c1", type="step")],
        )
        assert r.children == []

    def test_children_skips_missing_files(self):
        r = FsRecord(
            id="p",
            children_refs=[
                FsRecordRef(id="c1", type="step", record_path="/nonexistent/c1.json"),
            ],
        )
        assert r.children == []

    def test_children_loads_from_disk(self, tmp_path):
        # Save two children in separate folders
        c1_fp = tmp_path / "steps" / "c1.json"
        c2_fp = tmp_path / "steps" / "c2.json"
        FsRecord(id="c1", type="step", name="Step One").to_json(c1_fp)
        FsRecord(id="c2", type="step", name="Step Two").to_json(c2_fp)

        parent = FsRecord(
            id="p",
            type="session",
            children_refs=[
                FsRecordRef(id="c1", type="step", record_path=str(c1_fp)),
                FsRecordRef(id="c2", type="step", record_path=str(c2_fp)),
            ],
        )

        kids = parent.children
        assert len(kids) == 2
        assert kids[0].id == "c1"
        assert kids[0].name == "Step One"
        assert kids[1].id == "c2"

    def test_children_distributed_across_folders(self, tmp_path):
        """Each child record lives in a completely different directory tree."""
        c1_fp = tmp_path / "region_us" / "worker_a" / "step.json"
        c2_fp = tmp_path / "region_eu" / "worker_b" / "step.json"
        FsRecord(id="c1", type="step", name="US Step").to_json(c1_fp)
        FsRecord(id="c2", type="step", name="EU Step").to_json(c2_fp)

        parent_fp = tmp_path / "orchestrator" / "session.json"
        parent = FsRecord(
            id="sess",
            type="session",
            children_refs=[
                FsRecordRef(id="c1", type="step", record_path=str(c1_fp)),
                FsRecordRef(id="c2", type="step", record_path=str(c2_fp)),
            ],
        )
        parent.to_json(parent_fp)

        # Reload parent from disk, then resolve children
        reloaded = FsRecord.from_json(parent_fp)
        kids = reloaded.children
        assert len(kids) == 2
        assert {k.name for k in kids} == {"US Step", "EU Step"}

    def test_children_skips_missing_but_loads_existing(self, tmp_path):
        """Partial resolution: one child exists on disk, another doesn't."""
        c1_fp = tmp_path / "c1.json"
        FsRecord(id="c1", type="step", name="Exists").to_json(c1_fp)

        parent = FsRecord(
            id="p",
            children_refs=[
                FsRecordRef(id="c1", type="step", record_path=str(c1_fp)),
                FsRecordRef(id="c2", type="step", record_path="/gone/c2.json"),
                FsRecordRef(id="c3", type="step"),  # no record_path
            ],
        )

        kids = parent.children
        assert len(kids) == 1
        assert kids[0].id == "c1"


class TestLiveRoundTrip:
    def test_full_hierarchy_across_folders(self, tmp_path):
        """Build a parent→child hierarchy where each record is in its own folder,
        save all to disk, then resolve the full tree from any starting point."""
        parent_fp = tmp_path / "tasks" / "task.json"
        child_fp = tmp_path / "processes" / "proc.json"

        # Create and save child first (so we know its path for the ref)
        child = FsRecord(id="proc-1", type="process", name="Worker")
        child.to_json(child_fp)

        # Create parent with ref pointing to saved child
        parent = FsRecord(
            id="task-1",
            type="task",
            name="Analysis",
            children_refs=[FsRecordRef(id="proc-1", type="process", record_path=str(child_fp))],
        )
        parent.to_json(parent_fp)

        # Update child with ref pointing back to parent
        child.parent_ref = FsRecordRef(id="task-1", type="task", record_path=str(parent_fp))
        child.to_json()

        # Now verify: load parent → resolve children → from child resolve parent
        loaded_parent = FsRecord.from_json(parent_fp)
        kids = loaded_parent.children
        assert len(kids) == 1
        assert kids[0].id == "proc-1"
        assert kids[0].name == "Worker"

        # From child, resolve back to parent
        grandparent = kids[0].parent
        assert grandparent is not None
        assert grandparent.id == "task-1"
        assert grandparent.name == "Analysis"
