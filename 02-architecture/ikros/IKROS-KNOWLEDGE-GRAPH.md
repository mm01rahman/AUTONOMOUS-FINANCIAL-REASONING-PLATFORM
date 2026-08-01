# IKROS Knowledge Graph Design

**Document ID:** AFRP-IKROS-GRAPH-1.0.0
**Specification Authority:** SPEC-060 §4 — Knowledge Graph
**Work Package:** WP-IMP-0041
**Version:** 1.0.0
**Status:** Draft — Awaiting ARB Approval

---

## 1. Graph Model

IKROS uses a **Labelled Property Graph (LPG)** model with temporal validity on all edges.

### 1.1 Design Rationale

The LPG model is chosen over RDF/OWL because:
- Native support for property-rich edges (confidence, timestamps, provenance)
- Natural expression of temporal intervals on relationships
- Efficient traversal of multi-hop lineage chains
- Flexible schema evolution without ontology recompilation
- Direct mapping to Python dataclass representations

See **ADR-IKROS-001** for full selection rationale.

### 1.2 Graph Schema Version

Schema version: `IKROS-GRAPH-SCHEMA-1.0.0`

---

## 2. Node Types

Every node corresponds to one IKROS ontology entity. Nodes carry:
- `ikros_id` (unique identifier, partition key)
- `entity_type` (ontology class name)
- `lifecycle_state` (current state machine state)
- `confidence_score` (current confidence, 0.0–1.0)
- `created_at` (ISO8601)
- `version` (SemVer for versioned entities)
- All entity-specific attributes from the ontology

### 2.1 Node Type Registry

| Node Label | Entity | Key Property |
|-----------|--------|-------------|
| `ResearchQuestion` | ResearchQuestion | `title` |
| `EconomicThesis` | EconomicThesis | `title` |
| `Literature` | Literature | `doi_or_url` |
| `Dataset` | Dataset | `name`, `instrument` |
| `DatasetVersion` | DatasetVersion | `hash_sha256` |
| `Feature` | Feature | `name`, `version` |
| `FeatureFamily` | FeatureFamily | `name` |
| `Factor` | Factor | `name` |
| `Hypothesis` | Hypothesis | `statement` |
| `Experiment` | Experiment | `title`, `reproducibility_hash` |
| `Validation` | Validation | `experiment_id`, `method` |
| `Model` | Model | `architecture`, `training_hash` |
| `WorldModel` | WorldModel | `valid_from` |
| `Decision` | Decision | `timestamp` |
| `Policy` | Policy | `policy_type` |
| `Backtest` | Backtest | `strategy_id`, `start_date` |
| `WalkForward` | WalkForward | `parent_experiment` |
| `StressTest` | StressTest | `scenario` |
| `MonteCarlo` | MonteCarlo | `simulation_count` |
| `Regime` | Regime | `name` |
| `MarketEvent` | MarketEvent | `name`, `date` |
| `AlphaCandidate` | AlphaCandidate | `name` |
| `Alpha` | Alpha | `promoted_from` |
| `Failure` | Failure | `failed_object_id`, `failure_type` |
| `ContradictoryEvidence` | ContradictoryEvidence | `contradicts` |
| `ResearchConclusion` | ResearchConclusion | `statement` |
| `KnowledgeObject` | KnowledgeObject | `title`, `category` |

---

## 3. Relationship Types

### 3.1 Edge Schema

Every edge carries:
| Property | Type | Description |
|----------|------|-------------|
| `edge_type` | String | Relationship type label |
| `valid_from` | ISO8601 | When this relationship became true |
| `valid_to` | ISO8601 \| null | When this relationship ceased (null = current) |
| `confidence` | Float[0,1] | Confidence in this relationship |
| `created_by` | String | Agent or analyst that asserted this edge |
| `evidence_ref` | IKROS-ID \| null | Supporting evidence for this edge |

### 3.2 Relationship Type Catalogue

