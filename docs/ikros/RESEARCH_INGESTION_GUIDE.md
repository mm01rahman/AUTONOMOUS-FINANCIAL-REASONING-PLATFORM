# IKROS Research Ingestion Guide

**Version:** 1.0.0  
**Specification:** SPEC-060 IKROS Architecture  
**Work Package:** WP-IMP-0046

---

## Overview

The IKROS Institutional Research Ingestion Engine transforms structured research
documents into governed IKROS objects without using natural-language reasoning,
LLMs, embeddings, or autonomous research logic.

The subsystem is intentionally bounded:

- no free-text semantic inference
- no automatic hypothesis generation
- no summarization beyond explicit structured fields
- no Runtime or Engineering OS changes
- no registry bypasses for registry-backed entity types

---

## Package Layout

| File | Responsibility |
|------|----------------|
| `tools/ikros/ingestion/models.py` | Structured source, extracted object, relationship, result, and report models |
| `tools/ikros/ingestion/loaders.py` | Deterministic Markdown, YAML, and JSON document loading |
| `tools/ikros/ingestion/validation.py` | Source, object, reference, lifecycle, and duplicate validation |
| `tools/ikros/ingestion/persistence.py` | YAML-backed ingestion report repository |
| `tools/ikros/ingestion/engine.py` | End-to-end ingestion, registry routing, graph integration, memory integration, and query integration |
| `tests/unit/test_ikros_ingestion.py` | Source loading, integration, duplicate detection, validation, and determinism coverage |

---

## Supported Source Formats

The loader accepts:

| Format | Support |
|--------|---------|
| Markdown | Front matter, metadata lines, section extraction, fenced YAML/JSON object blocks |
| YAML | Structured document payloads and ERS-1.0 evidence records |
| JSON | Structured document payloads with explicit IKROS object blocks |

Supported source kinds include:

- AFRP specifications
- internal research reports
- experiment reports
- validation reports
- backtest reports
- statistical reports
- evidence records
- ADRs
- generic structured Markdown
- generic structured YAML
- generic structured JSON

Extension points are preserved through the loader and source-kind model for
future academic papers, central bank publications, exchange documentation, and
market reports.

---

## Deterministic Extraction Model

The ingestion engine extracts only explicitly structured knowledge objects.

Preferred source schema:

```yaml
metadata:
  source_kind: INTERNAL_RESEARCH_REPORT
  specification_refs: [SPEC-060]
  work_package_id: WP-IMP-0046
ikros_objects:
  - type: ResearchQuestion
    identifier: IKROS-RQ-20260802-0001
    title: Does gold regime persistence predict continuation?
    summary: Structured import example
    lifecycle_state: OPEN
    confidence: 0.72
    source_ids: []
    dependency_ids: []
    capability_refs: [IKROS-INGESTION]
    work_package_refs: [WP-IMP-0046]
    attributes:
      instrument: XAU/USD
      scope: MACRO
      time_horizon: 1D
```

For Markdown, the same object list may be supplied in:

1. YAML front matter, or
2. a fenced YAML/JSON block in the body

When no explicit object block exists, the engine can still ingest a structured
specification, ADR, Markdown, YAML, or JSON document as a governed
`KnowledgeObject`.

ERS-1.0 evidence records are extracted automatically into:

- `Evidence`
- `Validation`

---

## Extraction Catalogue

The engine supports deterministic ingestion for:

- `ResearchQuestion`
- `EconomicThesis`
- `Hypothesis`
- `Feature`
- `FeatureFamily`
- `Dataset`
- `DatasetVersion`
- `Experiment`
- `Validation`
- `MarketEvent`
- `Regime`
- `AlphaCandidate`
- `Alpha`
- `ResearchConclusion`
- `Evidence`
- `ContradictoryEvidence`
- `KnowledgeObject`

Registry-backed types are routed through existing registries:

- `ResearchQuestion` → `ResearchRegistry`
- `Hypothesis` → `HypothesisRegistry`
- `Experiment` → `ExperimentRegistry`
- `Feature` / `FeatureFamily` → `FeatureRegistry`
- `AlphaCandidate` / `Alpha` → `AlphaRegistry`

Non-registry knowledge objects are still preserved through:

- Knowledge Graph nodes
- Research Memory records
- ingestion reports

---

## Classification and Metadata

Every extracted object is normalized with:

