"""Tests for Program 3 — Autonomous Institutional Alpha Campaign Engine."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.autonomous_institutional_alpha_campaign_engine import (
    COMMITTEE_DECISIONS,
    TERMINAL_STATES,
    emit_program3_reports,
    prepare_program3_artifacts,
)
from tools.alpha_research.program3_autonomous_campaign_engine import (
    run_program3_campaign_engine,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_program3_artifacts()


def test_program3_top_level_keys(analysis: dict[str, Any]) -> None:
    required = {
        "program",
        "campaigns_executed",
        "experiments_executed",
        "evidence_accumulated",
        "campaign_archive",
        "final_mechanism_states",
        "confidence_evolution",
        "mechanisms_promoted",
        "mechanisms_rejected",
        "mechanisms_blocked_by_data",
        "scientific_principles_learned",
        "ikros_growth",
        "research_economics",
        "dashboards",
        "arb_recommendation",
    }
    assert required.issubset(analysis.keys())


def test_program3_executes_multiple_campaigns(analysis: dict[str, Any]) -> None:
    assert int(analysis["campaigns_executed"]) >= 4
    assert int(analysis["experiments_executed"]) >= 10
    assert int(analysis["evidence_accumulated"]) >= int(analysis["campaigns_executed"])


def test_all_mechanisms_terminal(analysis: dict[str, Any]) -> None:
    states = analysis["final_mechanism_states"]
    assert len(states) == 2
    for state in states.values():
        assert state["terminal_state"] in TERMINAL_STATES
    assert analysis["remaining_mechanisms"] == []


def test_safe_haven_promoted(analysis: dict[str, Any]) -> None:
    shm = analysis["final_mechanism_states"]["safe_haven_migration"]
    assert shm["terminal_state"] == "APPROVED_ALPHA"
    assert "safe_haven_migration" in analysis["mechanisms_promoted"]
    assert float(shm["confidence"]) > 0.70


def test_decision_cascade_blocked_by_data(analysis: dict[str, Any]) -> None:
    dc = analysis["final_mechanism_states"]["decision_cascade"]
    assert dc["terminal_state"] == "BLOCKED_BY_DATA"
    assert "decision_cascade" in analysis["mechanisms_blocked_by_data"]


def test_campaign_archive_structure(analysis: dict[str, Any]) -> None:
    for campaign in analysis["campaign_archive"]:
        required = {
            "campaign_id",
            "mechanism",
            "campaign_plan",
            "research_questions",
            "hypotheses",
            "experiments",
            "evidence",
            "results",
            "confidence_updates",
            "failure_analysis",
            "replication_results",
            "committee_decision",
            "knowledge_updates",
            "future_work",
            "campaign_dashboard",
            "campaign_metrics",
            "campaign_audit",
        }
        assert required.issubset(campaign.keys())
        assert campaign["committee_decision"]["decision"] in COMMITTEE_DECISIONS


def test_campaign_results_are_deterministic_shape(analysis: dict[str, Any]) -> None:
    for campaign in analysis["campaign_archive"]:
        results = campaign["results"]
        assert float(results["confidence_after"]) >= 0.0
        assert float(results["evidence_completeness_after"]) >= 0.0
        assert isinstance(campaign["experiments"], list)
        assert isinstance(campaign["evidence"], list)


def test_confidence_histories_progress(analysis: dict[str, Any]) -> None:
    histories = analysis["confidence_evolution"]
    assert len(histories["safe_haven_migration"]) >= 3
    assert len(histories["decision_cascade"]) >= 2
    assert float(histories["safe_haven_migration"][-1]) > float(
        histories["safe_haven_migration"][0]
    )


def test_dataset_gaps_recorded(analysis: dict[str, Any]) -> None:
    gaps = analysis["dataset_gaps_discovered"]
    assert len(gaps["safe_haven_migration"]) >= 1
    assert len(gaps["decision_cascade"]) >= 1


def test_scientific_principles_present(analysis: dict[str, Any]) -> None:
    principles = analysis["scientific_principles_learned"]
    assert len(principles) >= 3
    for principle in principles:
        assert "principle_id" in principle
        assert "statement" in principle


def test_ikros_growth_metrics(analysis: dict[str, Any]) -> None:
    growth = analysis["ikros_growth"]
    assert int(growth["campaign_registry_updates"]) == int(analysis["campaigns_executed"])
    assert int(growth["experiment_registry_updates"]) == int(analysis["experiments_executed"])


def test_research_economics_structure(analysis: dict[str, Any]) -> None:
    economics = analysis["research_economics"]
    required = {
        "research_cost",
        "engineering_cost",
        "dataset_cost",
        "expected_information_gain",
        "expected_alpha_gain",
        "expected_confidence_gain",
        "expected_roi",
        "campaign_efficiency",
        "research_throughput",
    }
    assert required.issubset(economics.keys())


def test_dashboard_set_present(analysis: dict[str, Any]) -> None:
    required = {
        "research_queue_dashboard",
        "campaign_dashboard",
        "evidence_dashboard",
        "replication_dashboard",
        "promotion_dashboard",
        "mechanism_dashboard",
        "failure_dashboard",
        "confidence_dashboard",
        "dataset_dashboard",
        "observability_dashboard",
        "scientific_progress_dashboard",
    }
    dashboards = analysis["dashboards"]
    assert required.issubset(dashboards.keys())
    for dashboard in required:
        assert "tiles" in dashboards[dashboard]


def test_queue_history_recorded(analysis: dict[str, Any]) -> None:
    history = analysis["queue_history"]
    assert len(history) >= 2
    assert history[0]["iteration"] == 1


def test_report_emission(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = emit_program3_reports(analysis=analysis, repo_root=root)
        assert Path(paths["final_report"]).exists()
        assert Path(paths["campaign_archive"]).exists()
        assert Path(paths["research_economics"]).exists()


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

        result = run_program3_campaign_engine(root)
        assert int(result["campaigns_executed"]) >= 4
        assert int(result["promoted_count"]) == 1
        assert int(result["blocked_by_data_count"]) == 1
        assert result["terminal_states"]["safe_haven_migration"] == "APPROVED_ALPHA"
        assert result["terminal_states"]["decision_cascade"] == "BLOCKED_BY_DATA"
