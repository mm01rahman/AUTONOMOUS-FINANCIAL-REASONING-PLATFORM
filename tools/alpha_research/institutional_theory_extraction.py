"""Program F: Institutional Theory Extraction from Discovery Cycle 2 evidence."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

DC2_PROGRAM_F_PHASE1_DIR = Path("11-research") / "discovery-cycle-2" / "research-program-f-phase1"
DC2_PROGRAM_F_PHASE1_ANALYSIS = DC2_PROGRAM_F_PHASE1_DIR / "dc2_program_f_institutional_theory_analysis.json"


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], __import__("json").loads(path.read_text(encoding="utf-8")))


def _source_analysis_paths(repo_root: Path) -> dict[str, Path]:
    base = repo_root / "11-research" / "discovery-cycle-2"
    return {
        "program_a_phase1": base / "research-program-a" / "dc2_program_a_analysis.json",
        "program_a_phase2": base / "research-program-a-phase2" / "dc2_phase2_causal_analysis.json",
        "program_a_phase3": base / "research-program-a-phase3" / "dc2_phase3_information_network_analysis.json",
        "program_b_phase1": base / "research-program-b-phase1" / "dc2_program_b_market_ecology_analysis.json",
        "program_b_phase2": base / "research-program-b-phase2" / "dc2_program_b_phase2_decision_ecology_analysis.json",
        "program_c_phase1": base / "research-program-c-phase1" / "dc2_program_c_transition_engine_analysis.json",
        "program_d_phase1": base / "research-program-d-phase1" / "dc2_program_d_verification_analysis.json",
        "program_e_phase1": base / "research-program-e-phase1" / "dc2_program_e_ablation_analysis.json",
    }


def _extract_principles(evidence: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    a1 = evidence["program_a_phase1"]
    a2 = evidence["program_a_phase2"]
    a3 = evidence["program_a_phase3"]
    b1 = evidence["program_b_phase1"]
    b2 = evidence["program_b_phase2"]
    c1 = evidence["program_c_phase1"]
    d1 = evidence["program_d_phase1"]
    e1 = evidence["program_e_phase1"]

    stable_edges = cast(list[str], a3["arb_recommendation"]["stable_edges"])
    dominant_sources = cast(list[str], a3["arb_recommendation"]["dominant_sources"])
    dominant_relays = cast(list[str], a3["arb_recommendation"]["dominant_relays"])
    dominant_sinks = cast(list[str], a3["arb_recommendation"]["dominant_sinks"])
    topology_overlap = float(a3["arb_recommendation"]["mean_topology_overlap"])

    d_outcome = cast(dict[str, Any], d1["arb_recommendation"])
    d_failures = cast(list[str], d1["failure_catalogue"])
    e_arb = cast(dict[str, Any], e1["arb_recommendation"])
    e_contrib = cast(list[dict[str, Any]], e1["component_contribution_report"])
    contrib_map = {str(row["component"]): float(row["incremental_gain"]) for row in e_contrib}

    principles: list[dict[str, Any]] = [
        {
            "principle_id": "IKROS-PF1-PRINCIPLE-0001",
            "name": "Directed cross-asset topology governs information propagation",
            "classification": "INSTITUTIONAL_AXIOM",
            "scientific_statement": "Information before XAU/USD regime transitions propagates through a directed, confidence-weighted cross-asset topology with identifiable source, relay, and sink hierarchy.",
            "supporting_evidence": [
                "Program A Phase 3 ARB: governing model is confidence-weighted directed network with regime overlays.",
                f"Program A Phase 3 stable edges: {', '.join(stable_edges[:5])}.",
                f"Program A Phase 3 hierarchy: sources={', '.join(dominant_sources)}, relays={', '.join(dominant_relays)}, sinks={', '.join(dominant_sinks)}.",
            ],
            "contradictory_evidence": [],
            "confidence": 0.82,
            "scope": "XAU/USD cross-asset regime transition context (1D horizon).",
            "failure_conditions": ["If directed hierarchy disappears after adding missing external market datasets."],
            "regime_dependence": "Topology reconfigures by regime while preserving core hierarchy constraints.",
            "economic_rationale": "Institutional capital reallocates through constrained relay channels, producing directed information flow.",
            "institutional_candidate": True,
        },
        {
            "principle_id": "IKROS-PF1-PRINCIPLE-0002",
            "name": "Topology is regime-dependent but structurally persistent",
            "classification": "INSTITUTIONAL_AXIOM",
            "scientific_statement": "Cross-asset network topology changes under stress/event regimes but retains substantial structural overlap and persistent bottlenecks.",
            "supporting_evidence": [
                f"Program A Phase 3 mean topology overlap: {topology_overlap:.4f}.",
                f"Program A Phase 3 bottlenecks: {', '.join(cast(list[str], a3['arb_recommendation']['network_bottlenecks']))}.",
                "Program A Phase 3 stress/event topology reports show conditional rewiring rather than complete topology collapse.",
            ],
            "contradictory_evidence": [],
            "confidence": 0.79,
            "scope": "Regime-conditioned network topology around transitions.",
            "failure_conditions": ["If out-of-sample topology overlap collapses materially below observed governed window."],
            "regime_dependence": "High; topology differs across six approved regimes.",
            "economic_rationale": "Institutional constraints and common collateral channels anchor flow skeleton while risk appetite rotates edges.",
            "institutional_candidate": True,
        },
        {
            "principle_id": "IKROS-PF1-PRINCIPLE-0003",
            "name": "Institutional heterogeneity is a necessary descriptive layer",
            "classification": "SUPPORTED_PRINCIPLE",
            "scientific_statement": "Participant classes (central banks, dealers, market makers, hedge funds, CTAs, ETF/safe-haven flows, hedgers) exhibit differentiated objectives, constraints, and liquidity effects that shape observed ecology.",
            "supporting_evidence": [
                "Program B Phase 1 participant profiles and interaction matrix.",
                f"Program B Phase 1 critical interactions: {', '.join(cast(list[str], b1['research_recommendations']['critical_interactions'])[:5])}.",
                "Program B Phase 2 confirms heterogeneous decision responses and asymmetry rankings.",
            ],
            "contradictory_evidence": [
                "Program E found participant_ecology_layer negative incremental gain in Transition Engine v1 implementation."
            ],
            "confidence": 0.68,
            "scope": "Descriptive institutional ecology; not automatically predictive when naively encoded.",
            "failure_conditions": ["If participant proxies remain too coarse to map to transition timing decisions."],
            "regime_dependence": "Participant influence and interaction intensity vary by regime.",
            "economic_rationale": "Different balance-sheet mandates and risk constraints generate non-homogeneous order-flow impact.",
            "institutional_candidate": True,
        },
        {
            "principle_id": "IKROS-PF1-PRINCIPLE-0004",
            "name": "Decision latency hierarchy and cascades matter",
            "classification": "SUPPORTED_PRINCIPLE",
            "scientific_statement": "Faster institutional actors initiate decision cascades that propagate through slower agents and inventory relays.",
            "supporting_evidence": [
                f"Program B Phase 2 fastest decision makers: {', '.join(cast(list[str], b2['institutional_recommendations']['fastest_decision_makers'])[:5])}.",
                f"Program B Phase 2 dominant cascade initiators: {', '.join(cast(list[str], b2['institutional_recommendations']['dominant_cascade_initiators'])[:4])}.",
                "Program C transition timelines explicitly include participant action and decision sequence stages.",
            ],
            "contradictory_evidence": [],
            "confidence": 0.73,
            "scope": "Transition formation sequencing, not sufficient as standalone predictor.",
            "failure_conditions": ["If latency rankings invert under richer event-annotated data."],
            "regime_dependence": "Cascade pathways vary with liquidity and macro stress state.",
            "economic_rationale": "Short-horizon discretionary and systematic actors react before policy/anchor actors fully reprice.",
            "institutional_candidate": True,
        },
        {
            "principle_id": "IKROS-PF1-PRINCIPLE-0005",
            "name": "Integrated transition narratives are plausible but not yet validated",
            "classification": "CONDITIONAL_PRINCIPLE",
            "scientific_statement": "A systems narrative combining macro repricing, participant ecology, decision cascades, cross-asset propagation, and liquidity transformation is economically coherent but not empirically superior in v1 implementation.",
            "supporting_evidence": [
                f"Program C mean transition confidence: {float(c1['transition_confidence_model']['mean_confidence']):.4f}.",
                "Program C generated complete six-state transition library and dependency graph.",
                "Program D still acknowledged interpretability and plausibility dimensions for structured models.",
            ],
            "contradictory_evidence": [
                f"Program D outcome: {d_outcome['outcome']} ({d_outcome['decision']}).",
                "Program D: engine not superior in transition detection/timing versus simpler baselines.",
            ],
            "confidence": 0.52,
            "scope": "Explanatory architecture-level framing only.",
            "failure_conditions": ["If integrated models cannot outperform simple baselines after mechanism-level correction."],
            "regime_dependence": "Expected high dependence; currently under-constrained.",
            "economic_rationale": "Regime transitions are multi-channel institutional phenomena, but channel weights were mis-specified in v1.",
            "institutional_candidate": False,
        },
        {
            "principle_id": "IKROS-PF1-PRINCIPLE-0006",
            "name": "High trigger sensitivity without calibration degrades transition validity",
            "classification": "INSTITUTIONAL_AXIOM",
            "scientific_statement": "Transition detection architectures must explicitly control false-transition rates and calibrate transition-risk confidence; otherwise explanatory claims are unreliable.",
            "supporting_evidence": [
                f"Program D failures include: {d_failures[0]}",
                f"Program D failures include: {d_failures[2]}",
                "Program E interaction/regime/cross-asset layers flagged for redesign partly due to calibration and over-sensitivity outcomes.",
            ],
            "contradictory_evidence": [],
            "confidence": 0.86,
            "scope": "All future transition inference architectures in AFRP.",
            "failure_conditions": ["If model governance allows uncalibrated confidence or unbounded trigger amplification."],
            "regime_dependence": "Applies across regimes, especially stress regimes.",
            "economic_rationale": "Institutional transitions are sparse; over-triggering creates spurious regime narratives.",
            "institutional_candidate": True,
        },
        {
            "principle_id": "IKROS-PF1-PRINCIPLE-0007",
            "name": "Transition Engine v1 component set is not institutionally retained",
            "classification": "REJECTED_PRINCIPLE",
            "scientific_statement": "The specific Transition Engine v1 composition qualifies as a governing explanatory model.",
            "supporting_evidence": [],
            "contradictory_evidence": [
                f"Program D outcome: {d_outcome['outcome']} / {d_outcome['decision']}.",
                "Program E: components_to_retain is empty.",
            ],
            "confidence": 0.9,
            "scope": "Transition Engine v1 implementation only.",
            "failure_conditions": ["N/A (already falsified/rejected in current governed evidence)."],
            "regime_dependence": "N/A",
            "economic_rationale": "Empirical performance and calibration deficits prevent institutional retention.",
            "institutional_candidate": False,
        },
        {
            "principle_id": "IKROS-PF1-PRINCIPLE-0008",
            "name": "Participant ecology layer as encoded in v1 adds negative incremental value",
            "classification": "REJECTED_PRINCIPLE",
            "scientific_statement": "The v1 participant ecology layer implementation improves transition explanatory performance.",
            "supporting_evidence": [],
            "contradictory_evidence": [
                f"Program E incremental gain participant_ecology_layer: {contrib_map.get('participant_ecology_layer', 0.0):.4f}.",
                f"Program E components_to_remove: {', '.join(cast(list[str], e_arb['components_to_remove']))}.",
            ],
            "confidence": 0.84,
            "scope": "Current v1 parameterization and proxy encoding only.",
            "failure_conditions": ["Could be reconsidered only with materially improved participant-state observability."],
            "regime_dependence": "Likely regime dependent but unresolved due signal specification weakness.",
            "economic_rationale": "Coarse participant proxies can inject noise and overfit institutional narratives.",
            "institutional_candidate": False,
        },
        {
            "principle_id": "IKROS-PF1-PRINCIPLE-0009",
            "name": "Macro and decision layers remain unresolved evidence targets",
            "classification": "OPEN_QUESTION",
            "scientific_statement": "Macro and decision-ecology layers may contain explanatory signal but require additional evidence before institutional retention or rejection.",
            "supporting_evidence": [
                f"Program E components requiring evidence: {', '.join(cast(list[str], e_arb['components_requiring_additional_evidence']))}.",
                f"Program E incremental gain macro={contrib_map.get('macro_layer', 0.0):.4f}, decision={contrib_map.get('decision_ecology_layer', 0.0):.4f}.",
            ],
            "contradictory_evidence": [
                f"Program A Phase 2 retained-for-validation signals were limited: {', '.join(cast(list[str], a2['arb_summary']['retain_for_validation']))}."
            ],
            "confidence": 0.49,
            "scope": "Future evidence acquisition and controlled validation studies.",
            "failure_conditions": ["If future studies fail to demonstrate stable incremental gain over simpler baselines."],
            "regime_dependence": "Potentially high but currently under-identified.",
            "economic_rationale": "Macro and decision channels are plausible but weakly observed in current dataset coverage.",
            "institutional_candidate": False,
        },
        {
            "principle_id": "IKROS-PF1-PRINCIPLE-0010",
            "name": "Data completeness constrains causal claims",
            "classification": "INSTITUTIONAL_AXIOM",
            "scientific_statement": "Causal or transition-level institutional claims are bounded by exogenous data coverage quality; missing cross-market observability should default conclusions toward conditional status.",
            "supporting_evidence": [
                f"Program A Phase 1 data gap priority includes: {', '.join(cast(list[str], a1['arb_recommendation']['data_gap_priority'])[:5])}.",
                "Program D contradictory evidence: CPI/NFP direct datasets unavailable; proxies were used.",
                "Program A Phase 2 promoted zero strong causal candidates under available data.",
            ],
            "contradictory_evidence": [],
            "confidence": 0.88,
            "scope": "All AFRP discovery cycles and model-governance decisions.",
            "failure_conditions": ["If governance permits strong-causal promotion without closing critical data gaps."],
            "regime_dependence": "Data requirements amplify in stress/event regimes.",
            "economic_rationale": "Unobserved drivers induce omitted-variable bias and unstable causal attribution.",
            "institutional_candidate": True,
        },
    ]
    return principles


def _classify_principles(principles: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "institutional_axioms": [],
        "supported_principles": [],
        "conditional_principles": [],
        "rejected_principles": [],
        "open_questions": [],
        "research_unknowns": [],
    }
    for principle in principles:
        cls = str(principle["classification"])
        if cls == "INSTITUTIONAL_AXIOM":
            buckets["institutional_axioms"].append(principle)
        elif cls == "SUPPORTED_PRINCIPLE":
            buckets["supported_principles"].append(principle)
        elif cls == "CONDITIONAL_PRINCIPLE":
            buckets["conditional_principles"].append(principle)
        elif cls == "REJECTED_PRINCIPLE":
            buckets["rejected_principles"].append(principle)
        elif cls == "OPEN_QUESTION":
            buckets["open_questions"].append(principle)
        else:
            buckets["research_unknowns"].append(principle)
    return buckets


def _evidence_synthesis(principles: list[dict[str, Any]]) -> dict[str, Any]:
    proved = [p["scientific_statement"] for p in principles if str(p["classification"]) in {"INSTITUTIONAL_AXIOM", "SUPPORTED_PRINCIPLE"}]
    disproved = [p["scientific_statement"] for p in principles if str(p["classification"]) == "REJECTED_PRINCIPLE"]
    uncertain = [p["scientific_statement"] for p in principles if str(p["classification"]) in {"CONDITIONAL_PRINCIPLE", "OPEN_QUESTION"}]

    constraints = [
        "Future architectures MUST model directed cross-asset information flow with explicit source-relay-sink structure.",
        "Future architectures MUST be regime-aware and stress-aware; topology and mechanism parameters cannot be globally stationary.",
        "Future architectures MUST include explicit confidence calibration checks (e.g., Brier-style diagnostics) and false-transition controls.",
        "Future architectures MUST beat or match simple baselines on transition detection and timing before institutional promotion.",
        "Future architectures MUST separate descriptive institutional narratives from predictive claims unless verified by out-of-sample evidence.",
        "Future architectures MUST treat unresolved macro and decision layers as hypothesis zones requiring dedicated evidence programs.",
        "Future architectures MUST enforce data-gap governance; missing critical markets block strong-causal promotion.",
    ]

    return {
        "what_dc2_proved": proved,
        "what_dc2_disproved": disproved,
        "what_remains_uncertain": uncertain,
        "architecture_constraints_for_future_models": constraints,
    }


def _knowledge_graph_payload(classification: dict[str, list[dict[str, Any]]], synthesis: dict[str, Any]) -> dict[str, Any]:
    principle_nodes: list[dict[str, Any]] = []
    for items in classification.values():
        for p in items:
            principle_nodes.append(
                {
                    "node_id": p["principle_id"],
                    "label": p["name"],
                    "classification": p["classification"],
                    "confidence": p["confidence"],
                }
            )

    conclusion_node = {
        "node_id": "IKROS-PF1-CONCLUSION-20260802-0001",
        "label": "Discovery Cycle 2 Institutional Theory Extraction Conclusion",
        "node_type": "RESEARCH_CONCLUSION",
        "attributes": {
            "axioms": len(classification["institutional_axioms"]),
            "supported": len(classification["supported_principles"]),
            "conditional": len(classification["conditional_principles"]),
            "rejected": len(classification["rejected_principles"]),
            "open_questions": len(classification["open_questions"]),
        },
    }
    constraints_node = {
        "node_id": "IKROS-PF1-CONSTRAINTS-20260802-0001",
        "label": "Future Architecture Constraints",
        "node_type": "KNOWLEDGE_OBJECT",
        "attributes": {"constraint_count": len(synthesis["architecture_constraints_for_future_models"])},
    }

    edges: list[dict[str, Any]] = []
    for p in principle_nodes:
        relation = "SUPPORTED_BY" if str(p["classification"]) != "REJECTED_PRINCIPLE" else "REFUTES"
        edges.append({"source": p["node_id"], "target": conclusion_node["node_id"], "relation": relation, "confidence": p["confidence"]})
    edges.append({"source": conclusion_node["node_id"], "target": constraints_node["node_id"], "relation": "EXPLAINS", "confidence": 0.8})

    return {
        "principle_nodes": principle_nodes,
        "conclusion_node": conclusion_node,
        "constraints_node": constraints_node,
        "edges": edges,
    }


def prepare_dc2_program_f_phase1_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(".")
    source_paths = _source_analysis_paths(root)
    if any(not path.exists() for path in source_paths.values()):
        source_paths = _source_analysis_paths(Path("."))
    evidence: dict[str, dict[str, Any]] = {}
    for key, path in source_paths.items():
        evidence[key] = _load_json(path)

    principles = _extract_principles(evidence)
    classification = _classify_principles(principles)
    synthesis = _evidence_synthesis(principles)
    graph_payload = _knowledge_graph_payload(classification, synthesis)

    analysis: dict[str, Any] = {
        "phase": "DC2_PROGRAM_F_PHASE1",
        "title": "Institutional Theory Extraction",
        "source_programs": list(source_paths.keys()),
        "scientific_principle_registry": principles,
        "institutional_axiom_registry": classification["institutional_axioms"],
        "supported_principles": classification["supported_principles"],
        "conditional_principles": classification["conditional_principles"],
        "rejected_principles": classification["rejected_principles"],
        "open_research_questions": classification["open_questions"],
        "research_unknowns": classification["research_unknowns"],
        "evidence_synthesis": synthesis,
        "knowledge_consolidation_report": {
            "axiom_count": len(classification["institutional_axioms"]),
            "supported_count": len(classification["supported_principles"]),
            "conditional_count": len(classification["conditional_principles"]),
            "rejected_count": len(classification["rejected_principles"]),
            "open_question_count": len(classification["open_questions"]),
        },
        "arb_recommendation": {
            "promote_to_institutional_constraints": [item["name"] for item in classification["institutional_axioms"]],
            "retain_as_supported_principles": [item["name"] for item in classification["supported_principles"]],
            "keep_conditional": [item["name"] for item in classification["conditional_principles"]],
            "reject": [item["name"] for item in classification["rejected_principles"]],
            "open_questions": [item["name"] for item in classification["open_questions"]],
            "architecture_constraints": synthesis["architecture_constraints_for_future_models"],
            "stop_confirmation": "Program F extracted institutional scientific theory only; no engine redesign and no alpha generation performed.",
        },
        "ecology_knowledge_graph": graph_payload,
    }

    out_dir = root / DC2_PROGRAM_F_PHASE1_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc2_program_f_institutional_theory_analysis.json", analysis)
    return analysis


def emit_dc2_program_f_phase1_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC2_PROGRAM_F_PHASE1_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    principle_registry = cast(list[dict[str, Any]], analysis["scientific_principle_registry"])
    axioms = cast(list[dict[str, Any]], analysis["institutional_axiom_registry"])
    supported = cast(list[dict[str, Any]], analysis["supported_principles"])
    conditional = cast(list[dict[str, Any]], analysis["conditional_principles"])
    rejected = cast(list[dict[str, Any]], analysis["rejected_principles"])
    open_q = cast(list[dict[str, Any]], analysis["open_research_questions"])
    synthesis = cast(dict[str, Any], analysis["evidence_synthesis"])
    arb = cast(dict[str, Any], analysis["arb_recommendation"])

    theory_md = out_dir / "INSTITUTIONAL_THEORY_REPORT.md"
    theory_rows = [[p["principle_id"], p["name"], p["classification"], p["confidence"]] for p in principle_registry]
    write_markdown(
        theory_md,
        f"""# Institutional Theory Report
