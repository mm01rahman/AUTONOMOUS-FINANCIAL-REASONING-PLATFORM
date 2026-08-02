"""Generation 5 / Program 8 — governed runner for autonomous self-evolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.autonomous_research_organization_self_evolution import (
    PROGRAM8_DIR,
    emit_program8_reports,
    prepare_program8_artifacts,
)
from tools.alpha_research.reporting import write_json
from tools.ikros.graph import EdgeType, GraphNode, NodeType, YAMLGraphRepository
from tools.ikros.graph.models import GraphEdge
from tools.ikros.identifiers import compute_reproducibility_hash
from tools.ikros.models import Experiment, ResearchQuestion
from tools.ikros.orchestrator import (
    FailurePolicy,
    ResearchCampaign,
    ResearchOrchestrator,
    TaskKind,
)


def _with_hash(entity: dict[str, Any]) -> dict[str, Any]:
    payload = dict(entity)
    if "reproducibility_hash" not in payload:
        payload["reproducibility_hash"] = compute_reproducibility_hash(payload)
    return payload


def _select_pipeline(campaign: ResearchCampaign, task_kinds: list[str]) -> ResearchCampaign:
    selected = [task for task in campaign.tasks if task.kind in set(task_kinds)]
    ordered = sorted(
        selected, key=lambda task: task_kinds.index(task.kind) if task.kind in task_kinds else 999
    )
    for index, task in enumerate(ordered):
        task.depends_on = [ordered[index - 1].task_id] if index > 0 else []
    campaign.tasks = ordered
    campaign.pipeline.task_ids = [task.task_id for task in ordered]
    campaign.pipeline.stages = [task.kind for task in ordered]
    return campaign


def _upsert_graph(repo_root: Path, analysis: dict[str, Any], campaign_id: str) -> dict[str, int]:
    graph_repo = YAMLGraphRepository((repo_root / "data" / "ikros" / "graph").resolve())
    graph = graph_repo.load()
    created_nodes = 0
    created_edges = 0
    relation_index = {(edge.source_id, edge.target_id, edge.edge_type) for edge in graph.edges()}

    def add_node(node_id: str, label: str, confidence: float) -> None:
        nonlocal created_nodes
        if graph.has_node(node_id):
            return
        graph.add_node(
            GraphNode(
                node_id=node_id,
                node_type=NodeType.RESEARCH_CONCLUSION.value,
                ikros_id=node_id,
                label=label,
                confidence=confidence,
                spec_refs=["SPEC-061"],
                wp_refs=["WP-IMP-0058"],
                attributes={},
            )
        )
        created_nodes += 1

    def add_edge(source_id: str, target_id: str, edge_type: str, confidence: float) -> None:
        nonlocal created_edges
        key = (source_id, target_id, edge_type)
        if key in relation_index:
            return
        if not graph.has_node(source_id) or not graph.has_node(target_id):
            return
        graph.add_edge(
            GraphEdge(
                edge_id=graph.next_edge_id(),
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                confidence=confidence,
                evidence_ref=str(PROGRAM8_DIR / "FINAL_REPORT.md"),
                spec_ref="SPEC-061",
                wp_ref="WP-IMP-0058",
                attributes={},
            )
        )
        relation_index.add(key)
        created_edges += 1

    add_node("PROGRAM8-META-ORG", "Generation 5 Autonomous Research Organization", 0.93)
    add_node("PROGRAM7-INTELLIGENCE", "Generation 4 Institutional Intelligence", 0.91)
    add_edge("PROGRAM8-META-ORG", "PROGRAM7-INTELLIGENCE", EdgeType.DERIVED_FROM.value, 0.88)
    for row in cast(list[dict[str, Any]], analysis["improvement_registry"]):
        node_id = f"IKROS-IMPROVEMENT-{row['improvement_id']}"
        add_node(node_id, str(row["title"]), 0.79)
        add_edge("PROGRAM8-META-ORG", node_id, EdgeType.RELATED_TO.value, 0.77)
    add_edge("PROGRAM8-META-ORG", campaign_id, EdgeType.DERIVED_FROM.value, 0.84)
    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _campaign_spec() -> dict[str, Any]:
    return {
        "title": "Generation 5 — Autonomous Research Organization & Self-Evolution",
        "rq": {
            "ikros_id": "IKROS-RQ-20260803-0059",
            "title": "Generation 5 Primary Research Question",
            "question": (
                "Can AFRP continuously evaluate and improve its own institutional "
                "research process, prioritize improvements by evidence and expected "
                "value, and produce governed strategic roadmaps autonomously?"
            ),
            "category": "MECHANISM_VALIDATION",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "confidence": {
                "prior": 0.78,
                "statistical": 0.0,
                "economic": 0.76,
                "data": 0.75,
                "model": 0.79,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "program8-self-evolution",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Generation 5 autonomous institutional organization",
                    "motivation": (
                        "Create a permanent meta-research and self-improvement loop "
                        "without introducing execution pathways."
                    ),
                }
            },
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260803-0059",
            "title": "Generation 5 Autonomous Self-Evolution Integration",
            "experiment_type": "MECHANISM_VALIDATION",
            "hypothesis_under_test": "IKROS-HYP-20260803-0059",
            "dataset_refs": [
                "meta_research_registry.json",
                "self_evaluation_registry.json",
                "improvement_registry.json",
            ],
            "methodology": "autonomous_research_organization_self_evolution_v1",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.77,
                "statistical": 0.0,
                "economic": 0.75,
                "data": 0.74,
                "model": 0.78,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "program8-self-evolution",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Generation 5 governed autonomy campaign",
                    "motivation": (
                        "Operate AFRP as a continuously self-improving institutional "
                        "research organization."
                    ),
                }
            },
        },
    }


def run_program8_autonomous_research_organization(repo_root: Path) -> dict[str, Any]:
    """Execute Generation 5 and persist governed self-evolution artifacts."""
    orchestrator = ResearchOrchestrator(base_dir=(repo_root / "data" / "ikros").resolve())
    spec = _campaign_spec()
    rq = ResearchQuestion.from_dict(_with_hash(spec["rq"]))
    exp = Experiment.from_dict(_with_hash(spec["experiment"]))
    task_payloads: dict[str, Any] = {
        TaskKind.RESEARCH_QUESTION.value: {
            "entity_type": "ResearchQuestion",
            "entity": rq.to_dict(),
        },
        TaskKind.EXPERIMENT_REGISTRATION.value: {
            "entity_type": "Experiment",
            "entity": exp.to_dict(),
        },
    }
    campaign = orchestrator.build_campaign(
        title=str(spec["title"]),
        objective=(
            "Evaluate AFRP research-system quality, identify bottlenecks, rank "
            "improvements, apply autonomous ARB pre-screening, and emit governed "
            "roadmaps and organizational memory updates."
        ),
        campaign_type="HYPOTHESIS_VALIDATION",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_pipeline(
        campaign,
        [
            TaskKind.RESEARCH_QUESTION.value,
            TaskKind.EXPERIMENT_REGISTRATION.value,
            TaskKind.STATISTICAL_EVALUATION.value,
            TaskKind.FINAL_REPORT.value,
        ],
    )
    analysis = prepare_program8_artifacts()
    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_program8_reports(analysis, report.to_dict(), repo_root=repo_root)
    graph_metrics = _upsert_graph(repo_root, analysis, campaign.campaign_id)
    metrics = {
        "campaign_id": campaign.campaign_id,
        "program": analysis["program"],
        "top_priority_improvement": analysis["institutional_organization_registry"][
            "top_priority_improvement"
        ],
        "approved_improvements": analysis["institutional_organization_registry"][
            "approved_improvements"
        ],
        "overall_scientific_health": analysis["institutional_organization_registry"][
            "overall_scientific_health"
        ],
        "research_roi": analysis["institutional_organization_registry"]["research_roi"],
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "report_paths": report_paths,
    }
    write_json(repo_root / PROGRAM8_DIR / "program8_metrics.json", metrics)
    return metrics


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_program8_autonomous_research_organization(root)
    print(
        "Program 8 complete - "
        f"top={result['top_priority_improvement']}, "
        f"approved={result['approved_improvements']}, "
        f"health={result['overall_scientific_health']}"
    )
