"""Tests for DC2 Program F Phase 1 - Institutional Theory Extraction."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc2_program_f import run_dc2_program_f_phase1_campaign
from tools.alpha_research.institutional_theory_extraction import (
    emit_dc2_program_f_phase1_reports,
    prepare_dc2_program_f_phase1_artifacts,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc2_program_f_phase1_artifacts()


def test_program_f_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DC2_PROGRAM_F_PHASE1"
    assert len(analysis["source_programs"]) == 8
    assert len(analysis["scientific_principle_registry"]) >= 8


def test_program_f_has_classifications(analysis: dict[str, Any]) -> None:
    assert len(analysis["institutional_axiom_registry"]) >= 1
    assert len(analysis["supported_principles"]) >= 1
    assert len(analysis["conditional_principles"]) >= 1
    assert len(analysis["rejected_principles"]) >= 1
    assert len(analysis["open_research_questions"]) >= 1


def test_program_f_principle_schema(analysis: dict[str, Any]) -> None:
    first = analysis["scientific_principle_registry"][0]
    for key in [
        "principle_id",
        "name",
        "classification",
        "scientific_statement",
        "supporting_evidence",
        "contradictory_evidence",
        "confidence",
        "scope",
        "failure_conditions",
        "regime_dependence",
        "economic_rationale",
        "institutional_candidate",
    ]:
        assert key in first


def test_program_f_evidence_synthesis(analysis: dict[str, Any]) -> None:
    synthesis = analysis["evidence_synthesis"]
    assert "what_dc2_proved" in synthesis
    assert "what_dc2_disproved" in synthesis
    assert "what_remains_uncertain" in synthesis
    assert "architecture_constraints_for_future_models" in synthesis
    assert len(synthesis["architecture_constraints_for_future_models"]) >= 5


def test_program_f_graph_payload(analysis: dict[str, Any]) -> None:
    payload = analysis["ecology_knowledge_graph"]
    assert "principle_nodes" in payload
    assert "conclusion_node" in payload
    assert "constraints_node" in payload
    assert len(payload["principle_nodes"]) == len(analysis["scientific_principle_registry"])
    assert isinstance(payload["edges"], list)


def test_program_f_reports_emitted(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        paths = emit_dc2_program_f_phase1_reports(analysis, repo_root=Path(tmp))
    assert "institutional_theory_report" in paths
    assert "scientific_principle_registry" in paths
    assert "evidence_synthesis" in paths
    assert "knowledge_consolidation_report" in paths
    assert "institutional_axiom_registry" in paths
    assert "open_research_questions" in paths
    assert "architecture_constraints" in paths
    assert "arb_recommendation" in paths
    assert "classification_summary" in paths


def test_program_f_campaign_completes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_dc2_program_f_phase1_campaign(Path(tmp))
    assert "campaign_id" in result
    assert "analysis_summary" in result
    assert "promote_to_institutional_constraints" in result["analysis_summary"]
