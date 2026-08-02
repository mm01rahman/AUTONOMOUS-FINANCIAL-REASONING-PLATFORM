# Diagnostic Experiment Report


## IKROS-EXP-20260802-0601 — Bull-state persistence replay audit

**Target hypothesis:** IKROS-HYP-20260802-0401

**Research question:** Does H0401 remain directionally valid only when bull_trend persists across the holding window, and is transition overlap the dominant contamination source?

**Scientific motivation:** Campaign 0006 identified transition fragility as the primary reason H0401 failed promotion; this experiment isolates the clean persistent bull subset from overlapping exit windows.

**Experimental design:** Replay the governed H0401 event set and partition events into persistent bull_trend windows versus transition-overlap windows across the same three-day holding period.

**Validation method:** Governed event replay with persistent-versus-transition segmentation on the frozen validation frame.

### Result metrics

| Metric | Value |
| --- | --- |
| persistent_event_count | 7 |
| persistent_mean_return | 0.0298 |
| persistent_win_rate | 1.0000 |
| transition_event_count | 17 |
| transition_mean_return | -0.0050 |
| transition_win_rate | 0.3529 |
| persistent_transition_spread | 0.0349 |

### Findings

| Dimension | Assessment |
| --- | --- |
| Reduces uncertainty | HIGH |
| Economic understanding | True |
| Confidence impact | True |
| Explains failures | True |
| Supports/contradicts | SUPPORTS_CURRENT_HYPOTHESIS |
| Requires additional data | False |
| New explanatory variable | regime persistence versus transition overlap |
| No further work | False |

### Evidence summary

- Persistent bull windows delivered +2.98% average event return with a 100% win rate across 7 governed events.
- Transition-overlap windows delivered -0.50% average event return with only 35.29% wins across 17 events.
- The +3.49 percentage-point persistent-versus-transition spread identifies regime exit contamination as the dominant failure driver.


## IKROS-EXP-20260802-0602 — USD spillover decomposition study

**Target hypothesis:** IKROS-HYP-20260802-0401

**Research question:** Does USD spillover intensity explain why some expectation-relief bull windows continue while others fail?

**Scientific motivation:** Campaign 0006 flagged adverse USD spillovers as a secondary failure driver for H0401; this experiment measures whether low-versus-high DXY pressure cleanly separates the outcomes.

**Experimental design:** Split the governed H0401 events into low and high absolute DXY spillover slices and compare continuation quality without changing the base event rule.

**Validation method:** Median-split diagnostic replay on the frozen H0401 event sample.

### Result metrics

| Metric | Value |
| --- | --- |
| absolute_dxy_median | 0.0053 |
| low_dxy_event_count | 12 |
| low_dxy_mean_return | 0.0136 |
| low_dxy_win_rate | 0.6667 |
| high_dxy_event_count | 12 |
| high_dxy_mean_return | -0.0033 |
| high_dxy_win_rate | 0.4167 |
| low_high_spread | 0.0169 |

### Findings

| Dimension | Assessment |
| --- | --- |
| Reduces uncertainty | MEDIUM |
| Economic understanding | True |
| Confidence impact | True |
| Explains failures | True |
| Supports/contradicts | SUPPORTS_CURRENT_HYPOTHESIS |
| Requires additional data | False |
| New explanatory variable | USD spillover intensity |
| No further work | False |

### Evidence summary

- Low-DXY-spillover H0401 events returned +1.36% on average across 12 events.
- High-DXY-spillover H0401 events returned -0.33% on average across 12 events.
- The 1.69 percentage-point low-versus-high DXY spread shows that benign USD conditions materially improve the continuation mechanism.


## IKROS-EXP-20260802-0603 — Macro-transition branch asymmetry audit

**Target hypothesis:** IKROS-HYP-20260802-0405

**Research question:** Is H0405 supported symmetrically across bullish and bearish policy-shock branches, or is one branch carrying the aggregate signal?

**Scientific motivation:** Campaign 0006 concluded that H0405 was real but shallow, with likely branch imbalance hidden inside the aggregate event result.

**Experimental design:** Replay the governed H0405 event set and evaluate bullish- and bearish-shock branches separately while preserving the original continuation rule.

**Validation method:** Branch-level diagnostic replay on the frozen H0405 event sample.

### Result metrics

| Metric | Value |
| --- | --- |
| bearish_branch_event_count | 8 |
| bearish_branch_mean_return | 0.0031 |
| bearish_branch_win_rate | 0.6250 |
| bullish_branch_event_count | 91 |
| bullish_branch_mean_return | 0.0016 |
| bullish_branch_win_rate | 0.5275 |

### Findings

| Dimension | Assessment |
| --- | --- |
| Reduces uncertainty | MEDIUM |
| Economic understanding | True |
| Confidence impact | True |
| Explains failures | True |
| Supports/contradicts | SUPPORTS_WITH_ASYMMETRY |
| Requires additional data | False |
| New explanatory variable | branch-level shock direction asymmetry |
| No further work | False |

### Evidence summary

- Bearish policy-shock branches produced +0.31% average continuation with a 62.5% win rate, but only across 8 events.
- Bullish policy-shock branches produced +0.16% average continuation with a 52.75% win rate across 91 events.
- The aggregate signal was positive on both branches, but branch imbalance explains why the overall validation result looked shallow.


## IKROS-EXP-20260802-0604 — Wide-range transition contamination study