| Relationship | From | To | Cardinality | Description |
|-------------|------|-----|------------|-------------|
| `MOTIVATED_BY` | ResearchQuestion | MarketEvent | N:1 | What observation triggered research |
| `INFORMED_BY` | ResearchQuestion | Literature | N:M | Prior literature |
| `DECOMPOSED_INTO` | ResearchQuestion | ResearchQuestion | N:M | Sub-questions |
| `ANSWERED_BY` | ResearchQuestion | ResearchConclusion | N:1 | Final answer |
| `GENERATED` | ResearchQuestion | Hypothesis | 1:N | Derived hypotheses |
| `SUPPORTS` | EconomicThesis | Hypothesis | 1:N | Theoretical support |
| `CONTRADICTED_BY` | EconomicThesis | ContradictoryEvidence | 1:N | Contradictions |
| `APPLIES_IN` | EconomicThesis | Regime | N:M | Regime applicability |
| `CITED_BY` | Literature | Hypothesis | N:M | Citation |
| `CONTRADICTS_LIT` | Literature | Literature | N:M | Conflicting findings |
| `HAS_VERSION` | Dataset | DatasetVersion | 1:N | Version chain |
| `DERIVED_FROM` | Dataset | Dataset | N:1 | Data lineage |
| `USED_IN` | Dataset | Experiment | N:M | Data usage |
| `SUPERSEDES_DSV` | DatasetVersion | DatasetVersion | 1:1 | Version chain |
| `MEMBER_OF` | Feature | FeatureFamily | N:1 | Family membership |
| `COMPUTED_FROM` | Feature | Dataset | N:M | Input data |
| `COMPUTED_FROM_FEAT` | Feature | Feature | N:M | Derived feature |
| `SUPERSEDED_BY_FEAT` | Feature | Feature | 1:1 | Feature evolution |
| `CONTAINS` | FeatureFamily | Feature | 1:N | Family contents |
| `ALIGNED_WITH` | FeatureFamily | EconomicThesis | N:M | Theoretical alignment |
| `IMPLEMENTED_BY` | Factor | Feature | 1:N | Factor proxies |
| `SUPPORTED_BY_FAC` | Factor | Literature | N:M | Factor evidence |
| `CAPTURED_IN` | Factor | Alpha | N:M | Alpha implementations |
| `GENERATED_FROM` | Hypothesis | ResearchQuestion | N:1 | Hypothesis origin |
| `MOTIVATED_BY_HYP` | Hypothesis | EconomicThesis | N:M | Theoretical basis |
| `TESTED_BY` | Hypothesis | Experiment | 1:N | Testing lineage |
| `SUPPORTED_BY_HYP` | Hypothesis | Validation | N:M | Evidence support |
| `CONTRADICTED_BY_HYP` | Hypothesis | ContradictoryEvidence | N:M | Counter-evidence |
| `REFINED_INTO` | Hypothesis | Hypothesis | 1:1 | Hypothesis evolution |
| `TESTS` | Experiment | Hypothesis | 1:N | What is being tested |
| `USES_DSV` | Experiment | DatasetVersion | N:M | Data used |
| `USES_FEAT` | Experiment | Feature | N:M | Features used |
| `PRODUCES_VAL` | Experiment | Validation | 1:N | Results |
| `PRODUCES_FAIL` | Experiment | Failure | 1:N | Failures |
| `VALIDATES` | Validation | Hypothesis | N:M | What is validated |
| `VALIDATES_MODEL` | Validation | Model | N:M | Model validation |
| `VALIDATES_ALPHA` | Validation | Alpha | N:M | Alpha validation |
| `PRODUCED_BY_VAL` | Validation | Experiment | N:1 | Producing experiment |
| `TRAINED_ON` | Model | DatasetVersion | N:1 | Training data |
| `USES_MODEL_FEAT` | Model | Feature | N:M | Feature inputs |
| `VALIDATED_BY_MODEL` | Model | Validation | 1:N | Model validation |
| `INCORPORATED_IN` | Model | Alpha | N:M | Alpha usage |
| `INCORPORATED_WM` | Model | WorldModel | N:M | World model usage |
| `SUPERSEDED_BY_MODEL` | Model | Model | 1:1 | Model evolution |
| `INFORMS` | WorldModel | Decision | 1:N | Decision basis |
| `INFORMS_POL` | WorldModel | Policy | N:M | Policy basis |
| `INCORPORATES_MODEL` | WorldModel | Model | 1:N | Models used |
| `CONDITIONED_ON` | WorldModel | Regime | N:M | Regime conditioning |
| `PRODUCED_BY_DEC` | Decision | Policy | N:1 | Governing policy |
| `INFORMED_BY_DEC` | Decision | WorldModel | N:1 | World model used |
| `GOVERNED_BY` | Decision | Policy | N:1 | Policy governing |
| `CONTRIBUTES_TO` | Decision | Alpha | N:1 | Alpha track record |
| `GOVERNS` | Policy | Decision | 1:N | Decisions governed |
| `IMPLEMENTS_ALPHA` | Policy | Alpha | N:1 | Alpha implemented |
| `EVALUATED_IN_BT` | AlphaCandidate | Backtest | 1:N | Backtest evaluations |
| `EVALUATED_IN_WF` | AlphaCandidate | WalkForward | 1:N | WF evaluations |
| `EVALUATED_IN_MC` | AlphaCandidate | MonteCarlo | 1:N | MC evaluations |
| `IMPLEMENTS_HYP` | AlphaCandidate | Hypothesis | N:M | Hypothesis implemented |
| `PROMOTED_TO` | AlphaCandidate | Alpha | 1:1 | Promotion |
| `PROMOTED_FROM` | Alpha | AlphaCandidate | 1:1 | Promotion source |
| `TRACKED_IN_BT` | Alpha | Backtest | 1:N | Backtests |
| `IMPLEMENTED_BY_ALPHA` | Alpha | Policy | 1:N | Policy implementations |
| `RECORDS_FAILURE_OF` | Failure | Experiment | N:1 | What failed |
| `GENERATES_KO` | Failure | KnowledgeObject | 1:N | Lessons extracted |
| `MOTIVATES_NEW_RQ` | Failure | ResearchQuestion | N:M | Follow-up research |
| `CONTRADICTS_OBJ` | ContradictoryEvidence | Hypothesis | N:M | Contradiction target |
| `CONTRADICTS_THESIS` | ContradictoryEvidence | EconomicThesis | N:M | Thesis contradiction |
| `RESOLVED_BY` | ContradictoryEvidence | Validation | N:M | Resolution evidence |
| `GENERATED_BY_CONTRA` | ContradictoryEvidence | Experiment | N:1 | Producing experiment |
| `ANSWERS` | ResearchConclusion | ResearchQuestion | N:1 | Question answered |
| `GENERATED_FROM_CONCL` | ResearchConclusion | Experiment | N:M | Source experiments |
| `SUPERSEDED_BY_CONCL` | ResearchConclusion | ResearchConclusion | 1:1 | Conclusion evolution |
| `EXTRACTED_FROM` | KnowledgeObject | ResearchConclusion | N:M | Extraction source |
| `EXTRACTED_FROM_FAIL` | KnowledgeObject | Failure | N:M | Failure lessons |
| `APPLIED_IN` | KnowledgeObject | Experiment | N:M | Applied instances |
| `TRIGGERED_REGIME` | MarketEvent | Regime | N:M | Regime transitions |
| `MOTIVATES_RQ` | MarketEvent | ResearchQuestion | N:M | Research motivation |
| `DETECTED_BY` | Regime | Feature | N:M | Detection features |
| `AFFECTS_ALPHA` | Regime | AlphaCandidate | N:M | Performance impact |

