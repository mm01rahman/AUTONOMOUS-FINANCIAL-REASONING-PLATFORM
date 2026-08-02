from __future__ import annotations

from pathlib import Path

from tools.alpha_research.phase_g import run_phase_g_scientific_validation_campaign


def test_phase_g_scientific_validation_campaign_completes_and_partitions_hypotheses(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]

    result = run_phase_g_scientific_validation_campaign(
        repo_root,
        base_dir=tmp_path / "ikros",
        output_dir=tmp_path / "reports",
    )

    assert result["report"]["lifecycle_state"] == "COMPLETED"
    assert result["research_question"]["lifecycle_state"] == "ANSWERED"
    assert result["hypothesis"]["lifecycle_state"] == "SUPPORTED"
    assert result["experiment"]["lifecycle_state"] == "REVIEWED"
    assert len(result["validation_summary"]["rejected_hypotheses"]) == 2
    assert len(result["validation_summary"]["further_research_hypotheses"]) == 3
    assert result["validation_summary"]["promoted_hypotheses"] == []
    assert Path(result["report_paths"]["final_report_markdown"]).is_file()
    assert Path(result["report_paths"]["campaign_result"]).is_file()
