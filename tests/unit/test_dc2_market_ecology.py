"""Tests for DC2 Program B Phase 1 - Institutional Market Ecology."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc2_program_b import run_dc2_program_b_campaign
from tools.alpha_research.market_ecology import (
    emit_dc2_program_b_reports,
    prepare_dc2_program_b_artifacts,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc2_program_b_artifacts()


def test_program_b_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DC2_PROGRAM_B_PHASE1"
    assert "participant_profiles" in analysis
    assert "participant_interaction_network" in analysis
    assert "capital_flow_network" in analysis
    assert "ecology_knowledge_graph" in analysis


def test_program_b_has_all_participants(analysis: dict[str, Any]) -> None:
    profiles = analysis["participant_profiles"]
    assert len(profiles) == 10
    assert "central_banks" in profiles
    assert "safe_haven_capital_flows" in profiles


def test_program_b_participant_profiles(analysis: dict[str, Any]) -> None:
    profile = analysis["participant_profiles"]["macro_hedge_funds"]
    assert profile["ecology_role"] in (
        "ecology_driver",
        "ecology_relay",
        "ecology_sink",
        "ecology_adapter",
    )
    assert profile["aggregate_ecology_score"] >= 0.0
    assert "macro_transition" in profile["expected_behaviour_by_regime"]


def test_program_b_interaction_network(analysis: dict[str, Any]) -> None:
    network = analysis["participant_interaction_network"]
    assert len(network["edges"]) > 0
    assert "central_banks" in network["matrix"]
    assert "macro_hedge_funds" in network["matrix"]["central_banks"]


def test_program_b_capital_flow_network(analysis: dict[str, Any]) -> None:
    capital = analysis["capital_flow_network"]
    assert len(capital["edges"]) > 0
    first = capital["edges"][0]
    assert "participant" in first
    assert "market_node" in first
    assert "capital_intensity" in first


def test_program_b_liquidity_network(analysis: dict[str, Any]) -> None:
    liquidity = analysis["liquidity_network"]
    assert len(liquidity["edges"]) > 0
    assert liquidity["edges"][0]["liquidity_effect"] in (
        "provision",
        "withdrawal_pressure",
        "competition",
        "balancing",
    )


def test_program_b_feedback_and_adaptive_model(analysis: dict[str, Any]) -> None:
    assert isinstance(analysis["feedback_loops"], list)
    adaptive = analysis["adaptive_behaviour_model"]
    assert "central_banks" in adaptive
    assert adaptive["central_banks"]["regime_sensitivity"] in ("high", "moderate")


def test_program_b_knowledge_graph_payload(analysis: dict[str, Any]) -> None:
    graph_payload = analysis["ecology_knowledge_graph"]
    assert len(graph_payload["participant_nodes"]) == 10
    assert len(graph_payload["factor_nodes"]) > 0
    assert len(graph_payload["interaction_edges"]) > 0


def test_program_b_reports_emitted(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        paths = emit_dc2_program_b_reports(analysis, repo_root=Path(tmp))
    assert "ecology_atlas" in paths
    assert "participant_profiles" in paths
    assert "interaction_matrix" in paths
    assert "capital_flow_atlas" in paths
    assert "liquidity_ecology" in paths
    assert "adaptive_behaviour" in paths
    assert "ecology_knowledge_graph" in paths
    assert "research_recommendations" in paths


def test_program_b_campaign_completes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_dc2_program_b_campaign(Path(tmp))
    assert "campaign_id" in result
    assert "analysis_summary" in result
    assert result["analysis_summary"]["arb_recommendation"]
