"""Tests for DC2 Program D Phase 1 - Transition Engine verification/falsification."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc2_program_d import run_dc2_program_d_phase1_campaign
from tools.alpha_research.transition_engine_verification import (
    emit_dc2_program_d_phase1_reports,
    prepare_dc2_program_d_phase1_artifacts,
)

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc2_program_d_phase1_artifacts()


def test_program_d_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DC2_PROGRAM_D_PHASE1"
    assert len(analysis["models_evaluated"]) >= 7
    assert "baseline_comparison_matrix" in analysis
    assert "falsification_report" in analysis


def test_program_d_baseline_matrix(analysis: dict[str, Any]) -> None:
    matrix = analysis["baseline_comparison_matrix"]
    assert len(matrix) >= 7
    first = matrix[0]
    assert "model" in first
    assert "transition_detection_accuracy" in first
    assert "transition_timing_error" in first


def test_program_d_reports_content(analysis: dict[str, Any]) -> None:
    assert "transition_accuracy_report" in analysis
    assert "transition_timing_report" in analysis
    assert "transition_robustness_report" in analysis
    assert "failure_catalogue" in analysis


def test_program_d_graph_payload(analysis: dict[str, Any]) -> None:
    payload = analysis["ecology_knowledge_graph"]
    assert len(payload["model_nodes"]) >= 7
    assert "verification_node" in payload
    assert isinstance(payload["failure_nodes"], list)


def test_program_d_reports_emitted(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        paths = emit_dc2_program_d_phase1_reports(analysis, repo_root=Path(tmp))
    assert "verification_report" in paths
    assert "baseline_comparison_report" in paths
    assert "transition_accuracy_report" in paths
    assert "transition_timing_report" in paths
    assert "transition_robustness_report" in paths
    assert "falsification_report" in paths
    assert "failure_catalogue" in paths
    assert "evidence_summary" in paths
    assert "model_comparison_matrix" in paths
    assert "research_recommendations" in paths
    assert "arb_recommendation" in paths


def test_program_d_campaign_completes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_dc2_program_d_phase1_campaign(Path(tmp))
    assert "campaign_id" in result
    assert "analysis_summary" in result
    assert "decision" in result["analysis_summary"]
