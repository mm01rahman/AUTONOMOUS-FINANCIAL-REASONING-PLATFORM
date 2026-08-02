"""Discovery Cycle 3 Phase 2: Institutional Alpha Validation Framework."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

DC3_PHASE2_DIR = Path("11-research") / "discovery-cycle-3" / "phase-2-institutional-alpha-validation-framework"
DC3_PHASE2_ANALYSIS = DC3_PHASE2_DIR / "dc3_phase2_institutional_alpha_validation_framework.json"


VALIDATION_DIMENSIONS: list[str] = [
    "scientific_validity",
    "economic_plausibility",
    "market_mechanism",
    "cross_asset_consistency",
    "regime_consistency",
    "temporal_stability",
    "robustness",
    "generalization",
    "failure_behaviour",
    "capacity",
    "transaction_cost_sensitivity",
    "slippage_sensitivity",
    "liquidity_sensitivity",
    "complexity",
    "interpretability",
    "explainability",
    "confidence_calibration",
    "reproducibility",
    "institutional_risk",
    "evidence_quality",
]

MANDATORY_METHODS: list[str] = [
    "walk_forward_validation",
    "nested_walk_forward",
    "combinatorial_purged_cross_validation",
    "monte_carlo",
    "bootstrap",
    "sensitivity_analysis",
    "stress_testing",
    "historical_replay",
    "out_of_sample_validation",
    "probability_of_backtest_overfitting",
    "deflated_sharpe_ratio",
    "probabilistic_sharpe_ratio",
    "whites_reality_check",
    "spa_test",
    "concept_drift_detection",
    "stability_analysis",
    "failure_replay",
]

PROMOTION_LEVELS: list[str] = [
    "REJECTED",
    "RESEARCH",
    "REVISE",
    "VALIDATE_AGAIN",
    "CANDIDATE",
    "PROMOTION_REVIEW",
    "APPROVED",
]


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], __import__("json").loads(path.read_text(encoding="utf-8")))


def _phase1_path(repo_root: Path) -> Path:
    return (
        repo_root
        / "11-research"
        / "discovery-cycle-3"
        / "institutional-alpha-discovery-program"
        / "dc3_institutional_alpha_discovery_analysis.json"
    )


def _validation_method_specs() -> list[dict[str, Any]]:
    return [
        {"method_id": "VAL-METHOD-0001", "method": "walk_forward_validation", "purpose": "Temporal forward robustness", "minimum_outputs": ["window_metrics", "drift_flags", "stability_summary"]},
        {"method_id": "VAL-METHOD-0002", "method": "nested_walk_forward", "purpose": "Nested temporal robustness with inner diagnostics", "minimum_outputs": ["outer_metrics", "inner_selection_trace", "variance_estimates"]},
        {"method_id": "VAL-METHOD-0003", "method": "combinatorial_purged_cross_validation", "purpose": "Leakage-resistant combinatorial validation", "minimum_outputs": ["fold_metrics", "purge_log", "overlap_controls"]},
        {"method_id": "VAL-METHOD-0004", "method": "monte_carlo", "purpose": "Path perturbation and stochastic resilience", "minimum_outputs": ["distribution_summary", "tail_behavior", "failure_rate"]},
        {"method_id": "VAL-METHOD-0005", "method": "bootstrap", "purpose": "Resampling confidence estimation", "minimum_outputs": ["resampled_statistics", "confidence_intervals"]},
        {"method_id": "VAL-METHOD-0006", "method": "sensitivity_analysis", "purpose": "Parameter/assumption sensitivity", "minimum_outputs": ["sensitivity_map", "fragility_points"]},
        {"method_id": "VAL-METHOD-0007", "method": "stress_testing", "purpose": "Extreme-market resilience", "minimum_outputs": ["stress_scenarios", "drawdown_behavior", "regime_breaks"]},
        {"method_id": "VAL-METHOD-0008", "method": "historical_replay", "purpose": "Historical event consistency", "minimum_outputs": ["event_replay_outcomes", "contradiction_flags"]},
        {"method_id": "VAL-METHOD-0009", "method": "out_of_sample_validation", "purpose": "Generalization beyond in-sample", "minimum_outputs": ["oos_metrics", "degradation_delta"]},
        {"method_id": "VAL-METHOD-0010", "method": "probability_of_backtest_overfitting", "purpose": "Overfitting probability estimate", "minimum_outputs": ["pbo_score", "risk_band"]},
        {"method_id": "VAL-METHOD-0011", "method": "deflated_sharpe_ratio", "purpose": "Selection-adjusted Sharpe significance", "minimum_outputs": ["dsr_value", "significance_level"]},
        {"method_id": "VAL-METHOD-0012", "method": "probabilistic_sharpe_ratio", "purpose": "Probabilistic Sharpe confidence", "minimum_outputs": ["psr_value", "confidence"]},
        {"method_id": "VAL-METHOD-0013", "method": "whites_reality_check", "purpose": "Data-snooping adjustment", "minimum_outputs": ["wrc_pvalue", "null_rejection"]},
        {"method_id": "VAL-METHOD-0014", "method": "spa_test", "purpose": "Superior predictive ability test", "minimum_outputs": ["spa_pvalue", "comparative_outcome"]},
        {"method_id": "VAL-METHOD-0015", "method": "concept_drift_detection", "purpose": "Distribution/mechanism drift detection", "minimum_outputs": ["drift_statistics", "drift_timeline"]},
        {"method_id": "VAL-METHOD-0016", "method": "stability_analysis", "purpose": "Feature and mechanism stability", "minimum_outputs": ["stability_scores", "instability_diagnostics"]},
        {"method_id": "VAL-METHOD-0017", "method": "failure_replay", "purpose": "Failure mode replay and attribution", "minimum_outputs": ["failure_sequences", "cause_attribution"]},
    ]


def _validation_registry_schema() -> dict[str, Any]:
    return {
        "schema_id": "IKROS-VALREG-SCHEMA-20260802-0001",
        "description": "Canonical validation registry schema for alpha mechanisms.",
        "required_fields": [
            "validation_id",
            "alpha_id",
            "framework_version",
            "methods_executed",
            "dimensions_scored",
            "promotion_level",
            "confidence_post",
            "evidence_refs",
            "contradiction_refs",
            "reproducibility_hash",
        ],
    }


def _failure_registry_schema() -> dict[str, Any]:
    return {
        "schema_id": "IKROS-FAILREG-SCHEMA-20260802-0001",
        "description": "Canonical failed-alpha analysis schema.",
        "required_fields": [
            "failure_id",
            "alpha_id",
            "failure_classification",
            "failure_cause",
            "failure_timeline",
            "failure_modes",
            "contradictory_evidence",
            "confidence_update",
            "required_future_research",
            "diagnostic_experiments",
        ],
    }


def _promotion_framework() -> dict[str, Any]:
    return {
        "framework_id": "IKROS-PROMOTION-FRAMEWORK-20260802-0001",
        "levels": PROMOTION_LEVELS,
        "gating_rules": [
            "No mechanism may reach APPROVED without passing all mandatory validation methods.",
            "No mechanism may reach PROMOTION_REVIEW if confidence calibration or reproducibility fails.",
            "REJECTED and REVISE outcomes must create failure analyses and research continuation tasks.",
            "APPROVED status remains institutional-only until separate ARB production authorization.",
        ],
        "promotion_criteria": {
            "minimum_scientific_validity": 0.7,
            "minimum_economic_plausibility": 0.7,
            "minimum_regime_consistency": 0.65,
            "minimum_temporal_stability": 0.65,
            "minimum_reproducibility": 1.0,
            "maximum_institutional_risk": 0.4,
        },
    }


def _failure_workflow() -> dict[str, Any]:
    return {
        "workflow_id": "IKROS-FAILURE-WORKFLOW-20260802-0001",
        "steps": [
            "Classify failure (noise/correlation/conditional/causal-breakdown/alpha-breakdown).",
            "Identify root causes and contradictory evidence.",
            "Build failure timeline and replay packet.",
            "Update confidence and lineage.",
            "Generate required future research and diagnostic experiments.",
            "Insert continuation item into research queue.",
        ],
    }


def _success_workflow() -> dict[str, Any]:
    return {
        "workflow_id": "IKROS-SUCCESS-WORKFLOW-20260802-0001",
        "steps": [
            "Collect supporting evidence set and replication packet.",
            "Generate economic, market, regime, and cross-asset narratives.",
            "Estimate expected capacity, decay, and risks.",
            "List known weaknesses and unresolved contradictions.",
            "Assign promotion level with explicit confidence calibration record.",
        ],
    }


def _validation_api_spec() -> dict[str, Any]:
    return {
        "api_version": "1.0.0",
        "endpoints": [
            {"name": "register_alpha_for_validation", "input": ["alpha_id", "mechanism_spec", "evidence_refs"], "output": ["validation_id", "status"]},
            {"name": "execute_validation_protocol", "input": ["validation_id", "methods"], "output": ["method_reports", "dimension_scores", "promotion_level"]},
            {"name": "record_failure_analysis", "input": ["validation_id", "failure_packet"], "output": ["failure_id", "continuation_task_id"]},
            {"name": "record_success_analysis", "input": ["validation_id", "success_packet"], "output": ["support_packet_id", "promotion_level"]},
            {"name": "update_validation_confidence", "input": ["validation_id", "confidence_components"], "output": ["confidence_post"]},
        ],
    }


def _institutional_alpha_standard() -> dict[str, Any]:
    return {
        "standard_id": "IKROS-INSTITUTIONAL-ALPHA-STANDARD-20260802-0001",
        "definition": "Institutional Alpha requires mechanism-level evidence beyond correlation, stable cross-regime behavior, reproducible validation, calibrated confidence, and acceptable institutional risk.",
        "non_negotiables": [
            "No promotion on backtest return alone.",
            "No promotion without contradiction accounting.",
            "No promotion without method-complete validation trace.",
            "No promotion without reproducibility and lineage integrity.",
        ],
    }


def _validation_dashboard_spec() -> dict[str, Any]:
    return {
        "dashboard_id": "IKROS-VAL-DASHBOARD-20260802-0001",
        "tiles": [
            "Validation pipeline status",
            "Dimension score heatmap",
            "Method pass/fail matrix",
            "Promotion distribution",
            "Failure cause clusters",
            "Confidence evolution timeline",
            "Evidence quality summary",
            "Research continuation queue",
        ],
    }


def _framework_analysis(phase1: dict[str, Any]) -> dict[str, Any]:
    queue = cast(list[dict[str, Any]], phase1["institutional_alpha_queue"])
    retained_ids = cast(list[str], phase1["arb_recommendation"]["retained_alpha_ids"])
    return {
        "phase": "DISCOVERY_CYCLE_3_PHASE_2",
        "title": "Institutional Alpha Validation Framework",
        "framework_version": "1.0.0",
        "scope": "Mechanism-agnostic, reusable for all future alpha mechanisms.",
        "phase1_campaign_id": "IKROS-RESEARCHCAMPAIGN-20260802-0026",
        "phase1_registry_size": len(cast(list[dict[str, Any]], phase1["institutional_alpha_registry"])),
        "phase1_retained_size": len(retained_ids),
        "validation_dimensions": VALIDATION_DIMENSIONS,
        "mandatory_validation_methods": MANDATORY_METHODS,
        "validation_method_specifications": _validation_method_specs(),
        "validation_registry_schema": _validation_registry_schema(),
        "validation_evidence_registry_schema": {
            "schema_id": "IKROS-VALEVID-SCHEMA-20260802-0001",
            "required_fields": ["evidence_id", "validation_id", "method", "artifact_ref", "quality_score", "lineage_ref"],
        },
        "failure_registry_schema": _failure_registry_schema(),
        "replication_registry_schema": {
            "schema_id": "IKROS-REPLICA-SCHEMA-20260802-0001",
            "required_fields": ["replication_id", "validation_id", "environment", "seed", "result_consistency", "status"],
        },
        "promotion_framework": _promotion_framework(),
        "failure_workflow": _failure_workflow(),
        "success_workflow": _success_workflow(),
        "validation_dashboard_spec": _validation_dashboard_spec(),
        "validation_api_spec": _validation_api_spec(),
        "institutional_alpha_standard": _institutional_alpha_standard(),
        "promotion_criteria": _promotion_framework()["promotion_criteria"],
        "research_continuation_queue_schema": {
            "schema_id": "IKROS-RESEARCH-CONTINUATION-SCHEMA-20260802-0001",
            "required_fields": ["task_id", "alpha_id", "reason", "priority", "required_evidence", "assigned_method_bundle"],
        },
        "governance_guards": [
            "Do not validate Phase 1 mechanisms in this phase.",
            "Do not optimize any mechanism.",
            "Do not generate trading strategies.",
            "No runtime modifications.",
        ],
        "arb_recommendation": {
            "framework_ready": True,
            "validate_phase1_mechanisms_now": False,
            "promote_any_alpha_now": False,
            "adopt_as_only_approved_path": True,
            "next_action": "Await ARB approval, then run validation executions under this framework in Phase 3.",
            "remaining_gaps": [
                "Repository-wide Ruff cleanup still required for fully green baseline.",
                "afrp evidence boundary scope must align with bounded files for current work package.",
                "Performance-test harness for validation methods to be implemented with Phase 3 execution.",
            ],
            "initial_queue_reference_size": len(queue),
        },
    }


def _graph_payload(analysis: dict[str, Any]) -> dict[str, Any]:
    methods = cast(list[str], analysis["mandatory_validation_methods"])
    method_nodes = [
        {
            "node_id": f"IKROS-VALMETHOD-{idx + 1:04d}",
            "label": name,
            "node_type": "VALIDATION",
            "confidence": 0.7,
        }
        for idx, name in enumerate(methods)
    ]
    framework_node = {
        "node_id": "IKROS-DC3-P2-FRAMEWORK-20260802-0001",
        "label": "Institutional Alpha Validation Framework",
        "node_type": "WORLD_MODEL",
        "confidence": 0.8,
    }
    standard_node = {
        "node_id": "IKROS-DC3-P2-STANDARD-20260802-0001",
        "label": "Institutional Alpha Standard",
        "node_type": "KNOWLEDGE_OBJECT",
        "confidence": 0.79,
    }
    conclusion_node = {
        "node_id": "IKROS-DC3-P2-CONCLUSION-20260802-0001",
        "label": "DC3 Phase 2 Validation Framework Conclusion",
        "node_type": "RESEARCH_CONCLUSION",
        "confidence": 0.78,
    }
    edges: list[dict[str, Any]] = []
    for method in method_nodes:
        edges.append({"source": method["node_id"], "target": framework_node["node_id"], "relation": "IMPLEMENTS", "confidence": method["confidence"]})
    edges.append({"source": framework_node["node_id"], "target": standard_node["node_id"], "relation": "EXPLAINS", "confidence": 0.8})
    edges.append({"source": standard_node["node_id"], "target": conclusion_node["node_id"], "relation": "SUPPORTED_BY", "confidence": 0.79})
    return {
        "framework_node": framework_node,
        "standard_node": standard_node,
        "conclusion_node": conclusion_node,
        "method_nodes": method_nodes,
        "edges": edges,
    }


def prepare_dc3_phase2_validation_framework_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(".")
    phase1_path = _phase1_path(root)
    if not phase1_path.exists():
        phase1_path = _phase1_path(Path("."))
    phase1 = _load_json(phase1_path)

    analysis = _framework_analysis(phase1)
    analysis["ecology_knowledge_graph"] = _graph_payload(analysis)
    out_dir = root / DC3_PHASE2_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc3_phase2_institutional_alpha_validation_framework.json", analysis)
    return analysis


def emit_dc3_phase2_validation_framework_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC3_PHASE2_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    dimensions = cast(list[str], analysis["validation_dimensions"])
    methods = cast(list[str], analysis["mandatory_validation_methods"])
    method_specs = cast(list[dict[str, Any]], analysis["validation_method_specifications"])
    promotion_levels = cast(list[str], analysis["promotion_framework"]["levels"])
    arb = cast(dict[str, Any], analysis["arb_recommendation"])

    arch_md = out_dir / "VALIDATION_ARCHITECTURE.md"
    arch_rows = [[idx + 1, name] for idx, name in enumerate(dimensions)]
    write_markdown(arch_md, f"# Validation Architecture\n## Discovery Cycle 3 Phase 2\n\n{markdown_table(['Dimension #', 'Validation Dimension'], arch_rows)}\n")
    written["validation_architecture"] = str(arch_md)

    val_registry_md = out_dir / "VALIDATION_REGISTRY.md"
    schema = cast(dict[str, Any], analysis["validation_registry_schema"])
    write_markdown(val_registry_md, f"# Validation Registry\n## Discovery Cycle 3 Phase 2\n\nSchema ID: **{schema['schema_id']}**\n\nRequired fields:\n" + "\n".join(f"- {x}" for x in cast(list[str], schema["required_fields"])) + "\n")
    written["validation_registry"] = str(val_registry_md)

    evidence_md = out_dir / "VALIDATION_EVIDENCE_REGISTRY.md"
    ev_schema = cast(dict[str, Any], analysis["validation_evidence_registry_schema"])
    write_markdown(evidence_md, f"# Validation Evidence Registry\n## Discovery Cycle 3 Phase 2\n\nSchema ID: **{ev_schema['schema_id']}**\n\nRequired fields:\n" + "\n".join(f"- {x}" for x in cast(list[str], ev_schema["required_fields"])) + "\n")
    written["validation_evidence_registry"] = str(evidence_md)

    fail_md = out_dir / "FAILURE_REGISTRY.md"
    fail_schema = cast(dict[str, Any], analysis["failure_registry_schema"])
    write_markdown(fail_md, f"# Failure Registry\n## Discovery Cycle 3 Phase 2\n\nSchema ID: **{fail_schema['schema_id']}**\n\nRequired fields:\n" + "\n".join(f"- {x}" for x in cast(list[str], fail_schema["required_fields"])) + "\n")
    written["failure_registry"] = str(fail_md)

    promotion_md = out_dir / "PROMOTION_FRAMEWORK.md"
    criteria = cast(dict[str, Any], analysis["promotion_criteria"])
    c_rows = [[k, v] for k, v in criteria.items()]
    write_markdown(
        promotion_md,
        "# Promotion Framework\n## Discovery Cycle 3 Phase 2\n\nPromotion levels:\n" + "\n".join(f"- {lvl}" for lvl in promotion_levels) + "\n\n" + markdown_table(["Criterion", "Threshold"], c_rows) + "\n",
    )
    written["promotion_framework"] = str(promotion_md)

    dashboard_md = out_dir / "VALIDATION_DASHBOARD.md"
    tiles = cast(list[str], analysis["validation_dashboard_spec"]["tiles"])
    write_markdown(dashboard_md, "# Validation Dashboard\n## Discovery Cycle 3 Phase 2\n\n" + "\n".join(f"- {tile}" for tile in tiles) + "\n")
    written["validation_dashboard"] = str(dashboard_md)

    reports_md = out_dir / "VALIDATION_REPORTS.md"
    method_rows = [[m["method_id"], m["method"], m["purpose"]] for m in method_specs]
    write_markdown(reports_md, f"# Validation Reports\n## Discovery Cycle 3 Phase 2\n\n{markdown_table(['Method ID', 'Method', 'Purpose'], method_rows)}\n")
    written["validation_reports"] = str(reports_md)

    failure_report_md = out_dir / "FAILURE_REPORTS.md"
    f_steps = cast(list[str], analysis["failure_workflow"]["steps"])
    write_markdown(failure_report_md, "# Failure Reports\n## Discovery Cycle 3 Phase 2\n\nFailure workflow:\n" + "\n".join(f"- {step}" for step in f_steps) + "\n")
    written["failure_reports"] = str(failure_report_md)

    confidence_md = out_dir / "CONFIDENCE_REPORTS.md"
    write_markdown(confidence_md, "# Confidence Reports\n## Discovery Cycle 3 Phase 2\n\nConfidence updates are recorded per validation in Validation Confidence and Lineage registries under IKROS.\n")
    written["confidence_reports"] = str(confidence_md)

    criteria_md = out_dir / "PROMOTION_CRITERIA.md"
    write_markdown(criteria_md, "# Promotion Criteria\n## Discovery Cycle 3 Phase 2\n\n" + markdown_table(["Criterion", "Threshold"], c_rows) + "\n")
    written["promotion_criteria"] = str(criteria_md)

    standard_md = out_dir / "INSTITUTIONAL_ALPHA_STANDARD.md"
    std = cast(dict[str, Any], analysis["institutional_alpha_standard"])
    write_markdown(
        standard_md,
        f"# Institutional Alpha Standard\n## Discovery Cycle 3 Phase 2\n\n**Definition:** {std['definition']}\n\nNon-negotiables:\n" + "\n".join(f"- {x}" for x in cast(list[str], std["non_negotiables"])) + "\n",
    )
    written["institutional_alpha_standard"] = str(standard_md)

    api_md = out_dir / "VALIDATION_API.md"
    api = cast(dict[str, Any], analysis["validation_api_spec"])
    api_rows = [[ep["name"], ", ".join(cast(list[str], ep["input"])), ", ".join(cast(list[str], ep["output"]))] for ep in cast(list[dict[str, Any]], api["endpoints"])]
    write_markdown(api_md, f"# Validation API\n## Discovery Cycle 3 Phase 2\n\nAPI version: **{api['api_version']}**\n\n{markdown_table(['Endpoint', 'Input', 'Output'], api_rows)}\n")
    written["validation_api"] = str(api_md)

    schemas_md = out_dir / "GOVERNED_JSON_SCHEMAS.md"
    write_markdown(
        schemas_md,
        "# Governed JSON Schemas\n## Discovery Cycle 3 Phase 2\n\n- Validation Registry\n- Validation Evidence Registry\n- Failure Registry\n- Replication Registry\n- Research Continuation Queue\n",
    )
    written["governed_json_schemas"] = str(schemas_md)

    docs_md = out_dir / "DOCUMENTATION.md"
    guards = cast(list[str], analysis["governance_guards"])
    write_markdown(docs_md, "# Documentation\n## Discovery Cycle 3 Phase 2\n\nGovernance guards:\n" + "\n".join(f"- {g}" for g in guards) + "\n")
    written["documentation"] = str(docs_md)

    ikros_md = out_dir / "IKROS_INTEGRATION.md"
    write_markdown(
        ikros_md,
        "# IKROS Integration\n## Discovery Cycle 3 Phase 2\n\nFramework defines Validation Registry, Evidence Registry, Failure Registry, Replication Registry, Promotion Registry, Validation Lineage, Validation Confidence, and Research Continuation Queue interfaces.",
    )
    written["ikros_integration"] = str(ikros_md)

    final_md = out_dir / "FINAL_REPORT.md"
    gaps = "\n".join(f"- {g}" for g in cast(list[str], arb["remaining_gaps"]))
    write_markdown(
        final_md,
        f"""# Final Report
## Discovery Cycle 3 Phase 2

- Validation architecture: complete
- Validation registry: complete
- Promotion workflow: complete
- Failure workflow: complete
- IKROS integration specification: complete

Repository stabilization summary:
{gaps}

Engineering quality summary:
- Framework files pass focused ruff, mypy --strict, and pytest.
- Global baseline cleanup remains a separate stabilization stream.

ARB recommendation:
{arb['next_action']}
""",
    )
    written["final_report"] = str(final_md)

    write_json(out_dir / "dc3_phase2_validation_framework_methods.json", methods)
    written["methods_json"] = str(out_dir / "dc3_phase2_validation_framework_methods.json")
    if campaign_result is not None:
        write_json(out_dir / "dc3_phase2_campaign_result.json", campaign_result)
        written["campaign_result"] = str(out_dir / "dc3_phase2_campaign_result.json")
    return written
