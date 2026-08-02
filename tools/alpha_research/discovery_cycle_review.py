"""Phase H institutional review for Discovery Cycle 1."""

# ruff: noqa: E501

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

import yaml

from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

PHASE_H_DISCOVERY_CYCLE_1_DIR = (
    Path("11-research") / "phase-h" / "discovery-cycle-1-review"
)


def prepare_discovery_cycle_1_review(
    *,
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    campaign_inputs = _load_campaign_inputs(repo_root)
    registries = _load_registry_state(repo_root)
    confidence = _load_confidence_state(repo_root)
    graph = _load_graph_state(repo_root)
    memory = _load_memory_state(repo_root)

    promoted_features = cast(
        list[dict[str, Any]],
        campaign_inputs["feature"]["promoted_feature_registry"],
    )
    rejected_features = cast(
        list[dict[str, Any]],
        campaign_inputs["feature"]["rejected_feature_registry"],
    )
    validation_rows = cast(
        list[dict[str, Any]],
        campaign_inputs["scientific"]["hypothesis_validations"],
    )
    failure_retained = cast(
        list[dict[str, Any]],
        campaign_inputs["failure"]["retained_hypotheses"],
    )
    diagnostic_recommendations = cast(
        list[dict[str, Any]],
        campaign_inputs["diagnostic"]["recommendation_matrix"],
    )
    diagnostic_experiments = cast(
        list[dict[str, Any]],
        campaign_inputs["diagnostic"]["diagnostic_experiments"],
    )
    regimes = cast(
        list[dict[str, Any]],
        campaign_inputs["regime_catalogue"],
    )

    success_catalogue = [
        {
            "theme": "Canonical regime taxonomy",
            "finding": "Institutional Six-State Overlay Taxonomy v1 is now the canonical AFRP market-state model.",
            "supporting_evidence": "Campaign 0002 accepted six regimes with 0.7801 stability and persistent transition structure.",
            "institutional_status": "INSTITUTIONAL_KNOWLEDGE",
        },
        {
            "theme": "Governed feature catalogue",
            "finding": f"Campaign 0003 promoted {len(promoted_features)} regime-conditioned features and identified 12 cross-regime anchors that survive conditioning.",
            "supporting_evidence": "The promoted set is dominated by return anchors, volatility/trend context, and bounded interaction terms.",
            "institutional_status": "INSTITUTIONAL_KNOWLEDGE",
        },
        {
            "theme": "Hypothesis generation discipline",
            "finding": "Campaign 0004 narrowed the institutional hypothesis catalogue to five validation-worthy hypotheses out of eight generated candidates.",
            "supporting_evidence": "Three lower-priority hypotheses were held back before costly validation, preserving governance discipline.",
            "institutional_status": "INSTITUTIONAL_KNOWLEDGE",
        },
        {
            "theme": "Diagnostic value of governed follow-up",
            "finding": "Campaigns 0006 and 0007 reduced uncertainty materially without changing any hypothesis definition or resorting to optimization.",
            "supporting_evidence": "Two retained hypotheses returned to validation readiness, while one remained in testing due to unresolved data gaps.",
            "institutional_status": "INSTITUTIONAL_KNOWLEDGE",
        },
        {
            "theme": "Bull-trend persistence and macro-transition follow-through",
            "finding": "The most durable signals in Discovery Cycle 1 live in bull_trend and macro_transition rather than in macro-only or crisis-only framing.",
            "supporting_evidence": "H0401 and H0405 survived scientific validation and improved under diagnostic segmentation; H0408 stayed directionally positive but underpowered.",
            "institutional_status": "INSTITUTIONAL_KNOWLEDGE",
        },
    ]

    failure_catalogue = [
        {
            "finding": "Macro-only alpha baseline",
            "campaign": "0001",
            "status": "DISPROVEN",
            "evidence": "Alpha candidate rejected with negative walk-forward Sharpe, zero positive fold ratio, and no promotable edge.",
        },
        {
            "finding": "Liquidation-pressure bear continuation (H0402)",
            "campaign": "0005",
            "status": "DISPROVEN",
            "evidence": "Rejected after governed validation because the expected sign did not hold out-of-sample.",
        },
        {
            "finding": "Crisis safe-haven breakout convexity (H0404)",
            "campaign": "0005",
            "status": "DISPROVEN",
            "evidence": "Rejected after governed validation because crisis continuation did not preserve expected direction.",
        },
        {
            "finding": "Standalone macro_pressure as a predictive feature",
            "campaign": "0003",
            "status": "DISPROVEN",
            "evidence": "Rejected as a direct predictive feature and retained only as regime-defining context.",
        },
        {
            "finding": "Unsegmented crisis alpha",
            "campaign": "0002-0005",
            "status": "FAILED_MECHANISM",
            "evidence": "Crisis_dislocation is real as a state label but poor as a direct alpha environment because volatility dominates signal reliability.",
        },
    ]

    contradiction_map = [
        {
            "contradiction": "Macro pressure matters, but macro-only alpha fails.",
            "source_campaigns": "0001, 0002, 0003",
            "resolution_status": "RESOLVED",
            "review_conclusion": "Macro pressure is informative as a regime/context variable, not as a standalone predictive edge.",
        },
        {
            "contradiction": "Crisis episodes look economically important, but crisis-specific alpha did not survive validation.",
            "source_campaigns": "0002, 0004, 0005",
            "resolution_status": "RESOLVED",
            "review_conclusion": "Crisis_dislocation is institutionally important for taxonomy and risk framing, but too unstable for direct continuation alpha in Cycle 1.",
        },
        {
            "contradiction": "H0408 stayed positive in sign, but still did not justify re-validation.",
            "source_campaigns": "0005, 0006, 0007",
            "resolution_status": "OPEN",
            "review_conclusion": "The handoff thesis may be real, but sparse episode coverage and missing intraday sequencing still block institutional confidence.",
        },
        {
            "contradiction": "DXY and rates spillovers appear important, but DXY return was rejected as a standalone feature.",
            "source_campaigns": "0003, 0006, 0007",
            "resolution_status": "PARTIALLY_RESOLVED",
            "review_conclusion": "Cross-asset variables matter most as conditioning and sequencing variables rather than as isolated predictors.",
        },
        {
            "contradiction": "Macro_transition is highly informative, but pooled event windows degrade signal quality.",
            "source_campaigns": "0002, 0005, 0006, 0007",
            "resolution_status": "OPEN",
            "review_conclusion": "The regime is valuable, but its internal event ecology needs finer decomposition before stronger alpha conclusions can be drawn.",
        },
    ]

    knowledge_gaps = [
        {
            "theme": "Cross-asset sequencing",
            "severity": "HIGH",
            "affected_hypotheses": "IKROS-HYP-20260802-0405",
            "evidence": "Campaign 0007 improved branch and range diagnostics, but still could not tell whether gold led or followed broader repricing.",
        },
        {
            "theme": "Participant crowding and positioning",
            "severity": "HIGH",
            "affected_hypotheses": "IKROS-HYP-20260802-0401",
            "evidence": "Bull continuation remains plausible, but the repository lacks governed positioning proxies to distinguish healthy continuation from exhaustion.",
        },
        {
            "theme": "Intraday transition structure",
            "severity": "HIGH",
            "affected_hypotheses": "IKROS-HYP-20260802-0408",
            "evidence": "Daily handoff replay improved path accounting, but intraday event ordering remains absent from the governed dataset stack.",
        },
        {
            "theme": "Event taxonomy granularity",
            "severity": "HIGH",
            "affected_hypotheses": "IKROS-HYP-20260802-0405",
            "evidence": "Macro-transition windows still pool scheduled policy decisions, macro prints, and noisy headlines.",
        },
        {
            "theme": "Episode coverage",
            "severity": "HIGH",
            "affected_hypotheses": "IKROS-HYP-20260802-0408",
            "evidence": "Campaign 0007 expanded handoff coverage from 7 to 18 episodes, but coverage remains too thin for decisive validation.",
        },
        {
            "theme": "Liquidity and event-quality proxies",
            "severity": "MEDIUM",
            "affected_hypotheses": "IKROS-HYP-20260802-0405",
            "evidence": "Wide-range contamination is now visible, but liquidity quality is still inferred from crude range/event-pressure proxies.",
        },
    ]

    research_lessons = [
        "Governed regime conditioning adds more scientific value than raw macro drift tests.",
        "Return anchors, volatility context, and bounded interaction terms outperform raw single-variable narratives after conditioning on regime.",
        "Scientific validation and failure analysis are both productive: rejected hypotheses created lasting institutional knowledge by clarifying what does not survive.",
        "Diagnostic segmentation is most useful when it isolates contamination sources such as transition overlap, DXY spillovers, branch imbalance, and wide-range event noise.",
        "Alpha discovery in gold is constrained more by explanatory data sufficiency than by lack of candidate ideas.",
    ]

    informative_regimes = _rank_informative_regimes(regimes)
    roadmap = _build_roadmap()
    maturity = _build_maturity_assessment(
        promoted_feature_count=len(promoted_features),
        validated_hypothesis_count=len(validation_rows),
        diagnostic_experiment_count=len(diagnostic_experiments),
        registry_counts=registries["counts"],
    )
    confidence_evolution = _build_confidence_evolution(
        validation_rows=validation_rows,
        failure_retained=failure_retained,
        diagnostic_recommendations=diagnostic_recommendations,
        confidence_assessments=confidence["assessments"],
    )

    analysis = {
        "cycle_title": "Phase H Institutional Research Review — Discovery Cycle 1",
        "campaign_summary": _campaign_summary(
            campaign_inputs=campaign_inputs,
            diagnostic_recommendations=diagnostic_recommendations,
        ),
        "institutional_knowledge_review": success_catalogue,
        "research_lessons_learned": research_lessons,
        "failure_catalogue": failure_catalogue,
        "success_catalogue": success_catalogue,
        "evidence_synthesis": {
            "campaign_count": 7,
            "registry_counts": registries["counts"],
            "graph": graph,
            "memory": memory,
            "confidence": confidence["summary"],
            "promoted_feature_count": len(promoted_features),
            "rejected_feature_count": len(rejected_features),
            "validated_hypothesis_count": len(validation_rows),
            "diagnostic_experiment_count": len(diagnostic_experiments),
        },
        "knowledge_gaps": knowledge_gaps,
        "contradiction_map": contradiction_map,
        "research_maturity_assessment": maturity,
        "confidence_evolution_report": confidence_evolution,
        "research_roadmap_v2": roadmap,
        "informative_regimes": informative_regimes,
        "consistent_features": [
            {
                "identifier": item["identifier"],
                "feature": item["feature"],
                "title": item["title"],
                "robust_regime_count": item["robust_regime_count"],
            }
            for item in promoted_features
        ],
        "uncertain_findings": [
            "IKROS-HYP-20260802-0401 needs re-validation with explicit persistence and DXY conditioning panels.",
            "IKROS-HYP-20260802-0405 needs re-validation with branch and event-quality segmentation.",
            "IKROS-HYP-20260802-0408 remains plausible but cannot advance until sequencing and episode-depth gaps close.",
        ],
        "disproven_findings": [
            "Macro-only next-day gold drift is not an institutional alpha candidate.",
            "Liquidation-pressure bear continuation did not survive scientific validation.",
            "Crisis safe-haven breakout convexity did not survive scientific validation.",
            "Standalone macro_pressure and dxy_return_20 do not survive as direct predictive features after regime conditioning.",
        ],
        "review_recommendation": roadmap[0],
    }

    analysis_path = output_dir / "discovery_cycle_1_review_analysis.json"
    write_json(analysis_path, analysis)
    return {"analysis": analysis, "paths": {"analysis": str(analysis_path)}}


def emit_discovery_cycle_1_reports(
    *,
    output_dir: Path,
    analysis: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    knowledge_md = output_dir / "INSTITUTIONAL_KNOWLEDGE_REVIEW.md"
    lessons_md = output_dir / "RESEARCH_LESSONS_LEARNED.md"
    failure_md = output_dir / "FAILURE_CATALOGUE.md"
    success_md = output_dir / "SUCCESS_CATALOGUE.md"
    evidence_md = output_dir / "EVIDENCE_SYNTHESIS.md"
    gaps_md = output_dir / "KNOWLEDGE_GAPS.md"
    contradiction_md = output_dir / "CONTRADICTION_MAP.md"
    maturity_md = output_dir / "RESEARCH_MATURITY_ASSESSMENT.md"
    confidence_md = output_dir / "CONFIDENCE_EVOLUTION_REPORT.md"
    roadmap_md = output_dir / "RESEARCH_ROADMAP_V2.md"
    final_md = output_dir / "DISCOVERY_CYCLE_1_FINAL_REVIEW.md"

    knowledge_rows = [
        [
            item["theme"],
            item["finding"],
            item["supporting_evidence"],
            item["institutional_status"],
        ]
        for item in analysis["institutional_knowledge_review"]
    ]
    write_markdown(
        knowledge_md,
        f"""
# Institutional Knowledge Review

{markdown_table(
    ["Theme", "Finding", "Supporting Evidence", "Status"],
    knowledge_rows,
)}
""",
    )

    write_markdown(
        lessons_md,
        "# Research Lessons Learned\n\n" + _markdown_bullets(analysis["research_lessons_learned"]) + "\n",
    )

    failure_rows = [
        [item["finding"], item["campaign"], item["status"], item["evidence"]]
        for item in analysis["failure_catalogue"]
    ]
    write_markdown(
        failure_md,
        f"""
# Failure Catalogue

{markdown_table(["Finding", "Campaign", "Status", "Evidence"], failure_rows)}
""",
    )

    success_rows = [
        [item["theme"], item["finding"], item["supporting_evidence"]]
        for item in analysis["success_catalogue"]
    ]
    write_markdown(
        success_md,
        f"""
# Success Catalogue

{markdown_table(["Theme", "Finding", "Evidence"], success_rows)}
""",
    )

    evidence = analysis["evidence_synthesis"]
    campaign_rows = [
        [
            item["campaign_id"],
            item["title"],
            item["status"],
            item["institutional_result"],
        ]
        for item in analysis["campaign_summary"]
    ]
    registry_rows = [
        [name, value] for name, value in sorted(evidence["registry_counts"].items())
    ]
    write_markdown(
        evidence_md,
        f"""
# Evidence Synthesis

## Campaign outcomes

{markdown_table(["Campaign", "Title", "Status", "Institutional Result"], campaign_rows)}

## IKROS footprint

- Graph nodes: **{evidence["graph"]["node_count"]}**
- Graph edges: **{evidence["graph"]["edge_count"]}**
- Memory records: **{evidence["memory"]["total_records"]}**
- Confidence assessments: **{evidence["confidence"]["assessment_count"]}**

## Registry counts

{markdown_table(["Registry Metric", "Count"], registry_rows)}
""",
    )

    gaps_rows = [
        [item["theme"], item["severity"], item["affected_hypotheses"], item["evidence"]]
        for item in analysis["knowledge_gaps"]
    ]
    write_markdown(
        gaps_md,
        f"""
# Knowledge Gaps

{markdown_table(
    ["Theme", "Severity", "Affected Hypotheses", "Evidence"],
    gaps_rows,
)}
""",
    )

    contradiction_rows = [
        [
            item["contradiction"],
            item["source_campaigns"],
            item["resolution_status"],
            item["review_conclusion"],
        ]
        for item in analysis["contradiction_map"]
    ]
    write_markdown(
        contradiction_md,
        f"""
# Contradiction Map

{markdown_table(
    ["Contradiction", "Source Campaigns", "Resolution", "Review Conclusion"],
    contradiction_rows,
)}
""",
    )

    maturity_rows = [
        [item["domain"], item["maturity_level"], item["evidence"], item["implication"]]
        for item in analysis["research_maturity_assessment"]
    ]
    write_markdown(
        maturity_md,
        f"""
# Research Maturity Assessment

{markdown_table(
    ["Domain", "Maturity", "Evidence", "Implication"],
    maturity_rows,
)}
""",
    )

    confidence_rows = [
        [
            item["target"],
            item["stage"],
            item["previous_confidence"],
            item["new_confidence"],
            item["interpretation"],
        ]
        for item in analysis["confidence_evolution_report"]
    ]
    write_markdown(
        confidence_md,
        f"""
# Confidence Evolution Report

{markdown_table(
    ["Target", "Stage", "Previous", "New", "Interpretation"],
    confidence_rows,
)}
""",
    )

    roadmap_rows = [
        [
            item["priority"],
            item["direction"],
            item["classification"],
            item["justification"],
            item["expected_information_gain"],
        ]
        for item in analysis["research_roadmap_v2"]
    ]
    write_markdown(
        roadmap_md,
        f"""
# Research Roadmap v2

{markdown_table(
    ["Priority", "Direction", "Classification", "Justification", "Expected Info Gain"],
    roadmap_rows,
)}
""",
    )

    write_markdown(
        final_md,
        f"""
# Discovery Cycle 1 Final Review

## What AFRP has learned

- Institutional knowledge now centers on the six-state regime taxonomy, the 12 promoted regime-conditioned features, and the conclusion that macro-only alpha does not survive governance.
- The most informative regimes in Cycle 1 were **bull_trend** and **macro_transition**, while **crisis_dislocation** mattered more as a risk state than as a direct alpha environment.
- The most durable explanatory structures were medium-horizon return anchors, bounded trend/volatility context, and cross-asset/event interactions rather than raw standalone macro variables.

## Discovery Cycle 2 recommendation

**Primary focus: {analysis["review_recommendation"]["direction"]}.**

{analysis["review_recommendation"]["justification"]}

## Immediate implication

Discovery Cycle 2 should prioritize closing cross-asset sequencing, participant-ecology, and event-taxonomy gaps before broadening into lower-evidence directions such as adaptive markets or explainability-first workstreams.
""",
    )

    return {
        "institutional_knowledge_review": str(knowledge_md),
        "research_lessons_learned": str(lessons_md),
        "failure_catalogue": str(failure_md),
        "success_catalogue": str(success_md),
        "evidence_synthesis": str(evidence_md),
        "knowledge_gaps": str(gaps_md),
        "contradiction_map": str(contradiction_md),
        "research_maturity_assessment": str(maturity_md),
        "confidence_evolution_report": str(confidence_md),
        "research_roadmap_v2": str(roadmap_md),
        "final_review": str(final_md),
    }


def run_discovery_cycle_1_review(
    repo_root: Path,
    *,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    resolved_output = (output_dir or (repo_root / PHASE_H_DISCOVERY_CYCLE_1_DIR)).resolve()
    prepared = prepare_discovery_cycle_1_review(
        repo_root=repo_root,
        output_dir=resolved_output,
    )
    analysis = cast(dict[str, Any], prepared["analysis"])
    report_paths = emit_discovery_cycle_1_reports(output_dir=resolved_output, analysis=analysis)
    result = {
        "analysis": analysis,
        "report_paths": report_paths,
    }
    result_path = resolved_output / "discovery_cycle_1_review_result.json"
    write_json(result_path, result)
    result["report_paths"]["result"] = str(result_path)
    return result


def _load_campaign_inputs(repo_root: Path) -> dict[str, Any]:
    def _load_json(relative_path: str) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            json.loads((repo_root / Path(relative_path)).read_text(encoding="utf-8")),
        )

    return {
        "macro_result": _load_json("11-research/phase-g/macro-alpha/macro_alpha_campaign_result.json"),
        "regime": _load_json("11-research/phase-g/regime-discovery/regime_discovery_analysis.json"),
        "regime_catalogue": cast(
            list[dict[str, Any]],
            json.loads(
                (repo_root / "11-research/phase-g/regime-discovery/regime_catalogue.json").read_text(
                    encoding="utf-8"
                )
            ),
        ),
        "feature": _load_json("11-research/phase-g/feature-discovery/feature_discovery_analysis.json"),
        "hypothesis": _load_json(
            "11-research/phase-g/hypothesis-discovery/hypothesis_discovery_analysis.json"
        ),
        "scientific": _load_json(
            "11-research/phase-g/scientific-validation/scientific_validation_analysis.json"
        ),
        "failure": _load_json("11-research/phase-g/failure-analysis/failure_analysis_analysis.json"),
        "diagnostic": _load_json(
            "11-research/phase-g/diagnostic-experiments/diagnostic_experiment_analysis.json"
        ),
    }


def _load_registry_state(repo_root: Path) -> dict[str, Any]:
    registry_root = repo_root / "data" / "ikros" / "registries"
    counts = {
        "research_questions": _count_yaml_files(registry_root / "research"),
        "hypotheses": _count_yaml_files(registry_root / "hypotheses"),
        "experiments": _count_yaml_files(registry_root / "experiments"),
        "alpha_candidates": _count_yaml_files(registry_root / "alphas"),
        "features": _count_yaml_files(registry_root / "features"),
    }
    return {"counts": counts}


def _load_confidence_state(repo_root: Path) -> dict[str, Any]:
    assessment_root = repo_root / "data" / "ikros" / "confidence" / "assessments"
    assessments = []
    for path in sorted(assessment_root.glob("ICA-*.yaml")):
        item = cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))
        new_confidence = cast(
            dict[str, Any],
            item.get("assessed_confidence") or item.get("new_confidence") or {},
        )
        previous_confidence = cast(dict[str, Any], item.get("previous_confidence") or {})
        assessments.append(
            {
                "target_id": str(item.get("target_id", "")),
                "reason": str(item.get("reason", "")),
                "previous_overall": float(previous_confidence.get("overall", 0.0)),
                "new_overall": float(new_confidence.get("overall", 0.0)),
            }
        )
    return {
        "assessments": assessments,
        "summary": {"assessment_count": len(assessments)},
    }


