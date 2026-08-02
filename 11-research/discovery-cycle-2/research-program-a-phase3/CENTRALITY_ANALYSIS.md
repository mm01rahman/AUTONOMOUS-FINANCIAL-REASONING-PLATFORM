# Centrality Analysis
## Discovery Cycle 2 Program A Phase 3

| Node | Market | Out Strength | In Strength | Net Flow | Role |
| --- | --- | --- | --- | --- | --- |
| xau_return_1 | XAU/USD | 3.4607 | 1.8121 | 1.6486 | source |
| dxy_return_1 | DXY | 3.9323 | 2.2411 | 1.6912 | source |
| dxy_return_5 | DXY | 3.8801 | 3.4570 | 0.4231 | relay |
| dxy_return_20 | DXY | 2.2252 | 4.2724 | -2.0472 | sink |
| yield_curve_10y_3m | US_Treasuries | 0.0000 | 0.0000 | 0.0000 | intermediate |
| yield_10y_change_5 | US_Treasuries | 0.0000 | 0.0000 | 0.0000 | intermediate |
| yield_30y_change_20 | US_Treasuries | 0.0000 | 0.0000 | 0.0000 | intermediate |
| fed_surprise | Economic_Calendar | 0.0000 | 0.0000 | 0.0000 | intermediate |
| geo_severity | Geopolitical | 2.3744 | 2.4972 | -0.1228 | sink |
| macro_pressure | Composite | 3.7437 | 3.2894 | 0.4543 | relay |
| forward_expectation | Composite | 2.2252 | 4.2724 | -2.0472 | sink |

### Top Sources
dxy_return_1, xau_return_1, macro_pressure, dxy_return_5, yield_curve_10y_3m

### Top Relays
dxy_return_5, macro_pressure, dxy_return_20, forward_expectation, dxy_return_1

### Top Sinks
dxy_return_20, forward_expectation, geo_severity, yield_curve_10y_3m, yield_10y_change_5
