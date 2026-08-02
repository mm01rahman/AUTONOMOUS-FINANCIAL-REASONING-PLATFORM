# IKROS Registry Guide

**Version:** 1.0.0
**Specification:** SPEC-060 IKROS Architecture
**Work Package:** WP-IMP-0042

---

## Overview

The IKROS Core Registries form the institutional foundation for all AFRP research
governance. Each registry manages a distinct class of research objects with full
lifecycle control, lineage provenance, confidence tracking, and YAML persistence.

---

## Registry Classes

| Class | Entity | File | ID Prefix |
|-------|--------|------|-----------|
| `ResearchRegistry` | `ResearchQuestion` | `tools/ikros/registries/research.py` | `IKROS-RQ-` |
| `HypothesisRegistry` | `Hypothesis` | `tools/ikros/registries/hypothesis.py` | `IKROS-HYP-` |
| `ExperimentRegistry` | `Experiment` | `tools/ikros/registries/experiment.py` | `IKROS-EXP-` |
| `FeatureRegistry` | `Feature` / `FeatureFamily` | `tools/ikros/registries/feature.py` | `IKROS-FEAT-` / `IKROS-FF-` |
| `AlphaRegistry` | `AlphaCandidate` / `Alpha` | `tools/ikros/registries/alpha.py` | `IKROS-ALPHACAND-` / `IKROS-ALPHA-` |

---

## Installation and Import

```python
from tools.ikros import (
    ResearchRegistry, HypothesisRegistry, ExperimentRegistry,
    FeatureRegistry, AlphaRegistry,
    ResearchQuestion, Hypothesis, Experiment, Feature, Alpha, AlphaCandidate,
    ConfidenceVector, LineageRecord,
)
```

---

## IKROS Identifier Format

Every entity has a canonical immutable identifier:

```
IKROS-{TYPE_CODE}-{YYYYMMDD}-{SEQ:04d}
```

Examples:
- `IKROS-RQ-20260802-0001` — first research question created on 2026-08-02
- `IKROS-HYP-20260802-0042` — 42nd hypothesis created on the same date
- `IKROS-ALPHACAND-20260901-0001` — first alpha candidate in September

Generate with `tools.ikros.identifiers.make_ikros_id(entity_type, date, seq)`.

---

## Creating and Registering Entities

All registries share the same CRUD interface from `BaseRegistry[T]`.

### ResearchQuestion

```python
from tools.ikros import ResearchRegistry, ResearchQuestion, ConfidenceVector, LineageRecord
from tools.ikros.models import LineageOrigin, ResearchStatus
from tools.ikros.identifiers import make_ikros_id

reg = ResearchRegistry()  # in-memory; pass base_dir=Path("data/ikros/registries") for persistence

rq = ResearchQuestion(
    ikros_id=make_ikros_id("ResearchQuestion", seq=1),
    entity_type="ResearchQuestion",
    version="1.0.0",
    lifecycle_state=ResearchStatus.OPEN,
    confidence=ConfidenceVector(statistical=0.3),
    lineage=LineageRecord(
        origin=LineageOrigin(
            created_by="researcher-agent",
            created_at="2026-08-02T00:00:00Z",
            creation_context="PHASE-F",
            motivation="Investigate momentum regime switching in XAU/USD",
        )
    ),
    title="Does XAU/USD exhibit momentum regime switching?",
    instrument="XAU/USD",
    scope="MACRO",
    time_horizon="1D",
    campaign_tag="PHASE-F",
    motivation="Phase F research campaign",
)

ikros_id = reg.register(rq)  # raises ValidationError on invalid entity
```

### Hypothesis

```python
from tools.ikros import HypothesisRegistry, Hypothesis
from tools.ikros.models import HypothesisStatus, LineageDependencies

hyp_reg = HypothesisRegistry()

hyp = Hypothesis(
    ikros_id=make_ikros_id("Hypothesis", seq=1),
    entity_type="Hypothesis",
    version="1.0.0",
    lifecycle_state=HypothesisStatus.PROPOSED,
    confidence=ConfidenceVector(statistical=0.25, economic=0.3),
    lineage=LineageRecord(
        origin=LineageOrigin(...),
        dependencies=LineageDependencies(inputs=[rq.ikros_id]),
    ),
    statement="XAU/USD returns exhibit positive autocorrelation above 0.10 in bull regimes",
    null_hypothesis="H0: No autocorrelation in XAU/USD daily returns",
    alternative_hypothesis="H1: Positive autocorrelation above 0.10 in identified regimes",
    significance_level=0.05,
    power=0.80,
    prior_confidence=0.25,
    source_rq=rq.ikros_id,
)

hyp_reg.register(hyp)
```

