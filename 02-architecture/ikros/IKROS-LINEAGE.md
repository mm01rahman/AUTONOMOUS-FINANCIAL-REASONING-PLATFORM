# IKROS Lineage Model

**Document ID:** AFRP-IKROS-LINEAGE-1.0.0
**Specification Authority:** SPEC-060 §7 — Lineage Model
**Work Package:** WP-IMP-0041
**Version:** 1.0.0
**Status:** Draft — Awaiting ARB Approval

---

## 1. Overview

The IKROS Lineage Model records **complete provenance** for every knowledge object. No IKROS object may exist without answering: *where did it come from, what does it depend on, what validated it, and what came after it?*

Lineage is enforced by the `LineageRecorder` component, which verifies lineage completeness before any object can advance to `APPROVED` lifecycle state.

---

## 2. Lineage Record Structure

Every IKROS entity carries an embedded `lineage` block:

```yaml
lineage:
  origin:
    created_by: str              # Agent ID or analyst
    created_at: ISO8601
    creation_context: str        # Session ID, WP, or experiment
    motivation: str              # Why this was created
  dependencies:
    inputs: list[IKROS-ID]       # Direct predecessors
    datasets: list[IKROS-ID]     # DatasetVersion IDs
    features: list[IKROS-ID]     # Feature IDs
    models: list[IKROS-ID]       # Model IDs
    external_refs: list[str]     # External literature, URLs
  experiments:
    tested_in: list[IKROS-ID]    # Experiment IDs
    validated_by: list[IKROS-ID] # Validation IDs
  evidence:
    supporting: list[IKROS-ID]   # Supporting evidence IDs
    contradicting: list[IKROS-ID] # Contradicting evidence IDs
    ers_records: list[str]       # ERS-1.0 EXEC-*.yaml paths
  successors:
    refined_by: IKROS-ID | null  # Refined version (if any)
    superseded_by: IKROS-ID | null  # Superseder
    inspired: list[IKROS-ID]    # Objects this inspired
  retirement:
    retired_at: ISO8601 | null
    retired_by: str | null
    retirement_reason: str | null
    successor_id: IKROS-ID | null
```

---

## 3. Lineage by Entity Type

### 3.1 Hypothesis Lineage

```
ResearchQuestion (origin)
    ↓ GENERATED
Hypothesis
    ↓ MOTIVATED_BY
EconomicThesis (optional theoretical basis)
    ↓ TESTED_BY
Experiment(s)
    ↓ PRODUCES
Validation(s)
    ↓ SUPPORTED_BY / CONTRADICTED_BY
Hypothesis (updated posterior_confidence)
    ↓ [if REFUTED or RETIRED]
Failure (permanent record)
    ↓ [if SUPPORTED and PROMOTED]
AlphaCandidate → Alpha
```

**Required lineage fields for Hypothesis:**
- `origin.motivation` (non-empty)
- `dependencies.inputs` contains parent ResearchQuestion ID
- `experiments.tested_in` (at least one once `TESTING` state reached)
- `experiments.validated_by` (at least one once `SUPPORTED`/`REFUTED`)

### 3.2 Experiment Lineage

```
Hypothesis (what is being tested)
    ↓
Experiment
    ├── USES_DSV → DatasetVersion(s)
    ├── USES_FEAT → Feature(s)
    ├── reproducibility_hash (SHA256 of all inputs)
    ↓
Validation(s) | Failure(s)
```

**Required lineage fields for Experiment:**
- `dependencies.datasets` (at least one DatasetVersion)
- `dependencies.features` (at least one Feature)
- `reproducibility_hash` (computed from all inputs before execution)
- `lineage.origin.creation_context` (WP or session ID)

### 3.3 Model Lineage

```
DatasetVersion (training data)
    ↓ TRAINED_ON
Model
    ├── USES_MODEL_FEAT → Features used
    ├── training_hash (SHA256 of training run)
    ↓ VALIDATED_BY_MODEL
Validation(s)
    ↓ [if APPROVED]
INCORPORATED_IN → Alpha / WorldModel
    ↓ [if SUPERSEDED]
SUPERSEDED_BY_MODEL → newer Model
```

### 3.4 Alpha Lineage

```
Hypothesis (implemented by strategy)
    ↓ IMPLEMENTS_HYP
AlphaCandidate
    ├── EVALUATED_IN_BT → Backtest(s)
    ├── EVALUATED_IN_WF → WalkForward(s)
    ├── EVALUATED_IN_MC → MonteCarlo(s)
    ↓
PROMOTED_TO → Alpha  [OR]  REJECTED → Failure
```

**For a promoted Alpha, complete lineage must trace back to:**
- ResearchQuestion (root motivation)
- DatasetVersion(s) (data used)
- Feature(s) (signal inputs)
- Hypothesis (testable prediction)
- Validation(s) (evidence of performance)
- ERS evidence records

### 3.5 Failure Lineage

Failures have **simplified but permanent** lineage:

```yaml
lineage:
  origin:
    created_by: str
    created_at: ISO8601         # IMMUTABLE
    creation_context: str       # IMMUTABLE
    motivation: str             # "Records failure of {object_id}"
  dependencies:
    inputs: [<failed_object_id>]
  experiments:
    tested_in: [<experiment_id>]
  evidence:
    ers_records: [<evidence_path>]
  # No successors section — failures do not retire
```

### 3.6 KnowledgeObject Lineage

```
Failure(s) | ResearchConclusion(s) | Validation(s)
    ↓ EXTRACTED_FROM | EXTRACTED_FROM_FAIL
KnowledgeObject
    ↓ APPLIED_IN
Future Experiment(s)
```

