"""Tests for Discovery Cycle 3 Phase 4 Adaptive Institutional Alpha Validation Program — Batch 1."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc3_phase4_validation_execution import (
    run_dc3_phase4_validation_campaign,
)
from tools.alpha_research.institutional_alpha_validation_execution import (
    VALIDATION_OUTCOMES,
    emit_dc3_phase4_validation_reports,
    prepare_dc3_phase4_validation_artifacts,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc3_phase4_validation_artifacts()


def test_phase4_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DISCOVERY_CYCLE_3_PHASE_4"
    assert analysis["batch"] == "BATCH-001"
    assert int(analysis["batch_mechanisms_validated"]) == 2
    assert analysis["promotion_this_phase"] is False


def test_phase4_validation_results(analysis: dict[str, Any]) -> None:
    results = analysis["validation_results"]
    assert len(results) == 2
    alpha_ids = {r["alpha_id"] for r in results}
    assert "IKROS-ALPHA-DC3-20260802-0006" in alpha_ids
    assert "IKROS-ALPHA-DC3-20260802-0009" in alpha_ids
    for r in results:
        outcome = r["outcome"]["outcome"]
        assert outcome in VALIDATION_OUTCOMES
        assert 0.0 <= float(r["outcome"]["confidence_posterior"]) <= 1.0
        assert len(r["dimension_scores"]) == 20
        assert len(r["method_results"]) == 17


def test_phase4_dimension_aggregates(analysis: dict[str, Any]) -> None:
    for r in analysis["validation_results"]:
        agg = r["dimension_aggregate"]
        assert 0.0 <= float(agg["pass_rate"]) <= 1.0
        assert int(agg["dimensions_total"]) == 20


def test_phase4_adaptive_signals(analysis: dict[str, Any]) -> None:
    for r in analysis["validation_results"]:
        signals = r["adaptive_signals"]
        assert "should_confidence_increase" in signals
        assert "should_confidence_decrease" in signals
        assert "recommended_next_action" in signals
        assert isinstance(signals["recommended_next_action"], str)


def test_phase4_adaptive_queue(analysis: dict[str, Any]) -> None:
    queue = analysis["adaptive_research_queue"]
    assert len(queue) == 12
    validated = [q for q in queue if q["status"] == "VALIDATED"]
    pending = [q for q in queue if q["status"] == "PENDING"]
    assert len(validated) == 2
    assert len(pending) == 10


def test_phase4_family_ranking(analysis: dict[str, Any]) -> None:
    ranking = analysis["family_ranking"]
    assert len(ranking) == 7
    validated_fams = [f for f in ranking if f["mechanisms_validated"] > 0]
    assert len(validated_fams) == 2
    for f in validated_fams:
        assert f["confidence_updated"] is not None


def test_phase4_campaign_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src_dc3 = Path("11-research/discovery-cycle-3/institutional-alpha-discovery-program")
        dst_dc3 = root / "11-research" / "discovery-cycle-3" / "institutional-alpha-discovery-program"
        dst_dc3.mkdir(parents=True, exist_ok=True)
        for f in src_dc3.glob("*.json"):
            shutil.copy(f, dst_dc3 / f.name)
        src_phase3 = Path("11-research/discovery-cycle-3/phase-3-institutional-alpha-taxonomy")
        dst_phase3 = root / "11-research" / "discovery-cycle-3" / "phase-3-institutional-alpha-taxonomy"
        dst_phase3.mkdir(parents=True, exist_ok=True)
        for f in src_phase3.glob("*.json"):
            shutil.copy(f, dst_phase3 / f.name)
        ikros_src = Path("data/ikros")
        shutil.copytree(str(ikros_src), str(root / "data" / "ikros"))
        result = run_dc3_phase4_validation_campaign(root)
        assert int(result["mechanisms_validated"]) == 2
        assert int(result["mechanisms_pending"]) == 10
        assert result["promotion_this_phase"] is False
        assert result["batch_2_requires_arb_approval"] is True
        assert len(result["outcomes"]) == 2
