"""Tests for Program 2 — Institutional Alpha Research Laboratory (Parts A–O)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.institutional_alpha_research_laboratory import (
    emit_program2_reports,
    prepare_program2_artifacts,
)
from tools.alpha_research.program2_research_laboratory import (
    run_program2_research_laboratory_campaign,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_program2_artifacts()


# ---------------------------------------------------------------------------
# Part O.1 — Top-level structure
# ---------------------------------------------------------------------------


def test_program2_top_level_keys(analysis: dict[str, Any]) -> None:
    required = {
        "program",
        "version",
        "mechanisms_under_research",
        "approved_alpha_count",
        "no_portfolio_construction",
        "no_live_trading",
        "research_director",
        "experiment_designer",
        "feature_evolution",
        "causal_refinement",
        "dataset_intelligence",
        "eig_engine",
        "mechanism_evolution",
        "knowledge_synthesis",
        "research_economics",
        "scheduler",
        "dashboards",
        "arb_recommendation",
    }
    assert required.issubset(analysis.keys())
    assert analysis["program"] == "INSTITUTIONAL_ALPHA_RESEARCH_LABORATORY_PROGRAM_2"


def test_governance_flags(analysis: dict[str, Any]) -> None:
    assert analysis["no_portfolio_construction"] is True
    assert analysis["no_live_trading"] is True
    assert analysis["approved_alpha_count"] == 0


def test_two_mechanisms_in_lab(analysis: dict[str, Any]) -> None:
    assert analysis["mechanisms_under_research"] == 2


# ---------------------------------------------------------------------------
# Part O.2 — Part A: Research Director
# ---------------------------------------------------------------------------


def test_research_director_structure(analysis: dict[str, Any]) -> None:
    director = analysis["research_director"]
    assert "priority_registry" in director
    assert "research_schedule" in director
    assert "campaign_queue" in director
    assert "research_calendar" in director
    assert "budget_allocation" in director


def test_priority_registry_sorted_by_score(analysis: dict[str, Any]) -> None:
    reg = analysis["research_director"]["priority_registry"]
    assert len(reg) == 2
    scores = [float(r["priority_score"]) for r in reg]
    assert scores == sorted(scores, reverse=True)
    for r in reg:
        assert 0.0 < float(r["priority_score"]) <= 1.0
        assert isinstance(r["failed_criteria_count"], int)
        assert r["failed_criteria_count"] >= 0


def test_campaign_queue_structure(analysis: dict[str, Any]) -> None:
    queue = analysis["research_director"]["campaign_queue"]
    assert len(queue) >= 3
    for item in queue:
        assert "campaign_name" in item
        assert "mechanism" in item
        assert "estimated_eig" in item
        assert float(item["estimated_eig"]) > 0.0


def test_research_calendar_has_four_quarters(analysis: dict[str, Any]) -> None:
    cal = analysis["research_director"]["research_calendar"]
    assert set(cal.keys()) == {"Q1", "Q2", "Q3", "Q4"}
    for q in cal.values():
        assert "theme" in q
        assert "expected_confidence_gain" in q


# ---------------------------------------------------------------------------
# Part O.3 — Part B: Experiment Designer
# ---------------------------------------------------------------------------


def test_experiment_designer_structure(analysis: dict[str, Any]) -> None:
    ed = analysis["experiment_designer"]
    assert "experiment_registry" in ed
    assert "total_experiments_designed" in ed
    assert int(ed["total_experiments_designed"]) >= 5


def test_experiments_have_required_fields(analysis: dict[str, Any]) -> None:
    for exp in analysis["experiment_designer"]["experiment_registry"]:
        assert "experiment_id" in exp
        assert "alpha_id" in exp
        assert "experiment_type" in exp
        assert "expected_information_gain" in exp
        assert float(exp["expected_information_gain"]) >= 0.0
        assert exp["experiment_type"] in {
            "VALIDATION", "ABLATION", "CAUSAL",
            "COUNTERFACTUAL", "REGIME", "INTERACTION",
        }


def test_blocked_mechanism_experiments_pending_data(analysis: dict[str, Any]) -> None:
    dc_exps = [
        e for e in analysis["experiment_designer"]["experiment_registry"]
        if e["alpha_id"] == "IKROS-ALPHA-DC3-20260802-0009"
        and e["experiment_type"] != "COUNTERFACTUAL"
    ]
    for exp in dc_exps:
        assert exp["status"] == "PENDING_DATA"


# ---------------------------------------------------------------------------
# Part O.4 — Part C: Feature Evolution Engine
# ---------------------------------------------------------------------------


def test_feature_evolution_structure(analysis: dict[str, Any]) -> None:
    fe = analysis["feature_evolution"]
    assert "evolution_reports" in fe
    assert "replacement_registry" in fe
    assert "retired_feature_registry" in fe
    assert len(fe["evolution_reports"]) == 2


def test_feature_evolution_aging_detection(analysis: dict[str, Any]) -> None:
    for report in analysis["feature_evolution"]["evolution_reports"]:
        assert "aging_features" in report
        assert "stable_features" in report
        assert "average_feature_confidence" in report
        assert 0.0 <= float(report["average_feature_confidence"]) <= 1.0


# ---------------------------------------------------------------------------
# Part O.5 — Part D: Causal Refinement Engine
# ---------------------------------------------------------------------------


def test_causal_refinement_structure(analysis: dict[str, Any]) -> None:
    cr = analysis["causal_refinement"]
    assert "causal_revision_reports" in cr
    assert len(cr["causal_revision_reports"]) == 2
    for report in cr["causal_revision_reports"]:
        assert "mechanism" in report
        assert "missing_variables" in report
        assert "weak_links" in report
        assert "strong_links" in report
        assert float(report["expected_causal_improvement"]) >= 0.0


# ---------------------------------------------------------------------------
# Part O.6 — Part E: Dataset Intelligence Engine
# ---------------------------------------------------------------------------


def test_dataset_intelligence_structure(analysis: dict[str, Any]) -> None:
    di = analysis["dataset_intelligence"]
    assert "dataset_intelligence_reports" in di
    assert len(di["dataset_intelligence_reports"]) == 2
    for report in di["dataset_intelligence_reports"]:
        assert "mechanism" in report
        assert "current_observation_completeness" in report
        assert "projected_observation_completeness" in report
        assert "dataset_recommendations" in report
        assert len(report["dataset_recommendations"]) >= 1


def test_decision_cascade_observation_gain(analysis: dict[str, Any]) -> None:
    reports = analysis["dataset_intelligence"]["dataset_intelligence_reports"]
    dc = next(r for r in reports if r["mechanism"] == "decision_cascade")
    # With recommended datasets, observation completeness should cross 0.70
    assert bool(dc["observation_gate_would_pass"]) is True
    assert float(dc["projected_observation_completeness"]) >= 0.70


# ---------------------------------------------------------------------------
# Part O.7 — Part F: EIG Engine
# ---------------------------------------------------------------------------


def test_eig_engine_structure(analysis: dict[str, Any]) -> None:
    eig = analysis["eig_engine"]
    assert "eig_ranked_list" in eig
    assert "top_priority" in eig
    assert "total_items_ranked" in eig
    assert int(eig["total_items_ranked"]) >= 5
    assert float(eig["total_expected_eig"]) > 0.0


def test_eig_ranked_list_is_sorted(analysis: dict[str, Any]) -> None:
    ranked = analysis["eig_engine"]["eig_ranked_list"]
    eig_values = [float(r["expected_information_gain"]) for r in ranked]
    assert eig_values == sorted(eig_values, reverse=True)
    for r in ranked:
        assert r["rank"] >= 1


def test_top_priority_experiment_eig_is_maximum(analysis: dict[str, Any]) -> None:
    ranked = analysis["eig_engine"]["eig_ranked_list"]
    top = analysis["eig_engine"]["top_priority"]
    # Top priority must be the highest EIG item in the list
    assert float(top["expected_information_gain"]) == float(ranked[0]["expected_information_gain"])
    assert float(top["expected_information_gain"]) > 0.05


# ---------------------------------------------------------------------------
# Part O.8 — Part G: Mechanism Evolution Engine
# ---------------------------------------------------------------------------


def test_mechanism_evolution_structure(analysis: dict[str, Any]) -> None:
    me = analysis["mechanism_evolution"]
    assert "mechanism_evolution_records" in me
    assert "lineage_records" in me
    assert len(me["mechanism_evolution_records"]) == 2
    assert len(me["lineage_records"]) == 2


def test_mechanism_variants_proposed(analysis: dict[str, Any]) -> None:
    me = analysis["mechanism_evolution"]
    total_variants = int(me["total_variants_proposed"])
    assert total_variants >= 2
    for record in me["mechanism_evolution_records"]:
        for variant in record["proposed_variants"]:
            assert "variant_id" in variant
            assert "evolution_type" in variant
            assert variant["evolution_type"] in {
                "SPECIALIZATION", "DECOMPOSITION", "MUTATION", "BRANCHING", "MERGING",
            }


# ---------------------------------------------------------------------------
# Part O.9 — Part H: Knowledge Synthesis
# ---------------------------------------------------------------------------


def test_knowledge_synthesis_structure(analysis: dict[str, Any]) -> None:
    ks = analysis["knowledge_synthesis"]
    required = {
        "institutional_lessons_learned",
        "contradiction_registry",
        "evidence_atlas",
        "failure_atlas",
        "scientific_principle_registry",
        "research_maturity_report",
        "knowledge_evolution_report",
    }
    assert required.issubset(ks.keys())
    assert len(ks["institutional_lessons_learned"]) >= 2
    assert len(ks["scientific_principle_registry"]) >= 1


def test_lessons_have_required_fields(analysis: dict[str, Any]) -> None:
    for lesson in analysis["knowledge_synthesis"]["institutional_lessons_learned"]:
        assert "lesson_id" in lesson
        assert "title" in lesson
        assert "description" in lesson
        assert 0.0 <= float(lesson["confidence"]) <= 1.0


# ---------------------------------------------------------------------------
# Part O.10 — Part I: Research Economics
# ---------------------------------------------------------------------------


def test_research_economics_structure(analysis: dict[str, Any]) -> None:
    econ = analysis["research_economics"]
    assert "research_economics_dashboard" in econ
    assert "cost_benefit_analysis" in econ
    assert "research_investment_priority" in econ
    assert len(econ["cost_benefit_analysis"]) >= 3
    for item in econ["cost_benefit_analysis"]:
        assert item["recommendation"] in {"APPROVE", "DEFER"}


# ---------------------------------------------------------------------------
# Part O.11 — Part J: Research Scheduler
# ---------------------------------------------------------------------------


def test_research_scheduler_structure(analysis: dict[str, Any]) -> None:
    sched = analysis["scheduler"]
    assert "daily_agenda" in sched
    assert "weekly_agenda" in sched
    assert "research_campaign_plan" in sched
    assert "scheduler_policy" in sched
    assert len(sched["daily_agenda"]) >= 3
    assert len(sched["weekly_agenda"]) == 5


# ---------------------------------------------------------------------------
# Part O.12 — Part K: Dashboards
# ---------------------------------------------------------------------------


def test_ten_dashboards_present(analysis: dict[str, Any]) -> None:
    required = {
        "research_dashboard",
        "mechanism_dashboard",
        "failure_dashboard",
        "experiment_dashboard",
        "feature_dashboard",
        "dataset_dashboard",
        "confidence_dashboard",
        "knowledge_dashboard",
        "research_queue_dashboard",
        "promotion_pipeline_dashboard",
    }
    assert required.issubset(analysis["dashboards"].keys())
    for name in required:
        assert "tiles" in analysis["dashboards"][name]
        assert len(analysis["dashboards"][name]["tiles"]) > 0


def test_promotion_pipeline_has_no_approved(analysis: dict[str, Any]) -> None:
    tiles = {t[0]: t[1] for t in analysis["dashboards"]["promotion_pipeline_dashboard"]["tiles"]}
    assert tiles.get("APPROVED_ALPHA", 0) == 0


# ---------------------------------------------------------------------------
# Part O.13 — Report emission
# ---------------------------------------------------------------------------


def test_report_emission(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = emit_program2_reports(analysis, repo_root=root)
        assert "final_report" in paths
        assert "eig_engine" in paths
        assert "knowledge_synthesis" in paths
        assert "research_director" in paths
        assert Path(paths["final_report"]).exists()
        assert Path(paths["eig_engine"]).exists()


def test_lab_schemas_emitted(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        emit_program2_reports(analysis, repo_root=root)
        schema_dir = root / "schemas" / "institutional-alpha-research-laboratory"
        assert schema_dir.exists()
        files = list(schema_dir.glob("*.schema.json"))
        assert len(files) >= 9


# ---------------------------------------------------------------------------
# Part O.14 — End-to-end campaign
# ---------------------------------------------------------------------------


def test_campaign_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for d in [
            "data/ikros/graph",
            "data/ikros/registries/research",
            "data/ikros/registries/experiments",
            "data/ikros/orchestrator/campaigns",
            "data/ikros/orchestrator/audit",
            "data/ikros/orchestrator/reports",
            "data/ikros/memory/t1-episodic",
            "data/ikros/memory/t4-institutional",
        ]:
            (root / d).mkdir(parents=True)

        result = run_program2_research_laboratory_campaign(root)

        assert result["mechanisms_under_research"] == 2
        assert result["approved_alpha_count"] == 0
        assert int(result["experiments_designed"]) >= 5
        assert float(result["total_eig_available"]) > 0.0
        assert int(result["dashboard_count"]) == 10
        assert isinstance(result["campaign_id"], str)
