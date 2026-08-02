"""Tests for Discovery Cycle 3 Phase 2 Institutional Alpha Validation Framework."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc3_phase2_validation_framework import (
    run_dc3_phase2_validation_framework_campaign,
)
from tools.alpha_research.institutional_alpha_validation import (
    emit_dc3_phase2_validation_framework_reports,
    prepare_dc3_phase2_validation_framework_artifacts,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc3_phase2_validation_framework_artifacts()


def test_phase2_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DISCOVERY_CYCLE_3_PHASE_2"
    assert analysis["framework_version"] == "1.0.0"
    assert analysis["scope"].startswith("Mechanism-agnostic")


def test_phase2_dimensions_and_methods(analysis: dict[str, Any]) -> None:
    dims = analysis["validation_dimensions"]
    methods = analysis["mandatory_validation_methods"]
    assert len(dims) == 20
    assert len(methods) >= 17
    assert "walk_forward_validation" in methods
    assert "confidence_calibration" in dims


def test_phase2_registry_schemas(analysis: dict[str, Any]) -> None:
    val = analysis["validation_registry_schema"]
    fail = analysis["failure_registry_schema"]
    assert "schema_id" in val
    assert "required_fields" in val
    assert "schema_id" in fail
    assert "required_fields" in fail


def test_phase2_promotion_framework(analysis: dict[str, Any]) -> None:
    pf = analysis["promotion_framework"]
    assert "levels" in pf
    assert "APPROVED" in pf["levels"]
    assert "gating_rules" in pf
    assert len(pf["gating_rules"]) >= 3


def test_phase2_arb_guards(analysis: dict[str, Any]) -> None:
    arb = analysis["arb_recommendation"]
    assert arb["framework_ready"] is True
    assert arb["validate_phase1_mechanisms_now"] is False
    assert arb["promote_any_alpha_now"] is False
    assert arb["adopt_as_only_approved_path"] is True


def test_phase2_reports_emit(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        paths = emit_dc3_phase2_validation_framework_reports(analysis, repo_root=Path(tmp))
    assert "validation_architecture" in paths
    assert "validation_registry" in paths
    assert "validation_evidence_registry" in paths
    assert "failure_registry" in paths
    assert "promotion_framework" in paths
    assert "validation_dashboard" in paths
    assert "validation_reports" in paths
    assert "failure_reports" in paths
    assert "confidence_reports" in paths
    assert "promotion_criteria" in paths
    assert "institutional_alpha_standard" in paths
    assert "validation_api" in paths
    assert "governed_json_schemas" in paths
    assert "documentation" in paths
    assert "ikros_integration" in paths
    assert "final_report" in paths


def test_phase2_campaign_completes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_dc3_phase2_validation_framework_campaign(Path(tmp))
    assert "campaign_id" in result
    assert "analysis_summary" in result
    assert result["analysis_summary"]["framework_ready"] is True
