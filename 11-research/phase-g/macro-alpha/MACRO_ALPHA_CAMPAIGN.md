# Macro Alpha Campaign

## Campaign identity

- **Program:** Macro Alpha
- **Campaign type:** Hypothesis Validation
- **Instrument:** XAU/USD
- **Scope:** Macro
- **Status target:** Completed baseline audit

## Research question

Do macro pressure shocks driven by USD weakness, rates compression, and policy surprise generate durable next-day XAU/USD upside drift after governance-grade validation?

## Economic rationale

Gold should benefit when the opportunity cost of holding it falls, the USD weakens, or policy surprises increase demand for defensive stores of value. A governed macro-pressure feature family should therefore explain part of next-day XAU/USD drift if the effect is durable rather than episodic.

## Supporting literature and institutional sources

1. `SPEC-010` — Research Standard RS-1.0
2. `SPEC-012` — XAU/USD Alpha Discovery Bible
3. `SPEC-060` — IKROS Architecture
4. `11-research/phase-e/phase_e_final_report.md`
5. `11-research/phase-e/promotion_assessment.json`
6. `11-research/phase-e/walk_forward_validation_report.md`
7. `11-research/phase-e/monte_carlo_report.md`
8. `05-work-packages/WP-IMP-0039/evidence/EXEC-041.yaml`

## Datasets

1. Canonical XAU/USD daily research dataset used by Phase E
2. DXY return series used in the macro-only feature stack
3. Yield-curve proxies used in the macro-only feature stack
4. Fed-surprise proxies used in the macro-only feature stack

## Hypothesis

- **Primary hypothesis:** A macro-pressure signal combining USD, rates, and policy-surprise proxies produces durable next-day XAU/USD edge.
- **Null hypothesis:** The macro-pressure signal does not produce durable next-day XAU/USD edge.
- **Alternative hypothesis:** The macro-pressure signal produces durable next-day XAU/USD edge.

## Expected mechanism

Macro stress that compresses real-rate expectations or weakens the USD should increase marginal demand for gold. The signal should survive out-of-sample validation only if that mechanism dominates transaction costs, regime instability, and specification noise.

## Experiment design

1. Reuse the frozen Phase E macro-only experiment as the deterministic baseline.
2. Register the macro dataset, feature family, features, hypothesis, experiment, validation artifact, contradiction, conclusion, and alpha candidate inside IKROS.
3. Evaluate whether the prior macro-only result is strong enough to justify advancement under Phase G governance.

## Validation methodology

Required standards for advancement remain:

1. Walk-forward validation
2. Combinatorial purged cross validation
3. Monte Carlo
4. Stress testing
5. Sensitivity analysis
6. Deflated Sharpe ratio
7. Probabilistic Sharpe ratio
8. White's Reality Check where applicable
9. Probability of backtest overfitting where applicable

This baseline audit uses the completed Phase E walk-forward, Monte Carlo, and promotion evidence to determine whether the macro-only candidate is worth advancing. Missing validation components are treated as blocking gaps, not waived requirements.

## Acceptance criteria

Advance only if the macro-only candidate:

1. Preserves positive out-of-sample edge
2. Meets governance promotion bars
3. Avoids material contradiction from replication or stress evidence
4. Retains a credible macro mechanism after validation

## Failure criteria

Reject or retire the baseline if any of the following occur:

1. Walk-forward edge is not positive
2. Positive fold ratio is below governance minimum
3. Full-sample expectancy remains non-positive
4. Macro-only evidence remains statistically weak
5. Required validation components are incomplete

## Statistical tests and decision surfaces

- full-sample return / Sharpe / Sortino / expectancy
- walk-forward Sharpe
- positive fold ratio
- Monte Carlo ruin probability
- overfitting gap
- contradiction-aware confidence update

## Required evidence

1. `EXEC-041`
2. `11-research/phase-e/phase_e_summary.json`
3. `11-research/phase-e/phase_e_final_report.md`
4. `11-research/phase-e/promotion_assessment.json`

## Expected deliverables

1. Structured Macro Alpha campaign manifest
2. IKROS-registered dataset, thesis, features, hypothesis, experiment, validation, contradiction, conclusion, and alpha candidate
3. Campaign completion report
4. Candidate rejection rationale or advancement rationale

## Deterministic decision

This campaign is expected to complete as a **baseline audit**, not a promotion case. The purpose is to preserve institutional learning and prevent re-testing a weak macro-only baseline without new evidence.
