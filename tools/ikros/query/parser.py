"""IKROS query parser — deterministic structured grammar for institutional queries."""

from __future__ import annotations

import shlex

from tools.ikros.query.models import GraphOperation, ParsedQuery, QuerySource


class QueryParseError(ValueError):
    """Raised when a query string violates the deterministic grammar."""


class QueryParser:
    """Parser for the deterministic institutional query grammar."""

    def parse(self, query_text: str) -> ParsedQuery:
        tokens = shlex.split(query_text)
        if not tokens:
            raise QueryParseError("query is empty")
        if tokens[0].upper() != "GET":
            raise QueryParseError("query must start with GET")
        if len(tokens) < 3:
            raise QueryParseError("query is incomplete")

        source = tokens[1].upper()
        if source == QuerySource.ENTITY.value:
            return self._parse_entity(query_text, tokens)
        if source == QuerySource.REGISTRY.value:
            return self._parse_registry(query_text, tokens)
        if source == QuerySource.MEMORY.value:
            return self._parse_memory(query_text, tokens)
        if source == QuerySource.GRAPH.value:
            return self._parse_graph(query_text, tokens)
        raise QueryParseError(f"unsupported query source '{tokens[1]}'")

    def _parse_entity(self, raw: str, tokens: list[str]) -> ParsedQuery:
        if len(tokens) < 3:
            raise QueryParseError("ENTITY query requires an identifier")
        include_archive = any(token.upper() == "INCLUDE_ARCHIVE" for token in tokens[3:])
        return ParsedQuery(
            raw=raw,
            source=QuerySource.ENTITY,
            target=tokens[2],
            include_archive=include_archive,
        )

    def _parse_registry(self, raw: str, tokens: list[str]) -> ParsedQuery:
        if len(tokens) < 3:
            raise QueryParseError("REGISTRY query requires an entity type")
        filters = self._parse_where(tokens[3:])
        return ParsedQuery(
            raw=raw,
            source=QuerySource.REGISTRY,
            target=tokens[2],
            filters=filters,
        )

    def _parse_memory(self, raw: str, tokens: list[str]) -> ParsedQuery:
        if len(tokens) < 3:
            raise QueryParseError("MEMORY query requires a tier or ALL")
        include_archive = any(token.upper() == "INCLUDE_ARCHIVE" for token in tokens[3:])
        filtered_tokens = [
            token for token in tokens[3:] if token.upper() != "INCLUDE_ARCHIVE"
        ]
        filters = self._parse_where(filtered_tokens)
        return ParsedQuery(
            raw=raw,
            source=QuerySource.MEMORY,
            target=tokens[2],
            filters=filters,
            include_archive=include_archive,
        )

    def _parse_graph(self, raw: str, tokens: list[str]) -> ParsedQuery:
        operation = tokens[2].upper()
        if operation in {
            GraphOperation.DESCENDANTS,
            GraphOperation.ANCESTORS,
            GraphOperation.SUCCESSORS,
            GraphOperation.PREDECESSORS,
        }:
            if len(tokens) < 5 or tokens[3].upper() != "OF":
                raise QueryParseError(f"{operation} query requires 'OF <identifier>'")
            return ParsedQuery(
                raw=raw,
                source=QuerySource.GRAPH,
                target=tokens[4],
                graph_operation=operation,
                source_id=tokens[4],
                max_depth=self._parse_optional_int(tokens[5:], "MAX_DEPTH"),
            )
        if operation == GraphOperation.SUPPORTING_EXPERIMENTS:
            if len(tokens) < 5 or tokens[3].upper() != "FOR":
                raise QueryParseError("SUPPORTING_EXPERIMENTS query requires 'FOR <identifier>'")
            return ParsedQuery(
                raw=raw,
                source=QuerySource.GRAPH,
                target=tokens[4],
                graph_operation=operation,
                source_id=tokens[4],
            )
        if operation == GraphOperation.CONTRADICTIONS:
            if len(tokens) < 5 or tokens[3].upper() != "FOR":
                raise QueryParseError("CONTRADICTIONS query requires 'FOR <identifier>'")
            return ParsedQuery(
                raw=raw,
                source=QuerySource.GRAPH,
                target=tokens[4],
                graph_operation=operation,
                source_id=tokens[4],
            )
        if operation == GraphOperation.FEATURES_FROM_DATASET:
            if len(tokens) < 4:
                raise QueryParseError("FEATURES_FROM_DATASET query requires a dataset identifier")
            return ParsedQuery(
                raw=raw,
                source=QuerySource.GRAPH,
                target=tokens[3],
                graph_operation=operation,
                source_id=tokens[3],
            )
        if operation == GraphOperation.SHORTEST_PATH:
            if len(tokens) < 7 or tokens[3].upper() != "FROM" or tokens[5].upper() != "TO":
                raise QueryParseError("SHORTEST_PATH query requires 'FROM <id> TO <id>'")
            return ParsedQuery(
                raw=raw,
                source=QuerySource.GRAPH,
                target=f"{tokens[4]}->{tokens[6]}",
                graph_operation=operation,
                source_id=tokens[4],
                target_id=tokens[6],
            )
        if operation in {GraphOperation.DEPENDENCY_CHAIN, GraphOperation.CONTRADICTION_CHAIN}:
            if len(tokens) < 5 or tokens[3].upper() != "OF":
                raise QueryParseError(f"{operation} query requires 'OF <identifier>'")
            return ParsedQuery(
                raw=raw,
                source=QuerySource.GRAPH,
                target=tokens[4],
                graph_operation=operation,
                source_id=tokens[4],
                direction=self._parse_optional_choice(
                    tokens[5:],
                    "DIRECTION",
                    {"in", "out"},
                    "out",
                ),
                max_depth=self._parse_optional_int(tokens[5:], "MAX_DEPTH"),
            )
        raise QueryParseError(f"unsupported graph operation '{tokens[2]}'")

    def _parse_where(self, tokens: list[str]) -> dict[str, str]:
        if not tokens:
            return {}
        if tokens[0].upper() != "WHERE":
            raise QueryParseError("expected WHERE before filters")
        filters: dict[str, str] = {}
        for token in tokens[1:]:
            if token.upper() == "AND":
                continue
            if "=" not in token:
                raise QueryParseError(f"invalid filter '{token}'")
            key, value = token.split("=", 1)
            if not key:
                raise QueryParseError(f"invalid filter '{token}'")
            filters[key] = value
        return filters

    def _parse_optional_int(self, tokens: list[str], key: str) -> int | None:
        marker = key.upper()
        for idx, token in enumerate(tokens):
            if token.upper() == marker:
                if idx + 1 >= len(tokens):
                    raise QueryParseError(f"{key} requires an integer value")
                try:
                    return int(tokens[idx + 1])
                except ValueError as exc:
                    raise QueryParseError(f"{key} must be an integer") from exc
        return None

    def _parse_optional_choice(
        self,
        tokens: list[str],
        key: str,
        choices: set[str],
        default: str,
    ) -> str:
        marker = key.upper()
        for idx, token in enumerate(tokens):
            if token.upper() == marker:
                if idx + 1 >= len(tokens):
                    raise QueryParseError(f"{key} requires a value")
                value = tokens[idx + 1].lower()
                if value not in choices:
                    raise QueryParseError(
                        f"{key} must be one of {sorted(choices)}, got '{tokens[idx + 1]}'"
                    )
                return value
        return default
