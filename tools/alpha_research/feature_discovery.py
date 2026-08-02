"""Compatibility helpers for Phase G feature-discovery artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pandas as pd

from tools.alpha_research.reporting import write_json, write_markdown

PHASE_G_FEATURE_DISCOVERY_DIR = Path("11-research") / "phase-g" / "feature-discovery"
PHASE_G_FEATURE_DISCOVERY_ANALYSIS = (
    PHASE_G_FEATURE_DISCOVERY_DIR / "feature_discovery_analysis.json"
)
PHASE_G_FEATURE_DISCOVERY_KNOWLEDGE = (
    PHASE_G_FEATURE_DISCOVERY_DIR / "feature_discovery_knowledge.json"
)
PHASE_G_FEATURE_DISCOVERY_VALIDATION = (
    PHASE_G_FEATURE_DISCOVERY_DIR / "feature_discovery_validation_report.json"
)


def _build_conditioned_frame() -> pd.DataFrame:
    raise RuntimeError("Conditioned frame generation is unavailable in this repository snapshot.")


def prepare_phase_g_feature_discovery_artifacts(
    *,
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis = cast(
        dict[str, Any],
        json.loads((repo_root / PHASE_G_FEATURE_DISCOVERY_ANALYSIS).read_text(encoding="utf-8")),
    )
    knowledge = cast(
        dict[str, Any],
        json.loads((repo_root / PHASE_G_FEATURE_DISCOVERY_KNOWLEDGE).read_text(encoding="utf-8")),
    )
    validation = cast(
        dict[str, Any],
        json.loads((repo_root / PHASE_G_FEATURE_DISCOVERY_VALIDATION).read_text(encoding="utf-8")),
    )
    analysis_path = output_dir / "feature_discovery_analysis.json"
    knowledge_path = output_dir / "feature_discovery_knowledge.json"
    validation_path = output_dir / "feature_discovery_validation_report.json"
    write_json(analysis_path, analysis)
    write_json(knowledge_path, knowledge)
    write_json(validation_path, validation)
    return {
        "analysis": analysis,
        "paths": {
            "analysis": str(analysis_path),
            "knowledge": str(knowledge_path),
            "validation": str(validation_path),
        },
    }


def emit_feature_discovery_reports(
    *,
    output_dir: Path,
    analysis: dict[str, Any],
    campaign_result: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix_json = output_dir / "regime_feature_matrix.json"
    final_md = output_dir / "FEATURE_DISCOVERY_FINAL_CAMPAIGN_REPORT.md"
    write_json(matrix_json, analysis.get("regime_feature_matrix", []))
    write_markdown(
        final_md,
        (
            "# Feature Discovery Final Report\n\n"
            f"State: {campaign_result['report']['lifecycle_state']}"
        ),
    )
    return {
        "regime_feature_matrix_json": str(matrix_json),
        "final_report_markdown": str(final_md),
    }
