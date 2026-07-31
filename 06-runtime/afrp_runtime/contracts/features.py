"""Canonical CIO-02 feature identifiers (shared contract vocabulary).

Feature ids are part of the wire vocabulary consumed across layers; they
live in the contracts package so no layer ever imports a sibling layer for
them (EDR-002 / FIT-004).
"""

from __future__ import annotations

# Emitted by L1-FST from quotes/trades.
FEATURE_MID = "mid_price"
FEATURE_SPREAD_BPS = "spread_bps"
FEATURE_LOG_RETURN = "log_return"
FEATURE_EWM_VOL = "ewm_volatility"

# Published by oracle/macro telemetry pipelines.
FEATURE_REAL_YIELD = "macro_real_yield"
FEATURE_DXY_RETURN = "macro_dxy_log_return"
FEATURE_FORWARD_SLOPE = "forward_curve_slope"
FEATURE_SENTIMENT = "positioning_sentiment"