**Target hypothesis:** IKROS-HYP-20260802-0405

**Research question:** Do wide-range macro-transition windows contaminate H0405 by mixing disorderly shock noise with genuine repricing continuation?

**Scientific motivation:** Campaign 0006 identified high-range post-shock turbulence as a likely reason the policy-shock continuation thesis remained too shallow for promotion.

**Experimental design:** Split the governed H0405 event set into narrow-range and wide-range slices using the frozen event frame and compare continuation quality.

**Validation method:** Median-split contamination audit on the frozen H0405 event sample.

### Result metrics

| Metric | Value |
| --- | --- |
| range_median | 0.0122 |
| narrow_range_event_count | 50 |
| narrow_range_mean_return | 0.0056 |
| narrow_range_win_rate | 0.6000 |
| wide_range_event_count | 49 |
| wide_range_mean_return | -0.0023 |
| wide_range_win_rate | 0.4694 |
| narrow_wide_spread | 0.0079 |

### Findings

| Dimension | Assessment |
| --- | --- |
| Reduces uncertainty | HIGH |
| Economic understanding | True |
| Confidence impact | True |
| Explains failures | True |
| Supports/contradicts | SUPPORTS_CURRENT_HYPOTHESIS |
| Requires additional data | False |
| New explanatory variable | post-shock range quality |
| No further work | False |

### Evidence summary

- Narrow-range macro-transition events returned +0.56% on average with a 60% win rate across 50 events.
- Wide-range macro-transition events returned -0.23% on average with a 46.94% win rate across 49 events.
- The narrow-versus-wide range spread identifies disorderly post-shock turbulence as a key contamination channel for H0405.


## IKROS-EXP-20260802-0605 — Sparse handoff episode expansion audit

**Target hypothesis:** IKROS-HYP-20260802-0408

**Research question:** If H0408 is evaluated as a broader macro-to-bull handoff episode class, does the edge remain positive once over-restrictive confirmation filters are removed from the diagnostic layer?

**Scientific motivation:** Campaign 0006 found that H0408 was dominated by sparse episode coverage; this experiment tests whether the handoff mechanism survives broader governed episode accounting.

**Experimental design:** Compare the original H0408 event set with a broader diagnostic handoff episode universe defined only by macro_transition immediately resolving into bull_trend.

**Validation method:** Episode-expansion replay on the frozen transition-to-bull sequence set.

### Result metrics

| Metric | Value |
| --- | --- |
| base_event_count | 7 |
| base_mean_return | 0.0074 |
| base_win_rate | 0.7143 |
| expanded_event_count | 18 |
| expanded_mean_return | 0.0087 |
| expanded_win_rate | 0.7222 |
| expanded_probability_positive | 0.8880 |
| base_episode_overlap | 7 |

### Findings

| Dimension | Assessment |
| --- | --- |
| Reduces uncertainty | HIGH |
| Economic understanding | True |
| Confidence impact | True |
| Explains failures | True |
| Supports/contradicts | SUPPORTS_WITH_SCOPE_EXPANSION |
| Requires additional data | False |
| New explanatory variable | broader macro-to-bull handoff episode class |
| No further work | False |

### Evidence summary

- Broadening H0408 to all governed macro-to-bull handoff episodes increased coverage from 7 to 18 events without losing directional sign.
- Expanded handoff episodes returned +0.87% on average with a 72.22% win rate, slightly stronger than the base sample.
- All 7 base events remained inside the broadened episode class, showing that Campaign 0005 likely used an over-restrictive confirmation layer rather than discovering a false signal.


## IKROS-EXP-20260802-0606 — Transition sequence replay book

**Target hypothesis:** IKROS-HYP-20260802-0408

**Research question:** Do daily regime sequences following macro-to-bull handoff episodes display enough structural consistency to support eventual re-validation, even without intraday ordering data?

**Scientific motivation:** Campaign 0006 identified unresolved transition-ordering uncertainty; this experiment documents what the frozen daily sequence can and cannot explain.

**Experimental design:** Catalogue the dominant future-regime paths after broadened H0408 handoff episodes and measure how often the follow-through remains bull_trend across the five-day holding window.

**Validation method:** Daily-sequence replay book on the broadened handoff event universe.

### Result metrics

| Metric | Value |
| --- | --- |
| expanded_event_count | 18 |
| mean_future_bull_share | 0.4667 |
| median_future_bull_share | 0.4000 |
| top_path_1 | bull_trend > bull_trend > bull_trend |
| top_path_1_count | 4 |
| top_path_2 | bull_trend > range_compression > range_compression |
| top_path_2_count | 3 |
| top_path_3 | range_compression > bull_trend > bull_trend |
| top_path_3_count | 2 |

### Findings

| Dimension | Assessment |
| --- | --- |
| Reduces uncertainty | MEDIUM |
| Economic understanding | True |
| Confidence impact | False |
| Explains failures | True |
| Supports/contradicts | MIXED_SUPPORT |
| Requires additional data | True |
| New explanatory variable | daily transition-sequence stability |
| No further work | False |

### Evidence summary

- The most common broadened H0408 path was a clean bull_trend continuation, but only 4 times.
- Mean future bull-share across broadened episodes was 46.67%, showing that constructive handoffs exist but do not dominate the full five-day horizon.
- Daily sequence replay reduced uncertainty about path diversity, but it could not close the intraday ordering gap that Campaign 0006 identified as the main blocking issue.
