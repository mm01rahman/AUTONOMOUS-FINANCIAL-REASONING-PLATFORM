"""Governed runner for Discovery Cycle 3 Phase 5 Institutional Alpha Revision Program."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.institutional_alpha_revision import (
    DC3_PHASE5_DIR,
    emit_dc3_phase5_revision_reports,
    prepare_dc3_phase5_revision_artifacts,
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
    if "reproducibility_hash" not in result or result["reproducibility_hash"] == "dc3-phase5-revision-v1":
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


def _upsert_graph_payload(repo_root: Path, analysis: dict[str, Any], campaign_id: str) -> dict[str, int]:
    graph_repo = YAMLGraphRepository((repo_root / "data" / "ikros" / "graph").resolve())
    graph = graph_repo.load()
    payload = cast(dict[str, Any], analysis["ecology_knowledge_graph"])
    created_nodes = 0
    created_edges = 0

    revision_nodes = cast(list[dict[str, Any]], payload["revision_nodes"])
    conclusion_node = cast(dict[str, Any], payload["conclusion_node"])

    for item in revision_nodes:
        node = GraphNode(
            node_id=str(item["node_id"]),
            node_type=NodeType.KNOWLEDGE_OBJECT.value,
            ikros_id=str(item["node_id"]),
            label=str(item["label"]),
            confidence=float(item["confidence"]),
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes={},
        )
        if not graph.has_node(node.node_id):
            graph.add_node(node)
            created_nodes += 1

    conc = GraphNode(
        node_id=str(conclusion_node["node_id"]),
        node_type=NodeType.RESEARCH_CONCLUSION.value,
        ikros_id=str(conclusion_node["node_id"]),
        label=str(conclusion_node["label"]),
        confidence=float(conclusion_node["confidence"]),
        spec_refs=["SPEC-060"],
        wp_refs=["WP-IMP-0048"],
        attributes={},
    )
    if not graph.has_node(conc.node_id):
        graph.add_node(conc)
        created_nodes += 1

    relation_index = {(e.source_id, e.target_id, e.edge_type) for e in graph.edges()}

    def add_edge(src: str, tgt: str, etype: str, conf: float, ref: str) -> None:
        nonlocal created_edges
        key = (src, tgt, etype)
        if key in relation_index or not graph.has_node(src) or not graph.has_node(tgt):
            return
        graph.add_edge(GraphEdge(
            edge_id=graph.next_edge_id(),
            source_id=src, target_id=tgt, edge_type=etype,
            confidence=conf, evidence_ref=ref,
            spec_ref="SPEC-060", wp_ref="WP-IMP-0048", attributes={},
        ))
        relation_index.add(key)
        created_edges += 1

    for edge in cast(list[dict[str, Any]], payload["edges"]):
        rel = str(edge["relation"])
        etype = EdgeType.SUPPORTED_BY.value if rel == "SUPPORTED_BY" else EdgeType.RELATED_TO.value
        add_edge(str(edge["source"]), str(edge["target"]), etype, float(edge["confidence"]), str(DC3_PHASE5_DIR / "ARB_RECOMMENDATION_PHASE5.md"))

    add_edge(str(conclusion_node["node_id"]), campaign_id, EdgeType.DERIVED_FROM.value, 0.78, str(DC3_PHASE5_DIR / "ARB_RECOMMENDATION_PHASE5.md"))
    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _default_campaign_spec() -> dict[str, Any]:
    return {
        "title": "DC3 Phase 5 Institutional Alpha Revision Program",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260802-9601",
            "title": "DC3 Phase 5 Primary Research Question",
            "question": "What scientific revisions are required to advance safe_haven_migration and decision_cascade mechanisms from RESEARCH to READY_FOR_REVALIDATION?",
            "category": "MECHANISM_REVISION",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "confidence": {"prior": 0.60, "statistical": 0.0, "economic": 0.62, "data": 0.55, "model": 0.55, "validation": 0.0, "replication": 0.0, "operational": 0.0, "last_updated": "2026-08-02T00:00:00Z"},
            "lineage": {"origin": {"created_by": "dc3-phase5-revision", "created_at": "2026-08-02T00:00:00Z", "creation_context": "DC3 phase5 primary question", "motivation": "Identify scientific revisions required for RESEARCH mechanisms."}},
            "reproducibility_hash": "dc3-phase5-revision-v1",
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260802-9601",
            "title": "DC3 Phase 5 Revision Analysis",
            "experiment_type": "HYPOTHESIS_VALIDATION",
            "hypothesis_under_test": "IKROS-HYP-20260802-0601",
            "dataset_refs": ["dc3_phase4_batch1_validation.json"],
            "methodology": "scientific_failure_analysis_and_revision",
            "lifecycle_state": "DESIGNED",
            "confidence": {"prior": 0.60, "statistical": 0.0, "economic": 0.62, "data": 0.55, "model": 0.55, "validation": 0.0, "replication": 0.0, "operational": 0.0, "last_updated": "2026-08-02T00:00:00Z"},
            "lineage": {"origin": {"created_by": "dc3-phase5-revision", "created_at": "2026-08-02T00:00:00Z", "creation_context": "DC3 phase5 revision experiment", "motivation": "Produce scientific revision plans for Batch 1 RESEARCH mechanisms."}},
            "reproducibility_hash": "dc3-phase5-revision-v1",
        },
    }


def run_dc3_phase5_revision_campaign(repo_root: Path) -> dict[str, Any]:
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
        objective="Revise safe_haven_migration and decision_cascade mechanisms using Phase 4 validation evidence; produce assumption audits, feature/proxy/causal revision plans, experiment backlogs, confidence updates, and ARB decisions.",
        campaign_type="RESEARCH_AUDIT",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_campaign_pipeline(campaign, [TaskKind.RESEARCH_QUESTION.value, TaskKind.EXPERIMENT_REGISTRATION.value, TaskKind.FINAL_REPORT.value])

    analysis = prepare_dc3_phase5_revision_artifacts(repo_root=repo_root)

    rq_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    exp_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    if not rq_registry.exists(rq.ikros_id):
        rq_registry.register(rq)
    if not exp_registry.exists(exp.ikros_id):
        exp_registry.register(exp)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_dc3_phase5_revision_reports(analysis, campaign_result=report.to_dict(), repo_root=repo_root)
    graph_metrics = _upsert_graph_payload(repo_root, analysis, campaign.campaign_id)

    arb = cast(dict[str, Any], analysis["arb_summary"])
    conf_updates = cast(dict[str, Any], analysis["confidence_updates"])

    metrics: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "mechanisms_revised": int(analysis["mechanisms_revised"]),
        "mechanisms_ready_for_revalidation": arb["mechanisms_ready_for_revalidation"],
        "mechanisms_research": arb["mechanisms_research"],
        "mechanisms_reject": arb["mechanisms_reject"],
        "total_experiment_backlog": int(arb["total_experiment_backlog"]),
        "total_dataset_gaps": int(arb["total_dataset_gaps"]),
        "confidence_updates": conf_updates,
        "promote_now": False,
        "execute_batch_2_now": False,
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "report_paths": report_paths,
    }
    write_json((repo_root / DC3_PHASE5_DIR / "dc3_phase5_metrics.json"), metrics)
    return metrics


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_dc3_phase5_revision_campaign(root)
    print(f"DC3 Phase 5 complete - revised: {result['mechanisms_revised']}, ready: {result['mechanisms_ready_for_revalidation']}, research: {result['mechanisms_research']}")