## Discovery Cycle 2 Program F Phase 1

{markdown_table(["Principle ID", "Principle", "Classification", "Confidence"], theory_rows)}

### Synthesis
- **What DC2 proved**: {len(cast(list[str], synthesis["what_dc2_proved"]))} principles
- **What DC2 disproved**: {len(cast(list[str], synthesis["what_dc2_disproved"]))} principles
- **What remains uncertain**: {len(cast(list[str], synthesis["what_remains_uncertain"]))} principles
""",
    )
    written["institutional_theory_report"] = str(theory_md)

    registry_md = out_dir / "SCIENTIFIC_PRINCIPLE_REGISTRY.md"
    reg_rows = [[p["name"], p["classification"], p["scope"], p["confidence"]] for p in principle_registry]
    write_markdown(
        registry_md,
        f"""# Scientific Principle Registry
## Discovery Cycle 2 Program F Phase 1

{markdown_table(["Principle", "Classification", "Scope", "Confidence"], reg_rows)}
""",
    )
    written["scientific_principle_registry"] = str(registry_md)

    synthesis_md = out_dir / "EVIDENCE_SYNTHESIS.md"
    proved_list = "\n".join(f"- {line}" for line in cast(list[str], synthesis["what_dc2_proved"]))
    disproved_list = "\n".join(f"- {line}" for line in cast(list[str], synthesis["what_dc2_disproved"]))
    uncertain_list = "\n".join(f"- {line}" for line in cast(list[str], synthesis["what_remains_uncertain"]))
    write_markdown(
        synthesis_md,
        f"""# Evidence Synthesis