def _load_graph_state(repo_root: Path) -> dict[str, Any]:
    edges = cast(
        list[dict[str, Any]],
        yaml.safe_load((repo_root / "data" / "ikros" / "graph" / "edges.yaml").read_text(encoding="utf-8")),
    )
    node_root = repo_root / "data" / "ikros" / "graph" / "nodes"
    node_types: Counter[str] = Counter()
    node_count = 0
    for path in node_root.glob("*.yaml"):
        item = cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))
        node_types[str(item.get("node_type", "UNKNOWN"))] += 1
        node_count += 1
    return {
        "node_count": node_count,
        "edge_count": len(edges),
        "node_types": dict(node_types),
    }


def _load_memory_state(repo_root: Path) -> dict[str, Any]:
    memory_root = repo_root / "data" / "ikros" / "memory"
    tiers = {
        "t1_episodic": _count_yaml_files(memory_root / "t1-episodic"),
        "t2_semantic": _count_yaml_files(memory_root / "t2-semantic"),
        "t4_institutional": _count_yaml_files(memory_root / "t4-institutional"),
    }
    return {"tiers": tiers, "total_records": sum(tiers.values())}


def _campaign_summary(
    *,
    campaign_inputs: dict[str, Any],
    diagnostic_recommendations: list[dict[str, Any]],
) -> list[dict[str, str]]:
    validation_rows = cast(
        list[dict[str, Any]],
        campaign_inputs["scientific"]["hypothesis_validations"],
    )
    rejected = [item["hypothesis_id"] for item in validation_rows if item["decision"]["outcome"] == "REJECTED"]
    further = [
        item["hypothesis_id"]
        for item in validation_rows
        if item["decision"]["outcome"] == "REQUIRES_FURTHER_RESEARCH"
    ]
    recommended = [
        item["hypothesis_id"]
        for item in diagnostic_recommendations
        if item["recommendation"] == "RETURN_FOR_VALIDATION"
    ]
    return [
        {
            "campaign_id": "0001",
            "title": "Macro Alpha Baseline",
            "status": "Completed",
            "institutional_result": "Macro-only alpha rejected.",
        },
        {
            "campaign_id": "0002",
            "title": "Institutional Six-State Overlay Taxonomy",
            "status": "Completed",
            "institutional_result": "Canonical six-state taxonomy accepted.",
        },
        {
            "campaign_id": "0003",
            "title": "Institutional Feature Discovery",
            "status": "Completed",
            "institutional_result": "12 features promoted, 7 rejected, 34 candidates reviewed.",
        },
        {
            "campaign_id": "0004",
            "title": "Institutional Alpha Hypothesis Discovery",
            "status": "Completed",
            "institutional_result": "Five hypotheses advanced to scientific validation.",
        },
        {
            "campaign_id": "0005",
            "title": "Institutional Scientific Alpha Validation",
            "status": "Completed",
            "institutional_result": f"{len(rejected)} hypotheses rejected, {len(further)} retained, none promoted.",
        },
        {
            "campaign_id": "0006",
            "title": "Institutional Alpha Failure Analysis",
            "status": "Completed",
            "institutional_result": "Three retained hypotheses diagnosed and six governed experiments authorized.",
        },
        {
            "campaign_id": "0007",
            "title": "Institutional Diagnostic Experiment Program",
            "status": "Completed",
            "institutional_result": f"{', '.join(recommended)} returned for validation; IKROS-HYP-20260802-0408 remains in testing.",
        },
    ]


