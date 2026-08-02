"""Tests for Program 1 — Institutional Alpha Factory (Parts A–K)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.institutional_alpha_factory import (
    LIFECYCLE_STATES,
    PROMOTION_DECISIONS,
    emit_program1_reports,
    prepare_program1_artifacts,
)
from tools.alpha_research.program1_alpha_factory import run_program1_alpha_factory_campaign


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_program1_artifacts()


# ---------------------------------------------------------------------------
# Part K.1 — Factory structure
# ---------------------------------------------------------------------------


def test_program1_top_level_keys(analysis: dict[str, Any]) -> None:
    required = {
        "program",
        "version",
        "no_promotion_executed",
        "approved_alpha_count",
        "mechanisms_processed",
        "mechanism_results",
        "replication_registry",
        "promotion_reviews",
        "institutional_alpha_registry",
        "evidence_convergence_reports",
        "institutional_dossiers",
        "ikros_extensions",
        "dashboards",
        "arb_recommendation",
    }
    assert required.issubset(analysis.keys())
    assert analysis["program"] == "INSTITUTIONAL_ALPHA_FACTORY_PROGRAM_1"


def test_two_mechanisms_processed(analysis: dict[str, Any]) -> None:
    assert analysis["mechanisms_processed"] == 2
    assert len(analysis["mechanism_results"]) == 2
    assert len(analysis["replication_registry"]) == 2
    assert len(analysis["promotion_reviews"]) == 2
    assert len(analysis["institutional_alpha_registry"]) == 2
    assert len(analysis["evidence_convergence_reports"]) == 2
    assert len(analysis["institutional_dossiers"]) == 2
    assert len(analysis["ikros_extensions"]) == 2


# ---------------------------------------------------------------------------
# Part K.2 — Part A: Replication Engine
# ---------------------------------------------------------------------------


def test_replication_registry_structure(analysis: dict[str, Any]) -> None:
    for entry in analysis["replication_registry"]:
        assert "alpha_id" in entry
        assert "mechanism" in entry
        assert "replication_status" in entry
        assert entry["replication_status"] in {"CONFIRMED", "PARTIAL", "FAILED", "BLOCKED"}
        assert isinstance(entry["overall_replication_score"], float)
        assert 0.0 <= entry["overall_replication_score"] <= 1.0
        assert isinstance(entry["contradictions_found"], int)


def test_safe_haven_migration_replication_partial(analysis: dict[str, Any]) -> None:
    reg = analysis["replication_registry"]
    shm = next(
        r for r in reg if r["alpha_id"] == "IKROS-ALPHA-DC3-20260802-0006"
    )
    assert shm["replication_status"] == "PARTIAL"
    assert float(shm["overall_replication_score"]) < 0.70
    assert float(shm["overall_replication_score"]) >= 0.50
    assert len(shm["replication_ledger"]) == 3


def test_decision_cascade_replication_blocked(analysis: dict[str, Any]) -> None:
    reg = analysis["replication_registry"]
    dc = next(
        r for r in reg if r["alpha_id"] == "IKROS-ALPHA-DC3-20260802-0009"
    )
    assert dc["replication_status"] == "BLOCKED"
    assert dc["overall_replication_score"] == 0.0
    assert dc["total_replications"] == 0
    assert dc["replication_ledger"] == []


# ---------------------------------------------------------------------------
# Part K.3 — Part B: Promotion Committee
# ---------------------------------------------------------------------------


def test_promotion_reviews_structure(analysis: dict[str, Any]) -> None:
    for review in analysis["promotion_reviews"]:
        assert "alpha_id" in review
        assert "decision" in review
        assert review["decision"] in PROMOTION_DECISIONS
        assert "criteria_scores" in review
        assert "criteria_pass" in review
        assert isinstance(review["criteria_met"], int)
        assert isinstance(review["criteria_total"], int)
        assert 0.0 <= review["overall_score"] <= 1.0


def test_safe_haven_migration_committee_returns(analysis: dict[str, Any]) -> None:
    rev = analysis["promotion_reviews"]
    shm = next(r for r in rev if r["alpha_id"] == "IKROS-ALPHA-DC3-20260802-0006")
    # Must not be PROMOTE — scientific validity (0.61) is below threshold (0.70)
    assert shm["decision"] in {"RETURN_FOR_RESEARCH", "RETURN_FOR_REPLICATION"}
    # Observation completeness passes for safe_haven_migration
    assert shm["criteria_pass"]["observation_completeness"] is True


def test_decision_cascade_committee_returns(analysis: dict[str, Any]) -> None:
    rev = analysis["promotion_reviews"]
    dc = next(r for r in rev if r["alpha_id"] == "IKROS-ALPHA-DC3-20260802-0009")
    # Must return for research — observation gate failed
    assert dc["decision"] == "RETURN_FOR_RESEARCH"
    assert dc["criteria_pass"]["observation_completeness"] is False


# ---------------------------------------------------------------------------
# Part K.4 — Part C: Institutional Alpha Registry
# ---------------------------------------------------------------------------


def test_alpha_registry_structure(analysis: dict[str, Any]) -> None:
    for entry in analysis["institutional_alpha_registry"]:
        required = {
            "alpha_id", "mechanism", "lifecycle_state", "registry_status",
            "confidence", "replication_score", "scientific_mechanism",
            "economic_rationale", "feature_dependencies",
            "capacity_class", "retirement_criteria",
        }
        assert required.issubset(entry.keys())
        assert entry["lifecycle_state"] in LIFECYCLE_STATES
        assert entry["registry_status"] in {"CANDIDATE", "APPROVED", "RETIRED"}
        assert 0.0 <= float(entry["confidence"]) <= 1.0


def test_no_approved_alpha_in_registry(analysis: dict[str, Any]) -> None:
    for entry in analysis["institutional_alpha_registry"]:
        assert entry["registry_status"] != "APPROVED"
        assert entry["lifecycle_state"] not in {"APPROVED_ALPHA", "ACTIVE_ALPHA"}


# ---------------------------------------------------------------------------
# Part K.5 — Part D: Evidence Convergence Engine
# ---------------------------------------------------------------------------


def test_convergence_reports_structure(analysis: dict[str, Any]) -> None:
    valid_states = {
        "CONVERGING", "CONVERGING_SLOWLY", "OSCILLATING",
        "DIVERGING", "INSUFFICIENT_DATA",
    }
    for report in analysis["evidence_convergence_reports"]:
        assert "alpha_id" in report
        assert "convergence_state" in report
        assert report["convergence_state"] in valid_states
        assert 0.0 <= float(report["stability_score"]) <= 1.0
        assert isinstance(report["is_converging"], bool)
        assert 0.0 <= float(report["evidence_weight"]) <= 1.0


def test_safe_haven_migration_convergence(analysis: dict[str, Any]) -> None:
    convs = analysis["evidence_convergence_reports"]
    shm = next(r for r in convs if r["alpha_id"] == "IKROS-ALPHA-DC3-20260802-0006")
    assert shm["convergence_state"] in {"CONVERGING", "CONVERGING_SLOWLY", "OSCILLATING"}
    assert len(shm["confidence_trajectory"]) >= 3


# ---------------------------------------------------------------------------
# Part K.6 — Part E: Promotion Review / Lifecycle States
# ---------------------------------------------------------------------------


def test_lifecycle_states_are_valid(analysis: dict[str, Any]) -> None:
    for result in analysis["mechanism_results"]:
        assert result["initial_lifecycle_state"] in LIFECYCLE_STATES
        assert result["final_lifecycle_state"] in LIFECYCLE_STATES


def test_no_promotion_executed(analysis: dict[str, Any]) -> None:
    assert analysis["no_promotion_executed"] is True
    assert analysis["approved_alpha_count"] == 0
    for result in analysis["mechanism_results"]:
        assert result["final_lifecycle_state"] not in {
            "APPROVED_ALPHA", "ACTIVE_ALPHA", "UNDER_MONITORING"
        }


def test_safe_haven_migration_traverses_stages(analysis: dict[str, Any]) -> None:
    results = analysis["mechanism_results"]
    shm = next(r for r in results if r["alpha_id"] == "IKROS-ALPHA-DC3-20260802-0006")
    # Should have traversed through intermediate stages (PARTIAL replication + observation pass)
    assert len(shm["stages_traversed"]) >= 1
    assert shm["observation_gate_pass"] is True


def test_decision_cascade_blocked_no_stages(analysis: dict[str, Any]) -> None:
    results = analysis["mechanism_results"]
    dc = next(r for r in results if r["alpha_id"] == "IKROS-ALPHA-DC3-20260802-0009")
    assert dc["stages_traversed"] == []
    assert dc["observation_gate_pass"] is False
    assert dc["final_lifecycle_state"] == "RESEARCH"


# ---------------------------------------------------------------------------
# Part K.7 — Part F: Institutional Dossier
# ---------------------------------------------------------------------------


def test_dossier_structure(analysis: dict[str, Any]) -> None:
    required_sections = {
        "executive_summary", "scientific_basis", "validation_history",
        "replication_record", "evidence_convergence", "feature_and_dataset_profile",
        "risk_and_capacity", "future_research",
    }
    for dossier in analysis["institutional_dossiers"]:
        assert "dossier_id" in dossier
        assert "alpha_id" in dossier
        assert "sections" in dossier
        assert required_sections.issubset(dossier["sections"].keys())


# ---------------------------------------------------------------------------
# Part K.8 — Part G: IKROS Extensions
# ---------------------------------------------------------------------------


def test_ikros_extensions_structure(analysis: dict[str, Any]) -> None:
    required_keys = {
        "alpha_registry_upsert", "replication_registry_upsert",
        "promotion_registry_upsert", "confidence_registry_upsert", "lineage_record",
    }
    for ext in analysis["ikros_extensions"]:
        assert required_keys.issubset(ext.keys())
        assert "alpha_id" in ext["lineage_record"]
        assert ext["lineage_record"]["program"] == "INSTITUTIONAL_ALPHA_FACTORY_PROGRAM_1"


# ---------------------------------------------------------------------------
# Part K.9 — Part H: Dashboards
# ---------------------------------------------------------------------------


def test_seven_dashboards_present(analysis: dict[str, Any]) -> None:
    dashboards = analysis["dashboards"]
    required = {
        "institutional_alpha_dashboard",
        "promotion_dashboard",
        "evidence_dashboard",
        "replication_dashboard",
        "confidence_dashboard",
        "research_queue_dashboard",
        "scientific_status_dashboard",
    }
    assert required.issubset(dashboards.keys())
    for name in required:
        assert "tiles" in dashboards[name]
        assert len(dashboards[name]["tiles"]) > 0


def test_promotion_dashboard_counts_correct(analysis: dict[str, Any]) -> None:
    tiles = {t[0]: t[1] for t in analysis["dashboards"]["promotion_dashboard"]["tiles"]}
    # No promotions expected
    assert tiles.get("PROMOTE Decisions", 0) == 0


# ---------------------------------------------------------------------------
# Part K.10 — Report emission
# ---------------------------------------------------------------------------


def test_report_emission(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = emit_program1_reports(analysis, repo_root=root)
        assert "final_report" in paths
        assert "replication_registry" in paths
        assert "institutional_alpha_registry" in paths
        assert "promotion_reviews" in paths
        assert "evidence_convergence_reports" in paths
        assert Path(paths["final_report"]).exists()
        assert Path(paths["replication_registry"]).exists()
        assert Path(paths["institutional_alpha_registry"]).exists()


def test_schemas_emitted(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        emit_program1_reports(analysis, repo_root=root)
        schema_dir = root / "schemas" / "institutional-alpha-factory"
        assert schema_dir.exists()
        schema_files = list(schema_dir.glob("*.schema.json"))
        assert len(schema_files) >= 9


# ---------------------------------------------------------------------------
# Part K.11 — End-to-end campaign
# ---------------------------------------------------------------------------


def test_campaign_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Bootstrap minimal IKROS directory structure
        (root / "data" / "ikros" / "graph").mkdir(parents=True)
        (root / "data" / "ikros" / "registries" / "research").mkdir(parents=True)
        (root / "data" / "ikros" / "registries" / "experiments").mkdir(parents=True)
        (root / "data" / "ikros" / "orchestrator" / "campaigns").mkdir(parents=True)
        (root / "data" / "ikros" / "orchestrator" / "audit").mkdir(parents=True)
        (root / "data" / "ikros" / "orchestrator" / "reports").mkdir(parents=True)
        (root / "data" / "ikros" / "memory" / "t1-episodic").mkdir(parents=True)
        (root / "data" / "ikros" / "memory" / "t4-institutional").mkdir(parents=True)

        result = run_program1_alpha_factory_campaign(root)

        assert result["mechanisms_processed"] == 2
        assert result["approved_alpha_count"] == 0
        assert result["no_promotion_executed"] is True
        assert isinstance(result["campaign_id"], str)
        assert len(result["replication_statuses"]) == 2
        assert len(result["committee_decisions"]) == 2
        assert len(result["final_lifecycle_states"]) == 2
