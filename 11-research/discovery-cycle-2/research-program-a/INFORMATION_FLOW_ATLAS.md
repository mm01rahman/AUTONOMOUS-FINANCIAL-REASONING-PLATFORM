# Information Flow Atlas

## Transfer Entropy Proxy (Mutual Information at Lags)

| Signal | Peak TE Lag | Peak MI | MI Gain from Lag | Granger R² Gain | Granger Positive |
| --- | --- | --- | --- | --- | --- |
| dxy_return_1 | 20 | 0.0009 | -0.0712 | 0.0002 | False |
| dxy_return_5 | 7 | 0.0012 | -0.0104 | 0.0007 | False |
| dxy_return_20 | 5 | 0.0009 | -0.0031 | 0.0003 | False |
| yield_curve_10y_3m | 1 | 0.0000 | 0.0000 | -0.0000 | False |
| yield_10y_change_5 | 1 | 0.0000 | 0.0000 | -0.0000 | False |
| yield_30y_change_20 | 1 | 0.0000 | 0.0000 | -0.0000 | False |
| fed_surprise | 1 | 0.0000 | 0.0000 | -0.0000 | False |
| geo_severity | 1 | 0.0002 | -0.0000 | 0.0000 | False |
| macro_pressure | 3 | 0.0010 | -0.0108 | 0.0007 | False |
| forward_expectation | 5 | 0.0009 | -0.0031 | 0.0003 | False |

## Regime-Conditioned Mutual Information

### `dxy_return_1`

| Regime | MI |
| --- | --- |
| Bull Trend | 0.0000 |
| Bear Unwind | 0.0707 |
| Calm Carry | 0.0697 |
| Crisis Dislocation | 0.0280 |
| Macro Transition | 0.1049 |
| Range Compression | 0.0763 |

### `dxy_return_5`

| Regime | MI |
| --- | --- |
| Bull Trend | 0.0000 |
| Bear Unwind | 0.0101 |
| Calm Carry | 0.0140 |
| Crisis Dislocation | 0.0109 |
| Macro Transition | 0.0491 |
| Range Compression | 0.0053 |

### `yield_curve_10y_3m`

| Regime | MI |
| --- | --- |
| Bull Trend | 0.0000 |
| Bear Unwind | 0.0000 |
| Calm Carry | 0.0000 |
| Crisis Dislocation | 0.0000 |
| Macro Transition | 0.0000 |
| Range Compression | 0.0000 |

### `macro_pressure`

| Regime | MI |
| --- | --- |
| Bull Trend | 0.0000 |
| Bear Unwind | 0.0119 |
| Calm Carry | 0.0173 |
| Crisis Dislocation | 0.0078 |
| Macro Transition | 0.0536 |
| Range Compression | 0.0052 |
