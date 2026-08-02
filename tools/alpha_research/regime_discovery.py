"""Reporting helpers for Phase G Campaign 0002 regime discovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

PHASE_G_REGIME_DISCOVERY_ANALYSIS = (
    Path("11-research") / "phase-g" / "regime-discovery" / "regime_discovery_analysis.json"
)


def load_phase_g_regime_discovery_analysis(repo_root: Path) -> dict[str, Any]:
    analysis_path = repo_root / PHASE_G_REGIME_DISCOVERY_ANALYSIS
    return cast(dict[str, Any], json.loads(analysis_path.read_text(encoding="utf-8")))


def emit_regime_discovery_reports(
    *,
    repo_root: Path,
    output_dir: Path,
    analysis: dict[str, Any],
    campaign_result: dict[str, Any],
) -> dict[str, str]:
    del repo_root
    output_dir.mkdir(parents=True, exist_ok=True)
    taxonomy = analysis["accepted_taxonomy"]
    methods = analysis["candidate_methods"]
    historical_atlas = analysis["historical_atlas"]
    utility_test = analysis["utility_test"]
    validation_metrics = analysis["validation_metrics"]

    method_report_json = output_dir / "method_comparison_report.json"
    method_report_md = output_dir / "METHOD_COMPARISON_REPORT.md"
    regime_catalogue_json = output_dir / "regime_catalogue.json"
    regime_catalogue_md = output_dir / "REGIME_CATALOGUE.md"
    transition_json = output_dir / "transition_matrix.json"
    transition_md = output_dir / "TRANSITION_MATRIX.md"
    historical_json = output_dir / "historical_regime_atlas.json"
    historical_md = output_dir / "HISTORICAL_REGIME_ATLAS.md"
    validation_md = output_dir / "VALIDATION_REPORT.md"
    confidence_md = output_dir / "CONFIDENCE_REPORT.md"
    interpretation_md = output_dir / "ECONOMIC_INTERPRETATION_GUIDE.md"
    final_report_md = output_dir / "REGIME_DISCOVERY_FINAL_CAMPAIGN_REPORT.md"

    write_json(method_report_json, methods)
    write_json(regime_catalogue_json, taxonomy["regimes"])
    write_json(transition_json, taxonomy["transition_matrix"])
    write_json(historical_json, historical_atlas)

    method_rows = [
        [
            item["name"],
            item["executed_on_frozen_stack"],
            item["determinism_score"],
            item["interpretability_score"],
            item["cost_score"],
            item["stability_score"],
            item["utility_score"],
            item["institutional_suitability_score"],
            item["decision"],
        ]
        for item in methods
    ]
    write_markdown(
        method_report_md,
        f"""
# Method Comparison Report

## Decision

Accepted methodology: **{taxonomy["name"]}**

{markdown_table(
    [
        "Method",
        "Executed",
        "Determinism",
        "Interpretability",
        "Cost",
        "Stability",
        "Utility",
        "Institutional Fit",
        "Decision",
    ],
    method_rows,
)}

## Accepted rationale

{taxonomy["name"]} improved return separation to
**{utility_test["macro_overlay_return_spread"]:.6f}**
versus **{utility_test["volatility_baseline_return_spread"]:.6f}** for the volatility-only
baseline and **{utility_test["trend_volatility_return_spread"]:.6f}** for the trend/volatility
partition, while preserving **{taxonomy["stability"]:.4f}** transition stability.
""",
    )

    regime_rows = [
        [
            regime["institutional_name"],
            regime["label"],
            regime["count"],
            regime["avg_future_return"],
            regime["hit_rate"],
            regime["avg_volatility"],
            regime["avg_macro_pressure"],
        ]
        for regime in taxonomy["regimes"]
    ]
    write_markdown(
        regime_catalogue_md,
        f"""
# Regime Catalogue

## Accepted taxonomy

{markdown_table(
    [
        "Institutional Name",
        "Label",
        "Count",
        "Avg 5D Return",
        "Hit Rate",
        "Avg Volatility",
        "Avg Macro Pressure",
    ],
    regime_rows,
)}

## Notes

The taxonomy is minimal enough to stay interpretable while still separating
high-utility and low-utility research states.
""",
    )

    transition_headers = ["From"] + [regime["label"] for regime in taxonomy["regimes"]]
    transition_rows: list[list[object]] = []
    for regime in taxonomy["regimes"]:
        row = [regime["label"]]
        row.extend(
            taxonomy["transition_matrix"][regime["label"]][other["label"]]
            for other in taxonomy["regimes"]
        )
        transition_rows.append(row)
    write_markdown(
        transition_md,
        f"""
# Transition Matrix

Stability score: **{taxonomy["stability"]:.4f}**

