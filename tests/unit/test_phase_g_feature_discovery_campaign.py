from __future__ import annotations

from pathlib import Path

from tools.alpha_research.phase_g import run_phase_g_feature_discovery_campaign


def test_phase_g_feature_discovery_campaign_completes_and_registers_catalogue(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]

    result = run_phase_g_feature_discovery_campaign(
        repo_root,
        base_dir=tmp_path / "ikros",
        output_dir=tmp_path / "reports",
    )

    assert result["report"]["lifecycle_state"] == "COMPLETED"
    assert result["progress"]["completed"] == 11
    assert result["research_question"]["lifecycle_state"] == "ANSWERED"
    assert result["hypothesis"]["lifecycle_state"] == "SUPPORTED"
    assert result["experiment"]["lifecycle_state"] == "REVIEWED"
    assert result["assessment_ids"]["hypothesis"] is not None
    assert (
        result["validation_summary"]["approved_catalogue"]
        == "Institutional Regime-Conditioned Feature Catalogue v1"
    )
    assert result["validation_summary"]["approved_feature_count"] == 12
    assert Path(result["report_paths"]["final_report_markdown"]).is_file()
    assert Path(result["report_paths"]["campaign_result"]).is_file()
