# Lead-Lag Atlas

Positive peak lag → signal leads XAU/USD.
Negative peak lag → signal lags XAU/USD.

| Signal | Market | Peak Lag (days) | Peak Correlation | T-Stat Proxy | Direction |
| --- | --- | --- | --- | --- | --- |
| dxy_return_1 | DXY | 0 | -0.4003 | 34.5470 | contemporaneous |
| dxy_return_5 | DXY | -3 | -0.2305 | 18.7350 | lagged |
| dxy_return_20 | DXY | -5 | -0.1052 | 8.3650 | lagged |
| yield_curve_10y_3m | US_Treasuries | -20 | 0.0000 | 0.0000 | lagged |
| yield_10y_change_5 | US_Treasuries | -20 | 0.0000 | 0.0000 | lagged |
| yield_30y_change_20 | US_Treasuries | -20 | 0.0000 | 0.0000 | lagged |
| fed_surprise | Economic_Calendar | -20 | 0.0000 | 0.0000 | lagged |
| geo_severity | Geopolitical | -1 | 0.0039 | 0.3120 | lagged |
| macro_pressure | Composite | -3 | 0.2299 | 18.6820 | lagged |
| forward_expectation | Composite | -5 | 0.1052 | 8.3650 | lagged |

## Regime-Conditioned Lead-Lag
### Bull Trend

| Signal | Best Lead Lag (days) | Best Correlation |
| --- | --- | --- |
| dxy_return_1 | 1 | -0.0693 |
| dxy_return_5 | 5 | 0.1316 |
| yield_10y_change_5 | 0 | 0.0000 |
| macro_pressure | 5 | -0.1426 |

### Bear Unwind

| Signal | Best Lead Lag (days) | Best Correlation |
| --- | --- | --- |
| dxy_return_1 | 3 | 0.0236 |
| dxy_return_5 | 1 | 0.0635 |
| yield_10y_change_5 | 0 | 0.0000 |
| macro_pressure | 1 | -0.0712 |

### Calm Carry

| Signal | Best Lead Lag (days) | Best Correlation |
| --- | --- | --- |
| dxy_return_1 | 2 | 0.0833 |
| dxy_return_5 | 5 | 0.0779 |
| yield_10y_change_5 | 0 | 0.0000 |
| macro_pressure | 5 | -0.0908 |

### Crisis Dislocation

| Signal | Best Lead Lag (days) | Best Correlation |
| --- | --- | --- |
| dxy_return_1 | 1 | -0.1320 |
| dxy_return_5 | 3 | 0.1059 |
| yield_10y_change_5 | 0 | 0.0000 |
| macro_pressure | 3 | -0.1076 |

### Macro Transition

| Signal | Best Lead Lag (days) | Best Correlation |
| --- | --- | --- |
| dxy_return_1 | 1 | -0.1461 |
| dxy_return_5 | 1 | -0.1801 |
| yield_10y_change_5 | 0 | 0.0000 |
| macro_pressure | 1 | 0.1833 |

### Range Compression

| Signal | Best Lead Lag (days) | Best Correlation |
| --- | --- | --- |
| dxy_return_1 | 3 | 0.0584 |
| dxy_return_5 | 1 | 0.0764 |
| yield_10y_change_5 | 0 | 0.0000 |
| macro_pressure | 1 | -0.0723 |
