"""Market regime definitions for Phase C backtesting."""

from __future__ import annotations

import pandas as pd

REGIMES: dict[str, dict[str, str]] = {
    "gfc_2008": {
        "start": "2008-01-01",
        "end": "2008-12-31",
        "label": "2008 Financial Crisis",
    },
    "gold_bull_2011": {
        "start": "2011-01-01",
        "end": "2011-12-31",
        "label": "2011 Gold Bull Market",
    },
    "gold_collapse_2013": {
        "start": "2013-01-01",
        "end": "2013-12-31",
        "label": "2013 Gold Collapse",
    },
    "covid_2020": {
        "start": "2020-01-01",
        "end": "2020-12-31",
        "label": "2020 COVID",
    },
    "inflation_2022": {
        "start": "2022-01-01",
        "end": "2022-12-31",
        "label": "2022 Inflation Cycle",
    },
    "rate_cycle_2024": {
        "start": "2024-01-01",
        "end": "2024-12-31",
        "label": "2024 Rate Cycle",
    },
    "historical_2025": {
        "start": "2025-01-01",
        "end": "2025-12-31",
        "label": "2025 Historical",
    },
    "available_2026": {
        "start": "2026-01-01",
        "end": "2026-07-31",
        "label": "2026 Available",
    },
}

ROBUSTNESS_SCENARIOS: dict[str, dict[str, str]] = {
    "trending_bull": {
        "start": "2024-01-01",
        "end": "2024-06-30",
        "label": "Trending Bull",
    },
    "trending_bear": {
        "start": "2013-01-01",
        "end": "2013-06-30",
        "label": "Trending Bear",
    },
    "ranging": {
        "start": "2015-01-01",
        "end": "2015-12-31",
        "label": "Ranging Market",
    },
    "high_volatility": {
        "start": "2020-03-01",
        "end": "2020-06-30",
        "label": "High Volatility",
    },
    "low_volatility": {
        "start": "2016-01-01",
        "end": "2016-06-30",
        "label": "Low Volatility",
    },
    "flash_crash": {
        "start": "2013-04-01",
        "end": "2013-04-30",
        "label": "Flash Crash",
    },
    "liquidity_vacuum": {
        "start": "2008-10-01",
        "end": "2008-10-31",
        "label": "Liquidity Vacuum",
    },
    "fomc_cycle": {
        "start": "2022-06-01",
        "end": "2022-09-30",
        "label": "FOMC Rate Cycle",
    },
    "cpi_shock": {
        "start": "2022-01-01",
        "end": "2022-03-31",
        "label": "CPI Shock",
    },
}


def filter_by_regime(df: pd.DataFrame, regime_key: str) -> pd.DataFrame:
    """Return rows of *df* whose DatetimeIndex falls in the given regime window."""
    regime = REGIMES[regime_key]
    start = pd.Timestamp(regime["start"])
    end = pd.Timestamp(regime["end"])
    # Handle tz-aware index gracefully
    idx = df.index
    if hasattr(idx, "tz") and idx.tz is not None:
        start = start.tz_localize(idx.tz)
        end = end.tz_localize(idx.tz)
    mask: pd.Series[bool] = (df.index >= start) & (df.index <= end)  # type: ignore[assignment]
    return df.loc[mask]


def filter_by_dates(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Return rows of *df* between *start* and *end* (inclusive)."""
    ts_start = pd.Timestamp(start)
    ts_end = pd.Timestamp(end)
    idx = df.index
    if hasattr(idx, "tz") and idx.tz is not None:
        ts_start = ts_start.tz_localize(idx.tz)
        ts_end = ts_end.tz_localize(idx.tz)
    mask: pd.Series[bool] = (df.index >= ts_start) & (df.index <= ts_end)  # type: ignore[assignment]
    return df.loc[mask]
