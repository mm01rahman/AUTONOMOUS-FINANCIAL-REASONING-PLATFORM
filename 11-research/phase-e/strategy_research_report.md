# Phase E Strategy Research

## Alpha hypotheses evaluated

- Trend Following
- Mean Reversion
- Liquidity Sweep
- Macro-only
- Technical-only
- Hybrid
- Frozen baseline comparator (`tools.backtest.engine.BacktestEngine`)

## Strategy comparison

| Strategy | Full Return | Full Sharpe | Full Sortino | Full Max DD | Full Expectancy | WF Sharpe | WF Positive Fold Ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline Afrp | 0.3473 | -0.9210 | -0.9752 | 0.1385 | -9.6702 | -0.9613 | 0.3500 |
| Trend Following | 0.0800 | -2.2123 | -2.5283 | 0.0708 | -9.8223 | -0.8174 | 0.4000 |
| Mean Reversion | -0.0837 | -3.1676 | -3.8617 | 0.1160 | -12.7048 | -3.2663 | 0.0000 |
| Liquidity Sweep | -0.0230 | -12.2689 | -10.7595 | 0.0303 | -4.8299 | -12.2382 | 0.0000 |
| Macro Only | -0.0817 | -2.1270 | -2.5097 | 0.1090 | -12.8278 | -1.9781 | 0.0000 |
| Technical Only | 0.1676 | -1.1615 | -1.3074 | 0.1080 | -13.2980 | -0.4131 | 0.3000 |
| Hybrid | 0.0972 | -2.0617 | -2.3785 | 0.0650 | -9.8338 | -1.5117 | 0.0500 |

Best walk-forward candidate: **Technical Only**.
