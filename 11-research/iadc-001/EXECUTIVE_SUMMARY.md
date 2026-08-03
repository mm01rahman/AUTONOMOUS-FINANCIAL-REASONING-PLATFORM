# IADC-001 Executive Summary

**Campaign state:** `EVIDENCE_EXHAUSTED_FOR_AVAILABLE_DATA`

AFRP generated and tested **1,080** pre-specified directional hypotheses over
**6,242** daily XAU/USD observations from **2001-08-15** through
**2026-07-02**. Multiple-testing control, temporal split validation,
moving-block bootstrap, and circular-shift placebo testing retained **22**
observational associations. **No causal mechanism was validated.**

The campaign did not create trading rules, optimize entries, connect a broker, or perform
paper/live trading. Supported results remain institutional research candidates until independent
data and causal identification are available.

## Strongest retained associations

| Hypothesis | Driver | Regime | Lag | Horizon | N | Correlation | BH q | Bootstrap sign P |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IADC-HYP-0658 | yield_10y_change_5 | all | 20 | 5 | 6217 | -0.062943 | 0.000043 | 0.996667 |
| IADC-HYP-0662 | yield_10y_change_5 | policy_easing | 20 | 5 | 1869 | -0.112204 | 0.000068 | 1.000000 |
| IADC-HYP-0666 | yield_10y_change_5 | market_stress | 20 | 5 | 617 | -0.187601 | 0.000145 | 1.000000 |
| IADC-HYP-0901 | curve_change_5 | all | 10 | 5 | 6222 | 0.057786 | 0.000249 | 0.983333 |
| IADC-HYP-0552 | yield_10y_change_5 | gold_bear | 0 | 5 | 1868 | -0.095746 | 0.001252 | 0.993333 |
| IADC-HYP-0687 | yield_10y_change_20 | gold_bear | 0 | 5 | 1864 | -0.095153 | 0.001336 | 0.973333 |
| IADC-HYP-0615 | yield_10y_change_5 | gold_bear | 5 | 20 | 1851 | -0.092533 | 0.001935 | 0.953333 |
| IADC-HYP-0579 | yield_10y_change_5 | gold_bear | 1 | 5 | 1867 | -0.091719 | 0.002034 | 1.000000 |
| IADC-HYP-0006 | dxy_return_1 | usd_strength | 0 | 1 | 1872 | -0.088288 | 0.002993 | 1.000000 |
| IADC-HYP-0714 | yield_10y_change_20 | gold_bear | 1 | 5 | 1864 | -0.087529 | 0.003379 | 0.956667 |
| IADC-HYP-0001 | dxy_return_1 | all | 0 | 1 | 6241 | -0.047456 | 0.003626 | 1.000000 |
| IADC-HYP-0531 | yield_10y_change_1 | market_stress | 20 | 5 | 616 | -0.140562 | 0.007973 | 1.000000 |
| IADC-HYP-0902 | curve_change_5 | gold_bull | 10 | 5 | 1873 | 0.080667 | 0.007973 | 0.996667 |
| IADC-HYP-0410 | yield_10y_change_1 | policy_easing | 0 | 1 | 1869 | -0.079936 | 0.008826 | 0.973333 |
| IADC-HYP-0657 | yield_10y_change_5 | market_stress | 20 | 1 | 621 | -0.137844 | 0.009080 | 1.000000 |
| IADC-HYP-0555 | yield_10y_change_5 | usd_strength | 0 | 5 | 1868 | -0.079556 | 0.009139 | 0.976667 |
| IADC-HYP-0406 | yield_10y_change_1 | all | 0 | 1 | 6240 | -0.043201 | 0.009799 | 0.993333 |
| IADC-HYP-0437 | yield_10y_change_1 | policy_easing | 1 | 1 | 1869 | -0.078347 | 0.010016 | 0.986667 |
| IADC-HYP-0083 | dxy_return_1 | gold_bull | 10 | 1 | 1873 | -0.076224 | 0.012617 | 1.000000 |
| IADC-HYP-0705 | yield_10y_change_20 | gold_bear | 1 | 1 | 1868 | -0.069445 | 0.025616 | 0.990000 |

## Mechanism-family disposition

| Mechanism | Family | State | Supported tests | Best evidence | Confidence |
| --- | --- | --- | --- | --- | --- |
| IADC-MECH-001 | curve_expectations | SUPPORTED_ASSOCIATION | 2 | IADC-HYP-0901 | 0.750000 |
| IADC-MECH-002 | nominal_yield_transmission | SUPPORTED_ASSOCIATION | 16 | IADC-HYP-0658 | 0.750000 |
| IADC-MECH-003 | policy_anchor | REJECTED_OR_UNRESOLVED | 0 | IADC-HYP-1020 | 0.500000 |
| IADC-MECH-004 | usd_transmission | SUPPORTED_ASSOCIATION | 4 | IADC-HYP-0006 | 0.750000 |

## Evidence boundaries

| Domain | Available evidence | Required evidence | Decision |
| --- | --- | --- | --- |
| real yields | six-row fixture only | historical TIPS real-yield curve | BLOCKED_BY_DATA |
| inflation surprise | not present | CPI/Core CPI/PCE releases, consensus, and vintages | BLOCKED_BY_DATA |
| FOMC event studies | daily short-rate proxy only | meeting/statement timestamps and expectation surprises | BLOCKED_BY_DATA |
| institutional positioning and ETF transmission | four-to-six-row fixtures only | multi-cycle CFTC and ETF holdings histories | BLOCKED_BY_DATA |
| causal identification | observational daily time series | valid instruments, natural experiments, or identified structural model | NOT_ESTABLISHED |
