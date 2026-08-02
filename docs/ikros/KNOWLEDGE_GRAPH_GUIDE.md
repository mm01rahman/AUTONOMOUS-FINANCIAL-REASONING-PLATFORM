# IKROS Knowledge Graph Guide

**Version:** 1.0.0
**Specification:** SPEC-060 IKROS Architecture
**Work Package:** WP-IMP-0043

---

## Overview

The IKROS Knowledge Graph is the storage-independent relationship layer for AFRP
institutional research objects. It connects core registry entities through typed,
versioned edges, preserves lineage, records contradictions without deletion, and
supports deterministic traversal, persistence, and validation.

This implementation is intentionally bounded to the Knowledge Graph foundation.
It does **not** implement memory, natural-language querying, vector retrieval,
autonomous research, or Runtime integration beyond the approved graph interface.

---

## Package Layout

| File | Responsibility |
|------|----------------|
| `tools/ikros/graph/models.py` | Node and edge types, graph dataclasses, deterministic serialisation helpers |
| `tools/ikros/graph/core.py` | In-memory directed property graph, traversal, path finding, graph summary |
| `tools/ikros/graph/lineage.py` | Forward and reverse lineage traversal helpers |
| `tools/ikros/graph/confidence.py` | Deterministic confidence propagation and contradiction penalties |
| `tools/ikros/graph/validation.py` | Structural, semantic, temporal, and evidence validation |
| `tools/ikros/graph/persistence.py` | Repository port and YAML adapter |
| `tests/unit/test_ikros_graph.py` | Unit and integration coverage for the full graph stack |

---

## Public API

```python
from pathlib import Path

from tools.ikros import (
    ConfidencePropagator,
    EdgeType,
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    LineageEngine,
    NodeType,
    YAMLGraphRepository,
    assert_graph_valid,
)
```

---

## Node Catalogue

The graph supports 27 first-class node types:

| Node Type |
|-----------|
| `RESEARCH_QUESTION` |
| `ECONOMIC_THESIS` |
| `LITERATURE` |
| `DATASET` |
| `DATASET_VERSION` |
| `FEATURE` |
| `FEATURE_FAMILY` |
| `FACTOR` |
| `HYPOTHESIS` |
| `EXPERIMENT` |
| `VALIDATION` |
| `MODEL` |
| `WORLD_MODEL` |
| `BACKTEST` |
| `WALK_FORWARD_STUDY` |
| `STRESS_TEST` |
| `MONTE_CARLO_STUDY` |
| `MARKET_EVENT` |
| `REGIME` |
| `DECISION` |
| `POLICY` |
| `ALPHA_CANDIDATE` |
| `ALPHA` |
| `FAILURE` |
| `EVIDENCE` |
| `RESEARCH_CONCLUSION` |
| `KNOWLEDGE_OBJECT` |

Every `GraphNode` stores:

- immutable `node_id`
- canonical `ikros_id`
- typed `node_type`
- `confidence` in `[0.0, 1.0]`
- optional valid-time interval via `valid_from` / `valid_to`
- `spec_refs` and `wp_refs`
- free-form `attributes`

---

## Relationship Catalogue

The graph supports 20 deterministic edge types:

| Edge Type | Purpose |
|-----------|---------|
| `USES_DATASET` | Experiment or derivative object consumes a dataset |
| `GENERATED_FEATURE` | Upstream object produces a feature |
| `SUPPORTED_BY` | Positive supporting evidence |
| `TESTED_IN` | Hypothesis or dependency is evaluated in an experiment |
| `VALIDATED_BY` | Validation evidence for an object |
| `GENERATED_ALPHA` | Experiment produces an alpha candidate |
| `REJECTED_BY` | Negative rejection evidence |
| `CONTRADICTED_BY` | Explicit contradiction relationship |
| `DERIVED_FROM` | Provenance or derivation |
| `SUPERSEDES` | Institutional replacement without deletion |
| `DEPENDS_ON` | Dependency relationship |
| `RELATED_TO` | Weak semantic association |
| `PRODUCED` | Strong production / promotion output |
| `EVALUATED` | Evaluation link |
| `OBSERVED_DURING` | Event or regime observation context |
| `EXPLAINS` | Explanatory relationship |
| `CAUSES` | Causal relationship |
| `ASSOCIATED_WITH` | Non-causal association |
| `IMPLEMENTS` | Strategy or policy implementation |
| `REFUTES` | Explicit falsification relationship |

Every `GraphEdge` stores:

- immutable `edge_id`
- `source_id` and `target_id`
- typed `edge_type`
- `version`
- `timestamp`
- `confidence` in `[0.0, 1.0]`
- optional `evidence_ref`, `spec_ref`, `wp_ref`
- free-form `attributes`

Contradiction edges are first-class and never imply deletion.

---

## Creating a Graph

