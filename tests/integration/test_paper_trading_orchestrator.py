"""Integration tests for Phase D orchestrator and reports."""

from __future__ import annotations

import json
from pathlib import Path

from tools.paper_trading.orchestrator import PaperTradingConfig, PaperTradingOrchestrator


def test_orchestrator_generates_phase_d_artifacts(tmp_path: Path) -> None:
    config = PaperTradingConfig(
        iterations=8, poll_interval_seconds=60, output_dir=str(tmp_path), random_seed=123
    )
    result = PaperTradingOrchestrator(config).run()

    assert Path(result.dashboard.json_path).exists()
    assert Path(result.dashboard.markdown_path).exists()
    assert Path(result.dashboard.html_path).exists()
    assert Path(result.decision_log_path).exists()
    assert Path(result.reports.daily_json).exists()
    assert Path(result.reports.weekly_json).exists()
    assert Path(result.reports.monthly_json).exists()
    assert Path(result.reports.runtime_json).exists()
    assert Path(result.reports.learning_json).exists()


def test_orchestrator_decision_log_is_jsonl(tmp_path: Path) -> None:
    config = PaperTradingConfig(
        iterations=5, poll_interval_seconds=60, output_dir=str(tmp_path), random_seed=7
    )
    result = PaperTradingOrchestrator(config).run()
    lines = Path(result.decision_log_path).read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 5
    first = json.loads(lines[0])
    assert "market_snapshot" in first
    assert "execution_simulation" in first


def test_orchestrator_deterministic_checksum(tmp_path: Path) -> None:
    config1 = PaperTradingConfig(
        iterations=6, poll_interval_seconds=60, output_dir=str(tmp_path / "a"), random_seed=42
    )
    config2 = PaperTradingConfig(
        iterations=6, poll_interval_seconds=60, output_dir=str(tmp_path / "b"), random_seed=42
    )

    run1 = PaperTradingOrchestrator(config1).run()
    run2 = PaperTradingOrchestrator(config2).run()
    assert run1.decision_log_checksum == run2.decision_log_checksum
