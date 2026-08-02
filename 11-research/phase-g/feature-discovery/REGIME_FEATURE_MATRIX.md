# Regime Feature Matrix

| Regime | Approved Features | Mean Score | Highest-Scoring Feature | Rationale |
| --- | --- | --- | --- | --- |
| Bull Trend | regime_return_60, xau_return_20, breakdown_20, forward_expectation | 5.3034 | regime_return_60 | Persistent upside phases reward carry-aware pullback and expectation features. |
| Bear Unwind | xau_return_20, regime_vol_20, trend_gap_30_180 | 2.4056 | xau_return_20 | Downside liquidation phases reward volatility control and trend persistence filters. |
| Calm Carry | regime_return_60, macro_trend_interaction, regime_vol_20 | 2.1541 | regime_return_60 | Compressed risk-premium phases reward slow-moving regime anchors over fast noise. |
| Crisis Dislocation | breakout_60, breakdown_20, trend_gap_20_120 | 4.6872 | breakout_60 | Shock states reward exhaustion and breakout diagnostics that separate panic from persistence. |
| Macro Transition | xau_return_1, trend_breakout_interaction, sessionless_event_pressure | 1.1125 | xau_return_1 | Policy and event transitions reward short-horizon response features and event-conditioned trend interactions. |
| Range Compression | macro_trend_interaction, regime_vol_20, forward_expectation | 0.3068 | macro_trend_interaction | Sideways states reward context filters that suppress redundant trend and shock features. |
