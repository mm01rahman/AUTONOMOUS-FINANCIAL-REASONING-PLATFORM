"""Program 3 — governed runner for the autonomous institutional alpha campaign engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.autonomous_institutional_alpha_campaign_engine import (
    PROGRAM3_DIR,
    emit_program3_reports,
    prepare_program3_artifacts,
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
    allowed = set(task_kinds)
    selected = [task for task in campaign.tasks if task.kind in allowed]
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
                wp_refs=["WP-IMP-0053"],
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
                evidence_ref=str(PROGRAM3_DIR / "FINAL_REPORT.md"),
                spec_ref="SPEC-060",
                wp_ref="WP-IMP-0053",
                attributes={},
            )
        )
        relation_index.add(key)
        created_edges += 1

    add_node("PROGRAM3-RESEARCH-LOOP", "Program 3 Autonomous Research Loop", 0.83)

    for mechanism, state in cast(dict[str, Any], analysis["final_mechanism_states"]).items():
        alpha_id = str(state["alpha_id"])
        add_node(alpha_id, f"{mechanism} terminal state", float(state["confidence"]))
        add_edge("PROGRAM3-RESEARCH-LOOP", alpha_id, EdgeType.RELATED_TO.value, 0.79)

    add_edge("PROGRAM3-RESEARCH-LOOP", campaign_id, EdgeType.DERIVED_FROM.value, 0.74)

    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _campaign_spec() -> dict[str, Any]:
    return {
        "title": "Program 3 — Autonomous Institutional Alpha Campaign Engine",
        "rq": {
            "ikros_id": "IKROS-RQ-20260803-0054",
            "title": "Program 3 Primary Research Question",
            "question": (
                "Can AFRP autonomously operate governed research campaigns until every "
                "current institutional alpha mechanism reaches a terminal scientific state?"
            ),
            "category": "MECHANISM_VALIDATION",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "confidence": {
                "prior": 0.66,
                "statistical": 0.0,
                "economic": 0.63,
                "data": 0.61,
                "model": 0.64,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "program3-autonomous-campaign-engine",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Generation 2 Program 3 bootstrap",
                    "motivation": (
                        "Resolve the current institutional alpha inventory through "
                        "continuous governed research campaigns."
                    ),
                }
            },
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260803-0054",
            "title": "Program 3 Autonomous Campaign Engine Integration",
            "experiment_type": "MECHANISM_VALIDATION",
            "hypothesis_under_test": "IKROS-HYP-20260803-0054",
            "dataset_refs": [
                "wp_imp_0050_evidence_validation_engine.json",
                "program1_institutional_alpha_factory.json",
                "program2_research_laboratory.json",
            ],
            "methodology": "autonomous_institutional_alpha_campaign_engine_v1",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.65,
                "statistical": 0.0,
                "economic": 0.62,
                "data": 0.60,
                "model": 0.63,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "program3-autonomous-campaign-engine",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Generation 2 Program 3 autonomous execution",
                    "motivation": (
                        "Run the research laboratory continuously until all current "
                        "mechanisms are scientifically resolved."
                    ),
                }
            },
        },
    }


def run_program3_campaign_engine(repo_root: Path) -> dict[str, Any]:
    """Execute Program 3 and persist all governed campaign-engine artifacts."""
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
            "Operate governed research campaigns continuously until every current "
            "institutional alpha mechanism reaches APPROVED_ALPHA, REJECTED, or "
            "BLOCKED_BY_DATA."
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

    analysis = prepare_program3_artifacts()

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_program3_reports(
        analysis=analysis, campaign_result=report.to_dict(), repo_root=repo_root
    )
    graph_metrics = _upsert_graph(repo_root, analysis, campaign.campaign_id)

    metrics = {
        "campaign_id": campaign.campaign_id,
        "program": analysis["program"],
        "campaigns_executed": analysis["campaigns_executed"],
        "experiments_executed": analysis["experiments_executed"],
        "promoted_count": len(analysis["mechanisms_promoted"]),
        "rejected_count": len(analysis["mechanisms_rejected"]),
        "blocked_by_data_count": len(analysis["mechanisms_blocked_by_data"]),
        "terminal_states": {
            name: state["terminal_state"]
            for name, state in analysis["final_mechanism_states"].items()
        },
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "report_paths": report_paths,
        "arb_recommendation": analysis["arb_recommendation"],
    }
    write_json(repo_root / PROGRAM3_DIR / "program3_metrics.json", metrics)
    return metrics


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_program3_campaign_engine(root)
    print(
        "Program 3 complete - "
        f"campaigns={result['campaigns_executed']}, "
        f"promoted={result['promoted_count']}, "
        f"blocked={result['blocked_by_data_count']}"
    )
