"""IKROS query engine — parse, validate, plan, execute, rank, and audit."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.ikros.graph import GraphNode, KnowledgeGraph
from tools.ikros.memory import MemoryRecord, ResearchMemoryManager
from tools.ikros.models import IKROSEntity
from tools.ikros.query.adapters import (
    GraphQueryAdapter,
    MemoryQueryAdapter,
    RegistryQueryAdapter,
    extract_confidence,
    extract_identifier,
    extract_type,
    object_to_dict,
)
from tools.ikros.query.audit import QueryAuditLog
from tools.ikros.query.models import (
    ParsedQuery,
    QueryAuditEntry,
    QueryPlan,
    QueryResponse,
    QueryResultItem,
    QuerySource,
)
from tools.ikros.query.parser import QueryParser
from tools.ikros.query.planner import QueryPlanner
from tools.ikros.query.validation import QueryValidator
from tools.ikros.registries.base import BaseRegistry


class QueryEngine:
    """Deterministic institutional query engine."""

    def __init__(
        self,
        registries: dict[str, BaseRegistry[IKROSEntity]] | None = None,
        graph: KnowledgeGraph | None = None,
        memory: ResearchMemoryManager | None = None,
        audit_log: QueryAuditLog | None = None,
    ) -> None:
        self._registry_adapter = RegistryQueryAdapter(registries)
        self._graph_adapter = GraphQueryAdapter(graph)
        self._memory_adapter = MemoryQueryAdapter(memory)
        self._parser = QueryParser()
        self._planner = QueryPlanner()
        self._validator = QueryValidator()
        self._audit_log = audit_log or QueryAuditLog(
            Path("data") / "ikros" / "query" / "audit"
        )

    def execute(self, query_text: str) -> QueryResponse:
        parsed = self._parser.parse(query_text)
        self._validator.validate(
            parsed,
            self._registry_adapter,
            self._graph_adapter,
            self._memory_adapter,
        )
        plan = self._planner.build(parsed)
        results = self._execute_plan(parsed, plan)
        ranked = self._rank_results(results)
        self._validator.validate_results(ranked)
        audit_entry = self._write_audit(parsed, plan, ranked)
        return QueryResponse(
            parsed_query=parsed,
            plan=plan,
            results=ranked,
            audit_id=audit_entry.audit_id,
            executed_at=audit_entry.executed_at,
        )

    def _execute_plan(
        self,
        query: ParsedQuery,
        _plan: QueryPlan,
    ) -> list[QueryResultItem]:
        if query.source == QuerySource.ENTITY:
            return self._execute_entity(query)
        if query.source == QuerySource.REGISTRY:
            entities = self._registry_adapter.query(query.target, query.filters)
            return [self._normalize_registry_result(entity) for entity in entities]
        if query.source == QuerySource.MEMORY:
            records = self._memory_adapter.query(query)
            if not query.include_archive:
                records = [
                    record
                    for record in records
                    if record.tier != "T5_ARCHIVE"
                ]
            return [self._normalize_memory_result(record) for record in records]
        if query.source == QuerySource.GRAPH:
            graph_results = self._graph_adapter.execute(query)
            return [
                self._normalize_graph_result(node, meta)
                for node, meta in graph_results
            ]
        return []

    def _execute_entity(self, query: ParsedQuery) -> list[QueryResultItem]:
        results: list[QueryResultItem] = []
        registry_entity = self._registry_adapter.get(query.target)
        if registry_entity is not None:
            results.append(self._normalize_registry_result(registry_entity))
        memory_record = self._memory_adapter.get(query.target)
        if memory_record is not None:
            if memory_record.tier != "T5_ARCHIVE" or query.include_archive:
                results.append(self._normalize_memory_result(memory_record))
        graph_node = self._graph_adapter.get(query.target)
        if graph_node is not None:
            results.append(self._normalize_graph_result(graph_node, {"operation": "ENTITY"}))
        return results

    def _rank_results(self, results: list[QueryResultItem]) -> list[QueryResultItem]:
        ranked = sorted(
            results,
            key=lambda item: (-item.confidence, item.identifier, item.type),
        )
        for idx, item in enumerate(ranked, start=1):
            item.rank = idx
        return ranked

    def _write_audit(
        self,
        query: ParsedQuery,
        plan: QueryPlan,
        results: list[QueryResultItem],
    ) -> QueryAuditEntry:
        audit_id = self._audit_log.next_audit_id()
        entry = QueryAuditEntry(
            audit_id=audit_id,
            executed_at=datetime.now(UTC).isoformat(),
            raw_query=query.raw,
            parsed_query=query.to_dict(),
            plan=plan.to_dict(),
            result_ids=[result.identifier for result in results],
            result_count=len(results),
        )
        self._audit_log.write(entry)
        return entry

    def _normalize_registry_result(self, entity: IKROSEntity) -> QueryResultItem:
        return QueryResultItem(
            object=object_to_dict(entity),
            identifier=extract_identifier(entity),
            type=extract_type(entity),
            confidence=extract_confidence(entity),
            lineage=entity.lineage.to_dict(),
            evidence_refs=list(entity.lineage.evidence.ers_records),
            specification_refs=list(entity.spec_refs),
            work_package_refs=list(entity.work_package_refs),
            temporal_metadata={
                "created_at": entity.lineage.origin.created_at,
                "valid_from": entity.lineage.origin.created_at,
                "valid_to": entity.lineage.retirement.retired_at,
            },
            version=entity.version,
            source="registry",
        )

    def _normalize_memory_result(self, record: MemoryRecord) -> QueryResultItem:
        return QueryResultItem(
            object=object_to_dict(record),
            identifier=extract_identifier(record),
            type=extract_type(record),
            confidence=extract_confidence(record),
            lineage={
                "source_ids": list(record.source_ids),
                "lineage_ids": list(record.lineage_ids),
                "dependency_ids": list(record.dependency_ids),
                "graph_node_ids": list(record.graph_node_ids),
            },
            evidence_refs=list(record.evidence_refs),
            specification_refs=list(record.spec_refs),
            work_package_refs=list(record.work_package_refs),
            temporal_metadata={
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "valid_from": record.valid_from,
                "valid_to": record.valid_to,
                "retired_at": record.retired_at,
                "archived_at": record.archived_at,
            },
            version=record.version,
            source="memory",
        )

    def _normalize_graph_result(
        self,
        node: GraphNode,
        extra_lineage: dict[str, Any],
    ) -> QueryResultItem:
        lineage = {"graph_node_ids": [node.node_id]}
        lineage.update(extra_lineage)
        return QueryResultItem(
            object=object_to_dict(node),
            identifier=extract_identifier(node),
            type=extract_type(node),
            confidence=extract_confidence(node),
            lineage=lineage,
            evidence_refs=[],
            specification_refs=list(node.spec_refs),
            work_package_refs=list(node.wp_refs),
            temporal_metadata={
                "created_at": node.created_at,
                "valid_from": node.valid_from,
                "valid_to": node.valid_to,
            },
            version="1.0",
            source="graph",
        )
