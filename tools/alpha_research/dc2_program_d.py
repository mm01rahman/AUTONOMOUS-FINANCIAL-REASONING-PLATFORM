"""Discovery Cycle 2 Program D Phase 1 governed verification/falsification execution."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import write_json
from tools.alpha_research.transition_engine_verification import (
    DC2_PROGRAM_D_PHASE1_DIR,
    emit_dc2_program_d_phase1_reports,
    prepare_dc2_program_d_phase1_artifacts,
)
from tools.ikros.graph import EdgeType, GraphNode, NodeType, YAMLGraphRepository
from tools.ikros.graph.models import GraphEdge
from tools.ikros.identifiers import compute_reproducibility_hash
from tools.ikros.models import Experiment, ResearchQuestion
from tools.ikros.orchestrator import FailurePolicy, ResearchCampaign, ResearchOrchestrator, TaskKind
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.research import ResearchRegistry


def _with_reproducibility_hash(entity: dict[str, Any]) -> dict[str, Any]:
    result = dict(entity)
    if (
        "reproducibility_hash" not in result
        or result["reproducibility_hash"] == "dc2-program-d-phase1-v1"
    ):
        result["reproducibility_hash"] = compute_reproducibility_hash(result)
    return result


def _select_campaign_pipeline(campaign: ResearchCampaign, task_kinds: list[str]) -> ResearchCampaign:
    kind_set = set(task_kinds)
    filtered = [task for task in campaign.tasks if task.kind in kind_set]
    ordered = sorted(filtered, key=lambda task: task_kinds.index(task.kind) if task.kind in task_kinds else 999)
    for idx, task in enumerate(ordered):
        task.depends_on = [ordered[idx - 1].task_id] if idx > 0 else []
    campaign.tasks = ordered
    campaign.pipeline.task_ids = [task.task_id for task in ordered]
    campaign.pipeline.stages = [task.kind for task in ordered]
    return campaign


def _transition_if_needed(
    registry: Any,  # noqa: ANN401
    entity_id: str,
    target_state: str,
    note: str = "",
) -> None:
    rank = {"PROPOSED": 0, "OPEN": 0, "APPROVED_FOR_TESTING": 1, "ACTIVE": 1, "TESTING": 2, "ANSWERED": 3, "COMPLETE": 3, "ARCHIVED": 4, "RETIRED": 4}
    try:
        current = str(registry.get(entity_id).lifecycle_state)
        if rank.get(current, 0) < rank.get(target_state, 0):
            if note:
                registry.transition(entity_id, target_state, note=note)
            else:
                registry.transition(entity_id, target_state)
    except Exception:
        pass


def _upsert_graph_payload(repo_root: Path, analysis: dict[str, Any], campaign_id: str) -> dict[str, int]:
    graph_repo = YAMLGraphRepository((repo_root / "data" / "ikros" / "graph").resolve())
    graph = graph_repo.load()
    payload = analysis["ecology_knowledge_graph"]
    created_nodes = 0
    created_edges = 0

    model_node_id = "IKROS-PD1-WORLDMODEL-20260802-0001"
    conclusion_node_id = "IKROS-PD1-CONCLUSION-20260802-0001"
    evidence_node_id = "IKROS-PD1-EVIDENCE-20260802-0001"

    nodes = [
        GraphNode(
            node_id=model_node_id,
            node_type=NodeType.WORLD_MODEL.value,
            ikros_id=model_node_id,
            label="Transition Engine Verification Program",
            confidence=0.72,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes={"program": "DC2 Program D Phase 1"},
        ),
        GraphNode(
            node_id=conclusion_node_id,
            node_type=NodeType.RESEARCH_CONCLUSION.value,
            ikros_id=conclusion_node_id,
            label="Transition engine falsification verdict",
            confidence=0.70,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes={"outcome": analysis["arb_recommendation"]["outcome"], "decision": analysis["arb_recommendation"]["decision"]},
        ),
        GraphNode(
            node_id=evidence_node_id,
            node_type=NodeType.EVIDENCE.value,
            ikros_id=evidence_node_id,
            label="Program D verification evidence",
            confidence=0.68,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes={"evidence_ref": str(DC2_PROGRAM_D_PHASE1_DIR / "INSTITUTIONAL_TRANSITION_ENGINE_VERIFICATION_REPORT.md")},
        ),
    ]
    nodes.extend(
        GraphNode(
            node_id=node["node_id"],
            node_type=NodeType.MODEL.value,
            ikros_id=node["node_id"],
            label=str(node["label"]),
            confidence=0.66,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes=dict(node["attributes"]),
        )
        for node in payload["model_nodes"]
    )
    nodes.append(
        GraphNode(
            node_id=payload["verification_node"]["node_id"],
            node_type=NodeType.VALIDATION.value,
            ikros_id=payload["verification_node"]["node_id"],
            label=payload["verification_node"]["label"],
            confidence=0.68,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes=dict(payload["verification_node"]["attributes"]),
        )
    )
    nodes.extend(
        GraphNode(
            node_id=node["node_id"],
            node_type=NodeType.FAILURE.value,
            ikros_id=node["node_id"],
            label=node["label"],
            confidence=0.64,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes=dict(node["attributes"]),
        )
        for node in payload["failure_nodes"]
    )

    for node in nodes:
        if not graph.has_node(node.node_id):
            graph.add_node(node)
            created_nodes += 1

    relation_index = {(edge.source_id, edge.target_id, edge.edge_type) for edge in graph.edges()}

    def add_edge(source_id: str, target_id: str, edge_type: str, confidence: float, evidence_ref: str) -> None:
        nonlocal created_edges
        key = (source_id, target_id, edge_type)
        if key in relation_index:
            return
        edge = GraphEdge(
            edge_id=graph.next_edge_id(),
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            confidence=confidence,
            evidence_ref=evidence_ref,
            spec_ref="SPEC-060",
            wp_ref="WP-IMP-0048",
            attributes={},
        )
        graph.add_edge(edge)
        relation_index.add(key)
        created_edges += 1

    for edge in payload["edges"]:
        mapped = EdgeType.EVALUATED.value if edge["relation"] == "EVALUATED" else EdgeType.CONTRADICTED_BY.value
        add_edge(edge["source"], edge["target"], mapped, float(edge["confidence"]), str(DC2_PROGRAM_D_PHASE1_DIR / "MODEL_COMPARISON_MATRIX.md"))
    add_edge(conclusion_node_id, model_node_id, EdgeType.EXPLAINS.value, 0.7, str(DC2_PROGRAM_D_PHASE1_DIR / "ARB_RECOMMENDATION.md"))
    add_edge(conclusion_node_id, evidence_node_id, EdgeType.SUPPORTED_BY.value, 0.69, str(DC2_PROGRAM_D_PHASE1_DIR / "EVIDENCE_SUMMARY.md"))
    add_edge(model_node_id, campaign_id, EdgeType.DERIVED_FROM.value, 0.71, str(DC2_PROGRAM_D_PHASE1_DIR / "INSTITUTIONAL_TRANSITION_ENGINE_VERIFICATION_REPORT.md"))
    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def run_dc2_program_d_phase1_campaign(repo_root: Path) -> dict[str, Any]:
    orchestrator = ResearchOrchestrator(base_dir=(repo_root / "data" / "ikros").resolve())
    spec = _default_campaign_spec()

    rq = ResearchQuestion.from_dict(_with_reproducibility_hash(spec["research_question_primary"]))
    exp = Experiment.from_dict(_with_reproducibility_hash(spec["experiment"]))
    task_payloads: dict[str, Any] = {
        TaskKind.RESEARCH_QUESTION.value: {"entity_type": "ResearchQuestion", "entity": rq.to_dict()},
        TaskKind.EXPERIMENT_REGISTRATION.value: {"entity_type": "Experiment", "entity": exp.to_dict()},
    }
    campaign = orchestrator.build_campaign(
        title=str(spec["title"]),
        objective="Attempt to falsify Institutional Transition Engine v1 against simple baseline transition models.",
        campaign_type="RESEARCH_AUDIT",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_campaign_pipeline(campaign, [TaskKind.RESEARCH_QUESTION.value, TaskKind.EXPERIMENT_REGISTRATION.value, TaskKind.FINAL_REPORT.value])

    analysis = prepare_dc2_program_d_phase1_artifacts(repo_root=repo_root)
    rq_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    exp_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    if not rq_registry.exists(rq.ikros_id):
        rq_registry.register(rq)
    if not exp_registry.exists(exp.ikros_id):
        exp_registry.register(exp)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_dc2_program_d_phase1_reports(analysis, campaign_result=report.to_dict(), repo_root=repo_root)
    graph_metrics = _upsert_graph_payload(repo_root, analysis, campaign.campaign_id)

    for rq_secondary in spec["research_questions_secondary"]:
        rq_id = str(rq_secondary["ikros_id"])
        if not rq_registry.exists(rq_id):
            try:
                rq_dict = {
                    "ikros_id": rq_id,
                    "entity_type": "ResearchQuestion",
                    "version": "1.0.0",
                    "lifecycle_state": "ANSWERED",
                    "confidence": {
                        "prior": 0.55,
                        "statistical": 0.57,
                        "economic": 0.63,
                        "data": 0.46,
                        "model": 0.58,
                        "validation": 0.52,
                        "replication": 0.0,
                        "operational": 0.5,
                        "last_updated": "2026-08-02T00:00:00Z",
                    },
                    "lineage": {
                        "origin": {
                            "created_by": "dc2-program-d-phase1",
                            "created_at": "2026-08-02T00:00:00Z",
                            "creation_context": "Program D secondary question",
                            "motivation": rq_secondary.get("statement", ""),
                        },
                        "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
                    },
                    "spec_refs": [],
                    "capability_refs": [],
                    "work_package_refs": [],
                    "version_history": [],
                    "title": f"DC2-PD1: {rq_secondary.get('theme', rq_id)}",
                    "motivation": str(rq_secondary.get("statement", "")),
                    "instrument": "XAU/USD",
                    "scope": "CROSS_ASSET",
                    "time_horizon": "1D",
                    "reproducibility_hash": compute_reproducibility_hash(rq_secondary),
                }
                rq_obj = ResearchQuestion.from_dict(rq_dict)
                rq_registry.register(rq_obj)
                rq_registry.link_conclusion(rq_id, campaign.campaign_id)
                _transition_if_needed(rq_registry, rq_id, "ANSWERED", note="Program D phase1 addressed verification theme.")
            except Exception:
                pass

    _transition_if_needed(rq_registry, rq.ikros_id, "ANSWERED", note="Program D phase1 completed.")
    _transition_if_needed(exp_registry, exp.ikros_id, "COMPLETE")

    metrics = {
        "phase": "DC2_PROGRAM_D_PHASE1",
        "campaign_id": campaign.campaign_id,
        "outcome": analysis["arb_recommendation"]["outcome"],
        "decision": analysis["arb_recommendation"]["decision"],
        "transition_engine_rank": analysis["evidence_summary"]["transition_engine_rank"],
        "models_evaluated": len(analysis["models_evaluated"]),
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "reports": report_paths,
    }
    (repo_root / "reports").mkdir(parents=True, exist_ok=True)
    write_json(repo_root / "reports" / "dc2-program-d-phase1-metrics.json", metrics)
    return {
        "campaign_id": campaign.campaign_id,
        "campaign_result": report.to_dict(),
        "analysis_summary": analysis["arb_recommendation"],
        "report_paths": report_paths,
        "metrics": metrics,
    }


def _default_campaign_spec() -> dict[str, Any]:
    return {
        "title": "DC2 Program D Phase 1: Institutional Transition Engine Verification & Falsification",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260802-7001",
            "entity_type": "ResearchQuestion",
            "version": "1.0.0",
            "lifecycle_state": "ANSWERED",
            "confidence": {
                "prior": 0.56,
                "statistical": 0.57,
                "economic": 0.64,
                "data": 0.46,
                "model": 0.58,
                "validation": 0.52,
                "replication": 0.0,
                "operational": 0.5,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc2-program-d-phase1",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "Program D phase1 primary question",
                    "motivation": "Transition Engine v1 is institutional hypothesis and must survive falsification.",
                },
                "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
            },
            "spec_refs": [],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "title": "DC2-PD1: Does Transition Engine v1 explain historical regime transitions better than simple baselines?",
            "motivation": "Scientific falsification requires baseline comparison before retaining governing model status.",
            "instrument": "XAU/USD",
            "scope": "CROSS_ASSET",
            "time_horizon": "1D",
            "reproducibility_hash": "dc2-program-d-phase1-rq-primary-v1",
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260802-7001",
            "entity_type": "Experiment",
            "version": "1.0.0",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.56,
                "statistical": 0.57,
                "economic": 0.64,
                "data": 0.46,
                "model": 0.58,
                "validation": 0.52,
                "replication": 0.0,
                "operational": 0.5,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc2-program-d-phase1",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "Program D phase1 verification experiment",
                    "motivation": "Compare Transition Engine to volatility, HMM, Markov, technical, macro, and random baselines.",
                },
                "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
            },
            "spec_refs": [],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "title": "DC2-PD1-EXP-001: Transition Engine Verification",
            "description": "Falsification program comparing Transition Engine v1 against required baseline transition models.",
            "reproducibility_hash": "dc2-program-d-phase1-exp-v1",
        },
        "research_questions_secondary": [
            {"ikros_id": "IKROS-RQ-20260802-7002", "theme": "Baseline Comparison", "statement": "Does the transition engine outperform volatility-only, HMM, Markov, technical, macro-only, and random baselines?"},
            {"ikros_id": "IKROS-RQ-20260802-7003", "theme": "Robustness", "statement": "Does the transition engine remain stable across stress, event, and out-of-sample subsets?"},
            {"ikros_id": "IKROS-RQ-20260802-7004", "theme": "Falsification", "statement": "Which assumptions fail under contradictory evidence and where does explanatory power degrade?"},
        ],
    }
