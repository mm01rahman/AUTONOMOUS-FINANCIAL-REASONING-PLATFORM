"""Unit tests for the IKROS Institutional Research Confidence & Evidence Engine."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import cast

import pytest

from tools.ikros.confidence import (
    ConfidenceEvidence,
    ConfidenceEvidenceType,
    ConfidenceValidationError,
    ContradictionSeverity,
    EvidenceReferences,
    EvidenceRelation,
    ResearchConfidenceEngine,
    validate_evidence,
)
from tools.ikros.graph import EdgeType, GraphEdge, GraphNode, KnowledgeGraph, NodeType
from tools.ikros.memory import MemoryQuery
from tools.ikros.models import (
    ConfidenceVector,
    Experiment,
    ExperimentStatus,
    Hypothesis,
    HypothesisStatus,
    IKROSEntity,
    LineageDependencies,
    LineageEvidence,
    LineageExperiments,
    LineageOrigin,
    LineageRecord,
)
from tools.ikros.registries.alpha import AlphaRegistry
from tools.ikros.registries.base import BaseRegistry
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.feature import FeatureRegistry
from tools.ikros.registries.hypothesis import HypothesisRegistry
from tools.ikros.registries.research import ResearchRegistry


def _origin() -> LineageOrigin:
    return LineageOrigin(
        created_by="confidence-test",
        created_at="2026-08-02T00:00:00Z",
        creation_context="wp47-test",
        motivation="confidence assessment fixture",
    )


def _confidence(level: float) -> ConfidenceVector:
    return ConfidenceVector(
        prior=max(level - 0.1, 0.0),
        statistical=level,
        economic=max(level - 0.05, 0.0),
        data=level,
        model=level,
        validation=max(level - 0.02, 0.0),
        replication=max(level - 0.15, 0.0),
        operational=max(level - 0.20, 0.0),
    )


def _hypothesis() -> Hypothesis:
    return Hypothesis(
        ikros_id="IKROS-HYP-20260802-0001",
        entity_type="Hypothesis",
        version="1.0.0",
        lifecycle_state=HypothesisStatus.SUPPORTED.value,
        confidence=_confidence(0.45),
        lineage=LineageRecord(
            origin=_origin(),
            dependencies=LineageDependencies(inputs=["IKROS-RQ-20260802-0001"]),
            experiments=LineageExperiments(
                tested_in=["IKROS-EXP-20260802-0001"],
                validated_by=["IKROS-VAL-20260802-0001"],
            ),
            evidence=LineageEvidence(ers_records=["EXEC-049"]),
        ),
        spec_refs=["SPEC-060"],
        capability_refs=["IKROS-CONFIDENCE"],
        work_package_refs=["WP-IMP-0047"],
        statement="Validated regime persistence supports continuation alpha.",
        null_hypothesis="H0: no continuation effect",
        alternative_hypothesis="H1: continuation exists after validated persistence",
        significance_level=0.05,
        power=0.80,
        prior_confidence=0.35,
        posterior_confidence=0.45,
        source_rq="IKROS-RQ-20260802-0001",
        experiments=["IKROS-EXP-20260802-0001"],
        validations=["IKROS-VAL-20260802-0001"],
    )


def _experiment() -> Experiment:
    return Experiment(
        ikros_id="IKROS-EXP-20260802-0001",
        entity_type="Experiment",
        version="1.0.0",
        lifecycle_state=ExperimentStatus.COMPLETE.value,
        confidence=_confidence(0.50),
        lineage=LineageRecord(
            origin=_origin(),
            dependencies=LineageDependencies(
                inputs=["IKROS-HYP-20260802-0001"],
                datasets=["IKROS-DSV-20260802-0001"],
                features=["IKROS-FEAT-20260802-0001"],
            ),
            evidence=LineageEvidence(ers_records=["EXEC-049"]),
        ),
        spec_refs=["SPEC-060"],
        capability_refs=["IKROS-CONFIDENCE"],
        work_package_refs=["WP-IMP-0047"],
        title="Walk-forward validation experiment",
        hypotheses=["IKROS-HYP-20260802-0001"],
        protocol="Walk-forward",
        dataset_versions=["IKROS-DSV-20260802-0001"],
        feature_versions=["IKROS-FEAT-20260802-0001"],
        parameters={"window": 63},
        random_seed=42,
        reproducibility_hash="abc123",
        validations_produced=["IKROS-VAL-20260802-0001"],
    )


def _graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()
    graph.add_node(
        GraphNode(
            node_id="IKROS-HYP-20260802-0001",
            node_type=NodeType.HYPOTHESIS,
            ikros_id="IKROS-HYP-20260802-0001",
            label="Hypothesis",
            confidence=0.45,
            attributes={"entity_type": "Hypothesis"},
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0047"],
        )
    )
    graph.add_node(
        GraphNode(
            node_id="IKROS-EXP-20260802-0001",
            node_type=NodeType.EXPERIMENT,
            ikros_id="IKROS-EXP-20260802-0001",
            label="Experiment",
            confidence=0.50,
            attributes={"entity_type": "Experiment"},
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0047"],
        )
    )
    graph.add_node(
        GraphNode(
            node_id="IKROS-ALPHACAND-20260802-0001",
            node_type=NodeType.ALPHA_CANDIDATE,
            ikros_id="IKROS-ALPHACAND-20260802-0001",
            label="Candidate",
            confidence=0.40,
            attributes={"entity_type": "AlphaCandidate"},
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0047"],
        )
    )
    graph.add_node(
        GraphNode(
            node_id="IKROS-ALPHA-20260802-0001",
            node_type=NodeType.ALPHA,
            ikros_id="IKROS-ALPHA-20260802-0001",
            label="Alpha",
            confidence=0.38,
            attributes={"entity_type": "Alpha"},
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0047"],
        )
    )
    graph.add_edge(
        GraphEdge(
            edge_id="IKROS-EDGE-20260802-1001",
            source_id="IKROS-HYP-20260802-0001",
            target_id="IKROS-EXP-20260802-0001",
            edge_type=EdgeType.TESTED_IN,
            confidence=1.0,
        )
    )
    graph.add_edge(
        GraphEdge(
            edge_id="IKROS-EDGE-20260802-1002",
            source_id="IKROS-EXP-20260802-0001",
            target_id="IKROS-ALPHACAND-20260802-0001",
            edge_type=EdgeType.GENERATED_ALPHA,
            confidence=0.9,
        )
    )
    graph.add_edge(
        GraphEdge(
            edge_id="IKROS-EDGE-20260802-1003",
            source_id="IKROS-ALPHACAND-20260802-0001",
            target_id="IKROS-ALPHA-20260802-0001",
            edge_type=EdgeType.PRODUCED,
            confidence=0.85,
        )
    )
    return graph


def _registries(base_dir: Path) -> dict[str, BaseRegistry[IKROSEntity]]:
    research = ResearchRegistry(base_dir)
    hypothesis = HypothesisRegistry(base_dir)
    experiment = ExperimentRegistry(base_dir)
    feature = FeatureRegistry(base_dir)
    alpha = AlphaRegistry(base_dir)
    hypothesis.register(_hypothesis())
    experiment.register(_experiment())
    return {
        "ResearchQuestion": cast(BaseRegistry[IKROSEntity], research),
        "Hypothesis": cast(BaseRegistry[IKROSEntity], hypothesis),
        "Experiment": cast(BaseRegistry[IKROSEntity], experiment),
        "Feature": cast(BaseRegistry[IKROSEntity], feature),
        "AlphaCandidate": cast(BaseRegistry[IKROSEntity], alpha),
    }


def _supporting_evidence() -> list[ConfidenceEvidence]:
    common_refs = EvidenceReferences(
        specification_ids=["SPEC-060"],
        work_package_ids=["WP-IMP-0047"],
        capability_ids=["IKROS-CONFIDENCE"],
        evidence_record_ids=["EXEC-049"],
        research_report_ids=["RPT-IKROS-001"],
    )
    return [
        ConfidenceEvidence(
            evidence_id="EVID-VAL-001",
            evidence_type=ConfidenceEvidenceType.VALIDATION,
            relation=EvidenceRelation.SUPPORTS,
            references=EvidenceReferences(
                specification_ids=common_refs.specification_ids,
                validation_ids=["IKROS-VAL-20260802-0001"],
                work_package_ids=common_refs.work_package_ids,
                capability_ids=common_refs.capability_ids,
                evidence_record_ids=common_refs.evidence_record_ids,
            ),
            confidence_weight=1.0,
            independent_source="desk-a",
            temporal_bucket="2026Q1",
            observed_at="2026-08-01T00:00:00Z",
            metrics={
                "p_value": 0.03,
                "consistency_score": 0.82,
                "sharpe_degradation": 0.10,
                "verdict": "PASS",
                "oos_confirmed": True,
                "regime_ids": ["REGIME-TREND", "REGIME-NEUTRAL"],
            },
        ),
        ConfidenceEvidence(
            evidence_id="EVID-EXP-001",
            evidence_type=ConfidenceEvidenceType.EXPERIMENT,
            relation=EvidenceRelation.SUPPORTS,
            references=EvidenceReferences(
                specification_ids=common_refs.specification_ids,
                experiment_ids=["IKROS-EXP-20260802-0001"],
                dataset_ids=["IKROS-DSV-20260802-0001"],
                feature_ids=["IKROS-FEAT-20260802-0001"],
                work_package_ids=common_refs.work_package_ids,
                capability_ids=common_refs.capability_ids,
                research_report_ids=common_refs.research_report_ids,
            ),
            confidence_weight=0.95,
            independent_source="desk-b",
            temporal_bucket="2026Q2",
            observed_at="2026-08-01T12:00:00Z",
            metrics={
                "reproducibility_score": 0.88,
                "design_score": 0.80,
                "regime_ids": ["REGIME-TREND"],
            },
        ),
        ConfidenceEvidence(
            evidence_id="EVID-DATA-001",
            evidence_type=ConfidenceEvidenceType.DATASET,
            relation=EvidenceRelation.SUPPORTS,
            references=EvidenceReferences(
                specification_ids=common_refs.specification_ids,
                dataset_ids=["IKROS-DSV-20260802-0001", "IKROS-DSV-20260802-0002"],
                work_package_ids=common_refs.work_package_ids,
                capability_ids=common_refs.capability_ids,
            ),
            confidence_weight=0.85,
            temporal_bucket="2026Q2",
            observed_at="2026-07-31T00:00:00Z",
            metrics={"data_quality_grade": "A"},
        ),
        ConfidenceEvidence(
            evidence_id="EVID-REPORT-001",
            evidence_type=ConfidenceEvidenceType.RESEARCH_REPORT,
            relation=EvidenceRelation.SUPPORTS,
            references=EvidenceReferences(
                specification_ids=common_refs.specification_ids,
                work_package_ids=common_refs.work_package_ids,
                capability_ids=common_refs.capability_ids,
                research_report_ids=common_refs.research_report_ids,
            ),
            confidence_weight=0.70,
            temporal_bucket="2026Q3",
            observed_at="2026-08-02T00:00:00Z",
            metrics={"economic_score": 0.74, "operational_confidence": 0.60},
        ),
    ]


def _engine(base_dir: Path) -> ResearchConfidenceEngine:
    return ResearchConfidenceEngine(
        registries=_registries(base_dir / "registries"),
        graph=_graph(),
        base_dir=base_dir,
    )


class TestResearchConfidenceEngine:
    def test_assessment_updates_registry_graph_memory_and_query_view(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = _engine(Path(temp_dir))
            assessment = engine.assess(
                "IKROS-HYP-20260802-0001",
                _supporting_evidence(),
                reason="Validated walk-forward and reproducibility evidence",
            )

            assert assessment.target_type == "Hypothesis"
            assert assessment.new_overall() > assessment.previous_overall()
            assert assessment.quality.replication_count == 2
            assert assessment.quality.dataset_diversity == 2
            assert assessment.propagation

            updated = cast(
                Hypothesis,
                engine._registries["Hypothesis"].get("IKROS-HYP-20260802-0001"),
            )
            assert updated.posterior_confidence == pytest.approx(assessment.new_overall())
            assert updated.confidence.model == pytest.approx(
                assessment.assessed_confidence.experimental
            )

            graph_node = engine._graph.get_node("IKROS-HYP-20260802-0001")
            assert graph_node.confidence == pytest.approx(assessment.new_overall())

            memory_records = engine._memory.retrieve(
                MemoryQuery(entity_type="ConfidenceAssessment")
            )
            assert len(memory_records) == 1

            query = engine.build_query_engine().execute(
                "GET MEMORY ALL WHERE entity_type=ConfidenceAssessment"
            )
            assert query.results[0].type == "ConfidenceAssessment"
            assert query.results[0].source == "memory"

            audits = engine._audit_log.list_entries()
            assert len(audits) == 1
            assert audits[0].entry_hash

    def test_contradictions_reduce_confidence_and_trigger_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = _engine(Path(temp_dir))
            support_only = engine.assess(
                "IKROS-HYP-20260802-0001",
                _supporting_evidence(),
                reason="Support-only baseline",
            )
            contradiction = ConfidenceEvidence(
                evidence_id="EVID-STRESS-001",
                evidence_type=ConfidenceEvidenceType.STRESS_TEST,
                relation=EvidenceRelation.CONTRADICTS,
                contradiction_severity=ContradictionSeverity.MAJOR,
                references=EvidenceReferences(
                    specification_ids=["SPEC-060"],
                    stress_test_ids=["IKROS-STRESS-20260802-0001"],
                    work_package_ids=["WP-IMP-0047"],
                    capability_ids=["IKROS-CONFIDENCE"],
                ),
                confidence_weight=0.80,
                independent_source="desk-c",
                observed_at="2026-08-02T00:00:00Z",
                metrics={"verdict": "FAIL"},
            )

            contradicted = engine.assess(
                "IKROS-HYP-20260802-0001",
                _supporting_evidence() + [contradiction],
                reason="Add contradictory stress evidence",
            )

            assert (
                contradicted.contradiction_resolution.recommended_action == "ARB_REVIEW"
            )
            assert contradicted.contradiction_resolution.requires_review is True
            assert contradicted.new_overall() < support_only.new_overall()

    def test_audit_hash_chain_and_history_are_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = _engine(Path(temp_dir))
            first = engine.assess(
                "IKROS-HYP-20260802-0001",
                _supporting_evidence(),
                reason="Initial assessment",
            )
            second_evidence = _supporting_evidence()
            second_evidence[0].metrics["p_value"] = 0.01
            second = engine.assess(
                "IKROS-HYP-20260802-0001",
                second_evidence,
                reason="Higher-confidence follow-up",
            )

            history = engine.history_for_target("IKROS-HYP-20260802-0001")
            audits = engine._audit_log.list_entries()

            assert len(history) == 2
            assert len(audits) == 2
            assert audits[1].previous_hash == audits[0].entry_hash
            assert history[1].previous_confidence.overall("Hypothesis") == pytest.approx(
                first.new_overall()
            )
            assert second.previous_overall() == pytest.approx(first.new_overall())


class TestConfidenceValidation:
    def test_validate_evidence_requires_structured_references(self) -> None:
        evidence = ConfidenceEvidence(
            evidence_id="EVID-001",
            evidence_type=ConfidenceEvidenceType.EXPERIMENT,
            relation=EvidenceRelation.SUPPORTS,
            references=EvidenceReferences(),
        )
        errors = validate_evidence(evidence)
        assert any("structured reference" in error for error in errors)

    def test_unknown_target_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = _engine(Path(temp_dir))
            with pytest.raises(ConfidenceValidationError):
                engine.assess(
                    "IKROS-HYP-20260802-9999",
                    _supporting_evidence(),
                    reason="Unknown target",
                )
