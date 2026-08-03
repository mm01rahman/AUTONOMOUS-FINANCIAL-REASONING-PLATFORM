"""Tests for Program 6 — Institutional Market Simulation & Paper Trading Laboratory."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.institutional_market_simulation_laboratory import (
    emit_program6_reports,
    prepare_program6_artifacts,
)
from tools.alpha_research.program6_institutional_market_simulation_laboratory import (
    run_program6_simulation_laboratory,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_program6_artifacts()


def test_program6_top_level_keys(analysis: dict[str, Any]) -> None:
    required = {
        "program",
        "market_replay_engine",
        "paper_trade_registry",
        "portfolio_performance_registry",
        "performance_attribution_registry",
        "portfolio_evolution_engine",
        "alpha_decay_registry",
        "drift_registry",
        "risk_monitoring_registry",
        "live_market_monitor",
        "continuous_performance_database",
        "research_feedback_registry",
        "institutional_dashboards",
        "schemas",
    }
    assert required.issubset(analysis.keys())


def test_replay_engine_supports_all_required_modes(analysis: dict[str, Any]) -> None:
    supported = set(analysis["market_replay_engine"]["supported_modes"])
    assert supported == {
        "historical_replay",
        "walk_forward_replay",
        "rolling_replay",
        "multi_year_replay",
        "regime_replay",
        "event_replay",
        "shock_replay",
        "session_replay",
    }
    rows = analysis["market_replay_engine"]["replay_rows"]
    assert len(rows) >= 8
    timestamps = [row["timestamp"] for row in rows]
    assert timestamps == sorted(timestamps)


def test_paper_trade_registry_is_non_empty_and_simulated(analysis: dict[str, Any]) -> None:
    trades = analysis["paper_trade_registry"]
    assert len(trades) == len(analysis["market_replay_engine"]["replay_rows"])
    for trade in trades:
        assert trade["decision"] in {"BUY", "SELL", "HOLD", "REDUCE", "INCREASE", "NO POSITION"}
        if trade["execution"]["status"] != "skipped":
            assert trade["execution"]["simulated_only"] is True


def test_portfolio_history_and_database_lengths_match(analysis: dict[str, Any]) -> None:
    history = analysis["portfolio_evolution_engine"]
    db = analysis["continuous_performance_database"]
    assert len(history) == len(db["daily_portfolio"])
    assert len(history) == len(db["portfolio_decisions"])
    assert len(history) == len(db["confidence_history"])
    for row in history:
        total = sum(float(item["allocation_weight"]) for item in row["allocation"])
        assert total == pytest.approx(1.0, abs=2e-4)


def test_drift_and_decay_entries_exist(analysis: dict[str, Any]) -> None:
    assert len(analysis["drift_registry"]) >= 1
    assert len(analysis["alpha_decay_registry"]) >= 1
    assert all(item["entries"] for item in analysis["drift_registry"])
    assert all(item["entries"] for item in analysis["alpha_decay_registry"])


def test_research_feedback_is_generated(analysis: dict[str, Any]) -> None:
    feedback = analysis["research_feedback_registry"]
    assert len(feedback) >= 1
    assert all("recommended_action" in row for row in feedback)
    assert any(
        row["recommended_action"]
        in {"research_campaign", "revalidation_request", "data_request"}
        for row in feedback
    )


def test_live_monitor_and_risk_outputs(analysis: dict[str, Any]) -> None:
    live = analysis["live_market_monitor"]
    risk = analysis["risk_monitoring_registry"][-1]
    assert live["symbol"] == "XAU/USD"
    assert live["portfolio_recommendation"] in {
        "BUY",
        "SELL",
        "HOLD",
        "REDUCE",
        "INCREASE",
        "NO POSITION",
    }
    assert 0.0 <= float(live["confidence"]) <= 1.0
    assert "portfolio_var" in risk
    assert "expected_shortfall" in risk


def test_deterministic_prepare_program6_artifacts() -> None:
    first = prepare_program6_artifacts()
    second = prepare_program6_artifacts()
    assert first["portfolio_performance_registry"] == second["portfolio_performance_registry"]
    assert first["live_market_monitor"] == second["live_market_monitor"]
    assert first["research_feedback_registry"] == second["research_feedback_registry"]


def test_schema_catalog_contains_required_files(analysis: dict[str, Any]) -> None:
    assert {
        "paper-trade.schema.json",
        "portfolio-history.schema.json",
        "performance.schema.json",
        "attribution.schema.json",
        "drift.schema.json",
        "decay.schema.json",
        "research-feedback.schema.json",
    }.issubset(analysis["schemas"].keys())


def test_report_emission_writes_reports_and_schemas(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = emit_program6_reports(analysis, repo_root=root)
        assert Path(paths["final_report"]).exists()
        assert Path(paths["paper_trade_registry"]).exists()
        assert Path(paths["schema:paper-trade.schema.json"]).exists()


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
        result = run_program6_simulation_laboratory(root)
        assert int(result["simulation_steps"]) >= 8
        assert result["portfolio_recommendation"] in {
            "BUY",
            "SELL",
            "HOLD",
            "REDUCE",
            "INCREASE",
            "NO POSITION",
        }
        assert int(result["research_feedback_count"]) >= 1