```python
from tools.ikros import EdgeType, GraphEdge, GraphNode, KnowledgeGraph, NodeType

graph = KnowledgeGraph()

graph.add_node(
    GraphNode(
        node_id="IKROS-RQ-20260802-0001",
        ikros_id="IKROS-RQ-20260802-0001",
        node_type=NodeType.RESEARCH_QUESTION,
        label="Does XAU/USD regime persistence create usable alpha?",
        confidence=0.35,
        spec_refs=["SPEC-060"],
        wp_refs=["WP-IMP-0043"],
    )
)

graph.add_node(
    GraphNode(
        node_id="IKROS-HYP-20260802-0001",
        ikros_id="IKROS-HYP-20260802-0001",
        node_type=NodeType.HYPOTHESIS,
        label="Regime persistence predicts continuation",
        confidence=0.45,
    )
)

graph.add_edge(
    GraphEdge(
        edge_id=graph.next_edge_id(),
        source_id="IKROS-RQ-20260802-0001",
        target_id="IKROS-HYP-20260802-0001",
        edge_type=EdgeType.DEPENDS_ON,
        confidence=0.90,
        spec_ref="SPEC-060",
        wp_ref="WP-IMP-0043",
    )
)
```

---

## Traversal and Lineage

### Basic traversal

```python
downstream = graph.bfs("IKROS-RQ-20260802-0001")
upstream = graph.bfs("IKROS-HYP-20260802-0001", direction="in")
path = graph.find_path(
    "IKROS-RQ-20260802-0001",
    "IKROS-HYP-20260802-0001",
)
```

### Lineage traversal

```python
lineage = LineageEngine(graph)

full_lineage = lineage.get_full_lineage("IKROS-HYP-20260802-0001")
research_chain = lineage.get_research_chain("IKROS-RQ-20260802-0001")
alpha_paths = lineage.get_alpha_chain("IKROS-RQ-20260802-0001")
contradictions = lineage.get_contradicting_nodes("IKROS-HYP-20260802-0001")
```

`LineageEngine` uses governed lineage edge sets so forward and reverse traversal
remain deterministic and bounded.

---

## Confidence Propagation

`ConfidencePropagator` implements deterministic, bounded propagation:

- downstream propagation uses a damping factor of `0.85`
- propagation depth defaults to `5`
- confidence is capped at `0.95`
- each contradiction reduces effective confidence by `0.20`

```python
propagator = ConfidencePropagator(graph)

downstream_map = propagator.propagate_downstream("IKROS-RQ-20260802-0001")
effective_confidence = propagator.aggregate_upstream_confidence(
    "IKROS-HYP-20260802-0001",
)
summary = propagator.get_propagation_summary()
```

This implementation preserves determinism by sorting node IDs for whole-graph
aggregation and by avoiding probabilistic weighting.

---

## Persistence Model

The persistence boundary follows the approved port/adapter structure:

```text
KnowledgeGraphRepository
        |
        +-- YAMLGraphRepository
```

Current deterministic YAML layout:

```text
data/ikros/graph/
  nodes/
    IKROS-RQ-20260802-0001.yaml
    IKROS-HYP-20260802-0001.yaml
  edges.yaml
```

Example:

```python
repo = YAMLGraphRepository(Path("data/ikros/graph"))
repo.save(graph)
reloaded = repo.load()
```

Design constraints:

- node files are persisted one-per-entity
- edges are stored as a sorted YAML manifest
- save → load is deterministic
- future adapters can target SQLite, NetworkX, Neo4j, or Memgraph
- graph API stays unchanged across storage backends

---

## Validation

Use `validate_graph()` for non-throwing checks or `assert_graph_valid()` to fail
fast.

```python
errors = validate_graph(graph)
assert_graph_valid(graph)
```

Current validation covers:

- valid node and edge types
- referential integrity
- duplicate prevention at insertion time
- confidence bounds
- temporal consistency on nodes
- contradiction edges requiring `evidence_ref`
- dangling adjacency detection
- isolated node discovery

Helpers:

- `find_isolated_nodes(graph)`
- `find_missing_evidence(graph)`
- `check_referential_integrity(graph)`

---

## Determinism Notes

Determinism is a hard requirement for WP-IMP-0043. The implementation preserves
it by:

- generating canonical edge IDs via monotonic sequence counters
- sorting edge manifests before persistence
- loading node files alphabetically
- sorting graph-wide confidence maps by node ID
- keeping serialisation limited to plain YAML-safe scalars and mappings

---

## Integration Notes

- The Knowledge Graph lives under `tools/ikros/graph/`.
- It does not import AFRP Runtime modules.
- It composes with the existing IKROS core registries through shared IDs and
  governance references.
- Runtime behaviour remains unchanged.

---

## Limitations

- No graph database adapter is included yet; YAML is the initial deterministic
  backend.
- Edge valid-time intervals are represented only through edge metadata fields
  currently supplied by callers.
- No automatic ontology enforcement beyond type sets and validation helpers.
- No natural-language, semantic, or vector query layer.
- No autonomous research automation, GNN, or Memory Engine integration.

---

## Future Extensions

Future ARB-approved work may add:

- SQLite-backed persistence
- graph database adapters
- richer temporal edge validation
- query and retrieval APIs
- memory-tier integration
- ontology-aware validation rules

These extensions must preserve the current public graph API and storage
independence boundary.
