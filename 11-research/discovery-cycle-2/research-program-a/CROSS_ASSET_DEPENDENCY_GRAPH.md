# Cross-Asset Dependency Graph

## Signal Correlation Matrix (Pairwise)

| Signal | dxy_return_1 | dxy_return_5 | dxy_return_20 | yield_curve_10y_3m | yield_10y_change_5 | yield_30y_change_20 |
| --- | --- | --- | --- | --- | --- | --- |
| dxy_return_1 | 1.0000 | 0.4480 | 0.2299 | 0.0000 | 0.0000 | 0.0000 |
| dxy_return_5 | 0.4480 | 1.0000 | 0.5076 | 0.0000 | 0.0000 | 0.0000 |
| dxy_return_20 | 0.2299 | 0.5076 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| yield_curve_10y_3m | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| yield_10y_change_5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| yield_30y_change_20 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |

## Interpretation
Pairwise correlations reveal structural collinearity among available signals.
DXY-derived signals cluster with macro_pressure and forward_expectation.
Yield-derived signals form a semi-independent yield ecology cluster.

## Data Gap Impact
The following HIGH-severity markets, if added, would materially extend this dependency graph:
- VIX: Equity volatility regime context; synchronization during stress; cross-asset fear transmission.
- S&P 500: Equity-gold correlation and regime interaction; risk-on/risk-off transmission.
- Crude Oil: Inflation proxy; commodity bloc co-movement; regime transition signal.
- EUR/USD: DXY component; European macro and ECB policy signal.
- USD/JPY: Risk-off safe-haven dynamics; BOJ policy interaction with gold.
- Bond Futures: Duration positioning and flight-to-quality flows.
- ETF Flows (GLD): Institutional positioning and retail flow pressure on gold.
- COMEX Positioning: Futures open interest and COT-style positioning for crowding signals.
