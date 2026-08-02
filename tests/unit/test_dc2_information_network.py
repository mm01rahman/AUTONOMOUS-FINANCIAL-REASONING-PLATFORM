"""Tests for DC2 Program A Phase 3 - Institutional Cross-Asset Information Network."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.cross_asset_ecology import REGIME_ORDER
from tools.alpha_research.dc2_phase3 import run_dc2_phase3_campaign
from tools.alpha_research.information_network import (
    emit_dc2_phase3_reports,
    prepare_dc2_phase3_artifacts,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc2_phase3_artifacts()


def test_dc2_phase3_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DC2_PROGRAM_A_PHASE3"
    assert "overall_network" in analysis
    assert "centrality_analysis" in analysis
    assert "network_stability_analysis" in analysis
    assert "arb_recommendation" in analysis


def test_dc2_phase3_dynamic_network_graph(analysis: dict[str, Any]) -> None:
    network = analysis["overall_network"]
    assert len(network["nodes"]) > 0
    assert len(network["edges"]) > 0
    assert 0.0 <= float(network["density"]) <= 1.0


def test_dc2_phase3_temporal_influence_network(analysis: dict[str, Any]) -> None:
    temporal = analysis["temporal_influence_network"]
    assert len(temporal) > 0
    for item in temporal[:10]:
        assert "edge" in item
        assert "best_lag" in item
        assert item["lag_horizon"] in ("immediate", "short", "medium", "long")


def test_dc2_phase3_regime_network_atlas(analysis: dict[str, Any]) -> None:
    atlas = analysis["regime_network_atlas"]
    for regime in REGIME_ORDER:
        assert regime in atlas
        assert "edges" in atlas[regime]
        assert "centrality" in atlas[regime]


def test_dc2_phase3_centrality_roles(analysis: dict[str, Any]) -> None:
    centrality = analysis["centrality_analysis"]
    assert len(centrality["nodes"]) > 0
    assert len(centrality["top_sources"]) > 0
    assert len(centrality["top_sinks"]) > 0
    for info in centrality["nodes"].values():
        assert info["topology_role"] in ("source", "sink", "relay", "intermediate")


def test_dc2_phase3_communities_and_feedback(analysis: dict[str, Any]) -> None:
    communities = analysis["community_detection"]
    assert len(communities["communities"]) > 0
    assert isinstance(communities["feedback_loops"], list)


def test_dc2_phase3_hierarchy(analysis: dict[str, Any]) -> None:
    hierarchy = analysis["information_flow_hierarchy"]
    assert len(hierarchy) > 0
    assert hierarchy[0]["role"] in ("source", "relay", "intermediate", "sink")


def test_dc2_phase3_stability(analysis: dict[str, Any]) -> None:
    stability = analysis["network_stability_analysis"]
    assert "topology_overlap" in stability
    assert "stable_edges" in stability
    assert "mean_overlap" in stability


def test_dc2_phase3_edge_registry(analysis: dict[str, Any]) -> None:
    registry = analysis["confidence_weighted_edge_registry"]
    assert len(registry) > 0
    first = registry[0]
    assert "edge" in first
    assert "confidence" in first
    assert "institutional_support" in first


def test_dc2_phase3_reports_emitted(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report_paths = emit_dc2_phase3_reports(analysis, repo_root=Path(tmp))
    assert "dynamic_network_graph" in report_paths
    assert "temporal_influence_network" in report_paths
    assert "regime_network_atlas" in report_paths
    assert "centrality_analysis" in report_paths
    assert "community_detection" in report_paths
    assert "information_flow_hierarchy" in report_paths
    assert "network_stability_analysis" in report_paths
    assert "edge_registry" in report_paths
    assert "arb_network_recommendation" in report_paths


def test_dc2_phase3_campaign_completes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_dc2_phase3_campaign(Path(tmp))
    assert "campaign_id" in result
    assert "analysis_summary" in result
    assert "report_paths" in result
    assert result["analysis_summary"]["governing_model"]
