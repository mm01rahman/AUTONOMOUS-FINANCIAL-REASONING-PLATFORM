# Cross-Asset Ecology Report

## Program
**DC2 Research Program A — Cross-Asset Transition Ecology**

Cycle: Discovery Cycle 2 | Authority: Architecture Review Board (ARB)
Governing taxonomy: Institutional Six-State Overlay Taxonomy v1
Rows analyzed: 6,257

## Research Themes
- Theme 1: Cross-Asset Lead-Lag
- Theme 2: Information Flow
- Theme 3: Transition Ecology
- Theme 4: Market Synchronization
- Theme 5: Adaptive Behaviour

## Available Signals
- `dxy_return_1`
- `dxy_return_5`
- `dxy_return_20`
- `yield_curve_10y_3m`
- `yield_10y_change_5`
- `yield_30y_change_20`
- `fed_surprise`
- `geo_severity`
- `macro_pressure`
- `forward_expectation`

## Unavailable Markets (Data Gaps)
- **VIX** (severity: HIGH) — Equity volatility regime context; synchronization during stress; cross-asset fear transmission.
- **S&P 500** (severity: HIGH) — Equity-gold correlation and regime interaction; risk-on/risk-off transmission.
- **NASDAQ** (severity: MEDIUM) — Growth-proxy and tech-sector risk appetite signal.
- **Crude Oil** (severity: HIGH) — Inflation proxy; commodity bloc co-movement; regime transition signal.
- **Silver** (severity: MEDIUM) — Industrial metals ratio and gold/silver spread as positioning diagnostic.
- **Copper** (severity: MEDIUM) — Global growth proxy and commodity cycle signal.
- **Platinum** (severity: LOW) — Precious metals basket diversification signal.
- **Palladium** (severity: LOW) — Industrial precious metals demand signal.
- **EUR/USD** (severity: HIGH) — DXY component; European macro and ECB policy signal.
- **USD/JPY** (severity: HIGH) — Risk-off safe-haven dynamics; BOJ policy interaction with gold.
- **CHF** (severity: MEDIUM) — Safe-haven currency co-movement with gold during crisis regimes.
- **Bond Futures** (severity: HIGH) — Duration positioning and flight-to-quality flows.
- **ETF Flows (GLD)** (severity: HIGH) — Institutional positioning and retail flow pressure on gold.
- **COMEX Positioning** (severity: HIGH) — Futures open interest and COT-style positioning for crowding signals.

## Cross-Market Influence Ranking

| Signal | Market | Category | Peak Lead (days) | Peak Corr | Influence Score | Direction |
| --- | --- | --- | --- | --- | --- | --- |
| dxy_return_1 | DXY | USD_pressure | 0 | -0.4003 | 0.3861 | contemporaneous |
| dxy_return_5 | DXY | USD_pressure | -3 | -0.2305 | 0.2207 | lagged |
| macro_pressure | Composite | macro_composite | -3 | 0.2299 | 0.2168 | lagged |
| dxy_return_20 | DXY | USD_pressure | -5 | -0.1052 | 0.0890 | lagged |
| forward_expectation | Composite | expectation | -5 | 0.1052 | 0.0890 | lagged |
| geo_severity | Geopolitical | safe_haven_demand | -1 | 0.0039 | 0.0020 | lagged |
| yield_curve_10y_3m | US_Treasuries | yield_curve | -20 | 0.0000 | 0.0000 | lagged |
| yield_10y_change_5 | US_Treasuries | real_rates | -20 | 0.0000 | 0.0000 | lagged |
| yield_30y_change_20 | US_Treasuries | real_rates | -20 | 0.0000 | 0.0000 | lagged |
| fed_surprise | Economic_Calendar | macro_event | -20 | 0.0000 | 0.0000 | lagged |

## ARB Narrative
The cross-asset transition ecology analysis identifies dxy_return_1, dxy_return_5, yield_10y_change_5 as the dominant pre-transition drivers visible in locally governed data. The strongest overall relationships are dxy_return_1, dxy_return_5, macro_pressure. The most critical data gaps blocking a complete cross-asset network are: VIX. The ARB is recommended to authorize data acquisition for HIGH-severity gaps before Discovery Cycle 2 validation.