---

## Lifecycle Management

Every entity has a governed lifecycle. Transitions are validated against the state
machine defined in `tools/ikros/identifiers.py`.

### Lifecycle Transitions

| Entity | Valid Path |
|--------|------------|
| ResearchQuestion | `OPEN → ACTIVE → ANSWERED → RETIRED` |
| Hypothesis | `PROPOSED → UNDER_REVIEW → APPROVED_FOR_TESTING → TESTING → SUPPORTED\|REFUTED\|INCONCLUSIVE → RETIRED` |
| Experiment | `DESIGNED → APPROVED → RUNNING → COMPLETE\|FAILED → REVIEWED → ARCHIVED\|INVALIDATED` |
| Feature | `DRAFT → VALIDATED → ACTIVE → DEPRECATED → RETIRED` |
| AlphaCandidate | `CANDIDATE → PROMOTED\|REJECTED → RETIRED` |
| Alpha | `PROMOTED → RETIRED` |

```python
# Transition a hypothesis through review
hyp_reg.transition("IKROS-HYP-20260802-0001", "UNDER_REVIEW")
hyp_reg.transition("IKROS-HYP-20260802-0001", "APPROVED_FOR_TESTING")
hyp_reg.transition("IKROS-HYP-20260802-0001", "TESTING")

# After results: mark supported
hyp_reg.transition("IKROS-HYP-20260802-0001", "SUPPORTED")
```

Invalid transitions raise `tools.ikros.identifiers.LifecycleError`.

---

## Validation

All entities are validated on `register()` and `update()`. Validation checks:

- **LIN-001**: `lineage.origin.created_by` must be non-empty
- **LIN-002**: `lineage.origin.created_at` must be non-empty
- **LIN-003**: `dependencies.datasets` must be populated for APPROVED/RUNNING/COMPLETE experiments
- **LIN-004**: `experiments.tested_in` and `validated_by` must be non-empty for SUPPORTED/REFUTED hypotheses
- **LIN-006**: `lineage.evidence.ers_records` must be non-empty for PROMOTED candidates and Alphas
- **LIN-009**: `reproducibility_hash` required when experiment is COMPLETE

```python
from tools.ikros.validation import validate_entity, assert_valid, ValidationError

errors = validate_entity(entity)  # returns list of error strings
assert_valid(entity)              # raises ValidationError if errors exist
```

---

## Confidence Tracking

Every entity carries an 8-dimensional confidence vector:

```python
cv = ConfidenceVector(
    prior=0.20,        # prior belief
    statistical=0.60,  # statistical significance
    economic=0.45,     # economic intuition
    data=0.80,         # data quality
    model=0.50,        # model validity
    validation=0.70,   # out-of-sample validation
    replication=0.40,  # replication across regimes
    operational=0.30,  # operational feasibility
)
print(cv.overall())    # geometric mean, capped at 0.95
```

---

## Lineage Provenance

Full 6-component provenance per entity:

```python
from tools.ikros.models import (
    LineageRecord, LineageOrigin, LineageDependencies,
    LineageExperiments, LineageEvidence, LineageSuccessors, LineageRetirement,
)

lineage = LineageRecord(
    origin=LineageOrigin(
        created_by="agent-id",
        created_at="2026-08-02T12:00:00Z",
        creation_context="WP-IMP-0042",
        motivation="Establish baseline trend hypothesis",
    ),
    dependencies=LineageDependencies(
        inputs=["IKROS-RQ-20260802-0001"],
        datasets=["IKROS-DSV-20260802-0001"],
    ),
    experiments=LineageExperiments(
        tested_in=["IKROS-EXP-20260802-0001"],
        validated_by=["IKROS-VAL-20260802-0001"],
    ),
    evidence=LineageEvidence(
        ers_records=["05-work-packages/WP-IMP-0042/evidence/EXEC-044.yaml"],
    ),
)
```

