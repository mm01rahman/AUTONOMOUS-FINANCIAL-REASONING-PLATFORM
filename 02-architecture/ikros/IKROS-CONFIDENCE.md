# IKROS Confidence & Uncertainty Model

**Document ID:** AFRP-IKROS-CONFIDENCE-1.0.0
**Specification Authority:** SPEC-060 §8–§9 — Confidence and Uncertainty
**Work Package:** WP-IMP-0041
**Version:** 1.0.0
**Status:** Draft — Awaiting ARB Approval

---

## 1. Overview

IKROS treats **confidence** and **uncertainty** as first-class properties of every knowledge object. No implicit confidence is permitted. The absence of evidence is represented as uncertainty, not as confidence.

See **ADR-IKROS-002** for the confidence model design rationale.

---

## 2. Confidence Model

### 2.1 Confidence Dimensions

Every IKROS entity carries an 8-dimensional confidence vector:

| Dimension | Symbol | Range | Description |
|-----------|--------|-------|-------------|
| Prior Confidence | C_prior | [0,1] | Confidence before any evidence |
| Statistical Confidence | C_stat | [0,1] | p-value based (1 - p_value) |
| Economic Confidence | C_econ | [0,1] | Strength of economic rationale |
| Data Confidence | C_data | [0,1] | Data quality and quantity |
| Model Confidence | C_model | [0,1] | Model generalization quality |
| Validation Confidence | C_val | [0,1] | Walk-forward and OOS stability |
| Replication Confidence | C_rep | [0,1] | Independent replication count |
| Operational Confidence | C_op | [0,1] | Live or paper trading performance |

**Overall Confidence:**
```
C_overall = Geometric_Mean(
    C_prior^w_prior,
    C_stat^w_stat,
    C_econ^w_econ,
    C_data^w_data,
    C_model^w_model,
    C_val^w_val,
    C_rep^w_rep,
    C_op^w_op
)
```

Where weights `w_i` sum to 1.0 and are set per entity type.

### 2.2 Default Dimension Weights by Entity Type

| Entity Type | w_stat | w_econ | w_data | w_model | w_val | w_rep | w_op | w_prior |
|------------|--------|--------|--------|---------|-------|-------|------|---------|
| Hypothesis | 0.25 | 0.15 | 0.15 | 0.10 | 0.20 | 0.10 | 0.05 | 0.00 |
| Alpha | 0.15 | 0.10 | 0.10 | 0.15 | 0.25 | 0.10 | 0.15 | 0.00 |
| EconomicThesis | 0.10 | 0.30 | 0.10 | 0.05 | 0.15 | 0.20 | 0.05 | 0.05 |
| KnowledgeObject | 0.15 | 0.20 | 0.10 | 0.05 | 0.20 | 0.25 | 0.05 | 0.00 |
| Model | 0.20 | 0.05 | 0.15 | 0.25 | 0.25 | 0.05 | 0.05 | 0.00 |

### 2.3 Confidence Schema

```yaml
confidence:
  prior: float[0,1]           # Set at object creation
  statistical: float[0,1]     # Updated from Validation p_value
  economic: float[0,1]        # Set by analyst / ARB
  data: float[0,1]            # Derived from DatasetVersion quality
  model: float[0,1]           # Derived from overfitting_index
  validation: float[0,1]      # Derived from WF consistency_score
  replication: float[0,1]     # Derived from replication_count
  operational: float[0,1]     # Derived from paper trading performance
  overall: float[0,1]         # Computed (see formula above)
  last_updated: ISO8601
  update_history: list         # Append-only update log
```

---

## 3. Confidence Propagation Rules

### 3.1 Rule P-1: Statistical Confidence Update

When a `Validation` record is linked with verdict `PASS`:
```
C_stat_new = max(C_stat_current, 1.0 - validation.p_value)
```

When a `Validation` record is linked with verdict `FAIL`:
```
C_stat_new = C_stat_current × (validation.p_value / 0.05)
```

### 3.2 Rule P-2: Data Confidence Inheritance

When an Experiment uses a DatasetVersion:
```
C_data_experiment = min(C_data for each DatasetVersion used)
```

Data quality grade mapping:
- Grade A → C_data = 0.90
- Grade B → C_data = 0.70
- Grade C → C_data = 0.50
- UNVERIFIED → C_data = 0.20

### 3.3 Rule P-3: Model Confidence from Overfitting Index

```
C_model = max(0, 1.0 - (overfitting_index - 1.0) / 2.0)
```
- `overfitting_index = 1.0` → `C_model = 1.0` (perfect generalisation)
- `overfitting_index = 2.0` → `C_model = 0.5`
- `overfitting_index ≥ 3.0` → `C_model = 0.0`

### 3.4 Rule P-4: Validation Confidence from Walk-Forward

```
C_val = WalkForward.consistency_score × (1 - WalkForward.sharpe_degradation / 2)
```

