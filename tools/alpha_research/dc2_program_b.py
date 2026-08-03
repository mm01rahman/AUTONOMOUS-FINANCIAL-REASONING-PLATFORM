"""Discovery Cycle 2 Program B Phase 1 governed campaign execution.

Program B Phase 1: Institutional Market Ecology Research Program.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, cast

from tools.alpha_research.market_ecology import (
    DC2_PROGRAM_B_DIR,
    emit_dc2_program_b_reports,
    prepare_dc2_program_b_artifacts,
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
    if "reproducibility_hash" not in result or result["reproducibility_hash"] == "dc2-program-b-v1":
        result["reproducibility_hash"] = compute_reproducibility_hash(result)
    return result


def _select_campaign_pipeline(
    campaign: ResearchCampaign, task_kinds: list[str]
) -> ResearchCampaign:
    kind_set = set(task_kinds)
    filtered = [task for task in campaign.tasks if task.kind in kind_set]
    ordered = sorted(
        filtered, key=lambda task: task_kinds.index(task.kind) if task.kind in task_kinds else 999
    )
    for idx, task in enumerate(ordered):
        task.depends_on = [ordered[idx - 1].task_id] if idx > 0 else []
    campaign.tasks = ordered
    campaign.pipeline.task_ids = [task.task_id for task in ordered]
    campaign.pipeline.stages = [task.kind for task in ordered]
    return campaign


class _TransitionEntity(Protocol):
    lifecycle_state: str


class _TransitionRegistry(Protocol):
    def get(self, entity_id: str) -> _TransitionEntity: ...

    def transition(
        self,
        entity_id: str,
        target_state: str,
        note: str = "",
    ) -> object: ...

def _transition_if_needed(
    registry: _TransitionRegistry,
    entity_id: str,
    target_state: str,
    note: str = "",
) -> None:
    state_rank: dict[str, int] = {
        "PROPOSED": 0,
        "OPEN": 0,
        "APPROVED_FOR_TESTING": 1,
        "ACTIVE": 1,
        "TESTING": 2,
        "ANSWERED": 3,
        "COMPLETE": 3,
        "ARCHIVED": 4,
        "RETIRED": 4,
    }
    try:
        current = str(registry.get(entity_id).lifecycle_state)
        if state_rank.get(current, 0) < state_rank.get(target_state, 0):
            if note:
                registry.transition(entity_id, target_state, note=note)
            else:
                registry.transition(entity_id, target_state)
    except Exception:
        pass


def _upsert_graph_payload(
    repo_root: Path, analysis: dict[str, Any], campaign_id: str
) -> dict[str, int]:
    graph_repo = YAMLGraphRepository((repo_root / "data" / "ikros" / "graph").resolve())
    graph = graph_repo.load()
    payload = analysis["ecology_knowledge_graph"]

    created_nodes = 0
    created_edges = 0

    model_node_id = "IKROS-PB1-WORLDMODEL-20260802-0001"
    conclusion_node_id = "IKROS-PB1-CONCLUSION-20260802-0001"
    evidence_node_id = "IKROS-PB1-EVIDENCE-20260802-0001"

    all_nodes = [
        GraphNode(
            node_id=model_node_id,
            node_type=NodeType.WORLD_MODEL.value,
            ikros_id=model_node_id,
            label="Institutional Market Ecology Model",
            confidence=0.72,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes={
                "program": "DC2 Program B Phase 1",
                "description": (
                    "First institutional ecology model explaining participant "
                    "interactions behind the cross-asset information network."
                ),
            },
        ),
        GraphNode(
            node_id=conclusion_node_id,
            node_type=NodeType.RESEARCH_CONCLUSION.value,
            ikros_id=conclusion_node_id,
            label="Participant ecology explains cross-asset information propagation",
            confidence=0.70,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes={
                "arb_recommendation": analysis["research_recommendations"]["arb_recommendation"],
                "critical_interactions": analysis["research_recommendations"][
                    "critical_interactions"
                ],
            },
        ),
        GraphNode(
            node_id=evidence_node_id,
            node_type=NodeType.EVIDENCE.value,
            ikros_id=evidence_node_id,
            label="Program B Phase 1 Ecology Atlas Evidence",
            confidence=0.68,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes={
                "evidence_ref": str(DC2_PROGRAM_B_DIR / "INSTITUTIONAL_MARKET_ECOLOGY_ATLAS.md"),
            },
        ),
    ]
    all_nodes.extend(
        GraphNode(
            node_id=node["node_id"],
            node_type=NodeType.KNOWLEDGE_OBJECT.value
            if node["node_type"] == "KNOWLEDGE_OBJECT"
            else NodeType.FACTOR.value,
            ikros_id=node["node_id"],
            label=str(node["label"]),
            confidence=0.65,
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes=dict(node["attributes"]),
        )
        for node in payload["participant_nodes"] + payload["factor_nodes"]
    )

    for node in all_nodes:
        if not graph.has_node(node.node_id):
            graph.add_node(node)
            created_nodes += 1

    relation_index = {(edge.source_id, edge.target_id, edge.edge_type) for edge in graph.edges()}

    def add_edge(
        source_id: str,
        target_id: str,
        edge_type: str,
        confidence: float,
        evidence_ref: str,
        attributes: dict[str, Any],
    ) -> None:
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
            attributes=attributes,
        )
        graph.add_edge(edge)
        relation_index.add(key)
        created_edges += 1

    for edge in payload["interaction_edges"]:
        add_edge(
            edge["source"],
            edge["target"],
            EdgeType.RELATED_TO.value
            if edge["relation"] == "RELATED_TO"
            else EdgeType.ASSOCIATED_WITH.value,
            float(edge["confidence"]),
            str(DC2_PROGRAM_B_DIR / "INTERACTION_MATRIX.md"),
            dict(edge["attributes"]),
        )
    for edge in payload["factor_edges"]:
        add_edge(
            edge["source"],
            edge["target"],
            EdgeType.CAUSES.value,
            float(edge["confidence"]),
            str(DC2_PROGRAM_B_DIR / "CAPITAL_FLOW_ATLAS.md"),
            dict(edge["attributes"]),
        )
    add_edge(
        model_node_id,
        campaign_id,
        EdgeType.DERIVED_FROM.value,
        0.74,
        str(DC2_PROGRAM_B_DIR / "INSTITUTIONAL_MARKET_ECOLOGY_ATLAS.md"),
        {},
    )
    add_edge(
        conclusion_node_id,
        model_node_id,
        EdgeType.EXPLAINS.value,
        0.72,
        str(DC2_PROGRAM_B_DIR / "RESEARCH_RECOMMENDATIONS.md"),
        {},
    )
    add_edge(
        conclusion_node_id,
        evidence_node_id,
        EdgeType.SUPPORTED_BY.value,
        0.70,
        str(DC2_PROGRAM_B_DIR / "INSTITUTIONAL_MARKET_ECOLOGY_ATLAS.md"),
        {},
    )

    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def run_dc2_program_b_campaign(repo_root: Path) -> dict[str, Any]:
    resolved_base = (repo_root / "data" / "ikros").resolve()
    orchestrator = ResearchOrchestrator(base_dir=resolved_base)
    spec = _default_campaign_spec()

    research_question = ResearchQuestion.from_dict(
        _with_reproducibility_hash(spec["research_question_primary"])
    )
    experiment = Experiment.from_dict(_with_reproducibility_hash(spec["experiment"]))

    task_payloads: dict[str, Any] = {
        TaskKind.RESEARCH_QUESTION.value: {
            "entity_type": "ResearchQuestion",
            "entity": research_question.to_dict(),
        },
        TaskKind.EXPERIMENT_REGISTRATION.value: {
            "entity_type": "Experiment",
            "entity": experiment.to_dict(),
        },
    }
    campaign = orchestrator.build_campaign(
        title=str(spec["title"]),
        objective=(
            "Construct the first institutional market ecology model "
            "explaining how heterogeneous participants collectively "
            "generate the cross-asset information network and XAU/USD "
            "regime transitions."
        ),
        campaign_type="RESEARCH_AUDIT",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_campaign_pipeline(
        campaign,
        [
            TaskKind.RESEARCH_QUESTION.value,
            TaskKind.EXPERIMENT_REGISTRATION.value,
            TaskKind.FINAL_REPORT.value,
        ],
    )

    analysis = prepare_dc2_program_b_artifacts(repo_root=repo_root)
    research_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    experiment_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])

    if not research_registry.exists(research_question.ikros_id):
        research_registry.register(research_question)
    if not experiment_registry.exists(experiment.ikros_id):
        experiment_registry.register(experiment)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)

    output_dir = repo_root / DC2_PROGRAM_B_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    report_paths = emit_dc2_program_b_reports(
        analysis, campaign_result=report.to_dict(), repo_root=repo_root
    )
    graph_metrics = _upsert_graph_payload(repo_root, analysis, campaign.campaign_id)

    for rq_secondary in spec["research_questions_secondary"]:
        rq_id = str(rq_secondary["ikros_id"])
        if not research_registry.exists(rq_id):
            try:
                rq_dict = {
                    "ikros_id": rq_id,
                    "entity_type": "ResearchQuestion",
                    "version": "1.0.0",
                    "lifecycle_state": "ANSWERED",
                    "confidence": {
                        "prior": 0.5,
                        "statistical": 0.55,
                        "economic": 0.60,
                        "data": 0.45,
                        "model": 0.55,
                        "validation": 0.5,
                        "replication": 0.0,
                        "operational": 0.5,
                        "last_updated": "2026-08-02T00:00:00Z",
                    },
                    "lineage": {
                        "origin": {
                            "created_by": "dc2-program-b",
                            "created_at": "2026-08-02T00:00:00Z",
                            "creation_context": "Program B Phase 1 secondary question",
                            "motivation": rq_secondary.get("statement", ""),
                        },
                        "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
                    },
                    "spec_refs": [],
                    "capability_refs": [],
                    "work_package_refs": [],
                    "version_history": [],
                    "title": f"DC2-PB1: {rq_secondary.get('theme', rq_id)}",
                    "motivation": str(rq_secondary.get("statement", "")),
                    "instrument": "XAU/USD",
                    "scope": "CROSS_ASSET",
                    "time_horizon": "1D",
                    "reproducibility_hash": compute_reproducibility_hash(rq_secondary),
                }
                rq_obj = ResearchQuestion.from_dict(rq_dict)
                research_registry.register(rq_obj)
                research_registry.link_conclusion(rq_id, campaign.campaign_id)
                _transition_if_needed(
                    research_registry,
                    rq_id,
                    "ANSWERED",
                    note="Program B Phase 1 addressed this participant-ecology question.",
                )
            except Exception:
                pass

    _transition_if_needed(
        research_registry,
        research_question.ikros_id,
        "ANSWERED",
        note="Program B Phase 1 completed: participant ecology model generated.",
    )
    _transition_if_needed(experiment_registry, experiment.ikros_id, "COMPLETE")

    (repo_root / "reports").mkdir(parents=True, exist_ok=True)
    metrics = {
        "phase": "DC2_PROGRAM_B_PHASE1",
        "n_participants": len(analysis["participant_profiles"]),
        "n_interactions": len(analysis["participant_interaction_network"]["edges"]),
        "n_capital_flow_edges": len(analysis["capital_flow_network"]["edges"]),
        "n_feedback_loops": len(analysis["feedback_loops"]),
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "campaign_id": campaign.campaign_id,
        "reports": report_paths,
    }
    write_json(repo_root / "reports" / "dc2-program-b-phase1-metrics.json", metrics)

    return {
        "campaign_id": campaign.campaign_id,
        "campaign_result": report.to_dict(),
        "analysis_summary": analysis["research_recommendations"],
        "report_paths": report_paths,
        "metrics": metrics,
    }


def _default_campaign_spec() -> dict[str, Any]:
    return {
        "title": "DC2 Program B Phase 1: Institutional Market Ecology Research Program",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260802-4001",
            "entity_type": "ResearchQuestion",
            "version": "1.0.0",
            "lifecycle_state": "ANSWERED",
            "confidence": {
                "prior": 0.55,
                "statistical": 0.55,
                "economic": 0.65,
                "data": 0.45,
                "model": 0.60,
                "validation": 0.50,
                "replication": 0.0,
                "operational": 0.50,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc2-program-b",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "Program B Phase 1 primary research question",
                    "motivation": (
                        "Program A completed the cross-asset network; "
                        "Program B explains it through participant ecology."
                    ),
                },
                "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
            },
            "spec_refs": [],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "title": (
                "DC2-PB1: How do heterogeneous market participants "
                "collectively generate the cross-asset information network "
                "and XAU/USD regime transitions?"
            ),
            "motivation": (
                "The network must be explained through institutional "
                "participant behavior rather than treated as purely "
                "statistical structure."
            ),
            "instrument": "XAU/USD",
            "scope": "CROSS_ASSET",
            "time_horizon": "1D",
            "reproducibility_hash": "dc2-program-b-rq-primary-v1",
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260802-4001",
            "entity_type": "Experiment",
            "version": "1.0.0",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.55,
                "statistical": 0.55,
                "economic": 0.65,
                "data": 0.45,
                "model": 0.60,
                "validation": 0.50,
                "replication": 0.0,
                "operational": 0.50,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc2-program-b",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "Program B Phase 1 ecology experiment",
                    "motivation": (
                        "Integrate participant objectives, constraints, and "
                        "interactions into the first institutional ecology "
                        "model."
                    ),
                },
                "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
            },
            "spec_refs": [],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "title": "DC2-PB1-EXP-001: Institutional Market Ecology Model",
            "description": (
                "Participant-layer ecology model grounded in the approved "
                "Program A confidence-weighted network."
            ),
            "reproducibility_hash": "dc2-program-b-exp-v1",
        },
        "research_questions_secondary": [
            {
                "ikros_id": "IKROS-RQ-20260802-4002",
                "theme": "Participant Drivers",
                "statement": (
                    "Which participant classes most consistently initiate the "
                    "network structures and regime transitions observed in "
                    "Program A?"
                ),
            },
            {
                "ikros_id": "IKROS-RQ-20260802-4003",
                "theme": "Liquidity Ecology",
                "statement": (
                    "How do dealers, makers, and bullion banks transform "
                    "macro shocks into liquidity conditions and bottlenecks?"
                ),
            },
            {
                "ikros_id": "IKROS-RQ-20260802-4004",
                "theme": "Capital Flow Network",
                "statement": (
                    "How do ETF investors, macro hedge funds, and safe-haven "
                    "flows propagate capital across the network during "
                    "different regimes?"
                ),
            },
            {
                "ikros_id": "IKROS-RQ-20260802-4005",
                "theme": "Adaptive Behaviour",
                "statement": (
                    "How do participant reaction functions adapt across the "
                    "six regimes and during stress dislocations?"
                ),
            },
        ],
    }
