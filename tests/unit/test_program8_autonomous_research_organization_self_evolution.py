"""Tests for Generation 5 / Program 8 autonomous research self-evolution."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.autonomous_research_organization_self_evolution import (
    emit_program8_reports,
    prepare_program8_artifacts,
)
from tools.alpha_research.program8_autonomous_research_organization_self_evolution import (
    run_program8_autonomous_research_organization,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_program8_artifacts()


def test_program8_top_level_keys(analysis: dict[str, Any]) -> None:
    required = {
        "program",
        "meta_research_registry",
        "self_evaluation_registry",
        "improvement_registry",
        "meta_learning_registry",
        "organizational_memory_registry",
        "roadmap_registry",
        "productivity_registry",
        "autonomous_arb_registry",
        "continuous_improvement_loop_registry",
        "executive_dashboards",
        "institutional_organization_registry",
        "schemas",
    }
    assert required.issubset(analysis.keys())


def test_improvement_priority_is_sorted(analysis: dict[str, Any]) -> None:
    priorities = [float(row["priority"]) for row in analysis["improvement_registry"]]
    assert priorities == sorted(priorities, reverse=True)
    assert priorities[0] >= priorities[-1]


def test_arb_registry_has_governed_decisions(analysis: dict[str, Any]) -> None:
    decisions = [row["decision"] for row in analysis["autonomous_arb_registry"]]
    assert set(decisions).issubset({"APPROVE", "DEFER"})
    assert len(decisions) == len(analysis["improvement_registry"])


def test_non_executing_guardrails(analysis: dict[str, Any]) -> None:
    summary = analysis["institutional_organization_registry"]
    assert summary["non_executing"] is True
    assert summary["broker_connections"] == 0
    assert summary["trade_execution_calls"] == 0


def test_schema_catalog_complete(analysis: dict[str, Any]) -> None:
    assert {
        "meta-research.schema.json",
        "organizational-review.schema.json",
        "roadmap.schema.json",
        "improvement-plan.schema.json",
        "institutional-playbook.schema.json",
        "executive-review.schema.json",
    }.issubset(analysis["schemas"].keys())


def test_prepare_program8_is_deterministic() -> None:
    first = prepare_program8_artifacts()
    second = prepare_program8_artifacts()
    assert first["improvement_registry"] == second["improvement_registry"]
    assert first["self_evaluation_registry"] == second["self_evaluation_registry"]
    assert (
        first["institutional_organization_registry"]
        == second["institutional_organization_registry"]
    )


def test_report_emission_writes_artifacts(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = emit_program8_reports(analysis, repo_root=root)
        assert Path(paths["final_report"]).exists()
        assert Path(paths["meta_research_registry"]).exists()
        assert Path(paths["schema:meta-research.schema.json"]).exists()


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
        result = run_program8_autonomous_research_organization(root)
        assert str(result["top_priority_improvement"]).startswith("IMP-")
        assert int(result["approved_improvements"]) >= 1
        assert float(result["overall_scientific_health"]) > 0.0
