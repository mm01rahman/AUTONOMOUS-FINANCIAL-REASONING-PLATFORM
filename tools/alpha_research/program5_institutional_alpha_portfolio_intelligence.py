"""Program 5 — governed runner for institutional alpha portfolio intelligence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.institutional_alpha_portfolio_intelligence import (
    PROGRAM5_DIR,
    emit_program5_reports,
    prepare_program5_artifacts,
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


def _upsert_graph(
    repo_root: Path, analysis: dict[str, Any], campaign_id: str
) -> dict[str, int]:
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
                spec_refs=["SPEC-060"],
                wp_refs=["WP-IMP-0055"],
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
                evidence_ref=str(PROGRAM5_DIR / "FINAL_REPORT.md"),
                spec_ref="SPEC-060",
                wp_ref="WP-IMP-0055",
                attributes={},
            )
        )
        relation_index.add(key)
        created_edges += 1

    add_node("PROGRAM5-PORTFOLIO", "Program 5 Institutional Portfolio", 0.88)
    for row in cast(list[dict[str, Any]], analysis["allocation_registry"]):
        alpha_id = str(row["alpha_id"])
        add_node(
            alpha_id,
            f"{row['mechanism']} portfolio constituent",
            float(row["confidence_weight"]),
        )
        add_edge("PROGRAM5-PORTFOLIO", alpha_id, EdgeType.RELATED_TO.value, 0.82)
    add_edge("PROGRAM5-PORTFOLIO", campaign_id, EdgeType.DERIVED_FROM.value, 0.79)
    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _campaign_spec() -> dict[str, Any]:
    return {
        "title": "Program 5 — Institutional Alpha Portfolio Intelligence System",
        "rq": {
            "ikros_id": "IKROS-RQ-20260803-0056",
            "title": "Program 5 Primary Research Question",
            "question": (
                "Can AFRP autonomously construct, explain, govern, and maintain an "
                "institutional alpha portfolio from the approved alpha library without "
                "introducing execution infrastructure?"
            ),
            "category": "MECHANISM_VALIDATION",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "confidence": {
                "prior": 0.72,
                "statistical": 0.0,
                "economic": 0.71,
                "data": 0.69,
                "model": 0.73,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "program5-portfolio-intelligence",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Program 5 portfolio intelligence bootstrap",
                    "motivation": (
                        "Turn the approved alpha library into a governed "
                        "institutional portfolio."
                    ),
                }
            },
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260803-0056",
            "title": "Program 5 Portfolio Intelligence Integration",
            "experiment_type": "MECHANISM_VALIDATION",
            "hypothesis_under_test": "IKROS-HYP-20260803-0056",
            "dataset_refs": [
                "approved_alpha_registry.json",
                "mechanism_independence_matrix.json",
                "institutional_correlation_atlas.json",
            ],
            "methodology": "institutional_alpha_portfolio_intelligence_v1",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.71,
                "statistical": 0.0,
                "economic": 0.70,
                "data": 0.68,
                "model": 0.72,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "program5-portfolio-intelligence",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Program 5 portfolio-construction campaign",
                    "motivation": (
                        "Construct a governed institutional portfolio from the "
                        "approved alpha library."
                    ),
                }
            },
        },
    }


def run_program5_portfolio_intelligence(repo_root: Path) -> dict[str, Any]:
    """Execute Program 5 and persist governed portfolio-intelligence artifacts."""
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
            "Transform the approved institutional alpha library into a governed "
            "portfolio with explainable allocation, conflict resolution, risk, "
            "capacity, lifecycle, and regime-aware decision logic."
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

    analysis = prepare_program5_artifacts()
    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_program5_reports(analysis, report.to_dict(), repo_root=repo_root)
    graph_metrics = _upsert_graph(repo_root, analysis, campaign.campaign_id)

    metrics = {
        "campaign_id": campaign.campaign_id,
        "program": analysis["program"],
        "portfolio_id": analysis["portfolio_registry"]["portfolio_id"],
        "approved_alpha_count": analysis["portfolio_registry"]["approved_alpha_count"],
        "active_alpha_count": analysis["portfolio_registry"]["active_alpha_count"],
        "current_regime": analysis["current_regime"],
        "portfolio_decision": analysis["portfolio_registry"]["portfolio_decision"],
        "portfolio_confidence": analysis["portfolio_registry"]["portfolio_confidence"],
        "portfolio_uncertainty": analysis["portfolio_registry"]["portfolio_uncertainty"],
        "conflict_count": len(analysis["conflict_registry"]),
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "report_paths": report_paths,
    }
    write_json(repo_root / PROGRAM5_DIR / "program5_metrics.json", metrics)
    return metrics


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_program5_portfolio_intelligence(root)
    print(
        "Program 5 complete - "
        f"decision={result['portfolio_decision']}, "
        f"confidence={result['portfolio_confidence']}, "
        f"conflicts={result['conflict_count']}"
    )