---

## 4. Graph Constraints

### 4.1 Uniqueness Constraints

```
CONSTRAINT ikros_id_unique ON (n) ASSERT n.ikros_id IS UNIQUE
CONSTRAINT dataset_version_hash ON (n:DatasetVersion) ASSERT n.hash_sha256 IS UNIQUE
CONSTRAINT experiment_reproducibility ON (n:Experiment) ASSERT n.reproducibility_hash IS UNIQUE
```

### 4.2 Mandatory Properties

All nodes MUST have:
- `ikros_id` (not null, matches canonical pattern)
- `entity_type` (not null, matches ontology class)
- `lifecycle_state` (not null, valid state for entity type)
- `created_at` (not null, valid ISO8601)

### 4.3 Immutability Constraints

- `Failure` nodes: once created, `entity_type`, `failed_object_id`, `failure_type`, `failure_description` are immutable
- `DatasetVersion` nodes: `hash_sha256` is immutable after creation
- `Experiment` nodes: `reproducibility_hash` is immutable after `COMPLETE` state

### 4.4 Referential Integrity

- Every `PROMOTED_TO` edge MUST have a corresponding `PROMOTED_FROM` edge
- Every `VALIDATED_BY_MODEL` edge target MUST have `lifecycle_state = ACTIVE`
- Every `ANSWERS` edge MUST point to a `ResearchConclusion` with `approval_status = APPROVED`

