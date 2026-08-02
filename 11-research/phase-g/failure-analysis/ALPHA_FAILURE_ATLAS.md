# Alpha Failure Atlas


## IKROS-HYP-20260802-0401 — Expectation-relief bull continuation

**Root cause:** The continuation thesis is strongest only while bull_trend persists; negative transition windows and adverse USD spillovers diluted a positive but modest core effect below the institutional promotion floor.

### Evidence matrix

| Dimension | Signal | Implication |
| --- | --- | --- |
| Statistical signal | mean=0.0051, t=0.9870, p=0.1618 | Positive direction survived, but statistical amplitude remained below promotion strength. |
| Bootstrap robustness | CI=[-0.0035, 0.0136], P(>0)=0.8330 | Confidence interval still touched non-positive territory. |
| Regime dependence | persistent=0.0298, transition=-0.0050, fragility=HIGH | Performance was not equally portable across clean persistent states and transition-overlap states. |
| Temporal degradation | drift=0.4208, sign_changes=0 | Temporal stability weakened enough to block institutional promotion. |
| Out-of-sample replay | events=10, mean=0.0070, win=0.6000 | Recent replay support existed only where event coverage was sufficient. |
| Monte Carlo resilience | median=0.1333, downside_p05=-0.0759 | Path-level variation still exposed a non-trivial downside tail even where the average event sign stayed positive. |
| Sensitivity | positive_variant_ratio=1.0000, return_range=0.0011 | Threshold variants kept the sign positive, but robustness alone was not enough to offset weak aggregate evidence. |
| Cross-asset dependence | DXY low=0.0136, DXY high=-0.0033 | Higher-pressure slice weakened average continuation. |
| Stress windows | worst_window_mean=-0.0194 | Stress episodes remained too sparse or too uneven to establish institutional robustness on their own. |
| Feature interaction gaps | forward_expectation_low=BINDING, regime_return_high=OVER_RESTRICTIVE, xau_return_high=SUPPORTING | Some rule components remained critical, while others looked redundant or over-restrictive. |

### Failure tree

| Level | Node | Evidence |
| --- | --- | --- |
| Root | Institutional promotion failure | Mean return 0.0051, win rate 0.5417. |
| Primary | Regime fragility | Transition fragility=HIGH, transition mean=-0.0050. |
| Primary | Temporal degradation | Concept drift=0.4208, sign changes=0. |
| Secondary | Feature interaction weakness | Redundant or over-restrictive conditions: regime_return_high. |

### Feature gap analysis

| Condition | Base Mean | Drop Mean | Class | Interpretation |
| --- | --- | --- | --- | --- |
| forward_expectation_low | 0.0051 | 0.0034 | BINDING | Removing forward_expectation_low materially weakened the average event return (0.0051 -> 0.0034). |
| regime_return_high | 0.0051 | 0.0060 | OVER_RESTRICTIVE | Removing regime_return_high preserved or improved the mean return while broadening coverage, suggesting that the filter may be too tight. |
| xau_return_high | 0.0051 | 0.0039 | SUPPORTING | Removing xau_return_high changed the result modestly, so the condition still helps explain the mechanism even if it is not the sole driver. |


## IKROS-HYP-20260802-0405 — Policy-shock repricing continuation

**Root cause:** The policy-shock thesis contains a real but shallow edge; it degrades when macro-transition events expand into noisy, high-range follow-through and when the regime handoff remains unresolved after the first shock day.

### Evidence matrix

| Dimension | Signal | Implication |
| --- | --- | --- |
| Statistical signal | mean=0.0017, t=0.9139, p=0.1804 | Positive direction survived, but statistical amplitude remained below promotion strength. |
| Bootstrap robustness | CI=[-0.0013, 0.0048], P(>0)=0.8350 | Confidence interval still touched non-positive territory. |
| Regime dependence | persistent=0.0146, transition=-0.0016, fragility=HIGH | Performance was not equally portable across clean persistent states and transition-overlap states. |
| Temporal degradation | drift=1.6971, sign_changes=2 | Temporal stability weakened enough to block institutional promotion. |
| Out-of-sample replay | events=16, mean=0.0066, win=0.6875 | Recent replay support existed only where event coverage was sufficient. |
| Monte Carlo resilience | median=0.1787, downside_p05=-0.1338 | Path-level variation still exposed a non-trivial downside tail even where the average event sign stayed positive. |
| Sensitivity | positive_variant_ratio=1.0000, return_range=0.0014 | Threshold variants kept the sign positive, but robustness alone was not enough to offset weak aggregate evidence. |
| Cross-asset dependence | DXY low=0.0029, DXY high=0.0005 | Higher-pressure slice weakened average continuation. |
| Stress windows | worst_window_mean=-0.0027 | Stress episodes remained too sparse or too uneven to establish institutional robustness on their own. |
| Feature interaction gaps | shock_abs=BINDING, event_abs=REDUNDANT, trend_align=SUPPORTING, event_align=BINDING | Some rule components remained critical, while others looked redundant or over-restrictive. |

