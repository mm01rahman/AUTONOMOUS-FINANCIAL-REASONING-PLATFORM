"""Unit tests for the IKROS Institutional Query Engine — WP-IMP-0045."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import cast

import pytest

from tools.ikros.graph import EdgeType, GraphEdge, GraphNode, KnowledgeGraph, NodeType
from tools.ikros.memory import (
    MemoryLifecycleState,
    MemoryRecord,
    MemoryTier,
    ResearchMemoryManager,
)
from tools.ikros.models import (
    Alpha,
    AlphaCandidate,
    AlphaPaperStatus,
    ConfidenceVector,
    Experiment,
    ExperimentStatus,
    Feature,
    FeatureFamily,
    Hypothesis,
    HypothesisStatus,
    IKROSEntity,
    LineageDependencies,
    LineageEvidence,
    LineageExperiments,
    LineageOrigin,
    LineageRecord,
    PromotionStatus,
    ResearchQuestion,
    ResearchStatus,
    Stationarity,
    StrategyType,
)
from tools.ikros.query import (
    GraphOperation,
    QueryAuditLog,
    QueryEngine,
    QueryParseError,
    QueryParser,
    QueryValidationError,
)
from tools.ikros.registries.alpha import AlphaRegistry
from tools.ikros.registries.base import BaseRegistry
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.feature import FeatureRegistry
from tools.ikros.registries.hypothesis import HypothesisRegistry
from tools.ikros.registries.research import ResearchRegistry


def _origin(context: str = "wp45-test") -> LineageOrigin:
    return LineageOrigin(
        created_by="test-agent",
        created_at="2026-08-02T00:00:00Z",
        creation_context=context,
        motivation="query-engine test fixture",
    )


def _lineage(context: str = "wp45-test") -> LineageRecord:
    return LineageRecord(origin=_origin(context))


def _confidence(level: float = 0.6) -> ConfidenceVector:
    return ConfidenceVector(
        statistical=level,
        economic=max(level - 0.1, 0.0),
        data=min(level + 0.1, 0.95),
    )


def _rq(ikros_id: str = "IKROS-RQ-20260802-0001") -> ResearchQuestion:
    return ResearchQuestion(
        ikros_id=ikros_id,
        entity_type="ResearchQuestion",
        version="1.0.0",
        lifecycle_state=ResearchStatus.ACTIVE.value,
        confidence=_confidence(0.55),
        lineage=_lineage(),
        spec_refs=["SPEC-060"],
        capability_refs=["IKROS-QUERY"],
        work_package_refs=["WP-IMP-0045"],
        title="Does regime persistence create gold alpha?",
        motivation="Institutional query testing",
        instrument="XAU/USD",
        scope="MACRO",
        time_horizon="1D",
        campaign_tag="PHASE-Q",
    )


def _hyp(
    ikros_id: str = "IKROS-HYP-20260802-0001",
    rq_id: str = "IKROS-RQ-20260802-0001",
) -> Hypothesis:
    return Hypothesis(
        ikros_id=ikros_id,
        entity_type="Hypothesis",
        version="1.0.0",
        lifecycle_state=HypothesisStatus.SUPPORTED.value,
        confidence=_confidence(0.75),
        lineage=LineageRecord(
            origin=_origin(),
            dependencies=LineageDependencies(inputs=[rq_id]),
            experiments=LineageExperiments(
                tested_in=["IKROS-EXP-20260802-0001"],
                validated_by=["IKROS-VAL-20260802-0001"],
            ),
            evidence=LineageEvidence(
                ers_records=["05-work-packages/WP-IMP-0045/evidence/EXEC-047.yaml"]
            ),
        ),
        spec_refs=["SPEC-060"],
        capability_refs=["IKROS-QUERY"],
        work_package_refs=["WP-IMP-0045"],
        statement="XAU/USD regime persistence supports continuation alpha",
        null_hypothesis="H0: No continuation effect",
        alternative_hypothesis="H1: Regime persistence predicts continuation",
        significance_level=0.05,
        power=0.80,
        prior_confidence=0.35,
        source_rq=rq_id,
        experiments=["IKROS-EXP-20260802-0001"],
        validations=["IKROS-VAL-20260802-0001"],
        posterior_confidence=0.78,
    )


def _exp(
    ikros_id: str = "IKROS-EXP-20260802-0001",
    hyp_id: str = "IKROS-HYP-20260802-0001",
) -> Experiment:
    return Experiment(
        ikros_id=ikros_id,
        entity_type="Experiment",
        version="1.0.0",
        lifecycle_state=ExperimentStatus.COMPLETE.value,
        confidence=_confidence(0.70),
        lineage=LineageRecord(
            origin=_origin(),
            dependencies=LineageDependencies(
                inputs=[hyp_id],
                datasets=["IKROS-DSV-20260802-0001"],
                features=["IKROS-FEAT-20260802-0001"],
            ),
            evidence=LineageEvidence(
                ers_records=["05-work-packages/WP-IMP-0045/evidence/EXEC-047.yaml"]
            ),
        ),
        spec_refs=["SPEC-060"],
        capability_refs=["IKROS-QUERY"],
        work_package_refs=["WP-IMP-0045"],
        title="Regime persistence walk-forward study",
        hypotheses=[hyp_id],
        protocol="Walk-forward",
        dataset_versions=["IKROS-DSV-20260802-0001"],
        feature_versions=["IKROS-FEAT-20260802-0001"],
        parameters={"window": 63},
        random_seed=42,
        reproducibility_hash="abc123",
        validations_produced=["IKROS-VAL-20260802-0001"],
    )


def _feature_family(
    ikros_id: str = "IKROS-FF-20260802-0001",
) -> FeatureFamily:
    return FeatureFamily(
        ikros_id=ikros_id,
        entity_type="FeatureFamily",
        version="1.0.0",
        lifecycle_state="ACTIVE",
        confidence=_confidence(0.65),
        lineage=_lineage(),
        spec_refs=["SPEC-060"],
        capability_refs=["IKROS-QUERY"],
        work_package_refs=["WP-IMP-0045"],
        name="REGIME",
        description="Regime detection family",
        member_features=["IKROS-FEAT-20260802-0001"],
    )


def _feature(
    ikros_id: str = "IKROS-FEAT-20260802-0001",
    family_id: str = "IKROS-FF-20260802-0001",
) -> Feature:
    return Feature(
        ikros_id=ikros_id,
        entity_type="Feature",
        version="1.0.0",
        lifecycle_state="ACTIVE",
        confidence=_confidence(0.68),
        lineage=LineageRecord(
            origin=_origin(),
            dependencies=LineageDependencies(inputs=["close"]),
            evidence=LineageEvidence(
                ers_records=["05-work-packages/WP-IMP-0045/evidence/EXEC-047.yaml"]
            ),
        ),
        spec_refs=["SPEC-060"],
        capability_refs=["IKROS-QUERY"],
        work_package_refs=["WP-IMP-0045"],
        name="regime_persistence_score",
        family_id=family_id,
        computation="rolling regime persistence score",
        inputs=["close"],
        lookback="63 bars",
        normalization="z-score",
        stationarity=Stationarity.STATIONARY.value,
        information_content=0.71,
        stability_score=0.82,
    )


def _candidate(
    ikros_id: str = "IKROS-ALPHACAND-20260802-0001",
    hyp_id: str = "IKROS-HYP-20260802-0001",
) -> AlphaCandidate:
    return AlphaCandidate(
        ikros_id=ikros_id,
        entity_type="AlphaCandidate",
        version="1.0.0",
        lifecycle_state=PromotionStatus.CANDIDATE.value,
        confidence=_confidence(0.66),
        lineage=LineageRecord(
            origin=_origin(),
            dependencies=LineageDependencies(inputs=[hyp_id]),
            evidence=LineageEvidence(
                ers_records=["05-work-packages/WP-IMP-0045/evidence/EXEC-047.yaml"]
            ),
        ),
        spec_refs=["SPEC-060"],
        capability_refs=["IKROS-QUERY"],
        work_package_refs=["WP-IMP-0045"],
        name="regime_persistence_alpha_v1",
        strategy_type=StrategyType.TREND.value,
        sharpe_oos=1.12,
        max_drawdown=0.13,
        direction_accuracy=0.55,
        win_rate=0.53,
        promotion_score=0.72,
        implements_hypotheses=[hyp_id],
    )


def _alpha(
    ikros_id: str = "IKROS-ALPHA-20260802-0001",
    candidate_id: str = "IKROS-ALPHACAND-20260802-0001",
) -> Alpha:
    return Alpha(
        ikros_id=ikros_id,
        entity_type="Alpha",
        version="1.0.0",
        lifecycle_state=PromotionStatus.PROMOTED.value,
        confidence=_confidence(0.82),
        lineage=LineageRecord(
            origin=_origin(),
            dependencies=LineageDependencies(inputs=[candidate_id]),
            evidence=LineageEvidence(
                ers_records=["05-work-packages/WP-IMP-0045/evidence/EXEC-047.yaml"]
            ),
        ),
        spec_refs=["SPEC-060"],
        capability_refs=["IKROS-QUERY"],
        work_package_refs=["WP-IMP-0045"],
        promoted_from=candidate_id,
        promotion_date="2026-08-02T00:00:00Z",
        promotion_evidence="05-work-packages/WP-IMP-0045/evidence/EXEC-047.yaml",
        paper_trading_status=AlphaPaperStatus.ACTIVE.value,
        live_eligible=True,
    )


def _graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()
    for node_id, node_type, confidence in [
        ("IKROS-RQ-20260802-0001", NodeType.RESEARCH_QUESTION, 0.55),
        ("IKROS-HYP-20260802-0001", NodeType.HYPOTHESIS, 0.75),
        ("IKROS-EXP-20260802-0001", NodeType.EXPERIMENT, 0.70),
        ("IKROS-FEAT-20260802-0001", NodeType.FEATURE, 0.68),
        ("IKROS-DSV-20260802-0001", NodeType.DATASET_VERSION, 0.64),
        ("IKROS-ALPHACAND-20260802-0001", NodeType.ALPHA_CANDIDATE, 0.66),
        ("IKROS-ALPHA-20260802-0001", NodeType.ALPHA, 0.82),
        ("IKROS-EVID-20260802-0001", NodeType.EVIDENCE, 0.50),
    ]:
        graph.add_node(
            GraphNode(
                node_id=node_id,
                ikros_id=node_id,
                node_type=node_type,
                label=node_id,
                confidence=confidence,
                spec_refs=["SPEC-060"],
                wp_refs=["WP-IMP-0045"],
            )
        )
    graph.add_edge(
        GraphEdge(
            edge_id="IKROS-EDGE-20260802-0001",
            source_id="IKROS-RQ-20260802-0001",
            target_id="IKROS-HYP-20260802-0001",
            edge_type=EdgeType.DEPENDS_ON,
        )
    )
    graph.add_edge(
        GraphEdge(
            edge_id="IKROS-EDGE-20260802-0002",
            source_id="IKROS-HYP-20260802-0001",
            target_id="IKROS-EXP-20260802-0001",
            edge_type=EdgeType.TESTED_IN,
        )
    )
    graph.add_edge(
        GraphEdge(
            edge_id="IKROS-EDGE-20260802-0003",
            source_id="IKROS-EXP-20260802-0001",
            target_id="IKROS-ALPHACAND-20260802-0001",
            edge_type=EdgeType.GENERATED_ALPHA,
        )
    )
    graph.add_edge(
        GraphEdge(
            edge_id="IKROS-EDGE-20260802-0004",
            source_id="IKROS-ALPHACAND-20260802-0001",
            target_id="IKROS-ALPHA-20260802-0001",
            edge_type=EdgeType.PRODUCED,
        )
    )
    graph.add_edge(
        GraphEdge(
            edge_id="IKROS-EDGE-20260802-0005",
            source_id="IKROS-FEAT-20260802-0001",
            target_id="IKROS-DSV-20260802-0001",
            edge_type=EdgeType.DERIVED_FROM,
        )
    )
    graph.add_edge(
        GraphEdge(
            edge_id="IKROS-EDGE-20260802-0006",
            source_id="IKROS-EVID-20260802-0001",
            target_id="IKROS-ALPHA-20260802-0001",
            edge_type=EdgeType.CONTRADICTED_BY,
            evidence_ref="05-work-packages/WP-IMP-0045/evidence/EXEC-047.yaml",
        )
    )
    return graph


def _memory_manager() -> ResearchMemoryManager:
    manager = ResearchMemoryManager(graph=_graph())
    manager.store(
        MemoryRecord(
            memory_id="IKMEM-T2-20260802-0001",
            tier=MemoryTier.SEMANTIC,
            entity_type="Hypothesis",
            title="Semantic hypothesis memory",
            summary="Validated regime persistence hypothesis",
            source_ids=["IKROS-HYP-20260802-0001"],
            evidence_refs=["05-work-packages/WP-IMP-0045/evidence/EXEC-047.yaml"],
            spec_refs=["SPEC-060"],
            capability_refs=["IKROS-QUERY"],
            work_package_refs=["WP-IMP-0045"],
            graph_node_ids=["IKROS-HYP-20260802-0001"],
            tags=["semantic", "hypothesis"],
            payload={"kind": "semantic"},
            confidence=0.78,
            lifecycle_state=MemoryLifecycleState.ACTIVE,
            created_at="2026-08-02T00:00:00+00:00",
            updated_at="2026-08-02T00:00:00+00:00",
        )
    )
    manager.store(
        MemoryRecord(
            memory_id="IKMEM-T5-20260802-0001",
            tier=MemoryTier.ARCHIVE,
            entity_type="Hypothesis",
            title="Archived hypothesis memory",
            summary="Retired institutional memory",
            source_ids=["IKROS-HYP-20260802-0001"],
            evidence_refs=["05-work-packages/WP-IMP-0045/evidence/EXEC-047.yaml"],
            spec_refs=["SPEC-060"],
            capability_refs=["IKROS-QUERY"],
            work_package_refs=["WP-IMP-0045"],
            graph_node_ids=["IKROS-HYP-20260802-0001"],
            tags=["archive"],
            payload={"kind": "archive"},
            confidence=0.61,
            lifecycle_state=MemoryLifecycleState.ARCHIVED,
            created_at="2026-08-02T00:00:00+00:00",
            updated_at="2026-08-02T00:00:00+00:00",
            archived_at="2026-08-02T01:00:00+00:00",
        )
    )
    return manager


def _registries() -> dict[str, BaseRegistry[IKROSEntity]]:
    research = ResearchRegistry()
    hypotheses = HypothesisRegistry()
    experiments = ExperimentRegistry()
    features = FeatureRegistry()
    alphas = AlphaRegistry()

    research.register(_rq())
    hypotheses.register(_hyp())
    experiments.register(_exp())
    features.register_family(_feature_family())
    features.register(_feature())
    alphas.register(_candidate())
    alpha = _alpha()
    alphas.promote("IKROS-ALPHACAND-20260802-0001", alpha)

    registries: dict[str, BaseRegistry[IKROSEntity]] = {
        "ResearchQuestion": cast(BaseRegistry[IKROSEntity], research),
        "Hypothesis": cast(BaseRegistry[IKROSEntity], hypotheses),
        "Experiment": cast(BaseRegistry[IKROSEntity], experiments),
        "Feature": cast(BaseRegistry[IKROSEntity], features),
        "AlphaCandidate": cast(BaseRegistry[IKROSEntity], alphas),
    }
    return registries


def _engine(audit_dir: Path) -> QueryEngine:
    return QueryEngine(
        registries=_registries(),
        graph=_graph(),
        memory=_memory_manager(),
        audit_log=QueryAuditLog(audit_dir),
    )


class TestQueryParser:
    def test_parse_entity_query(self) -> None:
        parsed = QueryParser().parse("GET ENTITY IKROS-HYP-20260802-0001")
        assert parsed.source == "ENTITY"
        assert parsed.target == "IKROS-HYP-20260802-0001"

    def test_parse_registry_query(self) -> None:
        parsed = QueryParser().parse(
            "GET REGISTRY Hypothesis WHERE lifecycle_state=SUPPORTED AND capability=IKROS-QUERY"
        )
        assert parsed.source == "REGISTRY"
        assert parsed.target == "Hypothesis"
        assert parsed.filters["lifecycle_state"] == "SUPPORTED"

    def test_parse_memory_query(self) -> None:
        parsed = QueryParser().parse(
            "GET MEMORY T2_SEMANTIC WHERE hypothesis=IKROS-HYP-20260802-0001"
        )
        assert parsed.source == "MEMORY"
        assert parsed.target == "T2_SEMANTIC"

    def test_parse_graph_shortest_path(self) -> None:
        parsed = QueryParser().parse(
            "GET GRAPH SHORTEST_PATH FROM IKROS-RQ-20260802-0001 TO IKROS-ALPHA-20260802-0001"
        )
        assert parsed.graph_operation == GraphOperation.SHORTEST_PATH
        assert parsed.source_id == "IKROS-RQ-20260802-0001"
        assert parsed.target_id == "IKROS-ALPHA-20260802-0001"

    def test_parse_graph_dependency_chain(self) -> None:
        parsed = QueryParser().parse(
            "GET GRAPH DEPENDENCY_CHAIN OF IKROS-RQ-20260802-0001 DIRECTION out MAX_DEPTH 3"
        )
        assert parsed.graph_operation == GraphOperation.DEPENDENCY_CHAIN
        assert parsed.direction == "out"
        assert parsed.max_depth == 3

    def test_parse_invalid_query_raises(self) -> None:
        with pytest.raises(QueryParseError):
            QueryParser().parse("BAD QUERY")


class TestQueryEngine:
    def test_entity_query_registry_hit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET ENTITY IKROS-HYP-20260802-0001"
            )
            assert {item.source for item in response.results} == {"registry", "graph"}
            assert all(
                item.identifier == "IKROS-HYP-20260802-0001" for item in response.results
            )
            assert any(item.source == "registry" and item.lineage for item in response.results)

    def test_entity_query_archived_memory_requires_include_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = _engine(Path(temp_dir))
            with pytest.raises(QueryValidationError):
                engine.execute("GET ENTITY IKMEM-T5-20260802-0001")

    def test_entity_query_archived_memory_allowed_with_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET ENTITY IKMEM-T5-20260802-0001 INCLUDE_ARCHIVE"
            )
            assert response.results[0].identifier == "IKMEM-T5-20260802-0001"
            assert response.results[0].source == "memory"

    def test_registry_query_by_lifecycle_and_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET REGISTRY Hypothesis WHERE lifecycle_state=SUPPORTED AND capability=IKROS-QUERY"
            )
            assert [item.identifier for item in response.results] == [
                "IKROS-HYP-20260802-0001"
            ]

    def test_registry_query_by_requirement_keyword(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET REGISTRY Hypothesis WHERE requirement=WP-IMP-0045"
            )
            assert len(response.results) == 1

    def test_memory_query_semantic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET MEMORY T2_SEMANTIC WHERE hypothesis=IKROS-HYP-20260802-0001"
            )
            assert [item.identifier for item in response.results] == [
                "IKMEM-T2-20260802-0001"
            ]

    def test_memory_archive_requires_include_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = _engine(Path(temp_dir))
            with pytest.raises(QueryValidationError):
                engine.execute("GET MEMORY T5_ARCHIVE WHERE entity_type=Hypothesis")

    def test_memory_archive_with_include_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET MEMORY T5_ARCHIVE WHERE entity_type=Hypothesis INCLUDE_ARCHIVE"
            )
            assert [item.identifier for item in response.results] == [
                "IKMEM-T5-20260802-0001"
            ]

    def test_memory_query_by_confidence_range(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET MEMORY ALL WHERE min_confidence=0.70 AND max_confidence=0.90"
            )
            assert [item.identifier for item in response.results] == [
                "IKMEM-T2-20260802-0001"
            ]

    def test_graph_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET GRAPH DESCENDANTS OF IKROS-RQ-20260802-0001 MAX_DEPTH 4"
            )
            ids = [item.identifier for item in response.results]
            assert "IKROS-HYP-20260802-0001" in ids
            assert "IKROS-ALPHA-20260802-0001" in ids

    def test_graph_ancestors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET GRAPH ANCESTORS OF IKROS-ALPHACAND-20260802-0001 MAX_DEPTH 3"
            )
            ids = [item.identifier for item in response.results]
            assert "IKROS-EXP-20260802-0001" in ids
            assert "IKROS-RQ-20260802-0001" in ids

    def test_graph_supporting_experiments(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET GRAPH SUPPORTING_EXPERIMENTS FOR IKROS-HYP-20260802-0001"
            )
            assert [item.identifier for item in response.results] == [
                "IKROS-EXP-20260802-0001"
            ]

    def test_graph_contradictions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET GRAPH CONTRADICTIONS FOR IKROS-ALPHA-20260802-0001"
            )
            assert [item.identifier for item in response.results] == [
                "IKROS-EVID-20260802-0001"
            ]

    def test_graph_features_from_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET GRAPH FEATURES_FROM_DATASET IKROS-DSV-20260802-0001"
            )
            assert [item.identifier for item in response.results] == [
                "IKROS-FEAT-20260802-0001"
            ]

    def test_graph_shortest_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET GRAPH SHORTEST_PATH FROM IKROS-RQ-20260802-0001 TO IKROS-ALPHA-20260802-0001"
            )
            assert {item.identifier for item in response.results} == {
                "IKROS-RQ-20260802-0001",
                "IKROS-HYP-20260802-0001",
                "IKROS-EXP-20260802-0001",
                "IKROS-ALPHACAND-20260802-0001",
                "IKROS-ALPHA-20260802-0001",
            }
            assert sorted(item.lineage["path_index"] for item in response.results) == [
                0,
                1,
                2,
                3,
                4,
            ]

    def test_graph_dependency_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET GRAPH DEPENDENCY_CHAIN OF IKROS-RQ-20260802-0001 DIRECTION out MAX_DEPTH 2"
            )
            assert [item.identifier for item in response.results] == [
                "IKROS-HYP-20260802-0001"
            ]

    def test_graph_contradiction_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET GRAPH CONTRADICTION_CHAIN OF IKROS-ALPHA-20260802-0001 MAX_DEPTH 2"
            )
            assert [item.identifier for item in response.results] == [
                "IKROS-EVID-20260802-0001"
            ]

    def test_invalid_entity_reference_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = _engine(Path(temp_dir))
            with pytest.raises(QueryValidationError):
                engine.execute("GET ENTITY IKROS-HYP-20260802-9999")

    def test_invalid_confidence_threshold_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = _engine(Path(temp_dir))
            with pytest.raises(QueryValidationError):
                engine.execute(
                    "GET REGISTRY Hypothesis WHERE confidence_threshold=1.5"
                )

    def test_results_rank_by_confidence_then_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            response = _engine(Path(temp_dir)).execute(
                "GET GRAPH DESCENDANTS OF IKROS-RQ-20260802-0001 MAX_DEPTH 4"
            )
            confidences = [item.confidence for item in response.results]
            assert confidences == sorted(confidences, reverse=True)
            assert [item.rank for item in response.results] == list(
                range(1, len(response.results) + 1)
            )

    def test_audit_log_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_dir = Path(temp_dir) / "audit"
            engine = _engine(audit_dir)
            response = engine.execute("GET ENTITY IKROS-HYP-20260802-0001")
            audit_entries = QueryAuditLog(audit_dir).list_entries()
            assert len(audit_entries) == 1
            assert audit_entries[0].audit_id == response.audit_id

    def test_query_results_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = _engine(Path(temp_dir))
            first = engine.execute(
                "GET REGISTRY Hypothesis WHERE lifecycle_state=SUPPORTED"
            )
            second = engine.execute(
                "GET REGISTRY Hypothesis WHERE lifecycle_state=SUPPORTED"
            )
            assert [item.to_dict() for item in first.results] == [
                item.to_dict() for item in second.results
            ]
