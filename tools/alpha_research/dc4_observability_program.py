"""Governed runner for Discovery Cycle 4 Institutional Market Observability & Data Expansion Program."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.institutional_observability import (
    DC4_DIR,
    emit_dc4_observability_reports,
    prepare_dc4_observability_artifacts,
)
from tools.alpha_research.reporting import write_json
from tools.ikros.graph import EdgeType, GraphNode, NodeType, YAMLGraphRepository
from tools.ikros.graph.models import GraphEdge
from tools.ikros.identifiers import compute_reproducibility_hash
from tools.ikros.models import Experiment, ResearchQuestion
from tools.ikros.orchestrator import FailurePolicy, ResearchCampaign, ResearchOrchestrator, TaskKind
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.research import ResearchRegistry


def _with_hash(entity: dict[str, Any]) -> dict[str, Any]:
    result = dict(entity)
    if "reproducibility_hash" not in result or result["reproducibility_hash"] == "dc4-observability-v1":
        result["reproducibility_hash"] = compute_reproducibility_hash(result)
    return result


def _select_pipeline(campaign: ResearchCampaign, task_kinds: list[str]) -> ResearchCampaign:
    kind_set = set(task_kinds)
    filtered = [t for t in campaign.tasks if t.kind in kind_set]
    ordered = sorted(filtered, key=lambda t: task_kinds.index(t.kind) if t.kind in task_kinds else 999)
    for idx, task in enumerate(ordered):
        task.depends_on = [ordered[idx - 1].task_id] if idx > 0 else []
    campaign.tasks = ordered
    campaign.pipeline.task_ids = [t.task_id for t in ordered]
    campaign.pipeline.stages = [t.kind for t in ordered]
    return campaign


def _upsert_graph(repo_root: Path, analysis: dict[str, Any], campaign_id: str) -> dict[str, int]:
    graph_repo = YAMLGraphRepository((repo_root / "data" / "ikros" / "graph").resolve())
    graph = graph_repo.load()
    payload = cast(dict[str, Any], analysis["ecology_knowledge_graph"])
    created_nodes = created_edges = 0

    for item in cast(list[dict[str, Any]], payload["obs_nodes"]):
        node = GraphNode(
            node_id=str(item["node_id"]), node_type=NodeType.KNOWLEDGE_OBJECT.value,
            ikros_id=str(item["node_id"]), label=str(item["label"]),
            confidence=float(item["confidence"]), spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"], attributes={},
        )
        if not graph.has_node(node.node_id):
            graph.add_node(node)
            created_nodes += 1

    conc = cast(dict[str, Any], payload["conclusion_node"])
    cn = GraphNode(
        node_id=str(conc["node_id"]), node_type=NodeType.RESEARCH_CONCLUSION.value,
        ikros_id=str(conc["node_id"]), label=str(conc["label"]),
        confidence=float(conc["confidence"]), spec_refs=["SPEC-060"],
        wp_refs=["WP-IMP-0048"], attributes={},
    )
    if not graph.has_node(cn.node_id):
        graph.add_node(cn)
        created_nodes += 1

    rel_idx = {(e.source_id, e.target_id, e.edge_type) for e in graph.edges()}

    def add_edge(src: str, tgt: str, etype: str, conf: float) -> None:
        nonlocal created_edges
        key = (src, tgt, etype)
        if key in rel_idx or not graph.has_node(src) or not graph.has_node(tgt):
            return
        graph.add_edge(GraphEdge(
            edge_id=graph.next_edge_id(), source_id=src, target_id=tgt,
            edge_type=etype, confidence=conf,
            evidence_ref=str(DC4_DIR / "OBSERVABILITY_DASHBOARD.md"),
            spec_ref="SPEC-060", wp_ref="WP-IMP-0048", attributes={},
        ))
        rel_idx.add(key)
        created_edges += 1

    for edge in cast(list[dict[str, Any]], payload["edges"]):
        etype = EdgeType.SUPPORTED_BY.value if edge["relation"] == "SUPPORTED_BY" else EdgeType.RELATED_TO.value
        add_edge(str(edge["source"]), str(edge["target"]), etype, float(edge["confidence"]))

    add_edge(str(conc["node_id"]), campaign_id, EdgeType.DERIVED_FROM.value, 0.78)
    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _campaign_spec() -> dict[str, Any]:
    return {
        "title": "DC4 Institutional Market Observability & Data Expansion Program",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260802-9701",
            "title": "DC4 Observability Audit Primary Question",
            "question": "What market state variables are required for institutional alpha validation, and which are currently unobservable?",
            "category": "OBSERVABILITY_AUDIT",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "confidence": {"prior": 0.70, "statistical": 0.0, "economic": 0.70, "data": 0.65, "model": 0.65, "validation": 0.0, "replication": 0.0, "operational": 0.0, "last_updated": "2026-08-02T00:00:00Z"},
            "lineage": {"origin": {"created_by": "dc4-observability-program", "created_at": "2026-08-02T00:00:00Z", "creation_context": "DC4 primary question", "motivation": "Map AFRP observability against institutional alpha validation requirements."}},
            "reproducibility_hash": "dc4-observability-v1",
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260802-9701",
            "title": "DC4 Observability Analysis Experiment",
            "experiment_type": "DATASET_VALIDATION",
            "hypothesis_under_test": "IKROS-HYP-20260802-0701",
            "dataset_refs": ["dc3_institutional_alpha_registry.json"],
            "methodology": "observability_matrix_and_gap_analysis",
            "lifecycle_state": "DESIGNED",
            "confidence": {"prior": 0.70, "statistical": 0.0, "economic": 0.70, "data": 0.65, "model": 0.65, "validation": 0.0, "replication": 0.0, "operational": 0.0, "last_updated": "2026-08-02T00:00:00Z"},
            "lineage": {"origin": {"created_by": "dc4-observability-program", "created_at": "2026-08-02T00:00:00Z", "creation_context": "DC4 observability experiment", "motivation": "Produce market state model, observability matrix, data gap catalogue, source registry, data foundation V2 spec, feature expansion roadmap."}},
            "reproducibility_hash": "dc4-observability-v1",
        },
    }


def run_dc4_observability_campaign(repo_root: Path) -> dict[str, Any]:
    orchestrator = ResearchOrchestrator(base_dir=(repo_root / "data" / "ikros").resolve())
    spec = _campaign_spec()
    rq = ResearchQuestion.from_dict(_with_hash(spec["research_question_primary"]))
    exp = Experiment.from_dict(_with_hash(spec["experiment"]))
    task_payloads: dict[str, Any] = {
        TaskKind.RESEARCH_QUESTION.value: {"entity_type": "ResearchQuestion", "entity": rq.to_dict()},
        TaskKind.EXPERIMENT_REGISTRATION.value: {"entity_type": "Experiment", "entity": exp.to_dict()},
    }
    campaign = orchestrator.build_campaign(
        title=str(spec["title"]),
        objective="Produce observability matrix, dataset gap catalogue, institutional data source registry, market state model, observability scores, data foundation V2 spec, and feature expansion roadmap for all 12 alpha mechanisms.",
        campaign_type="RESEARCH_AUDIT",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_pipeline(campaign, [TaskKind.RESEARCH_QUESTION.value, TaskKind.EXPERIMENT_REGISTRATION.value, TaskKind.FINAL_REPORT.value])

    analysis = prepare_dc4_observability_artifacts(repo_root=repo_root)

    rq_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    exp_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    if not rq_registry.exists(rq.ikros_id):
        rq_registry.register(rq)
    if not exp_registry.exists(exp.ikros_id):
        exp_registry.register(exp)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_dc4_observability_reports(analysis, campaign_result=report.to_dict(), repo_root=repo_root)
    graph_metrics = _upsert_graph(repo_root, analysis, campaign.campaign_id)

    arb = cast(dict[str, Any], analysis["arb_recommendation"])
    metrics: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "mechanism_count": int(analysis["mechanism_count"]),
        "state_variables_identified": int(analysis["state_variables_identified"]),
        "missing_datasets": int(analysis["missing_datasets"]),
        "avg_observation_completeness": float(analysis["avg_observation_completeness"]),
        "mechanisms_blocked": int(analysis["mechanisms_blocked_by_observability"]),
        "p1_datasets": int(analysis["p1_dataset_count"]),
        "new_feature_families": int(analysis["new_feature_families"]),
        "new_features_total": int(analysis["new_features_total"]),
        "promote_now": False,
        "validate_additional_now": False,
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "report_paths": report_paths,
        "immediate_free_acquisitions": arb["immediate_free_acquisitions"],
    }
    write_json((repo_root / DC4_DIR / "dc4_metrics.json"), metrics)
    return metrics


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_dc4_observability_campaign(root)
    print(f"DC4 complete - variables: {result['state_variables_identified']}, datasets: {result['missing_datasets']}, blocked: {result['mechanisms_blocked']}, obs_completeness: {result['avg_observation_completeness']:.1%}")
