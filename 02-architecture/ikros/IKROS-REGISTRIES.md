# IKROS Registry Architecture

**Document ID:** AFRP-IKROS-REGISTRIES-1.0.0
**Specification Authority:** SPEC-060 §5 — Registry Architecture
**Work Package:** WP-IMP-0041
**Version:** 1.0.0
**Status:** Draft — Awaiting ARB Approval

---

## 1. Overview

IKROS maintains **13 institutional registries**, each governing a specific class of research object. Every registry provides:
- Schema-validated storage
- Governed lifecycle transitions
- Versioning and audit trail
- Standard query interface
- Integration hooks to the Knowledge Graph

All registries implement the **IKROSRegistry** interface and use the naming convention:
```
REGISTRY/{TYPE}/{IKROS-ID}.yaml
```

---

## 2. Registry Interface Contract

Every registry implements:

```python
class IKROSRegistry:
    def register(self, entity: KnowledgeObject) -> str: ...  # Returns ikros_id
    def get(self, ikros_id: str) -> KnowledgeObject: ...
    def update(self, ikros_id: str, delta: dict) -> None: ...
    def transition(self, ikros_id: str, new_state: str, evidence: str) -> None: ...
    def list(self, filters: dict) -> List[KnowledgeObject]: ...
    def search(self, query: str) -> List[KnowledgeObject]: ...
    def history(self, ikros_id: str) -> List[VersionRecord]: ...
    def retire(self, ikros_id: str, reason: str) -> None: ...
```

---

## 3. Research Registry

**Purpose:** Central index of all research questions and campaigns.

**Schema:**
```yaml
ikros_id: "IKROS-RQ-YYYYMMDD-NNNN"
title: str
motivation: str
scope: MICRO | MACRO | REGIME | STRUCTURAL
instrument: str
time_horizon: str
status: OPEN | ACTIVE | ANSWERED | RETIRED
created_at: ISO8601
confidence_score: float[0,1]
linked_hypotheses: list[IKROS-ID]
linked_conclusions: list[IKROS-ID]
campaign_tag: str           # e.g., "PHASE-E", "PHASE-F"
```

**Lifecycle:** `OPEN` → `ACTIVE` → `ANSWERED` → `RETIRED`

**Key Queries:**
- `list(status=OPEN)` — all unanswered research questions
- `list(instrument='XAU/USD', scope='MACRO')` — gold macro questions
- `search("inflation hedge")` — semantic search

---

## 4. Hypothesis Registry

**Purpose:** All testable hypotheses with full evidence linkage.

**Schema:**
```yaml
ikros_id: "IKROS-HYP-YYYYMMDD-NNNN"
statement: str
null_hypothesis: str
alternative_hypothesis: str
significance_level: float     # e.g., 0.05
power: float                  # e.g., 0.80
prior_confidence: float[0,1]
posterior_confidence: float[0,1]
status: PROPOSED | TESTING | SUPPORTED | REFUTED | INCONCLUSIVE | RETIRED
version: semver
source_rq: IKROS-ID
motivating_thesis: list[IKROS-ID]
experiments: list[IKROS-ID]
validations: list[IKROS-ID]
contradictions: list[IKROS-ID]
```

**Lifecycle:**
`PROPOSED` → `UNDER_REVIEW` → `APPROVED_FOR_TESTING` → `TESTING` → `SUPPORTED` | `REFUTED` | `INCONCLUSIVE` → `RETIRED`

**Governance Gates:**
- `APPROVED_FOR_TESTING`: requires peer review sign-off
- `SUPPORTED` / `REFUTED`: requires Validation with `verdict != INCONCLUSIVE`
- `RETIRED`: requires ResearchConclusion or Failure record

**Key Queries:**
- `list(status=SUPPORTED)` — all supported hypotheses
- `list(status=REFUTED)` — institutional memory of refuted ideas
- `search("gold inflation")` — semantic hypothesis search

---

## 5. Experiment Registry

**Purpose:** Complete record of all research experiments with reproducibility anchors.

