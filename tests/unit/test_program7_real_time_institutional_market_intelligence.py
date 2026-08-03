"""Tests for Generation 4 / Program 7 real-time institutional market intelligence."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.program7_real_time_institutional_market_intelligence import (
    run_program7_market_intelligence,
)
from tools.alpha_research.real_time_institutional_market_intelligence import (
    emit_program7_reports,
    prepare_program7_artifacts,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_program7_artifacts()


def test_program7_top_level_keys(analysis: dict[str, Any]) -> None:
    required = {
        "program",
        "market_state_registry",
        "belief_registry",
        "regime_registry",
        "alpha_activation_registry",
        "portfolio_evolution_registry",
        "research_trigger_registry",
        "event_registry",
        "knowledge_growth_registry",
        "longitudinal_registry",
        "institutional_intelligence_registry",
        "executive_dashboards",
        "schemas",
    }
    assert required.issubset(analysis.keys())


def test_streaming_registries_are_aligned(analysis: dict[str, Any]) -> None:
    n = len(analysis["market_state_registry"])
    assert n >= 12
    assert len(analysis["belief_registry"]) == n
    assert len(analysis["regime_registry"]) == n
    assert len(analysis["alpha_activation_registry"]) == n
    assert len(analysis["portfolio_evolution_registry"]) == n


def test_regime_probabilities_are_valid(analysis: dict[str, Any]) -> None:
    for row in analysis["regime_registry"]:
        probs = row["regime_probabilities"]
        assert set(probs.keys()) == {
            "BULL_TREND",
            "BEAR_TREND",
            "RISK_OFF",
            "RISK_ON",
            "MACRO_TRANSITION",
            "LIQUIDITY_CRISIS",
        }
        assert sum(float(value) for value in probs.values()) == pytest.approx(1.0, abs=2e-4)


def test_portfolio_recommendations_are_non_executing(analysis: dict[str, Any]) -> None:
    for row in analysis["portfolio_evolution_registry"]:
        portfolio = row["portfolio"]
        assert portfolio["decision"] in {"BUY", "SELL", "HOLD", "REDUCE", "INCREASE", "NO POSITION"}
        total = sum(float(item["allocation_weight"]) for item in portfolio["allocation"])
        assert total == pytest.approx(1.0, abs=2e-4)
    registry = analysis["institutional_intelligence_registry"]
    assert registry["broker_connections"] == 0
    assert registry["trade_execution_calls"] == 0
    assert registry["non_executing"] is True


def test_research_triggers_and_event_reasoning_present(analysis: dict[str, Any]) -> None:
    assert len(analysis["research_trigger_registry"]) >= 1
    assert len(analysis["event_registry"]) >= 1
    assert any(row["governed_campaign_opened"] for row in analysis["research_trigger_registry"])


def test_knowledge_evolution_preserves_lineage(analysis: dict[str, Any]) -> None:
    for row in analysis["knowledge_growth_registry"]:
        assert row["lineage_preserved"] is True


def test_dashboard_catalog_complete(analysis: dict[str, Any]) -> None:
    required = {
        "market_state_dashboard",
        "institutional_beliefs_dashboard",
        "portfolio_dashboard",
        "alpha_activity_dashboard",
        "research_queue_dashboard",
        "evidence_dashboard",
        "confidence_dashboard",
        "risk_dashboard",
        "regimes_dashboard",
        "knowledge_growth_dashboard",
        "research_productivity_dashboard",
        "scientific_health_dashboard",
    }
    assert required.issubset(analysis["executive_dashboards"].keys())


def test_schema_catalog_complete(analysis: dict[str, Any]) -> None:
    assert {
        "belief-state.schema.json",
        "market-state.schema.json",
        "regime-probabilities.schema.json",
        "alpha-activation.schema.json",
        "portfolio-evolution.schema.json",
        "research-trigger.schema.json",
        "event-reasoning.schema.json",
        "executive-dashboard.schema.json",
    }.issubset(analysis["schemas"].keys())


def test_prepare_program7_is_deterministic() -> None:
    first = prepare_program7_artifacts()
    second = prepare_program7_artifacts()
    assert (
        first["institutional_intelligence_registry"]
        == second["institutional_intelligence_registry"]
    )
    assert first["portfolio_evolution_registry"] == second["portfolio_evolution_registry"]
    assert first["research_trigger_registry"] == second["research_trigger_registry"]


def test_report_emission_writes_artifacts_and_schemas(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = emit_program7_reports(analysis, repo_root=root)
        assert Path(paths["final_report"]).exists()
        assert Path(paths["market_state_registry"]).exists()
        assert Path(paths["schema:belief-state.schema.json"]).exists()


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
        result = run_program7_market_intelligence(root)
        assert int(result["intelligence_cycles"]) >= 12
        assert result["latest_decision"] in {
            "BUY",
            "SELL",
            "HOLD",
            "REDUCE",
            "INCREASE",
            "NO POSITION",
        }
        assert int(result["governed_research_triggers"]) >= 1
