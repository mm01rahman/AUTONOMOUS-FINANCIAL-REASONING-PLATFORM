"""IKROS entity models — Pydantic dataclasses for all first-class research objects.

All entities are defined with:
- Canonical IKROS identifier (ikros_id)
- Lifecycle state
- Lineage metadata
- Confidence vector
- Audit trail
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ResearchScope(StrEnum):
    MICRO = "MICRO"
    MACRO = "MACRO"
    REGIME = "REGIME"
    STRUCTURAL = "STRUCTURAL"


class ResearchStatus(StrEnum):
    OPEN = "OPEN"
    ACTIVE = "ACTIVE"
    ANSWERED = "ANSWERED"
    RETIRED = "RETIRED"


class HypothesisStatus(StrEnum):
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED_FOR_TESTING = "APPROVED_FOR_TESTING"
    TESTING = "TESTING"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    RETIRED = "RETIRED"


class ExperimentStatus(StrEnum):
    DESIGNED = "DESIGNED"
    APPROVED = "APPROVED"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    REVIEWED = "REVIEWED"
    ARCHIVED = "ARCHIVED"
    INVALIDATED = "INVALIDATED"


class FeatureStatus(StrEnum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


class Stationarity(StrEnum):
    STATIONARY = "STATIONARY"
    NON_STATIONARY = "NON_STATIONARY"
    UNKNOWN = "UNKNOWN"


class PromotionStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    RETIRED = "RETIRED"


class StrategyType(StrEnum):
    TREND = "TREND"
    MEAN_REVERSION = "MEAN_REVERSION"
    LIQUIDITY = "LIQUIDITY"
    MACRO = "MACRO"
    TECHNICAL = "TECHNICAL"
    HYBRID = "HYBRID"


class AlphaPaperStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Confidence vector
# ---------------------------------------------------------------------------


@dataclass
class ConfidenceVector:
    """8-dimensional confidence vector per IKROS-CONFIDENCE.md §2."""

    prior: float = 0.0
    statistical: float = 0.0
    economic: float = 0.0
    data: float = 0.0
    model: float = 0.0
    validation: float = 0.0
    replication: float = 0.0
    operational: float = 0.0
    last_updated: str = field(default_factory=lambda: _now_iso())

    def overall(self) -> float:
        """Compute geometric-mean overall confidence (equal weights)."""
        dims = [
            self.statistical,
            self.economic,
            self.data,
            self.model,
            self.validation,
            self.replication,
            self.operational,
        ]
        # Exclude prior from geometric mean; use it as a floor
        product = 1.0
        count = 0
        for d in dims:
            if d > 0.0:
                product *= d
                count += 1
        if count == 0:
            return max(self.prior, 0.0)
        geom = product ** (1.0 / count)
        return float(min(geom, 0.95))  # Max confidence cap

    def to_dict(self) -> dict[str, Any]:
        return {
            "prior": self.prior,
            "statistical": self.statistical,
            "economic": self.economic,
            "data": self.data,
            "model": self.model,
            "validation": self.validation,
            "replication": self.replication,
            "operational": self.operational,
            "overall": self.overall(),
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ConfidenceVector:
        return cls(
            prior=float(d.get("prior", 0.0)),
            statistical=float(d.get("statistical", 0.0)),
            economic=float(d.get("economic", 0.0)),
            data=float(d.get("data", 0.0)),
            model=float(d.get("model", 0.0)),
            validation=float(d.get("validation", 0.0)),
            replication=float(d.get("replication", 0.0)),
            operational=float(d.get("operational", 0.0)),
            last_updated=str(d.get("last_updated", _now_iso())),
        )


# ---------------------------------------------------------------------------
# Lineage metadata
# ---------------------------------------------------------------------------


@dataclass
class LineageOrigin:
    created_by: str
    created_at: str
    creation_context: str
    motivation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_by": self.created_by,
            "created_at": self.created_at,
            "creation_context": self.creation_context,
            "motivation": self.motivation,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LineageOrigin:
        return cls(
            created_by=str(d["created_by"]),
            created_at=str(d["created_at"]),
            creation_context=str(d["creation_context"]),
            motivation=str(d["motivation"]),
        )


@dataclass
class LineageDependencies:
    inputs: list[str] = field(default_factory=list)
    datasets: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    external_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "inputs": self.inputs,
            "datasets": self.datasets,
            "features": self.features,
            "models": self.models,
            "external_refs": self.external_refs,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LineageDependencies:
        return cls(
            inputs=list(d.get("inputs", [])),
            datasets=list(d.get("datasets", [])),
            features=list(d.get("features", [])),
            models=list(d.get("models", [])),
            external_refs=list(d.get("external_refs", [])),
        )


@dataclass
class LineageExperiments:
    tested_in: list[str] = field(default_factory=list)
    validated_by: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"tested_in": self.tested_in, "validated_by": self.validated_by}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LineageExperiments:
        return cls(
            tested_in=list(d.get("tested_in", [])),
            validated_by=list(d.get("validated_by", [])),
        )


@dataclass
class LineageEvidence:
    supporting: list[str] = field(default_factory=list)
    contradicting: list[str] = field(default_factory=list)
    ers_records: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "supporting": self.supporting,
            "contradicting": self.contradicting,
            "ers_records": self.ers_records,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LineageEvidence:
        return cls(
            supporting=list(d.get("supporting", [])),
            contradicting=list(d.get("contradicting", [])),
            ers_records=list(d.get("ers_records", [])),
        )


@dataclass
class LineageSuccessors:
    refined_by: str | None = None
    superseded_by: str | None = None
    inspired: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "refined_by": self.refined_by,
            "superseded_by": self.superseded_by,
            "inspired": self.inspired,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LineageSuccessors:
        return cls(
            refined_by=d.get("refined_by"),
            superseded_by=d.get("superseded_by"),
            inspired=list(d.get("inspired", [])),
        )


@dataclass
class LineageRetirement:
    retired_at: str | None = None
    retired_by: str | None = None
    retirement_reason: str | None = None
    successor_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "retired_at": self.retired_at,
            "retired_by": self.retired_by,
            "retirement_reason": self.retirement_reason,
            "successor_id": self.successor_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LineageRetirement:
        return cls(
            retired_at=d.get("retired_at"),
            retired_by=d.get("retired_by"),
            retirement_reason=d.get("retirement_reason"),
            successor_id=d.get("successor_id"),
        )


@dataclass
class LineageRecord:
    """Complete provenance record per IKROS-LINEAGE.md §2."""

    origin: LineageOrigin
    dependencies: LineageDependencies = field(default_factory=LineageDependencies)
    experiments: LineageExperiments = field(default_factory=LineageExperiments)
    evidence: LineageEvidence = field(default_factory=LineageEvidence)
    successors: LineageSuccessors = field(default_factory=LineageSuccessors)
    retirement: LineageRetirement = field(default_factory=LineageRetirement)

    def to_dict(self) -> dict[str, Any]:
        return {
            "origin": self.origin.to_dict(),
            "dependencies": self.dependencies.to_dict(),
            "experiments": self.experiments.to_dict(),
            "evidence": self.evidence.to_dict(),
            "successors": self.successors.to_dict(),
            "retirement": self.retirement.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LineageRecord:
        return cls(
            origin=LineageOrigin.from_dict(d["origin"]),
            dependencies=LineageDependencies.from_dict(d.get("dependencies", {})),
            experiments=LineageExperiments.from_dict(d.get("experiments", {})),
            evidence=LineageEvidence.from_dict(d.get("evidence", {})),
            successors=LineageSuccessors.from_dict(d.get("successors", {})),
            retirement=LineageRetirement.from_dict(d.get("retirement", {})),
        )


# ---------------------------------------------------------------------------
# Base entity
# ---------------------------------------------------------------------------


@dataclass
class IKROSEntity:
    """Common attributes shared by all IKROS entities."""

    ikros_id: str
    entity_type: str
    version: str
    lifecycle_state: str
    confidence: ConfidenceVector
    lineage: LineageRecord
    spec_refs: list[str] = field(default_factory=list)
    capability_refs: list[str] = field(default_factory=list)
    work_package_refs: list[str] = field(default_factory=list)
    version_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ikros_id": self.ikros_id,
            "entity_type": self.entity_type,
            "version": self.version,
            "lifecycle_state": self.lifecycle_state,
            "confidence": self.confidence.to_dict(),
            "lineage": self.lineage.to_dict(),
            "spec_refs": self.spec_refs,
            "capability_refs": self.capability_refs,
            "work_package_refs": self.work_package_refs,
            "version_history": self.version_history,
        }


# ---------------------------------------------------------------------------
# ResearchQuestion
# ---------------------------------------------------------------------------


@dataclass
class ResearchQuestion(IKROSEntity):
    """A formal research question motivating a research campaign."""

    title: str = ""
    motivation: str = ""
    scope: str = ResearchScope.MACRO.value
    instrument: str = ""
    time_horizon: str = ""
    campaign_tag: str = ""
    linked_hypotheses: list[str] = field(default_factory=list)
    linked_conclusions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "title": self.title,
                "motivation": self.motivation,
                "scope": self.scope,
                "instrument": self.instrument,
                "time_horizon": self.time_horizon,
                "campaign_tag": self.campaign_tag,
                "linked_hypotheses": self.linked_hypotheses,
                "linked_conclusions": self.linked_conclusions,
            }
        )
        return base

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ResearchQuestion:
        return cls(
            ikros_id=str(d["ikros_id"]),
            entity_type="ResearchQuestion",
            version=str(d.get("version", "1.0.0")),
            lifecycle_state=str(d.get("lifecycle_state", ResearchStatus.OPEN.value)),
            confidence=ConfidenceVector.from_dict(d.get("confidence", {})),
            lineage=LineageRecord.from_dict(d["lineage"]),
            spec_refs=list(d.get("spec_refs", [])),
            capability_refs=list(d.get("capability_refs", [])),
            work_package_refs=list(d.get("work_package_refs", [])),
            version_history=list(d.get("version_history", [])),
            title=str(d.get("title", "")),
            motivation=str(d.get("motivation", "")),
            scope=str(d.get("scope", ResearchScope.MACRO.value)),
            instrument=str(d.get("instrument", "")),
            time_horizon=str(d.get("time_horizon", "")),
            campaign_tag=str(d.get("campaign_tag", "")),
            linked_hypotheses=list(d.get("linked_hypotheses", [])),
            linked_conclusions=list(d.get("linked_conclusions", [])),
        )


# ---------------------------------------------------------------------------
# Hypothesis
# ---------------------------------------------------------------------------


@dataclass
class Hypothesis(IKROSEntity):
    """A testable, falsifiable prediction about market behaviour."""

    statement: str = ""
    null_hypothesis: str = ""
    alternative_hypothesis: str = ""
    significance_level: float = 0.05
    power: float = 0.80
    prior_confidence: float = 0.0
    posterior_confidence: float = 0.0
    source_rq: str = ""
    motivating_theses: list[str] = field(default_factory=list)
    experiments: list[str] = field(default_factory=list)
    validations: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "statement": self.statement,
                "null_hypothesis": self.null_hypothesis,
                "alternative_hypothesis": self.alternative_hypothesis,
                "significance_level": self.significance_level,
                "power": self.power,
                "prior_confidence": self.prior_confidence,
                "posterior_confidence": self.posterior_confidence,
                "source_rq": self.source_rq,
                "motivating_theses": self.motivating_theses,
                "experiments": self.experiments,
                "validations": self.validations,
                "contradictions": self.contradictions,
            }
        )
        return base

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Hypothesis:
        return cls(
            ikros_id=str(d["ikros_id"]),
            entity_type="Hypothesis",
            version=str(d.get("version", "1.0.0")),
            lifecycle_state=str(d.get("lifecycle_state", HypothesisStatus.PROPOSED.value)),
            confidence=ConfidenceVector.from_dict(d.get("confidence", {})),
            lineage=LineageRecord.from_dict(d["lineage"]),
            spec_refs=list(d.get("spec_refs", [])),
            capability_refs=list(d.get("capability_refs", [])),
            work_package_refs=list(d.get("work_package_refs", [])),
            version_history=list(d.get("version_history", [])),
            statement=str(d.get("statement", "")),
            null_hypothesis=str(d.get("null_hypothesis", "")),
            alternative_hypothesis=str(d.get("alternative_hypothesis", "")),
            significance_level=float(d.get("significance_level", 0.05)),
            power=float(d.get("power", 0.80)),
            prior_confidence=float(d.get("prior_confidence", 0.0)),
            posterior_confidence=float(d.get("posterior_confidence", 0.0)),
            source_rq=str(d.get("source_rq", "")),
            motivating_theses=list(d.get("motivating_theses", [])),
            experiments=list(d.get("experiments", [])),
            validations=list(d.get("validations", [])),
            contradictions=list(d.get("contradictions", [])),
        )


# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------


@dataclass
class Experiment(IKROSEntity):
    """A governed research execution testing one or more hypotheses."""

    title: str = ""
    hypotheses: list[str] = field(default_factory=list)
    protocol: str = ""
    dataset_versions: list[str] = field(default_factory=list)
    feature_versions: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    random_seed: int = 42
    in_sample_start: str = ""
    in_sample_end: str = ""
    out_of_sample_start: str = ""
    out_of_sample_end: str = ""
    reproducibility_hash: str = ""
    git_commit: str = ""
    completed_at: str | None = None
    validations_produced: list[str] = field(default_factory=list)
    failures_produced: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "title": self.title,
                "hypotheses": self.hypotheses,
                "protocol": self.protocol,
                "dataset_versions": self.dataset_versions,
                "feature_versions": self.feature_versions,
                "parameters": self.parameters,
                "random_seed": self.random_seed,
                "in_sample_start": self.in_sample_start,
                "in_sample_end": self.in_sample_end,
                "out_of_sample_start": self.out_of_sample_start,
                "out_of_sample_end": self.out_of_sample_end,
                "reproducibility_hash": self.reproducibility_hash,
                "git_commit": self.git_commit,
                "completed_at": self.completed_at,
                "validations_produced": self.validations_produced,
                "failures_produced": self.failures_produced,
            }
        )
        return base

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Experiment:
        return cls(
            ikros_id=str(d["ikros_id"]),
            entity_type="Experiment",
            version=str(d.get("version", "1.0.0")),
            lifecycle_state=str(d.get("lifecycle_state", ExperimentStatus.DESIGNED.value)),
            confidence=ConfidenceVector.from_dict(d.get("confidence", {})),
            lineage=LineageRecord.from_dict(d["lineage"]),
            spec_refs=list(d.get("spec_refs", [])),
            capability_refs=list(d.get("capability_refs", [])),
            work_package_refs=list(d.get("work_package_refs", [])),
            version_history=list(d.get("version_history", [])),
            title=str(d.get("title", "")),
            hypotheses=list(d.get("hypotheses", [])),
            protocol=str(d.get("protocol", "")),
            dataset_versions=list(d.get("dataset_versions", [])),
            feature_versions=list(d.get("feature_versions", [])),
            parameters=dict(d.get("parameters", {})),
            random_seed=int(d.get("random_seed", 42)),
            in_sample_start=str(d.get("in_sample_start", "")),
            in_sample_end=str(d.get("in_sample_end", "")),
            out_of_sample_start=str(d.get("out_of_sample_start", "")),
            out_of_sample_end=str(d.get("out_of_sample_end", "")),
            reproducibility_hash=str(d.get("reproducibility_hash", "")),
            git_commit=str(d.get("git_commit", "")),
            completed_at=d.get("completed_at"),
            validations_produced=list(d.get("validations_produced", [])),
            failures_produced=list(d.get("failures_produced", [])),
        )


# ---------------------------------------------------------------------------
# Feature / FeatureFamily
# ---------------------------------------------------------------------------


@dataclass
class FeatureFamily(IKROSEntity):
    """A named group of related features sharing common theoretical motivation."""

    name: str = ""
    description: str = ""
    member_features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "name": self.name,
                "description": self.description,
                "member_features": self.member_features,
            }
        )
        return base

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FeatureFamily:
        return cls(
            ikros_id=str(d["ikros_id"]),
            entity_type="FeatureFamily",
            version=str(d.get("version", "1.0.0")),
            lifecycle_state=str(d.get("lifecycle_state", FeatureStatus.ACTIVE.value)),
            confidence=ConfidenceVector.from_dict(d.get("confidence", {})),
            lineage=LineageRecord.from_dict(d["lineage"]),
            spec_refs=list(d.get("spec_refs", [])),
            capability_refs=list(d.get("capability_refs", [])),
            work_package_refs=list(d.get("work_package_refs", [])),
            version_history=list(d.get("version_history", [])),
            name=str(d.get("name", "")),
            description=str(d.get("description", "")),
            member_features=list(d.get("member_features", [])),
        )


@dataclass
class Feature(IKROSEntity):
    """A derived input signal computed from raw market data."""

    name: str = ""
    family_id: str = ""
    computation: str = ""
    inputs: list[str] = field(default_factory=list)
    lookback: str = ""
    normalization: str = ""
    stationarity: str = Stationarity.UNKNOWN.value
    information_content: float = 0.0
    stability_score: float = 0.0
    used_in_experiments: list[str] = field(default_factory=list)
    superseded_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "name": self.name,
                "family_id": self.family_id,
                "computation": self.computation,
                "inputs": self.inputs,
                "lookback": self.lookback,
                "normalization": self.normalization,
                "stationarity": self.stationarity,
                "information_content": self.information_content,
                "stability_score": self.stability_score,
                "used_in_experiments": self.used_in_experiments,
                "superseded_by": self.superseded_by,
            }
        )
        return base

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Feature:
        return cls(
            ikros_id=str(d["ikros_id"]),
            entity_type="Feature",
            version=str(d.get("version", "1.0.0")),
            lifecycle_state=str(d.get("lifecycle_state", FeatureStatus.DRAFT.value)),
            confidence=ConfidenceVector.from_dict(d.get("confidence", {})),
            lineage=LineageRecord.from_dict(d["lineage"]),
            spec_refs=list(d.get("spec_refs", [])),
            capability_refs=list(d.get("capability_refs", [])),
            work_package_refs=list(d.get("work_package_refs", [])),
            version_history=list(d.get("version_history", [])),
            name=str(d.get("name", "")),
            family_id=str(d.get("family_id", "")),
            computation=str(d.get("computation", "")),
            inputs=list(d.get("inputs", [])),
            lookback=str(d.get("lookback", "")),
            normalization=str(d.get("normalization", "")),
            stationarity=str(d.get("stationarity", Stationarity.UNKNOWN.value)),
            information_content=float(d.get("information_content", 0.0)),
            stability_score=float(d.get("stability_score", 0.0)),
            used_in_experiments=list(d.get("used_in_experiments", [])),
            superseded_by=d.get("superseded_by"),
        )


# ---------------------------------------------------------------------------
# AlphaCandidate / Alpha
# ---------------------------------------------------------------------------


@dataclass
class AlphaCandidate(IKROSEntity):
    """A strategy that has completed research but has not yet met promotion criteria."""

    name: str = ""
    strategy_type: str = StrategyType.HYBRID.value
    sharpe_oos: float = 0.0
    max_drawdown: float = 0.0
    direction_accuracy: float = 0.0
    win_rate: float = 0.0
    promotion_score: float = 0.0
    promotion_status: str = PromotionStatus.CANDIDATE.value
    rejection_reasons: list[str] = field(default_factory=list)
    backtests: list[str] = field(default_factory=list)
    walk_forwards: list[str] = field(default_factory=list)
    monte_carlos: list[str] = field(default_factory=list)
    implements_hypotheses: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "name": self.name,
                "strategy_type": self.strategy_type,
                "sharpe_oos": self.sharpe_oos,
                "max_drawdown": self.max_drawdown,
                "direction_accuracy": self.direction_accuracy,
                "win_rate": self.win_rate,
                "promotion_score": self.promotion_score,
                "promotion_status": self.promotion_status,
                "rejection_reasons": self.rejection_reasons,
                "backtests": self.backtests,
                "walk_forwards": self.walk_forwards,
                "monte_carlos": self.monte_carlos,
                "implements_hypotheses": self.implements_hypotheses,
            }
        )
        return base

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AlphaCandidate:
        return cls(
            ikros_id=str(d["ikros_id"]),
            entity_type="AlphaCandidate",
            version=str(d.get("version", "1.0.0")),
            lifecycle_state=str(d.get("lifecycle_state", PromotionStatus.CANDIDATE.value)),
            confidence=ConfidenceVector.from_dict(d.get("confidence", {})),
            lineage=LineageRecord.from_dict(d["lineage"]),
            spec_refs=list(d.get("spec_refs", [])),
            capability_refs=list(d.get("capability_refs", [])),
            work_package_refs=list(d.get("work_package_refs", [])),
            version_history=list(d.get("version_history", [])),
            name=str(d.get("name", "")),
            strategy_type=str(d.get("strategy_type", StrategyType.HYBRID.value)),
            sharpe_oos=float(d.get("sharpe_oos", 0.0)),
            max_drawdown=float(d.get("max_drawdown", 0.0)),
            direction_accuracy=float(d.get("direction_accuracy", 0.0)),
            win_rate=float(d.get("win_rate", 0.0)),
            promotion_score=float(d.get("promotion_score", 0.0)),
            promotion_status=str(d.get("promotion_status", PromotionStatus.CANDIDATE.value)),
            rejection_reasons=list(d.get("rejection_reasons", [])),
            backtests=list(d.get("backtests", [])),
            walk_forwards=list(d.get("walk_forwards", [])),
            monte_carlos=list(d.get("monte_carlos", [])),
            implements_hypotheses=list(d.get("implements_hypotheses", [])),
        )


@dataclass
class Alpha(IKROSEntity):
    """A strategy that has passed all promotion criteria and is approved for paper trading."""

    promoted_from: str = ""
    promotion_date: str = ""
    promotion_evidence: str = ""
    paper_trading_status: str = AlphaPaperStatus.NOT_STARTED.value
    live_eligible: bool = False

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "promoted_from": self.promoted_from,
                "promotion_date": self.promotion_date,
                "promotion_evidence": self.promotion_evidence,
                "paper_trading_status": self.paper_trading_status,
                "live_eligible": self.live_eligible,
            }
        )
        return base

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Alpha:
        return cls(
            ikros_id=str(d["ikros_id"]),
            entity_type="Alpha",
            version=str(d.get("version", "1.0.0")),
            lifecycle_state=str(d.get("lifecycle_state", PromotionStatus.PROMOTED.value)),
            confidence=ConfidenceVector.from_dict(d.get("confidence", {})),
            lineage=LineageRecord.from_dict(d["lineage"]),
            spec_refs=list(d.get("spec_refs", [])),
            capability_refs=list(d.get("capability_refs", [])),
            work_package_refs=list(d.get("work_package_refs", [])),
            version_history=list(d.get("version_history", [])),
            promoted_from=str(d.get("promoted_from", "")),
            promotion_date=str(d.get("promotion_date", "")),
            promotion_evidence=str(d.get("promotion_evidence", "")),
            paper_trading_status=str(
                d.get("paper_trading_status", AlphaPaperStatus.NOT_STARTED.value)
            ),
            live_eligible=bool(d.get("live_eligible", False)),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
