# Community Detection
## Discovery Cycle 2 Program A Phase 3

### Communities
| Community | Size | Members |
| --- | --- | --- |
| 1 | 7 | dxy_return_1, dxy_return_20, dxy_return_5, forward_expectation, geo_severity, macro_pressure, xau_return_1 |
| 2 | 1 | yield_curve_10y_3m |
| 3 | 1 | yield_10y_change_5 |
| 4 | 1 | yield_30y_change_20 |
| 5 | 1 | fed_surprise |

### Feedback Loops
| Loop | Forward | Backward | Combined |
| --- | --- | --- | --- |
| dxy_return_5 <-> forward_expectation | 1.0000 | 0.4127 | 0.7064 |
| dxy_return_20 <-> dxy_return_5 | 0.4127 | 1.0000 | 0.7064 |
| dxy_return_1 <-> xau_return_1 | 0.7000 | 0.7010 | 0.7005 |
| dxy_return_1 <-> dxy_return_5 | 0.9120 | 0.4327 | 0.6724 |
| dxy_return_1 <-> macro_pressure | 0.9140 | 0.3955 | 0.6548 |
| dxy_return_5 <-> macro_pressure | 0.7000 | 0.5665 | 0.6332 |
| dxy_return_20 <-> geo_severity | 0.5645 | 0.5645 | 0.5645 |
| forward_expectation <-> geo_severity | 0.5645 | 0.5645 | 0.5645 |
| geo_severity <-> macro_pressure | 0.5756 | 0.4478 | 0.5117 |
| dxy_return_20 <-> forward_expectation | 0.5000 | 0.5000 | 0.5000 |
