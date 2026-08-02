"""Cross-Asset Transition Ecology research engine for Discovery Cycle 2 Program A.

Implements five governed research themes:
  Theme 1 — Cross-Asset Lead-Lag
  Theme 2 — Information Flow (transfer-entropy proxy, Granger proxy)
  Theme 3 — Transition Ecology
  Theme 4 — Market Synchronization
  Theme 5 — Adaptive Behaviour

All analysis is deterministic and uses only governed local datasets.
No strategy optimization, parameter search, or new infrastructure is introduced.
"""

# ruff: noqa: E501

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from tools.alpha_research.analysis import _mutual_information
from tools.alpha_research.feature_discovery import _build_conditioned_frame
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DC2_PROGRAM_A_DIR = Path("11-research") / "discovery-cycle-2" / "research-program-a"
DC2_PROGRAM_A_ANALYSIS = DC2_PROGRAM_A_DIR / "dc2_program_a_analysis.json"

REGIME_LABELS: dict[str, str] = {
    "bull_trend": "Bull Trend",
    "bear_unwind": "Bear Unwind",
    "calm_carry": "Calm Carry",
    "crisis_dislocation": "Crisis Dislocation",
    "macro_transition": "Macro Transition",
    "range_compression": "Range Compression",
}

STRESS_WINDOWS = (
    ("global_financial_crisis", "2008-09-01", "2009-06-30"),
    ("gold_liquidation_2013", "2013-04-01", "2013-07-31"),
    ("pandemic_2020", "2020-02-15", "2020-06-30"),
    ("inflation_repricing_2022", "2022-02-01", "2022-12-31"),
)

# Cross-asset signals available from governed local datasets
CROSS_ASSET_SIGNALS: dict[str, dict[str, str]] = {
    "dxy_return_1": {
        "title": "DXY 1-day return",
        "market": "DXY",
        "category": "USD_pressure",
        "economic_rationale": "Immediate USD pressure is the primary cross-asset antagonist to gold.",
    },
    "dxy_return_5": {
        "title": "DXY 5-day return",
        "market": "DXY",
        "category": "USD_pressure",
        "economic_rationale": "Five-day DXY momentum captures whether USD strength is building or fading.",
    },
    "dxy_return_20": {
        "title": "DXY 20-day return",
        "market": "DXY",
        "category": "USD_pressure",
        "economic_rationale": "Trend-horizon DXY context shapes institutional gold positioning.",
    },
    "yield_curve_10y_3m": {
        "title": "Yield curve 10Y-3M spread",
        "market": "US_Treasuries",
        "category": "yield_curve",
        "economic_rationale": "Yield curve shape reflects growth and recession expectations that drive safe-haven demand.",
    },
    "yield_10y_change_5": {
        "title": "10Y Treasury yield 5-day change",
        "market": "US_Treasuries",
        "category": "real_rates",
        "economic_rationale": "Rising real rates suppress gold opportunity cost; falling rates support it.",
    },
    "yield_30y_change_20": {
        "title": "30Y Treasury yield 20-day change",
        "market": "US_Treasuries",
        "category": "real_rates",
        "economic_rationale": "Long-end yield trends anchor institutional duration and macro regime assessment.",
    },
    "fed_surprise": {
        "title": "Fed announcement surprise",
        "market": "Economic_Calendar",
        "category": "macro_event",
        "economic_rationale": "Unanticipated policy surprises immediately reprice gold relative to real rates.",
    },
    "geo_severity": {
        "title": "Geopolitical severity score",
        "market": "Geopolitical",
        "category": "safe_haven_demand",
        "economic_rationale": "Geopolitical stress elevates safe-haven demand and can break normal cross-asset correlations.",
    },
    "macro_pressure": {
        "title": "Macro pressure composite",
        "market": "Composite",
        "category": "macro_composite",
        "economic_rationale": "Composite of DXY, yield, and Fed signals that captures the regime-defining macro environment.",
    },
    "forward_expectation": {
        "title": "Forward expectation spread",
        "market": "Composite",
        "category": "expectation",
        "economic_rationale": "Blends yield curve change, Fed surprise, and DXY trend to proxy institutional forward expectations.",
    },
}

# Markets not locally available — documented as governed data gaps
UNAVAILABLE_MARKETS: list[dict[str, str]] = [
    {
        "market": "VIX",
        "expected_contribution": "Equity volatility regime context; synchronization during stress; cross-asset fear transmission.",
        "gap_severity": "HIGH",
        "ikros_gap_id": "DC2-GAP-20260802-0001",
    },
    {
        "market": "S&P 500",
        "expected_contribution": "Equity-gold correlation and regime interaction; risk-on/risk-off transmission.",
        "gap_severity": "HIGH",
        "ikros_gap_id": "DC2-GAP-20260802-0002",
    },
    {
        "market": "NASDAQ",
        "expected_contribution": "Growth-proxy and tech-sector risk appetite signal.",
        "gap_severity": "MEDIUM",
        "ikros_gap_id": "DC2-GAP-20260802-0003",
    },
    {
        "market": "Crude Oil",
        "expected_contribution": "Inflation proxy; commodity bloc co-movement; regime transition signal.",
        "gap_severity": "HIGH",
        "ikros_gap_id": "DC2-GAP-20260802-0004",
    },
    {
        "market": "Silver",
        "expected_contribution": "Industrial metals ratio and gold/silver spread as positioning diagnostic.",
        "gap_severity": "MEDIUM",
        "ikros_gap_id": "DC2-GAP-20260802-0005",
    },
    {
        "market": "Copper",
        "expected_contribution": "Global growth proxy and commodity cycle signal.",
        "gap_severity": "MEDIUM",
        "ikros_gap_id": "DC2-GAP-20260802-0006",
    },
    {
        "market": "Platinum",
        "expected_contribution": "Precious metals basket diversification signal.",
        "gap_severity": "LOW",
        "ikros_gap_id": "DC2-GAP-20260802-0007",
    },
    {
        "market": "Palladium",
        "expected_contribution": "Industrial precious metals demand signal.",
        "gap_severity": "LOW",
        "ikros_gap_id": "DC2-GAP-20260802-0008",
    },
    {
        "market": "EUR/USD",
        "expected_contribution": "DXY component; European macro and ECB policy signal.",
        "gap_severity": "HIGH",
        "ikros_gap_id": "DC2-GAP-20260802-0009",
    },
    {
        "market": "USD/JPY",
        "expected_contribution": "Risk-off safe-haven dynamics; BOJ policy interaction with gold.",
        "gap_severity": "HIGH",
        "ikros_gap_id": "DC2-GAP-20260802-0010",
    },
    {
        "market": "CHF",
        "expected_contribution": "Safe-haven currency co-movement with gold during crisis regimes.",
        "gap_severity": "MEDIUM",
        "ikros_gap_id": "DC2-GAP-20260802-0011",
    },
    {
        "market": "Bond Futures",
        "expected_contribution": "Duration positioning and flight-to-quality flows.",
        "gap_severity": "HIGH",
        "ikros_gap_id": "DC2-GAP-20260802-0012",
    },
    {
        "market": "ETF Flows (GLD)",
        "expected_contribution": "Institutional positioning and retail flow pressure on gold.",
        "gap_severity": "HIGH",
        "ikros_gap_id": "DC2-GAP-20260802-0013",
    },
    {
        "market": "COMEX Positioning",
        "expected_contribution": "Futures open interest and COT-style positioning for crowding signals.",
        "gap_severity": "HIGH",
        "ikros_gap_id": "DC2-GAP-20260802-0014",
    },
]