---

## 5. Temporal Model

### 5.1 Valid Time vs. Transaction Time

IKROS uses **Bitemporal Modelling**:

| Time Dimension | Property | Description |
|---------------|----------|-------------|
| Valid Time | `edge.valid_from`, `edge.valid_to` | When the relationship was true in the world |
| Transaction Time | `edge.asserted_at`, `edge.retracted_at` | When IKROS recorded this assertion |

### 5.2 Temporal Query Types

```
# Current state query (valid now, asserted now)
MATCH (h:Hypothesis {ikros_id: 'IKROS-HYP-20260101-0001'})
-[r:SUPPORTED_BY_HYP {valid_to: null}]->(v:Validation)
RETURN h, r, v

# Point-in-time query (what did we believe on 2026-01-01?)
MATCH (h:Hypothesis)-[r:SUPPORTED_BY_HYP]->(v:Validation)
WHERE r.valid_from <= '2026-01-01' AND (r.valid_to IS NULL OR r.valid_to > '2026-01-01')
RETURN h, r, v

# Full history query (all versions, all times)
MATCH (h:Hypothesis)-[r:SUPPORTED_BY_HYP]->(v:Validation)
WHERE h.ikros_id = 'IKROS-HYP-20260101-0001'
RETURN h, r, v ORDER BY r.valid_from
```

### 5.3 Temporal Integrity Rules

1. `valid_from` MUST be <= `valid_to` (when `valid_to` is not null)
2. For a given edge type between two nodes, valid intervals MUST NOT overlap
3. When a relationship is superseded, the old edge `valid_to` MUST equal the new edge `valid_from`
4. `Failure` edges are permanent: `valid_to` is always null

---

## 6. Confidence Propagation on the Graph

### 6.1 Propagation Rules

Confidence propagates from evidence to conclusions via weighted product:

```
confidence(conclusion) = min(
    Π(confidence(evidence_i)^weight_i),
    confidence_ceiling(conclusion_type)
)
```

Where:
- `weight_i` = normalized weight of each evidence edge
- `confidence_ceiling` = maximum confidence allowed for each entity type

### 6.2 Confidence Ceilings

| Entity Type | Max Confidence | Rationale |
|------------|---------------|-----------|
| `Hypothesis` | 0.95 | Cannot be fully proven |
| `Alpha` | 0.90 | Market regime uncertainty |
| `EconomicThesis` | 0.85 | Structural uncertainty |
| `ResearchConclusion` | 0.90 | Research limitations |
| `KnowledgeObject` | 0.95 | Distilled from multiple sources |

### 6.3 Confidence Degradation

Confidence degrades over time for time-sensitive objects:

```
confidence_t = confidence_0 × exp(-λ × age_in_days)
```

Where `λ` (decay rate) is set per entity type:
- `AlphaCandidate`: λ = 0.001 (daily decay of ~0.1%)
- `EconomicThesis`: λ = 0.0001 (slow decay)
- `KnowledgeObject`: λ = 0.00005 (very slow decay)
- `Failure`: λ = 0 (permanent, no decay)

---

## 7. Contradiction Handling

### 7.1 Contradiction Detection

IKROS automatically checks for contradictions when:
1. A new `Validation` with `verdict = FAIL` is linked to an existing supported `Hypothesis`
2. A new `Experiment` produces results inconsistent with registered `ResearchConclusion`
3. Two `EconomicThesis` nodes contain mutually exclusive predictions for the same regime

