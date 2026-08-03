"""Discovery Cycle 2 Program F Phase 1 governed institutional theory extraction execution."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.institutional_theory_extraction import (
    DC2_PROGRAM_F_PHASE1_DIR,
    emit_dc2_program_f_phase1_reports,
    prepare_dc2_program_f_phase1_artifacts,
)
from tools.alpha_research.reporting import write_json
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
        or result["reproducibility_hash"] == "dc2-program-f-phase1-v1"
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
    payload = cast(dict[str, Any], analysis["ecology_knowledge_graph"])
    created_nodes = 0
    created_edges = 0

    program_node_id = "IKROS-PF1-WORLDMODEL-20260802-0001"
    conclusion_node_id = "IKROS-PF1-CONCLUSION-20260802-0001"
    constraints_node_id = "IKROS-PF1-CONSTRAINTS-20260802-0001"

    top_nodes = [
        GraphNode(
            node_id=program_node_id,
            node_type=NodeType.WORLD_MODEL.value,
            ikros_id=program_node_id,
            label="Institutional Theory Extraction Program",
            confidence=0.76,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes={"program": "DC2 Program F Phase 1"},
        ),
        GraphNode(
            node_id=conclusion_node_id,
            node_type=NodeType.RESEARCH_CONCLUSION.value,
            ikros_id=conclusion_node_id,
            label=str(payload["conclusion_node"]["label"]),
            confidence=0.75,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes=dict(payload["conclusion_node"]["attributes"]),
        ),
        GraphNode(
            node_id=constraints_node_id,
            node_type=NodeType.KNOWLEDGE_OBJECT.value,
            ikros_id=constraints_node_id,
            label=str(payload["constraints_node"]["label"]),
            confidence=0.74,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes=dict(payload["constraints_node"]["attributes"]),
        ),
    ]

    principle_nodes: list[GraphNode] = []
    for item in cast(list[dict[str, Any]], payload["principle_nodes"]):
        cls = str(item["classification"])
        node_type = NodeType.KNOWLEDGE_OBJECT.value if cls != "REJECTED_PRINCIPLE" else NodeType.FAILURE.value
        principle_nodes.append(
            GraphNode(
                node_id=str(item["node_id"]),
                node_type=node_type,
                ikros_id=str(item["node_id"]),
                label=str(item["label"]),
                confidence=float(item["confidence"]),
                spec_refs=["SPEC-060"],
                wp_refs=["WP-IMP-0048"],
                attributes={"classification": cls},
            )
        )

    for node in top_nodes + principle_nodes:
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

    for edge in cast(list[dict[str, Any]], payload["edges"]):
        relation = str(edge["relation"])
        if relation == "SUPPORTED_BY":
            edge_type = EdgeType.SUPPORTED_BY.value
        elif relation == "REFUTES":
            edge_type = EdgeType.REFUTES.value
        else:
            edge_type = EdgeType.RELATED_TO.value
        add_edge(str(edge["source"]), str(edge["target"]), edge_type, float(edge["confidence"]), str(DC2_PROGRAM_F_PHASE1_DIR / "SCIENTIFIC_PRINCIPLE_REGISTRY.md"))

    add_edge(program_node_id, conclusion_node_id, EdgeType.EXPLAINS.value, 0.78, str(DC2_PROGRAM_F_PHASE1_DIR / "INSTITUTIONAL_THEORY_REPORT.md"))
    add_edge(conclusion_node_id, constraints_node_id, EdgeType.EXPLAINS.value, 0.77, str(DC2_PROGRAM_F_PHASE1_DIR / "ARCHITECTURE_CONSTRAINTS_FOR_FUTURE_MODELS.md"))
    add_edge(program_node_id, campaign_id, EdgeType.DERIVED_FROM.value, 0.78, str(DC2_PROGRAM_F_PHASE1_DIR / "ARB_RECOMMENDATION.md"))

    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def run_dc2_program_f_phase1_campaign(repo_root: Path) -> dict[str, Any]:
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
        objective="Extract enduring scientific principles from Programs A-E into institutional axioms, rejected principles, and future architecture constraints.",
        campaign_type="RESEARCH_AUDIT",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_campaign_pipeline(campaign, [TaskKind.RESEARCH_QUESTION.value, TaskKind.EXPERIMENT_REGISTRATION.value, TaskKind.FINAL_REPORT.value])

    analysis = prepare_dc2_program_f_phase1_artifacts(repo_root=repo_root)
    rq_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    exp_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    if not rq_registry.exists(rq.ikros_id):
        rq_registry.register(rq)
    if not exp_registry.exists(exp.ikros_id):
        exp_registry.register(exp)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_dc2_program_f_phase1_reports(analysis, campaign_result=report.to_dict(), repo_root=repo_root)
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
                        "prior": 0.57,
                        "statistical": 0.6,
                        "economic": 0.67,
                        "data": 0.51,
                        "model": 0.58,
                        "validation": 0.56,
                        "replication": 0.0,
                        "operational": 0.5,
                        "last_updated": "2026-08-02T00:00:00Z",
                    },
                    "lineage": {
                        "origin": {
                            "created_by": "dc2-program-f-phase1",
                            "created_at": "2026-08-02T00:00:00Z",
                            "creation_context": "Program F secondary question",
                            "motivation": rq_secondary.get("statement", ""),
                        },
                        "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
                    },
                    "spec_refs": [],
                    "capability_refs": [],
                    "work_package_refs": [],
                    "version_history": [],
                    "title": f"DC2-PF1: {rq_secondary.get('theme', rq_id)}",
                    "motivation": str(rq_secondary.get("statement", "")),
                    "instrument": "XAU/USD",
                    "scope": "CROSS_ASSET",
                    "time_horizon": "1D",
                    "reproducibility_hash": compute_reproducibility_hash(rq_secondary),
                }
                rq_obj = ResearchQuestion.from_dict(rq_dict)
                rq_registry.register(rq_obj)
                rq_registry.link_conclusion(rq_id, campaign.campaign_id)
                _transition_if_needed(rq_registry, rq_id, "ANSWERED", note="Program F phase1 addressed theory extraction theme.")
            except Exception:
                pass

    _transition_if_needed(rq_registry, rq.ikros_id, "ANSWERED", note="Program F phase1 completed.")
    _transition_if_needed(exp_registry, exp.ikros_id, "COMPLETE")

    arb = cast(dict[str, Any], analysis["arb_recommendation"])
    metrics = {
        "phase": "DC2_PROGRAM_F_PHASE1",
        "campaign_id": campaign.campaign_id,
        "principles_total": len(cast(list[dict[str, Any]], analysis["scientific_principle_registry"])),
        "axioms": len(cast(list[dict[str, Any]], analysis["institutional_axiom_registry"])),
        "supported": len(cast(list[dict[str, Any]], analysis["supported_principles"])),
        "conditional": len(cast(list[dict[str, Any]], analysis["conditional_principles"])),
        "rejected": len(cast(list[dict[str, Any]], analysis["rejected_principles"])),
        "open_questions": len(cast(list[dict[str, Any]], analysis["open_research_questions"])),
        "constraints": len(cast(list[str], arb["architecture_constraints"])),
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "reports": report_paths,
    }
    (repo_root / "reports").mkdir(parents=True, exist_ok=True)
    write_json(repo_root / "reports" / "dc2-program-f-phase1-metrics.json", metrics)
    return {
        "campaign_id": campaign.campaign_id,
        "campaign_result": report.to_dict(),
        "analysis_summary": arb,
        "report_paths": report_paths,
        "metrics": metrics,
    }


def _default_campaign_spec() -> dict[str, Any]:
    return {
        "title": "DC2 Program F Phase 1: Institutional Theory Extraction",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260802-9001",
            "entity_type": "ResearchQuestion",
            "version": "1.0.0",
            "lifecycle_state": "ANSWERED",
            "confidence": {
                "prior": 0.57,
                "statistical": 0.6,
                "economic": 0.67,
                "data": 0.51,
                "model": 0.58,
                "validation": 0.56,
                "replication": 0.0,
                "operational": 0.5,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc2-program-f-phase1",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "Program F phase1 primary question",
                    "motivation": "Extract enduring scientific principles from Discovery Cycle 2 after Program E showed no retained v1 component.",
                },
                "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
            },
            "spec_refs": [],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "title": "DC2-PF1: Which Discovery Cycle 2 principles are sufficiently supported to constrain future AFRP architecture?",
            "motivation": "Institutional theory extraction is required before any future architecture revision.",
            "instrument": "XAU/USD",
            "scope": "CROSS_ASSET",
            "time_horizon": "1D",
            "reproducibility_hash": "dc2-program-f-phase1-rq-primary-v1",
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260802-9001",
            "entity_type": "Experiment",
            "version": "1.0.0",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.57,
                "statistical": 0.6,
                "economic": 0.67,
                "data": 0.51,
                "model": 0.58,
                "validation": 0.56,
                "replication": 0.0,
                "operational": 0.5,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc2-program-f-phase1",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "Program F phase1 synthesis experiment",
                    "motivation": "Consolidate Programs A-E evidence into axioms, supported/conditional/rejected principles, open questions, and architecture constraints.",
                },
                "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
            },
            "spec_refs": [],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "title": "DC2-PF1-EXP-001: Institutional Theory Consolidation",
            "description": "Cross-program theory extraction over Program A-E outputs, including falsification and ablation evidence.",
            "reproducibility_hash": "dc2-program-f-phase1-exp-v1",
        },
        "research_questions_secondary": [
            {"ikros_id": "IKROS-RQ-20260802-9002", "theme": "Axiom Extraction", "statement": "Which principles survived verification/falsification strongly enough to become institutional axioms?"},
            {"ikros_id": "IKROS-RQ-20260802-9003", "theme": "Rejection Boundaries", "statement": "Which Discovery Cycle 2 principles are rejected by Program D/E evidence and must not constrain future architecture?"},
            {"ikros_id": "IKROS-RQ-20260802-9004", "theme": "Uncertainty", "statement": "Which principles remain conditional or unresolved due evidence limitations and require further research?"},
            {"ikros_id": "IKROS-RQ-20260802-9005", "theme": "Architecture Constraints", "statement": "What explicit constraints should all future AFRP transition architectures satisfy?"},
        ],
    }