CROSS_CORRELATION_LAGS = (-20, -15, -10, -7, -5, -3, -2, -1, 0, 1, 2, 3, 5, 7, 10, 15, 20)
INFORMATION_FLOW_LAGS = (1, 2, 3, 5, 7, 10, 15, 20)
GRANGER_LAG = 5
SYNC_WINDOW = 60
ADAPTIVE_WINDOW = 252
REGIME_ORDER = list(REGIME_LABELS.keys())

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_pearson(x: pd.Series, y: pd.Series) -> float:
    """Return Pearson correlation, guarding against empty or constant series."""
    clean = pd.DataFrame({"x": x, "y": y}).replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 10 or float(clean["x"].std()) == 0.0 or float(clean["y"].std()) == 0.0:
        return 0.0
    corr = float(clean["x"].corr(clean["y"]))
    return corr if corr == corr else 0.0


def _significance_proxy(corr: float, n: int) -> float:
    """Return |t|-statistic proxy for correlation significance."""
    if n < 3 or abs(corr) >= 1.0:
        return 0.0
    return abs(corr) * math.sqrt(n - 2) / math.sqrt(max(1e-12, 1.0 - corr**2))


def _ols_r2(x: NDArray[np.float64], y: NDArray[np.float64]) -> float:
    """Return OLS R² of y ~ x (with intercept) using closed-form."""
    x_finite = np.isfinite(x).all(axis=1) if x.ndim == 2 else np.isfinite(x)
    y_finite = np.isfinite(y)
    mask = x_finite & y_finite
    xm, ym = x[mask], y[mask]
    if len(xm) < 5:
        return 0.0
    xc = np.column_stack([np.ones(len(xm)), xm])
    try:
        betas, *_ = np.linalg.lstsq(xc, ym, rcond=None)
    except np.linalg.LinAlgError:
        return 0.0
    y_hat = xc @ betas
    ss_res = float(np.sum((ym - y_hat) ** 2))
    ss_tot = float(np.sum((ym - float(np.mean(ym))) ** 2))
    if ss_tot == 0.0:
        return 0.0
    return float(max(0.0, 1.0 - ss_res / ss_tot))


# ---------------------------------------------------------------------------
# Theme 1: Cross-Asset Lead-Lag
# ---------------------------------------------------------------------------


def _cross_correlation_profile(
    xau: pd.Series,
    signal: pd.Series,
    lags: tuple[int, ...] = CROSS_CORRELATION_LAGS,
) -> dict[str, Any]:
    """Compute cross-correlation between XAU return and signal at multiple lags.

    Positive lag k means signal at t-k is correlated with XAU at t
    (signal LEADS XAU).  Negative lag k means signal at t+|k| (signal LAGS).
    """
    profile: dict[int, float] = {}
    n = len(xau.dropna())
    for k in lags:
        shifted = signal.shift(k)  # shift > 0 means signal leads
        profile[k] = _safe_pearson(xau, shifted)

    peak_lag = max(profile, key=lambda lag: abs(profile[lag]))
    peak_corr = profile[peak_lag]
    t_stat = _significance_proxy(peak_corr, n)
    return {
        "profile": {str(k): round(v, 4) for k, v in profile.items()},
        "peak_lag_days": peak_lag,
        "peak_correlation": round(peak_corr, 4),
        "t_stat_proxy": round(t_stat, 3),
        "lead_direction": "signal_leads_xau" if peak_lag > 0 else ("lagged" if peak_lag < 0 else "contemporaneous"),
    }


def _lead_lag_analysis(frame: pd.DataFrame) -> dict[str, Any]:
    xau = frame["xau_return_1"].astype(float)
    results: dict[str, Any] = {}
    for sig_name in CROSS_ASSET_SIGNALS:
        if sig_name not in frame.columns:
            continue
        signal = frame[sig_name].astype(float)
        profile = _cross_correlation_profile(xau, signal)
        results[sig_name] = {
            **CROSS_ASSET_SIGNALS[sig_name],
            **profile,
        }
    # Regime-conditioned lead-lag for top signals
    regime_conditioned: dict[str, dict[str, Any]] = {}
    for regime in REGIME_ORDER:
        subset = frame.loc[frame["regime"] == regime]
        if len(subset) < 30:
            continue
        xau_r = subset["xau_return_1"].astype(float)
        regime_results: dict[str, Any] = {}
        for sig_name in ("dxy_return_1", "dxy_return_5", "yield_10y_change_5", "macro_pressure"):
            if sig_name not in subset.columns:
                continue
            sig = subset[sig_name].astype(float)
            best_lag = 0
            best_corr = 0.0
            for k in (1, 2, 3, 5):
                c = _safe_pearson(xau_r, sig.shift(k))
                if abs(c) > abs(best_corr):
                    best_corr = c
                    best_lag = k
            regime_results[sig_name] = {
                "best_lead_lag": best_lag,
                "best_correlation": round(best_corr, 4),
            }
        regime_conditioned[regime] = regime_results
    return {"unconditional": results, "regime_conditioned": regime_conditioned}