---

## 4. Lineage Completeness Rules

The `LineageRecorder` enforces these rules before state transitions:

| Rule ID | Rule | Applies To | Enforcement |
|---------|------|-----------|-------------|
| LIN-001 | `origin.created_by` must be non-empty | All entities | At creation |
| LIN-002 | `origin.created_at` must be valid ISO8601 | All entities | At creation |
| LIN-003 | `dependencies.inputs` must have ≥ 1 entry | Hypothesis, Experiment, Model, Feature | Before `APPROVED` |
| LIN-004 | `experiments.tested_in` must have ≥ 1 entry | Hypothesis | Before `SUPPORTED`/`REFUTED` |
| LIN-005 | `experiments.validated_by` must have ≥ 1 entry | AlphaCandidate, Model | Before `APPROVED`/`PROMOTED` |
| LIN-006 | `evidence.ers_records` must have ≥ 1 entry | Alpha (promoted) | Before promotion |
| LIN-007 | `retirement.retirement_reason` must be non-empty | Any entity | Before `RETIRED` state |
| LIN-008 | Failure `origin.*` fields must be immutable | Failure | Always |
| LIN-009 | `reproducibility_hash` must be set | Experiment | Before `COMPLETE` |
| LIN-010 | `training_hash` must be set | Model | Before `TRAINED` → `VALIDATED` |

---

## 5. Lineage Queries

### 5.1 Full Provenance Chain

```python
# IKROS lineage query — returns all ancestors of a given object
def get_full_lineage(ikros_id: str) -> LineageChain:
    """
    Traverse the knowledge graph backwards from the given object.
    Returns a tree of all predecessor objects.
    """
    ...
```

### 5.2 Impact Analysis (Forward Lineage)

```python
# What does this object affect downstream?
def get_impact(ikros_id: str) -> ImpactTree:
    """
    Traverse the knowledge graph forwards from the given object.
    Returns all objects that depend on or cite this object.
    Useful for: "If I retire this dataset, what breaks?"
    """
    ...
```

### 5.3 Evidence Chain

```python
# What evidence supports/contradicts this object?
def get_evidence_chain(ikros_id: str) -> EvidenceChain:
    """
    Returns all Validation, Failure, and ContradictoryEvidence
    objects linked to the given entity.
    """
    ...
```

### 5.4 Orphan Detection

```python
# Find objects with incomplete lineage (should never exist in production)
def find_orphans() -> List[str]:
    """
    Returns ikros_ids of objects that violate lineage completeness rules.
    Used by governance health checks.
    """
    ...
```

---

## 6. Lineage Visualisation

IKROS generates lineage diagrams in Mermaid format for any object:

**Example: Alpha Candidate Lineage**
```mermaid
graph TB
    RQ[ResearchQuestion<br/>IKROS-RQ-*] --> HYP[Hypothesis<br/>IKROS-HYP-*]
    THESIS[EconomicThesis<br/>IKROS-THESIS-*] --> HYP
    DS[Dataset<br/>IKROS-DS-*] --> DSV[DatasetVersion<br/>IKROS-DSV-*]
    DSV --> EXP[Experiment<br/>IKROS-EXP-*]
    FEAT[Feature(s)<br/>IKROS-FEAT-*] --> EXP
    HYP --> EXP
    EXP --> VAL[Validation<br/>IKROS-VAL-*]
    EXP --> BT[Backtest<br/>IKROS-BT-*]
    EXP --> WF[WalkForward<br/>IKROS-WF-*]
    EXP --> MC[MonteCarlo<br/>IKROS-MC-*]
    VAL --> CAND[AlphaCandidate<br/>IKROS-ALPHACAND-*]
    BT --> CAND
    WF --> CAND
    MC --> CAND
    CAND -->|PROMOTED| ALPHA[Alpha<br/>IKROS-ALPHA-*]
    CAND -->|REJECTED| FAIL[Failure<br/>IKROS-FAIL-*]
    FAIL -->|EXTRACTS| KO[KnowledgeObject<br/>IKROS-KO-*]
```

---

## 7. Lineage in Phase E Context

All Phase E research (WP-IMP-0039) produced the following lineage that IKROS should initialise:

| Object | Count | Lineage Status |
|--------|-------|---------------|
| ResearchQuestion | 1 | Complete (XAU/USD alpha discovery) |
| Hypothesis | 6 | Complete (one per strategy type) |
| Experiment | 6 | Complete (reproducibility_hash in phase_e_summary.json) |
| DatasetVersion | 4 | Complete (M1/H1 data, two versions each) |
| Feature | 47 | Complete (feature_importance_report.md) |
| Validation | 18 | Complete (BT + WF + MC per strategy) |
| AlphaCandidate | 6 | Complete (all REJECTED) |
| Failure | 6 | Complete (one per rejected candidate) |
| KnowledgeObject | 6 | Complete (lessons from failures) |
| ResearchConclusion | 1 | Complete (FAIL recommendation, no promotion) |

---

## 8. Traceability

| Specification Section | Implemented By |
|----------------------|----------------|
| SPEC-060 §7 Lineage | This document |
| SPEC-060 §7.1 Origin | §2 `lineage.origin` |
| SPEC-060 §7.2 Dependencies | §2 `lineage.dependencies` |
| SPEC-060 §7.3 Experiments | §2 `lineage.experiments` |
| SPEC-060 §7.4 Evidence | §2 `lineage.evidence` |
| SPEC-060 §7.5 Successors | §2 `lineage.successors` |
| SPEC-060 §7.6 Retirement | §2 `lineage.retirement` |
