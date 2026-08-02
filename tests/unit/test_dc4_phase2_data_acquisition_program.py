"""Tests for Discovery Cycle 4 Phase 2 dataset acquisition prioritization."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc4_phase2_data_acquisition_program import run_dc4_phase2_campaign
from tools.alpha_research.institutional_data_acquisition_prioritization import (
    _build_dataset_priorities,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return _build_dataset_priorities(Path("."))


def test_dc4_phase2_analysis_shape(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DISCOVERY_CYCLE_4_PHASE_2"
    assert int(analysis["dataset_count"]) == 20
    assert len(analysis["dataset_priority_registry"]) == 20
    assert len(analysis["top_5_datasets"]) == 5


def test_dc4_phase2_tier_distribution(analysis: dict[str, Any]) -> None:
    tier_counts = analysis["tier_counts"]
    assert int(tier_counts["Tier 1"]) >= 5
    assert int(tier_counts["Tier 4"]) >= 4
    assert int(tier_counts["Tier 5"]) >= 2


def test_dc4_phase2_priority_registry_scores(analysis: dict[str, Any]) -> None:
    registry = analysis["dataset_priority_registry"]
    for item in registry:
        assert 0.0 <= float(item["overall_institutional_priority"]) <= 1.0
        assert 0.0 <= float(item["roi_score"]) <= 1.0
        assert item["tier"] in {"Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"}


def test_dc4_phase2_core_tiers(analysis: dict[str, Any]) -> None:
    registry = {item["dataset_id"]: item for item in analysis["dataset_priority_registry"]}
    assert registry["DS-001"]["tier"] == "Tier 1"
    assert registry["DS-003"]["tier"] == "Tier 1"
    assert registry["DS-007"]["tier"] == "Tier 1"
    assert registry["DS-005"]["tier"] == "Tier 4"
    assert registry["DS-020"]["tier"] == "Tier 5"


def test_dc4_phase2_dependency_graph(analysis: dict[str, Any]) -> None:
    graph = analysis["acquisition_dependency_graph"]
    assert len(graph["nodes"]) == 20
    assert len(graph["edges"]) >= 20
    assert len(graph["high_leverage_datasets"]) >= 3


def test_dc4_phase2_work_package_plan(analysis: dict[str, Any]) -> None:
    work_packages = analysis["data_foundation_v2_work_package_plan"]
    assert len(work_packages) == 5
    assert work_packages[0]["wp_id"] == "DF2-WP-001"
    assert "DS-001" in work_packages[0]["datasets"]
    assert work_packages[-1]["wp_id"] == "DF2-WP-005"


def test_dc4_phase2_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src_dirs = [
            (
                Path("11-research/discovery-cycle-4/institutional-market-observability"),
                root / "11-research" / "discovery-cycle-4" / "institutional-market-observability",
            ),
            (
                Path("11-research/discovery-cycle-2/research-program-f-phase1"),
                root / "11-research" / "discovery-cycle-2" / "research-program-f-phase1",
            ),
            (
                Path("11-research/discovery-cycle-3/institutional-alpha-discovery-program"),
                root
                / "11-research"
                / "discovery-cycle-3"
                / "institutional-alpha-discovery-program",
            ),
        ]
        for src, dst in src_dirs:
            dst.mkdir(parents=True, exist_ok=True)
            for file_path in src.glob("*.json"):
                shutil.copy(file_path, dst / file_path.name)
        shutil.copytree(str(Path("data/ikros")), str(root / "data" / "ikros"))
        result = run_dc4_phase2_campaign(root)
        assert int(result["dataset_count"]) == 20
        assert len(result["top_5_datasets"]) == 5
        assert len(result["tier_1_immediate"]) >= 5
        assert result["no_acquisition_performed"] is True
        assert result["no_validation_resumed"] is True