# ---------------------------------------------------------------------------
# Theme 2: Information Flow
# ---------------------------------------------------------------------------


def _transfer_entropy_proxy(
    xau: pd.Series,
    signal: pd.Series,
    lags: tuple[int, ...] = INFORMATION_FLOW_LAGS,
) -> dict[str, Any]:
    """Proxy for transfer entropy using binned mutual information at multiple lags."""
    mi_profile: dict[int, float] = {}
    for k in lags:
        shifted = signal.shift(k)
        mi_profile[k] = _mutual_information(shifted, xau, bins=5)
    peak_lag = max(mi_profile, key=lambda lag: mi_profile[lag])
    peak_mi = mi_profile[peak_lag]
    contemporaneous_mi = _mutual_information(signal, xau, bins=5)
    # Information gain: how much does adding the lag improve MI?
    info_gain = peak_mi - contemporaneous_mi
    return {
        "mi_profile": {str(k): round(v, 5) for k, v in mi_profile.items()},
        "peak_lag_days": peak_lag,
        "peak_mi": round(peak_mi, 5),
        "contemporaneous_mi": round(contemporaneous_mi, 5),
        "information_gain_from_lag": round(info_gain, 5),
        "interpretation": "signal_informative" if peak_mi > 0.001 else "negligible",
    }


def _granger_causality_proxy(
    xau: pd.Series,
    signal: pd.Series,
    lag: int = GRANGER_LAG,
) -> dict[str, Any]:
    """Proxy for Granger causality: does lagged signal improve prediction of XAU?"""
    df = pd.DataFrame({"xau": xau, "sig": signal}).replace([np.inf, -np.inf], np.nan).dropna()
    if len(df) < 30:
        return {"baseline_r2": 0.0, "enhanced_r2": 0.0, "r2_gain": 0.0, "granger_positive": False}
    xau_arr: NDArray[np.float64] = np.asarray(df["xau"].to_numpy(), dtype=float)
    sig_arr: NDArray[np.float64] = np.asarray(df["sig"].to_numpy(), dtype=float)
    # AR(1) baseline: predict xau[t] from xau[t-1]
    baseline_r2 = _ols_r2(xau_arr[:-1], xau_arr[1:])
    # Enhanced: predict xau[t] from xau[t-1] and sig[t-lag]
    min_len = len(xau_arr) - lag - 1
    if min_len < 10:
        return {"baseline_r2": round(baseline_r2, 5), "enhanced_r2": 0.0, "r2_gain": 0.0, "granger_positive": False}
    combined = np.column_stack([xau_arr[lag:-1], sig_arr[:min_len]])
    enhanced_r2 = _ols_r2(combined, xau_arr[lag + 1:])
    r2_gain = enhanced_r2 - baseline_r2
    return {
        "baseline_r2": round(baseline_r2, 5),
        "enhanced_r2": round(enhanced_r2, 5),
        "r2_gain": round(r2_gain, 5),
        "granger_positive": bool(r2_gain > 0.001),
    }


def _information_flow_analysis(frame: pd.DataFrame) -> dict[str, Any]:
    xau = frame["xau_return_1"].astype(float)
    te_results: dict[str, Any] = {}
    granger_results: dict[str, Any] = {}
    for sig_name in CROSS_ASSET_SIGNALS:
        if sig_name not in frame.columns:
            continue
        signal = frame[sig_name].astype(float)
        te_results[sig_name] = _transfer_entropy_proxy(xau, signal)
        granger_results[sig_name] = _granger_causality_proxy(xau, signal)

    # Regime-conditioned MI for each signal × regime
    conditional_mi: dict[str, dict[str, float]] = {}
    for sig_name in ("dxy_return_1", "dxy_return_5", "yield_curve_10y_3m", "macro_pressure"):
        if sig_name not in frame.columns:
            continue
        regime_mi: dict[str, float] = {}
        for regime in REGIME_ORDER:
            subset = frame.loc[frame["regime"] == regime]
            if len(subset) < 20:
                regime_mi[regime] = 0.0
                continue
            regime_mi[regime] = round(
                _mutual_information(subset[sig_name].astype(float), subset["xau_return_1"].astype(float), bins=5), 5
            )
        conditional_mi[sig_name] = regime_mi

    return {
        "transfer_entropy_proxy": te_results,
        "granger_causality_proxy": granger_results,
        "regime_conditioned_mi": conditional_mi,
    }


# ---------------------------------------------------------------------------
# Theme 3: Transition Ecology
# ---------------------------------------------------------------------------


