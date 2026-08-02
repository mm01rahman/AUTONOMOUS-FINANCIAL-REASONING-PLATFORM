# Benchmark Comparison Report

**Regime:** full  
**Generated:** 2026-08-01

## Return & Risk Comparison

| Strategy | Total Return | CAGR | Sharpe | Sortino | Max DD | Win Rate | Trades |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **AFRP** | -83.71% | -6.79% | -0.4611 | -0.5561 | 90.03% | 32.39% | 1772 |
| buy_and_hold | 382.46% | 6.29% | 0.2440 | 0.2335 | 32.04% | 100.00% | 1 |
| sma_crossover | 112.31% | 2.96% | 0.0695 | 0.0686 | 64.85% | 38.52% | 135 |
| ema_crossover | 197.22% | 4.31% | 0.1141 | 0.1129 | 35.28% | 32.39% | 213 |
| momentum | -17.57% | -0.75% | -0.3337 | -0.4232 | 46.03% | 34.85% | 792 |
| mean_reversion | -40.79% | -2.01% | -0.5147 | -0.7490 | 53.98% | 57.62% | 361 |
| breakout | -7.61% | -0.31% | -0.3816 | -0.4739 | 32.32% | 40.93% | 645 |

## Key Findings

- AFRP uses the full reasoning pipeline with cost-aware execution.
- All strategies evaluated under identical cost assumptions.
- Benchmark strategies use pure price-action signals.