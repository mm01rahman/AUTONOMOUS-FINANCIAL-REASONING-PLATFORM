"""Tests for Discovery Cycle 3 Phase 5 Institutional Alpha Revision Program."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.dc3_phase5_revision_program import (
    run_dc3_phase5_revision_campaign,
)
from tools.alpha_research.institutional_alpha_revision import (
    _ARB_OUTCOME_RANK,
    prepare_dc3_phase5_revision_artifacts,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_dc3_phase5_revision_artifacts()


def test_phase5_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["phase"] == "DISCOVERY_CYCLE_3_PHASE_5"
    assert int(analysis["mechanisms_revised"]) == 2
    assert analysis["promote_now"] is False
    assert analysis["execute_batch_2_now"] is False


def test_phase5_revision_analyses_present(analysis: dict[str, Any]) -> None:
    analyses = analysis["revision_analyses"]
    assert "safe_haven_migration" in analyses
    assert "decision_cascade" in analyses
    for a in analyses.values():
        assert a["arb_decision"] in _ARB_OUTCOME_RANK
        assert len(a["assumptions_failed"]) >= 2
        assert len(a["assumptions_supported"]) >= 2
        assert len(a["experiment_backlog"]) >= 3


def test_phase5_confidence_updates(analysis: dict[str, Any]) -> None:
    conf = analysis["confidence_updates"]
    shm = conf["safe_haven_migration"]
    dc = conf["decision_cascade"]
    assert float(shm["phase5_posterior"]) > float(shm["phase4_posterior"])
    assert float(dc["phase5_posterior"]) < float(dc["phase4_posterior"])


def test_phase5_arb_decisions(analysis: dict[str, Any]) -> None:
    analyses = analysis["revision_analyses"]
    assert analyses["safe_haven_migration"]["arb_decision"] == "READY_FOR_REVALIDATION"
    assert analyses["decision_cascade"]["arb_decision"] == "RESEARCH"


def test_phase5_experiment_backlog(analysis: dict[str, Any]) -> None:
    backlog = analysis["combined_experiment_backlog"]
    assert len(backlog) >= 6
    ids = [e["experiment_id"] for e in backlog]
    assert "EXP-SHM-001" in ids
    assert "EXP-DC-001" in ids


def test_phase5_dataset_gaps(analysis: dict[str, Any]) -> None:
    gaps = analysis["combined_dataset_gaps"]
    assert len(gaps) >= 5
    priorities = {g["priority"] for g in gaps}
    assert "HIGH" in priorities


def test_phase5_campaign_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Seed Phase 4 artifacts
        src_p4 = Path("11-research/discovery-cycle-3/phase-4-adaptive-alpha-validation")
        dst_p4 = root / "11-research" / "discovery-cycle-3" / "phase-4-adaptive-alpha-validation"
        dst_p4.mkdir(parents=True, exist_ok=True)
        for f in src_p4.glob("*.json"):
            shutil.copy(f, dst_p4 / f.name)
        shutil.copytree(str(Path("data/ikros")), str(root / "data" / "ikros"))
        result = run_dc3_phase5_revision_campaign(root)
        assert int(result["mechanisms_revised"]) == 2
        assert result["promote_now"] is False
        assert "IKROS-ALPHA-DC3-20260802-0006" in str(result["mechanisms_ready_for_revalidation"])
        assert "IKROS-ALPHA-DC3-20260802-0009" in str(result["mechanisms_research"])
