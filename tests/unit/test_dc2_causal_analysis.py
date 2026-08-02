"""Tests for DC2 Program A Phase 2 — Cross-Asset Causal Transition Analysis."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tools.alpha_research.causal_analysis import (
    GRANGER_LAGS,
    MACRO_MEDIATORS,
    emit_dc2_phase2_reports,
    prepare_dc2_phase2_artifacts,
)
from tools.alpha_research.dc2_phase2 import run_dc2_phase2_campaign


@pytest.fixture(scope="module")
def analysis() -> dict:
    return prepare_dc2_phase2_artifacts()


def test_dc2_phase2_analysis_runs(analysis: dict) -> None:
    """Phase 2 analysis produces a well-formed result dict."""
    assert "theme1_conditional_causality" in analysis
    assert "theme2_lag_causality" in analysis
    assert "theme3_macro_mediation" in analysis
    assert "theme4_causal_stability" in analysis
    assert "causal_conclusions" in analysis
    assert "arb_summary" in analysis


def test_dc2_phase2_conditional_causality(analysis: dict) -> None:
    """Theme 1: each signal has regime-conditioned Granger results."""
    theme1 = analysis["theme1_conditional_causality"]
    assert len(theme1) > 0
    for sig_name, info in theme1.items():
        assert "overall" in info, f"{sig_name} missing overall"
        assert "by_regime" in info, f"{sig_name} missing by_regime"
        assert "significance" in info["overall"], f"{sig_name} missing significance"
        assert isinstance(info.get("causal_regimes"), list)


def test_dc2_phase2_lag_causality(analysis: dict) -> None:
    """Theme 2: lag profile covers all governed lags for each signal."""
    theme2 = analysis["theme2_lag_causality"]
    assert len(theme2) > 0
    for sig_name, info in theme2.items():
        lag_profile = info.get("lag_profile", {})
        for lag in GRANGER_LAGS:
            assert str(lag) in lag_profile, f"{sig_name} missing lag {lag}"
        assert info.get("dominant_lag") is not None
        assert info.get("horizon") in ("immediate", "short", "medium", "long")
        assert info.get("persistence") in ("persistent", "transient")


def test_dc2_phase2_macro_mediation(analysis: dict) -> None:
    """Theme 3: macro mediation analysis covers all non-mediator signals."""
    theme3 = analysis["theme3_macro_mediation"]
    assert len(theme3) > 0
    for sig_name, info in theme3.items():
        assert "direct_correlation" in info
        assert "mediation_by_factor" in info
        assert "interpretation" in info
        for med_name, med_info in info["mediation_by_factor"].items():
            assert med_name in MACRO_MEDIATORS
            assert med_info["mediation_classification"] in ("FULL_MEDIATION", "PARTIAL_MEDIATION", "DIRECT_EFFECT")


def test_dc2_phase2_causal_stability(analysis: dict) -> None:
    """Theme 4: stability analysis produces consistency assessment."""
    theme4 = analysis["theme4_causal_stability"]
    assert len(theme4) > 0
    for sig_name, info in theme4.items():
        assert "stability_score" in info
        assert "consistency" in info
        assert info["consistency"] in ("STABLE", "MODERATE", "UNSTABLE", "INSUFFICIENT_DATA")
        assert isinstance(info.get("rolling_f_proxy"), list)


def test_dc2_phase2_causal_conclusions(analysis: dict) -> None:
    """Synthesis: each signal gets a causal classification and ARB recommendation."""
    conclusions = analysis["causal_conclusions"]
    assert len(conclusions) > 0
    valid_classifications = {
        "STRONG_CAUSAL_CANDIDATE",
        "MODERATE_CAUSAL_CANDIDATE",
        "WEAK_CAUSAL_CANDIDATE",
        "NO_CAUSAL_EVIDENCE",
    }
    valid_arb = {
        "PROMOTE_TO_INSTITUTIONAL_KNOWLEDGE",
        "RETAIN_FOR_VALIDATION",
        "DEFER_PENDING_MORE_DATA",
        "REJECT",
    }
    for sig_name, info in conclusions.items():
        assert info["classification"] in valid_classifications, f"{sig_name}: bad classification"
        assert info["arb_recommendation"] in valid_arb, f"{sig_name}: bad ARB rec"
        assert isinstance(info.get("evidence"), list)
        assert isinstance(info.get("contradictions"), list)


def test_dc2_phase2_causal_graph(analysis: dict) -> None:
    """Causal graph has nodes and edges."""
    graph = analysis["causal_graph"]
    assert "nodes" in graph
    assert "edges" in graph
    assert len(graph["nodes"]) > 0
    # All edges must reference known nodes
    for edge in graph["edges"]:
        assert "→" in edge


def test_dc2_phase2_arb_summary(analysis: dict) -> None:
    """ARB summary partitions all signals into recommendation buckets."""
    arb = analysis["arb_summary"]
    assert "promote_to_institutional_knowledge" in arb
    assert "retain_for_validation" in arb
    assert "defer_pending_data" in arb
    assert "reject" in arb
    assert "primary_finding" in arb
    # All signals accounted for
    total = (
        len(arb["promote_to_institutional_knowledge"])
        + len(arb["retain_for_validation"])
        + len(arb["defer_pending_data"])
        + len(arb["reject"])
    )
    assert total == len(analysis["causal_conclusions"])


def test_dc2_phase2_reports_emitted(analysis: dict) -> None:
    """All nine Phase 2 deliverable reports are written."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        report_paths = emit_dc2_phase2_reports(analysis, repo_root=root)
    assert "causal_atlas" in report_paths
    assert "causal_graph" in report_paths
    assert "regime_causal_matrix" in report_paths
    assert "lag_analysis" in report_paths
    assert "macro_mediation" in report_paths
    assert "causal_stability" in report_paths
    assert "contradiction_report" in report_paths
    assert "confidence_report" in report_paths
    assert "research_recommendations" in report_paths


def test_dc2_phase2_campaign_completes() -> None:
    """End-to-end IKROS campaign completes without raising."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = run_dc2_phase2_campaign(root)
    assert "campaign_id" in result
    assert "analysis_summary" in result
    assert "report_paths" in result
    assert result["analysis_summary"]["primary_finding"]
