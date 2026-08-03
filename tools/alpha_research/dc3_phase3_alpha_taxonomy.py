"""Governed runner for Discovery Cycle 3 Phase 3 Institutional Alpha Taxonomy & Consolidation Program."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.institutional_alpha_taxonomy import (
    DC3_PHASE3_DIR,
    emit_dc3_phase3_taxonomy_reports,
    prepare_dc3_phase3_taxonomy_artifacts,
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
        or result["reproducibility_hash"] == "dc3-phase3-taxonomy-v1"
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

    family_nodes = cast(list[dict[str, Any]], payload["family_nodes"])
    conclusion_node = cast(dict[str, Any], payload["conclusion_node"])

    for item in family_nodes:
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

    conc_node = GraphNode(
        node_id=str(conclusion_node["node_id"]),
        node_type=NodeType.RESEARCH_CONCLUSION.value,
        ikros_id=str(conclusion_node["node_id"]),
        label=str(conclusion_node["label"]),
        confidence=float(conclusion_node["confidence"]),
        spec_refs=["SPEC-060"],
        wp_refs=["WP-IMP-0048"],
        attributes={},
    )
    if not graph.has_node(conc_node.node_id):
        graph.add_node(conc_node)
        created_nodes += 1

    relation_index = {(edge.source_id, edge.target_id, edge.edge_type) for edge in graph.edges()}

    def add_edge(source_id: str, target_id: str, edge_type: str, confidence: float, evidence_ref: str) -> None:
        nonlocal created_edges
        key = (source_id, target_id, edge_type)
        if key in relation_index:
            return
        if not graph.has_node(source_id) or not graph.has_node(target_id):
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
        if relation == "RELATED_TO":
            edge_type = EdgeType.RELATED_TO.value
        elif relation == "SUPPORTED_BY":
            edge_type = EdgeType.SUPPORTED_BY.value
        else:
            edge_type = EdgeType.EXPLAINS.value
        add_edge(str(edge["source"]), str(edge["target"]), edge_type, float(edge["confidence"]), str(DC3_PHASE3_DIR / "INSTITUTIONAL_ALPHA_TAXONOMY.md"))

    add_edge(str(conclusion_node["node_id"]), campaign_id, EdgeType.DERIVED_FROM.value, 0.8, str(DC3_PHASE3_DIR / "ARB_RECOMMENDATION.md"))

    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _default_campaign_spec() -> dict[str, Any]:
    return {
        "title": "DC3 Phase 3 Institutional Alpha Taxonomy & Consolidation Program",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260802-9401",
            "title": "DC3 Phase 3 Primary Research Question",
            "question": "How many genuinely distinct economic alpha mechanisms exist among the 12 discovered candidates?",
            "category": "MECHANISM_TAXONOMY",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "evidence_refs": ["dc3_phase1_alpha_registry.json"],
            "confidence": {"prior": 0.65, "statistical": 0.0, "economic": 0.65, "data": 0.60, "model": 0.60, "validation": 0.0, "replication": 0.0, "operational": 0.0, "last_updated": "2026-08-02T00:00:00Z"},
            "lineage": {"origin": {"created_by": "dc3-phase3-alpha-taxonomy", "created_at": "2026-08-02T00:00:00Z", "creation_context": "DC3 phase3 primary question", "motivation": "Classify 12 alpha mechanisms into governed institutional families."}},
            "reproducibility_hash": "dc3-phase3-taxonomy-v1",
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260802-9401",
            "title": "DC3 Phase 3 Institutional Alpha Taxonomy",
            "experiment_type": "MECHANISM_TAXONOMY",
            "hypothesis_under_test": "IKROS-HYP-20260802-0401",
            "dataset_refs": ["dc3_institutional_alpha_registry.json"],
            "methodology": "mechanism_decomposition_similarity_clustering",
            "lifecycle_state": "DESIGNED",
            "confidence": {"prior": 0.65, "statistical": 0.0, "economic": 0.65, "data": 0.60, "model": 0.60, "validation": 0.0, "replication": 0.0, "operational": 0.0, "last_updated": "2026-08-02T00:00:00Z"},
            "lineage": {"origin": {"created_by": "dc3-phase3-alpha-taxonomy", "created_at": "2026-08-02T00:00:00Z", "creation_context": "DC3 phase3 taxonomy experiment", "motivation": "Produce governed institutional alpha taxonomy including families, similarity matrix, redundancy analysis, prioritization, and batch plan."}},
            "reproducibility_hash": "dc3-phase3-taxonomy-v1",
        },
        "research_questions_secondary": [
            {
                "ikros_id": "IKROS-RQ-20260802-9402",
                "title": "DC3 Phase 3 Redundancy Analysis Question",
                "question": "Which alpha mechanisms share sufficient economic similarity to be consolidated into shared families?",
                "category": "REDUNDANCY_ANALYSIS",
                "priority": "HIGH",
                "lifecycle_state": "OPEN",
                "instrument": "XAU/USD",
                "confidence": {"prior": 0.62, "statistical": 0.0, "economic": 0.62, "data": 0.58, "model": 0.58, "validation": 0.0, "replication": 0.0, "operational": 0.0, "last_updated": "2026-08-02T00:00:00Z"},
                "lineage": {"origin": {"created_by": "dc3-phase3-alpha-taxonomy", "created_at": "2026-08-02T00:00:00Z", "creation_context": "DC3 phase3 secondary question", "motivation": ""}},
                "reproducibility_hash": "dc3-phase3-taxonomy-v1",
            },
            {
                "ikros_id": "IKROS-RQ-20260802-9403",
                "title": "DC3 Phase 3 Prioritization Question",
                "question": "Which institutional alpha families should be prioritised for Phase 4 validation?",
                "category": "RESEARCH_PRIORITIZATION",
                "priority": "MEDIUM",
                "lifecycle_state": "OPEN",
                "instrument": "XAU/USD",
                "confidence": {"prior": 0.60, "statistical": 0.0, "economic": 0.60, "data": 0.55, "model": 0.55, "validation": 0.0, "replication": 0.0, "operational": 0.0, "last_updated": "2026-08-02T00:00:00Z"},
                "lineage": {"origin": {"created_by": "dc3-phase3-alpha-taxonomy", "created_at": "2026-08-02T00:00:00Z", "creation_context": "DC3 phase3 secondary question", "motivation": ""}},
                "reproducibility_hash": "dc3-phase3-taxonomy-v1",
            },
        ],
    }


def run_dc3_phase3_alpha_taxonomy_campaign(repo_root: Path) -> dict[str, Any]:
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
        objective="Classify 12 discovered alpha mechanisms into governed institutional alpha families; produce taxonomy, similarity matrices, redundancy analysis, prioritization, and validation batch plan.",
        campaign_type="RESEARCH_AUDIT",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_campaign_pipeline(campaign, [TaskKind.RESEARCH_QUESTION.value, TaskKind.EXPERIMENT_REGISTRATION.value, TaskKind.FINAL_REPORT.value])

    analysis = prepare_dc3_phase3_taxonomy_artifacts(repo_root=repo_root)

    rq_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    exp_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    if not rq_registry.exists(rq.ikros_id):
        rq_registry.register(rq)
    if not exp_registry.exists(exp.ikros_id):
        exp_registry.register(exp)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_dc3_phase3_taxonomy_reports(analysis, campaign_result=report.to_dict(), repo_root=repo_root)
    graph_metrics = _upsert_graph_payload(repo_root, analysis, campaign.campaign_id)

    for rq_secondary in spec["research_questions_secondary"]:
        rq_id = str(rq_secondary["ikros_id"])
        if not rq_registry.exists(rq_id):
            try:
                rq2 = ResearchQuestion.from_dict(_with_reproducibility_hash(rq_secondary))
                rq_registry.register(rq2)
            except Exception:
                pass

    metrics: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "mechanism_count": int(analysis["mechanism_count"]),
        "family_count": int(analysis["family_count"]),
        "similarity_pairs": len(cast(list[Any], analysis["similarity_matrix"])),
        "redundant_pairs": int(analysis["redundancy_analysis"]["redundant_pairs_count"]),
        "merge_candidates": int(analysis["redundancy_analysis"]["merge_candidate_count"]),
        "independent_count": int(analysis["redundancy_analysis"]["independent_count"]),
        "validation_batches": len(cast(list[Any], analysis["validation_batch_plan"])),
        "top_priority_family": str(cast(list[dict[str, Any]], analysis["research_priority_matrix"])[0]["family_name"]),
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "report_paths": report_paths,
    }
    write_json((repo_root / DC3_PHASE3_DIR / "dc3_phase3_metrics.json"), metrics)
    return metrics


if __name__ == "__main__":
    import sys
    repo_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_dc3_phase3_alpha_taxonomy_campaign(repo_root)
    print(f"DC3 Phase 3 complete — families: {result['family_count']}, mechanisms: {result['mechanism_count']}, batches: {result['validation_batches']}")
