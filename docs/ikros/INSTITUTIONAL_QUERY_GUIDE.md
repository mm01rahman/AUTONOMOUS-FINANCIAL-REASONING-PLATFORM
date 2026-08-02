# IKROS Institutional Query Guide

**Version:** 1.0.0  
**Specification:** SPEC-060 IKROS Architecture  
**Work Package:** WP-IMP-0045

---

## Overview

The IKROS Institutional Query Engine provides deterministic retrieval over the
IKROS registries, Institutional Knowledge Graph, and Institutional Research
Memory. It is storage-independent, reproducible, and audit-logged.

This subsystem is intentionally bounded:

- no natural-language parsing
- no LLM integration
- no semantic or vector search
- no autonomous reasoning
- no Runtime or Engineering OS changes

---

## Package Layout

| File | Responsibility |
|------|----------------|
| `tools/ikros/query/models.py` | Parsed queries, plans, results, and audit entries |
| `tools/ikros/query/parser.py` | Deterministic query grammar and parsing |
| `tools/ikros/query/planner.py` | Stable execution-plan generation |
| `tools/ikros/query/adapters.py` | Registry, graph, and memory adapters plus normalization |
| `tools/ikros/query/validation.py` | Query and result validation, archive access rules |
| `tools/ikros/query/audit.py` | Deterministic YAML-backed audit logging |
| `tools/ikros/query/engine.py` | End-to-end query execution, ranking, and audit emission |
| `tests/unit/test_ikros_query.py` | Parser, execution, validation, traversal, and audit coverage |

---

## Query Sources

The engine supports four deterministic sources:

| Source | Purpose |
|--------|---------|
| `ENTITY` | Resolve a canonical identifier across registries, graph, and memory |
| `REGISTRY` | Filter structured IKROS registry objects |
| `GRAPH` | Traverse the Institutional Knowledge Graph |
| `MEMORY` | Retrieve deterministic Institutional Research Memory records |

Every response returns normalized results with:

- object payload
- identifier
- type
- confidence
- lineage metadata
- evidence references
- specification references
- work package references
- temporal metadata
- version
- deterministic rank

---

## Deterministic Query Grammar

The parser accepts only structured commands.

### Entity lookup

```text
GET ENTITY <identifier>
GET ENTITY <identifier> INCLUDE_ARCHIVE
```

### Registry lookup

```text
GET REGISTRY <EntityType>
GET REGISTRY <EntityType> WHERE key=value AND key=value
```

### Memory lookup

```text
GET MEMORY <Tier|ALL>
GET MEMORY <Tier|ALL> WHERE key=value AND key=value
GET MEMORY <Tier|ALL> WHERE key=value INCLUDE_ARCHIVE
```

### Graph lookup

```text
GET GRAPH DESCENDANTS OF <identifier> MAX_DEPTH <n>
GET GRAPH ANCESTORS OF <identifier> MAX_DEPTH <n>
GET GRAPH SUPPORTING_EXPERIMENTS FOR <identifier>
GET GRAPH CONTRADICTIONS FOR <identifier>
GET GRAPH FEATURES_FROM_DATASET <identifier>
GET GRAPH SHORTEST_PATH FROM <source_id> TO <target_id>
GET GRAPH DEPENDENCY_CHAIN OF <identifier> DIRECTION <in|out> MAX_DEPTH <n>
GET GRAPH CONTRADICTION_CHAIN OF <identifier> MAX_DEPTH <n>
```

---

## Supported Registry Filters

Registry queries support exact or governed filters for:

- `specification`
- `capability`
- `work_package`
- `evidence`
- `lifecycle_state`
- `confidence_threshold`
- `temporal_start`
- `temporal_end`
- `requirement`
- `dataset`
- `dataset_version`
- `experiment`
- `hypothesis`
- `feature`
- `feature_family`
- `factor`
- `market_regime`
- `market_event`
- `research_question`
- `economic_thesis`
- `alpha_candidate`
- `alpha`
- `validation_run`

