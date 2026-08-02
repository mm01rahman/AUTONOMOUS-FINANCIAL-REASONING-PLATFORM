# IKROS Research Memory Guide

**Version:** 1.0.0
**Specification:** SPEC-060 IKROS Architecture
**Work Package:** WP-IMP-0044

---

## Overview

The IKROS Institutional Research Memory subsystem preserves, organizes,
consolidates, retrieves, retires, archives, and restores governed research
knowledge for AFRP. It is a deterministic institutional memory system built on
structured records, lifecycle controls, and Knowledge Graph lineage.

This subsystem is intentionally bounded to governed research memory:

- no natural-language search
- no vector database behavior
- no LLM memory semantics
- no Runtime or Engineering OS changes
- no autonomous research automation

---

## Package Layout

| File | Responsibility |
|------|----------------|
| `tools/ikros/memory/models.py` | Memory tiers, lifecycle states, canonical IDs, memory records |
| `tools/ikros/memory/core.py` | Store, promote, consolidate, merge, retire, archive, restore |
| `tools/ikros/memory/retrieval.py` | Structured deterministic retrieval filters |
| `tools/ikros/memory/validation.py` | Record, lineage, archive, and graph-reference validation |
| `tools/ikros/memory/persistence.py` | Storage abstraction and YAML adapter |
| `tests/unit/test_ikros_memory.py` | Unit and integration coverage |

---

## Memory Tier Specification

The implementation follows the approved six-tier model:

| Tier | Enum | Purpose |
|------|------|---------|
| T0 | `T0_WORKING` | Temporary execution context and session-scoped working state |
| T1 | `T1_EPISODIC` | Research sessions, experiments, observations, and event history |
| T2 | `T2_SEMANTIC` | Validated concepts, mechanisms, conclusions, and factual assertions |
| T3 | `T3_PROCEDURAL` | Validated methods, protocols, and research procedures |
| T4 | `T4_INSTITUTIONAL` | Approved institutional knowledge and durable research history |
| T5 | `T5_ARCHIVE` | Retired, deprecated, superseded, and historical memory retained without deletion |

All tiers use the same governed `MemoryRecord` model so promotion and retrieval
remain deterministic and storage-independent.

---

## Canonical Memory Model

Every memory record stores:

- canonical `memory_id`
- approved `tier`
- `entity_type`
- `title` and `summary`
- `source_ids`
- `graph_node_ids`
- `lineage_ids`
- `dependency_ids`
- `spec_refs`, `capability_refs`, `work_package_refs`, `evidence_refs`
- `confidence`
- `lifecycle_state`
- `version` and `version_history`
- valid-time metadata and archive / retirement timestamps
- structured `payload`

Canonical memory IDs follow:

```text
IKMEM-T{0..5}-{YYYYMMDD}-{SEQ:04d}
```

Examples:

- `IKMEM-T0-20260802-0001`
- `IKMEM-T2-20260802-0003`
- `IKMEM-T5-20260802-0011`

---

## Working Memory

T0 working memory is modeled through `WorkingMemorySnapshot`, which captures:

- active research question
- active experiment
- active hypotheses
- active features
- active dataset version
- intermediate results
- session flags
- current confidence

```python
from tools.ikros import ResearchMemoryManager, WorkingMemorySnapshot

manager = ResearchMemoryManager()

snapshot = WorkingMemorySnapshot(
    session_id="SESSION-001",
    active_research_question="IKROS-RQ-20260802-0001",
    active_experiment="IKROS-EXP-20260802-0001",
    active_hypotheses=["IKROS-HYP-20260802-0001"],
    active_features=["IKROS-FEAT-20260802-0001"],
    current_confidence=0.42,
)

memory_id = manager.store_working_memory(snapshot)
```

Working memory is deterministic, session-scoped, and consolidates into episodic
memory rather than being silently discarded.

---

## Memory Operations

The manager supports the required deterministic operations:

- `store`
- `retrieve`
- `promote`
- `consolidate`
- `merge`
- `retire`
- `archive`
- `restore`
- `validate`
- `version`

### Core example

```python
from tools.ikros import (
    MemoryQuery,
    MemoryRecord,
    MemoryTier,
    ResearchMemoryManager,
)

manager = ResearchMemoryManager()

record = MemoryRecord(
    memory_id=manager.next_id(MemoryTier.EPISODIC),
    tier=MemoryTier.EPISODIC,
    entity_type="Experiment",
    title="Walk-forward study for regime persistence",
    source_ids=["IKROS-EXP-20260802-0001"],
    graph_node_ids=["IKROS-EXP-20260802-0001"],
    confidence=0.78,
)

manager.store(record)
manager.consolidate(record.memory_id, MemoryTier.SEMANTIC)
result = manager.retrieve(MemoryQuery(entity_type="Experiment"))
```

