from __future__ import annotations

from pathlib import Path

from tools.alpha_research.phase_g import run_phase_g_macro_alpha_campaign


def test_phase_g_macro_alpha_campaign_completes_and_rejects_baseline(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]

    result = run_phase_g_macro_alpha_campaign(repo_root, base_dir=tmp_path / "ikros")

    assert result["report"]["lifecycle_state"] == "COMPLETED"
    assert result["progress"]["completed"] == 11
    assert result["research_question"]["lifecycle_state"] == "ANSWERED"
    assert result["hypothesis"]["lifecycle_state"] == "REFUTED"
    assert result["experiment"]["lifecycle_state"] == "REVIEWED"
    assert result["alpha_candidate"]["promotion_status"] == "REJECTED"
    assert result["assessment_ids"]["hypothesis"] is not None
    assert result["assessment_ids"]["candidate"] is not None
    assert result["validation_summary"]["promotion_decision"] == "REJECTED"