The implementation reuses the existing registries and extends read-only access
to secondary collections such as `FeatureFamily` and promoted `Alpha`.

---

## Supported Graph Operations

The engine supports the approved deterministic graph operations:

| Operation | Behavior |
|-----------|----------|
| `DESCENDANTS` | Forward breadth-first traversal |
| `ANCESTORS` | Reverse breadth-first traversal |
| `SUCCESSORS` | Forward traversal alias |
| `PREDECESSORS` | Reverse traversal alias |
| `SUPPORTING_EXPERIMENTS` | `TESTED_IN` traversal from a hypothesis |
| `CONTRADICTIONS` | Direct contradiction evidence relationships |
| `FEATURES_FROM_DATASET` | Reverse `DERIVED_FROM` lookup |
| `SHORTEST_PATH` | Deterministic path lookup between two graph nodes |
| `DEPENDENCY_CHAIN` | `DEPENDS_ON` traversal with direction control |
| `CONTRADICTION_CHAIN` | Breadth-first contradiction traversal |

Graph results remain storage-independent because traversal is mediated through
the `KnowledgeGraph` abstraction rather than a concrete graph database.

---

## Memory Query Support

The engine integrates with Institutional Research Memory and supports
deterministic retrieval by:

- identifier
- tier
- entity type
- specification
- capability
- work package
- evidence
- feature
- hypothesis
- experiment
- alpha
- lineage
- confidence range
- temporal range
- lifecycle state
- tags

Archive access is governed. `T5_ARCHIVE` results require `INCLUDE_ARCHIVE`.

---

## Ranking and Determinism

All query results are ranked deterministically by:

1. descending confidence
2. canonical identifier
3. normalized type

This keeps repeated query responses reproducible across runs.

---

## Audit Logging

Every query execution emits a YAML audit entry under:

```text
data/ikros/query/audit/
```

Audit entries record:

- canonical audit ID
- execution timestamp
- raw query
- parsed query
- execution plan
- ordered result identifiers
- result count

Canonical audit IDs follow:

```text
IQA-YYYYMMDD-#### 
```

---

## Usage Examples

```python
from pathlib import Path

from tools.ikros import QueryAuditLog, QueryEngine

engine = QueryEngine(audit_log=QueryAuditLog(Path("data/ikros/query/audit")))

engine.execute("GET ENTITY IKROS-HYP-20260802-0001")
engine.execute(
    "GET REGISTRY Hypothesis "
    "WHERE lifecycle_state=SUPPORTED AND capability=IKROS-QUERY"
)
engine.execute(
    "GET GRAPH SHORTEST_PATH FROM IKROS-RQ-20260802-0001 "
    "TO IKROS-ALPHA-20260802-0001"
)
engine.execute(
    "GET MEMORY T2_SEMANTIC WHERE hypothesis=IKROS-HYP-20260802-0001"
)
```

---

## Validation Rules

The query validator enforces:

- supported query-source grammar
- entity existence checks
- graph endpoint existence checks
- archive access controls
- confidence threshold bounds
- result identifier presence
- result confidence bounds
- lineage presence for registry and memory results

---

## Performance Considerations

- Registry lookups are deterministic scans over bounded in-memory registries.
- Graph traversal uses explicit breadth-first traversal against the loaded
  `KnowledgeGraph`.
- Memory lookups reuse the governed `MemoryQuery` retrieval path.
- Ranking is local and stable; no nondeterministic scoring is used.

The engine is intentionally optimized for correctness and reproducibility over
heuristic search.

---

## Limitations

- No natural-language query interface
- No fuzzy matching or semantic ranking
- No vector or embedding retrieval
- No authorization layer beyond repository governance
- No automatic cross-repository federation

---

## Future Extensions

Future Architecture Review Board work may add:

- additional storage adapters behind the current abstractions
- richer deterministic registry filters
- institutional query profiles and saved query catalogs
- governed integration with later IKROS memory and confidence capabilities

Those extensions can be added without changing the query grammar contract or
the current storage-independent engine surface.
