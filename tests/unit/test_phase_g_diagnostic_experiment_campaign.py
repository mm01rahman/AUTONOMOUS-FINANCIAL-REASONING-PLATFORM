from __future__ import annotations

from pathlib import Path

from tools.alpha_research.phase_g import run_phase_g_diagnostic_experiment_campaign


def test_phase_g_diagnostic_experiment_campaign_completes_and_recommends_next_steps(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]

    result = run_phase_g_diagnostic_experiment_campaign(
        repo_root,
        base_dir=tmp_path / "ikros",
        output_dir=tmp_path / "reports",
    )

    assert result["report"]["lifecycle_state"] == "COMPLETED"
    assert result["research_question"]["lifecycle_state"] == "ANSWERED"
    assert result["hypothesis"]["lifecycle_state"] == "INCONCLUSIVE"
    assert result["experiment"]["lifecycle_state"] == "REVIEWED"
    assert len(result["diagnostic_summary"]["executed_experiments"]) == 6
    assert result["diagnostic_summary"]["return_for_validation"] == [
        "IKROS-HYP-20260802-0401",
        "IKROS-HYP-20260802-0405",
    ]
    assert result["diagnostic_summary"]["remain_in_testing"] == [
        "IKROS-HYP-20260802-0408"
    ]
    assert result["diagnostic_summary"]["rejected"] == []
    assert Path(result["report_paths"]["diagnostic_experiment_report_markdown"]).is_file()
    assert Path(result["report_paths"]["campaign_result"]).is_file()
