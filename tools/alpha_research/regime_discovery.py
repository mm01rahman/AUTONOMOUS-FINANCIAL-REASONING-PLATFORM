"""Compatibility helpers for Phase G regime-discovery artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import write_json, write_markdown

PHASE_G_REGIME_DISCOVERY_DIR = Path("11-research") / "phase-g" / "regime-discovery"
PHASE_G_REGIME_DISCOVERY_ANALYSIS = PHASE_G_REGIME_DISCOVERY_DIR / "regime_discovery_analysis.json"


def load_phase_g_regime_discovery_analysis(repo_root: Path) -> dict[str, Any]:
    analysis_path = repo_root / PHASE_G_REGIME_DISCOVERY_ANALYSIS
    return cast(dict[str, Any], json.loads(analysis_path.read_text(encoding="utf-8")))


def emit_regime_discovery_reports(
    *,
    repo_root: Path | None = None,
    output_dir: Path,
    analysis: dict[str, Any],
    campaign_result: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix_json = output_dir / "regime_transition_matrix.json"
    final_md = output_dir / "REGIME_DISCOVERY_FINAL_CAMPAIGN_REPORT.md"
    write_json(matrix_json, analysis.get("regime_transition_matrix", []))
    write_markdown(
        final_md,
        f"# Regime Discovery Final Report\n\nState: {campaign_result['report']['lifecycle_state']}",
    )
    return {
        "regime_transition_matrix_json": str(matrix_json),
        "final_report_markdown": str(final_md),
    }
