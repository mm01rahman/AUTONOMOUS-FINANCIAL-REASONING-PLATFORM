"""Tests for Program 4 — Institutional Alpha Expansion Program."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.institutional_alpha_expansion_program import (
    PROMOTION_DECISIONS,
    TARGET_APPROVED_ALPHA_COUNT,
    emit_program4_reports,
    prepare_program4_artifacts,
)
from tools.alpha_research.program4_institutional_alpha_expansion import (
    run_program4_expansion,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_program4_artifacts()


def test_program4_top_level_keys(analysis: dict[str, Any]) -> None:
    required = {
        "program",
        "approved_alpha_count",
        "approved_alpha_registry",
        "rejected_alpha_registry",
        "blocked_alpha_registry",
        "institutional_alpha_library",
        "alpha_family_atlas",
        "mechanism_independence_matrix",
        "correlation_matrix",
        "evidence_atlas",
        "promotion_history",
        "research_campaign_archive",
        "institutional_dashboards",
        "knowledge_evolution",
        "stop_reason",
        "arb_recommendation",
    }
    assert required.issubset(analysis.keys())


def test_target_approved_count_reached(analysis: dict[str, Any]) -> None:
    assert int(analysis["approved_alpha_count"]) >= TARGET_APPROVED_ALPHA_COUNT
    assert "Target approved alpha count reached" in str(analysis["stop_reason"])


def test_exact_five_approved_in_registry(analysis: dict[str, Any]) -> None:
    approved = analysis["approved_alpha_registry"]
    assert len(approved) == 5
    assert "safe_haven_migration" in approved
    assert "real_yield_dislocation_reversion" in approved
    assert "policy_expectation_repricing" in approved
    assert "etf_flow_accumulation_pressure" in approved
    assert "commodity_cross_curve_divergence" in approved


def test_blocked_and_rejected_registries(analysis: dict[str, Any]) -> None:
    blocked = analysis["blocked_alpha_registry"]
    rejected = analysis["rejected_alpha_registry"]
    blocked_names = {item["mechanism"] for item in blocked}
    rejected_names = {item["mechanism"] for item in rejected}
    assert "decision_cascade" in blocked_names
    assert "central_bank_reserve_reallocation" in blocked_names
    assert "volatility_carry_shadow" in rejected_names


def test_approved_entries_have_diversification_fields(analysis: dict[str, Any]) -> None:
    for entry in analysis["approved_alpha_registry"].values():
        required = {
            "family",
            "expected_regime",
            "cross_asset_dependencies",
            "correlation_to_existing_approved",
            "shared_datasets",
            "shared_failure_modes",
            "expected_holding_horizon",
            "expected_capacity",
            "expected_decay",
            "scientific_independence_score",
            "confidence",
        }
        assert required.issubset(entry.keys())
        assert float(entry["scientific_independence_score"]) >= 0.65


def test_campaign_archive_executes_multiple_campaigns(analysis: dict[str, Any]) -> None:
    archive = analysis["research_campaign_archive"]
    assert len(archive) >= 8
    for campaign in archive:
        assert campaign["committee_decision"]["decision"] in PROMOTION_DECISIONS
        assert isinstance(campaign["experiments"], list)
        assert isinstance(campaign["evidence"], list)


def test_promotion_history_contains_program3_seed_and_program4_additions(
    analysis: dict[str, Any]
) -> None:
    history = analysis["promotion_history"]
    assert len(history) == 5
    assert history[0]["source_program"] == "PROGRAM_3"
    assert any(item["source_program"] == "PROGRAM_4" for item in history[1:])


def test_independence_matrix_shape(analysis: dict[str, Any]) -> None:
    matrix = analysis["mechanism_independence_matrix"]
    assert len(matrix) == 10
    for row in matrix:
        assert float(row["scientific_independence"]) > 0.0
        assert float(row["correlation"]) >= 0.0


def test_correlation_matrix_shape(analysis: dict[str, Any]) -> None:
    matrix = analysis["correlation_matrix"]
    assert len(matrix) == 10


def test_family_atlas_not_empty(analysis: dict[str, Any]) -> None:
    atlas = analysis["alpha_family_atlas"]
    assert len(atlas) >= 5
    families = {row["family"] for row in atlas}
    assert "SAFE_HAVEN_FLOWS" in families


def test_knowledge_evolution_structure(analysis: dict[str, Any]) -> None:
    evolution = analysis["knowledge_evolution"]
    required = {
        "alpha_lineage",
        "mechanism_evolution",
        "institutional_lessons",
        "scientific_principles",
        "evidence_convergence",
        "failure_atlas",
    }
    assert required.issubset(evolution.keys())


def test_dashboards_present(analysis: dict[str, Any]) -> None:
    required = {
        "institutional_alpha_library_dashboard",
        "approved_alpha_dashboard",
        "rejected_alpha_dashboard",
        "blocked_alpha_dashboard",
        "promotion_history_dashboard",
        "evidence_dashboard",
        "independence_dashboard",
        "campaign_archive_dashboard",
    }
    dashboards = analysis["institutional_dashboards"]
    assert required.issubset(dashboards.keys())


def test_data_expansion_requests_exist_for_blocked_items(analysis: dict[str, Any]) -> None:
    requests = analysis["data_expansion_requests"]
    assert len(requests) >= 1
    assert any(item["mechanism"] == "central_bank_reserve_reallocation" for item in requests)


def test_report_emission(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = emit_program4_reports(analysis, repo_root=root)
        assert Path(paths["final_report"]).exists()
        assert Path(paths["institutional_alpha_library"]).exists()
        assert Path(paths["mechanism_independence_matrix"]).exists()


def test_runner_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for path in [
            "data/ikros/graph",
            "data/ikros/registries/research",
            "data/ikros/registries/experiments",
            "data/ikros/orchestrator/campaigns",
            "data/ikros/orchestrator/audit",
            "data/ikros/orchestrator/reports",
            "data/ikros/memory/t1-episodic",
            "data/ikros/memory/t4-institutional",
        ]:
            (root / path).mkdir(parents=True)
        result = run_program4_expansion(root)
        assert int(result["approved_alpha_count"]) == 5
        assert int(result["campaigns_executed"]) >= 8
        assert "real_yield_dislocation_reversion" in result["approved_mechanisms"]
        assert "volatility_carry_shadow" in result["rejected_mechanisms"]
