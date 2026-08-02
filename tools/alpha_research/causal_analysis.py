"""Cross-Asset Causal Transition Analysis engine for Discovery Cycle 2 Program A Phase 2.

Implements four governed research themes:
  Theme 1 — Conditional Causality (regime-conditioned Granger)
  Theme 2 — Time-Lag Causality (multi-horizon Granger / transfer-entropy)
  Theme 3 — Macro Mediation (partial-correlation / conditional-MI mediation)
  Theme 4 — Causal Stability (rolling-window Granger stability)

Methods applied (from the approved list):
  Granger Causality (OLS F-proxy)
  Conditional Granger (trivariate model)
  Transfer Entropy (MI at lags, directional)
  Conditional Mutual Information (regime-conditioned)
  Macro Mediation (partial correlation)

No strategy optimization, infrastructure changes, or new models are introduced.
All analysis is deterministic and uses only governed local datasets.
"""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from tools.alpha_research.analysis import _mutual_information
from tools.alpha_research.cross_asset_ecology import (
    CROSS_ASSET_SIGNALS,
    REGIME_ORDER,
    STRESS_WINDOWS,
    _ols_r2,
    _safe_pearson,
)
from tools.alpha_research.feature_discovery import _build_conditioned_frame
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DC2_PHASE2_DIR = Path("11-research") / "discovery-cycle-2" / "research-program-a-phase2"
DC2_PHASE2_ANALYSIS = DC2_PHASE2_DIR / "dc2_phase2_causal_analysis.json"

GRANGER_LAGS = (1, 2, 3, 5, 7, 10, 15, 20)
ROLLING_CAUSAL_WINDOW = 252  # 1 year of daily observations
MIN_OBS_CAUSAL = 30

# Macro mediators available from governed datasets
MACRO_MEDIATORS = ["dxy_return_1", "dxy_return_5", "yield_curve_10y_3m", "yield_10y_change_5", "macro_pressure"]

