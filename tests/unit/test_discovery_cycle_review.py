from __future__ import annotations

from pathlib import Path

from tools.alpha_research.discovery_cycle_review import run_discovery_cycle_1_review


def test_discovery_cycle_1_review_generates_reports_and_recommendation(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]

    result = run_discovery_cycle_1_review(
        repo_root,
        output_dir=tmp_path / "reports",
    )

    analysis = result["analysis"]
    assert analysis["review_recommendation"]["direction"] == "Cross-Asset Transition Ecology"
    assert analysis["campaign_summary"][0]["campaign_id"] == "0001"
    assert len(analysis["campaign_summary"]) == 7
    assert len(analysis["success_catalogue"]) >= 5
    assert len(analysis["knowledge_gaps"]) >= 5
    assert Path(result["report_paths"]["institutional_knowledge_review"]).is_file()
    assert Path(result["report_paths"]["research_roadmap_v2"]).is_file()
    assert Path(result["report_paths"]["result"]).is_file()
