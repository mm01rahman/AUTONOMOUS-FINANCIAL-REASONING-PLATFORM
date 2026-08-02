from __future__ import annotations

from pathlib import Path

from tools.alpha_research.phase_g import run_phase_g_failure_analysis_campaign


def test_phase_g_failure_analysis_campaign_completes_and_preserves_retained_set(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]

    result = run_phase_g_failure_analysis_campaign(
        repo_root,
        base_dir=tmp_path / "ikros",
        output_dir=tmp_path / "reports",
    )

    assert result["report"]["lifecycle_state"] == "COMPLETED"
    assert result["research_question"]["lifecycle_state"] == "ANSWERED"
    assert result["hypothesis"]["lifecycle_state"] == "INCONCLUSIVE"
    assert result["experiment"]["lifecycle_state"] == "REVIEWED"
    assert len(result["failure_analysis_summary"]["retained_hypotheses"]) == 3
    assert result["failure_analysis_summary"]["recommended_experiment_count"] == 6
    assert Path(result["report_paths"]["alpha_failure_atlas_markdown"]).is_file()
    assert Path(result["report_paths"]["campaign_result"]).is_file()
