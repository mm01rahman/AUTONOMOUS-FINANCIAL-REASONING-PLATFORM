"""IKROS query adapters for registries, graph, and memory."""

from __future__ import annotations

import json
from typing import Any

from tools.ikros.graph import EdgeType, GraphNode, KnowledgeGraph
from tools.ikros.memory import MemoryQuery, MemoryRecord, ResearchMemoryManager
from tools.ikros.models import IKROSEntity
from tools.ikros.query.models import GraphOperation, ParsedQuery
from tools.ikros.registries.alpha import AlphaRegistry
from tools.ikros.registries.base import BaseRegistry
from tools.ikros.registries.feature import FeatureRegistry


class RegistryQueryAdapter:
    """Read-only adapter over loaded IKROS registries."""

    def __init__(self, registries: dict[str, BaseRegistry[IKROSEntity]] | None = None) -> None:
        self._registries = registries or {}

    def get(self, identifier: str) -> IKROSEntity | None:
        for registry in self._registries.values():
            if registry.exists(identifier):
                return registry.get(identifier)
            if isinstance(registry, FeatureRegistry):
                try:
                    return registry.get_family(identifier)
                except KeyError:
                    pass
            if isinstance(registry, AlphaRegistry):
                try:
                    return registry.get_alpha(identifier)
                except KeyError:
                    pass
        return None

    def exists(self, identifier: str) -> bool:
        return self.get(identifier) is not None

    def query(self, entity_type: str, filters: dict[str, str]) -> list[IKROSEntity]:
        results = [
            entity
            for entity in self.all_entities()
            if entity.entity_type == entity_type and self._matches(entity, filters)
        ]
        return sorted(results, key=lambda entity: entity.ikros_id)

    def all_entities(self) -> list[IKROSEntity]:
        entities: list[IKROSEntity] = []
        for registry in self._registries.values():
            entities.extend(registry.list_all())
            if isinstance(registry, FeatureRegistry):
                entities.extend(registry.list_families())
            if isinstance(registry, AlphaRegistry):
                entities.extend(registry.list_alphas())
        return sorted(entities, key=lambda entity: entity.ikros_id)

    def _matches(self, entity: IKROSEntity, filters: dict[str, str]) -> bool:
        if not filters:
            return True
        for key, value in filters.items():
            if key == "specification" and value not in entity.spec_refs:
                return False
            if key == "capability" and value not in entity.capability_refs:
                return False
            if key == "work_package" and value not in entity.work_package_refs:
                return False
            if key == "evidence" and value not in entity.lineage.evidence.ers_records:
                return False
            if key == "lifecycle_state" and entity.lifecycle_state != value:
                return False
            if key == "confidence_threshold" and entity.confidence.overall() < float(value):
                return False
            if key == "temporal_start":
                if entity.lineage.origin.created_at < value:
                    return False
            if key == "temporal_end":
                if entity.lineage.origin.created_at > value:
                    return False
            if key in {
                "requirement",
                "dataset",
                "dataset_version",
                "experiment",
                "hypothesis",
                "feature",
                "feature_family",
                "factor",
                "market_regime",
                "market_event",
                "research_question",
                "economic_thesis",
                "alpha_candidate",
                "alpha",
                "validation_run",
            }:
                if not _serialized_contains(entity, value):
                    return False
            if key not in {
                "specification",
                "capability",
                "work_package",
                "evidence",
                "lifecycle_state",
                "confidence_threshold",
                "temporal_start",
                "temporal_end",
                "requirement",
                "dataset",
                "dataset_version",
                "experiment",
                "hypothesis",
                "feature",
                "feature_family",
                "factor",
                "market_regime",
                "market_event",
                "research_question",
                "economic_thesis",
                "alpha_candidate",
                "alpha",
                "validation_run",
            }:
                if getattr(entity, key, None) != value:
                    return False
        return True