**Schema:**
```yaml
ikros_id: "IKROS-EXP-YYYYMMDD-NNNN"
title: str
hypotheses: list[IKROS-ID]
protocol: str
dataset_versions: list[IKROS-ID]
feature_versions: list[IKROS-ID]
parameters: map
random_seed: int
in_sample_range: {start: date, end: date}
out_of_sample_range: {start: date, end: date}
status: DESIGNED | RUNNING | COMPLETE | FAILED | INVALIDATED
reproducibility_hash: str     # SHA256 of all inputs
git_commit: str               # Repository commit at time of experiment
created_at: ISO8601
completed_at: ISO8601 | null
validations_produced: list[IKROS-ID]
failures_produced: list[IKROS-ID]
```

**Lifecycle:**
`DESIGNED` → `APPROVED` → `RUNNING` → `COMPLETE` | `FAILED` → `REVIEWED` → `ARCHIVED` | `INVALIDATED`

**Governance Gates:**
- `APPROVED`: requires hypothesis list and protocol review
- `COMPLETE`: requires `reproducibility_hash` recorded
- `INVALIDATED`: requires reason (e.g., data error discovered)

**Key Queries:**
- `list(status=COMPLETE, hypotheses contains IKROS-HYP-*)` — experiments testing a hypothesis
- `get(reproducibility_hash=<hash>)` — exact experiment replay lookup

---

## 6. Dataset Registry

**Purpose:** Canonical index of all datasets and their versioned snapshots.

**Schema:**
```yaml
ikros_id: "IKROS-DS-YYYYMMDD-NNNN"
name: str
instrument: str
frequency: str
date_range: {start: date, end: date}
row_count: int
source: str
schema_version: str
quality_grade: A | B | C | UNVERIFIED
current_version: IKROS-ID   # Points to active DatasetVersion
versions: list[IKROS-ID]
status: REGISTERED | VALIDATED | ACTIVE | DEPRECATED | ARCHIVED
```

**DatasetVersion Schema:**
```yaml
ikros_id: "IKROS-DSV-YYYYMMDD-NNNN"
dataset_id: IKROS-ID
version: semver
created_at: ISO8601
hash_sha256: str             # IMMUTABLE after creation
row_count: int
change_summary: str
supersedes: IKROS-ID | null
```

**Governance Gates:**
- `VALIDATED`: requires quality scan pass
- Version creation: requires `hash_sha256` computed from file content

**Key Queries:**
- `list(instrument='XAU/USD', quality_grade='A')` — production-grade gold data
- `get(hash_sha256=<hash>)` — exact data snapshot lookup for experiment replay

---

## 7. Feature Registry

**Purpose:** Versioned catalogue of all computed features.

**Schema:**
```yaml
ikros_id: "IKROS-FEAT-YYYYMMDD-NNNN"
name: str
family: IKROS-ID             # FeatureFamily
computation: str             # Mathematical definition
inputs: list[str]            # Column names or parent feature names
lookback: str                # e.g., "200 bars"
normalization: str
stationarity: STATIONARY | NON_STATIONARY | UNKNOWN
information_content: float
stability_score: float[0,1]
version: semver
status: DRAFT | VALIDATED | ACTIVE | DEPRECATED | RETIRED
used_in_experiments: list[IKROS-ID]
superseded_by: IKROS-ID | null
```

**FeatureFamily Schema:**
```yaml
ikros_id: "IKROS-FF-YYYYMMDD-NNNN"
name: str
description: str
feature_count: int
average_information_content: float
member_features: list[IKROS-ID]
```

**Key Queries:**
- `list(family='MICROSTRUCTURE', status=ACTIVE)` — active microstructure features
- `list(stationarity=NON_STATIONARY)` — non-stationary features requiring transformation

---

## 8. Factor Registry

**Purpose:** Catalogue of economically-motivated return drivers.

**Schema:**
```yaml
ikros_id: "IKROS-FACTOR-YYYYMMDD-NNNN"
name: str
economic_motivation: str
persistence_score: float[0,1]
replication_count: int
last_validated_at: ISO8601
implementing_features: list[IKROS-ID]
supporting_literature: list[IKROS-ID]
captured_in_alphas: list[IKROS-ID]
status: PROPOSED | VALIDATED | ACTIVE | DEPRECATED
```

**Key Queries:**
- `list(status=ACTIVE, persistence_score > 0.7)` — robust factors
- `list(replication_count > 3)` — well-replicated factors

