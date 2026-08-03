"""Tests for Data Foundation V2 Phase 1 institutional market data infrastructure."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any, cast

import pytest

from tools.data_foundation.engine import build_data_foundation_v2_tier1
from tools.data_foundation.phase1_program import run_data_foundation_v2_phase1


@pytest.fixture(scope="module")
def summary() -> dict[str, Any]:
    return build_data_foundation_v2_tier1(Path("."))


def test_data_foundation_summary_shape(summary: dict[str, Any]) -> None:
    assert summary["phase"] == "DATA_FOUNDATION_V2_PHASE_1"
    assert int(summary["dataset_count"]) == 13
    assert len(summary["supported_datasets"]) == 13
    assert "DS-PUB-021" in summary["supported_datasets"]


def test_data_foundation_registry_and_quality(summary: dict[str, Any]) -> None:
    registry = cast(list[dict[str, Any]], summary["dataset_registry"])
    quality = cast(list[dict[str, Any]], summary["quality_registry"])
    assert len(registry) == 13
    assert len(quality) == 13
    ds001 = next(item for item in registry if item["dataset_id"] == "DS-001")
    assert float(ds001["quality_score"]) > 0.70
    assert float(ds001["confidence_score"]) > 0.60


def test_data_foundation_registries_exist(summary: dict[str, Any]) -> None:
    report_paths = cast(dict[str, str], summary["report_paths"])
    assert "dataset_registry" in report_paths
    assert "quality_dashboard" in report_paths
    assert "coverage_dashboard" in report_paths
    assert "arb_recommendation" in report_paths
    assert int(summary["proxy_dependence_reduction"]) >= 1


def test_data_foundation_observation_and_gaps(summary: dict[str, Any]) -> None:
    observations = cast(list[dict[str, Any]], summary["observation_registry"])
    commercial = cast(list[str], summary["remaining_commercial_only_gaps"])
    assert len(observations) == 12
    assert "DS-005" in commercial
    assert "DS-016" in commercial


def test_data_foundation_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shutil.copytree(str(Path("data/ikros")), str(root / "data" / "ikros"))
        result = run_data_foundation_v2_phase1(root)
        assert int(result["dataset_count"]) == 13
        assert int(result["covered_variable_count"]) >= 10
        assert result["no_runtime_changes"] is True
        assert result["no_broker_connectivity"] is True
        assert result["no_alpha_validation"] is True