---

## Alpha Promotion Workflow

```python
from tools.ikros import AlphaRegistry, AlphaCandidate, Alpha
from tools.ikros.models import PromotionStatus, AlphaPaperStatus

alpha_reg = AlphaRegistry()

# Register candidate
alpha_reg.register(candidate)

# Reject with documented reasons (permanent institutional memory)
alpha_reg.reject(
    "IKROS-ALPHACAND-20260802-0001",
    reasons=["OOS Sharpe 0.45 < minimum 1.0", "Walk-forward consistency 0.54 < 0.60"],
)

# Check promotion eligibility
eligible = alpha_reg.promotion_eligible(
    min_sharpe=1.0,
    max_drawdown=0.20,
    min_direction_accuracy=0.52,
)

# Promote with ERS evidence
alpha = Alpha(
    ikros_id=make_ikros_id("Alpha", seq=1),
    entity_type="Alpha",
    version="1.0.0",
    lifecycle_state=PromotionStatus.PROMOTED,
    confidence=ConfidenceVector(validation=0.85),
    lineage=LineageRecord(
        origin=LineageOrigin(...),
        evidence=LineageEvidence(ers_records=["05-work-packages/.../EXEC-099.yaml"]),
    ),
    promoted_from=candidate.ikros_id,
    promotion_date="2026-09-01",
    promotion_evidence="05-work-packages/.../EXEC-099.yaml",
    paper_trading_status=AlphaPaperStatus.NOT_STARTED,
)
alpha_reg.promote(candidate.ikros_id, alpha)
```

---

## Persistence

Registries can persist to disk by passing `base_dir`:

```python
from pathlib import Path

base = Path("data/ikros/registries")
reg = ResearchRegistry(base_dir=base)

# Files are written as: {base}/{subdir}/{IKROS-ID}.yaml
# e.g., data/ikros/registries/research/IKROS-RQ-20260802-0001.yaml
```

On construction with `base_dir`, the registry auto-loads all existing YAML files.

Serialization is deterministic (sorted keys), UTF-8, and human-readable.

---

## Update with Version History

```python
updated = reg.update("IKROS-RQ-20260802-0001", {"campaign_tag": "PHASE-G"})
# version_history grows by one entry; previous state is preserved
```

---

## Feature Registry — Families

```python
from tools.ikros import FeatureRegistry
from tools.ikros.models import FeatureFamily

feat_reg = FeatureRegistry()

family = FeatureFamily(
    ikros_id=make_ikros_id("FeatureFamily", seq=1),
    entity_type="FeatureFamily",
    version="1.0.0",
    lifecycle_state="ACTIVE",
    confidence=ConfidenceVector(statistical=0.7),
    lineage=LineageRecord(origin=LineageOrigin(...)),
    name="TREND",
    description="Trend-following signal features for XAU/USD",
)
feat_reg.register_family(family)

# Feature supersession
feat_reg.supersede("IKROS-FEAT-20260802-0001", "IKROS-FEAT-20260901-0001")
```

---

## Limitations

- Registries are not thread-safe (single-process use).
- `find(filter_kwargs)` performs linear scan; not suitable for large (>10,000 entity) registries.
- No full-text search — IKROS Query Engine (WP-IMP-0044, planned) will provide that.
- Knowledge Graph integration is planned for WP-IMP-0043.

---

## Integration with AFRP Governance

All IKROS entities must:

1. Carry valid IKROS IDs matching `IKROS-{TYPE}-{DATE}-{SEQ}` pattern.
2. Reference ERS evidence records in `lineage.evidence.ers_records` for promoted states.
3. Have `lineage.origin.created_by` and `created_at` populated (LIN-001, LIN-002).
4. Trace back to at least one `ResearchQuestion` via `source_rq` or `dependencies.inputs`.

---

## Next Steps (Out of Scope for WP-IMP-0042)

| Work Package | Capability |
|---|---|
| WP-IMP-0043 | Knowledge Graph — graph model over all IKROS entities |
| WP-IMP-0044 | Query Engine — natural language search over institutional knowledge |
| WP-IMP-0045 | Memory Engine — 6-tier memory consolidation |
| WP-IMP-0046 | Autonomous Research — hypothesis generation from knowledge graph |
