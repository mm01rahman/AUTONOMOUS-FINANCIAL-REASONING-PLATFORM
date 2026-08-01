"""Feature engineering for deterministic Phase E alpha research."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

FEATURE_COLUMNS: Sequence[str] = (
    "xau_return_1",
    "xau_return_5",
    "xau_return_20",
    "trend_gap_20_120",
    "trend_gap_30_180",
    "range_pct",
    "range_zscore_20",
    "regime_vol_20",
    "zscore_20",
    "zscore_60",
    "breakout_20",
    "breakout_60",
    "breakdown_20",
    "dxy_return_1",
    "dxy_return_5",
    "dxy_return_20",
    "yield_curve_10y_3m",
    "yield_10y_change_5",
    "yield_30y_change_20",
    "fed_surprise",
    "fed_change_5",
    "macro_pressure",
    "forward_expectation",
    "behavioral_stretch",
    "micro_momentum",
    "geo_severity",
    "geo_active",
    "geo_event_count",
    "regime_return_60",
)


def build_feature_frame(base: pd.DataFrame) -> pd.DataFrame:
    """Build deterministic feature frame and forward-return targets."""
    frame = base.copy()
    close = frame["close"].astype(float)
    high = frame["high"].astype(float)
    low = frame["low"].astype(float)
    dxy = frame["dxy_close"].astype(float)
    fed_actual = frame["fed_actual"].astype(float)
    fed_previous = frame["fed_previous"].astype(float)
    yield_3m = frame["yield_3m"].astype(float)
    yield_10y = frame["yield_10y"].astype(float)
    yield_30y = frame["yield_30y"].astype(float)

    frame["xau_return_1"] = close.pct_change().fillna(0.0)
    frame["xau_return_5"] = close.pct_change(5).fillna(0.0)
    frame["xau_return_20"] = close.pct_change(20).fillna(0.0)
    frame["ema_20"] = close.ewm(span=20, adjust=False).mean()
    frame["ema_120"] = close.ewm(span=120, adjust=False).mean()
    frame["ema_30"] = close.ewm(span=30, adjust=False).mean()
    frame["ema_180"] = close.ewm(span=180, adjust=False).mean()
    frame["trend_gap_20_120"] = (frame["ema_20"] / frame["ema_120"] - 1.0).fillna(0.0)
    frame["trend_gap_30_180"] = (frame["ema_30"] / frame["ema_180"] - 1.0).fillna(0.0)
    frame["range_pct"] = ((high - low) / close.replace(0.0, np.nan)).fillna(0.0)
    frame["range_zscore_20"] = (
        (frame["range_pct"] - frame["range_pct"].rolling(20).mean())
        / frame["range_pct"].rolling(20).std().replace(0.0, np.nan)
    ).fillna(0.0)
    frame["regime_vol_20"] = frame["xau_return_1"].rolling(20).std().bfill().fillna(0.0)
    frame["zscore_20"] = (
        (close - close.rolling(20).mean()) / close.rolling(20).std().replace(0.0, np.nan)
    ).fillna(0.0)
    frame["zscore_60"] = (
        (close - close.rolling(60).mean()) / close.rolling(60).std().replace(0.0, np.nan)
    ).fillna(0.0)
    frame["breakout_20"] = (close / close.rolling(20).max().shift(1) - 1.0).fillna(0.0)
    frame["breakout_60"] = (close / close.rolling(60).max().shift(1) - 1.0).fillna(0.0)
    frame["breakdown_20"] = (close / close.rolling(20).min().shift(1) - 1.0).fillna(0.0)
    frame["dxy_return_1"] = dxy.pct_change().fillna(0.0)
    frame["dxy_return_5"] = dxy.pct_change(5).fillna(0.0)
    frame["dxy_return_20"] = dxy.pct_change(20).fillna(0.0)
    frame["yield_curve_10y_3m"] = (yield_10y - yield_3m).fillna(0.0)
    frame["yield_10y_change_5"] = yield_10y.diff(5).fillna(0.0)
    frame["yield_30y_change_20"] = yield_30y.diff(20).fillna(0.0)
    frame["fed_surprise"] = (fed_actual - fed_previous).fillna(0.0)
    frame["fed_change_5"] = fed_actual.diff(5).fillna(0.0)
    frame["macro_pressure"] = (
        -50.0 * frame["dxy_return_5"]
        - 0.50 * frame["yield_10y_change_5"]
        - 0.25 * frame["fed_change_5"]
        + 0.20 * frame["geo_severity"]
    ).fillna(0.0)
    frame["forward_expectation"] = (
        -0.25 * frame["yield_curve_10y_3m"].diff(5).fillna(0.0)
        - 0.75 * frame["fed_surprise"]
        - 10.0 * frame["dxy_return_20"]
    ).fillna(0.0)
    frame["behavioral_stretch"] = frame["zscore_20"].abs().clip(0.0, 5.0) / 5.0
    frame["micro_momentum"] = (
        (frame["xau_return_1"] / frame["regime_vol_20"].replace(0.0, np.nan))
        .replace([np.inf, -np.inf], 0.0)
        .fillna(0.0)
    )
    frame["regime_return_60"] = close.pct_change(60).fillna(0.0)
    frame["liquidity_sweep_long"] = (
        (low < low.rolling(20).min().shift(1)) & (close > low.rolling(20).min().shift(1))
    ).astype(float)
    frame["liquidity_sweep_short"] = (
        (high > high.rolling(20).max().shift(1)) & (close < high.rolling(20).max().shift(1))
    ).astype(float)
    frame["future_return_5"] = close.shift(-5) / close - 1.0
    frame["future_direction_5"] = np.sign(frame["future_return_5"]).fillna(0.0)
    frame["calendar_event"] = (
        frame["fed_surprise"].abs() > frame["fed_surprise"].abs().quantile(0.90)
    ).astype(float)
    return frame.fillna(0.0)
