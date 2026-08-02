"""Tests for DC2 Program B Phase 2 - Institutional Decision Ecology."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc2_program_b_phase2 import run_dc2_program_b_phase2_campaign
from tools.alpha_research.decision_ecology import (
    emit_dc2_program_b_phase2_reports,
    prepare_dc2_program_b_phase2_artifacts,
)

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc2_program_b_phase2_artifacts()


def test_program_b_phase2_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DC2_PROGRAM_B_PHASE2"
    assert "decision_profiles" in analysis
    assert "belief_update_network" in analysis
    assert "reaction_time_hierarchy" in analysis
    assert "strategic_dependency_network" in analysis


def test_program_b_phase2_profiles(analysis: dict[str, Any]) -> None:
    profile = analysis["decision_profiles"]["macro_hedge_funds"]
    assert profile["reaction_speed"] in ("intraday", "fast", "medium", "slow")
    assert profile["belief_update_process"]
    assert profile["confidence"] > 0.0


def test_program_b_phase2_belief_network(analysis: dict[str, Any]) -> None:
    belief = analysis["belief_update_network"]
    assert len(belief["edges"]) > 0
    first = belief["edges"][0]
    assert "source" in first
    assert "target" in first
    assert "update_strength" in first


def test_program_b_phase2_reaction_hierarchy(analysis: dict[str, Any]) -> None:
    hierarchy = analysis["reaction_time_hierarchy"]
    assert len(hierarchy) == 10
    assert hierarchy[0]["rank"] == 1


def test_program_b_phase2_strategic_network(analysis: dict[str, Any]) -> None:
    strategic = analysis["strategic_dependency_network"]
    assert len(strategic["edges"]) > 0
    assert "central_banks" in strategic["matrix"]


def test_program_b_phase2_cascades_and_failures(analysis: dict[str, Any]) -> None:
    assert len(analysis["decision_cascade_models"]) > 0
    assert len(analysis["decision_failure_catalogue"]) == 10


def test_program_b_phase2_graph_payload(analysis: dict[str, Any]) -> None:
    payload = analysis["ecology_knowledge_graph"]
    assert len(payload["decision_nodes"]) == 10
    assert len(payload["belief_edges"]) > 0
    assert len(payload["strategic_edges"]) > 0


def test_program_b_phase2_reports_emitted(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        paths = emit_dc2_program_b_phase2_reports(analysis, repo_root=Path(tmp))
    assert "decision_ecology_report" in paths
    assert "participant_decision_profiles" in paths
    assert "decision_cascade_atlas" in paths
    assert "strategic_interaction_matrix" in paths
    assert "belief_update_report" in paths
    assert "reaction_hierarchy" in paths
    assert "decision_failure_catalogue" in paths
    assert "institutional_recommendations" in paths


def test_program_b_phase2_campaign_completes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_dc2_program_b_phase2_campaign(Path(tmp))
    assert "campaign_id" in result
    assert "analysis_summary" in result
    assert result["analysis_summary"]["arb_recommendation"]
