# SPEC-010 — Research Standard RS-1.0

> **Specification ID:** `SPEC-010`
> **Version:** `0.5.0`
> **Level:** L2 (Research Specification)
> **Status:** Draft
> **Owner:** Research Team
> **Approval Authority:** Principal Quantitative Researcher
> **Work Package:** WP-IMP-0040 (stub) / TBD (formal approval)
> **Canonical Source:** Derived from Phase C/D/E methodology
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

Defines the institutional research methodology standard governing all quantitative
research conducted on the AFRP platform. RS-1.0 ensures research is reproducible,
evidence-driven, and accumulates as institutional knowledge.

## 2. Research Methodology (Derived)

### 2.1 Research Lifecycle

The following lifecycle governs all research activities:

```
Observation → Research Question → Literature Review → Economic Thesis →
Hypothesis → Experiment Design → Dataset Selection → Feature Engineering →
Validation → Statistical Evaluation → Conclusion → Knowledge Registration →
Monitoring → Retirement
```

### 2.2 Hypothesis Formation Rules

- Every hypothesis must have an economic thesis (mechanism, not just correlation)
- Hypotheses registered before experiments begin
- Alternative hypotheses documented alongside primary hypothesis

### 2.3 Experiment Design Rules

- Walk-forward validation required (minimum 5 folds)
- Out-of-sample test set never touched until final evaluation
- Monte Carlo robustness test (minimum 1,000 simulations, ruin probability threshold)
- Parameter sensitivity analysis required

### 2.4 Anti-Overfitting Policy (Derived from Phase E)

- Optimization target: validation performance, not in-sample performance
- Overfitting gap threshold: in-sample Sharpe - validation Sharpe ≤ 0.3
- Maximum parameter count bounded per strategy class

### 2.5 Promotion Criteria (Six-Bar Rule)

A strategy may NOT be promoted to production unless ALL six bars pass:

| Bar | Threshold |
|-----|-----------|
| Full-sample expectancy | > 0 |
| Full-sample Sharpe | ≥ 0.5 |
| Full-sample Sortino | ≥ 0.7 |
| Walk-forward out-of-sample edge | > 0 |
| Walk-forward positive fold ratio | ≥ 0.6 |
| Monte Carlo ruin probability | < 0.05 |

**Current status:** All Phase E strategies fail promotion (avg full-sample Sharpe: -0.22).

### 2.6 Reproducibility Requirements

- All experiments use deterministic seed=42 (EDR-009)
- Datasets versioned with SHA-256 checksums
- Feature extraction pipelines versioned
- Results archived with full provenance

## 3. Current Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Backtest harness | Implemented | `tools/backtest/` |
| Walk-forward validation | Implemented | `tools/backtest/` |
| Monte Carlo analysis | Implemented | `tools/alpha_research/` |
| Promotion governance | Implemented | `tools/alpha_research/cli.py` |
| Hypothesis registry | **MISSING** | Requires IKROS |
| Literature registry | **MISSING** | Requires IKROS |
| Research question tracking | **MISSING** | Requires IKROS |

## 4. Traceability

NFR-022..032 in TVM-001.

## 5. Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.5.0 | 2026-08-02 | Draft derived from Phase C/D/E methodology; formal approval pending |
