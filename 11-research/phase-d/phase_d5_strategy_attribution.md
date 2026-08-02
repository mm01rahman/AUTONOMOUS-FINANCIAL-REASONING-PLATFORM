# Phase D.5 Strategy Performance Attribution

## Paper-trading attribution by deterministic trend bucket

| Trend | Periods | Signals | Execution statuses | Avg total PnL snapshot | Avg momentum | Avg geopolitical | Avg calendar impact |
|---|---:|---|---|---:|---:|---:|---:|
| up | 21 | {'buy': 21} | {'failed': 3, 'filled': 13, 'partial': 5} | -8.0755 | 0.4700 | -0.0143 | 0.4643 |
| down | 3 | {'sell': 3} | {'partial': 1, 'failed': 1, 'filled': 1} | -9.9531 | -0.5667 | -0.1000 | 0.5833 |

## Phase C historical context

- AFRP backtest total return: `-0.8371`; Sharpe `-0.4611`; max drawdown `0.9003`.
- Best benchmark by total return: `buy_and_hold` at `3.8246` return.
- Worst benchmark by total return: `mean_reversion` at `-0.4079` return.
- Conclusion: D5 removed false operational blockers but did not change the historically weak strategy edge.