---

## 9. Model Registry

**Purpose:** Versioned catalogue of trained predictive models.

**Schema:**
```yaml
ikros_id: "IKROS-MODEL-YYYYMMDD-NNNN"
architecture: str
features_used: list[IKROS-ID]
training_dataset: IKROS-ID   # DatasetVersion
hyperparameters: map
training_hash: str           # Reproducibility hash
in_sample_metrics:
  sharpe: float
  max_drawdown: float
  direction_accuracy: float
out_of_sample_metrics:
  sharpe: float
  max_drawdown: float
  direction_accuracy: float
overfitting_index: float     # sharpe_is / sharpe_oos; 1.0 = ideal
status: TRAINED | VALIDATED | APPROVED | REJECTED | ACTIVE | DEPRECATED | RETIRED
incorporated_in: list[IKROS-ID]
superseded_by: IKROS-ID | null
```

**Governance Gates:**
- `APPROVED`: requires `overfitting_index < 2.0` and OOS Sharpe > threshold
- `ACTIVE`: requires ARB sign-off
- `REJECTED`: requires failure record and root cause

**Key Queries:**
- `list(status=ACTIVE)` — all production-active models
- `list(overfitting_index < 1.5, oos_sharpe > 1.0)` — high-quality models

---

## 10. Validation Registry

**Purpose:** Complete record of all formal validations.

**Schema:**
```yaml
ikros_id: "IKROS-VAL-YYYYMMDD-NNNN"
experiment_id: IKROS-ID
validates: list[IKROS-ID]    # Hypotheses, Models, Alphas validated
verdict: PASS | FAIL | INCONCLUSIVE
method: STATISTICAL | WALK_FORWARD | MONTE_CARLO | STRESS_TEST | REGIME_ANALYSIS
metric_results: map
p_value: float | null
effect_size: float | null
confidence_interval: [float, float] | null
overfitting_score: float[0,1]
regime_stability: float[0,1]
ers_evidence_ref: str        # ERS-1.0 evidence record path
created_at: ISO8601
```

**Key Queries:**
- `list(verdict=FAIL, validates contains IKROS-HYP-*)` — failed hypothesis validations
- `list(method=WALK_FORWARD, regime_stability > 0.7)` — regime-stable walk-forward results

---

## 11. Alpha Registry

**Purpose:** Tracks all alpha candidates and promoted alphas.

**AlphaCandidate Schema:**
```yaml
ikros_id: "IKROS-ALPHACAND-YYYYMMDD-NNNN"
name: str
strategy_type: TREND | MEAN_REVERSION | LIQUIDITY | MACRO | HYBRID
sharpe_oos: float
max_drawdown: float
direction_accuracy: float
win_rate: float
promotion_score: float[0,1]
promotion_status: CANDIDATE | PROMOTED | REJECTED | RETIRED
rejection_reasons: list[str]
backtests: list[IKROS-ID]
walk_forwards: list[IKROS-ID]
monte_carlos: list[IKROS-ID]
implements_hypotheses: list[IKROS-ID]
```

**Alpha Schema:**
```yaml
ikros_id: "IKROS-ALPHA-YYYYMMDD-NNNN"
promoted_from: IKROS-ID      # AlphaCandidate
promotion_date: date
promotion_evidence: str      # ERS evidence path
paper_trading_status: NOT_STARTED | ACTIVE | COMPLETED | FAILED
live_eligible: bool
```

**Key Queries:**
- `list(promotion_status=REJECTED)` — all rejected candidates (institutional memory)
- `list(promotion_status=PROMOTED)` — all promoted alphas
- `list(strategy_type=TREND, sharpe_oos > 1.0)` — high-quality trend candidates

---

## 12. Failure Registry

**Purpose:** Permanent institutional memory of all research failures.

**Schema:**
```yaml
ikros_id: "IKROS-FAIL-YYYYMMDD-NNNN"
failed_object_id: IKROS-ID
failed_object_type: str
failure_type: STATISTICAL | ECONOMIC | OVERFITTING | DATA_QUALITY | REGIME_INSTABILITY
failure_description: str     # IMMUTABLE
root_cause: str              # IMMUTABLE
lessons_learned: str         # IMMUTABLE
prevents_repetition: str
created_at: ISO8601          # IMMUTABLE
supplemented_at: list[ISO8601]  # Can be added to but not changed
supplements: list[str]       # Additional analysis added later
```

