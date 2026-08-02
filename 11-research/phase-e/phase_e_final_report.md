# AFRP Phase E Final Report

## Alpha hypotheses evaluated

- Trend following persistence in XAU/USD with regime filters.
- Mean reversion after standardized overstretch.
- Liquidity-sweep reversals after failed range breaks.
- Macro-only gold reactions to DXY / rates / policy proxies.
- Technical-only composite momentum/breakout behavior.
- Hybrid world-model fusion over macro, microstructure, liquidity, regime,
  forward, behavioral, and technical signals.

## Feature importance summary

Top features by permutation importance:
macro_pressure, regime_vol_20, micro_momentum, forward_expectation, xau_return_1.

## Decision quality analysis

- Trade count analysed: 3699
- Direction accuracy: 0.5131
- Average regret: 0.0209

## Strategy comparisons

| Strategy | Full Return | Full Sharpe | WF Sharpe | Ruin Prob |
| --- | --- | --- | --- | --- |
| Trend Following | 0.0800 | -2.2123 | -0.8174 | 0.0000 |
| Mean Reversion | -0.0837 | -3.1676 | -3.2663 | 0.0800 |
| Liquidity Sweep | -0.0230 | -12.2689 | -12.2382 | 0.0000 |
| Macro Only | -0.0817 | -2.1270 | -1.9781 | 0.0125 |
| Technical Only | 0.1676 | -1.1615 | -0.4131 | 0.0075 |
| Hybrid | 0.0972 | -2.0617 | -1.5117 | 0.0075 |

## Walk-forward results

Best candidate: **Technical Only** with walk-forward Sharpe
-0.4131 and positive-fold
ratio 0.3000.

## Monte Carlo results

Best candidate ruin probability: 0.0075.

## Regime analysis

Requires regime adaptation: True.

## Parameter optimization summary

Validation-first optimization penalized overfit gaps. Best hybrid overfit gap:
-0.0683.

## FIX or Enhancement work packages created

- WP-IMP-0039 — Phase E Alpha Research & Strategy Evolution Framework.

## Evidence generated

- EXEC-041 under `05-work-packages/WP-IMP-0039/evidence/`.

## Research conclusions

- The frozen baseline remains statistically weak versus all viable candidates.
- Technical Only produced the strongest out-of-sample profile
  among Phase E candidates.
- Promotion still requires every governance bar to pass simultaneously.

## Recommended strategy promotions

- Trend Following: DO NOT PROMOTE — full-sample expectancy not positive; full-sample sharpe not positive enough; full-sample sortino below governance bar; walk-forward out-of-sample edge not positive; insufficient positive walk-forward fold ratio
- Mean Reversion: DO NOT PROMOTE — full-sample expectancy not positive; full-sample sharpe not positive enough; full-sample sortino below governance bar; walk-forward out-of-sample edge not positive; insufficient positive walk-forward fold ratio; parameter search shows overfitting gap
- Liquidity Sweep: DO NOT PROMOTE — full-sample expectancy not positive; full-sample sharpe not positive enough; full-sample sortino below governance bar; walk-forward out-of-sample edge not positive; insufficient positive walk-forward fold ratio
- Macro Only: DO NOT PROMOTE — full-sample expectancy not positive; full-sample sharpe not positive enough; full-sample sortino below governance bar; walk-forward out-of-sample edge not positive; insufficient positive walk-forward fold ratio
- Technical Only: DO NOT PROMOTE — full-sample expectancy not positive; full-sample sharpe not positive enough; full-sample sortino below governance bar; walk-forward out-of-sample edge not positive; insufficient positive walk-forward fold ratio
- Hybrid: DO NOT PROMOTE — full-sample expectancy not positive; full-sample sharpe not positive enough; full-sample sortino below governance bar; walk-forward out-of-sample edge not positive; insufficient positive walk-forward fold ratio

## Overall recommendation

**FAIL**
