# Campaign 0005 Scientific Validation

## Objective

Scientifically validate the five ARB-approved regime-conditioned hypotheses from
Campaign 0004 without tuning parameters, optimizing strategy rules, modifying the
Runtime, or adding infrastructure.

## Authorized hypotheses

1. `IKROS-HYP-20260802-0401` — Expectation-relief bull continuation
2. `IKROS-HYP-20260802-0402` — Liquidation-pressure bear continuation
3. `IKROS-HYP-20260802-0404` — Crisis safe-haven breakout convexity
4. `IKROS-HYP-20260802-0405` — Policy-shock repricing continuation
5. `IKROS-HYP-20260802-0408` — Transition-to-trend handoff

## Governed validation floor

- Walk-forward validation
- Combinatorial purged cross validation approximation with holding-period embargo
- Monte Carlo path analysis
- Bootstrap confidence intervals
- Sensitivity analysis
- Temporal stability and concept-drift review
- Cross-regime persistence review
- Out-of-sample replay
- Stress testing on governed shock windows
- Probabilistic Sharpe ratio
- Deflated Sharpe ratio approximation
- White's Reality Check approximation across bounded sensitivity variants
- Probability of backtest overfitting: not applicable because no model-selection or parameter-search workflow is permitted in Campaign 0005

## Campaign rule

Each hypothesis is translated into a fixed deterministic event rule using only the
approved taxonomy and approved Phase G feature catalogue. Any hypothesis failing
the institutional scientific standard is either rejected or retained for further
research. Promotion is allowed only when the full governed validation stack is
satisfied.
