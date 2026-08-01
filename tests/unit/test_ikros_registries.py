"""Unit tests for IKROS core registries — WP-IMP-0042."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tools.ikros.identifiers import (
    LifecycleError,
    allowed_transitions,
    compute_reproducibility_hash,
    is_valid_ikros_id,
    make_ikros_id,
    validate_transition,
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
    LineageDependencies,
    LineageEvidence,
    LineageExperiments,
    LineageOrigin,
    LineageRecord,
    LineageRetirement,
    LineageSuccessors,
    PromotionStatus,
    ResearchQuestion,
    ResearchStatus,
    Stationarity,
    StrategyType,
)
from tools.ikros.registries.alpha import AlphaRegistry
from tools.ikros.registries.base import RegistryError
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.feature import FeatureRegistry
from tools.ikros.registries.hypothesis import HypothesisRegistry
from tools.ikros.registries.research import ResearchRegistry
from tools.ikros.validation import ValidationError, assert_valid, validate_entity

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _origin(context: str = "test") -> LineageOrigin:
    return LineageOrigin(
        created_by="test-agent",
        created_at="2026-08-02T00:00:00Z",
        creation_context=context,
        motivation="unit-test motivation",
    )


def _lineage(context: str = "test") -> LineageRecord:
    return LineageRecord(origin=_origin(context))


def _confidence() -> ConfidenceVector:
    return ConfidenceVector(statistical=0.6, economic=0.5, data=0.8)


def _rq(ikros_id: str = "IKROS-RQ-20260802-0001") -> ResearchQuestion:
    return ResearchQuestion(
        ikros_id=ikros_id,
        entity_type="ResearchQuestion",
        version="1.0.0",
        lifecycle_state=ResearchStatus.OPEN.value,
        confidence=_confidence(),
        lineage=_lineage("wp42-test"),
        title="Does gold act as an inflation hedge for XAU/USD?",
        instrument="XAU/USD",
        scope="MACRO",
        time_horizon="1D",
        campaign_tag="PHASE-E",
        motivation="Phase E alpha research campaign",
    )


def _hyp(
    ikros_id: str = "IKROS-HYP-20260802-0001",
    rq_id: str = "IKROS-RQ-20260802-0001",
) -> Hypothesis:
    return Hypothesis(
        ikros_id=ikros_id,
        entity_type="Hypothesis",
        version="1.0.0",
        lifecycle_state=HypothesisStatus.PROPOSED.value,
        confidence=_confidence(),
        lineage=LineageRecord(
            origin=_origin("wp42-test"),
            dependencies=LineageDependencies(inputs=[rq_id]),
        ),
        statement="XAU/USD returns are positively correlated with CPI surprises",
        null_hypothesis="H0: No correlation between XAU/USD returns and CPI surprises",
        alternative_hypothesis="H1: Positive correlation exists",
        significance_level=0.05,
        power=0.80,
        prior_confidence=0.30,
        source_rq=rq_id,
    )


def _exp(
    ikros_id: str = "IKROS-EXP-20260802-0001",
    hyp_id: str = "IKROS-HYP-20260802-0001",
) -> Experiment:
    return Experiment(
        ikros_id=ikros_id,
        entity_type="Experiment",
        version="1.0.0",
        lifecycle_state=ExperimentStatus.DESIGNED.value,
        confidence=_confidence(),
        lineage=LineageRecord(
            origin=_origin("wp42-test"),
            dependencies=LineageDependencies(
                inputs=[hyp_id],
                datasets=["IKROS-DSV-20260802-0001"],
                features=["IKROS-FEAT-20260802-0001"],
            ),
        ),
        title="Trend following backtest — Phase E",
        hypotheses=[hyp_id],
        protocol="Walk-forward validation with 756d IS / 252d OOS windows",
        dataset_versions=["IKROS-DSV-20260802-0001"],
        feature_versions=["IKROS-FEAT-20260802-0001"],
        parameters={"fast_window": 20, "slow_window": 120},
        random_seed=42,
    )


def _feat(ikros_id: str = "IKROS-FEAT-20260802-0001") -> Feature:
    return Feature(
        ikros_id=ikros_id,
        entity_type="Feature",
        version="1.0.0",
        lifecycle_state="DRAFT",
        confidence=_confidence(),
        lineage=LineageRecord(
            origin=_origin("wp42-test"),
            dependencies=LineageDependencies(inputs=["close"]),
        ),
        name="sma_ratio_20_120",
        family_id="IKROS-FF-20260802-0001",
        computation="close.rolling(20).mean() / close.rolling(120).mean()",
        inputs=["close"],
        lookback="120 bars",
        normalization="z-score",
        stationarity=Stationarity.STATIONARY.value,
        information_content=0.35,
        stability_score=0.72,
    )


def _cand(
    ikros_id: str = "IKROS-ALPHACAND-20260802-0001",
    hyp_id: str = "IKROS-HYP-20260802-0001",
) -> AlphaCandidate:
    return AlphaCandidate(
        ikros_id=ikros_id,
        entity_type="AlphaCandidate",
        version="1.0.0",
        lifecycle_state=PromotionStatus.CANDIDATE.value,
        confidence=_confidence(),
        lineage=LineageRecord(
            origin=_origin("wp42-test"),
            dependencies=LineageDependencies(inputs=[hyp_id]),
        ),
        name="trend_following_v1",
        strategy_type=StrategyType.TREND.value,
        sharpe_oos=0.45,
        max_drawdown=0.18,
        direction_accuracy=0.52,
        win_rate=0.51,
        promotion_score=0.38,
        implements_hypotheses=[hyp_id],
    )


# ---------------------------------------------------------------------------
# Identifier tests
# ---------------------------------------------------------------------------


class TestIdentifiers:
    def test_make_ikros_id_format(self) -> None:
        id_ = make_ikros_id("ResearchQuestion", seq=1)
        assert id_.startswith("IKROS-RQ-")
        assert id_.endswith("-0001")

    def test_make_ikros_id_hypothesis(self) -> None:
        id_ = make_ikros_id("Hypothesis", seq=42)
        assert "HYP" in id_
        assert id_.endswith("-0042")

    def test_is_valid_true(self) -> None:
        assert is_valid_ikros_id("IKROS-RQ-20260802-0001")
        assert is_valid_ikros_id("IKROS-ALPHACAND-20260802-0001")
        assert is_valid_ikros_id("IKROS-HYP-20260101-9999")

    def test_is_valid_false(self) -> None:
        assert not is_valid_ikros_id("INVALID-RQ-20260802-0001")
        assert not is_valid_ikros_id("IKROS-20260802-0001")
        assert not is_valid_ikros_id("IKROS-RQ-0001")
        assert not is_valid_ikros_id("")

    def test_reproducibility_hash_deterministic(self) -> None:
        data = {"seed": 42, "window": 20, "dataset": "xau_h1"}
        h1 = compute_reproducibility_hash(data)
        h2 = compute_reproducibility_hash(data)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_reproducibility_hash_differs_on_change(self) -> None:
        h1 = compute_reproducibility_hash({"seed": 42})
        h2 = compute_reproducibility_hash({"seed": 43})
        assert h1 != h2


# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_valid_research_transition(self) -> None:
        validate_transition("ResearchQuestion", "OPEN", "ACTIVE")  # should not raise

    def test_invalid_research_transition(self) -> None:
        with pytest.raises(LifecycleError):
            validate_transition("ResearchQuestion", "OPEN", "ANSWERED")

    def test_hypothesis_full_path(self) -> None:
        states = [
            ("PROPOSED", "UNDER_REVIEW"),
            ("UNDER_REVIEW", "APPROVED_FOR_TESTING"),
            ("APPROVED_FOR_TESTING", "TESTING"),
            ("TESTING", "SUPPORTED"),
        ]
        for current, new in states:
            validate_transition("Hypothesis", current, new)

    def test_hypothesis_refuted_path(self) -> None:
        validate_transition("Hypothesis", "TESTING", "REFUTED")

    def test_experiment_designed_to_approved(self) -> None:
        validate_transition("Experiment", "DESIGNED", "APPROVED")

    def test_experiment_complete_to_reviewed(self) -> None:
        validate_transition("Experiment", "COMPLETE", "REVIEWED")

    def test_no_transition_from_terminal(self) -> None:
        with pytest.raises(LifecycleError):
            validate_transition("ResearchQuestion", "RETIRED", "OPEN")

    def test_allowed_transitions_research(self) -> None:
        allowed = allowed_transitions("ResearchQuestion", "OPEN")
        assert "ACTIVE" in allowed

    def test_allowed_transitions_empty_terminal(self) -> None:
        assert allowed_transitions("ResearchQuestion", "RETIRED") == []


# ---------------------------------------------------------------------------
# Confidence vector tests
# ---------------------------------------------------------------------------


class TestConfidenceVector:
    def test_overall_all_zero(self) -> None:
        cv = ConfidenceVector()
        assert cv.overall() == 0.0

    def test_overall_single_dim(self) -> None:
        cv = ConfidenceVector(statistical=0.64)
        assert 0.0 < cv.overall() <= 0.95

    def test_overall_capped_at_095(self) -> None:
        cv = ConfidenceVector(
            statistical=1.0, economic=1.0, data=1.0, model=1.0,
            validation=1.0, replication=1.0, operational=1.0,
        )
        assert cv.overall() <= 0.95

    def test_serialization_roundtrip(self) -> None:
        cv = ConfidenceVector(statistical=0.7, economic=0.5, data=0.8)
        d = cv.to_dict()
        cv2 = ConfidenceVector.from_dict(d)
        assert cv2.statistical == cv.statistical
        assert cv2.economic == cv.economic

    def test_overall_in_dict(self) -> None:
        cv = ConfidenceVector(statistical=0.5)
        d = cv.to_dict()
        assert "overall" in d
        assert 0.0 <= d["overall"] <= 1.0


# ---------------------------------------------------------------------------
# Lineage record tests
# ---------------------------------------------------------------------------


class TestLineageRecord:
    def test_serialization_roundtrip(self) -> None:
        lr = LineageRecord(
            origin=_origin("test"),
            dependencies=LineageDependencies(inputs=["A", "B"], datasets=["IKROS-DS-*"]),
            experiments=LineageExperiments(tested_in=["IKROS-EXP-001"]),
            evidence=LineageEvidence(ers_records=["05-work-packages/WP-X/evidence/EXEC-001.yaml"]),
            successors=LineageSuccessors(refined_by=None),
            retirement=LineageRetirement(),
        )
        d = lr.to_dict()
        lr2 = LineageRecord.from_dict(d)
        assert lr2.origin.created_by == lr.origin.created_by
        assert lr2.dependencies.inputs == lr.dependencies.inputs
        assert lr2.experiments.tested_in == lr.experiments.tested_in


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidation:
    def test_valid_rq(self) -> None:
        errors = validate_entity(_rq())
        assert errors == []

    def test_invalid_rq_no_title(self) -> None:
        rq = _rq()
        rq.title = ""
        errors = validate_entity(rq)
        assert any("title" in e for e in errors)

    def test_invalid_rq_bad_ikros_id(self) -> None:
        rq = _rq()
        rq.ikros_id = "BAD-ID"
        errors = validate_entity(rq)
        assert any("ikros_id" in e for e in errors)

    def test_valid_hypothesis(self) -> None:
        errors = validate_entity(_hyp())
        assert errors == []

    def test_hypothesis_missing_null(self) -> None:
        hyp = _hyp()
        hyp.null_hypothesis = ""
        errors = validate_entity(hyp)
        assert any("null_hypothesis" in e for e in errors)

    def test_hypothesis_supported_requires_validation(self) -> None:
        hyp = _hyp()
        hyp.lifecycle_state = HypothesisStatus.SUPPORTED.value
        errors = validate_entity(hyp)
        assert any("validated_by" in e for e in errors)

    def test_valid_experiment(self) -> None:
        errors = validate_entity(_exp())
        assert errors == []

    def test_experiment_complete_requires_hash(self) -> None:
        exp = _exp()
        exp.lifecycle_state = ExperimentStatus.COMPLETE.value
        errors = validate_entity(exp)
        assert any("reproducibility_hash" in e for e in errors)

    def test_valid_feature(self) -> None:
        errors = validate_entity(_feat())
        assert errors == []

    def test_valid_candidate(self) -> None:
        errors = validate_entity(_cand())
        assert errors == []

    def test_rejected_candidate_requires_reasons(self) -> None:
        cand = _cand()
        cand.promotion_status = PromotionStatus.REJECTED.value
        errors = validate_entity(cand)
        assert any("rejection_reasons" in e for e in errors)

    def test_assert_valid_raises(self) -> None:
        rq = _rq()
        rq.title = ""
        with pytest.raises(ValidationError):
            assert_valid(rq)


# ---------------------------------------------------------------------------
# Research Registry tests
# ---------------------------------------------------------------------------


class TestResearchRegistry:
    def test_register_and_get(self) -> None:
        reg = ResearchRegistry()
        rq = _rq()
        reg.register(rq)
        assert reg.get("IKROS-RQ-20260802-0001").title == rq.title

    def test_duplicate_raises(self) -> None:
        reg = ResearchRegistry()
        reg.register(_rq())
        with pytest.raises(RegistryError):
            reg.register(_rq())

    def test_invalid_entity_raises(self) -> None:
        reg = ResearchRegistry()
        rq = _rq()
        rq.title = ""
        with pytest.raises(ValidationError):
            reg.register(rq)

    def test_open_questions(self) -> None:
        reg = ResearchRegistry()
        reg.register(_rq())
        reg.register(_rq("IKROS-RQ-20260802-0002"))
        assert len(reg.open_questions()) == 2

    def test_transition_to_active(self) -> None:
        reg = ResearchRegistry()
        reg.register(_rq())
        updated = reg.transition("IKROS-RQ-20260802-0001", "ACTIVE")
        assert updated.lifecycle_state == "ACTIVE"
        assert reg.get("IKROS-RQ-20260802-0001").lifecycle_state == "ACTIVE"

    def test_invalid_transition_raises(self) -> None:
        reg = ResearchRegistry()
        reg.register(_rq())
        with pytest.raises(LifecycleError):
            reg.transition("IKROS-RQ-20260802-0001", "RETIRED")

    def test_by_instrument(self) -> None:
        reg = ResearchRegistry()
        reg.register(_rq())
        results = reg.by_instrument("XAU/USD")
        assert len(results) == 1

    def test_by_campaign(self) -> None:
        reg = ResearchRegistry()
        reg.register(_rq())
        results = reg.by_campaign("PHASE-E")
        assert len(results) == 1

    def test_link_hypothesis(self) -> None:
        reg = ResearchRegistry()
        reg.register(_rq())
        updated = reg.link_hypothesis("IKROS-RQ-20260802-0001", "IKROS-HYP-20260802-0001")
        assert "IKROS-HYP-20260802-0001" in updated.linked_hypotheses

    def test_count(self) -> None:
        reg = ResearchRegistry()
        reg.register(_rq())
        assert reg.count() == 1

    def test_next_id(self) -> None:
        reg = ResearchRegistry()
        reg.register(_rq())
        next_id = reg.next_id()
        assert next_id != "IKROS-RQ-20260802-0001"

    def test_persistence_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            reg = ResearchRegistry(base)
            reg.register(_rq())
            # Re-load from disk
            reg2 = ResearchRegistry(base)
            assert reg2.exists("IKROS-RQ-20260802-0001")
            assert reg2.get("IKROS-RQ-20260802-0001").title == (
                "Does gold act as an inflation hedge for XAU/USD?"
            )

    def test_version_history_on_update(self) -> None:
        reg = ResearchRegistry()
        reg.register(_rq())
        reg.update("IKROS-RQ-20260802-0001", {"campaign_tag": "PHASE-F"})
        updated = reg.get("IKROS-RQ-20260802-0001")
        assert len(updated.version_history) == 1
        assert updated.campaign_tag == "PHASE-F"


# ---------------------------------------------------------------------------
# Hypothesis Registry tests
# ---------------------------------------------------------------------------


class TestHypothesisRegistry:
    def test_register_and_get(self) -> None:
        reg = HypothesisRegistry()
        hyp = _hyp()
        reg.register(hyp)
        assert reg.get("IKROS-HYP-20260802-0001").statement == hyp.statement

    def test_supported_query(self) -> None:
        reg = HypothesisRegistry()
        hyp = _hyp()
        hyp.lifecycle_state = HypothesisStatus.SUPPORTED.value
        hyp.lineage.experiments.validated_by.append("IKROS-VAL-20260802-0001")
        hyp.lineage.experiments.tested_in.append("IKROS-EXP-20260802-0001")
        reg.register(hyp)
        assert len(reg.supported()) == 1

    def test_refuted_query(self) -> None:
        reg = HypothesisRegistry()
        hyp = _hyp()
        hyp.lifecycle_state = HypothesisStatus.REFUTED.value
        hyp.lineage.experiments.validated_by.append("IKROS-VAL-20260802-0001")
        hyp.lineage.experiments.tested_in.append("IKROS-EXP-20260802-0001")
        reg.register(hyp)
        assert len(reg.refuted()) == 1

    def test_add_experiment(self) -> None:
        reg = HypothesisRegistry()
        reg.register(_hyp())
        updated = reg.add_experiment("IKROS-HYP-20260802-0001", "IKROS-EXP-20260802-0001")
        assert "IKROS-EXP-20260802-0001" in updated.experiments
        assert "IKROS-EXP-20260802-0001" in updated.lineage.experiments.tested_in

    def test_update_posterior(self) -> None:
        reg = HypothesisRegistry()
        reg.register(_hyp())
        updated = reg.update_posterior_confidence("IKROS-HYP-20260802-0001", 0.75)
        assert updated.posterior_confidence == 0.75

    def test_invalid_posterior_raises(self) -> None:
        reg = HypothesisRegistry()
        reg.register(_hyp())
        with pytest.raises(ValueError):
            reg.update_posterior_confidence("IKROS-HYP-20260802-0001", 1.5)

    def test_by_source_rq(self) -> None:
        reg = HypothesisRegistry()
        reg.register(_hyp())
        results = reg.by_source_rq("IKROS-RQ-20260802-0001")
        assert len(results) == 1

    def test_persistence_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            reg = HypothesisRegistry(base)
            reg.register(_hyp())
            reg2 = HypothesisRegistry(base)
            assert reg2.exists("IKROS-HYP-20260802-0001")


# ---------------------------------------------------------------------------
# Experiment Registry tests
# ---------------------------------------------------------------------------


class TestExperimentRegistry:
    def test_register_and_get(self) -> None:
        reg = ExperimentRegistry()
        exp = _exp()
        reg.register(exp)
        assert reg.get("IKROS-EXP-20260802-0001").title == exp.title

    def test_by_hypothesis(self) -> None:
        reg = ExperimentRegistry()
        reg.register(_exp())
        results = reg.by_hypothesis("IKROS-HYP-20260802-0001")
        assert len(results) == 1

    def test_by_reproducibility_hash(self) -> None:
        reg = ExperimentRegistry()
        exp = _exp()
        h = compute_reproducibility_hash({"seed": 42})
        reg.register(exp)
        reg.update("IKROS-EXP-20260802-0001", {"reproducibility_hash": h})
        found = reg.by_reproducibility_hash(h)
        assert found is not None
        assert found.ikros_id == "IKROS-EXP-20260802-0001"

    def test_not_found_returns_none(self) -> None:
        reg = ExperimentRegistry()
        assert reg.by_reproducibility_hash("nonexistent") is None

    def test_add_validation(self) -> None:
        reg = ExperimentRegistry()
        reg.register(_exp())
        updated = reg.add_validation("IKROS-EXP-20260802-0001", "IKROS-VAL-20260802-0001")
        assert "IKROS-VAL-20260802-0001" in updated.validations_produced

    def test_add_failure(self) -> None:
        reg = ExperimentRegistry()
        reg.register(_exp())
        updated = reg.add_failure("IKROS-EXP-20260802-0001", "IKROS-FAIL-20260802-0001")
        assert "IKROS-FAIL-20260802-0001" in updated.failures_produced

    def test_reproducible_inputs(self) -> None:
        reg = ExperimentRegistry()
        reg.register(_exp())
        inputs = reg.get_reproducible_inputs("IKROS-EXP-20260802-0001")
        assert "random_seed" in inputs
        assert "dataset_versions" in inputs
        assert inputs["random_seed"] == 42

    def test_transition_complete_requires_hash(self) -> None:
        reg = ExperimentRegistry()
        exp = _exp()
        reg.register(exp)
        reg.transition("IKROS-EXP-20260802-0001", "APPROVED")
        reg.transition("IKROS-EXP-20260802-0001", "RUNNING")
        # Complete without reproducibility_hash should fail validation on transition
        with pytest.raises(ValidationError):
            reg.transition("IKROS-EXP-20260802-0001", "COMPLETE")


# ---------------------------------------------------------------------------
# Feature Registry tests
# ---------------------------------------------------------------------------


class TestFeatureRegistry:
    def _make_family(self) -> FeatureFamily:
        return FeatureFamily(
            ikros_id="IKROS-FF-20260802-0001",
            entity_type="FeatureFamily",
            version="1.0.0",
            lifecycle_state="ACTIVE",
            confidence=_confidence(),
            lineage=_lineage("wp42-test"),
            name="TREND",
            description="Trend-following signal features",
        )

    def test_register_feature(self) -> None:
        reg = FeatureRegistry()
        reg.register(_feat())
        assert reg.exists("IKROS-FEAT-20260802-0001")

    def test_register_family(self) -> None:
        reg = FeatureRegistry()
        reg.register_family(self._make_family())
        assert reg.family_count() == 1

    def test_duplicate_family_raises(self) -> None:
        reg = FeatureRegistry()
        reg.register_family(self._make_family())
        with pytest.raises(RegistryError):
            reg.register_family(self._make_family())

    def test_by_family(self) -> None:
        reg = FeatureRegistry()
        reg.register(_feat())
        results = reg.by_family("IKROS-FF-20260802-0001")
        assert len(results) == 1

    def test_high_information(self) -> None:
        reg = FeatureRegistry()
        reg.register(_feat())
        assert len(reg.high_information(threshold=0.30)) == 1
        assert len(reg.high_information(threshold=0.90)) == 0

    def test_high_stability(self) -> None:
        reg = FeatureRegistry()
        reg.register(_feat())
        assert len(reg.high_stability(threshold=0.70)) == 1
        assert len(reg.high_stability(threshold=0.90)) == 0

    def test_add_experiment_usage(self) -> None:
        reg = FeatureRegistry()
        reg.register(_feat())
        updated = reg.add_experiment_usage("IKROS-FEAT-20260802-0001", "IKROS-EXP-20260802-0001")
        assert "IKROS-EXP-20260802-0001" in updated.used_in_experiments

    def test_supersede(self) -> None:
        reg = FeatureRegistry()
        reg.register(_feat("IKROS-FEAT-20260802-0001"))
        feat2 = _feat("IKROS-FEAT-20260802-0002")
        feat2.name = "sma_ratio_20_200"
        reg.register(feat2)
        updated = reg.supersede("IKROS-FEAT-20260802-0001", "IKROS-FEAT-20260802-0002")
        assert updated.superseded_by == "IKROS-FEAT-20260802-0002"

    def test_supersede_unknown_raises(self) -> None:
        reg = FeatureRegistry()
        reg.register(_feat())
        with pytest.raises(RegistryError):
            reg.supersede("IKROS-FEAT-20260802-0001", "IKROS-FEAT-99999999-0099")

    def test_persistence_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            reg = FeatureRegistry(base)
            reg.register_family(self._make_family())
            reg.register(_feat())
            reg2 = FeatureRegistry(base)
            assert reg2.exists("IKROS-FEAT-20260802-0001")
            assert reg2.family_count() == 1


# ---------------------------------------------------------------------------
# Alpha Registry tests
# ---------------------------------------------------------------------------


class TestAlphaRegistry:
    def test_register_candidate(self) -> None:
        reg = AlphaRegistry()
        reg.register(_cand())
        assert reg.exists("IKROS-ALPHACAND-20260802-0001")

    def test_candidates_query(self) -> None:
        reg = AlphaRegistry()
        reg.register(_cand())
        assert len(reg.candidates()) == 1

    def test_reject_candidate(self) -> None:
        reg = AlphaRegistry()
        reg.register(_cand())
        updated = reg.reject(
            "IKROS-ALPHACAND-20260802-0001",
            reasons=["OOS Sharpe 0.45 < 1.0 threshold", "WF consistency < 0.60"],
        )
        assert updated.promotion_status == PromotionStatus.REJECTED.value
        assert len(updated.rejection_reasons) == 2

    def test_reject_requires_reasons(self) -> None:
        reg = AlphaRegistry()
        reg.register(_cand())
        with pytest.raises(RegistryError):
            reg.reject("IKROS-ALPHACAND-20260802-0001", reasons=[])

    def test_rejected_query(self) -> None:
        reg = AlphaRegistry()
        reg.register(_cand())
        reg.reject(
            "IKROS-ALPHACAND-20260802-0001",
            reasons=["Below threshold"],
        )
        assert len(reg.rejected()) == 1

    def test_promotion_eligible_none(self) -> None:
        reg = AlphaRegistry()
        reg.register(_cand())  # Sharpe 0.45 < 1.0
        assert len(reg.promotion_eligible()) == 0

    def test_promotion_eligible_above_threshold(self) -> None:
        reg = AlphaRegistry()
        cand = _cand()
        cand.sharpe_oos = 1.2
        cand.direction_accuracy = 0.55
        cand.max_drawdown = 0.15
        reg.register(cand)
        assert len(reg.promotion_eligible()) == 1

    def test_promote_candidate(self) -> None:
        reg = AlphaRegistry()
        cand = _cand()
        cand.sharpe_oos = 1.2
        cand.direction_accuracy = 0.55
        reg.register(cand)
        alpha = Alpha(
            ikros_id="IKROS-ALPHA-20260802-0001",
            entity_type="Alpha",
            version="1.0.0",
            lifecycle_state=PromotionStatus.PROMOTED.value,
            confidence=_confidence(),
            lineage=LineageRecord(
                origin=_origin("wp42-test"),
                evidence=LineageEvidence(
                    ers_records=["05-work-packages/WP-IMP-0099/evidence/EXEC-099.yaml"]
                ),
            ),
            promoted_from="IKROS-ALPHACAND-20260802-0001",
            promotion_date="2026-08-02",
            promotion_evidence="05-work-packages/WP-IMP-0099/evidence/EXEC-099.yaml",
            paper_trading_status=AlphaPaperStatus.NOT_STARTED.value,
        )
        alpha_id = reg.promote("IKROS-ALPHACAND-20260802-0001", alpha)
        assert alpha_id == "IKROS-ALPHA-20260802-0001"
        assert reg.alpha_count() == 1
        assert (
            reg.get("IKROS-ALPHACAND-20260802-0001").promotion_status
            == PromotionStatus.PROMOTED.value
        )

    def test_promote_without_ers_raises(self) -> None:
        reg = AlphaRegistry()
        reg.register(_cand())
        alpha = Alpha(
            ikros_id="IKROS-ALPHA-20260802-0001",
            entity_type="Alpha",
            version="1.0.0",
            lifecycle_state=PromotionStatus.PROMOTED.value,
            confidence=_confidence(),
            lineage=_lineage("wp42-test"),  # No ERS records
            promoted_from="IKROS-ALPHACAND-20260802-0001",
            promotion_date="2026-08-02",
            promotion_evidence="",
        )
        with pytest.raises(RegistryError):
            reg.promote("IKROS-ALPHACAND-20260802-0001", alpha)

    def test_by_strategy_type(self) -> None:
        reg = AlphaRegistry()
        reg.register(_cand())
        results = reg.by_strategy_type(StrategyType.TREND.value)
        assert len(results) == 1

    def test_persistence_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            reg = AlphaRegistry(base)
            reg.register(_cand())
            reg2 = AlphaRegistry(base)
            assert reg2.exists("IKROS-ALPHACAND-20260802-0001")

    def test_retire(self) -> None:
        reg = AlphaRegistry()
        reg.register(_cand())
        reg.retire("IKROS-ALPHACAND-20260802-0001", reason="Superseded by improved strategy")
        updated = reg.get("IKROS-ALPHACAND-20260802-0001")
        assert updated.lineage.retirement.retirement_reason is not None
