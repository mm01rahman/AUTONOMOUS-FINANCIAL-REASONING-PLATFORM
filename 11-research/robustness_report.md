# Robustness Analysis Report

**Generated:** 2026-08-01

## Scenario Results

| Scenario | Return | Sharpe | Max DD | Trades |
| --- | --- | --- | --- | --- |
| trending_bull | -8.75% | -1.0311 | 24.71% | 27 |
| trending_bear | -9.70% | -1.3789 | 20.69% | 29 |
| ranging | -8.67% | -1.0363 | 14.74% | 65 |
| high_volatility | -14.38% | -2.0958 | 23.22% | 20 |
| low_volatility | -0.75% | -0.3301 | 12.73% | 26 |
| flash_crash | 0.00% | -30202993349434872.0000 | 0.00% | 0 |
| liquidity_vacuum | -0.01% | -80.4441 | 0.01% | 1 |
| fomc_cycle | 6.32% | 1.1443 | 5.82% | 18 |
| cpi_shock | 2.85% | 0.4409 | 11.18% | 12 |

## Observations

- System tested across trending, ranging, high-vol, and stress scenarios.
- Signal generation remains deterministic under all conditions.