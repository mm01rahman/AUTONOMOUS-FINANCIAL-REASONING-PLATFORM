"""Unit tests for IKROS Institutional Research Memory — WP-IMP-0044."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tools.ikros.graph import GraphNode, KnowledgeGraph, NodeType
from tools.ikros.memory import (
    MemoryError,
    MemoryLifecycleState,
    MemoryQuery,
    MemoryRecord,
    MemoryTier,
    MemoryValidationError,
    MemoryVersion,
    ResearchMemoryManager,
    WorkingMemorySnapshot,
    YAMLMemoryRepository,
    assert_memory_valid,
    find_archive_integrity_issues,
    find_broken_lineage,
    is_valid_memory_id,
    make_memory_id,
    validate_memory_record,
    validate_memory_store,
)


def _graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()
    graph.add_node(
        GraphNode(
            node_id="IKROS-RQ-20260802-0001",
            ikros_id="IKROS-RQ-20260802-0001",
            node_type=NodeType.RESEARCH_QUESTION,
            label="Research question",
            confidence=0.4,
        )
    )
    graph.add_node(
        GraphNode(
            node_id="IKROS-HYP-20260802-0001",
            ikros_id="IKROS-HYP-20260802-0001",
            node_type=NodeType.HYPOTHESIS,
            label="Hypothesis",
            confidence=0.6,
        )
    )
    graph.add_node(
        GraphNode(
            node_id="IKROS-EXP-20260802-0001",
            ikros_id="IKROS-EXP-20260802-0001",
            node_type=NodeType.EXPERIMENT,
            label="Experiment",
            confidence=0.7,
        )
    )
    graph.add_node(
        GraphNode(
            node_id="IKROS-ALPHA-20260802-0001",
            ikros_id="IKROS-ALPHA-20260802-0001",
            node_type=NodeType.ALPHA,
            label="Alpha",
            confidence=0.8,
        )
    )
    return graph


def _record(
    memory_id: str,
    *,
    tier: str = MemoryTier.EPISODIC,
    entity_type: str = "Hypothesis",
    title: str = "Record",
    source_ids: list[str] | None = None,
    graph_node_ids: list[str] | None = None,
    confidence: float = 0.5,
    lifecycle_state: str = MemoryLifecycleState.ACTIVE,
    spec_refs: list[str] | None = None,
    capability_refs: list[str] | None = None,
    work_package_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    lineage_ids: list[str] | None = None,
    dependency_ids: list[str] | None = None,
    tags: list[str] | None = None,
    payload: dict[str, object] | None = None,
    created_at: str = "2026-08-02T00:00:00+00:00",
) -> MemoryRecord:
    return MemoryRecord(
        memory_id=memory_id,
        tier=tier,
        entity_type=entity_type,
        title=title,
        summary=f"{title} summary",
        source_ids=(
            ["IKROS-HYP-20260802-0001"] if source_ids is None else source_ids
        ),
        evidence_refs=(
            ["05-work-packages/WP-IMP-0044/evidence/EXEC-046.yaml"]
            if evidence_refs is None
            else evidence_refs
        ),
        spec_refs=["SPEC-060"] if spec_refs is None else spec_refs,
        capability_refs=(
            ["IKROS-MEMORY"] if capability_refs is None else capability_refs
        ),
        work_package_refs=(
            ["WP-IMP-0044"] if work_package_refs is None else work_package_refs
        ),
        graph_node_ids=(
            ["IKROS-HYP-20260802-0001"]
            if graph_node_ids is None
            else graph_node_ids
        ),
        lineage_ids=[] if lineage_ids is None else lineage_ids,
        dependency_ids=[] if dependency_ids is None else dependency_ids,
        tags=["memory"] if tags is None else tags,
        payload={"kind": title} if payload is None else payload,
        confidence=confidence,
        lifecycle_state=lifecycle_state,
        created_at=created_at,
        updated_at=created_at,
    )


class TestMemoryModels:
    def test_make_memory_id(self) -> None:
        memory_id = make_memory_id(MemoryTier.WORKING)
        assert memory_id.startswith("IKMEM-T0-")

    def test_validate_memory_id(self) -> None:
        assert is_valid_memory_id("IKMEM-T4-20260802-0001") is True
        assert is_valid_memory_id("IKROS-T4-20260802-0001") is False

    def test_memory_record_round_trip(self) -> None:
        record = _record("IKMEM-T1-20260802-0001")
        round_tripped = MemoryRecord.from_dict(record.to_dict())
        assert round_tripped.memory_id == record.memory_id
        assert round_tripped.tier == record.tier
        assert round_tripped.source_ids == record.source_ids

    def test_working_snapshot_to_record(self) -> None:
        snapshot = WorkingMemorySnapshot(
            session_id="SESSION-001",
            active_research_question="IKROS-RQ-20260802-0001",
            active_experiment="IKROS-EXP-20260802-0001",
            active_hypotheses=["IKROS-HYP-20260802-0001"],
            active_features=["IKROS-FEAT-20260802-0001"],
            current_confidence=0.4,
        )
        record = snapshot.to_record("IKMEM-T0-20260802-0001")
        assert record.tier == MemoryTier.WORKING
        assert record.entity_type == "WorkingMemory"
        assert "session_id" in record.payload

    def test_memory_version_round_trip(self) -> None:
        version = MemoryVersion(
            version="1.0.0",
            changed_at="2026-08-02T00:00:00+00:00",
            change_summary="Created",
        )
        assert MemoryVersion.from_dict(version.to_dict()) == version


class TestMemoryValidation:
    def test_valid_memory_record(self) -> None:
        graph = _graph()
        record = _record("IKMEM-T1-20260802-0001")
        assert validate_memory_record(record, {}, graph) == []

    def test_invalid_memory_id(self) -> None:
        record = _record("BAD-ID")
        errors = validate_memory_record(record)
        assert any("memory_id" in error for error in errors)

    def test_invalid_confidence(self) -> None:
        record = _record("IKMEM-T1-20260802-0001", confidence=1.5)
        errors = validate_memory_record(record)
        assert any("confidence" in error for error in errors)

    def test_non_working_requires_source_or_graph_ref(self) -> None:
        record = _record(
            "IKMEM-T1-20260802-0001",
            source_ids=[],
            graph_node_ids=[],
        )
        errors = validate_memory_record(record)
        assert any("non-working memory" in error for error in errors)

    def test_archived_requires_archived_at(self) -> None:
        record = _record(
            "IKMEM-T5-20260802-0001",
            tier=MemoryTier.ARCHIVE,
            lifecycle_state=MemoryLifecycleState.ARCHIVED,
        )
        errors = validate_memory_record(record)
        assert any("archived_at" in error for error in errors)

    def test_retired_requires_retired_at(self) -> None:
        record = _record(
            "IKMEM-T1-20260802-0001",
            lifecycle_state=MemoryLifecycleState.RETIRED,
        )
        errors = validate_memory_record(record)
        assert any("retired_at" in error for error in errors)

    def test_graph_reference_must_exist(self) -> None:
        graph = _graph()
        record = _record(
            "IKMEM-T1-20260802-0001",
            graph_node_ids=["IKROS-NONEXISTENT-20260802-0001"],
        )
        errors = validate_memory_record(record, {}, graph)
        assert any("graph node" in error for error in errors)

    def test_lineage_reference_must_exist(self) -> None:
        record = _record(
            "IKMEM-T1-20260802-0001",
            lineage_ids=["IKMEM-T1-20260802-9999"],
        )
        errors = validate_memory_record(record, {}, None)
        assert any("lineage memory" in error for error in errors)

    def test_duplicate_fingerprint_detected(self) -> None:
        first = _record("IKMEM-T1-20260802-0001")
        second = _record("IKMEM-T1-20260802-0002")
        errors = validate_memory_store(
            {
                first.memory_id: first,
                second.memory_id: second,
            }
        )
        assert any("duplicate" in error for error in errors)

    def test_assert_memory_valid_raises(self) -> None:
        invalid = _record("BAD-ID")
        with pytest.raises(MemoryValidationError):
            assert_memory_valid({invalid.memory_id: invalid})

    def test_find_archive_integrity_issues(self) -> None:
        archived = _record(
            "IKMEM-T5-20260802-0001",
            tier=MemoryTier.ARCHIVE,
            lifecycle_state=MemoryLifecycleState.ARCHIVED,
        )
        assert find_archive_integrity_issues({archived.memory_id: archived}) == [
            archived.memory_id
        ]

    def test_find_broken_lineage(self) -> None:
        record = _record(
            "IKMEM-T1-20260802-0001",
            lineage_ids=["IKMEM-T1-20260802-9999"],
        )
        assert find_broken_lineage({record.memory_id: record}) == [record.memory_id]


class TestResearchMemoryManager:
    def test_store_and_get(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record("IKMEM-T1-20260802-0001")
        manager.store(record)
        assert manager.get(record.memory_id).memory_id == record.memory_id

    def test_store_duplicate_id_raises(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record("IKMEM-T1-20260802-0001")
        manager.store(record)
        with pytest.raises(MemoryError):
            manager.store(_record("IKMEM-T1-20260802-0001", title="Other"))

    def test_store_duplicate_content_raises(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        manager.store(_record("IKMEM-T1-20260802-0001"))
        with pytest.raises(MemoryError):
            manager.store(_record("IKMEM-T1-20260802-0002"))

    def test_store_working_memory(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        snapshot = WorkingMemorySnapshot(session_id="SESSION-001")
        memory_id = manager.store_working_memory(snapshot)
        assert manager.get(memory_id).tier == MemoryTier.WORKING

    def test_list_by_tier(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        manager.store(_record("IKMEM-T1-20260802-0001", tier=MemoryTier.EPISODIC))
        manager.store(
            _record(
                "IKMEM-T2-20260802-0001",
                tier=MemoryTier.SEMANTIC,
                title="Semantic record",
            )
        )
        assert len(manager.list_by_tier(MemoryTier.EPISODIC)) == 1

    def test_next_id_uses_tier_code(self) -> None:
        manager = ResearchMemoryManager()
        assert manager.next_id(MemoryTier.PROCEDURAL).startswith("IKMEM-T3-")

    def test_promote(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record("IKMEM-T1-20260802-0001", tier=MemoryTier.EPISODIC)
        manager.store(record)
        promoted = manager.promote(record.memory_id, MemoryTier.SEMANTIC)
        assert promoted.tier == MemoryTier.SEMANTIC
        assert promoted.lifecycle_state == MemoryLifecycleState.PROMOTED

    def test_invalid_tier_transition_raises(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record("IKMEM-T4-20260802-0001", tier=MemoryTier.INSTITUTIONAL)
        manager.store(record)
        with pytest.raises(MemoryError):
            manager.promote(record.memory_id, MemoryTier.WORKING)

    def test_default_consolidation_working_to_episodic(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record(
            "IKMEM-T0-20260802-0001",
            tier=MemoryTier.WORKING,
            entity_type="WorkingMemory",
            title="Working",
        )
        manager.store(record)
        consolidated = manager.consolidate(record.memory_id)
        assert consolidated.tier == MemoryTier.EPISODIC

    def test_default_consolidation_failure_to_institutional(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record(
            "IKMEM-T1-20260802-0001",
            entity_type="Failure",
            title="Failure",
        )
        manager.store(record)
        consolidated = manager.consolidate(record.memory_id)
        assert consolidated.tier == MemoryTier.INSTITUTIONAL

    def test_default_consolidation_high_confidence_to_semantic(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record(
            "IKMEM-T1-20260802-0001",
            confidence=0.85,
        )
        manager.store(record)
        consolidated = manager.consolidate(record.memory_id)
        assert consolidated.tier == MemoryTier.SEMANTIC

    def test_merge_records(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        first = _record("IKMEM-T1-20260802-0001", title="First")
        second = _record(
            "IKMEM-T1-20260802-0002",
            title="Second",
            source_ids=["IKROS-EXP-20260802-0001"],
            graph_node_ids=["IKROS-EXP-20260802-0001"],
            payload={"kind": "Second"},
        )
        manager.store(first)
        manager.store(second)
        merged = manager.merge(
            [first.memory_id, second.memory_id],
            MemoryTier.INSTITUTIONAL,
            "Merged memory",
        )
        assert merged.lifecycle_state == MemoryLifecycleState.MERGED
        assert first.memory_id in merged.lineage_ids
        assert second.memory_id in merged.lineage_ids

    def test_retire_sets_metadata(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record("IKMEM-T1-20260802-0001")
        manager.store(record)
        retired = manager.retire(record.memory_id, "Superseded")
        assert retired.lifecycle_state == MemoryLifecycleState.RETIRED
        assert retired.retired_at is not None

    def test_archive_moves_to_archive_tier(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record("IKMEM-T4-20260802-0001", tier=MemoryTier.INSTITUTIONAL)
        manager.store(record)
        archived = manager.archive(record.memory_id, "Deprecated")
        assert archived.tier == MemoryTier.ARCHIVE
        assert archived.archived_at is not None

    def test_restore_from_archive(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record("IKMEM-T4-20260802-0001", tier=MemoryTier.INSTITUTIONAL)
        manager.store(record)
        manager.archive(record.memory_id, "Deprecated")
        restored = manager.restore(record.memory_id, MemoryTier.SEMANTIC)
        assert restored.tier == MemoryTier.SEMANTIC
        assert restored.lifecycle_state == MemoryLifecycleState.RESTORED
        assert restored.archived_at is None

    def test_restore_non_archived_raises(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record("IKMEM-T1-20260802-0001")
        manager.store(record)
        with pytest.raises(MemoryError):
            manager.restore(record.memory_id, MemoryTier.SEMANTIC)

    def test_summary(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        manager.store(_record("IKMEM-T1-20260802-0001"))
        summary = manager.summary()
        assert summary["record_count"] == 1
        assert "tier_counts" in summary


class TestMemoryRetrieval:
    def test_retrieve_by_identifier(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record("IKMEM-T1-20260802-0001")
        manager.store(record)
        result = manager.retrieve(MemoryQuery(identifier=record.memory_id))
        assert [item.memory_id for item in result] == [record.memory_id]

    def test_retrieve_by_entity_type(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        manager.store(_record("IKMEM-T1-20260802-0001", entity_type="Hypothesis"))
        manager.store(
            _record(
                "IKMEM-T1-20260802-0002",
                entity_type="Experiment",
                title="Experiment memory",
                source_ids=["IKROS-EXP-20260802-0001"],
                graph_node_ids=["IKROS-EXP-20260802-0001"],
                payload={"kind": "Experiment memory"},
            )
        )
        result = manager.retrieve(MemoryQuery(entity_type="Experiment"))
        assert [item.entity_type for item in result] == ["Experiment"]

    def test_retrieve_by_spec_capability_and_wp(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record("IKMEM-T1-20260802-0001")
        manager.store(record)
        result = manager.retrieve(
            MemoryQuery(
                specification="SPEC-060",
                capability="IKROS-MEMORY",
                work_package="WP-IMP-0044",
            )
        )
        assert [item.memory_id for item in result] == [record.memory_id]

    def test_retrieve_by_evidence(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record("IKMEM-T1-20260802-0001")
        manager.store(record)
        result = manager.retrieve(
            MemoryQuery(evidence="05-work-packages/WP-IMP-0044/evidence/EXEC-046.yaml")
        )
        assert [item.memory_id for item in result] == [record.memory_id]

    def test_retrieve_by_feature_ref(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        record = _record(
            "IKMEM-T1-20260802-0001",
            source_ids=["IKROS-FEAT-20260802-0001"],
            graph_node_ids=[],
        )
        manager.store(record)
        result = manager.retrieve(MemoryQuery(feature="IKROS-FEAT-20260802-0001"))
        assert len(result) == 1

    def test_retrieve_by_hypothesis_experiment_alpha(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        hypothesis = _record("IKMEM-T1-20260802-0001")
        experiment = _record(
            "IKMEM-T1-20260802-0002",
            entity_type="Experiment",
            title="Experiment memory",
            source_ids=["IKROS-EXP-20260802-0001"],
            graph_node_ids=["IKROS-EXP-20260802-0001"],
        )
        alpha = _record(
            "IKMEM-T1-20260802-0003",
            entity_type="Alpha",
            title="Alpha memory",
            source_ids=["IKROS-ALPHA-20260802-0001"],
            graph_node_ids=["IKROS-ALPHA-20260802-0001"],
        )
        manager.store(hypothesis)
        manager.store(experiment)
        manager.store(alpha)
        assert len(manager.retrieve(MemoryQuery(hypothesis="IKROS-HYP-20260802-0001"))) == 1
        assert len(manager.retrieve(MemoryQuery(experiment="IKROS-EXP-20260802-0001"))) == 1
        assert len(manager.retrieve(MemoryQuery(alpha="IKROS-ALPHA-20260802-0001"))) == 1

    def test_retrieve_by_lineage(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        parent = _record("IKMEM-T1-20260802-0001")
        child = _record(
            "IKMEM-T2-20260802-0001",
            tier=MemoryTier.SEMANTIC,
            title="Child",
            lineage_ids=[parent.memory_id],
            source_ids=["IKROS-HYP-20260802-0001"],
        )
        manager.store(parent)
        manager.store(child)
        result = manager.retrieve(MemoryQuery(lineage=parent.memory_id))
        assert [item.memory_id for item in result] == [child.memory_id]

    def test_retrieve_by_confidence_range(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        manager.store(_record("IKMEM-T1-20260802-0001", confidence=0.2))
        manager.store(
            _record(
                "IKMEM-T1-20260802-0002",
                confidence=0.8,
                title="High",
                source_ids=["IKROS-EXP-20260802-0001"],
                graph_node_ids=["IKROS-EXP-20260802-0001"],
                payload={"kind": "High"},
            )
        )
        result = manager.retrieve(MemoryQuery(min_confidence=0.7, max_confidence=0.9))
        assert [item.memory_id for item in result] == ["IKMEM-T1-20260802-0002"]

    def test_retrieve_by_temporal_range(self) -> None:
        manager = ResearchMemoryManager(graph=_graph())
        early = _record(
            "IKMEM-T1-20260801-0001",
            created_at="2026-08-01T00:00:00+00:00",
        )
        late = _record(
            "IKMEM-T1-20260803-0001",
            title="Late",
            source_ids=["IKROS-EXP-20260802-0001"],
            graph_node_ids=["IKROS-EXP-20260802-0001"],
            payload={"kind": "Late"},
            created_at="2026-08-03T00:00:00+00:00",
        )
        manager.store(early)
        manager.store(late)
        result = manager.retrieve(
            MemoryQuery(
                start_time="2026-08-02T00:00:00+00:00",
                end_time="2026-08-04T00:00:00+00:00",
            )
        )
        assert [item.memory_id for item in result] == [late.memory_id]


class TestYAMLMemoryRepository:
    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = YAMLMemoryRepository(Path(temp_dir))
            manager = ResearchMemoryManager(repository=repo, graph=_graph())
            first = _record("IKMEM-T1-20260802-0001")
            second = _record(
                "IKMEM-T2-20260802-0001",
                tier=MemoryTier.SEMANTIC,
                title="Semantic",
                source_ids=["IKROS-EXP-20260802-0001"],
                graph_node_ids=["IKROS-EXP-20260802-0001"],
                payload={"kind": "Semantic"},
            )
            manager.store(first)
            manager.store(second)
            reloaded = ResearchMemoryManager(repository=repo, graph=_graph())
            assert len(reloaded.list_all()) == 2

    def test_save_record_and_record_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = YAMLMemoryRepository(Path(temp_dir))
            repo.save_record(_record("IKMEM-T1-20260802-0001"))
            assert repo.record_ids() == ["IKMEM-T1-20260802-0001"]

    def test_persistence_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = YAMLMemoryRepository(Path(temp_dir))
            records = {
                "IKMEM-T2-20260802-0001": _record(
                    "IKMEM-T2-20260802-0001",
                    tier=MemoryTier.SEMANTIC,
                    title="Semantic",
                    source_ids=["IKROS-EXP-20260802-0001"],
                    graph_node_ids=["IKROS-EXP-20260802-0001"],
                    payload={"kind": "Semantic"},
                ),
                "IKMEM-T1-20260802-0001": _record("IKMEM-T1-20260802-0001"),
            }
            repo.save(records)
            first_load = [record.memory_id for record in repo.load()]
            second_load = [record.memory_id for record in repo.load()]
            assert first_load == second_load
