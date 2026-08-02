# IKROS Research Confidence & Evidence Engine Guide

**Version:** 1.0.0  
**Specification:** SPEC-060 IKROS Architecture  
**Work Package:** WP-IMP-0047

---

## Overview

The IKROS Institutional Research Confidence & Evidence Engine quantifies research
confidence deterministically from structured evidence already stored in IKROS.

The subsystem is intentionally bounded:

- no LLMs
- no semantic search or embeddings
- no autonomous reasoning
- no hypothesis generation
- no alpha discovery
- no Runtime or Engineering OS changes

It evaluates confidence; it does not invent knowledge.

---

## Package Layout

| File | Responsibility |
|------|----------------|
| `tools/ikros/confidence/models.py` | Confidence dimensions, evidence references, quality indicators, assessments, history, and audit models |
| `tools/ikros/confidence/persistence.py` | YAML-backed assessment, history, and audit persistence |
| `tools/ikros/confidence/validation.py` | Evidence, confidence, assessment, history, and audit validation |
| `tools/ikros/confidence/engine.py` | Deterministic scoring, evidence aggregation, contradiction handling, propagation, history emission, audit logging, and registry/graph/memory synchronization |
| `tests/unit/test_ikros_confidence.py` | Scoring, propagation, contradiction, replication, history, audit, and query-visible memory coverage |

---

## Confidence Dimensions

The engine tracks these dimensions independently:

| Dimension | Meaning |
|-----------|---------|
| `prior` | Institutional prior before new evidence |
| `statistical` | Strength of statistical evidence |
| `economic` | Mechanistic plausibility |
| `data` | Dataset quality and coverage |
| `experimental` | Reproducibility and design quality |
| `validation` | OOS and validation quality |
| `replication` | Independent confirmation strength |
| `operational` | Operational robustness evidence |
| `overall` | Weighted geometric summary with weakest-link ceiling |

For compatibility with the existing IKROS entity schema, the new
`experimental` dimension is synchronized into the legacy `ConfidenceVector.model`
slot when registry-backed entities are updated.

---

## Evidence Model

Every confidence update consumes explicit structured evidence items.

Each evidence item records:

- evidence identifier
- evidence type
- support or contradiction relation
- structured references
- confidence weight
- optional contradiction severity
- independence source
- temporal bucket
- deterministic metrics payload

Structured references support:

- specification
- experiment
- dataset
- feature
- validation
- evidence record
- work package
- capability
- research report
- backtest
- walk-forward study
- Monte Carlo study
- stress test

No natural-language extraction is performed by the confidence engine.

---

## Deterministic Scoring Rules

The engine applies deterministic rules derived from `SPEC-060` and
`02-architecture/ikros/IKROS-CONFIDENCE.md`.

### Evidence weighting

Each evidence type carries a fixed base weight, then applies:

1. explicit `confidence_weight`
2. a freshness multiplier
3. support or contradiction handling

### Dimension extraction

The engine reads explicit dimension fields when present, then derives values
from recognized metrics such as:

- `p_value`
- `economic_score`
- `data_quality_grade`
- `reproducibility_score`
- `design_score`
- `consistency_score`
- `sharpe_degradation`
- `paper_trading_score`
- `stress_pass_rate`

### Replication confidence

Replication strength is computed from independent evidence sources:

```text
C_rep = 1 - exp(-replication_count / 3)
```

### Contradiction handling

Contradictory evidence applies deterministic multipliers:

| Severity | Multiplier |
|----------|------------|
| `MINOR` | `0.95` |
| `MODERATE` | `0.80` |
| `MAJOR` | `0.60` |
| `INVALIDATING` | `0.10` |

The engine preserves contradictory knowledge and emits review guidance instead
of deleting records.

### Temporal decay

Freshness is handled in two ways:

1. evidence-level freshness weighting
2. entity-type temporal decay on the aggregated confidence result

---

## Research Quality Indicators

Each assessment emits deterministic quality indicators:

- independent validation count
- out-of-sample confirmation count
- regime diversity
- dataset diversity
- temporal diversity
- replication count
- contradiction count
- evidence freshness
- research maturity
- validation completeness
- overall quality score

These indicators are preserved with the assessment, history entry, graph
attributes, and episodic memory record.

---

## Propagation Rules

The engine propagates assessed confidence downstream through lineage edges in
the Knowledge Graph.

Supported propagation behavior:

- deterministic breadth-first traversal
- edge-confidence-aware damping
- per-dimension blending into downstream nodes
- registry-backed entity synchronization where a registry exists
- graph-only node synchronization through node attributes and graph confidence

Propagation records are preserved in the assessment so downstream changes remain
traceable.

---

## History and Audit

Every assessment produces:

1. a persisted confidence assessment
2. an append-only history entry for the target object
3. a hash-chained audit entry
4. an episodic memory record

Audit entries include:

- timestamp
- reason
- supporting evidence
- previous confidence
- new confidence
- operator
- specification references
- propagated targets
- previous hash
- entry hash

---

## Integration Surfaces

The subsystem integrates with:

- **Registries** by updating registry-backed entity confidence vectors
- **Knowledge Graph** by updating node confidence and attaching structured
  confidence assessment metadata
- **Research Memory** by storing confidence assessments as episodic memory
  records
- **Institutional Query Engine** through `build_query_engine()` over the updated
  registry, graph, and memory state
- **Research Ingestion** by consuming structured evidence references produced by
  ingested institutional artifacts
- **Evidence System** by referencing `EXEC-*` evidence records directly in
  assessments

---

## Example

```python
from pathlib import Path

from tools.ikros import (
    ConfidenceEvidence,
    ConfidenceEvidenceType,
    EvidenceReferences,
    EvidenceRelation,
    ResearchConfidenceEngine,
)

engine = ResearchConfidenceEngine(base_dir=Path("data") / "ikros")

assessment = engine.assess(
    "IKROS-HYP-20260802-0001",
    [
        ConfidenceEvidence(
            evidence_id="EVID-VAL-001",
            evidence_type=ConfidenceEvidenceType.VALIDATION,
            relation=EvidenceRelation.SUPPORTS,
            references=EvidenceReferences(
                specification_ids=["SPEC-060"],
                validation_ids=["IKROS-VAL-20260802-0001"],
                evidence_record_ids=["EXEC-049"],
                work_package_ids=["WP-IMP-0047"],
                capability_ids=["IKROS-CONFIDENCE"],
            ),
            metrics={
                "p_value": 0.03,
                "consistency_score": 0.82,
                "sharpe_degradation": 0.10,
                "verdict": "PASS",
            },
        ),
    ],
    reason="Validated walk-forward confirmation",
)
```

---

## Limitations

- The engine does not perform semantic duplicate detection.
- Confidence inputs must already be structured.
- Graph-only nodes retain full confidence metadata in graph attributes, but only
  registry-backed entities synchronize into typed registry models.
- The current query engine exposes the generated episodic confidence records
  through memory queries; it does not add a new query grammar for confidence
  assessments.
- Future dataset, validation, knowledge, and failure registries can deepen the
  evidence model without changing the current deterministic engine contract.
