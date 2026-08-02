"""Tests for Discovery Cycle 3 Phase 3 Institutional Alpha Taxonomy & Consolidation Program."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc3_phase3_alpha_taxonomy import (
    run_dc3_phase3_alpha_taxonomy_campaign,
)
from tools.alpha_research.institutional_alpha_taxonomy import (
    prepare_dc3_phase3_taxonomy_artifacts,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc3_phase3_taxonomy_artifacts()


def test_phase3_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DISCOVERY_CYCLE_3_PHASE_3"
    assert int(analysis["mechanism_count"]) == 12
    assert int(analysis["family_count"]) == 7


def test_phase3_taxonomy_families(analysis: dict[str, Any]) -> None:
    taxonomy = analysis["institutional_alpha_taxonomy"]
    assert len(taxonomy) == 7
    ids = {f["family_id"] for f in taxonomy}
    assert "FAM-001" in ids
    assert "FAM-007" in ids
    for fam in taxonomy:
        assert "definition" in fam
        assert "economic_rationale" in fam
        assert 0.0 <= float(fam["confidence"]) <= 1.0


def test_phase3_similarity_matrix(analysis: dict[str, Any]) -> None:
    sim_matrix = analysis["similarity_matrix"]
    # 12 mechanisms → C(12,2) = 66 pairs
    assert len(sim_matrix) == 66
    for row in sim_matrix:
        assert 0.0 <= float(row["overall_similarity"]) <= 1.0


def test_phase3_mechanism_clusters(analysis: dict[str, Any]) -> None:
    clusters = analysis["mechanism_clusters"]
    total_ids: list[str] = []
    for ids in clusters.values():
        total_ids.extend(ids)
    assert len(total_ids) == 12
    assert len(clusters) == 7


def test_phase3_redundancy_analysis(analysis: dict[str, Any]) -> None:
    redundancy = analysis["redundancy_analysis"]
    assert "near_duplicates" in redundancy
    assert "merge_candidates" in redundancy
    assert int(redundancy["independent_count"]) >= 0


def test_phase3_priority_matrix(analysis: dict[str, Any]) -> None:
    priority = analysis["research_priority_matrix"]
    assert len(priority) == 7
    assert priority[0]["rank"] == 1
    bands = {r["priority_band"] for r in priority}
    assert "P1" in bands


def test_phase3_campaign_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Seed discovery-cycle-3 registry (needed by engine)
        import shutil
        src = Path("11-research/discovery-cycle-3/institutional-alpha-discovery-program")
        dst = root / "11-research" / "discovery-cycle-3" / "institutional-alpha-discovery-program"
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.glob("*.json"):
            shutil.copy(f, dst / f.name)
        # Seed ikros data
        ikros_src = Path("data/ikros")
        ikros_dst = root / "data" / "ikros"
        shutil.copytree(str(ikros_src), str(ikros_dst))
        result = run_dc3_phase3_alpha_taxonomy_campaign(root)
        assert int(result["family_count"]) == 7
        assert int(result["mechanism_count"]) == 12
        assert int(result["validation_batches"]) == 3
        assert int(result["graph_nodes_created"]) >= 0
