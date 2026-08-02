"""IKROS confidence models — deterministic assessments, history, and audit records."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from tools.ikros.models import ConfidenceVector


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _clamp(value: float, minimum: float = 0.0, maximum: float = 0.95) -> float:
    return float(max(minimum, min(value, maximum)))


class ConfidenceEvidenceType(StrEnum):
    SPECIFICATION = "SPECIFICATION"
    EXPERIMENT = "EXPERIMENT"
    DATASET = "DATASET"
    FEATURE = "FEATURE"
    VALIDATION = "VALIDATION"
    EVIDENCE_RECORD = "EVIDENCE_RECORD"
    WORK_PACKAGE = "WORK_PACKAGE"
    CAPABILITY = "CAPABILITY"
    RESEARCH_REPORT = "RESEARCH_REPORT"
    BACKTEST = "BACKTEST"
    WALK_FORWARD_STUDY = "WALK_FORWARD_STUDY"
    MONTE_CARLO_STUDY = "MONTE_CARLO_STUDY"
    STRESS_TEST = "STRESS_TEST"


class EvidenceRelation(StrEnum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    NEUTRAL = "NEUTRAL"


class ContradictionSeverity(StrEnum):
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    INVALIDATING = "INVALIDATING"


@dataclass
class EvidenceReferences:
    specification_ids: list[str] = field(default_factory=list)
    experiment_ids: list[str] = field(default_factory=list)
    dataset_ids: list[str] = field(default_factory=list)
    feature_ids: list[str] = field(default_factory=list)
    validation_ids: list[str] = field(default_factory=list)
    evidence_record_ids: list[str] = field(default_factory=list)
    work_package_ids: list[str] = field(default_factory=list)
    capability_ids: list[str] = field(default_factory=list)
    research_report_ids: list[str] = field(default_factory=list)
    backtest_ids: list[str] = field(default_factory=list)
    walk_forward_ids: list[str] = field(default_factory=list)
    monte_carlo_ids: list[str] = field(default_factory=list)
    stress_test_ids: list[str] = field(default_factory=list)

    def merge(self, other: EvidenceReferences) -> EvidenceReferences:
        return EvidenceReferences(
            specification_ids=_sorted_unique(self.specification_ids + other.specification_ids),
            experiment_ids=_sorted_unique(self.experiment_ids + other.experiment_ids),
            dataset_ids=_sorted_unique(self.dataset_ids + other.dataset_ids),
            feature_ids=_sorted_unique(self.feature_ids + other.feature_ids),
            validation_ids=_sorted_unique(self.validation_ids + other.validation_ids),
            evidence_record_ids=_sorted_unique(
                self.evidence_record_ids + other.evidence_record_ids
            ),
            work_package_ids=_sorted_unique(self.work_package_ids + other.work_package_ids),
            capability_ids=_sorted_unique(self.capability_ids + other.capability_ids),
            research_report_ids=_sorted_unique(
                self.research_report_ids + other.research_report_ids
            ),
            backtest_ids=_sorted_unique(self.backtest_ids + other.backtest_ids),
            walk_forward_ids=_sorted_unique(self.walk_forward_ids + other.walk_forward_ids),
            monte_carlo_ids=_sorted_unique(self.monte_carlo_ids + other.monte_carlo_ids),
            stress_test_ids=_sorted_unique(self.stress_test_ids + other.stress_test_ids),
        )

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "specification_ids": list(self.specification_ids),
            "experiment_ids": list(self.experiment_ids),
            "dataset_ids": list(self.dataset_ids),
            "feature_ids": list(self.feature_ids),
            "validation_ids": list(self.validation_ids),
            "evidence_record_ids": list(self.evidence_record_ids),
            "work_package_ids": list(self.work_package_ids),
            "capability_ids": list(self.capability_ids),
            "research_report_ids": list(self.research_report_ids),
            "backtest_ids": list(self.backtest_ids),
            "walk_forward_ids": list(self.walk_forward_ids),
            "monte_carlo_ids": list(self.monte_carlo_ids),
            "stress_test_ids": list(self.stress_test_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceReferences:
        return cls(
            specification_ids=_sorted_unique(data.get("specification_ids", [])),
            experiment_ids=_sorted_unique(data.get("experiment_ids", [])),
            dataset_ids=_sorted_unique(data.get("dataset_ids", [])),
            feature_ids=_sorted_unique(data.get("feature_ids", [])),
            validation_ids=_sorted_unique(data.get("validation_ids", [])),
            evidence_record_ids=_sorted_unique(data.get("evidence_record_ids", [])),
            work_package_ids=_sorted_unique(data.get("work_package_ids", [])),
            capability_ids=_sorted_unique(data.get("capability_ids", [])),
            research_report_ids=_sorted_unique(data.get("research_report_ids", [])),
            backtest_ids=_sorted_unique(data.get("backtest_ids", [])),
            walk_forward_ids=_sorted_unique(data.get("walk_forward_ids", [])),
            monte_carlo_ids=_sorted_unique(data.get("monte_carlo_ids", [])),
            stress_test_ids=_sorted_unique(data.get("stress_test_ids", [])),
        )

    def all_identifiers(self) -> list[str]:
        return _sorted_unique(
            self.specification_ids
            + self.experiment_ids
            + self.dataset_ids
            + self.feature_ids
            + self.validation_ids
            + self.evidence_record_ids
            + self.work_package_ids
            + self.capability_ids
            + self.research_report_ids
            + self.backtest_ids
            + self.walk_forward_ids
            + self.monte_carlo_ids
            + self.stress_test_ids
        )


@dataclass
class ConfidenceDimensions:
    prior: float = 0.0
    statistical: float = 0.0
    economic: float = 0.0
    data: float = 0.0
    experimental: float = 0.0
    validation: float = 0.0
    replication: float = 0.0
    operational: float = 0.0
    last_updated: str = field(default_factory=_now_iso)

    def to_legacy(self) -> ConfidenceVector:
        return ConfidenceVector(
            prior=self.prior,
            statistical=self.statistical,
            economic=self.economic,
            data=self.data,
            model=self.experimental,
            validation=self.validation,
            replication=self.replication,
            operational=self.operational,
            last_updated=self.last_updated,
        )

    @classmethod
    def from_legacy(cls, vector: ConfidenceVector) -> ConfidenceDimensions:
        return cls(
            prior=float(vector.prior),
            statistical=float(vector.statistical),
            economic=float(vector.economic),
            data=float(vector.data),
            experimental=float(vector.model),
            validation=float(vector.validation),
            replication=float(vector.replication),
            operational=float(vector.operational),
            last_updated=vector.last_updated,
        )

    def with_multiplier(self, multiplier: float) -> ConfidenceDimensions:
        return ConfidenceDimensions(
            prior=self.prior,
            statistical=_clamp(self.statistical * multiplier),
            economic=_clamp(self.economic * multiplier),
            data=_clamp(self.data * multiplier),
            experimental=_clamp(self.experimental * multiplier),
            validation=_clamp(self.validation * multiplier),
            replication=_clamp(self.replication * multiplier),
            operational=_clamp(self.operational * multiplier),
            last_updated=self.last_updated,
        )

    def overall(self, entity_type: str = "IKROSEntity") -> float:
        weights = _WEIGHTS_BY_ENTITY_TYPE.get(entity_type, _DEFAULT_WEIGHTS)
        values = {
            "prior": self.prior,
            "statistical": self.statistical,
            "economic": self.economic,
            "data": self.data,
            "experimental": self.experimental,
            "validation": self.validation,
            "replication": self.replication,
            "operational": self.operational,
        }
        weighted_items = [
            (name, values[name], weight) for name, weight in weights.items() if weight > 0.0
        ]
        if not weighted_items:
            return _clamp(self.prior)
        weakest_link = min(value for _, value, _ in weighted_items)
        if weakest_link <= 0.0:
            return 0.0
        log_sum = sum(weight * math.log(value) for _, value, weight in weighted_items)
        geometric = math.exp(log_sum)
        return _clamp(min(geometric, weakest_link))

    def to_dict(self, entity_type: str = "IKROSEntity") -> dict[str, float | str]:
        return {
            "prior": self.prior,
            "statistical": self.statistical,
            "economic": self.economic,
            "data": self.data,
            "experimental": self.experimental,
            "validation": self.validation,
            "replication": self.replication,
            "operational": self.operational,
            "overall": self.overall(entity_type),
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfidenceDimensions:
        return cls(
            prior=float(data.get("prior", 0.0)),
            statistical=float(data.get("statistical", 0.0)),
            economic=float(data.get("economic", 0.0)),
            data=float(data.get("data", 0.0)),
            experimental=float(data.get("experimental", data.get("model", 0.0))),
            validation=float(data.get("validation", 0.0)),
            replication=float(data.get("replication", 0.0)),
            operational=float(data.get("operational", 0.0)),
            last_updated=str(data.get("last_updated", _now_iso())),
        )


@dataclass
class ConfidenceEvidence:
    evidence_id: str
    evidence_type: str
    relation: str = EvidenceRelation.SUPPORTS.value
    references: EvidenceReferences = field(default_factory=EvidenceReferences)
    confidence_weight: float = 1.0
    contradiction_severity: str | None = None
    independent_source: str = ""
    temporal_bucket: str = ""
    observed_at: str = field(default_factory=_now_iso)
    metrics: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": str(self.evidence_type),
            "relation": str(self.relation),
            "references": self.references.to_dict(),
            "confidence_weight": self.confidence_weight,
            "contradiction_severity": (
                str(self.contradiction_severity)
                if self.contradiction_severity is not None
                else None
            ),
            "independent_source": self.independent_source,
            "temporal_bucket": self.temporal_bucket,
            "observed_at": self.observed_at,
            "metrics": self.metrics,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfidenceEvidence:
        return cls(
            evidence_id=str(data["evidence_id"]),
            evidence_type=str(data["evidence_type"]),
            relation=str(data.get("relation", EvidenceRelation.SUPPORTS.value)),
            references=EvidenceReferences.from_dict(dict(data.get("references", {}))),
            confidence_weight=float(data.get("confidence_weight", 1.0)),
            contradiction_severity=(
                str(data["contradiction_severity"]) if data.get("contradiction_severity") else None
            ),
            independent_source=str(data.get("independent_source", "")),
            temporal_bucket=str(data.get("temporal_bucket", "")),
            observed_at=str(data.get("observed_at", _now_iso())),
            metrics=dict(data.get("metrics", {})),
            notes=str(data.get("notes", "")),
        )


@dataclass
class ResearchQualityIndicators:
    independent_validations: int = 0
    independent_validations_score: float = 0.0
    out_of_sample_confirmations: int = 0
    out_of_sample_score: float = 0.0
    regime_diversity: int = 0
    regime_diversity_score: float = 0.0
    dataset_diversity: int = 0
    dataset_diversity_score: float = 0.0
    temporal_diversity: int = 0
    temporal_diversity_score: float = 0.0
    replication_count: int = 0
    replication_score: float = 0.0
    contradiction_count: int = 0
    contradiction_score: float = 0.0
    evidence_freshness: float = 0.0
    research_maturity: float = 0.0
    validation_completeness: float = 0.0
    overall_quality: float = 0.0

    def to_dict(self) -> dict[str, float | int]:
        return {
            "independent_validations": self.independent_validations,
            "independent_validations_score": self.independent_validations_score,
            "out_of_sample_confirmations": self.out_of_sample_confirmations,
            "out_of_sample_score": self.out_of_sample_score,
            "regime_diversity": self.regime_diversity,
            "regime_diversity_score": self.regime_diversity_score,
            "dataset_diversity": self.dataset_diversity,
            "dataset_diversity_score": self.dataset_diversity_score,
            "temporal_diversity": self.temporal_diversity,
            "temporal_diversity_score": self.temporal_diversity_score,
            "replication_count": self.replication_count,
            "replication_score": self.replication_score,
            "contradiction_count": self.contradiction_count,
            "contradiction_score": self.contradiction_score,
            "evidence_freshness": self.evidence_freshness,
            "research_maturity": self.research_maturity,
            "validation_completeness": self.validation_completeness,
            "overall_quality": self.overall_quality,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResearchQualityIndicators:
        return cls(
            independent_validations=int(data.get("independent_validations", 0)),
            independent_validations_score=float(data.get("independent_validations_score", 0.0)),
            out_of_sample_confirmations=int(data.get("out_of_sample_confirmations", 0)),
            out_of_sample_score=float(data.get("out_of_sample_score", 0.0)),
            regime_diversity=int(data.get("regime_diversity", 0)),
            regime_diversity_score=float(data.get("regime_diversity_score", 0.0)),
            dataset_diversity=int(data.get("dataset_diversity", 0)),
            dataset_diversity_score=float(data.get("dataset_diversity_score", 0.0)),
            temporal_diversity=int(data.get("temporal_diversity", 0)),
            temporal_diversity_score=float(data.get("temporal_diversity_score", 0.0)),
            replication_count=int(data.get("replication_count", 0)),
            replication_score=float(data.get("replication_score", 0.0)),
            contradiction_count=int(data.get("contradiction_count", 0)),
            contradiction_score=float(data.get("contradiction_score", 0.0)),
            evidence_freshness=float(data.get("evidence_freshness", 0.0)),
            research_maturity=float(data.get("research_maturity", 0.0)),
            validation_completeness=float(data.get("validation_completeness", 0.0)),
            overall_quality=float(data.get("overall_quality", 0.0)),
        )


@dataclass
class ContradictionResolution:
    severity_counts: dict[str, int] = field(default_factory=dict)
    contradiction_multiplier: float = 1.0
    requires_review: bool = False
    recommended_action: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity_counts": dict(sorted(self.severity_counts.items())),
            "contradiction_multiplier": self.contradiction_multiplier,
            "requires_review": self.requires_review,
            "recommended_action": self.recommended_action,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContradictionResolution:
        severity_counts = {
            str(key): int(value) for key, value in dict(data.get("severity_counts", {})).items()
        }
        return cls(
            severity_counts=dict(sorted(severity_counts.items())),
            contradiction_multiplier=float(data.get("contradiction_multiplier", 1.0)),
            requires_review=bool(data.get("requires_review", False)),
            recommended_action=str(data.get("recommended_action", "NONE")),
        )


@dataclass
class PropagationImpact:
    target_id: str
    target_type: str
    depth: int
    previous_overall: float
    new_overall: float
    confidence: ConfidenceDimensions

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "target_type": self.target_type,
            "depth": self.depth,
            "previous_overall": self.previous_overall,
            "new_overall": self.new_overall,
            "confidence": self.confidence.to_dict(self.target_type),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PropagationImpact:
        return cls(
            target_id=str(data["target_id"]),
            target_type=str(data["target_type"]),
            depth=int(data["depth"]),
            previous_overall=float(data.get("previous_overall", 0.0)),
            new_overall=float(data.get("new_overall", 0.0)),
            confidence=ConfidenceDimensions.from_dict(dict(data.get("confidence", {}))),
        )


@dataclass
class ConfidenceAssessment:
    assessment_id: str
    target_id: str
    target_type: str
    reason: str
    operator: str
    references: EvidenceReferences
    evidence: list[ConfidenceEvidence]
    previous_confidence: ConfidenceDimensions
    assessed_confidence: ConfidenceDimensions
    quality: ResearchQualityIndicators
    contradiction_resolution: ContradictionResolution
    propagation: list[PropagationImpact] = field(default_factory=list)
    assessed_at: str = field(default_factory=_now_iso)
    source_assessment_id: str | None = None
    memory_record_id: str | None = None
    audit_id: str | None = None

    def previous_overall(self) -> float:
        return self.previous_confidence.overall(self.target_type)

    def new_overall(self) -> float:
        return self.assessed_confidence.overall(self.target_type)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "reason": self.reason,
            "operator": self.operator,
            "references": self.references.to_dict(),
            "evidence": [item.to_dict() for item in self.evidence],
            "previous_confidence": self.previous_confidence.to_dict(self.target_type),
            "assessed_confidence": self.assessed_confidence.to_dict(self.target_type),
            "quality": self.quality.to_dict(),
            "contradiction_resolution": self.contradiction_resolution.to_dict(),
            "propagation": [item.to_dict() for item in self.propagation],
            "assessed_at": self.assessed_at,
            "source_assessment_id": self.source_assessment_id,
            "memory_record_id": self.memory_record_id,
            "audit_id": self.audit_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfidenceAssessment:
        return cls(
            assessment_id=str(data["assessment_id"]),
            target_id=str(data["target_id"]),
            target_type=str(data["target_type"]),
            reason=str(data.get("reason", "")),
            operator=str(data.get("operator", "")),
            references=EvidenceReferences.from_dict(dict(data.get("references", {}))),
            evidence=[
                ConfidenceEvidence.from_dict(item)
                for item in data.get("evidence", [])
                if isinstance(item, dict)
            ],
            previous_confidence=ConfidenceDimensions.from_dict(
                dict(data.get("previous_confidence", {}))
            ),
            assessed_confidence=ConfidenceDimensions.from_dict(
                dict(data.get("assessed_confidence", {}))
            ),
            quality=ResearchQualityIndicators.from_dict(dict(data.get("quality", {}))),
            contradiction_resolution=ContradictionResolution.from_dict(
                dict(data.get("contradiction_resolution", {}))
            ),
            propagation=[
                PropagationImpact.from_dict(item)
                for item in data.get("propagation", [])
                if isinstance(item, dict)
            ],
            assessed_at=str(data.get("assessed_at", _now_iso())),
            source_assessment_id=(
                str(data["source_assessment_id"]) if data.get("source_assessment_id") else None
            ),
            memory_record_id=(
                str(data["memory_record_id"]) if data.get("memory_record_id") else None
            ),
            audit_id=str(data["audit_id"]) if data.get("audit_id") else None,
        )


@dataclass
class ConfidenceHistoryEntry:
    history_id: str
    assessment_id: str
    target_id: str
    target_type: str
    timestamp: str
    reason: str
    supporting_evidence: list[str]
    previous_confidence: ConfidenceDimensions
    new_confidence: ConfidenceDimensions
    operator: str
    specification_refs: list[str]
    work_package_refs: list[str]
    capability_refs: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "history_id": self.history_id,
            "assessment_id": self.assessment_id,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "timestamp": self.timestamp,
            "reason": self.reason,
            "supporting_evidence": list(self.supporting_evidence),
            "previous_confidence": self.previous_confidence.to_dict(self.target_type),
            "new_confidence": self.new_confidence.to_dict(self.target_type),
            "operator": self.operator,
            "specification_refs": list(self.specification_refs),
            "work_package_refs": list(self.work_package_refs),
            "capability_refs": list(self.capability_refs),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfidenceHistoryEntry:
        return cls(
            history_id=str(data["history_id"]),
            assessment_id=str(data["assessment_id"]),
            target_id=str(data["target_id"]),
            target_type=str(data["target_type"]),
            timestamp=str(data["timestamp"]),
            reason=str(data.get("reason", "")),
            supporting_evidence=_sorted_unique(data.get("supporting_evidence", [])),
            previous_confidence=ConfidenceDimensions.from_dict(
                dict(data.get("previous_confidence", {}))
            ),
            new_confidence=ConfidenceDimensions.from_dict(dict(data.get("new_confidence", {}))),
            operator=str(data.get("operator", "")),
            specification_refs=_sorted_unique(data.get("specification_refs", [])),
            work_package_refs=_sorted_unique(data.get("work_package_refs", [])),
            capability_refs=_sorted_unique(data.get("capability_refs", [])),
        )


@dataclass
class ConfidenceAuditEntry:
    audit_id: str
    assessment_id: str
    timestamp: str
    target_id: str
    target_type: str
    reason: str
    supporting_evidence: list[str]
    previous_confidence: ConfidenceDimensions
    new_confidence: ConfidenceDimensions
    operator: str
    specification_refs: list[str]
    work_package_refs: list[str]
    capability_refs: list[str]
    propagated_targets: list[str]
    previous_hash: str
    entry_hash: str

    def fingerprint(self) -> str:
        return json.dumps(
            {
                "audit_id": self.audit_id,
                "assessment_id": self.assessment_id,
                "timestamp": self.timestamp,
                "target_id": self.target_id,
                "target_type": self.target_type,
                "reason": self.reason,
                "supporting_evidence": sorted(self.supporting_evidence),
                "previous_confidence": self.previous_confidence.to_dict(self.target_type),
                "new_confidence": self.new_confidence.to_dict(self.target_type),
                "operator": self.operator,
                "specification_refs": sorted(self.specification_refs),
                "work_package_refs": sorted(self.work_package_refs),
                "capability_refs": sorted(self.capability_refs),
                "propagated_targets": sorted(self.propagated_targets),
                "previous_hash": self.previous_hash,
            },
            sort_keys=True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "assessment_id": self.assessment_id,
            "timestamp": self.timestamp,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "reason": self.reason,
            "supporting_evidence": list(self.supporting_evidence),
            "previous_confidence": self.previous_confidence.to_dict(self.target_type),
            "new_confidence": self.new_confidence.to_dict(self.target_type),
            "operator": self.operator,
            "specification_refs": list(self.specification_refs),
            "work_package_refs": list(self.work_package_refs),
            "capability_refs": list(self.capability_refs),
            "propagated_targets": list(self.propagated_targets),
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfidenceAuditEntry:
        return cls(
            audit_id=str(data["audit_id"]),
            assessment_id=str(data["assessment_id"]),
            timestamp=str(data["timestamp"]),
            target_id=str(data["target_id"]),
            target_type=str(data["target_type"]),
            reason=str(data.get("reason", "")),
            supporting_evidence=_sorted_unique(data.get("supporting_evidence", [])),
            previous_confidence=ConfidenceDimensions.from_dict(
                dict(data.get("previous_confidence", {}))
            ),
            new_confidence=ConfidenceDimensions.from_dict(dict(data.get("new_confidence", {}))),
            operator=str(data.get("operator", "")),
            specification_refs=_sorted_unique(data.get("specification_refs", [])),
            work_package_refs=_sorted_unique(data.get("work_package_refs", [])),
            capability_refs=_sorted_unique(data.get("capability_refs", [])),
            propagated_targets=_sorted_unique(data.get("propagated_targets", [])),
            previous_hash=str(data.get("previous_hash", "")),
            entry_hash=str(data.get("entry_hash", "")),
        )

    @classmethod
    def build(
        cls,
        *,
        audit_id: str,
        assessment: ConfidenceAssessment,
        previous_hash: str,
    ) -> ConfidenceAuditEntry:
        provisional = cls(
            audit_id=audit_id,
            assessment_id=assessment.assessment_id,
            timestamp=assessment.assessed_at,
            target_id=assessment.target_id,
            target_type=assessment.target_type,
            reason=assessment.reason,
            supporting_evidence=[item.evidence_id for item in assessment.evidence],
            previous_confidence=assessment.previous_confidence,
            new_confidence=assessment.assessed_confidence,
            operator=assessment.operator,
            specification_refs=list(assessment.references.specification_ids),
            work_package_refs=list(assessment.references.work_package_ids),
            capability_refs=list(assessment.references.capability_ids),
            propagated_targets=[item.target_id for item in assessment.propagation],
            previous_hash=previous_hash,
            entry_hash="",
        )
        entry_hash = hashlib.sha256(provisional.fingerprint().encode("utf-8")).hexdigest()
        provisional.entry_hash = entry_hash
        return provisional


_DEFAULT_WEIGHTS: dict[str, float] = {
    "prior": 0.05,
    "statistical": 0.15,
    "economic": 0.15,
    "data": 0.15,
    "experimental": 0.15,
    "validation": 0.15,
    "replication": 0.10,
    "operational": 0.10,
}

_WEIGHTS_BY_ENTITY_TYPE: dict[str, dict[str, float]] = {
    "Hypothesis": {
        "prior": 0.00,
        "statistical": 0.25,
        "economic": 0.15,
        "data": 0.15,
        "experimental": 0.10,
        "validation": 0.20,
        "replication": 0.10,
        "operational": 0.05,
    },
    "AlphaCandidate": {
        "prior": 0.00,
        "statistical": 0.15,
        "economic": 0.10,
        "data": 0.10,
        "experimental": 0.15,
        "validation": 0.25,
        "replication": 0.10,
        "operational": 0.15,
    },
    "Alpha": {
        "prior": 0.00,
        "statistical": 0.15,
        "economic": 0.10,
        "data": 0.10,
        "experimental": 0.15,
        "validation": 0.25,
        "replication": 0.10,
        "operational": 0.15,
    },
    "ResearchQuestion": {
        "prior": 0.15,
        "statistical": 0.10,
        "economic": 0.20,
        "data": 0.10,
        "experimental": 0.10,
        "validation": 0.15,
        "replication": 0.10,
        "operational": 0.10,
    },
    "Experiment": {
        "prior": 0.05,
        "statistical": 0.15,
        "economic": 0.05,
        "data": 0.20,
        "experimental": 0.25,
        "validation": 0.15,
        "replication": 0.10,
        "operational": 0.05,
    },
    "Feature": {
        "prior": 0.05,
        "statistical": 0.10,
        "economic": 0.10,
        "data": 0.20,
        "experimental": 0.20,
        "validation": 0.15,
        "replication": 0.10,
        "operational": 0.10,
    },
    "FeatureFamily": {
        "prior": 0.05,
        "statistical": 0.10,
        "economic": 0.10,
        "data": 0.20,
        "experimental": 0.20,
        "validation": 0.15,
        "replication": 0.10,
        "operational": 0.10,
    },
    "KnowledgeObject": {
        "prior": 0.00,
        "statistical": 0.15,
        "economic": 0.20,
        "data": 0.10,
        "experimental": 0.05,
        "validation": 0.20,
        "replication": 0.25,
        "operational": 0.05,
    },
    "EconomicThesis": {
        "prior": 0.05,
        "statistical": 0.10,
        "economic": 0.30,
        "data": 0.10,
        "experimental": 0.05,
        "validation": 0.15,
        "replication": 0.20,
        "operational": 0.05,
    },
}


def _sorted_unique(values: list[str] | tuple[str, ...] | set[str]) -> list[str]:
    return sorted({str(value) for value in values if value})