### 3.5 Rule P-5: Replication Confidence

```
C_rep = 1 - exp(-replication_count / 3)
```
- 0 replications → C_rep = 0.00
- 1 replication → C_rep = 0.28
- 3 replications → C_rep = 0.63
- 5 replications → C_rep = 0.81
- 10 replications → C_rep = 0.96

### 3.6 Rule P-6: Contradiction Penalty

When a `ContradictoryEvidence` of given severity is linked:
| Severity | Confidence Multiplier |
|----------|----------------------|
| MINOR | × 0.95 |
| MODERATE | × 0.80 |
| MAJOR | × 0.60 |
| INVALIDATING | × 0.10 |

### 3.7 Rule P-7: Temporal Decay

```
C_overall_t = C_overall_0 × exp(-λ_type × days_since_validation)
```

Decay rates (λ) per entity type:
| Entity Type | λ (per day) | Half-life |
|------------|------------|---------|
| AlphaCandidate | 0.001 | ~693 days |
| Alpha | 0.0005 | ~1386 days |
| KnowledgeObject | 0.0001 | ~6931 days |
| Failure | 0 | Never decays |

---

## 4. Uncertainty Model

### 4.1 Uncertainty Types

IKROS distinguishes six categories of uncertainty:

| Type | Symbol | Description | Reducible? |
|------|--------|-------------|-----------|
| Aleatoric | U_alea | Irreducible randomness in markets | No |
| Epistemic | U_epist | Lack of knowledge; reducible by research | Yes |
| Data | U_data | Uncertainty from data gaps or quality | Partially |
| Model | U_model | Uncertainty from model misspecification | Partially |
| Regime | U_regime | Uncertainty about current/future regime | No |
| Operational | U_op | Uncertainty from execution, slippage, etc. | Partially |

### 4.2 Uncertainty Schema

```yaml
uncertainty:
  aleatoric: float[0,1]        # Market noise floor
  epistemic: float[0,1]        # = 1 - C_statistical × C_replication
  data: float[0,1]             # = 1 - C_data
  model: float[0,1]            # = 1 - C_model
  regime: float[0,1]           # = WorldModel.uncertainty_regime
  operational: float[0,1]      # = 1 - C_operational
  total: float[0,1]            # Aggregated uncertainty
```

### 4.3 Total Uncertainty

```
U_total = 1 - C_overall^2
```

This formulation ensures:
- `C_overall = 1.0` → `U_total = 0.0` (certain)
- `C_overall = 0.5` → `U_total = 0.75` (highly uncertain)
- `C_overall = 0.0` → `U_total = 1.0` (completely uncertain)

### 4.4 Aleatoric Uncertainty Floor

For XAU/USD intraday trading:
- M1 bars: U_alea ≥ 0.40 (40% irreducible noise)
- H1 bars: U_alea ≥ 0.25
- D1 bars: U_alea ≥ 0.15

These floors are empirically calibrated from Phase E results (direction accuracy ceiling ~55%).

---

## 5. Confidence in Phase E Context

Phase E produced the following confidence assessments:

| Strategy | C_stat | C_val | C_model | C_overall | Verdict |
|---------|--------|-------|---------|-----------|---------|
| Trend Following | 0.08 | 0.23 | 0.45 | 0.15 | REJECTED |
| Mean Reversion | 0.05 | 0.18 | 0.40 | 0.12 | REJECTED |
| Liquidity Sweep | 0.03 | 0.12 | 0.35 | 0.08 | REJECTED |
| Macro-Only | 0.10 | 0.25 | 0.42 | 0.17 | REJECTED |
| Technical-Only | 0.12 | 0.28 | 0.48 | 0.19 | REJECTED |
| Hybrid | 0.09 | 0.22 | 0.44 | 0.16 | REJECTED |

**Institutional Conclusion (NFR-036 baseline):** No XAU/USD alpha candidate met the minimum C_overall threshold of 0.50 required for promotion. The epistemically honest overall research confidence is 0.19 (best candidate: Technical-Only).

---

## 6. Bayesian Update Protocol

When new evidence arrives for an existing object:

1. Record current `C_prior = C_overall` in history
2. Apply propagation rules (P-1 through P-7)
3. Compute new `C_overall`
4. Record update event to Episodic Memory (T1)
5. If `|C_new - C_old| > 0.10`: trigger downstream propagation to all linked objects
6. If `C_new < 0.20` and object is `SUPPORTED`: trigger contradiction review

---

## 7. Traceability

| Specification Section | Implemented By |
|----------------------|----------------|
| SPEC-060 §8 Confidence | §2–§3 Confidence Model |
| SPEC-060 §8.1 Dimensions | §2.1 Confidence Dimensions |
| SPEC-060 §8.2 Propagation | §3 Propagation Rules |
| SPEC-060 §9 Uncertainty | §4 Uncertainty Model |
| SPEC-060 §9.1–§9.6 Uncertainty types | §4.1 |