## Discovery Cycle 2 Program F Phase 1

### What Discovery Cycle 2 proved
{proved_list}

### What Discovery Cycle 2 disproved
{disproved_list}

### What remains uncertain
{uncertain_list}
""",
    )
    written["evidence_synthesis"] = str(synthesis_md)

    consolidation_md = out_dir / "KNOWLEDGE_CONSOLIDATION_REPORT.md"
    counts = cast(dict[str, Any], analysis["knowledge_consolidation_report"])
    count_rows = [[k, v] for k, v in counts.items()]
    write_markdown(
        consolidation_md,
        f"""# Knowledge Consolidation Report
## Discovery Cycle 2 Program F Phase 1

{markdown_table(["Category", "Count"], count_rows)}
""",
    )
    written["knowledge_consolidation_report"] = str(consolidation_md)

    axiom_md = out_dir / "INSTITUTIONAL_AXIOM_REGISTRY.md"
    axiom_rows = [[p["name"], p["scientific_statement"], p["confidence"]] for p in axioms]
    write_markdown(
        axiom_md,
        f"""# Institutional Axiom Registry
## Discovery Cycle 2 Program F Phase 1

{markdown_table(["Axiom", "Scientific Statement", "Confidence"], axiom_rows)}
""",
    )
    written["institutional_axiom_registry"] = str(axiom_md)

    open_md = out_dir / "OPEN_RESEARCH_QUESTIONS.md"
    open_rows = [[p["name"], p["scientific_statement"], p["confidence"]] for p in open_q]
    write_markdown(
        open_md,
        f"""# Open Research Questions