class GraphQueryAdapter:
    """Read-only adapter over the IKROS Knowledge Graph."""

    def __init__(self, graph: KnowledgeGraph | None = None) -> None:
        self._graph = graph

    def exists(self, identifier: str) -> bool:
        return self._graph is not None and self._graph.has_node(identifier)

    def get(self, identifier: str) -> GraphNode | None:
        if self._graph is None or not self._graph.has_node(identifier):
            return None
        return self._graph.get_node(identifier)

    def execute(self, query: ParsedQuery) -> list[tuple[GraphNode, dict[str, Any]]]:
        if self._graph is None:
            return []
        operation = query.graph_operation
        if operation in {
            GraphOperation.DESCENDANTS,
            GraphOperation.SUCCESSORS,
        }:
            ids = self._graph.bfs(
                query.source_id or "",
                direction="out",
                max_depth=query.max_depth,
            )
            return self._nodes_with_meta(ids, {"operation": operation})
        if operation in {
            GraphOperation.ANCESTORS,
            GraphOperation.PREDECESSORS,
        }:
            ids = self._graph.bfs(
                query.source_id or "",
                direction="in",
                max_depth=query.max_depth,
            )
            return self._nodes_with_meta(ids, {"operation": operation})
        if operation == GraphOperation.SUPPORTING_EXPERIMENTS:
            ids = self._graph.bfs(
                query.source_id or "",
                direction="out",
                edge_types=frozenset({EdgeType.TESTED_IN}),
            )
            experiments = [
                node_id
                for node_id in ids
                if self._graph.get_node(node_id).node_type == "EXPERIMENT"
            ]
            return self._nodes_with_meta(experiments, {"operation": operation})
        if operation == GraphOperation.CONTRADICTIONS:
            ids = sorted({
                edge.source_id if edge.source_id != query.source_id else edge.target_id
                for edge in self._graph.get_contradictions(query.source_id or "")
            })
            return self._nodes_with_meta(ids, {"operation": operation})
        if operation == GraphOperation.FEATURES_FROM_DATASET:
            feature_ids = [
                edge.source_id
                for edge in self._graph.get_in_edges(query.source_id or "", EdgeType.DERIVED_FROM)
                if self._graph.get_node(edge.source_id).node_type == "FEATURE"
            ]
            return self._nodes_with_meta(sorted(feature_ids), {"operation": operation})
        if operation == GraphOperation.SHORTEST_PATH:
            path_ids = self._graph.find_path(query.source_id or "", query.target_id or "")
            return [
                (
                    self._graph.get_node(node_id),
                    {
                        "operation": operation,
                        "path": path_ids,
                        "path_index": idx,
                    },
                )
                for idx, node_id in enumerate(path_ids)
            ]
        if operation == GraphOperation.DEPENDENCY_CHAIN:
            ids = self._graph.bfs(
                query.source_id or "",
                direction=query.direction,
                edge_types=frozenset({EdgeType.DEPENDS_ON}),
                max_depth=query.max_depth,
            )
            return self._nodes_with_meta(ids, {"operation": operation})
        if operation == GraphOperation.CONTRADICTION_CHAIN:
            ids = self._contradiction_chain(query.source_id or "", query.max_depth)
            return self._nodes_with_meta(ids, {"operation": operation})
        return []

    def _nodes_with_meta(
        self,
        node_ids: list[str],
        meta: dict[str, Any],
    ) -> list[tuple[GraphNode, dict[str, Any]]]:
        if self._graph is None:
            return []
        return [
            (self._graph.get_node(node_id), dict(meta))
            for node_id in node_ids
        ]

    def _contradiction_chain(self, start_id: str, max_depth: int | None) -> list[str]:
        if self._graph is None or not self._graph.has_node(start_id):
            return []
        visited = {start_id}
        result: list[str] = []
        queue: list[tuple[str, int]] = [(start_id, 0)]
        while queue:
            current, depth = queue.pop(0)
            if max_depth is not None and depth >= max_depth:
                continue
            for edge in self._graph.get_contradictions(current):
                neighbor = edge.source_id if edge.source_id != current else edge.target_id
                if neighbor not in visited:
                    visited.add(neighbor)
                    result.append(neighbor)
                    queue.append((neighbor, depth + 1))
        return result


class MemoryQueryAdapter:
    """Read-only adapter over the IKROS memory subsystem."""

    def __init__(self, memory: ResearchMemoryManager | None = None) -> None:
        self._memory = memory

    def get(self, identifier: str) -> MemoryRecord | None:
        if self._memory is None or not self._memory.exists(identifier):
            return None
        return self._memory.get(identifier)

    def exists(self, identifier: str) -> bool:
        return self._memory is not None and self._memory.exists(identifier)

    def query(self, query: ParsedQuery) -> list[MemoryRecord]:
        if self._memory is None:
            return []
        memory_query = MemoryQuery(
            identifier=query.filters.get("identifier"),
            tier=None if query.target.upper() == "ALL" else query.target,
            entity_type=query.filters.get("entity_type"),
            specification=query.filters.get("specification"),
            capability=query.filters.get("capability"),
            work_package=query.filters.get("work_package"),
            evidence=query.filters.get("evidence"),
            feature=query.filters.get("feature"),
            hypothesis=query.filters.get("hypothesis"),
            experiment=query.filters.get("experiment"),
            alpha=query.filters.get("alpha"),
            lineage=query.filters.get("lineage"),
            min_confidence=_optional_float(query.filters.get("min_confidence")),
            max_confidence=_optional_float(query.filters.get("max_confidence")),
            start_time=query.filters.get("start_time"),
            end_time=query.filters.get("end_time"),
            lifecycle_state=query.filters.get("lifecycle_state"),
            tags=_optional_csv(query.filters.get("tags")),
        )
        return self._memory.retrieve(memory_query)


def _optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_csv(value: str | None) -> list[str]:
    if value is None or not value:
        return []
    return [part for part in value.split(",") if part]


def _serialized_contains(entity: IKROSEntity, value: str) -> bool:
    return value in json.dumps(entity.to_dict(), sort_keys=True, default=str)


def object_to_dict(obj: object) -> dict[str, Any]:
    """Return a normalized mapping for supported query objects."""
    if isinstance(obj, IKROSEntity):
        return obj.to_dict()
    if isinstance(obj, MemoryRecord):
        return obj.to_dict()
    if isinstance(obj, GraphNode):
        return obj.to_dict()
    raise TypeError(f"Unsupported query object type: {type(obj).__name__}")


def extract_confidence(obj: object) -> float:
    """Extract normalized confidence across entity, graph, and memory objects."""
    if isinstance(obj, IKROSEntity):
        return float(obj.confidence.overall())
    if isinstance(obj, MemoryRecord):
        return float(obj.confidence)
    if isinstance(obj, GraphNode):
        return float(obj.confidence)
    return 0.0


def extract_identifier(obj: object) -> str:
    if isinstance(obj, IKROSEntity):
        return obj.ikros_id
    if isinstance(obj, MemoryRecord):
        return obj.memory_id
    if isinstance(obj, GraphNode):
        return str(obj.node_id)
    raise TypeError(f"Unsupported query object type: {type(obj).__name__}")


def extract_type(obj: object) -> str:
    if isinstance(obj, IKROSEntity):
        return obj.entity_type
    if isinstance(obj, MemoryRecord):
        return obj.entity_type
    if isinstance(obj, GraphNode):
        return str(obj.node_type)
    raise TypeError(f"Unsupported query object type: {type(obj).__name__}")
