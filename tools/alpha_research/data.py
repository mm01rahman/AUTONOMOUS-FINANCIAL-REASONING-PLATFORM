"""Data loading helpers for deterministic Phase E research."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd

_DATASET_ROOT: Final[Path] = Path("C:/Users/mm01r/AFRP-Datasets/processed")


def _load_parquet(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"dataset not found: {path}")
    frame = pd.read_parquet(path)
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError(f"expected DatetimeIndex in {path}")
    return frame.sort_index()


def _severity_to_score(severity: str) -> float:
    mapping = {
        "LOW": 0.25,
        "MEDIUM": 0.50,
        "HIGH": 0.75,
        "CRITICAL": 1.00,
    }
    return mapping.get(severity.upper(), 0.0)


def _align_daily_series(series: pd.Series, target_index: pd.DatetimeIndex) -> pd.Series:
    """Align observations by UTC calendar date while preserving the target timestamps."""
    source = series.copy()
    source.index = pd.DatetimeIndex(source.index).tz_convert("UTC").normalize()
    source = source.groupby(level=0).last()
    target_dates = target_index.tz_convert("UTC").normalize()
    aligned = source.reindex(target_dates).ffill().bfill()
    aligned.index = target_index
    return aligned


def load_research_frame(dataset_root: Path | None = None) -> pd.DataFrame:
    """Load and align all official local Phase E datasets."""
    root = dataset_root or _DATASET_ROOT
    xau = _load_parquet(root / "xauusd" / "xauusd_1d.parquet")
    dxy = _load_parquet(root / "dxy" / "dxy_1d.parquet")
    yields = _load_parquet(root / "yields" / "yields_daily.parquet")
    calendar = _load_parquet(root / "economic_calendar" / "economic_calendar.parquet")
    geopolitical = _load_parquet(root / "geopolitical" / "geopolitical_events.parquet")

    frame = xau[["open", "high", "low", "close", "volume"]].copy()
    target_index = pd.DatetimeIndex(frame.index)
    frame["dxy_close"] = _align_daily_series(dxy["close"], target_index)
    frame["yield_3m"] = _align_daily_series(yields["3M"], target_index)
    frame["yield_5y"] = _align_daily_series(yields["5Y"], target_index)
    frame["yield_10y"] = _align_daily_series(yields["10Y"], target_index)
    frame["yield_30y"] = _align_daily_series(yields["30Y"], target_index)

    policy_rows = calendar.loc[
        calendar["event"].astype(str).str.contains("Fed Funds Rate Proxy", case=False, na=False)
    ]
    if policy_rows.empty:
        raise ValueError("economic calendar has no Fed Funds Rate Proxy observations")
    frame["fed_actual"] = _align_daily_series(policy_rows["actual"], target_index)
    frame["fed_previous"] = _align_daily_series(policy_rows["previous"], target_index)
    frame["geo_active"] = 0.0
    frame["geo_severity"] = 0.0
    frame["geo_event_count"] = 0.0

    for index, row in geopolitical.iterrows():
        if not isinstance(index, pd.Timestamp):
            continue
        end_raw = row.get("end")
        if not isinstance(end_raw, pd.Timestamp):
            continue
        mask = (frame.index >= index) & (frame.index <= end_raw)
        severity = _severity_to_score(str(row.get("severity", "")))
        frame.loc[mask, "geo_active"] = 1.0
        frame.loc[mask, "geo_severity"] = frame.loc[mask, "geo_severity"].clip(lower=severity)
        frame.loc[mask, "geo_event_count"] = frame.loc[mask, "geo_event_count"] + 1.0

    return frame.astype(float)
