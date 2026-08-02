# Phase D.5 Decision Quality Report

## Paper-trading decision quality

- Confidence mean/min/max: `0.791042` / `0.785000` / `0.855000`
- Signals: 21 buy, 3 sell
- Authorized decisions: 24/24
- Paper-trading win rate: `0.0833`
- Paper-trading profit factor: `0.0591`
- Paper-trading Sharpe: `-15.6884`

## Assessment

The world-model / decision path is deterministic and internally stable, but its risk-adjusted returns remain weak. This is consistent with Phase C backtesting, where AFRP full-dataset return was `-0.8371` with Sharpe `-0.4611` and max drawdown `0.9003`. Improving this would require strategy redesign rather than a Phase D integration fix, so no decision-policy changes were implemented.
