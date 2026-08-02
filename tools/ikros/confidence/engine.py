"""IKROS Institutional Research Confidence & Evidence Engine."""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from tools.ikros.confidence.models import (
    ConfidenceAssessment,
    ConfidenceAuditEntry,
    ConfidenceDimensions,
    ConfidenceEvidence,
    ConfidenceEvidenceType,
    ConfidenceHistoryEntry,
    ContradictionResolution,
    ContradictionSeverity,
    EvidenceReferences,
    EvidenceRelation,
    PropagationImpact,
    ResearchQualityIndicators,
)
from tools.ikros.confidence.persistence import (
    ConfidenceAuditLog,
    ConfidenceRepository,
    YAMLConfidenceRepository,
)
from tools.ikros.confidence.validation import (
    ConfidenceValidationError,
    assert_valid_assessment,
    assert_valid_audit,
    assert_valid_history,
)
from tools.ikros.graph import (
    LINEAGE_EDGES,
    GraphNode,
    KnowledgeGraph,
    KnowledgeGraphRepository,
    YAMLGraphRepository,
)
from tools.ikros.memory import MemoryRecord, MemoryTier, ResearchMemoryManager, YAMLMemoryRepository
from tools.ikros.models import IKROSEntity
from tools.ikros.query import QueryEngine
from tools.ikros.query.audit import QueryAuditLog
from tools.ikros.registries.alpha import AlphaRegistry
from tools.ikros.registries.base import BaseRegistry
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.feature import FeatureRegistry
from tools.ikros.registries.hypothesis import HypothesisRegistry
from tools.ikros.registries.research import ResearchRegistry

_EVIDENCE_TYPE_WEIGHTS: dict[str, float] = {
    ConfidenceEvidenceType.SPECIFICATION: 0.35,
    ConfidenceEvidenceType.EXPERIMENT: 0.80,
    ConfidenceEvidenceType.DATASET: 0.70,
    ConfidenceEvidenceType.FEATURE: 0.65,
    ConfidenceEvidenceType.VALIDATION: 0.95,
    ConfidenceEvidenceType.EVIDENCE_RECORD: 0.60,
    ConfidenceEvidenceType.WORK_PACKAGE: 0.50,
    ConfidenceEvidenceType.CAPABILITY: 0.45,
    ConfidenceEvidenceType.RESEARCH_REPORT: 0.55,
    ConfidenceEvidenceType.BACKTEST: 0.85,
    ConfidenceEvidenceType.WALK_FORWARD_STUDY: 0.95,
    ConfidenceEvidenceType.MONTE_CARLO_STUDY: 0.90,
    ConfidenceEvidenceType.STRESS_TEST: 0.85,
}

_DATA_GRADE_CONFIDENCE: dict[str, float] = {
    "A": 0.90,
    "B": 0.70,
    "C": 0.50,
    "UNVERIFIED": 0.20,
}

_CONTRADICTION_MULTIPLIERS: dict[str, float] = {
    ContradictionSeverity.MINOR: 0.95,
    ContradictionSeverity.MODERATE: 0.80,
    ContradictionSeverity.MAJOR: 0.60,
    ContradictionSeverity.INVALIDATING: 0.10,
}

_TEMPORAL_DECAY_LAMBDAS: dict[str, float] = {
    "AlphaCandidate": 0.001,
    "Alpha": 0.0005,
    "KnowledgeObject": 0.0001,
    "Failure": 0.0,
}

_REPLICATION_EVIDENCE_TYPES: set[str] = {
    ConfidenceEvidenceType.EXPERIMENT,
    ConfidenceEvidenceType.VALIDATION,
    ConfidenceEvidenceType.BACKTEST,
    ConfidenceEvidenceType.WALK_FORWARD_STUDY,
    ConfidenceEvidenceType.MONTE_CARLO_STUDY,
    ConfidenceEvidenceType.STRESS_TEST,
}

