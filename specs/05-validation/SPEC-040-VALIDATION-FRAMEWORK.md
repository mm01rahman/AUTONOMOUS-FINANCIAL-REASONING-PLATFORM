# SPEC-040 — Validation Framework

> **Specification ID:** `SPEC-040`
> **Version:** `1.0.0`
> **Level:** L5 (Validation Specification)
> **Status:** Approved
> **Owner:** Validation Team
> **Approval Authority:** ARB
> **Work Package:** WP-IMP-0033, WP-IMP-0036
> **Canonical Source:** Derived from system_gate.py + tools/verification/
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

Defines the complete validation framework for AFRP, encompassing runtime verification,
mathematical invariant checks, stress testing, performance benchmarking, and
statistical validation of research results.

## 2. Architecture Fitness Functions

| FIT | Name | Tool | Result |
|-----|------|------|--------|
| FIT-001 | DAG Circularity | `afrp plan` | PASS |
| FIT-002 | AST Illegal Syntax | `afrp validate` | PASS |
| FIT-003 | Protobuf Custom Options | `buf lint` | PASS |
| FIT-004 | Cross-Layer Import | `afrp validate` | PASS |
| FIT-005 | Boundary Confinement | `afrp evidence` | PASS |
| FIT-006 | Kernel Length | `afrp validate` | PASS |
| FIT-007 | Traceability Coverage | `afrp health` | PASS |
| FIT-008 | Deterministic Replay | `tools/system_gate.py` | PASS |

## 3. Runtime Verification (Phase B)

### 3.1 Deterministic Replay (FIT-008)

Replays `09-validation/fixtures/mp04_ticks.yaml` through system pipeline.
Expected SHA-256 checksum: `9742f494fdfc3515e8b0e323af38d4ed73ecb039f6eeb671be7903a99ca8e079`
Tool: `tools/system_gate.py`

### 3.2 Mathematical Invariant Checks

| Check | Invariant | Tool |
|-------|----------|------|
| PCR5 mass conservation | sum(masses) ≈ 1.0 ± 1e-9 | `math_checks.py` |
| Calibration conservation | weights sum ≈ 1.0 | `math_checks.py` |
| Latency budget | P99 ≤ 50ms | `performance.py` |

### 3.3 Stress Tests

| Test | Scenario | Expected Behaviour |
|------|---------|-------------------|
| Feed loss | Total data feed loss | System enters DEGRADED state, not CRASH |
| Long replay | 1,000+ event replay | No memory leak, deterministic output |

## 4. Validation Scenarios Library

14 mandatory scenarios (VAL-001..VAL-014). Location: `09-validation/scenarios/`.

## 5. Research Validation Metrics

| Metric | Definition | Threshold |
|--------|-----------|-----------|
| Sharpe Ratio | Risk-adjusted return | ≥ 0.5 for promotion |
| Sortino Ratio | Downside risk return | ≥ 0.7 for promotion |
| Calmar Ratio | Return / Max Drawdown | Documented |
| Max Drawdown | Worst peak-to-trough | < 30% for promotion |
| Win Rate | Profitable trade % | > 45% for promotion |
| Brier Score | Calibration accuracy | < 0.25 ideal |

## 6. Quality Gates (All WPs)

Every Work Package must pass: ruff + mypy --strict + pytest + coverage ≥ 80% +
afrp validate + afrp plan + afrp health + afrp evidence.

## 7. Traceability

EDR-007, NFR-019..021 in TVM-001.

## 8. Revision History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-08-02 | Initial import into canonical specification library |
