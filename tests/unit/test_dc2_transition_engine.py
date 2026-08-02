"""Tests for DC2 Program C Phase 1 - Institutional Market Transition Engine."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc2_program_c import run_dc2_program_c_phase1_campaign
from tools.alpha_research.transition_engine import (
    emit_dc2_program_c_phase1_reports,
    prepare_dc2_program_c_phase1_artifacts,
)

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc2_program_c_phase1_artifacts()


def test_program_c_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DC2_PROGRAM_C_PHASE1"
    assert "institutional_transition_engine" in analysis
    assert "transition_state_machine" in analysis
    assert "transition_trigger_registry" in analysis


def test_program_c_transition_library(analysis: dict[str, Any]) -> None:
    transitions = analysis["institutional_transition_engine"]
    assert len(transitions) == 30
    first = transitions[0]
    assert "transition_id" in first
    assert "trigger" in first
    assert "participant_actions" in first


def test_program_c_state_machine(analysis: dict[str, Any]) -> None:
    machine = analysis["transition_state_machine"]
    assert len(machine["states"]) == 6
    assert len(machine["edges"]) == 30


def test_program_c_timelines_and_graph(analysis: dict[str, Any]) -> None:
    assert len(analysis["transition_timeline_library"]) == 30
    graph = analysis["transition_causal_graph"]
    assert len(graph["nodes"]) > 0
    assert len(graph["edges"]) > 0


def test_program_c_confidence_and_early_warning(analysis: dict[str, Any]) -> None:
    confidence = analysis["transition_confidence_model"]
    assert confidence["mean_confidence"] > 0.0
    early_warning = analysis["early_warning_indicator_catalogue"]
    assert len(early_warning) > 0
    assert "indicator" in early_warning[0]


def test_program_c_failure_catalogue(analysis: dict[str, Any]) -> None:
    failures = analysis["transition_failure_catalogue"]
    assert len(failures) == 30
    assert "failure_modes" in failures[0]


def test_program_c_graph_payload(analysis: dict[str, Any]) -> None:
    payload = analysis["ecology_knowledge_graph"]
    assert len(payload["regime_nodes"]) == 6
    assert len(payload["transition_nodes"]) == 30
    assert len(payload["mechanism_nodes"]) > 0


def test_program_c_reports_emitted(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        paths = emit_dc2_program_c_phase1_reports(analysis, repo_root=Path(tmp))
    assert "institutional_transition_atlas" in paths
    assert "transition_engine_specification" in paths
    assert "transition_timeline_catalogue" in paths
    assert "transition_causal_graph" in paths
    assert "transition_trigger_registry" in paths
    assert "transition_confidence_report" in paths
    assert "integrated_market_transition_report" in paths
    assert "research_recommendations" in paths


def test_program_c_campaign_completes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_dc2_program_c_phase1_campaign(Path(tmp))
    assert "campaign_id" in result
    assert "analysis_summary" in result
    assert result["analysis_summary"]["arb_recommendation"]