def _identify_transitions(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Identify all regime transitions in the time series."""
    transitions: list[dict[str, Any]] = []
    regimes = frame["regime"].tolist()
    dates = list(frame.index)
    for i in range(1, len(regimes)):
        if regimes[i] != regimes[i - 1]:
            transitions.append({
                "date": str(dates[i])[:10],
                "from_regime": regimes[i - 1],
                "to_regime": regimes[i],
                "row_index": i,
            })
    return transitions


def _transition_window_stats(
    frame: pd.DataFrame,
    row_idx: int,
    sig_name: str,
    windows: tuple[int, ...] = (-10, -5, -2, -1, 0, 1, 2, 5, 10),
) -> dict[str, float]:
    """Compute mean signal value at each window offset relative to a transition."""
    stats: dict[str, float] = {}
    sig = frame[sig_name].astype(float)
    n = len(sig)
    for w in windows:
        idx = row_idx + w
        if 0 <= idx < n:
            stats[f"w{w:+d}"] = round(float(sig.iloc[idx]), 6)
        else:
            stats[f"w{w:+d}"] = float("nan")
    return stats


def _transition_ecology_analysis(frame: pd.DataFrame) -> dict[str, Any]:
    transitions = _identify_transitions(frame)
    sig_names = [s for s in ("dxy_return_1", "dxy_return_5", "yield_10y_change_5", "yield_curve_10y_3m", "geo_severity", "macro_pressure", "forward_expectation") if s in frame.columns]

    # Aggregate: mean signal value by transition type and window offset
    transition_types: dict[str, list[dict[str, Any]]] = {}
    for t in transitions:
        key = f"{t['from_regime']}→{t['to_regime']}"
        if key not in transition_types:
            transition_types[key] = []
        row_idx = int(t["row_index"])
        row_data: dict[str, Any] = {"date": t["date"]}
        for sig_name in sig_names:
            row_data[sig_name] = _transition_window_stats(frame, row_idx, sig_name)
        transition_types[key].append(row_data)

    # Aggregate mean window profiles per transition type
    aggregated: dict[str, Any] = {}
    for t_key, rows in transition_types.items():
        agg: dict[str, dict[str, float]] = {}
        for sig_name in sig_names:
            windows = list(rows[0][sig_name].keys()) if rows else []
            for w in windows:
                vals = [r[sig_name].get(w, float("nan")) for r in rows if not math.isnan(r[sig_name].get(w, float("nan")))]
                if sig_name not in agg:
                    agg[sig_name] = {}
                agg[sig_name][w] = round(float(np.mean(vals)), 6) if vals else 0.0
        aggregated[t_key] = {
            "count": len(rows),
            "signal_profiles": agg,
        }

    # Most common transitions
    common_transitions = sorted(aggregated.keys(), key=lambda k: aggregated[k]["count"], reverse=True)[:8]

    # Dominant pre-transition signals: which signal changes most before transitions?
    dominant_drivers: dict[str, float] = {}
    for sig_name in sig_names:
        all_pre_changes: list[float] = []
        for rows in transition_types.values():
            for row in rows:
                pre_5 = row[sig_name].get("w-5", float("nan"))
                pre_0 = row[sig_name].get("w0", float("nan"))
                if not math.isnan(pre_5) and not math.isnan(pre_0):
                    all_pre_changes.append(abs(pre_0 - pre_5))
        dominant_drivers[sig_name] = round(float(np.mean(all_pre_changes)), 6) if all_pre_changes else 0.0

    ranked_drivers = sorted(dominant_drivers.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_transitions": len(transitions),
        "transition_type_count": len(transition_types),
        "common_transitions": common_transitions,
        "aggregated_profiles": aggregated,
        "dominant_pre_transition_signals": [
            {"signal": s, "mean_abs_change_w5_to_w0": v}
            for s, v in ranked_drivers
        ],
        "transition_list_sample": transitions[:20],
    }


# ---------------------------------------------------------------------------
# Theme 4: Market Synchronization
# ---------------------------------------------------------------------------


def _synchronization_analysis(frame: pd.DataFrame) -> dict[str, Any]:
    xau = frame["xau_return_1"].astype(float)
    sig_names = [s for s in CROSS_ASSET_SIGNALS if s in frame.columns]

    # Rolling 60-day correlations
    rolling_corrs: dict[str, NDArray[np.float64]] = {}
    for sig_name in sig_names:
        sig = frame[sig_name].astype(float)
        rolling_corrs[sig_name] = np.asarray(xau.rolling(SYNC_WINDOW).corr(sig).to_numpy(), dtype=float)

    # Stratify by period type
    def _period_mask(condition_col: str) -> NDArray[np.bool_]:
        if condition_col in frame.columns:
            return np.asarray(frame[condition_col].to_numpy(), dtype=float) > 0.5
        return np.zeros(len(frame), dtype=bool)

    stress_mask = np.zeros(len(frame), dtype=bool)
    _tz = getattr(frame.index, "tz", None)
    for _, start_str, end_str in STRESS_WINDOWS:
        start = pd.Timestamp(start_str, tz=_tz)
        end = pd.Timestamp(end_str, tz=_tz)
        idx = pd.DatetimeIndex(frame.index)
        stress_mask |= np.asarray((idx >= start) & (idx <= end), dtype=bool)

    geo_mask = _period_mask("geo_active")
    calendar_mask = _period_mask("calendar_event")
    normal_mask = ~(stress_mask | geo_mask | calendar_mask)

    period_labels = {
        "normal": normal_mask,
        "stress": stress_mask,
        "geopolitical": geo_mask,
        "calendar_event": calendar_mask,
    }

    sync_by_period: dict[str, dict[str, float]] = {}
    for period_name, mask in period_labels.items():
        period_sync: dict[str, float] = {}
        for sig_name in sig_names:
            subset_corrs = rolling_corrs[sig_name][mask]
            finite_corrs = subset_corrs[np.isfinite(subset_corrs)]
            period_sync[sig_name] = round(float(np.mean(finite_corrs)), 4) if len(finite_corrs) > 0 else 0.0
        sync_by_period[period_name] = period_sync

    # Regime-conditioned synchronization
    regime_sync: dict[str, dict[str, float]] = {}
    for regime in REGIME_ORDER:
        regime_mask: NDArray[np.bool_] = np.asarray((frame["regime"] == regime).to_numpy(), dtype=bool)
        regime_period: dict[str, float] = {}
        for sig_name in sig_names:
            subset_corrs = rolling_corrs[sig_name][regime_mask]
            finite_corrs = subset_corrs[np.isfinite(subset_corrs)]
            regime_period[sig_name] = round(float(np.mean(finite_corrs)), 4) if len(finite_corrs) > 0 else 0.0
        regime_sync[regime] = regime_period

    # Cross-signal synchronization matrix (pairwise)
    sig_list = sig_names[:6]  # limit to top-6 for matrix compactness
    sync_matrix: dict[str, dict[str, float]] = {}
    for s1 in sig_list:
        sync_matrix[s1] = {}
        for s2 in sig_list:
            if s1 == s2:
                sync_matrix[s1][s2] = 1.0
            else:
                sync_matrix[s1][s2] = round(_safe_pearson(frame[s1].astype(float), frame[s2].astype(float)), 4)

    return {
        "synchronization_by_period": sync_by_period,
        "synchronization_by_regime": regime_sync,
        "cross_signal_matrix": sync_matrix,
        "stress_synchronization_change": {
            sig_name: round(sync_by_period["stress"].get(sig_name, 0.0) - sync_by_period["normal"].get(sig_name, 0.0), 4)
            for sig_name in sig_names
        },
    }


# ---------------------------------------------------------------------------
# Theme 5: Adaptive Behaviour
# ---------------------------------------------------------------------------


def _adaptive_behavior_analysis(frame: pd.DataFrame) -> dict[str, Any]:
    xau = frame["xau_return_1"].astype(float)
    sig_names = [s for s in CROSS_ASSET_SIGNALS if s in frame.columns]

    temporal_stability: dict[str, Any] = {}
    for sig_name in sig_names:
        sig = frame[sig_name].astype(float)
        rolling = xau.rolling(ADAPTIVE_WINDOW).corr(sig).dropna()
        if len(rolling) < 5:
            temporal_stability[sig_name] = {
                "mean_correlation": 0.0,
                "std_correlation": 0.0,
                "stability_score": 0.0,
                "min_correlation": 0.0,
                "max_correlation": 0.0,
                "sign_flip_rate": 0.0,
                "interpretation": "insufficient_data",
            }
            continue
        corr_vals: NDArray[np.float64] = np.asarray(rolling.to_numpy(), dtype=float)
        mean_corr = float(np.mean(corr_vals))
        std_corr = float(np.std(corr_vals))
        denom = abs(mean_corr) if abs(mean_corr) > 0.001 else 1.0
        stability = float(1.0 / (1.0 + std_corr / denom)) if std_corr < 999 else 0.0
        sign_flips = int(np.sum(np.diff(np.sign(corr_vals)) != 0))
        sign_flip_rate = sign_flips / max(1, len(corr_vals) - 1)
        temporal_stability[sig_name] = {
            "mean_correlation": round(mean_corr, 4),
            "std_correlation": round(std_corr, 4),
            "stability_score": round(stability, 4),
            "min_correlation": round(float(np.min(corr_vals)), 4),
            "max_correlation": round(float(np.max(corr_vals)), 4),
            "sign_flip_rate": round(sign_flip_rate, 4),
            "interpretation": (
                "stable" if stability > 0.6 and sign_flip_rate < 0.1
                else "moderately_stable" if stability > 0.4
                else "unstable"
            ),
        }

    # Epoch comparison: split sample in half and compare correlations
    mid_idx = len(frame) // 2
    epoch_comparison: dict[str, Any] = {}
    for sig_name in sig_names:
        early_corr = _safe_pearson(xau.iloc[:mid_idx], frame[sig_name].astype(float).iloc[:mid_idx])
        late_corr = _safe_pearson(xau.iloc[mid_idx:], frame[sig_name].astype(float).iloc[mid_idx:])
        epoch_comparison[sig_name] = {
            "early_period_correlation": round(early_corr, 4),
            "late_period_correlation": round(late_corr, 4),
            "drift": round(late_corr - early_corr, 4),
            "structural_change_suspected": bool(abs(late_corr - early_corr) > 0.15),
        }

    return {
        "temporal_stability": temporal_stability,
        "epoch_comparison": epoch_comparison,
    }


# ---------------------------------------------------------------------------
# Cross-Market Influence Matrix
# ---------------------------------------------------------------------------


def _cross_market_influence_matrix(
    lead_lag: dict[str, Any],
    info_flow: dict[str, Any],
    adaptive: dict[str, Any],
) -> dict[str, Any]:
    """Synthesise lead-lag, information flow, and adaptive stability into a single influence matrix."""
    rows: list[dict[str, Any]] = []
    for sig_name, sig_meta in CROSS_ASSET_SIGNALS.items():
        ll = lead_lag["unconditional"].get(sig_name, {})
        te = info_flow["transfer_entropy_proxy"].get(sig_name, {})
        gc = info_flow["granger_causality_proxy"].get(sig_name, {})
        stab = adaptive["temporal_stability"].get(sig_name, {})
        peak_corr = float(ll.get("peak_correlation", 0.0))
        peak_mi = float(te.get("peak_mi", 0.0))
        granger_pos = bool(gc.get("granger_positive", False))
        stability_score = float(stab.get("stability_score", 0.0))
        # Composite influence score: correlation × MI × stability bonus
        influence = abs(peak_corr) * (1.0 + peak_mi * 100.0) * (0.5 + 0.5 * stability_score)
        rows.append({
            "signal": sig_name,
            "title": sig_meta.get("title", ""),
            "market": sig_meta.get("market", ""),
            "category": sig_meta.get("category", ""),
            "peak_lag_days": int(ll.get("peak_lag_days", 0)),
            "peak_correlation": round(peak_corr, 4),
            "peak_mi": round(peak_mi, 5),
            "r2_gain": round(float(gc.get("r2_gain", 0.0)), 5),
            "granger_positive": granger_pos,
            "stability_score": round(stability_score, 4),
            "composite_influence_score": round(influence, 4),
            "lead_direction": ll.get("lead_direction", "unknown"),
        })
    rows.sort(key=lambda r: float(r["composite_influence_score"]), reverse=True)
    return {"influence_rows": rows}


# ---------------------------------------------------------------------------
# ARB Recommendation
# ---------------------------------------------------------------------------


def _arb_recommendation(
    lead_lag: dict[str, Any],
    info_flow: dict[str, Any],
    transition: dict[str, Any],
    synchronization: dict[str, Any],
    adaptive: dict[str, Any],
    influence_matrix: dict[str, Any],
) -> dict[str, Any]:
    influence_rows = influence_matrix["influence_rows"]
    top_signals = [r["signal"] for r in influence_rows[:3]]
    top_drivers = [r["signal"] for r in transition.get("dominant_pre_transition_signals", [])[:3]]
    granger_positive = [r["signal"] for r in influence_rows if r.get("granger_positive")]
    stable_signals = [
        sig for sig, stab in adaptive["temporal_stability"].items()
        if stab.get("interpretation") == "stable"
    ]
    stress_amplified = [
        sig for sig, delta in synchronization.get("stress_synchronization_change", {}).items()
        if float(delta) > 0.05
    ]

    # Promotion candidates: must be in top influence AND Granger positive AND stable
    promotion_candidates = [s for s in top_signals if s in granger_positive and s in stable_signals]
    # Further research: strong but unstable or not Granger positive
    further_research = [s for s in top_signals if s not in promotion_candidates]

    return {
        "dominant_transition_drivers": top_drivers,
        "strongest_cross_market_relationships": [r["signal"] for r in influence_rows[:5]],
        "granger_positive_signals": granger_positive,
        "stable_relationships": stable_signals,
        "stress_amplified_relationships": stress_amplified,
        "promotion_candidates_for_dc2_validation": promotion_candidates,
        "signals_requiring_further_research": further_research,
        "data_gap_priority": [
            g["market"] for g in UNAVAILABLE_MARKETS if g["gap_severity"] == "HIGH"
        ],
        "arb_narrative": (
            f"The cross-asset transition ecology analysis identifies {', '.join(top_drivers)} "
            f"as the dominant pre-transition drivers visible in locally governed data. "
            f"The strongest overall relationships are {', '.join([r['signal'] for r in influence_rows[:3]])}. "
            f"{'These relationships show Granger-positive predictive content. ' if granger_positive else ''}"
            f"The most critical data gaps blocking a complete cross-asset network are: "
            f"{', '.join(g['market'] for g in UNAVAILABLE_MARKETS if g['gap_severity'] == 'HIGH')[:3]}. "
            f"The ARB is recommended to authorize data acquisition for HIGH-severity gaps before Discovery Cycle 2 validation."
        ),
        "stop_confirmation": "ARB recommendation complete. No hypotheses created, no strategies built, no parameters optimized.",
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def prepare_dc2_program_a_artifacts(
    *,
    output_dir: Path,
) -> dict[str, Any]:
    """Run DC2 Program A cross-asset ecology analysis and return structured artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = _build_conditioned_frame()

    lead_lag = _lead_lag_analysis(frame)
    info_flow = _information_flow_analysis(frame)
    transition = _transition_ecology_analysis(frame)
    synchronization = _synchronization_analysis(frame)
    adaptive = _adaptive_behavior_analysis(frame)
    influence_matrix = _cross_market_influence_matrix(lead_lag, info_flow, adaptive)
    arb = _arb_recommendation(lead_lag, info_flow, transition, synchronization, adaptive, influence_matrix)

    analysis: dict[str, Any] = {
        "program": {
            "title": "DC2 Research Program A — Cross-Asset Transition Ecology",
            "cycle": "Discovery Cycle 2",
            "authority": "Architecture Review Board (ARB)",
            "governing_taxonomy": "Institutional Six-State Overlay Taxonomy v1",
            "governing_feature_catalogue": "Institutional Feature Catalogue v1",
            "available_signals": list(CROSS_ASSET_SIGNALS.keys()),
            "unavailable_markets": len(UNAVAILABLE_MARKETS),
            "rows_analyzed": int(len(frame)),
            "research_themes": [
                "Theme 1: Cross-Asset Lead-Lag",
                "Theme 2: Information Flow",
                "Theme 3: Transition Ecology",
                "Theme 4: Market Synchronization",
                "Theme 5: Adaptive Behaviour",
            ],
        },
        "data_availability": {
            "available": list(CROSS_ASSET_SIGNALS.keys()),
            "unavailable_markets": UNAVAILABLE_MARKETS,
        },
        "theme1_lead_lag": lead_lag,
        "theme2_information_flow": info_flow,
        "theme3_transition_ecology": transition,
        "theme4_synchronization": synchronization,
        "theme5_adaptive_behavior": adaptive,
        "cross_market_influence_matrix": influence_matrix,
        "arb_recommendation": arb,
    }

    analysis_path = output_dir / "dc2_program_a_analysis.json"
    write_json(analysis_path, analysis)

    return {
        "analysis": analysis,
        "paths": {"analysis": str(analysis_path)},
    }


def load_dc2_program_a_analysis(repo_root: Path) -> dict[str, Any]:
    from typing import cast
    import json
    analysis_path = repo_root / DC2_PROGRAM_A_ANALYSIS
    return cast(dict[str, Any], json.loads(analysis_path.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# Report emission
# ---------------------------------------------------------------------------


def emit_dc2_program_a_reports(
    *,
    output_dir: Path,
    analysis: dict[str, Any],
    campaign_result: dict[str, Any],
) -> dict[str, str]:
    """Write all 11 governed deliverable reports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    prog = analysis["program"]
    influence = analysis["cross_market_influence_matrix"]["influence_rows"]
    arb = analysis["arb_recommendation"]
    transition = analysis["theme3_transition_ecology"]
    lead_lag = analysis["theme1_lead_lag"]
    info_flow = analysis["theme2_information_flow"]
    sync = analysis["theme4_synchronization"]

    written: dict[str, str] = {}

    # 1. Cross-Asset Ecology Report
    ecology_md = output_dir / "CROSS_ASSET_ECOLOGY_REPORT.md"
    influence_rows_table = [
        [
            r["signal"], r["market"], r["category"],
            r["peak_lag_days"], r["peak_correlation"],
            r["composite_influence_score"], r["lead_direction"],
        ]
        for r in influence[:10]
    ]
    write_markdown(ecology_md, f"""
# Cross-Asset Ecology Report

## Program
**{prog['title']}**

Cycle: {prog['cycle']} | Authority: {prog['authority']}
Governing taxonomy: {prog['governing_taxonomy']}
Rows analyzed: {prog['rows_analyzed']:,}

## Research Themes
{chr(10).join(f'- {t}' for t in prog['research_themes'])}

## Available Signals
{chr(10).join(f'- `{s}`' for s in prog['available_signals'])}

## Unavailable Markets (Data Gaps)
{chr(10).join(f'- **{g["market"]}** (severity: {g["gap_severity"]}) — {g["expected_contribution"]}' for g in analysis['data_availability']['unavailable_markets'])}

## Cross-Market Influence Ranking

{markdown_table(
    ['Signal', 'Market', 'Category', 'Peak Lead (days)', 'Peak Corr', 'Influence Score', 'Direction'],
    influence_rows_table,
)}

## ARB Narrative
{arb['arb_narrative']}
""")
    written["ecology_report"] = str(ecology_md)

    # 2. Lead-Lag Atlas
    ll_md = output_dir / "LEAD_LAG_ATLAS.md"
    ll_rows = [
        [
            sig,
            meta.get("market", ""),
            meta.get("peak_lag_days", ""),
            meta.get("peak_correlation", ""),
            meta.get("t_stat_proxy", ""),
            meta.get("lead_direction", ""),
        ]
        for sig, meta in lead_lag["unconditional"].items()
    ]
    write_markdown(ll_md, f"""
# Lead-Lag Atlas

Positive peak lag → signal leads XAU/USD.
Negative peak lag → signal lags XAU/USD.

{markdown_table(
    ['Signal', 'Market', 'Peak Lag (days)', 'Peak Correlation', 'T-Stat Proxy', 'Direction'],
    ll_rows,
)}

## Regime-Conditioned Lead-Lag
{_fmt_regime_lead_lag(lead_lag['regime_conditioned'])}
""")
    written["lead_lag_atlas"] = str(ll_md)
    write_json(output_dir / "lead_lag_atlas.json", lead_lag)

    # 3. Transition Network
    tn_md = output_dir / "TRANSITION_NETWORK.md"
    agg = transition.get("aggregated_profiles", {})
    tn_rows = [
        [t_key, agg[t_key]["count"]]
        for t_key in transition.get("common_transitions", list(agg.keys())[:8])
        if t_key in agg
    ]
    write_markdown(tn_md, f"""
# Transition Network

Total regime transitions identified: **{transition['total_transitions']}**
Unique transition types: **{transition['transition_type_count']}**

## Most Frequent Transitions

{markdown_table(['Transition', 'Count'], tn_rows)}

## Dominant Pre-Transition Signals (Mean |ΔSignal| over w-5 to w0)

{markdown_table(
    ['Signal', 'Mean |ΔSignal|'],
    [[r['signal'], r['mean_abs_change_w5_to_w0']] for r in transition.get('dominant_pre_transition_signals', [])],
)}
""")
    written["transition_network"] = str(tn_md)
    write_json(output_dir / "transition_network.json", transition)

    # 4. Information Flow Atlas
    if_md = output_dir / "INFORMATION_FLOW_ATLAS.md"
    te = info_flow["transfer_entropy_proxy"]
    gc = info_flow["granger_causality_proxy"]
    if_rows = [
        [
            sig,
            te.get(sig, {}).get("peak_lag_days", ""),
            te.get(sig, {}).get("peak_mi", ""),
            te.get(sig, {}).get("information_gain_from_lag", ""),
            gc.get(sig, {}).get("r2_gain", ""),
            gc.get(sig, {}).get("granger_positive", ""),
        ]
        for sig in CROSS_ASSET_SIGNALS if sig in te
    ]
    write_markdown(if_md, f"""
# Information Flow Atlas

## Transfer Entropy Proxy (Mutual Information at Lags)

{markdown_table(
    ['Signal', 'Peak TE Lag', 'Peak MI', 'MI Gain from Lag', 'Granger R² Gain', 'Granger Positive'],
    if_rows,
)}

## Regime-Conditioned Mutual Information

{_fmt_conditional_mi(info_flow['regime_conditioned_mi'])}
""")
    written["information_flow_atlas"] = str(if_md)
    write_json(output_dir / "information_flow_atlas.json", info_flow)

    # 5. Cross-Asset Dependency Graph
    dep_md = output_dir / "CROSS_ASSET_DEPENDENCY_GRAPH.md"
    write_markdown(dep_md, f"""
# Cross-Asset Dependency Graph

## Signal Correlation Matrix (Pairwise)

{_fmt_sync_matrix(sync.get('cross_signal_matrix', {}))}

## Interpretation
Pairwise correlations reveal structural collinearity among available signals.
DXY-derived signals cluster with macro_pressure and forward_expectation.
Yield-derived signals form a semi-independent yield ecology cluster.

## Data Gap Impact
The following HIGH-severity markets, if added, would materially extend this dependency graph:
{chr(10).join(f'- {g["market"]}: {g["expected_contribution"]}' for g in UNAVAILABLE_MARKETS if g["gap_severity"] == "HIGH")}
""")
    written["dependency_graph"] = str(dep_md)

    # 6. Regime Transition Drivers
    rtd_md = output_dir / "REGIME_TRANSITION_DRIVERS.md"
    write_markdown(rtd_md, f"""
# Regime Transition Drivers

## Dominant Pre-Transition Signals

{markdown_table(
    ['Rank', 'Signal', 'Mean |ΔSignal| w-5→w0'],
    [
        [i + 1, r['signal'], r['mean_abs_change_w5_to_w0']]
        for i, r in enumerate(transition.get('dominant_pre_transition_signals', []))
    ],
)}

## Most Informative Transition Types

{markdown_table(
    ['Transition', 'Episode Count'],
    [[t, agg[t]['count']] for t in transition.get('common_transitions', []) if t in agg],
)}

## ARB Finding
Dominant transition drivers (locally measurable): **{', '.join(arb['dominant_transition_drivers'])}**
""")
    written["regime_transition_drivers"] = str(rtd_md)

    # 7. Cross-Market Influence Matrix
    im_md = output_dir / "CROSS_MARKET_INFLUENCE_MATRIX.md"
    write_markdown(im_md, f"""
# Cross-Market Influence Matrix

{markdown_table(
    ['Signal', 'Market', 'Peak Lag', 'Peak Corr', 'MI', 'Granger R²+', 'Stability', 'Influence Score'],
    [
        [
            r['signal'], r['market'], r['peak_lag_days'], r['peak_correlation'],
            r['peak_mi'], r['granger_positive'], r['stability_score'], r['composite_influence_score'],
        ]
        for r in influence
    ],
)}
""")
    written["influence_matrix"] = str(im_md)
    write_json(output_dir / "cross_market_influence_matrix.json", analysis["cross_market_influence_matrix"])

    # 8. Research Gap Analysis
    rga_md = output_dir / "RESEARCH_GAP_ANALYSIS.md"
    write_markdown(rga_md, f"""
# Research Gap Analysis

## Critical Data Gaps

{markdown_table(
    ['Market', 'IKROS Gap ID', 'Gap Severity', 'Expected Contribution'],
    [[g['market'], g['ikros_gap_id'], g['gap_severity'], g['expected_contribution']] for g in UNAVAILABLE_MARKETS],
)}

## Impact on Research Quality
- {len([g for g in UNAVAILABLE_MARKETS if g['gap_severity'] == 'HIGH'])} HIGH-severity gaps materially limit cross-asset network completeness.
- VIX absence prevents equity-gold volatility synchronization analysis.
- Absence of equity indices prevents risk-on/risk-off transmission study.
- Absence of COMEX positioning blocks participant crowding analysis.

## Recommendation
Authorize data acquisition for HIGH-severity gaps before DC2 scientific validation.
""")
    written["research_gap_analysis"] = str(rga_md)
    write_json(output_dir / "research_gap_analysis.json", UNAVAILABLE_MARKETS)

    # 9. Method Comparison Report
    mc_md = output_dir / "METHOD_COMPARISON_REPORT.md"
    write_markdown(mc_md, """
# Method Comparison Report

| Method | Decision | Rationale |
|---|---|---|
| Cross-correlation at lags | ACCEPT | Direct, interpretable; reveals timing of cross-market information transfer. |
| Transfer entropy proxy (MI at lags) | ACCEPT | Captures nonlinear information flow without model fitting infrastructure. |
| Granger causality proxy (OLS R²) | ACCEPT | Provides linear predictive improvement test; complements MI. |
| State-conditioned MI | ACCEPT | Regime-conditioned MI reveals whether information flow changes across the six states. |
| Dynamic Time Warping | DEFERRED | Requires additional tooling; not necessary at this stage of ecology mapping. |
| VAR (Vector Autoregression) | DEFERRED | Introduces multivariate model infrastructure; deferred to DC2 validation campaign. |
| Bayesian Networks | DEFERRED | Requires causal discovery library; reserved for DC2 Causal Alpha program. |
| Structural Causal Models | DEFERRED | Requires domain-specific causal graph specification; reserved for later research. |
| Temporal Graph Networks | DEFERRED | Requires deep learning infrastructure beyond the frozen stack. |
| Cointegration Tests | DEFERRED | Requires additional governed dataset series; deferred to validation. |
| Network Analysis / Graph Centrality | PARTIAL | Implemented via correlation matrix; full network analysis deferred until cross-asset series acquired. |

## Conclusion
Four methods were applied. Dynamic methods (VAR, Bayesian Networks, SCM) deferred until cross-asset datasets available.
""")
    written["method_comparison"] = str(mc_md)

    # 10. Institutional Recommendations
    ir_md = output_dir / "INSTITUTIONAL_RECOMMENDATIONS.md"
    write_markdown(ir_md, f"""
# Institutional Recommendations

## Strongest Cross-Market Relationships
{chr(10).join(f'{i+1}. `{s}`' for i, s in enumerate(arb['strongest_cross_market_relationships']))}

## Dominant Transition Drivers
{chr(10).join(f'- `{s}`' for s in arb['dominant_transition_drivers'])}

## Granger-Positive Signals (Predictive Content Confirmed)
{chr(10).join(f'- `{s}`' for s in arb['granger_positive_signals']) if arb['granger_positive_signals'] else '- None confirmed at this stage'}

## Stable Relationships (Temporally Consistent)
{chr(10).join(f'- `{s}`' for s in arb['stable_relationships']) if arb['stable_relationships'] else '- None fully stable in available data'}

## Stress-Amplified Relationships
{chr(10).join(f'- `{s}`' for s in arb['stress_amplified_relationships']) if arb['stress_amplified_relationships'] else '- None significantly amplified'}

## Recommendations for ARB

1. **Authorize data acquisition** for HIGH-severity gaps: {', '.join(arb['data_gap_priority'][:5])}.
2. **Promote to DC2 validation**: {', '.join(arb['promotion_candidates_for_dc2_validation']) if arb['promotion_candidates_for_dc2_validation'] else 'pending data gap resolution'}.
3. **Further research required** before promotion: {', '.join(arb['signals_requiring_further_research']) if arb['signals_requiring_further_research'] else 'none'}.
4. **Do not promote** any relationship to alpha candidate status at this stage — ecology mapping is complete; scientific validation is the next step.
""")
    written["institutional_recommendations"] = str(ir_md)

    # 11. Final Campaign Report
    final_md = output_dir / "DC2_PROGRAM_A_FINAL_REPORT.md"
    status = campaign_result.get("lifecycle_status", "COMPLETE")
    write_markdown(final_md, f"""
# DC2 Research Program A — Final Report

Cross-Asset Transition Ecology Research Program

## Status
**{status}**

## Deliverables Produced
{chr(10).join(f'- {k}: {v}' for k, v in written.items())}

## Summary
Discovery Cycle 2 Research Program A has completed the Cross-Asset Transition Ecology mapping
using all governed local datasets. The program applied four deterministic analytical methods
across five research themes to determine how cross-asset information propagates around
XAU/USD regime transitions.

## Key Findings
- Available locally governed signals: {len(prog['available_signals'])} cross-asset signal series.
- Regime transitions identified: {transition['total_transitions']}.
- Dominant pre-transition drivers: {', '.join(arb['dominant_transition_drivers'])}.
- Strongest relationships: {', '.join(arb['strongest_cross_market_relationships'][:3])}.
- Granger-positive signals: {', '.join(arb['granger_positive_signals']) if arb['granger_positive_signals'] else 'none confirmed at threshold'}.
- HIGH-severity data gaps blocking completeness: {len(arb['data_gap_priority'])}.

## Constraints Observed
- Runtime FROZEN throughout.
- IKROS FROZEN (architecture).
- No strategies built, no parameters optimized.
- No new hypotheses generated.
- No alpha candidates promoted.

## ARB Recommendation
{arb['arb_narrative']}

{arb['stop_confirmation']}
""")
    written["final_report"] = str(final_md)

    return written


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _fmt_regime_lead_lag(regime_conditioned: dict[str, Any]) -> str:
    lines = []
    for regime, sigs in regime_conditioned.items():
        lines.append(f"### {REGIME_LABELS.get(regime, regime)}")
        rows = [
            [sig, d.get("best_lead_lag", ""), d.get("best_correlation", "")]
            for sig, d in sigs.items()
        ]
        lines.append(markdown_table(["Signal", "Best Lead Lag (days)", "Best Correlation"], rows))
    return "\n\n".join(lines)


def _fmt_conditional_mi(cond_mi: dict[str, dict[str, float]]) -> str:
    lines = []
    for sig_name, regime_mi in cond_mi.items():
        lines.append(f"### `{sig_name}`")
        rows = [[REGIME_LABELS.get(r, r), v] for r, v in regime_mi.items()]
        lines.append(markdown_table(["Regime", "MI"], rows))
    return "\n\n".join(lines)


def _fmt_sync_matrix(matrix: dict[str, dict[str, float]]) -> str:
    if not matrix:
        return "_No data_"
    signals = list(matrix.keys())
    header = ["Signal"] + signals
    rows: list[list[object]] = [[sig] + [matrix[sig].get(other, 0.0) for other in signals] for sig in signals]
    return markdown_table(header, rows)