**IMMUTABILITY POLICY:** All fields marked IMMUTABLE may NEVER be modified after creation. Only `supplements` may be appended.

**Key Queries:**
- `list(failure_type=OVERFITTING)` — all overfitting failures
- `list(failed_object_type=AlphaCandidate)` — all failed strategies
- `search("gold inflation regime")` — semantic failure search

---

## 13. Knowledge Registry

**Purpose:** Distilled institutional knowledge objects available for future research.

**Schema:**
```yaml
ikros_id: "IKROS-KO-YYYYMMDD-NNNN"
title: str
content: str
category: PATTERN | PRINCIPLE | CONSTRAINT | HEURISTIC | ANOMALY
applicability: str
confidence: float[0,1]
replication_count: int
last_validated: ISO8601
extracted_from: list[IKROS-ID]
applied_in: list[IKROS-ID]
status: EXTRACTED | VALIDATED | INSTITUTIONALISED | MONITORING | RETIRED
```

**Key Queries:**
- `list(category=CONSTRAINT, confidence > 0.8)` — high-confidence constraints
- `list(status=INSTITUTIONALISED)` — all ratified knowledge
- `search("regime transition")` — semantic knowledge search

---

## 14. Decision Registry

**Purpose:** Record of all AFRP trading decisions for audit and learning.

**Schema:**
```yaml
ikros_id: "IKROS-DEC-YYYYMMDD-NNNN"
signal: float                # -1 to +1
direction: LONG | SHORT | FLAT
confidence: float[0,1]
rationale: str
world_model_id: IKROS-ID
policy_id: IKROS-ID
timestamp: ISO8601
outcome: PROFITABLE | LOSS | FLAT | UNKNOWN
outcome_pnl: float | null
outcome_recorded_at: ISO8601 | null
```

**Key Queries:**
- `list(outcome=LOSS, confidence > 0.8)` — high-confidence losses for analysis
- `list(direction=LONG)` — all long decisions

---

## 15. Literature Registry

**Purpose:** Canonical index of all external research referenced by AFRP.

**Schema:**
```yaml
ikros_id: "IKROS-LIT-YYYYMMDD-NNNN"
title: str
authors: list[str]
publication_date: date
source: str
doi_or_url: str
abstract: str
relevance_tags: list[str]
ingested_at: ISO8601
quality_score: float[0,1]
cited_by: list[IKROS-ID]
status: INGESTED | REVIEWED | REFERENCED | SUPERSEDED | ARCHIVED
```

**Key Queries:**
- `list(relevance_tags contains 'gold', quality_score > 0.7)` — high-quality gold research
- `search("safe haven asset inflation")` — semantic literature search

---

## 16. Registry File Layout

```
data/ikros/registries/
├── research/         # IKROS-RQ-*.yaml
├── hypotheses/       # IKROS-HYP-*.yaml
├── experiments/      # IKROS-EXP-*.yaml
├── datasets/         # IKROS-DS-*.yaml, IKROS-DSV-*.yaml
├── features/         # IKROS-FEAT-*.yaml, IKROS-FF-*.yaml
├── factors/          # IKROS-FACTOR-*.yaml
├── models/           # IKROS-MODEL-*.yaml
├── validations/      # IKROS-VAL-*.yaml
├── alphas/           # IKROS-ALPHACAND-*.yaml, IKROS-ALPHA-*.yaml
├── failures/         # IKROS-FAIL-*.yaml (IMMUTABLE)
├── knowledge/        # IKROS-KO-*.yaml
├── decisions/        # IKROS-DEC-*.yaml
└── literature/       # IKROS-LIT-*.yaml
```

---

## 17. Traceability

| Specification Section | Implemented By |
|----------------------|----------------|
| SPEC-060 §5 Registry Architecture | This document |
| SPEC-060 §5.1 Research Registry | §3 Research Registry |
| SPEC-060 §5.2–5.13 All Registries | §4–§15 |