## Discovery Cycle 2 Program F Phase 1

{markdown_table(["Question", "Statement", "Confidence"], open_rows)}
""",
    )
    written["open_research_questions"] = str(open_md)

    constraints_md = out_dir / "ARCHITECTURE_CONSTRAINTS_FOR_FUTURE_MODELS.md"
    constraints_lines = "\n".join(f"- {line}" for line in cast(list[str], synthesis["architecture_constraints_for_future_models"]))
    write_markdown(
        constraints_md,
        f"""# Architecture Constraints for Future Models
## Discovery Cycle 2 Program F Phase 1

{constraints_lines}
""",
    )
    written["architecture_constraints"] = str(constraints_md)

    arb_md = out_dir / "ARB_RECOMMENDATION.md"
    class_rows = [
        ["Institutional Axioms", len(axioms)],
        ["Supported Principles", len(supported)],
        ["Conditional Principles", len(conditional)],
        ["Rejected Principles", len(rejected)],
        ["Open Questions", len(open_q)],
    ]
    write_markdown(
        arb_md,
        f"""# Architecture Review Board Recommendation
## Discovery Cycle 2 Program F Phase 1

{markdown_table(["Classification", "Count"], class_rows)}

### Promote to Institutional Constraints
{chr(10).join(f"- {name}" for name in cast(list[str], arb["promote_to_institutional_constraints"]))}

### Keep as Supported Principles
{chr(10).join(f"- {name}" for name in cast(list[str], arb["retain_as_supported_principles"]))}

### Keep Conditional
{chr(10).join(f"- {name}" for name in cast(list[str], arb["keep_conditional"]))}

### Reject
{chr(10).join(f"- {name}" for name in cast(list[str], arb["reject"]))}

### Open Questions
{chr(10).join(f"- {name}" for name in cast(list[str], arb["open_questions"]))}

### Stop Condition
{arb["stop_confirmation"]}
""",
    )
    written["arb_recommendation"] = str(arb_md)

    if campaign_result is not None:
        write_json(out_dir / "dc2_program_f_campaign_result.json", campaign_result)
        written["campaign_result"] = str(out_dir / "dc2_program_f_campaign_result.json")

    write_json(out_dir / "dc2_program_f_classification_summary.json", cast(dict[str, Any], analysis["knowledge_consolidation_report"]))
    written["classification_summary"] = str(out_dir / "dc2_program_f_classification_summary.json")
    return written
