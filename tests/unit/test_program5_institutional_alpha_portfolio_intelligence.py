"""Tests for Program 5 — Institutional Alpha Portfolio Intelligence System."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.institutional_alpha_portfolio_intelligence import (
    PORTFOLIO_DECISIONS,
    PORTFOLIO_LIFECYCLE_STATES,
    emit_program5_reports,
    prepare_program5_artifacts,
)
from tools.alpha_research.program5_institutional_alpha_portfolio_intelligence import (
    run_program5_portfolio_intelligence,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_program5_artifacts()


def test_program5_top_level_keys(analysis: dict[str, Any]) -> None:
    required = {
        "program",
        "portfolio_registry",
        "allocation_registry",
        "mechanism_independence_matrix",
        "evidence_independence_matrix",
        "institutional_correlation_atlas",
        "conflict_registry",
        "portfolio_risk_report",
        "capacity_registry",
        "regime_allocation_engine",
        "institutional_portfolio_decision",
        "portfolio_explanation",
        "portfolio_lifecycle",
        "institutional_portfolio_dashboards",
        "portfolio_lineage",
        "portfolio_memory",
        "portfolio_evidence_registry",
        "portfolio_confidence_registry",
        "portfolio_graph",
        "portfolio_audit_trail",
        "schemas",
    }
    assert required.issubset(analysis.keys())


def test_all_five_approved_alphas_present(analysis: dict[str, Any]) -> None:
    allocations = analysis["allocation_registry"]
    names = {row["mechanism"] for row in allocations}
    assert len(allocations) == 5
    assert names == {
        "safe_haven_migration",
        "real_yield_dislocation_reversion",
        "policy_expectation_repricing",
        "etf_flow_accumulation_pressure",
        "commodity_cross_curve_divergence",
    }


def test_allocations_sum_to_one(analysis: dict[str, Any]) -> None:
    total = sum(float(row["allocation_weight"]) for row in analysis["allocation_registry"])
    assert total == pytest.approx(1.0, abs=1e-6)


def test_current_decision_is_explainable(analysis: dict[str, Any]) -> None:
    decision = analysis["institutional_portfolio_decision"]["current_decision"]
    assert decision["decision"] in PORTFOLIO_DECISIONS
    assert decision["explanation"]
    assert len(decision["contributions"]) == 5


def test_conflicts_are_resolved_institutionally(analysis: dict[str, Any]) -> None:
    conflicts = analysis["conflict_registry"]
    assert len(conflicts) >= 1
    for conflict in conflicts:
        assert conflict["winning_alpha"]["decision"] in PORTFOLIO_DECISIONS
        assert conflict["minority_opinion"]["decision"] in PORTFOLIO_DECISIONS
        assert conflict["combined_recommendation"] in PORTFOLIO_DECISIONS


def test_lifecycle_states_are_valid(analysis: dict[str, Any]) -> None:
    lifecycle = analysis["portfolio_lifecycle"]
    assert len(lifecycle) == 5
    for row in lifecycle:
        assert row["current_state"] in PORTFOLIO_LIFECYCLE_STATES
        assert row["history"][0] == "CANDIDATE"
        assert row["history"][1] == "APPROVED"


def test_independence_and_correlation_shapes(analysis: dict[str, Any]) -> None:
    assert len(analysis["mechanism_independence_matrix"]) == 10
    assert len(analysis["evidence_independence_matrix"]) == 10
    assert len(analysis["institutional_correlation_atlas"]) == 10


def test_regime_engine_covers_all_required_regimes(analysis: dict[str, Any]) -> None:
    regime_engine = analysis["regime_allocation_engine"]
    assert set(regime_engine.keys()) == {
        "BULL_TREND",
        "BEAR_TREND",
        "RISK_OFF",
        "RISK_ON",
        "MACRO_TRANSITION",
        "LIQUIDITY_CRISIS",
    }
    for payload in regime_engine.values():
        total = sum(float(row["allocation_weight"]) for row in payload["preferred_alpha_mix"])
        assert total == pytest.approx(1.0, abs=2e-4)


def test_portfolio_risk_report_has_core_metrics(analysis: dict[str, Any]) -> None:
    risk = analysis["portfolio_risk_report"]
    assert 0.0 <= float(risk["portfolio_confidence"]) <= 1.0
    assert 0.0 <= float(risk["portfolio_uncertainty"]) <= 1.0
    assert 0.0 <= float(risk["robustness_score"]) <= 1.0


def test_schema_catalog_contains_required_files(analysis: dict[str, Any]) -> None:
    schemas = analysis["schemas"]
    assert {
        "portfolio.schema.json",
        "allocation.schema.json",
        "risk.schema.json",
        "capacity.schema.json",
        "conflict.schema.json",
        "portfolio-decision.schema.json",
        "portfolio-explanation.schema.json",
        "portfolio-lifecycle.schema.json",
        "dashboard.schema.json",
    }.issubset(schemas.keys())


def test_report_emission_writes_reports_and_schemas(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = emit_program5_reports(analysis, repo_root=root)
        assert Path(paths["final_report"]).exists()
        assert Path(paths["allocation_registry"]).exists()
        assert Path(paths["schema:portfolio.schema.json"]).exists()
        assert Path(paths["schema:dashboard.schema.json"]).exists()


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
        result = run_program5_portfolio_intelligence(root)
        assert result["portfolio_decision"] in PORTFOLIO_DECISIONS
        assert int(result["approved_alpha_count"]) == 5
        assert int(result["conflict_count"]) >= 1
