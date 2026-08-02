"""Tests for Discovery Cycle 4 Institutional Market Observability & Data Expansion Program."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc4_observability_program import run_dc4_observability_campaign
from tools.alpha_research.institutional_observability import prepare_dc4_observability_artifacts


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc4_observability_artifacts()


def test_dc4_analysis_runs(analysis: dict[str, Any]) -> None:
    arb = analysis["arb_recommendation"]
    assert analysis["phase"] == "DISCOVERY_CYCLE_4"
    assert int(analysis["mechanism_count"]) == 12
    assert int(analysis["state_variables_identified"]) > 50
    assert int(analysis["missing_datasets"]) >= 15
    assert arb["promote_now"] is False
    assert arb["validate_additional_now"] is False


def test_dc4_observability_scores(analysis: dict[str, Any]) -> None:
    scores = analysis["observability_scores"]
    assert len(scores) == 12
    for s in scores:
        assert 0.0 <= float(s["observation_completeness"]) <= 1.0
        assert 0.0 <= float(s["scientific_confidence_ceiling"]) <= 1.0
        assert isinstance(s["blocked_by_observability"], bool)


def test_dc4_all_mechanisms_blocked(analysis: dict[str, Any]) -> None:
    scores = analysis["observability_scores"]
    blocked = [s for s in scores if s["blocked_by_observability"]]
    assert len(blocked) == int(analysis["mechanisms_blocked_by_observability"])
    assert len(blocked) == 11
    ready = [s for s in scores if not s["blocked_by_observability"]]
    assert len(ready) == 1
    assert ready[0]["mechanism_type"] == "cross_asset_transition"


def test_dc4_dataset_catalogue(analysis: dict[str, Any]) -> None:
    datasets = analysis["dataset_gap_catalogue"]
    assert len(datasets) >= 15
    priorities = {d["priority"] for d in datasets}
    assert "P1" in priorities
    p1_ids = {d["dataset_id"] for d in datasets if d["priority"] == "P1"}
    assert "DS-001" in p1_ids  # VIX
    assert "DS-003" in p1_ids  # TED Spread


def test_dc4_market_state_domains(analysis: dict[str, Any]) -> None:
    domains = analysis["market_state_domains"]
    assert len(domains) >= 10
    domain_names = {d["name"] for d in domains}
    assert "Macro" in domain_names
    assert "Volatility" in domain_names
    assert "Flows" in domain_names


def test_dc4_feature_expansion_roadmap(analysis: dict[str, Any]) -> None:
    roadmap = analysis["feature_expansion_roadmap"]
    assert len(roadmap) >= 5
    families = {f["feature_family"] for f in roadmap}
    assert "stress_features_v1" in families
    assert "vol_features_v2" in families
    total_features = sum(len(f["new_features"]) for f in roadmap)
    assert total_features >= 20


def test_dc4_campaign_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src = Path("11-research/discovery-cycle-3/institutional-alpha-discovery-program")
        dst = root / "11-research" / "discovery-cycle-3" / "institutional-alpha-discovery-program"
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.glob("*.json"):
            shutil.copy(f, dst / f.name)
        shutil.copytree(str(Path("data/ikros")), str(root / "data" / "ikros"))
        result = run_dc4_observability_campaign(root)
        assert int(result["mechanism_count"]) == 12
        assert int(result["state_variables_identified"]) > 50
        assert int(result["missing_datasets"]) >= 15
        assert result["promote_now"] is False
        assert len(result["immediate_free_acquisitions"]) >= 3
