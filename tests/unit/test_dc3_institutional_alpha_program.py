"""Tests for Discovery Cycle 3 Institutional Alpha Discovery Program."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc3_institutional_alpha_program import (
    run_dc3_institutional_alpha_campaign,
)
from tools.alpha_research.institutional_alpha_discovery import (
    emit_dc3_institutional_alpha_reports,
    prepare_dc3_institutional_alpha_artifacts,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc3_institutional_alpha_artifacts()


def test_dc3_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DISCOVERY_CYCLE_3_INSTITUTIONAL_ALPHA_PROGRAM"
    assert "institutional_alpha_discovery_engine" in analysis
    assert len(analysis["institutional_alpha_registry"]) >= 10


def test_dc3_catalogue_and_queue(analysis: dict[str, Any]) -> None:
    assert len(analysis["institutional_alpha_catalogue"]) > 0
    assert len(analysis["institutional_alpha_queue"]) == len(
        analysis["institutional_alpha_catalogue"]
    )
    first = analysis["institutional_alpha_queue"][0]
    assert "priority_band" in first
    assert first["priority_band"] in {"P1", "P2", "P3"}


def test_dc3_competition_report(analysis: dict[str, Any]) -> None:
    report = analysis["alpha_competition_report"]
    assert "retained" in report
    assert "removed" in report
    assert report["retained"] >= 1
    assert isinstance(report["dominant_mechanism_families"], list)


def test_dc3_validation_prep_is_pre_validation_only(analysis: dict[str, Any]) -> None:
    completion = analysis["discovery_cycle_3_completion_report"]
    assert completion["validation_executed"] is False
    assert completion["optimization_executed"] is False
    assert completion["strategy_generation_executed"] is False


def test_dc3_arb_guardrails(analysis: dict[str, Any]) -> None:
    arb = analysis["arb_recommendation"]
    assert arb["validate_now"] is False
    assert arb["optimize_now"] is False
    assert arb["promote_alpha_now"] is False


def test_dc3_reports_emitted(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        paths = emit_dc3_institutional_alpha_reports(analysis, repo_root=Path(tmp))
    assert "institutional_alpha_discovery_engine" in paths
    assert "institutional_alpha_registry" in paths
    assert "institutional_alpha_catalogue" in paths
    assert "alpha_mechanism_atlas" in paths
    assert "economic_mechanism_atlas" in paths
    assert "research_priority_matrix" in paths
    assert "alpha_competition_report" in paths
    assert "institutional_alpha_queue" in paths
    assert "alpha_explainability_reports" in paths
    assert "validation_preparation_reports" in paths
    assert "institutional_alpha_roadmap" in paths
    assert "discovery_cycle_3_completion_report" in paths
    assert "arb_recommendation" in paths


def test_dc3_campaign_completes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_dc3_institutional_alpha_campaign(Path(tmp))
    assert "campaign_id" in result
    assert "analysis_summary" in result
    assert result["analysis_summary"]["governed_discovery_complete"] is True