- canonical identifier
- object type
- specification references
- confidence
- source reference
- version
- lifecycle state
- lineage references
- dependency references
- explicit graph relationships

Graph nodes preserve the normalized object shape, and memory records preserve
the ingested payload plus provenance and references.

---

## Validation Rules

The ingestion validator enforces:

- supported object types only
- canonical IKROS identifiers
- required title and source reference
- at least one specification reference
- confidence in `[0, 1]`
- lifecycle validity for non-registry object types
- duplicate identifier rejection
- duplicate content rejection within a batch
- duplicate content rejection against prior ingestion reports
- explicit relationship type validation
- relationship target existence
- dependency and source reference existence

Registry-backed entities also pass the existing IKROS entity validation rules by
being materialized into canonical entity models before registration.

---

## Duplicate Detection

Two duplicate checks are enforced:

1. **Exact source duplicate**  
   If the same `source_ref` and `content_hash` have already been ingested, the
   engine returns `SKIPPED_DUPLICATE` deterministically.

2. **Object-content duplicate**  
   Every normalized extracted object produces a deterministic fingerprint. If
   the fingerprint already exists in prior ingestion reports, ingestion fails.

This prevents silent multi-registration of the same research content.

---

## Graph Integration

Every ingested object becomes a graph node using the canonical IKROS node type
mapping.

The engine creates edges from:

- `source_ids` and `dependency_ids` → `DEPENDS_ON`
- explicit `relationships` entries
- automatic mappings such as:
  - `Hypothesis.source_rq` → `DEPENDS_ON`
  - `Hypothesis.validations` → `VALIDATED_BY`
  - `Experiment.hypotheses` → `TESTED_IN`
  - `Experiment.dataset_versions` → `USES_DATASET`
  - `Feature` dataset lineage → `DERIVED_FROM`
  - `AlphaCandidate.implements_hypotheses` → `IMPLEMENTS`
  - `ContradictoryEvidence.contradicts` → `CONTRADICTED_BY`

Existing registry entities referenced by new ingestion objects are materialized
into the graph on demand when required for referential integrity.

---

## Memory Integration

Every ingested object is also stored in Institutional Research Memory using a
deterministic tier policy:

| Object / Condition | Default Tier |
|--------------------|--------------|
| `Evidence`, `Validation`, `Experiment`, `MarketEvent` | `T1_EPISODIC` |
| `ResearchConclusion`, `EconomicThesis`, `Alpha`, `AlphaCandidate` | `T4_INSTITUTIONAL` |
| `KnowledgeObject` from specifications or ADRs | `T3_PROCEDURAL` |
| archived objects | `T5_ARCHIVE` |
| all other supported objects | `T2_SEMANTIC` |

The resulting memory records remain queryable through the existing query engine.

---

## Query Engine Integration

The ingestion engine exposes a `build_query_engine()` helper over the active:

- registries
- Knowledge Graph
- Research Memory store

This allows immediate deterministic queries over newly ingested objects without
modifying the query subsystem.

Example:

```python
from pathlib import Path

from tools.ikros import ResearchIngestionEngine

engine = ResearchIngestionEngine(base_dir=Path("data/ikros"))
result = engine.ingest_path(Path("reports/research-report.json"))

query = engine.build_query_engine()
response = query.execute(f"GET ENTITY {result.report.object_ids[0]}")
```

---

## Ingestion Reports

Every successful ingestion writes a deterministic YAML report under:

```text
data/ikros/ingestion/reports/
```

Each report records:

- ingestion ID
- source reference
- source kind
- source format
- source hash
- source version
- ingestion status
- ingested object IDs
- generated memory IDs
- generated graph node IDs
- object fingerprints

Canonical report IDs follow:

```text
IKING-YYYYMMDD-####
```

---

## Limitations

- The engine does not infer domain objects from unstructured prose.
- Structured extraction requires explicit object blocks or known structured
  source schemas.
- Only the existing five implemented registries are used for registry-backed
  entity creation.
- Non-registry object types are preserved through graph and memory, not through
  dedicated registries.
- No semantic duplicate detection is used; duplicate detection is deterministic
  and structure-based only.

---

## Future Extensions

Future ARB-approved work may add:

- dedicated registries for datasets, validation, literature, decisions, and
  knowledge objects
- richer source loaders for institutional publications
- stricter source-specific schemas
- queued or asynchronous ingestion orchestration
- downstream institutional analytics over ingestion reports

These can be added without changing the current deterministic core contract.