_OOS_EVIDENCE_TYPES: set[str] = {
    ConfidenceEvidenceType.VALIDATION,
    ConfidenceEvidenceType.BACKTEST,
    ConfidenceEvidenceType.WALK_FORWARD_STUDY,
    ConfidenceEvidenceType.MONTE_CARLO_STUDY,
    ConfidenceEvidenceType.STRESS_TEST,
}

_REGISTRY_TYPES: dict[str, str] = {
    "ResearchQuestion": "ResearchQuestion",
    "Hypothesis": "Hypothesis",
    "Experiment": "Experiment",
    "Feature": "Feature",
    "FeatureFamily": "Feature",
    "AlphaCandidate": "AlphaCandidate",
    "Alpha": "AlphaCandidate",
}

_DIMENSION_KEYS: tuple[str, ...] = (
    "prior",
    "statistical",
    "economic",
    "data",
    "experimental",
    "validation",
    "replication",
    "operational",
)


class ResearchConfidenceEngine:
    """Deterministic confidence assessment, propagation, and audit engine."""

    def __init__(
        self,
        registries: dict[str, BaseRegistry[IKROSEntity]] | None = None,
        graph: KnowledgeGraph | None = None,
        graph_repository: KnowledgeGraphRepository | None = None,
        memory: ResearchMemoryManager | None = None,
        confidence_repository: ConfidenceRepository | None = None,
        audit_log: ConfidenceAuditLog | None = None,
        base_dir: Path | None = None,
    ) -> None:
        resolved_base = base_dir or Path("data") / "ikros"
        self._base_dir = resolved_base
        self._registries = registries or self._default_registries(resolved_base / "registries")
        self._graph_repository = graph_repository or YAMLGraphRepository(resolved_base / "graph")
        self._graph = graph or self._graph_repository.load()
        memory_repository = YAMLMemoryRepository(resolved_base / "memory")
        self._memory = memory or ResearchMemoryManager(memory_repository, self._graph)
        self._confidence_repository = confidence_repository or YAMLConfidenceRepository(
            resolved_base / "confidence"
        )
        self._audit_log = audit_log or ConfidenceAuditLog(resolved_base / "confidence" / "audit")

    def assess(
        self,
        target_id: str,
        evidence: list[ConfidenceEvidence],
        *,
        reason: str,
        operator: str = "ikros-confidence-engine",
    ) -> ConfidenceAssessment:
        target, target_type = self._resolve_target(target_id)
        previous_confidence = self._baseline_confidence(target_id, target)
        references = self._merge_references(evidence)
        quality = self._quality_indicators(evidence)
        contradiction = self._contradiction_resolution(evidence)
        assessed_confidence = self._assessed_confidence(
            target_type=target_type,
            previous=previous_confidence,
            evidence=evidence,
            quality=quality,
            contradiction=contradiction,
        )
        assessment = ConfidenceAssessment(
            assessment_id=self._confidence_repository.next_assessment_id(),
            target_id=target_id,
            target_type=target_type,
            reason=reason,
            operator=operator,
            references=references,
            evidence=sorted(evidence, key=lambda item: item.evidence_id),
            previous_confidence=previous_confidence,
            assessed_confidence=assessed_confidence,
            quality=quality,
            contradiction_resolution=contradiction,
        )
        assessment.propagation = self._propagate_confidence(
            target_id=target_id,
            source_confidence=assessed_confidence,
        )
        assert_valid_assessment(assessment, known_identifiers=self._existing_identifiers())
        self._persist_target_confidence(target_id, target_type, assessed_confidence, assessment)
        history_entry = self._history_entry(assessment)
        assert_valid_history(history_entry)
        self._confidence_repository.save_assessment(assessment)
        self._confidence_repository.save_history_entry(history_entry)
        audit_entry = ConfidenceAuditEntry.build(
            audit_id=self._audit_log.next_audit_id(),
            assessment=assessment,
            previous_hash=self._audit_log.previous_hash(),
        )
        assert_valid_audit(audit_entry)
        self._audit_log.write(audit_entry)
        assessment.audit_id = audit_entry.audit_id
        assessment.memory_record_id = self._store_assessment_memory(assessment)
        self._confidence_repository.save_assessment(assessment)
        self._graph_repository.save(self._graph)
        return assessment

    def latest_assessment(self, target_id: str) -> ConfidenceAssessment | None:
        return self._confidence_repository.latest_assessment(target_id)

    def history_for_target(self, target_id: str) -> list[ConfidenceHistoryEntry]:
        return self._confidence_repository.history_for_target(target_id)

    def build_query_engine(self) -> QueryEngine:
        return QueryEngine(
            registries=self._registries,
            graph=self._graph,
            memory=self._memory,
            audit_log=QueryAuditLog(self._base_dir / "confidence" / "query-audit"),
        )

    def _resolve_target(self, target_id: str) -> tuple[object, str]:
        entity = self._find_entity(target_id)
        if entity is not None:
            return entity, entity.entity_type
        if self._graph.has_node(target_id):
            node = self._graph.get_node(target_id)
            return node, self._node_target_type(node)
        raise ConfidenceValidationError(
            f"target '{target_id}' was not found in registries or graph"
        )

    def _baseline_confidence(self, target_id: str, target: object) -> ConfidenceDimensions:
        latest = self._confidence_repository.latest_assessment(target_id)
        if latest is not None:
            return latest.assessed_confidence
        if isinstance(target, IKROSEntity):
            return ConfidenceDimensions.from_legacy(target.confidence)
        if isinstance(target, GraphNode):
            payload = target.attributes.get("confidence_assessment", {})
            if isinstance(payload, dict) and payload.get("assessed_confidence"):
                return ConfidenceDimensions.from_dict(
                    cast(dict[str, Any], payload["assessed_confidence"])
                )
            return ConfidenceDimensions(
                prior=float(target.confidence),
                statistical=float(target.confidence),
                economic=float(target.confidence),
                data=float(target.confidence),
                experimental=float(target.confidence),
                validation=float(target.confidence),
                replication=float(target.confidence),
                operational=float(target.confidence),
            )
        raise ConfidenceValidationError(f"unsupported target type '{type(target).__name__}'")

    def _merge_references(self, evidence: list[ConfidenceEvidence]) -> EvidenceReferences:
        merged = EvidenceReferences(specification_ids=["SPEC-060"])
        for item in evidence:
            merged = merged.merge(item.references)
        return merged

    def _quality_indicators(self, evidence: list[ConfidenceEvidence]) -> ResearchQualityIndicators:
        supporting = [item for item in evidence if item.relation == EvidenceRelation.SUPPORTS]
        contradictions = [
            item for item in evidence if item.relation == EvidenceRelation.CONTRADICTS
        ]
        independent_sources = {
            item.independent_source or item.evidence_id
            for item in supporting
            if item.evidence_type in _REPLICATION_EVIDENCE_TYPES
        }
        validation_support = [
            item for item in supporting if item.evidence_type in _OOS_EVIDENCE_TYPES
        ]
        oos_confirmations = [
            item
            for item in validation_support
            if bool(item.metrics.get("oos_confirmed", item.metrics.get("verdict") == "PASS"))
        ]
        regime_diversity = {
            regime_id
            for item in supporting
            for regime_id in item.metrics.get("regime_ids", [])
            if isinstance(regime_id, str)
        }
        dataset_diversity = {
            dataset_id for item in supporting for dataset_id in item.references.dataset_ids
        }
        temporal_diversity = {item.temporal_bucket for item in supporting if item.temporal_bucket}
        freshness_values = [self._freshness_multiplier(item) for item in supporting]
        evidence_types = {item.evidence_type for item in supporting}
        maturity_components = 0
        for expected in (
            ConfidenceEvidenceType.SPECIFICATION,
            ConfidenceEvidenceType.RESEARCH_REPORT,
            ConfidenceEvidenceType.EXPERIMENT,
            ConfidenceEvidenceType.VALIDATION,
            ConfidenceEvidenceType.EVIDENCE_RECORD,
            ConfidenceEvidenceType.BACKTEST,
        ):
            if expected in evidence_types:
                maturity_components += 1
        replication_score = self._replication_confidence(len(independent_sources))
        contradiction_score = max(0.0, 1.0 - (len(contradictions) * 0.2))
        freshness = sum(freshness_values) / len(freshness_values) if freshness_values else 0.0
        validation_completeness = 0.0
        if validation_support:
            passed = sum(
                1 for item in validation_support if item.metrics.get("verdict", "PASS") == "PASS"
            )
            validation_completeness = passed / len(validation_support)
        indicators = ResearchQualityIndicators(
            independent_validations=len(independent_sources),
            independent_validations_score=min(len(independent_sources) / 3.0, 1.0),
            out_of_sample_confirmations=len(oos_confirmations),
            out_of_sample_score=min(len(oos_confirmations) / 3.0, 1.0),
            regime_diversity=len(regime_diversity),
            regime_diversity_score=min(len(regime_diversity) / 4.0, 1.0),
            dataset_diversity=len(dataset_diversity),
            dataset_diversity_score=min(len(dataset_diversity) / 4.0, 1.0),
            temporal_diversity=len(temporal_diversity),
            temporal_diversity_score=min(len(temporal_diversity) / 4.0, 1.0),
            replication_count=len(independent_sources),
            replication_score=replication_score,
            contradiction_count=len(contradictions),
            contradiction_score=contradiction_score,
            evidence_freshness=freshness,
            research_maturity=maturity_components / 6.0,
            validation_completeness=validation_completeness,
        )
        quality_scores = [
            indicators.independent_validations_score,
            indicators.out_of_sample_score,
            indicators.regime_diversity_score,
            indicators.dataset_diversity_score,
            indicators.temporal_diversity_score,
            indicators.replication_score,
            indicators.contradiction_score,
            indicators.evidence_freshness,
            indicators.research_maturity,
            indicators.validation_completeness,
        ]
        indicators.overall_quality = sum(quality_scores) / len(quality_scores)
        return indicators

    def _contradiction_resolution(
        self,
        evidence: list[ConfidenceEvidence],
    ) -> ContradictionResolution:
        severities: dict[str, int] = {}
        multiplier = 1.0
        for item in evidence:
            if item.relation != EvidenceRelation.CONTRADICTS:
                continue
            severity = str(item.contradiction_severity or ContradictionSeverity.MINOR.value)
            severities[severity] = severities.get(severity, 0) + 1
            multiplier *= _CONTRADICTION_MULTIPLIERS.get(severity, 0.95)
        requires_review = (
            severities.get(ContradictionSeverity.MAJOR.value, 0) > 0
            or severities.get(ContradictionSeverity.INVALIDATING.value, 0) > 0
        )
        action = "NONE"
        if severities.get(ContradictionSeverity.INVALIDATING.value, 0):
            action = "ARB_EMERGENCY_REVIEW"
        elif severities.get(ContradictionSeverity.MAJOR.value, 0):
            action = "ARB_REVIEW"
        elif severities.get(ContradictionSeverity.MODERATE.value, 0):
            action = "PEER_REVIEW"
        elif severities:
            action = "LOG_ONLY"
        return ContradictionResolution(
            severity_counts=dict(sorted(severities.items())),
            contradiction_multiplier=multiplier,
            requires_review=requires_review,
            recommended_action=action,
        )

    def _assessed_confidence(
        self,
        *,
        target_type: str,
        previous: ConfidenceDimensions,
        evidence: list[ConfidenceEvidence],
        quality: ResearchQualityIndicators,
        contradiction: ContradictionResolution,
    ) -> ConfidenceDimensions:
        supporting = [item for item in evidence if item.relation == EvidenceRelation.SUPPORTS]
        dimensions = ConfidenceDimensions(
            prior=previous.prior,
            statistical=self._aggregate_dimension("statistical", previous.statistical, supporting),
            economic=self._aggregate_dimension("economic", previous.economic, supporting),
            data=self._aggregate_dimension("data", previous.data, supporting),
            experimental=self._aggregate_dimension(
                "experimental", previous.experimental, supporting
            ),
            validation=self._aggregate_dimension("validation", previous.validation, supporting),
            replication=self._replication_confidence(quality.replication_count),
            operational=self._aggregate_dimension("operational", previous.operational, supporting),
            last_updated=datetime.now(UTC).isoformat(),
        )
        temporal_multiplier = self._temporal_decay_multiplier(target_type, supporting)
        dimensions = dimensions.with_multiplier(temporal_multiplier)
        dimensions = ConfidenceDimensions(
            prior=dimensions.prior,
            statistical=dimensions.statistical,
            economic=min(dimensions.economic, max(quality.overall_quality, dimensions.economic)),
            data=dimensions.data,
            experimental=dimensions.experimental,
            validation=dimensions.validation,
            replication=dimensions.replication,
            operational=dimensions.operational,
            last_updated=dimensions.last_updated,
        ).with_multiplier(contradiction.contradiction_multiplier)
        return dimensions

    def _aggregate_dimension(
        self,
        dimension: str,
        previous_value: float,
        evidence: list[ConfidenceEvidence],
    ) -> float:
        observations: list[tuple[float, float]] = []
        for item in evidence:
            value = self._dimension_value(dimension, item)
            if value is None:
                continue
            weight = self._evidence_weight(item)
            observations.append((value, weight))
        if not observations:
            return previous_value
        numerator = sum(value * weight for value, weight in observations)
        denominator = sum(weight for _, weight in observations)
        if denominator == 0.0:
            return previous_value
        return _clamp(numerator / denominator)

    def _dimension_value(self, dimension: str, evidence: ConfidenceEvidence) -> float | None:
        metrics = evidence.metrics
        direct_key = f"{dimension}_confidence"
        if direct_key in metrics:
            return _clamp(float(metrics[direct_key]))
        if dimension == "statistical":
            if "p_value" in metrics:
                return _clamp(1.0 - float(metrics["p_value"]))
            if "effect_size" in metrics:
                return _clamp(abs(float(metrics["effect_size"])))
        if dimension == "economic":
            if "economic_score" in metrics:
                return _clamp(float(metrics["economic_score"]))
            if "mechanism_score" in metrics:
                return _clamp(float(metrics["mechanism_score"]))
        if dimension == "data":
            if "data_quality_grade" in metrics:
                grade = str(metrics["data_quality_grade"]).upper()
                return _DATA_GRADE_CONFIDENCE.get(grade, 0.20)
            if "coverage_score" in metrics:
                return _clamp(float(metrics["coverage_score"]))
        if dimension == "experimental":
            if "reproducibility_score" in metrics:
                return _clamp(float(metrics["reproducibility_score"]))
            if "design_score" in metrics:
                return _clamp(float(metrics["design_score"]))
            if metrics.get("reproducibility_hash"):
                return 0.85
        if dimension == "validation":
            if "consistency_score" in metrics:
                sharpe_degradation = float(metrics.get("sharpe_degradation", 0.0))
                score = float(metrics["consistency_score"]) * (1.0 - (sharpe_degradation / 2.0))
                return _clamp(score)
            if "verdict" in metrics:
                return 0.90 if str(metrics["verdict"]) == "PASS" else 0.30
        if dimension == "operational":
            if "paper_trading_score" in metrics:
                return _clamp(float(metrics["paper_trading_score"]))
            if "stress_pass_rate" in metrics:
                return _clamp(float(metrics["stress_pass_rate"]))
        return None

    def _evidence_weight(self, evidence: ConfidenceEvidence) -> float:
        base = _EVIDENCE_TYPE_WEIGHTS.get(evidence.evidence_type, 0.50)
        return base * evidence.confidence_weight * self._freshness_multiplier(evidence)

    def _freshness_multiplier(self, evidence: ConfidenceEvidence) -> float:
        observed = self._parse_iso(evidence.observed_at)
        days_old = max((datetime.now(UTC) - observed).days, 0)
        return max(0.50, math.exp(-days_old / 3650.0))

    def _replication_confidence(self, replication_count: int) -> float:
        if replication_count <= 0:
            return 0.0
        return _clamp(1.0 - math.exp(-(replication_count / 3.0)))

    def _temporal_decay_multiplier(
        self,
        target_type: str,
        evidence: list[ConfidenceEvidence],
    ) -> float:
        if not evidence:
            return 1.0
        latest = max(self._parse_iso(item.observed_at) for item in evidence)
        days_since_validation = max((datetime.now(UTC) - latest).days, 0)
        decay_lambda = _TEMPORAL_DECAY_LAMBDAS.get(target_type, 0.0005)
        return math.exp(-(decay_lambda * days_since_validation))

    def _propagate_confidence(
        self,
        *,
        target_id: str,
        source_confidence: ConfidenceDimensions,
    ) -> list[PropagationImpact]:
        if not self._graph.has_node(target_id):
            return []
        impacts: list[PropagationImpact] = []
        visited: set[str] = {target_id}
        queue: deque[tuple[str, float, int]] = deque([(target_id, 1.0, 0)])
        while queue:
            current_id, factor, depth = queue.popleft()
            for edge in self._graph.get_out_edges(current_id):
                if edge.edge_type not in LINEAGE_EDGES:
                    continue
                neighbor = edge.target_id
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                propagated_factor = factor * 0.85 * edge.confidence
                target, target_type = self._resolve_target(neighbor)
                previous = self._baseline_confidence(neighbor, target)
                updated = ConfidenceDimensions(
                    prior=previous.prior,
                    statistical=_blend(
                        previous.statistical, source_confidence.statistical, propagated_factor
                    ),
                    economic=_blend(
                        previous.economic, source_confidence.economic, propagated_factor
                    ),
                    data=_blend(previous.data, source_confidence.data, propagated_factor),
                    experimental=_blend(
                        previous.experimental,
                        source_confidence.experimental,
                        propagated_factor,
                    ),
                    validation=_blend(
                        previous.validation, source_confidence.validation, propagated_factor
                    ),
                    replication=_blend(
                        previous.replication,
                        source_confidence.replication,
                        propagated_factor,
                    ),
                    operational=_blend(
                        previous.operational,
                        source_confidence.operational,
                        propagated_factor,
                    ),
                    last_updated=datetime.now(UTC).isoformat(),
                )
                self._persist_target_confidence(neighbor, target_type, updated, None)
                impacts.append(
                    PropagationImpact(
                        target_id=neighbor,
                        target_type=target_type,
                        depth=depth + 1,
                        previous_overall=previous.overall(target_type),
                        new_overall=updated.overall(target_type),
                        confidence=updated,
                    )
                )
                queue.append((neighbor, propagated_factor, depth + 1))
        return impacts

    def _persist_target_confidence(
        self,
        target_id: str,
        target_type: str,
        confidence: ConfidenceDimensions,
        assessment: ConfidenceAssessment | None,
    ) -> None:
        entity = self._find_entity(target_id)
        if entity is not None:
            delta: dict[str, Any] = {"confidence": confidence.to_legacy().to_dict()}
            if target_type == "Hypothesis":
                delta["posterior_confidence"] = confidence.overall(target_type)
                delta["prior_confidence"] = confidence.prior
            self._registry_for_type(target_type).update(target_id, delta)
        if self._graph.has_node(target_id):
            node = self._graph.get_node(target_id)
            attributes = dict(node.attributes)
            assessment_summary: dict[str, Any] = {
                "assessed_confidence": confidence.to_dict(target_type),
                "updated_at": confidence.last_updated,
            }
            if assessment is not None:
                assessment_summary.update(
                    {
                        "assessment_id": assessment.assessment_id,
                        "quality": assessment.quality.to_dict(),
                        "contradiction_resolution": assessment.contradiction_resolution.to_dict(),
                    }
                )
            attributes["confidence_assessment"] = assessment_summary
            self._graph.update_node(
                target_id,
                {
                    "confidence": confidence.overall(target_type),
                    "attributes": attributes,
                },
            )

    def _history_entry(self, assessment: ConfidenceAssessment) -> ConfidenceHistoryEntry:
        return ConfidenceHistoryEntry(
            history_id=self._confidence_repository.next_history_id(),
            assessment_id=assessment.assessment_id,
            target_id=assessment.target_id,
            target_type=assessment.target_type,
            timestamp=assessment.assessed_at,
            reason=assessment.reason,
            supporting_evidence=[item.evidence_id for item in assessment.evidence],
            previous_confidence=assessment.previous_confidence,
            new_confidence=assessment.assessed_confidence,
            operator=assessment.operator,
            specification_refs=list(assessment.references.specification_ids),
            work_package_refs=list(assessment.references.work_package_ids),
            capability_refs=list(assessment.references.capability_ids),
        )

    def _store_assessment_memory(self, assessment: ConfidenceAssessment) -> str:
        memory_id = self._memory.next_id(MemoryTier.EPISODIC)
        record = MemoryRecord(
            memory_id=memory_id,
            tier=MemoryTier.EPISODIC,
            entity_type="ConfidenceAssessment",
            title=f"Confidence assessment for {assessment.target_id}",
            summary=assessment.reason,
            source_ids=[assessment.target_id],
            evidence_refs=[item.evidence_id for item in assessment.evidence],
            spec_refs=list(assessment.references.specification_ids),
            capability_refs=_sorted_unique(
                list(assessment.references.capability_ids) + ["IKROS-CONFIDENCE"]
            ),
            work_package_refs=_sorted_unique(
                list(assessment.references.work_package_ids) + ["WP-IMP-0047"]
            ),
            graph_node_ids=[assessment.target_id]
            if self._graph.has_node(assessment.target_id)
            else [],
            tags=["confidence", assessment.target_type.lower()],
            payload=assessment.to_dict(),
            confidence=assessment.new_overall(),
        )
        self._memory.store(record)
        return memory_id

    def _find_entity(self, identifier: str) -> IKROSEntity | None:
        for registry in self._registries.values():
            if registry.exists(identifier):
                return registry.get(identifier)
            if isinstance(registry, FeatureRegistry):
                try:
                    return registry.get_family(identifier)
                except KeyError:
                    pass
            if isinstance(registry, AlphaRegistry):
                try:
                    return registry.get_alpha(identifier)
                except KeyError:
                    pass
        return None

    def _node_target_type(self, node: GraphNode) -> str:
        attributes = node.attributes
        entity_type = attributes.get("entity_type")
        if isinstance(entity_type, str) and entity_type:
            return entity_type
        return str(node.node_type)

    def _existing_identifiers(self) -> set[str]:
        identifiers = set(self._graph.node_ids())
        for registry in self._registries.values():
            identifiers.update(entity.ikros_id for entity in registry.list_all())
            if isinstance(registry, FeatureRegistry):
                identifiers.update(entity.ikros_id for entity in registry.list_families())
            if isinstance(registry, AlphaRegistry):
                identifiers.update(entity.ikros_id for entity in registry.list_alphas())
        return identifiers

    def _registry_for_type(self, entity_type: str) -> BaseRegistry[IKROSEntity]:
        registry_key = _REGISTRY_TYPES.get(entity_type)
        if registry_key is None:
            raise ConfidenceValidationError(f"no registry configured for '{entity_type}'")
        return self._registries[registry_key]

    def _default_registries(
        self,
        base_dir: Path,
    ) -> dict[str, BaseRegistry[IKROSEntity]]:
        return {
            "ResearchQuestion": cast(BaseRegistry[IKROSEntity], ResearchRegistry(base_dir)),
            "Hypothesis": cast(BaseRegistry[IKROSEntity], HypothesisRegistry(base_dir)),
            "Experiment": cast(BaseRegistry[IKROSEntity], ExperimentRegistry(base_dir)),
            "Feature": cast(BaseRegistry[IKROSEntity], FeatureRegistry(base_dir)),
            "AlphaCandidate": cast(BaseRegistry[IKROSEntity], AlphaRegistry(base_dir)),
        }

    def _parse_iso(self, value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)


def _blend(current: float, propagated: float, factor: float) -> float:
    return _clamp((current + (propagated * factor)) / 2.0)


def _clamp(value: float) -> float:
    return float(max(0.0, min(value, 0.95)))


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted({str(value) for value in values if value})