def _rank_informative_regimes(regimes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    qualitative_rank = {
        "bull_trend": 3,
        "macro_transition": 3,
        "range_compression": 2,
        "calm_carry": 2,
        "bear_unwind": 2,
        "crisis_dislocation": 1,
    }
    ranked = sorted(
        regimes,
        key=lambda item: (
            -qualitative_rank.get(str(item["label"]), 0),
            -float(item["hit_rate"]),
            -float(item["count"]),
        ),
    )
    return [
        {
            "label": str(item["label"]),
            "institutional_name": str(item["institutional_name"]),
            "hit_rate": float(item["hit_rate"]),
            "count": int(item["count"]),
            "review_view": _regime_review_view(str(item["label"])),
        }
        for item in ranked
    ]


def _build_roadmap() -> list[dict[str, Any]]:
    return [
        {
            "priority": "P1",
            "direction": "Cross-Asset Transition Ecology",
            "classification": "Another direction",
            "expected_information_gain": 4.9,
            "justification": "Cycle 1 repeatedly showed that DXY spillovers, policy/rates sequencing, participant adoption, and event-quality segmentation explain both surviving and failing hypotheses better than standalone macro drift. This direction unifies the strongest open evidence from H0401, H0405, and H0408 while staying closest to the actual unresolved uncertainties.",
        },
        {
            "priority": "P2",
            "direction": "Market Ecology",
            "classification": "Listed direction",
            "expected_information_gain": 4.6,
            "justification": "Participant crowding, adoption, and event ecology are the largest remaining non-price gaps behind the retained hypotheses.",
        },
        {
            "priority": "P3",
            "direction": "Causal Alpha",
            "classification": "Listed direction",
            "expected_information_gain": 4.3,
            "justification": "Once cross-asset and ecology gaps are narrowed, causal framing can separate true mechanism from correlated context.",
        },
        {
            "priority": "P4",
            "direction": "Liquidity",
            "classification": "Listed direction",
            "expected_information_gain": 3.8,
            "justification": "Liquidity quality mattered in H0405 contamination studies, but the current evidence points to sequencing and event ecology first.",
        },
        {
            "priority": "P5",
            "direction": "Macro",
            "classification": "Listed direction",
            "expected_information_gain": 3.1,
            "justification": "Macro remains important as context, but macro-only alpha was already disproven in Cycle 1.",
        },
    ]


def _build_maturity_assessment(
    *,
    promoted_feature_count: int,
    validated_hypothesis_count: int,
    diagnostic_experiment_count: int,
    registry_counts: dict[str, int],
) -> list[dict[str, str]]:
    return [
        {
            "domain": "Regime taxonomy",
            "maturity_level": "ESTABLISHED",
            "evidence": "Campaign 0002 accepted a canonical six-state model that remained the reference through Campaign 0007.",
            "implication": "Cycle 2 should build on the taxonomy rather than revisit regime discovery fundamentals.",
        },
        {
            "domain": "Feature catalogue",
            "maturity_level": "ESTABLISHED",
            "evidence": f"{promoted_feature_count} promoted features now anchor the governed explanatory library.",
            "implication": "New work should extend explanatory conditioning around the promoted set instead of restarting feature discovery from scratch.",
        },
        {
            "domain": "Hypothesis generation",
            "maturity_level": "MANAGED",
            "evidence": f"{validated_hypothesis_count} authorized hypotheses survived into formal validation, with governed triage before testing.",
            "implication": "The hypothesis process is strong enough to support a second cycle, but candidate promotion remains highly selective.",
        },
        {
            "domain": "Scientific validation",
            "maturity_level": "EMERGING",
            "evidence": "Campaign 0005 produced zero promoted alpha candidates and two hard rejections.",
            "implication": "Validation discipline is strong, but evidentiary sufficiency is the current bottleneck.",
        },
        {
            "domain": "Diagnostic experimentation",
            "maturity_level": "MANAGED",
            "evidence": f"{diagnostic_experiment_count} governed experiments reduced uncertainty and clarified next steps without changing hypotheses.",
            "implication": "AFRP can now use diagnostics as a standard bridge between failed validation and next-cycle design.",
        },
        {
            "domain": "Institutional memory and governance",
            "maturity_level": "ESTABLISHED",
            "evidence": f"{registry_counts['research_questions']} research questions, {registry_counts['hypotheses']} hypotheses, and {registry_counts['experiments']} reviewed experiments are persisted in IKROS.",
            "implication": "Cycle 2 can rely on strong traceability, memory, and graph coverage from day one.",
        },
        {
            "domain": "Alpha candidate production",
            "maturity_level": "INITIAL",
            "evidence": "The only alpha candidate in Cycle 1 was rejected, and no new alpha candidate survived later campaigns.",
            "implication": "Cycle 2 should optimize learning rate and mechanism clarity, not candidate count.",
        },
    ]


def _build_confidence_evolution(
    *,
    validation_rows: list[dict[str, Any]],
    failure_retained: list[dict[str, Any]],
    diagnostic_recommendations: list[dict[str, Any]],
    confidence_assessments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in confidence_assessments:
        rows.append(
            {
                "target": item["target_id"],
                "stage": item["reason"],
                "previous_confidence": round(float(item["previous_overall"]), 4),
                "new_confidence": round(float(item["new_overall"]), 4),
                "interpretation": "Confidence-engine update persisted in IKROS confidence history.",
            }
        )
    failure_by_id = {item["hypothesis_id"]: item for item in failure_retained}
    diagnostic_by_id = {item["hypothesis_id"]: item for item in diagnostic_recommendations}
    for item in validation_rows:
        hypothesis_id = str(item["hypothesis_id"])
        if hypothesis_id not in failure_by_id and hypothesis_id not in diagnostic_by_id:
            rows.append(
                {
                    "target": hypothesis_id,
                    "stage": "Campaign 0005 scientific validation",
                    "previous_confidence": round(float(item["confidence_prior"]), 4),
                    "new_confidence": round(float(item["suggested_posterior_confidence"]), 4),
                    "interpretation": str(item["decision"]["outcome"]),
                }
            )
            continue
        if hypothesis_id in failure_by_id:
            rows.append(
                {
                    "target": hypothesis_id,
                    "stage": "Campaign 0005 scientific validation",
                    "previous_confidence": round(float(item["confidence_prior"]), 4),
                    "new_confidence": round(float(item["suggested_posterior_confidence"]), 4),
                    "interpretation": str(item["decision"]["outcome"]),
                }
            )
            rows.append(
                {
                    "target": hypothesis_id,
                    "stage": "Campaign 0006 failure analysis",
                    "previous_confidence": round(float(item["suggested_posterior_confidence"]), 4),
                    "new_confidence": round(
                        float(failure_by_id[hypothesis_id]["updated_confidence"]["analysis_adjusted_confidence"]),
                        4,
                    ),
                    "interpretation": "Confidence reduced while failure drivers remained unresolved.",
                }
            )
        if hypothesis_id in diagnostic_by_id:
            rows.append(
                {
                    "target": hypothesis_id,
                    "stage": "Campaign 0007 diagnostic experiments",
                    "previous_confidence": round(
                        float(failure_by_id[hypothesis_id]["updated_confidence"]["analysis_adjusted_confidence"]),
                        4,
                    ),
                    "new_confidence": round(
                        float(diagnostic_by_id[hypothesis_id]["campaign_0007_confidence"]),
                        4,
                    ),
                    "interpretation": str(diagnostic_by_id[hypothesis_id]["recommendation"]),
                }
            )
    return rows


def _count_yaml_files(path: Path) -> int:
    return sum(1 for item in path.glob("*.yaml") if item.name != ".gitkeep")


def _markdown_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _regime_review_view(label: str) -> str:
    lookup = {
        "bull_trend": "Most informative positive state; strongest signal persistence and cleanest continuation logic.",
        "macro_transition": "Most informative event-driven state; strongest link to surviving hypotheses and diagnostic experiments.",
        "range_compression": "Useful baseline/default state, but more important as a comparison regime than as a direct alpha engine.",
        "calm_carry": "Moderately informative context, but not yet central to the strongest validated narratives.",
        "bear_unwind": "Informative for failure analysis, but bearish continuation did not survive validation.",
        "crisis_dislocation": "Important for taxonomy and risk framing, but poor direct alpha reliability in Cycle 1.",
    }
    return lookup.get(label, "Informative but not central to the strongest Cycle 1 conclusions.")
