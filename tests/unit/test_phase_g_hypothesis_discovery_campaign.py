from __future__ import annotations

from pathlib import Path

from tools.alpha_research.phase_g import run_phase_g_hypothesis_discovery_campaign


def test_phase_g_hypothesis_discovery_campaign_completes_and_registers_catalogue(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]

    result = run_phase_g_hypothesis_discovery_campaign(
        repo_root,
        base_dir=tmp_path / "ikros",
        output_dir=tmp_path / "reports",
    )

    assert result["report"]["lifecycle_state"] == "COMPLETED"
    assert result["progress"]["completed"] == 8
    assert result["research_question"]["lifecycle_state"] == "ANSWERED"
    assert result["hypothesis"]["lifecycle_state"] == "TESTING"
    assert result["experiment"]["lifecycle_state"] == "REVIEWED"
    assert (
        result["catalogue_summary"]["hypothesis_catalogue"]
        == "Institutional Alpha Hypothesis Catalogue v1"
    )
    assert len(result["catalogue_summary"]["recommended_hypotheses"]) == 5
    assert Path(result["report_paths"]["final_report_markdown"]).is_file()
    assert Path(result["report_paths"]["campaign_result"]).is_file()