### 7.2 Contradiction Severity Classification

| Severity | Condition | Required Action |
|----------|-----------|----------------|
| `MINOR` | Effect size < 0.1, p > 0.05 | Log and monitor |
| `MODERATE` | Effect size 0.1–0.3 or p 0.01–0.05 | Flag for review within 30 days |
| `MAJOR` | Effect size > 0.3 or p < 0.01 | Mandatory ARB review within 7 days |
| `INVALIDATING` | Original finding completely reversed | Immediate ARB review; freeze affected objects |

### 7.3 Contradiction Resolution Process

1. `ContradictoryEvidence` node created
2. `CONTRADICTS_OBJ` edge added with `valid_from = now()`
3. Affected object `lifecycle_state` set to `CONTESTED`
4. ARB review scheduled per severity
5. Resolution options:
   - **Accept contradiction:** Update affected object confidence, add resolution notes
   - **Reject contradiction:** Record evidence quality concerns, maintain original
   - **Refine scope:** Narrow conditions under which original conclusion holds
6. Resolution recorded in `ContradictoryEvidence.resolution_notes`

---

## 8. Lineage Traversal

### 8.1 Full Research Lineage Query

Given an Alpha, trace full lineage back to originating ResearchQuestion:

```cypher
MATCH path = (alpha:Alpha)
    <-[:PROMOTED_TO]-(cand:AlphaCandidate)
    <-[:IMPLEMENTS_HYP]-(hyp:Hypothesis)
    <-[:GENERATED]-(rq:ResearchQuestion)
RETURN path
```

### 8.2 Data Lineage Query

Given a Model, trace all data it was trained on:

```cypher
MATCH path = (m:Model)
    -[:TRAINED_ON]->(dsv:DatasetVersion)
    -[:VERSION_OF]->(ds:Dataset)
    -[:DERIVED_FROM*0..3]->(source_ds:Dataset)
RETURN path
```

### 8.3 Evidence Chain Query

Given a Hypothesis, find all supporting and contradicting evidence:

```cypher
MATCH (h:Hypothesis {ikros_id: $hyp_id})
OPTIONAL MATCH (h)-[:SUPPORTED_BY_HYP]->(val:Validation)
OPTIONAL MATCH (h)<-[:CONTRADICTS_OBJ]-(contra:ContradictoryEvidence)
RETURN h, collect(val) as support, collect(contra) as contradictions
```

---

## 9. Graph Storage Architecture

### 9.1 Phase 1 (Architecture Phase — No Implementation)

The graph is defined as a YAML-serialisable schema. Implementation will use:

**Option A (Recommended):** NetworkX in-memory graph with YAML persistence
- Lightweight, no external database dependency
- Full LPG semantics via node/edge attribute dicts
- Temporal validity via edge properties
- Cypher-like traversal via custom query engine

**Option B (Future):** Neo4j or Kuzu graph database
- Full Cypher query language
- Native temporal support
- ACID transactions
- Recommended when node count exceeds 100,000

See **ADR-IKROS-001** for selection rationale and migration path.

### 9.2 File Layout (Phase 1)

```
data/ikros/
├── graph/
│   ├── nodes/
│   │   ├── research_questions.yaml
│   │   ├── hypotheses.yaml
│   │   ├── experiments.yaml
│   │   └── ...
│   └── edges/
│       ├── tested_by.yaml
│       ├── supported_by.yaml
│       └── ...
├── snapshots/
│   └── IKROS-SNAPSHOT-{DATE}.yaml
└── GRAPH_MANIFEST.yaml
```

---

## 10. Traceability

| Specification Section | Implemented By |
|----------------------|----------------|
| SPEC-060 §4 Graph Model | This document |
| SPEC-060 §4.1 Node types | §2 Node Types |
| SPEC-060 §4.2 Relationship types | §3 Relationship Types |
| SPEC-060 §4.3 Constraints | §4 Graph Constraints |
| SPEC-060 §4.4 Temporal | §5 Temporal Model |
| SPEC-060 §4.5 Confidence | §6 Confidence Propagation |
| SPEC-060 §4.6 Contradictions | §7 Contradiction Handling |
