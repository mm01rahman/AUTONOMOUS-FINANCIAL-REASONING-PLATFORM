# SPEC-013 — Alpha Validation Framework

> **Specification ID:** `SPEC-013`
> **Version:** `0.5.0`
> **Level:** L2 (Research Specification)
> **Status:** Draft
> **Owner:** Research / Validation Teams
> **Approval Authority:** Principal Quantitative Researcher
> **Work Package:** WP-IMP-0036, WP-IMP-0037, WP-IMP-0039 (partial)
> **Canonical Source:** Derived from Phase B/C/E validation methodology
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

Defines the validation framework for all alpha candidates, strategies, and research
hypotheses. Specifies promotion criteria, statistical tests, and quality gates.

## 2. Validation Tiers

### Tier A — Runtime Verification (Phase B)

Statistical and deterministic verification of the runtime platform.

| Test | Metric | Threshold | Tool |
|------|--------|-----------|------|
| Deterministic replay | SHA-256 checksum match | Exact match | `system_gate.py` |
| PCR5 mass conservation | Sum of masses | ≈ 1.0 (≤1e-9 error) | `tools/verification/math_checks.py` |
| Feed loss degradation | System state after feed loss | DEGRADED (not CRASH) | `tools/verification/stress.py` |
| Decision latency P99 | Nanoseconds | ≤ 50ms | `tools/verification/performance.py` |

### Tier B — Statistical Validation (Phase C backtest)

In-sample and out-of-sample performance validation.

| Metric | Governance Threshold |
|--------|---------------------|
| Full-sample Sharpe ratio | ≥ 0.5 |
| Full-sample Sortino ratio | ≥ 0.7 |
| Full-sample positive expectancy | > 0 |
| Maximum drawdown | < 30% |
| Win rate | > 45% |

### Tier C — Walk-Forward Validation

Out-of-sample robustness across time periods.

| Metric | Governance Threshold |
|--------|---------------------|
| Walk-forward edge | > 0 |
| Positive fold ratio | ≥ 0.6 |
| Overfitting gap (IS - OOS Sharpe) | ≤ 0.3 |

### Tier D — Monte Carlo Robustness

Statistical robustness under path randomization.

| Metric | Governance Threshold |
|--------|---------------------|
| Ruin probability | < 0.05 |
| Confidence interval width | Documented |

## 3. Six-Bar Promotion Rule

All six bars must pass simultaneously for promotion:

```
Bar 1: Full-sample expectancy > 0          ← Phase E: ALL FAIL
Bar 2: Full-sample Sharpe ≥ 0.5            ← Phase E: ALL FAIL
Bar 3: Full-sample Sortino ≥ 0.7           ← Phase E: ALL FAIL
Bar 4: WF out-of-sample edge > 0           ← Phase E: ALL FAIL
Bar 5: WF positive fold ratio ≥ 0.6        ← Phase E: ALL FAIL
Bar 6: MC ruin probability < 0.05          ← Technical Only passes; others FAIL
```

## 4. Validation Scenarios (Phase B)

14 mandatory scenarios: VAL-001 (FOMC) through VAL-014 (Low Volatility).
All scenarios must PASS before any strategy promotion.

## 5. Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Deterministic replay | Implemented | `tools/system_gate.py` |
| Math invariant checks | Implemented | `tools/verification/math_checks.py` |
| Statistical metrics | Implemented | `tools/verification/statistical.py` |
| Walk-forward validation | Implemented | `tools/backtest/` |
| Monte Carlo | Implemented | `tools/alpha_research/` |
| Promotion assessment | Implemented | `tools/alpha_research/cli.py` |
| Formal spec document | Draft (this file) | — |

## 6. Traceability

NFR-019..021 (Phase B V&V), NFR-022..024 (Phase C backtest) in TVM-001.

## 7. Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.5.0 | 2026-08-02 | Draft derived from Phase B/C/E; formal approval pending |
