"""IKROS validation — schema, referential integrity, lifecycle, and lineage checks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tools.ikros.identifiers import is_valid_ikros_id
from tools.ikros.models import (
    Alpha,
    AlphaCandidate,
    Experiment,
    ExperimentStatus,
    Feature,
    FeatureFamily,
    Hypothesis,
    HypothesisStatus,
    IKROSEntity,
    PromotionStatus,
    ResearchQuestion,
    ResearchStatus,
)

if TYPE_CHECKING:
    pass


class ValidationError(ValueError):
    """Raised when an IKROS entity fails schema or governance validation."""


# ---------------------------------------------------------------------------
# Base validation
# ---------------------------------------------------------------------------


def _check_base(entity: IKROSEntity) -> list[str]:
    """Return list of base validation failures."""
    errors: list[str] = []
    if not entity.ikros_id:
        errors.append("ikros_id is required")
    elif not is_valid_ikros_id(entity.ikros_id):
        errors.append(f"ikros_id '{entity.ikros_id}' does not match canonical pattern")
    if not entity.lifecycle_state:
        errors.append("lifecycle_state is required")
    if not entity.lineage.origin.created_by:
        errors.append("lineage.origin.created_by is required (LIN-001)")
    if not entity.lineage.origin.created_at:
        errors.append("lineage.origin.created_at is required (LIN-002)")
    return errors


# ---------------------------------------------------------------------------
# Entity-specific validation
# ---------------------------------------------------------------------------


def validate_research_question(rq: ResearchQuestion) -> list[str]:
    errors = _check_base(rq)
    if not rq.title:
        errors.append("title is required")
    if not rq.instrument:
        errors.append("instrument is required")
    if rq.lifecycle_state not in {s.value for s in ResearchStatus}:
        errors.append(f"lifecycle_state '{rq.lifecycle_state}' is not valid for ResearchQuestion")
    return errors


def validate_hypothesis(hyp: Hypothesis) -> list[str]:
    errors = _check_base(hyp)
    if not hyp.statement:
        errors.append("statement is required")
    if not hyp.null_hypothesis:
        errors.append("null_hypothesis is required")
    if hyp.lifecycle_state not in {s.value for s in HypothesisStatus}:
        errors.append(f"lifecycle_state '{hyp.lifecycle_state}' is not valid for Hypothesis")
    if hyp.lifecycle_state in {
        HypothesisStatus.SUPPORTED.value,
        HypothesisStatus.REFUTED.value,
    }:
        if not hyp.lineage.experiments.validated_by:
            errors.append("validated_by must be non-empty for SUPPORTED/REFUTED (LIN-004)")
    if hyp.lifecycle_state in {
        HypothesisStatus.TESTING.value,
        HypothesisStatus.SUPPORTED.value,
        HypothesisStatus.REFUTED.value,
    }:
        if not hyp.lineage.experiments.tested_in:
            errors.append("tested_in must be non-empty once TESTING (LIN-004)")
    if not (0.0 <= hyp.significance_level <= 1.0):
        errors.append("significance_level must be in [0, 1]")
    if not (0.0 <= hyp.power <= 1.0):
        errors.append("power must be in [0, 1]")
    return errors


def validate_experiment(exp: Experiment) -> list[str]:
    errors = _check_base(exp)
    if not exp.title:
        errors.append("title is required")
    if exp.lifecycle_state not in {s.value for s in ExperimentStatus}:
        errors.append(f"lifecycle_state '{exp.lifecycle_state}' is not valid for Experiment")
    if exp.lifecycle_state == ExperimentStatus.COMPLETE.value:
        if not exp.reproducibility_hash:
            errors.append("reproducibility_hash required when COMPLETE (LIN-009)")
    if exp.lifecycle_state in {
        ExperimentStatus.APPROVED.value,
        ExperimentStatus.RUNNING.value,
        ExperimentStatus.COMPLETE.value,
    }:
        if not exp.lineage.dependencies.datasets:
            errors.append("dependencies.datasets must be non-empty (LIN-003)")
    return errors


def validate_feature(feat: Feature) -> list[str]:
    errors = _check_base(feat)
    if not feat.name:
        errors.append("name is required")
    if not feat.computation:
        errors.append("computation is required")
    if not (0.0 <= feat.information_content <= 1.0):
        errors.append("information_content must be in [0, 1]")
    if not (0.0 <= feat.stability_score <= 1.0):
        errors.append("stability_score must be in [0, 1]")
    return errors


def validate_feature_family(ff: FeatureFamily) -> list[str]:
    errors = _check_base(ff)
    if not ff.name:
        errors.append("name is required")
    return errors


def validate_alpha_candidate(cand: AlphaCandidate) -> list[str]:
    errors = _check_base(cand)
    if not cand.name:
        errors.append("name is required")
    if cand.promotion_status == PromotionStatus.REJECTED.value:
        if not cand.rejection_reasons:
            errors.append("rejection_reasons must be non-empty when REJECTED")
    if cand.promotion_status == PromotionStatus.PROMOTED.value:
        if not cand.lineage.evidence.ers_records:
            errors.append("ers_records must be non-empty when PROMOTED (LIN-006)")
    if not (-10.0 <= cand.sharpe_oos <= 10.0):
        errors.append("sharpe_oos must be in [-10, 10]")
    if not (0.0 <= cand.direction_accuracy <= 1.0):
        errors.append("direction_accuracy must be in [0, 1]")
    return errors


def validate_alpha(alpha: Alpha) -> list[str]:
    errors = _check_base(alpha)
    if not alpha.promoted_from:
        errors.append("promoted_from is required")
    if not alpha.promotion_date:
        errors.append("promotion_date is required")
    if not alpha.lineage.evidence.ers_records:
        errors.append("ers_records must be non-empty (LIN-006)")
    return errors


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


_VALIDATORS: dict[str, Any] = {
    "ResearchQuestion": validate_research_question,
    "Hypothesis": validate_hypothesis,
    "Experiment": validate_experiment,
    "Feature": validate_feature,
    "FeatureFamily": validate_feature_family,
    "AlphaCandidate": validate_alpha_candidate,
    "Alpha": validate_alpha,
}


def validate_entity(entity: IKROSEntity) -> list[str]:
    """Validate an entity and return a list of error strings (empty = valid)."""
    fn = _VALIDATORS.get(entity.entity_type)
    if fn is None:
        return _check_base(entity)
    return fn(entity)  # type: ignore[no-any-return]


def assert_valid(entity: IKROSEntity) -> None:
    """Validate and raise ValidationError if any errors are found."""
    errors = validate_entity(entity)
    if errors:
        raise ValidationError(
            f"{entity.entity_type} {entity.ikros_id} failed validation:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
