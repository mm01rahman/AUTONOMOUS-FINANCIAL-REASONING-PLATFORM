"""Generation 4 / Program 7 — governed runner for institutional market intelligence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.real_time_institutional_market_intelligence import (
    PROGRAM7_DIR,
    emit_program7_reports,
    prepare_program7_artifacts,
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
                spec_refs=["SPEC-060"],
                wp_refs=["WP-IMP-0057"],
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
                evidence_ref=str(PROGRAM7_DIR / "FINAL_REPORT.md"),
                spec_ref="SPEC-060",
                wp_ref="WP-IMP-0057",
                attributes={},
            )
        )
        relation_index.add(key)
        created_edges += 1

    add_node("PROGRAM7-INTELLIGENCE", "Generation 4 Institutional Intelligence", 0.91)
    add_node("PROGRAM6-SIM-LAB", "Program 6 Simulation Laboratory", 0.89)
    add_edge("PROGRAM7-INTELLIGENCE", "PROGRAM6-SIM-LAB", EdgeType.DERIVED_FROM.value, 0.84)
    for row in cast(list[dict[str, Any]], analysis["research_trigger_registry"]):
        trigger_stamp = (
            str(row["timestamp"])
            .replace(":", "")
            .replace("-", "")
            .replace("+", "")
            .replace("T", "-")
        )
        trigger_id = f"IKROS-TRIGGER-{trigger_stamp}-{str(row['trigger_type'])[:8]}"
        add_node(trigger_id, f"{row['trigger_type']} trigger", 0.76)
        add_edge("PROGRAM7-INTELLIGENCE", trigger_id, EdgeType.RELATED_TO.value, 0.74)
    add_edge("PROGRAM7-INTELLIGENCE", campaign_id, EdgeType.DERIVED_FROM.value, 0.82)
    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _campaign_spec() -> dict[str, Any]:
    return {
        "title": "Generation 4 — Real-Time Institutional Market Intelligence Platform",
        "rq": {
            "ikros_id": "IKROS-RQ-20260803-0058",
            "title": "Generation 4 Primary Research Question",
            "question": (
                "Can AFRP continuously observe markets, revise institutional beliefs, "
                "update portfolio recommendations, and autonomously initiate governed "
                "research without executing trades?"
            ),
            "category": "MECHANISM_VALIDATION",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "confidence": {
                "prior": 0.76,
                "statistical": 0.0,
                "economic": 0.74,
                "data": 0.73,
                "model": 0.77,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "program7-market-intelligence",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Generation 4 institutional intelligence bootstrap",
                    "motivation": (
                        "Close the real-time market observation-to-research loop "
                        "without enabling execution."
                    ),
                }
            },
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260803-0058",
            "title": "Generation 4 Market Intelligence Integration",
            "experiment_type": "MECHANISM_VALIDATION",
            "hypothesis_under_test": "IKROS-HYP-20260803-0058",
            "dataset_refs": [
                "market_state_registry.json",
                "belief_registry.json",
                "portfolio_evolution_registry.json",
            ],
            "methodology": "real_time_institutional_market_intelligence_v1",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.75,
                "statistical": 0.0,
                "economic": 0.73,
                "data": 0.72,
                "model": 0.76,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "program7-market-intelligence",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Generation 4 continuous intelligence campaign",
                    "motivation": (
                        "Operate AFRP as a continuously reasoning institutional "
                        "market intelligence organization."
                    ),
                }
            },
        },
    }


def run_program7_market_intelligence(repo_root: Path) -> dict[str, Any]:
    """Execute Generation 4 and persist governed intelligence artifacts."""
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
            "Continuously observe market state, update beliefs, maintain regime and "
            "alpha activation probabilities, revise portfolio recommendations, and "
            "open governed research triggers in a non-executing loop."
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

    analysis = prepare_program7_artifacts()
    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_program7_reports(analysis, report.to_dict(), repo_root=repo_root)
    graph_metrics = _upsert_graph(repo_root, analysis, campaign.campaign_id)

    metrics = {
        "campaign_id": campaign.campaign_id,
        "program": analysis["program"],
        "intelligence_cycles": analysis["institutional_intelligence_registry"][
            "intelligence_cycle_count"
        ],
        "latest_decision": analysis["institutional_intelligence_registry"][
            "latest_portfolio_decision"
        ],
        "latest_regime": analysis["institutional_intelligence_registry"]["latest_regime"],
        "latest_confidence": analysis["institutional_intelligence_registry"][
            "latest_confidence"
        ],
        "governed_research_triggers": analysis["institutional_intelligence_registry"][
            "governed_research_triggers"
        ],
        "scientific_health_score": analysis["institutional_intelligence_registry"][
            "scientific_health_score"
        ],
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "report_paths": report_paths,
    }
    write_json(repo_root / PROGRAM7_DIR / "program7_metrics.json", metrics)
    return metrics


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_program7_market_intelligence(root)
    print(
        "Program 7 complete - "
        f"cycles={result['intelligence_cycles']}, "
        f"decision={result['latest_decision']}, "
        f"triggers={result['governed_research_triggers']}"
    )