### Failure tree

| Level | Node | Evidence |
| --- | --- | --- |
| Root | Institutional promotion failure | Mean return 0.0017, win rate 0.5354. |
| Primary | Regime fragility | Transition fragility=HIGH, transition mean=-0.0016. |
| Primary | Temporal degradation | Concept drift=1.6971, sign changes=2. |
| Secondary | Feature interaction weakness | Redundant or over-restrictive conditions: event_abs. |

### Feature gap analysis

| Condition | Base Mean | Drop Mean | Class | Interpretation |
| --- | --- | --- | --- | --- |
| shock_abs | 0.0017 | 0.0001 | BINDING | Removing shock_abs materially weakened the average event return (0.0017 -> 0.0001). |
| event_abs | 0.0017 | 0.0017 | REDUNDANT | Removing event_abs left the mean return essentially unchanged, implying that the condition is not adding independent information. |
| trend_align | 0.0017 | 0.0011 | SUPPORTING | Removing trend_align changed the result modestly, so the condition still helps explain the mechanism even if it is not the sole driver. |
| event_align | 0.0017 | -0.0004 | BINDING | Removing event_align materially weakened the average event return (0.0017 -> -0.0004). |


## IKROS-HYP-20260802-0408 — Transition-to-trend handoff

**Root cause:** The handoff thesis never failed on direction, but the sample is too sparse and too transition-specific to satisfy institutional replication standards; most explanatory power comes from identifying the rare macro-to-trend handoff itself, not from the added confirmation filters.

### Evidence matrix

| Dimension | Signal | Implication |
| --- | --- | --- |
| Statistical signal | mean=0.0074, t=0.4041, p=0.3431 | Positive direction survived, but statistical amplitude remained below promotion strength. |
| Bootstrap robustness | CI=[-0.0219, 0.0347], P(>0)=0.7050 | Confidence interval still touched non-positive territory. |
| Regime dependence | persistent=0.0000, transition=0.0074, fragility=ELEVATED | Performance was not equally portable across clean persistent states and transition-overlap states. |
| Temporal degradation | drift=1.3675, sign_changes=2 | Temporal stability weakened enough to block institutional promotion. |
| Out-of-sample replay | events=0, mean=0.0000, win=0.0000 | Recent replay support existed only where event coverage was sufficient. |
| Monte Carlo resilience | median=0.0666, downside_p05=-0.1435 | Path-level variation still exposed a non-trivial downside tail even where the average event sign stayed positive. |
| Sensitivity | positive_variant_ratio=1.0000, return_range=0.0001 | Threshold variants kept the sign positive, but robustness alone was not enough to offset weak aggregate evidence. |
| Cross-asset dependence | DXY low=-0.0109, DXY high=0.0318 | Higher-pressure slice carried stronger average continuation. |
| Stress windows | worst_window_mean=0.0000 | Stress episodes remained too sparse or too uneven to establish institutional robustness on their own. |
| Feature interaction gaps | prior_macro_transition=BINDING, xau_return_positive=REDUNDANT, trend_breakout_positive=REDUNDANT, regime_return_high=OVER_RESTRICTIVE | Some rule components remained critical, while others looked redundant or over-restrictive. |

### Failure tree

| Level | Node | Evidence |
| --- | --- | --- |
| Root | Institutional promotion failure | Mean return 0.0074, win rate 0.7143. |
| Primary | Regime fragility | Transition fragility=ELEVATED, transition mean=0.0074. |
| Primary | Temporal degradation | Concept drift=1.3675, sign changes=2. |
| Secondary | Feature interaction weakness | Redundant or over-restrictive conditions: xau_return_positive, trend_breakout_positive, regime_return_high. |
| Secondary | Episode scarcity | Too few handoff episodes existed to satisfy replication and out-of-sample replay requirements. |

### Feature gap analysis

| Condition | Base Mean | Drop Mean | Class | Interpretation |
| --- | --- | --- | --- | --- |
| prior_macro_transition | 0.0074 | 0.0051 | BINDING | Removing prior_macro_transition materially weakened the average event return (0.0074 -> 0.0051). |
| xau_return_positive | 0.0074 | 0.0074 | REDUNDANT | Removing xau_return_positive left the mean return essentially unchanged, implying that the condition is not adding independent information. |
| trend_breakout_positive | 0.0074 | 0.0074 | REDUNDANT | Removing trend_breakout_positive left the mean return essentially unchanged, implying that the condition is not adding independent information. |
| regime_return_high | 0.0074 | 0.0087 | OVER_RESTRICTIVE | Removing regime_return_high preserved or improved the mean return while broadening coverage, suggesting that the filter may be too tight. |