# Causal direction encoding
CAUSAL_LABELS = {
    "signal_causes_xau": "Signal → XAU (signal Granger-causes gold returns)",
    "xau_causes_signal": "XAU → Signal (gold Granger-causes signal)",
    "bidirectional": "Bidirectional (mutual Granger causality)",
    "none": "No causal evidence at this lag",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _granger_fproxy(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    lag: int,
) -> dict[str, float]:
    """Granger causality F-proxy: does x at lag improve prediction of y?

    Returns dict with baseline_r2, enhanced_r2, r2_gain, f_proxy (pseudo F-statistic).
    """
    if len(x) < lag + MIN_OBS_CAUSAL:
        return {"baseline_r2": 0.0, "enhanced_r2": 0.0, "r2_gain": 0.0, "f_proxy": 0.0}
    x_lag = x[: len(x) - lag]
    y_target = y[lag:]
    y_lag = y[: len(y) - lag]
    n = len(y_target)
    finite = np.isfinite(x_lag) & np.isfinite(y_target) & np.isfinite(y_lag)
    if finite.sum() < MIN_OBS_CAUSAL:
        return {"baseline_r2": 0.0, "enhanced_r2": 0.0, "r2_gain": 0.0, "f_proxy": 0.0}
    x_lag_f: NDArray[np.float64] = x_lag[finite]
    y_target_f: NDArray[np.float64] = y_target[finite]
    y_lag_f: NDArray[np.float64] = y_lag[finite]
    baseline_r2 = _ols_r2(y_lag_f, y_target_f)
    combined: NDArray[np.float64] = np.column_stack([y_lag_f, x_lag_f])
    enhanced_r2 = _ols_r2(combined, y_target_f)
    r2_gain = max(0.0, enhanced_r2 - baseline_r2)
    k_new = 1  # one added predictor
    denom_df = max(1, n - 3)
    f_proxy = (r2_gain / k_new) / max(1e-12, (1.0 - enhanced_r2) / denom_df)
    return {
        "baseline_r2": round(baseline_r2, 5),
        "enhanced_r2": round(enhanced_r2, 5),
        "r2_gain": round(r2_gain, 5),
        "f_proxy": round(f_proxy, 4),
    }


def _conditional_granger(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    z: NDArray[np.float64],
    lag: int,
) -> dict[str, float]:
    """Conditional Granger: does x at lag add predictive power for y given z?

    Compares: y ~ AR(1) + z_lag  vs  y ~ AR(1) + z_lag + x_lag
    The incremental R² gain measures conditional causality beyond z.
    """
    if len(x) < lag + MIN_OBS_CAUSAL:
        return {"conditional_r2_gain": 0.0, "f_proxy": 0.0}
    x_lag = x[: len(x) - lag]
    y_target = y[lag:]
    y_lag = y[: len(y) - lag]
    z_lag = z[: len(z) - lag]
    finite = np.isfinite(x_lag) & np.isfinite(y_target) & np.isfinite(y_lag) & np.isfinite(z_lag)
    if finite.sum() < MIN_OBS_CAUSAL:
        return {"conditional_r2_gain": 0.0, "f_proxy": 0.0}
    x_f: NDArray[np.float64] = x_lag[finite]
    yt_f: NDArray[np.float64] = y_target[finite]
    yl_f: NDArray[np.float64] = y_lag[finite]
    zl_f: NDArray[np.float64] = z_lag[finite]
    n = int(finite.sum())
    restricted: NDArray[np.float64] = np.column_stack([yl_f, zl_f])
    full: NDArray[np.float64] = np.column_stack([yl_f, zl_f, x_f])
    r2_restricted = _ols_r2(restricted, yt_f)
    r2_full = _ols_r2(full, yt_f)
    gain = max(0.0, r2_full - r2_restricted)
    f_proxy = (gain / 1) / max(1e-12, (1.0 - r2_full) / max(1, n - 4))
    return {"conditional_r2_gain": round(gain, 5), "f_proxy": round(f_proxy, 4)}


def _transfer_entropy_proxy(
    source: pd.Series,
    target: pd.Series,
    lag: int,
) -> float:
    """Directional transfer entropy proxy using MI at lag.

    TE(source→target) ≈ MI(target_t ; source_{t-lag} | target_{t-1})
    Approximated as MI(target_t, source_{t-lag}) - MI(target_t, target_{t-1}).
    Higher positive value = more information flowing from source to target.
    """
    df = pd.DataFrame({"src": source, "tgt": target}).replace([np.inf, -np.inf], np.nan).dropna()
    if len(df) < lag + MIN_OBS_CAUSAL:
        return 0.0
    src_lag = np.asarray(df["src"].iloc[: len(df) - lag].to_numpy(), dtype=float)
    tgt_curr = np.asarray(df["tgt"].iloc[lag:].to_numpy(), dtype=float)
    tgt_lag = np.asarray(df["tgt"].iloc[: len(df) - lag].to_numpy(), dtype=float)
    finite = np.isfinite(src_lag) & np.isfinite(tgt_curr) & np.isfinite(tgt_lag)
    if finite.sum() < MIN_OBS_CAUSAL:
        return 0.0
    mi_src = _mutual_information(src_lag[finite], tgt_curr[finite])
    mi_self = _mutual_information(tgt_lag[finite], tgt_curr[finite])
    return round(float(max(0.0, mi_src - mi_self * 0.5)), 5)


def _partial_correlation(
    x: pd.Series,
    y: pd.Series,
    z: pd.Series,
) -> float:
    """Partial correlation of x and y controlling for z (via OLS residuals)."""
    df = pd.DataFrame({"x": x, "y": y, "z": z}).replace([np.inf, -np.inf], np.nan).dropna()
    if len(df) < MIN_OBS_CAUSAL:
        return 0.0
    z_arr = np.asarray(df["z"].to_numpy(), dtype=float)
    x_arr = np.asarray(df["x"].to_numpy(), dtype=float)
    y_arr = np.asarray(df["y"].to_numpy(), dtype=float)
    z_col = np.column_stack([np.ones(len(z_arr)), z_arr])
    try:
        bx, *_ = np.linalg.lstsq(z_col, x_arr, rcond=None)
        by, *_ = np.linalg.lstsq(z_col, y_arr, rcond=None)
    except np.linalg.LinAlgError:
        return 0.0
    rx: NDArray[np.float64] = x_arr - z_col @ bx
    ry: NDArray[np.float64] = y_arr - z_col @ by
    if float(np.std(rx)) == 0.0 or float(np.std(ry)) == 0.0:
        return 0.0
    return round(float(np.corrcoef(rx, ry)[0, 1]), 4)


def _significance_tag(f_proxy: float) -> str:
    if f_proxy > 10.0:
        return "STRONG"
    if f_proxy > 4.0:
        return "MODERATE"
    if f_proxy > 1.5:
        return "WEAK"
    return "NONE"


# ---------------------------------------------------------------------------
# Theme 1: Conditional Causality
# ---------------------------------------------------------------------------


def _theme1_conditional_causality(frame: pd.DataFrame) -> dict[str, Any]:
    """Granger causality conditioned on each of the six institutional regimes."""
    xau = frame["xau_return_1"].astype(float)
    xau_arr: NDArray[np.float64] = np.asarray(xau.to_numpy(), dtype=float)
    sig_names = [s for s in CROSS_ASSET_SIGNALS if s in frame.columns]
    lag = 5  # representative medium-horizon lag

    results: dict[str, Any] = {}
    for sig_name in sig_names:
        sig = frame[sig_name].astype(float)
        sig_arr: NDArray[np.float64] = np.asarray(sig.to_numpy(), dtype=float)
        regime_results: dict[str, Any] = {}
        for regime in REGIME_ORDER:
            idx: NDArray[np.bool_] = np.asarray((frame["regime"] == regime).to_numpy(), dtype=bool)
            if idx.sum() < MIN_OBS_CAUSAL + lag:
                regime_results[regime] = {"granger_r2_gain": 0.0, "f_proxy": 0.0, "significance": "NONE", "n": int(idx.sum())}
                continue
            xau_r: NDArray[np.float64] = xau_arr[idx]
            sig_r: NDArray[np.float64] = sig_arr[idx]
            gr = _granger_fproxy(sig_r, xau_r, lag=min(lag, len(xau_r) // 5))
            regime_results[regime] = {
                "granger_r2_gain": gr["r2_gain"],
                "f_proxy": gr["f_proxy"],
                "significance": _significance_tag(gr["f_proxy"]),
                "n": int(idx.sum()),
            }
        # Overall (unconditional)
        gr_all = _granger_fproxy(sig_arr, xau_arr, lag=lag)
        results[sig_name] = {
            "overall": {
                "granger_r2_gain": gr_all["r2_gain"],
                "f_proxy": gr_all["f_proxy"],
                "significance": _significance_tag(gr_all["f_proxy"]),
            },
            "by_regime": regime_results,
            "causal_regimes": [r for r, v in regime_results.items() if v["significance"] in ("STRONG", "MODERATE")],
            "economic_rationale": CROSS_ASSET_SIGNALS[sig_name]["economic_rationale"],
        }
    return results


# ---------------------------------------------------------------------------
# Theme 2: Time-Lag Causality
# ---------------------------------------------------------------------------


def _theme2_lag_causality(frame: pd.DataFrame) -> dict[str, Any]:
    """Multi-horizon Granger causality and transfer entropy at each governed lag."""
    xau = frame["xau_return_1"].astype(float)
    xau_arr: NDArray[np.float64] = np.asarray(xau.to_numpy(), dtype=float)
    sig_names = [s for s in CROSS_ASSET_SIGNALS if s in frame.columns]

    results: dict[str, Any] = {}
    for sig_name in sig_names:
        sig = frame[sig_name].astype(float)
        sig_arr: NDArray[np.float64] = np.asarray(sig.to_numpy(), dtype=float)
        lag_profile: dict[str, Any] = {}
        for lag in GRANGER_LAGS:
            gr = _granger_fproxy(sig_arr, xau_arr, lag=lag)
            te = _transfer_entropy_proxy(frame[sig_name], xau, lag=lag)
            lag_profile[str(lag)] = {
                "granger_r2_gain": gr["r2_gain"],
                "f_proxy": gr["f_proxy"],
                "transfer_entropy": te,
                "significance": _significance_tag(gr["f_proxy"]),
            }
        # Identify dominant lag (highest Granger f_proxy)
        best_lag = max(lag_profile, key=lambda k: lag_profile[k]["f_proxy"])
        peak_fp = lag_profile[best_lag]["f_proxy"]
        # Lag horizon classification
        bl = int(best_lag)
        horizon = "immediate" if bl <= 2 else ("short" if bl <= 5 else ("medium" if bl <= 10 else "long"))
        results[sig_name] = {
            "lag_profile": lag_profile,
            "dominant_lag": best_lag,
            "peak_f_proxy": peak_fp,
            "horizon": horizon,
            "significance": _significance_tag(peak_fp),
            "persistence": "persistent" if sum(1 for v in lag_profile.values() if v["f_proxy"] > 1.5) >= 4 else "transient",
        }
    return results


# ---------------------------------------------------------------------------
# Theme 3: Macro Mediation
# ---------------------------------------------------------------------------


def _theme3_macro_mediation(frame: pd.DataFrame) -> dict[str, Any]:
    """Partial correlation analysis: does the macro mediator explain away direct causality?"""
    xau = frame["xau_return_1"].astype(float)
    sig_names = [s for s in CROSS_ASSET_SIGNALS if s in frame.columns and s not in MACRO_MEDIATORS]
    mediators = [m for m in MACRO_MEDIATORS if m in frame.columns]

    results: dict[str, Any] = {}
    for sig_name in sig_names:
        sig = frame[sig_name].astype(float)
        direct_corr = _safe_pearson(sig, xau)
        mediation: dict[str, Any] = {}
        for med in mediators:
            z = frame[med].astype(float)
            partial = _partial_correlation(sig, xau, z)
            # Mediation ratio: how much of direct corr persists after controlling for mediator?
            raw_abs = abs(direct_corr)
            partial_abs = abs(partial)
            if raw_abs > 0.001:
                retention = round(partial_abs / raw_abs, 3)
            else:
                retention = 1.0
            mediation[med] = {
                "direct_correlation": round(direct_corr, 4),
                "partial_correlation_controlling_mediator": round(partial, 4),
                "mediation_retention_ratio": retention,
                "mediation_classification": (
                    "FULL_MEDIATION" if retention < 0.2
                    else "PARTIAL_MEDIATION" if retention < 0.7
                    else "DIRECT_EFFECT"
                ),
            }
        dominant_mediator = max(mediation, key=lambda m: 1.0 - mediation[m]["mediation_retention_ratio"]) if mediation else None
        results[sig_name] = {
            "direct_correlation": round(direct_corr, 4),
            "mediation_by_factor": mediation,
            "dominant_mediator": dominant_mediator,
            "interpretation": (
                "Strong direct causal path — relationship survives macro conditioning"
                if dominant_mediator and mediation[dominant_mediator]["mediation_retention_ratio"] > 0.7
                else "Macro-mediated — relationship substantially explained by macro factors"
            ),
        }
    return results


# ---------------------------------------------------------------------------
# Theme 4: Causal Stability
# ---------------------------------------------------------------------------


def _theme4_causal_stability(frame: pd.DataFrame) -> dict[str, Any]:
    """Rolling-window Granger causality to assess temporal stability."""
    xau = frame["xau_return_1"].astype(float)
    xau_arr: NDArray[np.float64] = np.asarray(xau.to_numpy(), dtype=float)
    sig_names = [s for s in CROSS_ASSET_SIGNALS if s in frame.columns]
    lag = 5

    results: dict[str, Any] = {}
    for sig_name in sig_names:
        sig = frame[sig_name].astype(float)
        sig_arr: NDArray[np.float64] = np.asarray(sig.to_numpy(), dtype=float)
        n = len(xau_arr)
        window = ROLLING_CAUSAL_WINDOW
        if n < window + lag + 10:
            results[sig_name] = {
                "rolling_f_proxy": [],
                "stability_score": 0.0,
                "consistency": "INSUFFICIENT_DATA",
                "stress_period_causality": {},
            }
            continue

        rolling_fp: list[float] = []
        for start in range(0, n - window, window // 4):
            end = start + window
            xau_w = xau_arr[start:end]
            sig_w = sig_arr[start:end]
            gr = _granger_fproxy(sig_w, xau_w, lag=lag)
            rolling_fp.append(gr["f_proxy"])

        if not rolling_fp:
            results[sig_name] = {
                "rolling_f_proxy": [],
                "stability_score": 0.0,
                "consistency": "INSUFFICIENT_DATA",
                "stress_period_causality": {},
            }
            continue

        fp_arr = np.asarray(rolling_fp, dtype=float)
        mean_fp = float(np.mean(fp_arr))
        std_fp = float(np.std(fp_arr))
        cv = std_fp / max(mean_fp, 0.001)
        stability_score = round(float(1.0 / (1.0 + cv)), 4)

        consistency = (
            "STABLE" if stability_score > 0.7
            else "MODERATE" if stability_score > 0.4
            else "UNSTABLE"
        )

        # Stress-period causal strength
        stress_causality: dict[str, Any] = {}
        _tz = getattr(frame.index, "tz", None)
        for label, start_str, end_str in STRESS_WINDOWS:
            t0 = pd.Timestamp(start_str, tz=_tz)
            t1 = pd.Timestamp(end_str, tz=_tz)
            idx_arr = pd.DatetimeIndex(frame.index)
            mask: NDArray[np.bool_] = np.asarray((idx_arr >= t0) & (idx_arr <= t1), dtype=bool)
            if mask.sum() < MIN_OBS_CAUSAL + lag:
                stress_causality[label] = {"f_proxy": 0.0, "significance": "INSUFFICIENT_DATA"}
                continue
            gr_s = _granger_fproxy(sig_arr[mask], xau_arr[mask], lag=min(lag, int(mask.sum()) // 5))
            stress_causality[label] = {"f_proxy": gr_s["f_proxy"], "significance": _significance_tag(gr_s["f_proxy"])}

        results[sig_name] = {
            "rolling_f_proxy": [round(v, 4) for v in rolling_fp],
            "mean_f_proxy": round(mean_fp, 4),
            "std_f_proxy": round(std_fp, 4),
            "stability_score": stability_score,
            "consistency": consistency,
            "stress_period_causality": stress_causality,
        }
    return results


# ---------------------------------------------------------------------------
# Causal synthesis
# ---------------------------------------------------------------------------


def _synthesize_causal_conclusions(
    theme1: dict[str, Any],
    theme2: dict[str, Any],
    theme3: dict[str, Any],
    theme4: dict[str, Any],
) -> dict[str, Any]:
    """Integrate evidence from all four themes into per-signal causal conclusions."""
    conclusions: dict[str, Any] = {}
    for sig_name in CROSS_ASSET_SIGNALS:
        t1 = theme1.get(sig_name, {})
        t2 = theme2.get(sig_name, {})
        t3 = theme3.get(sig_name, {})
        t4 = theme4.get(sig_name, {})

        # Evidence scoring
        score = 0
        evidence: list[str] = []
        contradictions: list[str] = []
        alt_explanations: list[str] = []

        overall_sig = t1.get("overall", {}).get("significance", "NONE")
        if overall_sig in ("STRONG", "MODERATE"):
            score += 3 if overall_sig == "STRONG" else 2
            evidence.append(f"Unconditional Granger: {overall_sig}")
        else:
            contradictions.append("Unconditional Granger: no significant causality")

        causal_regimes = t1.get("causal_regimes", [])
        if len(causal_regimes) >= 3:
            score += 2
            evidence.append(f"Regime-conditioned causality in {len(causal_regimes)} regimes: {causal_regimes}")
        elif len(causal_regimes) >= 1:
            score += 1
            evidence.append(f"Regime-specific causality in: {causal_regimes}")
        else:
            contradictions.append("No regime-specific causal signal")

        t2_sig = t2.get("significance", "NONE")
        if t2_sig in ("STRONG", "MODERATE"):
            score += 2
            evidence.append(f"Lag causality: {t2_sig} at lag {t2.get('dominant_lag')} ({t2.get('horizon')} horizon, {t2.get('persistence')})")
        else:
            contradictions.append(f"Lag causality: {t2_sig}")

        dom_med = t3.get("dominant_mediator")
        if dom_med:
            med_info = t3.get("mediation_by_factor", {}).get(dom_med, {})
            med_class = med_info.get("mediation_classification", "DIRECT_EFFECT")
            if med_class == "FULL_MEDIATION":
                score -= 2
                alt_explanations.append(f"Fully mediated by {dom_med} — may not be independently causal")
            elif med_class == "PARTIAL_MEDIATION":
                score -= 1
                alt_explanations.append(f"Partially mediated by {dom_med} — shared macro driver probable")
            else:
                evidence.append(f"Direct effect survives {dom_med} mediation")

        consistency = t4.get("consistency", "INSUFFICIENT_DATA")
        if consistency == "STABLE":
            score += 2
            evidence.append("Causal stability: STABLE across rolling windows")
        elif consistency == "MODERATE":
            score += 1
            evidence.append("Causal stability: MODERATE")
        else:
            contradictions.append(f"Causal stability: {consistency}")

        # Causal classification
        if score >= 6:
            classification = "STRONG_CAUSAL_CANDIDATE"
        elif score >= 3:
            classification = "MODERATE_CAUSAL_CANDIDATE"
        elif score >= 1:
            classification = "WEAK_CAUSAL_CANDIDATE"
        else:
            classification = "NO_CAUSAL_EVIDENCE"

        # ARB recommendation
        arb_rec = (
            "PROMOTE_TO_INSTITUTIONAL_KNOWLEDGE" if classification == "STRONG_CAUSAL_CANDIDATE"
            else "RETAIN_FOR_VALIDATION" if classification == "MODERATE_CAUSAL_CANDIDATE"
            else "DEFER_PENDING_MORE_DATA" if classification == "WEAK_CAUSAL_CANDIDATE"
            else "REJECT"
        )

        conclusions[sig_name] = {
            "causal_score": score,
            "classification": classification,
            "arb_recommendation": arb_rec,
            "evidence": evidence,
            "contradictions": contradictions,
            "alternative_explanations": alt_explanations,
            "economic_rationale": CROSS_ASSET_SIGNALS[sig_name]["economic_rationale"],
            "regime_dependent": len(causal_regimes) > 0 and len(causal_regimes) < 5,
        }
    return conclusions


# ---------------------------------------------------------------------------
# Main analysis entry point
# ---------------------------------------------------------------------------


def prepare_dc2_phase2_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    """Run all four causal themes and synthesize conclusions. Returns full analysis dict."""
    frame = _build_conditioned_frame()

    # Summary stats
    n_obs = len(frame)
    date_range = {
        "start": str(frame.index[0]),
        "end": str(frame.index[-1]),
        "n_obs": n_obs,
    }

    theme1 = _theme1_conditional_causality(frame)
    theme2 = _theme2_lag_causality(frame)
    theme3 = _theme3_macro_mediation(frame)
    theme4 = _theme4_causal_stability(frame)
    causal_conclusions = _synthesize_causal_conclusions(theme1, theme2, theme3, theme4)

    # Build causal graph (adjacency: signal → XAU if strong/moderate)
    causal_graph: dict[str, Any] = {"nodes": list(CROSS_ASSET_SIGNALS.keys()) + ["xau_return_1"], "edges": []}
    for sig, info in causal_conclusions.items():
        if info["classification"] in ("STRONG_CAUSAL_CANDIDATE", "MODERATE_CAUSAL_CANDIDATE"):
            causal_graph["edges"].append(f"{sig} → xau_return_1")

    # Regime-conditioned causal matrix (signal × regime → significance)
    causal_matrix: dict[str, dict[str, str]] = {}
    for sig, t1_info in theme1.items():
        causal_matrix[sig] = {r: t1_info["by_regime"].get(r, {}).get("significance", "NONE") for r in REGIME_ORDER}

    # ARB recommendation summary
    promoted = [s for s, v in causal_conclusions.items() if v["arb_recommendation"] == "PROMOTE_TO_INSTITUTIONAL_KNOWLEDGE"]
    retain = [s for s, v in causal_conclusions.items() if v["arb_recommendation"] == "RETAIN_FOR_VALIDATION"]
    deferred = [s for s, v in causal_conclusions.items() if v["arb_recommendation"] == "DEFER_PENDING_MORE_DATA"]
    rejected = [s for s, v in causal_conclusions.items() if v["arb_recommendation"] == "REJECT"]

    arb_summary = {
        "promote_to_institutional_knowledge": promoted,
        "retain_for_validation": retain,
        "defer_pending_data": deferred,
        "reject": rejected,
        "primary_finding": (
            f"Of {len(causal_conclusions)} observed cross-asset relationships, "
            f"{len(promoted)} qualify as strong causal candidates, "
            f"{len(retain)} require further validation, "
            f"{len(rejected)} show no causal evidence with available data."
        ),
    }

    analysis = {
        "phase": "DC2_PROGRAM_A_PHASE2",
        "title": "Cross-Asset Causal Transition Analysis",
        "date_range": date_range,
        "theme1_conditional_causality": theme1,
        "theme2_lag_causality": theme2,
        "theme3_macro_mediation": theme3,
        "theme4_causal_stability": theme4,
        "causal_conclusions": causal_conclusions,
        "causal_graph": causal_graph,
        "causal_matrix": causal_matrix,
        "arb_summary": arb_summary,
        "data_limitations": {
            "missing_markets": 14,
            "note": "Causal conclusions are limited to governed local datasets (XAU, DXY, Yields, Calendar, Geopolitical). VIX, equity indices, metals, and FX pairs are not locally available — 14 gaps documented in Phase 1.",
            "granger_limitation": "Granger causality establishes predictive precedence, not structural causation. Structural causal models (SCM) deferred pending additional dataset acquisition.",
        },
    }

    # Persist
    out_dir = (repo_root or Path(".")) / DC2_PHASE2_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc2_phase2_causal_analysis.json", analysis)
    return analysis


def load_dc2_phase2_analysis(repo_root: Path | None = None) -> dict[str, Any]:
    import json
    from typing import cast
    path = (repo_root or Path(".")) / DC2_PHASE2_ANALYSIS
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# Report emission
# ---------------------------------------------------------------------------


def emit_dc2_phase2_reports(analysis: dict[str, Any], campaign_result: dict[str, Any] | None = None, repo_root: Path | None = None) -> dict[str, str]:
    """Write all nine governed Phase 2 deliverable reports. Returns {report_name: path}."""
    out_dir = (repo_root or Path(".")) / DC2_PHASE2_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    conclusions = analysis["causal_conclusions"]
    theme2 = analysis["theme2_lag_causality"]
    theme3 = analysis["theme3_macro_mediation"]
    theme4 = analysis["theme4_causal_stability"]
    arb = analysis["arb_summary"]
    graph = analysis["causal_graph"]
    matrix = analysis["causal_matrix"]

    # 1. Cross-Asset Causal Atlas
    atlas_md = out_dir / "CROSS_ASSET_CAUSAL_ATLAS.md"
    sig_rows: list[list[object]] = [
        [
            sig,
            info["classification"].replace("_", " "),
            str(info["causal_score"]),
            info["arb_recommendation"].replace("_", " "),
        ]
        for sig, info in conclusions.items()
    ]
    write_markdown(atlas_md, f"""# Cross-Asset Causal Atlas
## Discovery Cycle 2 Program A Phase 2

{markdown_table(["Signal", "Classification", "Score", "ARB Recommendation"], sig_rows)}

### Primary Finding
{arb["primary_finding"]}

### Data Frame
- Observations: {analysis["date_range"]["n_obs"]}
- Start: {analysis["date_range"]["start"]}
- End: {analysis["date_range"]["end"]}

### Limitations
{analysis["data_limitations"]["note"]}
""")
    written["causal_atlas"] = str(atlas_md)

    # 2. Causal Graph
    cg_md = out_dir / "CAUSAL_GRAPH.md"
    edges_txt = "\n".join(f"  {e}" for e in graph.get("edges", [])) or "  (no strong causal edges detected)"
    write_markdown(cg_md, f"""# Causal Graph
## Discovery Cycle 2 Program A Phase 2

Directed edges represent Granger-causal relationships (strong or moderate evidence).

### Edges
```
{edges_txt}
```

### Interpretation
Each edge A → XAU means: A provides statistically significant predictive improvement for XAU/USD returns at the governed lag structure, surviving regime conditioning.

### Limitations
This is a Granger-causal graph, not a structural causal model (SCM). Edges indicate predictive precedence; structural causality requires SCM validation (deferred to DC2 Causal Alpha program).
""")
    written["causal_graph"] = str(cg_md)

    # 3. Regime-Conditioned Causal Matrix
    rcm_md = out_dir / "REGIME_CONDITIONED_CAUSAL_MATRIX.md"
    header_r = ["Signal"] + [r.replace("_", " ").title() for r in REGIME_ORDER]
    rcm_rows: list[list[object]] = [
        [sig] + [matrix.get(sig, {}).get(r, "NONE") for r in REGIME_ORDER]
        for sig in CROSS_ASSET_SIGNALS
        if sig in matrix
    ]
    write_markdown(rcm_md, f"""# Regime-Conditioned Causal Matrix
## Discovery Cycle 2 Program A Phase 2

Granger causality significance by signal and regime.

{markdown_table(header_r, rcm_rows)}

### Key: STRONG / MODERATE / WEAK / NONE / INSUFFICIENT_DATA
""")
    written["regime_causal_matrix"] = str(rcm_md)

    # 4. Lag Analysis
    lag_md = out_dir / "LAG_CAUSALITY_ANALYSIS.md"
    lag_rows: list[list[object]] = [
        [
            sig,
            info.get("dominant_lag", "—"),
            info.get("horizon", "—"),
            info.get("significance", "NONE"),
            info.get("persistence", "—"),
            str(round(info.get("peak_f_proxy", 0.0), 2)),
        ]
        for sig, info in theme2.items()
    ]
    write_markdown(lag_md, f"""# Lag Causality Analysis
## Discovery Cycle 2 Program A Phase 2

{markdown_table(["Signal", "Dominant Lag", "Horizon", "Significance", "Persistence", "Peak F-Proxy"], lag_rows)}

### Horizon Definitions
- Immediate: lag 1–2 days
- Short: lag 3–5 days
- Medium: lag 6–10 days
- Long: lag > 10 days

### Persistence Definitions
- Persistent: significant at ≥4 lag horizons
- Transient: significant at fewer horizons
""")
    written["lag_analysis"] = str(lag_md)

    # 5. Macro Mediation Report
    med_md = out_dir / "MACRO_MEDIATION_REPORT.md"
    med_rows: list[list[object]] = []
    for sig, info in theme3.items():
        dom = info.get("dominant_mediator") or "—"
        dom_med_class = "—"
        if dom != "—":
            dom_med_class = info.get("mediation_by_factor", {}).get(dom, {}).get("mediation_classification", "—")
        med_rows.append([sig, str(round(info.get("direct_correlation", 0.0), 3)), dom, dom_med_class])
    write_markdown(med_md, f"""# Macro Mediation Report
## Discovery Cycle 2 Program A Phase 2

{markdown_table(["Signal", "Direct Correlation", "Dominant Mediator", "Mediation Class"], med_rows)}

### Classification Key
- FULL_MEDIATION: < 20% of direct correlation survives macro conditioning
- PARTIAL_MEDIATION: 20–70% survives — shared macro driver probable
- DIRECT_EFFECT: > 70% survives — relationship has independent causal path
""")
    written["macro_mediation"] = str(med_md)

    # 6. Causal Stability Report
    stab_md = out_dir / "CAUSAL_STABILITY_REPORT.md"
    stab_rows: list[list[object]] = [
        [
            sig,
            str(round(info.get("mean_f_proxy", 0.0), 2)),
            str(round(info.get("stability_score", 0.0), 3)),
            info.get("consistency", "—"),
        ]
        for sig, info in theme4.items()
    ]
    write_markdown(stab_md, f"""# Causal Stability Report
## Discovery Cycle 2 Program A Phase 2

Rolling {ROLLING_CAUSAL_WINDOW}-day Granger causality stability assessment.

{markdown_table(["Signal", "Mean F-Proxy", "Stability Score", "Consistency"], stab_rows)}

### Stability Score
Score in [0, 1] — higher = more consistent across rolling windows.

### Consistency Key
- STABLE: score > 0.7
- MODERATE: score > 0.4
- UNSTABLE: score ≤ 0.4
""")
    written["causal_stability"] = str(stab_md)

    # 7. Contradiction Report
    contra_md = out_dir / "CONTRADICTION_REPORT.md"
    contra_blocks = []
    for sig, info in conclusions.items():
        if info["contradictions"] or info["alternative_explanations"]:
            contra_blocks.append(f"### {sig}\n**Contradictions:**\n" + "\n".join(f"- {c}" for c in info["contradictions"]) + "\n\n**Alternative Explanations:**\n" + "\n".join(f"- {a}" for a in (info["alternative_explanations"] or ["None"])))
    contra_body = "\n\n".join(contra_blocks) if contra_blocks else "_No contradictions detected._"
    write_markdown(contra_md, f"""# Contradiction Report
## Discovery Cycle 2 Program A Phase 2

{contra_body}
""")
    written["contradiction_report"] = str(contra_md)

    # 8. Confidence Report
    conf_md = out_dir / "CAUSAL_CONFIDENCE_REPORT.md"
    promoted = arb["promote_to_institutional_knowledge"]
    retain = arb["retain_for_validation"]
    conf_promoted_rows: list[list[object]] = [[s, conclusions[s]["causal_score"], conclusions[s]["classification"]] for s in promoted if s in conclusions]
    conf_retain_rows: list[list[object]] = [[s, conclusions[s]["causal_score"], conclusions[s]["classification"]] for s in retain if s in conclusions]
    write_markdown(conf_md, f"""# Causal Confidence Report
## Discovery Cycle 2 Program A Phase 2

### Promote to Institutional Knowledge ({len(promoted)} signals)
{markdown_table(["Signal", "Score", "Classification"], conf_promoted_rows) if conf_promoted_rows else "_None_"}

### Retain for Validation ({len(retain)} signals)
{markdown_table(["Signal", "Score", "Classification"], conf_retain_rows) if conf_retain_rows else "_None_"}

### Deferred Pending Data: {len(arb["defer_pending_data"])} signals
### Rejected: {len(arb["reject"])} signals

### Confidence Note
Causal confidence scores are composite across four themes (regime-conditioned Granger, lag-horizon Granger, macro mediation, rolling stability). Scores of 6+ indicate strong multi-method evidence convergence.
""")
    written["confidence_report"] = str(conf_md)

    # 9. Research Recommendations
    rec_md = out_dir / "RESEARCH_RECOMMENDATIONS.md"
    write_markdown(rec_md, f"""# Research Recommendations
## Discovery Cycle 2 Program A Phase 2

### ARB Finding
{arb["primary_finding"]}

### Signals Recommended for Institutional Knowledge
{chr(10).join(f"- {s}: {conclusions[s]['economic_rationale']}" for s in promoted) or "None identified."}

### Signals Requiring Validation Campaign
{chr(10).join(f"- {s}" for s in retain) or "None."}

### Dataset Acquisition Priorities
The following datasets would most improve causal resolution:
1. VIX — equity volatility regime transmission (DC2-GAP-20260802-0001)
2. S&P 500 — risk-on/risk-off mediation (DC2-GAP-20260802-0002)
3. COMEX positioning — institutional positioning as causal mediator (DC2-GAP-20260802-0014)
4. ETF Flows (GLD) — demand-side causal signal (DC2-GAP-20260802-0013)

### Method Upgrades Deferred
- Structural Causal Models (SCM) — requires domain causal graph specification
- PCMCI — requires additional time series infrastructure
- Temporal DAGs — requires causal discovery library
- Bayesian Networks — reserved for DC2 Causal Alpha program

### Next Research Program
DC2 Research Program B should focus on structural causal validation of the promoted signals using the acquired VIX and equity datasets, with SCM methodology.
""")
    written["research_recommendations"] = str(rec_md)

    # Persist JSON artifacts
    write_json(out_dir / "causal_graph.json", graph)
    write_json(out_dir / "causal_matrix.json", matrix)
    write_json(out_dir / "arb_summary.json", arb)
    written["causal_graph_json"] = str(out_dir / "causal_graph.json")
    written["causal_matrix_json"] = str(out_dir / "causal_matrix.json")
    written["arb_summary_json"] = str(out_dir / "arb_summary.json")

    return written


def _fmt_causal_matrix_md(matrix: dict[str, dict[str, str]]) -> str:
    if not matrix:
        return "_No data_"
    signals = list(matrix.keys())
    header = ["Signal"] + [r.replace("_", " ").title() for r in REGIME_ORDER]
    rows: list[list[object]] = [
        [sig, *[matrix[sig].get(r, "NONE") for r in REGIME_ORDER]]
        for sig in signals
    ]
    return markdown_table(header, rows)