---

## Consolidation Rules

The memory subsystem applies deterministic consolidation rules.

### Default consolidation

| Current Tier | Deterministic Default |
|--------------|-----------------------|
| `T0_WORKING` | `T1_EPISODIC` |
| `T1_EPISODIC` + `entity_type == Failure` | `T4_INSTITUTIONAL` |
| `T1_EPISODIC` + `confidence >= 0.75` | `T2_SEMANTIC` |
| `T1_EPISODIC` otherwise | `T4_INSTITUTIONAL` |
| retired or archived records | `T5_ARCHIVE` |

### Governed examples

Repeated experiment:

```text
T1 Episodic -> validated repeatedly -> T2 Semantic
```

Rejected or retired knowledge:

```text
T4 Institutional -> retired -> T5 Archive
```

Nothing is deleted. Archive remains retrievable and restorable.

---

## Retrieval Guide

Retrieval is structured and deterministic through `MemoryQuery`.

Supported filters:

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

### Retrieval examples

```python
from tools.ikros import MemoryQuery

manager.retrieve(MemoryQuery(identifier="IKMEM-T1-20260802-0001"))
manager.retrieve(MemoryQuery(entity_type="Hypothesis"))
manager.retrieve(MemoryQuery(specification="SPEC-060"))
manager.retrieve(MemoryQuery(capability="IKROS-MEMORY"))
manager.retrieve(MemoryQuery(work_package="WP-IMP-0044"))
manager.retrieve(MemoryQuery(hypothesis="IKROS-HYP-20260802-0001"))
manager.retrieve(MemoryQuery(min_confidence=0.70, max_confidence=0.95))
manager.retrieve(
    MemoryQuery(
        start_time="2026-08-01T00:00:00+00:00",
        end_time="2026-08-31T23:59:59+00:00",
    )
)
```

Natural-language search is intentionally out of scope.

---

## Lifecycle Documentation

Memory records transition through these governed states:

| State | Meaning |
|-------|---------|
| `ACTIVE` | Stored and available in its current tier |
| `CONSOLIDATED` | Consolidated into a new tier |
| `PROMOTED` | Explicitly promoted into a higher tier |
| `MERGED` | Produced by deterministic record merge |
| `RETIRED` | Kept historically but no longer current |
| `ARCHIVED` | Moved into T5 archive |
| `RESTORED` | Brought back from archive into an active tier |

Lifecycle updates append `version_history` entries rather than rewriting memory
history.

---

## Validation

Validation covers:

- canonical memory ID format
- approved tier and lifecycle state
- confidence bounds
- temporal consistency
- required source or graph linkage for non-working memory
- archive integrity
- retirement metadata
- duplicate fingerprint detection
- broken lineage references
- broken graph node references

Use:

```python
from tools.ikros import assert_memory_valid

assert_memory_valid(manager._records)  # internal store validation
```

Or call:

```python
manager.validate()
```

---

## Persistence

Persistence follows a storage abstraction:

```text
MemoryRepository
    |
    +-- YAMLMemoryRepository
```

Current YAML layout:

```text
data/ikros/memory/
  t0-working/
  t1-episodic/
  t2-semantic/
  t3-procedural/
  t4-institutional/
  t5-archive/
```

Every record is serialized into a deterministic single YAML file located under
its tier directory.

Future adapters may target:

- SQLite
- PostgreSQL
- object storage
- graph-backed persistence

without changing the public memory API.

---

## Knowledge Graph Integration

Memory integrates with the IKROS Knowledge Graph through `graph_node_ids` and
graph-aware validation:

- non-working records can anchor to governed graph nodes
- retrieval preserves graph lineage references
- validation rejects missing graph nodes
- archive and restoration preserve graph linkage

This keeps memory lineage consistent with the institutional graph without
coupling memory to any graph database implementation.

---

## Determinism Guarantees

The subsystem preserves determinism by:

- canonical sequential memory IDs
- sorted record iteration
- structured retrieval only
- deterministic default consolidation rules
- deterministic merge ordering
- YAML single-record persistence
- append-only version history

---

## Limitations

- No natural-language, semantic, or vector search
- No automatic ontology inference
- No background consolidation engine
- No direct Runtime integration
- No autonomous research orchestration
- No graph reasoning or LLM integration

---

## Future Extensions

ARB-approved follow-on work may add:

- richer procedural-memory templates
- retention policy scheduling
- institutional review workflows
- alternative persistence backends
- dedicated memory health reports

Those extensions must preserve the current storage-independent API.
