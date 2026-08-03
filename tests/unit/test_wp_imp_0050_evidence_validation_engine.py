"""Tests for Generation 2 WP-IMP-0050 Institutional Alpha Evidence Engine."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest

from tools.alpha_research.institutional_alpha_evidence_validation_engine import (
    emit_wp_imp_0050_reports,
    prepare_wp_imp_0050_artifacts,
)
from tools.alpha_research.wp_imp_0050_evidence_validation_engine import (
    run_wp_imp_0050_campaign,
)


@pytest.fixture(scope="module")
def analysis() -> dict[str, Any]:
    return prepare_wp_imp_0050_artifacts()


def test_wp0050_analysis_runs(analysis: dict[str, Any]) -> None:
    assert analysis["program"] == "GENERATION_2_WP_IMP_0050"
    assert analysis["no_promotion"] is True
    assert len(analysis["mechanism_dossiers"]) == 2


def test_wp0050_pipeline_shape(analysis: dict[str, Any]) -> None:
    for dossier in analysis["mechanism_dossiers"]:
        pipeline = dossier["pipeline"]
        stages = [step["stage"] for step in pipeline]
        assert "Evidence Sufficiency Check" in stages
        assert "Observation Completeness Check" in stages
        assert "Confidence Update" in stages
        assert "ARB Recommendation" in stages


def test_wp0050_scorecard_fields(analysis: dict[str, Any]) -> None:
    for scorecard in analysis["validation_scorecards"]:
        assert 0.0 <= float(scorecard["scientific_validity"]) <= 1.0
        assert 0.0 <= float(scorecard["economic_plausibility"]) <= 1.0
        assert 0.0 <= float(scorecard["cross_asset_consistency"]) <= 1.0
        assert 0.0 <= float(scorecard["institutional_confidence"]) <= 1.0
        assert "proxy_dependence" in scorecard
        assert "statistical_quality" in scorecard


def test_wp0050_observation_gate_enforced(analysis: dict[str, Any]) -> None:
    blocked = set(analysis["blocked_on_observation_completeness"])
    assert "IKROS-ALPHA-DC3-20260802-0009" in blocked
    dossiers = {d["alpha_id"]: d for d in analysis["mechanism_dossiers"]}
    blocked_dossier = dossiers["IKROS-ALPHA-DC3-20260802-0009"]
    assert blocked_dossier["observation_check"]["status"] == "FAIL"
    halted = [
        step
        for step in blocked_dossier["pipeline"]
        if step["stage"] == "Scientific Validation"
    ]
    assert halted and halted[0]["status"] == "HALTED"


def test_wp0050_failure_dossiers(analysis: dict[str, Any]) -> None:
    by_alpha = {f["alpha_id"]: f["failures"] for f in analysis["failure_dossiers"]}
    assert "IKROS-ALPHA-DC3-20260802-0009" in by_alpha
    fail_classes = {entry["failure_class"] for entry in by_alpha["IKROS-ALPHA-DC3-20260802-0009"]}
    assert "Observation Failure" in fail_classes
    assert "Concept Drift" in fail_classes


def test_wp0050_confidence_reports(analysis: dict[str, Any]) -> None:
    for report in analysis["confidence_reports"]:
        assert 0.0 <= float(report["prior"]) <= 1.0
        assert 0.0 <= float(report["posterior"]) <= 1.0
        assert report["direction"] in {"INCREASE", "DECREASE", "STABLE"}


def test_wp0050_report_emission(analysis: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        paths = emit_wp_imp_0050_reports(analysis, repo_root=Path(tmp))
        assert "validation_scorecards" in paths
        assert "evidence_ledger" in paths
        assert "failure_dossiers" in paths
        assert Path(paths["validation_scorecards"]).exists()
        assert Path(paths["schemas_markdown"]).exists()


def test_wp0050_campaign_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src_phase4 = Path("11-research/discovery-cycle-3/phase-4-adaptive-alpha-validation")
        dst_phase4 = (
            root
            / "11-research"
            / "discovery-cycle-3"
            / "phase-4-adaptive-alpha-validation"
        )
        dst_phase4.mkdir(parents=True, exist_ok=True)
        for file_path in src_phase4.glob("*.json"):
            shutil.copy(file_path, dst_phase4 / file_path.name)

        src_phase5 = Path("11-research/discovery-cycle-3/phase-5-institutional-alpha-revision")
        dst_phase5 = (
            root
            / "11-research"
            / "discovery-cycle-3"
            / "phase-5-institutional-alpha-revision"
        )
        dst_phase5.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            src_phase5 / "dc3_phase5_revision_analysis.json",
            dst_phase5 / "dc3_phase5_revision_analysis.json",
        )

        shutil.copytree("data/ikros", root / "data" / "ikros")

        result = run_wp_imp_0050_campaign(root)
        assert int(result["mechanisms_processed"]) == 2
        assert result["promote_any_alpha_now"] is False
        assert "IKROS-ALPHA-DC3-20260802-0009" in result["blocked_on_observation_completeness"]
