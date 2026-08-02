"""Discovery Cycle 2 Program E Phase 1 governed decomposition & ablation execution."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import write_json
from tools.alpha_research.transition_engine_ablation import (
    DC2_PROGRAM_E_PHASE1_DIR,
    emit_dc2_program_e_phase1_reports,
    prepare_dc2_program_e_phase1_artifacts,
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
        or result["reproducibility_hash"] == "dc2-program-e-phase1-v1"
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

    program_node_id = "IKROS-PE1-WORLDMODEL-20260802-0001"
    conclusion_node_id = "IKROS-PE1-CONCLUSION-20260802-0001"
    revision_node_id = "IKROS-PE1-REVISION-20260802-0001"

    top_level_nodes = [
        GraphNode(
            node_id=program_node_id,
            node_type=NodeType.WORLD_MODEL.value,
            ikros_id=program_node_id,
            label="Transition Engine Decomposition & Ablation Program",
            confidence=0.73,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes={"program": "DC2 Program E Phase 1"},
        ),
        GraphNode(
            node_id=conclusion_node_id,
            node_type=NodeType.RESEARCH_CONCLUSION.value,
            ikros_id=conclusion_node_id,
            label=str(payload["conclusion_node"]["label"]),
            confidence=0.71,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes=dict(payload["conclusion_node"]["attributes"]),
        ),
        GraphNode(
            node_id=revision_node_id,
            node_type=NodeType.VALIDATION.value,
            ikros_id=revision_node_id,
            label=str(payload["revision_node"]["label"]),
            confidence=0.70,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes=dict(payload["revision_node"]["attributes"]),
        ),
    ]

    component_nodes = [
        GraphNode(
            node_id=node["node_id"],
            node_type=NodeType.WORLD_MODEL.value,
            ikros_id=node["node_id"],
            label=str(node["label"]),
            confidence=0.68,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes=dict(node["attributes"]),
        )
        for node in payload["component_nodes"]
    ]

    for node in top_level_nodes + component_nodes:
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
        relation_map = {
            "EVALUATED": EdgeType.EVALUATED.value,
            "EXPLAINS": EdgeType.EXPLAINS.value,
        }
        mapped = relation_map.get(str(edge["relation"]), EdgeType.EVALUATED.value)
        add_edge(edge["source"], edge["target"], mapped, float(edge["confidence"]), str(DC2_PROGRAM_E_PHASE1_DIR / "COMPONENT_CONTRIBUTION_REPORT.md"))

    add_edge(program_node_id, conclusion_node_id, EdgeType.EXPLAINS.value, 0.72, str(DC2_PROGRAM_E_PHASE1_DIR / "COMPONENT_CONTRIBUTION_REPORT.md"))
    add_edge(conclusion_node_id, revision_node_id, EdgeType.EXPLAINS.value, 0.71, str(DC2_PROGRAM_E_PHASE1_DIR / "TRANSITION_ENGINE_REVISION_PLAN.md"))
    add_edge(program_node_id, campaign_id, EdgeType.DERIVED_FROM.value, 0.72, str(DC2_PROGRAM_E_PHASE1_DIR / "ARB_RECOMMENDATION.md"))

    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def run_dc2_program_e_phase1_campaign(repo_root: Path) -> dict[str, Any]:
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
        objective="Decompose Transition Engine v1 into testable components and measure incremental contribution via systematic ablation.",
        campaign_type="RESEARCH_AUDIT",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_campaign_pipeline(campaign, [TaskKind.RESEARCH_QUESTION.value, TaskKind.EXPERIMENT_REGISTRATION.value, TaskKind.FINAL_REPORT.value])

    analysis = prepare_dc2_program_e_phase1_artifacts(repo_root=repo_root)
    rq_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    exp_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    if not rq_registry.exists(rq.ikros_id):
        rq_registry.register(rq)
    if not exp_registry.exists(exp.ikros_id):
        exp_registry.register(exp)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_dc2_program_e_phase1_reports(analysis, campaign_result=report.to_dict(), repo_root=repo_root)
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
                        "statistical": 0.58,
                        "economic": 0.63,
                        "data": 0.47,
                        "model": 0.59,
                        "validation": 0.53,
                        "replication": 0.0,
                        "operational": 0.5,
                        "last_updated": "2026-08-02T00:00:00Z",
                    },
                    "lineage": {
                        "origin": {
                            "created_by": "dc2-program-e-phase1",
                            "created_at": "2026-08-02T00:00:00Z",
                            "creation_context": "Program E secondary question",
                            "motivation": rq_secondary.get("statement", ""),
                        },
                        "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
                    },
                    "spec_refs": [],
                    "capability_refs": [],
                    "work_package_refs": [],
                    "version_history": [],
                    "title": f"DC2-PE1: {rq_secondary.get('theme', rq_id)}",
                    "motivation": str(rq_secondary.get("statement", "")),
                    "instrument": "XAU/USD",
                    "scope": "CROSS_ASSET",
                    "time_horizon": "1D",
                    "reproducibility_hash": compute_reproducibility_hash(rq_secondary),
                }
                rq_obj = ResearchQuestion.from_dict(rq_dict)
                rq_registry.register(rq_obj)
                rq_registry.link_conclusion(rq_id, campaign.campaign_id)
                _transition_if_needed(rq_registry, rq_id, "ANSWERED", note="Program E phase1 addressed decomposition theme.")
            except Exception:
                pass

    _transition_if_needed(rq_registry, rq.ikros_id, "ANSWERED", note="Program E phase1 completed.")
    _transition_if_needed(exp_registry, exp.ikros_id, "COMPLETE")

    arb = analysis["arb_recommendation"]
    metrics = {
        "phase": "DC2_PROGRAM_E_PHASE1",
        "campaign_id": campaign.campaign_id,
        "components_evaluated": len(analysis["components_evaluated"]),
        "ablation_runs": analysis["ablation_run_count"],
        "components_to_retain": len(arb["components_to_retain"]),
        "components_to_redesign": len(arb["components_to_redesign"]),
        "components_to_remove": len(arb["components_to_remove"]),
        "components_to_investigate": len(arb["components_requiring_additional_evidence"]),
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "reports": report_paths,
    }
    (repo_root / "reports").mkdir(parents=True, exist_ok=True)
    write_json(repo_root / "reports" / "dc2-program-e-phase1-metrics.json", metrics)
    return {
        "campaign_id": campaign.campaign_id,
        "campaign_result": report.to_dict(),
        "analysis_summary": arb,
        "report_paths": report_paths,
        "metrics": metrics,
    }


def _default_campaign_spec() -> dict[str, Any]:
    return {
        "title": "DC2 Program E Phase 1: Institutional Transition Engine Decomposition & Ablation Analysis",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260802-8001",
            "entity_type": "ResearchQuestion",
            "version": "1.0.0",
            "lifecycle_state": "ANSWERED",
            "confidence": {
                "prior": 0.55,
                "statistical": 0.58,
                "economic": 0.63,
                "data": 0.47,
                "model": 0.59,
                "validation": 0.53,
                "replication": 0.0,
                "operational": 0.5,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc2-program-e-phase1",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "Program E phase1 primary question",
                    "motivation": "Identify which Transition Engine v1 components contribute meaningful explanatory power and which should be removed or redesigned.",
                },
                "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
            },
            "spec_refs": [],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "title": "DC2-PE1: Which Transition Engine components contribute meaningful explanatory power and which fail?",
            "motivation": "Program D concluded REQUIRES REVISION. Ablation identifies the revision target.",
            "instrument": "XAU/USD",
            "scope": "CROSS_ASSET",
            "time_horizon": "1D",
            "reproducibility_hash": "dc2-program-e-phase1-rq-primary-v1",
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260802-8001",
            "entity_type": "Experiment",
            "version": "1.0.0",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.55,
                "statistical": 0.58,
                "economic": 0.63,
                "data": 0.47,
                "model": 0.59,
                "validation": 0.53,
                "replication": 0.0,
                "operational": 0.5,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc2-program-e-phase1",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "Program E phase1 ablation experiment",
                    "motivation": "Systematic single, pairwise, and triple ablation of 7 engine components to isolate incremental contribution.",
                },
                "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
            },
            "spec_refs": [],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "title": "DC2-PE1-EXP-001: Transition Engine Ablation Study",
            "description": "Systematic ablation of Macro, Participant Ecology, Decision Ecology, Cross-Asset Network, Liquidity, Regime, and Interaction layers with single/pair/triple removal.",
            "reproducibility_hash": "dc2-program-e-phase1-exp-v1",
        },
        "research_questions_secondary": [
            {"ikros_id": "IKROS-RQ-20260802-8002", "theme": "Component Contribution", "statement": "Which components provide positive incremental gain in transition detection accuracy?"},
            {"ikros_id": "IKROS-RQ-20260802-8003", "theme": "Failure Attribution", "statement": "Which components are responsible for the five failure modes identified in Program D?"},
            {"ikros_id": "IKROS-RQ-20260802-8004", "theme": "Interaction Effects", "statement": "Are there synergistic or redundant interactions between pairs of engine components?"},
            {"ikros_id": "IKROS-RQ-20260802-8005", "theme": "Complexity Justification", "statement": "Is the full seven-layer complexity justified by performance outcomes?"},
        ],
    }
