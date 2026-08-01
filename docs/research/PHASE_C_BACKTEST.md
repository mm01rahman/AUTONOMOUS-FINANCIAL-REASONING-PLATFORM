# Phase C Backtesting Framework

## Overview

The AFRP quantitative backtesting framework (`tools/backtest/`) provides a
deterministic, cost-aware historical backtesting platform for evaluating the
AFRP autonomous trading system against 8 market regimes and 6 classical benchmark
strategies.

## Package Structure

```
tools/backtest/
├── __init__.py      — Public API exports
├── costs.py         — Execution cost model (spread, slippage, commission)
├── engine.py        — Core BacktestEngine and data models
├── benchmarks.py    — 6 benchmark strategy implementations
├── metrics.py       — Performance metric suite
├── regimes.py       — Market regime definitions and date filtering
├── reports.py       — Markdown and JSON report generators
├── campaign.py      — ResearchCampaign orchestrator (WP-C1..C9)
└── cli.py           — CLI entry point
```

## Core Components

### BacktestConfig

```python
@dataclass
class BacktestConfig:
    initial_capital: float = 100_000.0
    leverage: float = 1.0
    spread_pips: float = 0.3
    slippage_pips: float = 0.1
    commission_per_lot: float = 7.0
    risk_per_trade: float = 0.01   # 1%
    bars_per_year: float = 252.0
    risk_free_rate: float = 0.04   # 4% annual
```

### BacktestEngine

The engine processes bars deterministically:

1. Build a feature vector (`build_features(bars, idx)`)
2. Generate a rule-based signal (`_rule_based_signal(features)`)
3. Execute trades with cost application (spread, slippage, commission)
4. Track equity curve, compute SHA-256 checksum for reproducibility

### Signal Generation

The backtesting engine uses a deterministic rule-based signal that does not
depend on external state:

- **Long signal**: `price_vs_sma20 > 0.005` AND `returns > 0` AND
  `volatility_14 < 0.04` AND `high_low_range < 0.05`
- **Short signal**: symmetric bearish conditions
- **Flat**: all other conditions

### Feature Vector

Features derived from OHLCV bars:

| Feature | Description |
| --- | --- |
| `price` | Close price |
| `returns` | 1-period return |
| `sma20` | 20-period SMA |
| `price_vs_sma20` | Deviation from SMA20 |
| `volatility_14` | 14-period return std dev |
| `high_low_range` | (High - Low) / Close |
| `price_normalized` | Close / 3000 (≤ 1.0) |

## Market Regimes

| Key | Label | Period |
| --- | --- | --- |
| `gfc_2008` | 2008 Financial Crisis | 2008 |
| `gold_bull_2011` | 2011 Gold Bull Market | 2011 |
| `gold_collapse_2013` | 2013 Gold Collapse | 2013 |
| `covid_2020` | 2020 COVID | 2020 |
| `inflation_2022` | 2022 Inflation Cycle | 2022 |
| `rate_cycle_2024` | 2024 Rate Cycle | 2024 |
| `historical_2025` | 2025 Historical | 2025 |
| `available_2026` | 2026 Available | 2026 Jan–Jul |

## Benchmark Strategies

| Strategy | Description |
| --- | --- |
| `BuyAndHold` | Buy first bar, hold to end |
| `SMAcrossover` | SMA 20/50 crossover |
| `EMACrossover` | EMA 12/26 crossover |
| `Momentum` | N-day high/low breakout |
| `MeanReversion` | Z-score fade (±2σ) |
| `Breakout` | Donchian channel (20) |

## Execution Cost Model

All strategies apply identical execution costs:

- **Spread**: 0.3 pips = $0.30/lot (half-spread per entry/exit)
- **Slippage**: 0.1 pips per side = $0.20/lot round-trip
- **Commission**: $7.00/lot per side = $14.00/lot round-trip

Gold pip model: 1 lot = 100 oz; 1 pip = $0.01/oz → $1.00/pip/lot.

## Performance Metrics

The `compute_metrics()` function computes:

- Total Return, CAGR
- Sharpe Ratio (annualised), Sortino Ratio
- Calmar Ratio, Maximum Drawdown
- Win Rate, Profit Factor, Expectancy
- Recovery Factor

## Data Sources

Primary: `C:/Users/mm01r/AFRP-Datasets/processed/xauusd/xauusd_1d.parquet`
(6,502 daily bars, XAU/USD from 2000-08-30)

Fallback: Synthetic OHLCV data generated with NumPy (deterministic seed).

## Running the Campaign

```bash
uv run python -m tools.backtest.cli
```

Reports are written to `11-research/`.

## Reproducibility

Every `BacktestResult` contains a `checksum` field: the SHA-256 of all closed
trade records. Identical inputs produce identical checksums.

## Governance

- Work Package: WP-IMP-0037
- Evidence: EXEC-037
- Capability: QUANT-BACKTEST
- NFRs: NFR-022 (determinism), NFR-023 (regime coverage), NFR-024 (benchmarks)
