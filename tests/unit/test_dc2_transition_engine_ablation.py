"""Tests for DC2 Program E Phase 1 - Transition Engine Decomposition & Ablation Analysis."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc2_program_e import run_dc2_program_e_phase1_campaign
from tools.alpha_research.transition_engine_ablation import (
    COMPONENT_NAMES,
    emit_dc2_program_e_phase1_reports,
    prepare_dc2_program_e_phase1_artifacts,
)

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc2_program_e_phase1_artifacts()


def test_program_e_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DC2_PROGRAM_E_PHASE1"
    assert analysis["components_evaluated"] == COMPONENT_NAMES
    assert analysis["ablation_run_count"] > 0


def test_program_e_contribution_report(analysis: dict[str, Any]) -> None:
    report = analysis["component_contribution_report"]
    assert len(report) == len(COMPONENT_NAMES)
    first = report[0]
    assert "component" in first
    assert "incremental_gain" in first
    assert "detection_contribution" in first
    assert "complexity_cost" in first


def test_program_e_ablation_matrix(analysis: dict[str, Any]) -> None:
    matrix = analysis["ablation_matrix"]
    # 1 baseline + 7 single + 21 pair + 35 triple
    assert len(matrix) == 1 + 7 + 21 + 35
    baseline = next(row for row in matrix if row["combination_key"] == "BASELINE")
    assert baseline["removed_count"] == 0
    assert "transition_detection_accuracy" in baseline


def test_program_e_complexity_vs_benefit(analysis: dict[str, Any]) -> None:
    cvb = analysis["complexity_vs_benefit_analysis"]
    assert len(cvb) == len(COMPONENT_NAMES)
    for row in cvb:
        assert row["verdict"] in {"RETAIN", "REDESIGN", "REMOVE", "INVESTIGATE"}


def test_program_e_failure_attribution(analysis: dict[str, Any]) -> None:
    attr = analysis["failure_attribution_report"]
    assert len(attr) == 5  # five failures from Program D
    for row in attr:
        assert row["failure_id"].startswith("F-")
        assert row["redesign_priority"] in {"HIGH", "MEDIUM", "LOW"}


def test_program_e_arb_recommendation(analysis: dict[str, Any]) -> None:
    arb = analysis["arb_recommendation"]
    assert "components_to_retain" in arb
    assert "components_to_redesign" in arb
    assert "components_to_remove" in arb
    assert "components_requiring_additional_evidence" in arb
    # All components must be accounted for across the four categories
    all_assigned = (
        set(arb["components_to_retain"])
        | set(arb["components_to_redesign"])
        | set(arb["components_to_remove"])
        | set(arb["components_requiring_additional_evidence"])
    )
    assert all_assigned == set(COMPONENT_NAMES)


def test_program_e_reports_emitted(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        paths = emit_dc2_program_e_phase1_reports(analysis, repo_root=Path(tmp))
    assert "component_contribution_report" in paths
    assert "ablation_matrix" in paths
    assert "complexity_vs_benefit_analysis" in paths
    assert "failure_attribution_report" in paths
    assert "redesign_recommendations" in paths
    assert "revision_priority_matrix" in paths
    assert "transition_engine_revision_plan" in paths
    assert "arb_recommendation" in paths


def test_program_e_campaign_completes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_dc2_program_e_phase1_campaign(Path(tmp))
    assert "campaign_id" in result
    assert "analysis_summary" in result
    assert "components_to_retain" in result["analysis_summary"]
