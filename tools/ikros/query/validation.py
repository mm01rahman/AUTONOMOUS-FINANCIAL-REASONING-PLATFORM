"""IKROS query validation — syntax, reference integrity, archive access, and results."""

from __future__ import annotations

from tools.ikros.memory import MemoryLifecycleState, MemoryTier
from tools.ikros.query.adapters import GraphQueryAdapter, MemoryQueryAdapter, RegistryQueryAdapter
from tools.ikros.query.models import ParsedQuery, QueryResultItem, QuerySource


class QueryValidationError(ValueError):
    """Raised when a parsed query or its results fail validation."""


class QueryValidator:
    """Validate parsed queries against the active IKROS stores."""

    def validate(
        self,
        query: ParsedQuery,
        registries: RegistryQueryAdapter,
        graph: GraphQueryAdapter,
        memory: MemoryQueryAdapter,
    ) -> None:
        if query.source == QuerySource.ENTITY:
            self._validate_entity_query(query, registries, graph, memory)
            return
        if query.source == QuerySource.REGISTRY:
            self._validate_registry_query(query)
            return
        if query.source == QuerySource.MEMORY:
            self._validate_memory_query(query, memory)
            return
        if query.source == QuerySource.GRAPH:
            self._validate_graph_query(query, graph)
            return
        raise QueryValidationError(f"unsupported query source '{query.source}'")

    def validate_results(self, results: list[QueryResultItem]) -> None:
        for result in results:
            if not result.identifier:
                raise QueryValidationError("query result identifier is required")
            if not (0.0 <= result.confidence <= 1.0):
                raise QueryValidationError(
                    f"query result '{result.identifier}' has invalid confidence"
                )
            if not result.type:
                raise QueryValidationError(
                    f"query result '{result.identifier}' has no type"
                )
            if result.source in {"registry", "memory"} and not result.lineage:
                raise QueryValidationError(
                    f"query result '{result.identifier}' is missing lineage"
                )

    def _validate_entity_query(
        self,
        query: ParsedQuery,
        registries: RegistryQueryAdapter,
        graph: GraphQueryAdapter,
        memory: MemoryQueryAdapter,
    ) -> None:
        memory_record = memory.get(query.target)
        if (
            memory_record is not None
            and memory_record.tier == MemoryTier.ARCHIVE.value
            and not query.include_archive
        ):
            raise QueryValidationError(
                "archived memory requires INCLUDE_ARCHIVE"
            )
        if (
            registries.get(query.target) is None
            and graph.get(query.target) is None
            and memory_record is None
        ):
            raise QueryValidationError(f"identifier '{query.target}' does not exist")

    def _validate_registry_query(self, query: ParsedQuery) -> None:
        if not query.target:
            raise QueryValidationError("registry query requires an entity type")
        threshold = query.filters.get("confidence_threshold")
        if threshold is not None:
            self._validate_confidence_value(threshold)

    def _validate_memory_query(
        self,
        query: ParsedQuery,
        memory: MemoryQueryAdapter,
    ) -> None:
        if (
            query.target == MemoryTier.ARCHIVE.value
            or query.filters.get("lifecycle_state") == MemoryLifecycleState.ARCHIVED.value
        ) and not query.include_archive:
            raise QueryValidationError("archived memory access requires INCLUDE_ARCHIVE")
        if query.filters.get("min_confidence") is not None:
            self._validate_confidence_value(query.filters["min_confidence"])
        if query.filters.get("max_confidence") is not None:
            self._validate_confidence_value(query.filters["max_confidence"])
        identifier = query.filters.get("identifier")
        if identifier is not None and memory.get(identifier) is None:
            raise QueryValidationError(f"memory identifier '{identifier}' does not exist")

    def _validate_graph_query(
        self,
        query: ParsedQuery,
        graph: GraphQueryAdapter,
    ) -> None:
        if query.source_id is not None and not graph.exists(query.source_id):
            raise QueryValidationError(
                f"graph identifier '{query.source_id}' does not exist"
            )
        if query.target_id is not None and not graph.exists(query.target_id):
            raise QueryValidationError(
                f"graph identifier '{query.target_id}' does not exist"
            )
        if query.max_depth is not None and query.max_depth < 0:
            raise QueryValidationError("MAX_DEPTH must be non-negative")

    def _validate_confidence_value(self, value: str) -> None:
        parsed = float(value)
        if not (0.0 <= parsed <= 1.0):
            raise QueryValidationError("confidence thresholds must be in [0, 1]")
