# Campaign 0002 — Regime Discovery for XAU/USD

## Mission

Determine the minimum institutional market-state representation that improves XAU/USD
research quality without modifying the frozen Runtime or IKROS architecture.

## Research question

Which deterministic regime taxonomy best explains the success and failure of XAU/USD
alpha hypotheses?

## Hypothesis

A deterministic overlay taxonomy built from volatility, macro-transition pressure, and
trend persistence improves validation quality and hypothesis ranking relative to
volatility-only baselines.

## Governed inputs

- `11-research/phase-e/phase_e_summary.json`
- `11-research/phase-e/regime_adaptation.json`
- `11-research/phase-e/feature_importance.json`
- `11-research/regime_analysis.md`
- `11-research/results/*.json`
- Campaign 0001 completion artifacts under `11-research/phase-g/macro-alpha/`

## Method comparison floor

The campaign compares:

1. Hidden Markov Models
2. Gaussian Mixture Models
3. Hierarchical Clustering
4. Spectral Clustering
5. Bayesian Change Point Detection
6. Density-based clustering
7. Volatility-state baseline
8. Deterministic macro-event overlay taxonomy

## Acceptance criteria

Accept a taxonomy only if it improves one or more of:

1. Validation separation
2. Feature stability
3. Hypothesis ranking utility
4. Confidence calibration
5. Research reproducibility
6. Knowledge organization

## Expected deliverables

- Method Comparison Report
- Validation Report
- Economic Interpretation Guide
- Regime Catalogue
- Transition Matrix
- Historical Regime Atlas
- Confidence Report
- Final Campaign Report
