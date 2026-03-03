"""Tests for RelationshipRecord."""

from flow_sdk.fs_store import RecordRef
from flow_sdk.fs_records import RelationshipRecord, RelationshipType


class TestRelationshipRecord:
    def test_child_factory_sets_type_and_id(self):
        from_ref = RecordRef(id="task-1", type="task")
        to_ref = RecordRef(id="proc-1", type="agentic_process")

        rel = RelationshipRecord.child(from_ref=from_ref, to_ref=to_ref)

        assert rel.type == RelationshipType.CHILD
        assert rel.id == "child:task:task-1:agentic_process:proc-1"
        assert rel.from_ref == from_ref
        assert rel.to_ref == to_ref

    def test_to_dict_contains_refs(self):
        rel = RelationshipRecord(
            id="r1",
            type=RelationshipType.CHILD,
            from_ref=RecordRef(id="task-1", type="task"),
            to_ref=RecordRef(id="proc-1", type="agentic_process"),
        )

        data = rel.to_dict()
        assert data["type"] == "child"
        assert data["from_ref"] == {"id": "task-1", "type": "task"}
        assert data["to_ref"] == {"id": "proc-1", "type": "agentic_process"}

    def test_from_dict_restores_ref_types(self):
        data = {
            "id": "r1",
            "type": "child",
            "from_ref": {"id": "task-1", "type": "task"},
            "to_ref": {"id": "proc-1", "type": "agentic_process"},
        }

        rel = RelationshipRecord.from_dict(data)
        assert isinstance(rel.from_ref, RecordRef)
        assert isinstance(rel.to_ref, RecordRef)
        assert rel.from_ref.id == "task-1"
        assert rel.to_ref.id == "proc-1"
