"""IKROS query planner — deterministic execution planning."""

from __future__ import annotations

from tools.ikros.query.models import ParsedQuery, QueryPlan, QueryPlanStep, QuerySource


class QueryPlanner:
    """Build a deterministic execution plan for a parsed query."""

    def build(self, query: ParsedQuery) -> QueryPlan:
        steps: list[QueryPlanStep] = []
        if query.source == QuerySource.ENTITY:
            steps.extend(
                [
                    QueryPlanStep(
                        "resolve_registry_entity",
                        "registry",
                        "Search registries for exact identifier",
                    ),
                    QueryPlanStep(
                        "resolve_memory_record",
                        "memory",
                        "Search memory store for exact identifier",
                    ),
                    QueryPlanStep(
                        "resolve_graph_node",
                        "graph",
                        "Search graph nodes for exact identifier",
                    ),
                    QueryPlanStep(
                        "rank_results",
                        "engine",
                        "Sort exact matches deterministically",
                    ),
                ]
            )
        elif query.source == QuerySource.REGISTRY:
            steps.extend(
                [
                    QueryPlanStep(
                        "scan_registry_entities",
                        "registry",
                        f"Filter registry entity type {query.target}",
                    ),
                    QueryPlanStep(
                        "rank_results",
                        "engine",
                        "Sort registry results by confidence then identifier",
                    ),
                ]
            )
        elif query.source == QuerySource.MEMORY:
            steps.extend(
                [
                    QueryPlanStep(
                        "scan_memory_tier",
                        "memory",
                        f"Filter memory tier {query.target}",
                    ),
                    QueryPlanStep(
                        "rank_results",
                        "engine",
                        "Sort memory results by confidence then identifier",
                    ),
                ]
            )
        elif query.source == QuerySource.GRAPH:
            steps.extend(
                [
                    QueryPlanStep(
                        "graph_traversal",
                        "graph",
                        f"Execute graph operation {query.graph_operation}",
                    ),
                    QueryPlanStep(
                        "rank_results",
                        "engine",
                        "Sort graph results by confidence then identifier",
                    ),
                ]
            )
        else:
            steps.append(
                QueryPlanStep("unsupported", "engine", f"Unsupported source {query.source}")
            )
        return QueryPlan(query=query, steps=steps)
