"""Program 4 — governed runner for the institutional alpha expansion program."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.institutional_alpha_expansion_program import (
    PROGRAM4_DIR,
    emit_program4_reports,
    prepare_program4_artifacts,
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
                wp_refs=["WP-IMP-0054"],
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
                evidence_ref=str(PROGRAM4_DIR / "FINAL_REPORT.md"),
                spec_ref="SPEC-060",
                wp_ref="WP-IMP-0054",
                attributes={},
            )
        )
        relation_index.add(key)
        created_edges += 1

    add_node("PROGRAM4-ALPHA-LIBRARY", "Program 4 Institutional Alpha Library", 0.86)
    approved_registry = cast(dict[str, Any], analysis["approved_alpha_registry"])
    for mechanism, entry in approved_registry.items():
        alpha_id = str(entry["alpha_id"])
        add_node(alpha_id, f"{mechanism} approved alpha", float(entry["confidence"]))
        add_edge("PROGRAM4-ALPHA-LIBRARY", alpha_id, EdgeType.RELATED_TO.value, 0.80)
    add_edge("PROGRAM4-ALPHA-LIBRARY", campaign_id, EdgeType.DERIVED_FROM.value, 0.76)

    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _campaign_spec() -> dict[str, Any]:
    return {
        "title": "Program 4 — Institutional Alpha Expansion Program",
        "rq": {
            "ikros_id": "IKROS-RQ-20260803-0055",
            "title": "Program 4 Primary Research Question",
            "question": (
                "Can AFRP autonomously expand the approved institutional alpha library "
                "to at least five independent mechanisms using current observations?"
            ),
            "category": "MECHANISM_VALIDATION",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "confidence": {
                "prior": 0.68,
                "statistical": 0.0,
                "economic": 0.65,
                "data": 0.63,
                "model": 0.66,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "program4-alpha-expansion",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Generation 2 Program 4 bootstrap",
                    "motivation": (
                        "Expand the approved alpha inventory into a diversified "
                        "institutional alpha library."
                    ),
                }
            },
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260803-0055",
            "title": "Program 4 Alpha Expansion Integration",
            "experiment_type": "MECHANISM_VALIDATION",
            "hypothesis_under_test": "IKROS-HYP-20260803-0055",
            "dataset_refs": [
                "program3_metrics.json",
                "approved_alpha_registry.json",
                "research_director.json",
            ],
            "methodology": "institutional_alpha_expansion_program_v1",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.67,
                "statistical": 0.0,
                "economic": 0.64,
                "data": 0.62,
                "model": 0.65,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "program4-alpha-expansion",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Generation 2 Program 4 autonomous expansion",
                    "motivation": (
                        "Continuously discover and promote additional independent "
                        "institutional alpha mechanisms."
                    ),
                }
            },
        },
    }


def run_program4_expansion(repo_root: Path) -> dict[str, Any]:
    """Execute Program 4 and persist all governed expansion artifacts."""
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
            "Use the existing alpha factory and research laboratory concepts to "
            "autonomously expand the approved institutional alpha library until at "
            "least five independent approved alphas exist or observations are exhausted."
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

    analysis = prepare_program4_artifacts()
    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_program4_reports(analysis, report.to_dict(), repo_root=repo_root)
    graph_metrics = _upsert_graph(repo_root, analysis, campaign.campaign_id)

    metrics = {
        "campaign_id": campaign.campaign_id,
        "program": analysis["program"],
        "approved_alpha_count": analysis["approved_alpha_count"],
        "target_approved_alpha_count": analysis["target_approved_alpha_count"],
        "approved_mechanisms": sorted(list(analysis["approved_alpha_registry"].keys())),
        "blocked_mechanisms": [item["mechanism"] for item in analysis["blocked_alpha_registry"]],
        "rejected_mechanisms": [item["mechanism"] for item in analysis["rejected_alpha_registry"]],
        "campaigns_executed": len(analysis["research_campaign_archive"]),
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "report_paths": report_paths,
        "stop_reason": analysis["stop_reason"],
        "arb_recommendation": analysis["arb_recommendation"],
    }
    write_json(repo_root / PROGRAM4_DIR / "program4_metrics.json", metrics)
    return metrics


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_program4_expansion(root)
    print(
        "Program 4 complete - "
        f"approved={result['approved_alpha_count']}, "
        f"campaigns={result['campaigns_executed']}, "
        f"stop_reason={result['stop_reason']}"
    )
