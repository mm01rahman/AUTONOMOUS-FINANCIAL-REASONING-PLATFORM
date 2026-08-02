# Phase E Alpha Research & Strategy Evolution

## Scope

Phase E is a **deterministic, offline-only quantitative research package**. It does not
modify the frozen runtime, does not alter system architecture, and does not connect to
any broker or live venue.

## Package

`tools/alpha_research/`

- `data.py`: official local AFRP-Datasets ingestion and alignment.
- `features.py`: deterministic feature engineering for macro, microstructure,
  liquidity, regime, forward-expectations, behavioral, and technical signals.
- `strategies.py`: baseline plus required Phase E candidate strategy families.
- `backtester.py`: deterministic close-to-close portfolio accounting with
  reproducible trade checksums.
- `optimization.py`: compact parameter search, anti-overfitting penalties,
  rolling walk-forward validation, and Monte Carlo resampling.
- `analysis.py`: alpha attribution, feature importance, decision quality, and
  regime-adaptation analytics.
- `reporting.py`: JSON/Markdown artifact emission under `11-research/phase-e/`.
- `cli.py` / `tools/alpha_research_run.py`: end-to-end orchestration.

## Governance guarantees

- Uses only local deterministic methods and official local datasets.
- Produces governed research artifacts and promotion assessments only.
- Promotion bars require positive expectancy, positive Sharpe, acceptable
  Sortino / drawdown, stable walk-forward behavior, robust Monte Carlo, and no
  material overfitting gap.

## Run

```bash
uv run python -m tools.alpha_research_run
```

Outputs are written to `11-research/phase-e/`.