{markdown_table(transition_headers, transition_rows)}
""",
    )

    historical_rows = [
        [
            item["window_id"],
            item["label"],
            item["dominant_regime"],
            item["avg_future_return"],
            item["dominant_share"],
        ]
        for item in historical_atlas
    ]
    write_markdown(
        historical_md,
        f"""
# Historical Regime Atlas

{markdown_table(
    ["Window", "Label", "Dominant Regime", "Avg 5D Return", "Dominant Share"],
    historical_rows,
)}
""",
    )

    write_markdown(
        validation_md,
        f"""
# Validation Report

## Utility test

1. Volatility-only return spread: `{utility_test["volatility_baseline_return_spread"]:.6f}`
2. Trend/volatility return spread: `{utility_test["trend_volatility_return_spread"]:.6f}`
3. Accepted taxonomy return spread: `{utility_test["macro_overlay_return_spread"]:.6f}`
4. Volatility-only hit-rate spread: `{utility_test["volatility_baseline_hit_spread"]:.6f}`
5. Accepted taxonomy hit-rate spread: `{utility_test["macro_overlay_hit_spread"]:.6f}`

## Statistical synthesis

1. p-value proxy: `{validation_metrics["p_value"]:.4f}`
2. effect size: `{validation_metrics["effect_size"]:.4f}`
3. consistency score: `{validation_metrics["consistency_score"]:.4f}`
4. sharpe degradation: `{validation_metrics["sharpe_degradation"]:.4f}`
5. overfitting index: `{validation_metrics["overfitting_index"]:.4f}`
""",
    )

    hypothesis_confidence = campaign_result["hypothesis"]["confidence"]["overall"]
    write_markdown(
        confidence_md,
        f"""
# Confidence Report

## Hypothesis outcome

- Hypothesis state: **{campaign_result["hypothesis"]["lifecycle_state"]}**
- Overall confidence: **{hypothesis_confidence:.4f}**
- Assessment ID: `{campaign_result["assessment_ids"]["hypothesis"]}`

## Confidence posture

Confidence improved because the accepted taxonomy increased validation separation,
improved hypothesis ranking utility, and remained economically interpretable. Confidence
is capped by the absence of full multi-campaign replication.
""",
    )

    interpretation_sections = []
    for regime in taxonomy["regimes"]:
        interpretation_sections.append(
            "\n".join(
                [
                    f"## {regime['institutional_name']}",
                    "",
                    f"- **Rationale:** {regime['economic_rationale']}",
                    f"- **Mechanics:** {regime['market_mechanics']}",
                    f"- **Participants:** {regime['dominant_participants']}",
                    f"- **Backdrop:** {regime['typical_backdrop']}",
                    f"- **Liquidity:** {regime['liquidity_profile']}",
                    f"- **Volatility:** {regime['volatility_profile']}",
                    f"- **Transition triggers:** {', '.join(regime['transition_triggers'])}",
                    f"- **Failure modes:** {', '.join(regime['failure_modes'])}",
                ]
            )
        )
    write_markdown(
        interpretation_md,
        "# Economic Interpretation Guide\n\n" + "\n\n".join(interpretation_sections),
    )

    write_markdown(
        final_report_md,
        f"""
# Regime Discovery Final Campaign Report

## Outcome

Campaign 0002 completed with the recommendation to adopt **{taxonomy["name"]}** as the
institutional state model for future AFRP research.

## Registered conclusion

- Campaign ID: `{campaign_result["campaign_id"]}`
- Completion report: `{campaign_result["report"]["report_id"]}`
- Research question: `{campaign_result["research_question"]["ikros_id"]}`
- Hypothesis: `{campaign_result["hypothesis"]["ikros_id"]}`
- Experiment: `{campaign_result["experiment"]["ikros_id"]}`
- Validation: `{campaign_result["validation_summary"]["validation_id"]}`
- Conclusion: `{campaign_result["validation_summary"]["conclusion_id"]}`

## ARB recommendation

{campaign_result["validation_summary"]["arb_recommendation"]}
""",
    )

    return {
        "method_comparison_json": str(method_report_json),
        "method_comparison_markdown": str(method_report_md),
        "regime_catalogue_json": str(regime_catalogue_json),
        "regime_catalogue_markdown": str(regime_catalogue_md),
        "transition_matrix_json": str(transition_json),
        "transition_matrix_markdown": str(transition_md),
        "historical_atlas_json": str(historical_json),
        "historical_atlas_markdown": str(historical_md),
        "validation_report_markdown": str(validation_md),
        "confidence_report_markdown": str(confidence_md),
        "economic_interpretation_markdown": str(interpretation_md),
        "final_report_markdown": str(final_report_md),
    }
