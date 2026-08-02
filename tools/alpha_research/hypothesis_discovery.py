"""Compatibility helpers for Phase G hypothesis-discovery artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import write_json, write_markdown

PHASE_G_HYPOTHESIS_DISCOVERY_DIR = Path("11-research") / "phase-g" / "hypothesis-discovery"
PHASE_G_HYPOTHESIS_DISCOVERY_ANALYSIS = (
    PHASE_G_HYPOTHESIS_DISCOVERY_DIR / "hypothesis_discovery_analysis.json"
)
PHASE_G_HYPOTHESIS_DISCOVERY_CATALOGUE = (
    PHASE_G_HYPOTHESIS_DISCOVERY_DIR / "institutional_alpha_hypothesis_catalogue_v1.json"
)
PHASE_G_HYPOTHESIS_DISCOVERY_KNOWLEDGE = (
    PHASE_G_HYPOTHESIS_DISCOVERY_DIR / "hypothesis_discovery_knowledge.json"
)
PHASE_G_HYPOTHESIS_DISCOVERY_VALIDATION = (
    PHASE_G_HYPOTHESIS_DISCOVERY_DIR / "expected_validation_matrix.json"
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
HYPOTHESIS_BLUEPRINTS = cast(
    list[dict[str, Any]],
    json.loads((_REPO_ROOT / PHASE_G_HYPOTHESIS_DISCOVERY_CATALOGUE).read_text(encoding="utf-8")),
)


def prepare_phase_g_hypothesis_discovery_artifacts(
    *,
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis = cast(
        dict[str, Any],
        json.loads((repo_root / PHASE_G_HYPOTHESIS_DISCOVERY_ANALYSIS).read_text(encoding="utf-8")),
    )
    knowledge = cast(
        dict[str, Any],
        json.loads(
            (repo_root / PHASE_G_HYPOTHESIS_DISCOVERY_KNOWLEDGE).read_text(encoding="utf-8")
        ),
    )
    validation = cast(
        list[dict[str, Any]],
        json.loads(
            (repo_root / PHASE_G_HYPOTHESIS_DISCOVERY_VALIDATION).read_text(encoding="utf-8")
        ),
    )

    analysis_path = output_dir / "hypothesis_discovery_analysis.json"
    knowledge_path = output_dir / "hypothesis_discovery_knowledge.json"
    validation_path = output_dir / "hypothesis_discovery_validation_report.json"
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


def emit_hypothesis_discovery_reports(
    *,
    output_dir: Path,
    analysis: dict[str, Any],
    campaign_result: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cards_json = output_dir / "hypothesis_cards.json"
    cards_md = output_dir / "HYPOTHESIS_CARDS.md"
    final_md = output_dir / "HYPOTHESIS_DISCOVERY_FINAL_CAMPAIGN_REPORT.md"
    write_json(cards_json, analysis.get("hypothesis_cards", []))
    write_markdown(cards_md, "# Hypothesis Cards\n")
    write_markdown(
        final_md,
        (
            "# Hypothesis Discovery Final Report\n\n"
            f"State: {campaign_result['report']['lifecycle_state']}"
        ),
    )
    return {
        "hypothesis_cards_json": str(cards_json),
        "hypothesis_cards_markdown": str(cards_md),
        "final_report_markdown": str(final_md),
    }
