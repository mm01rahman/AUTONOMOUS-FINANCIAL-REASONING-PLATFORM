"""Unit tests for DC2 Research Program A — Cross-Asset Transition Ecology."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def test_dc2_program_a_analysis_runs(tmp_path: Path) -> None:
    """DC2 Program A analysis completes and returns required keys."""
    from tools.alpha_research.cross_asset_ecology import prepare_dc2_program_a_artifacts

    result = prepare_dc2_program_a_artifacts(output_dir=tmp_path)

    assert "analysis" in result
    assert "paths" in result
    analysis = result["analysis"]
    assert "program" in analysis
    assert "theme1_lead_lag" in analysis
    assert "theme2_information_flow" in analysis
    assert "theme3_transition_ecology" in analysis
    assert "theme4_synchronization" in analysis
    assert "theme5_adaptive_behavior" in analysis
    assert "cross_market_influence_matrix" in analysis
    assert "arb_recommendation" in analysis


def test_dc2_program_a_has_influence_matrix(tmp_path: Path) -> None:
    """Influence matrix is non-empty and all entries have required fields."""
    from tools.alpha_research.cross_asset_ecology import prepare_dc2_program_a_artifacts

    result = prepare_dc2_program_a_artifacts(output_dir=tmp_path)
    rows = result["analysis"]["cross_market_influence_matrix"]["influence_rows"]
    assert len(rows) > 0
    for row in rows:
        assert "signal" in row
        assert "composite_influence_score" in row
        assert "peak_lag_days" in row


def test_dc2_program_a_transition_ecology(tmp_path: Path) -> None:
    """Transition ecology identifies at least some regime transitions."""
    from tools.alpha_research.cross_asset_ecology import prepare_dc2_program_a_artifacts

    result = prepare_dc2_program_a_artifacts(output_dir=tmp_path)
    transition = result["analysis"]["theme3_transition_ecology"]
    assert int(transition["total_transitions"]) > 0
    assert len(transition.get("dominant_pre_transition_signals", [])) > 0


def test_dc2_program_a_arb_recommendation(tmp_path: Path) -> None:
    """ARB recommendation is present with required governance fields."""
    from tools.alpha_research.cross_asset_ecology import prepare_dc2_program_a_artifacts

    result = prepare_dc2_program_a_artifacts(output_dir=tmp_path)
    arb = result["analysis"]["arb_recommendation"]
    assert "dominant_transition_drivers" in arb
    assert "strongest_cross_market_relationships" in arb
    assert "stop_confirmation" in arb
    # Must confirm no strategies were built
    assert "no strategies built" in arb["stop_confirmation"].lower()


def test_dc2_program_a_data_gaps_documented(tmp_path: Path) -> None:
    """All unavailable HIGH-severity markets are documented."""
    from tools.alpha_research.cross_asset_ecology import (
        UNAVAILABLE_MARKETS,
        prepare_dc2_program_a_artifacts,
    )

    result = prepare_dc2_program_a_artifacts(output_dir=tmp_path)
    gaps = result["analysis"]["data_availability"]["unavailable_markets"]
    assert len(gaps) == len(UNAVAILABLE_MARKETS)
    high_severity = [g for g in gaps if g["gap_severity"] == "HIGH"]
    assert len(high_severity) >= 6  # VIX, S&P, Crude, EUR/USD, USD/JPY, Bond Futures, ETF, COMEX


def test_dc2_program_a_reports_emitted(tmp_path: Path) -> None:
    """All 11 governed deliverable reports are written."""
    from tools.alpha_research.cross_asset_ecology import (
        emit_dc2_program_a_reports,
        prepare_dc2_program_a_artifacts,
    )

    result = prepare_dc2_program_a_artifacts(output_dir=tmp_path)
    paths = emit_dc2_program_a_reports(
        output_dir=tmp_path,
        analysis=result["analysis"],
        campaign_result={"lifecycle_status": "COMPLETE"},
    )
    assert len(paths) >= 10
    for path_str in paths.values():
        assert Path(path_str).exists()


def test_dc2_program_a_campaign_completes() -> None:
    """Full DC2 Program A campaign completes with lifecycle_status COMPLETE."""
    from tools.alpha_research.dc2 import run_dc2_program_a_campaign

    repo_root = _repo_root()
    result = run_dc2_program_a_campaign(repo_root)

    assert result["lifecycle_status"] == "COMPLETE"
    assert "program_summary" in result
    summary = result["program_summary"]
    assert int(summary["rows_analyzed"]) > 0
    assert len(summary["dominant_transition_drivers"]) > 0
    assert len(summary["strongest_relationships"]) > 0


def test_dc2_program_a_information_flow(tmp_path: Path) -> None:
    """Information flow analysis returns transfer entropy and Granger results."""
    from tools.alpha_research.cross_asset_ecology import prepare_dc2_program_a_artifacts

    result = prepare_dc2_program_a_artifacts(output_dir=tmp_path)
    info_flow = result["analysis"]["theme2_information_flow"]
    assert "transfer_entropy_proxy" in info_flow
    assert "granger_causality_proxy" in info_flow
    assert "regime_conditioned_mi" in info_flow
    te = info_flow["transfer_entropy_proxy"]
    assert len(te) > 0
    for _sig, data in te.items():
        assert "peak_lag_days" in data
        assert "peak_mi" in data


def test_dc2_program_a_synchronization(tmp_path: Path) -> None:
    """Synchronization analysis covers normal and stress periods."""
    from tools.alpha_research.cross_asset_ecology import prepare_dc2_program_a_artifacts

    result = prepare_dc2_program_a_artifacts(output_dir=tmp_path)
    sync = result["analysis"]["theme4_synchronization"]
    periods = sync["synchronization_by_period"]
    assert "normal" in periods
    assert "stress" in periods
    assert "geopolitical" in periods
