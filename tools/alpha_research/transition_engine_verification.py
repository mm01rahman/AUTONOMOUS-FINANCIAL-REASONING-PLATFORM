"""Program D Phase 1: Institutional Transition Engine Verification & Falsification."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from tools.alpha_research.cross_asset_ecology import REGIME_ORDER, STRESS_WINDOWS
from tools.alpha_research.feature_discovery import _build_conditioned_frame
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown
from tools.alpha_research.transition_engine import (
    REGIME_TRANSITION_PRIORS,
    prepare_dc2_program_c_phase1_artifacts,
)

DC2_PROGRAM_D_PHASE1_DIR = Path("11-research") / "discovery-cycle-2" / "research-program-d-phase1"
DC2_PROGRAM_D_PHASE1_ANALYSIS = DC2_PROGRAM_D_PHASE1_DIR / "dc2_program_d_verification_analysis.json"

BASELINE_MODELS = [
    "institutional_transition_engine_v1",
    "volatility_only_transition_model",
    "hidden_markov_model",
    "markov_transition_model",
    "technical_trend_transition_heuristic",
    "macro_only_transition_model",
    "random_transition_baseline",
]


def _regime_to_int() -> dict[str, int]:
    return {name: idx for idx, name in enumerate(REGIME_ORDER)}


def _actual_transitions(regimes: pd.Series) -> NDArray[np.bool_]:
    prev = regimes.shift(1)
    return np.asarray((regimes != prev).fillna(False).to_numpy(), dtype=bool)


def _transition_days(mask: NDArray[np.bool_]) -> NDArray[np.int64]:
    return np.asarray(np.where(mask)[0], dtype=np.int64)


def _zscore(series: pd.Series, train_end: int) -> pd.Series:
    base = series.iloc[:train_end].astype(float)
    mu = float(base.mean())
    sigma = float(base.std())
    if sigma <= 1e-9:
        return pd.Series(np.zeros(len(series), dtype=float), index=series.index)
    return (series.astype(float) - mu) / sigma


def _engine_scores(frame: pd.DataFrame, train_end: int) -> tuple[pd.DataFrame, pd.Series]:
    data: dict[str, pd.Series] = {}
    for signal in sorted({sig for cfg in REGIME_TRANSITION_PRIORS.values() for sig in cast(list[str], cfg["signals"])}):
        if signal in frame.columns:
            data[signal] = _zscore(frame[signal].astype(float), train_end)
        elif signal == "xau_return_1":
            data[signal] = _zscore(frame["xau_return_1"].astype(float), train_end)
        else:
            data[signal] = pd.Series(np.zeros(len(frame), dtype=float), index=frame.index)

    regime_scores: dict[str, pd.Series] = {}
    for regime, cfg in REGIME_TRANSITION_PRIORS.items():
        signals = cast(list[str], cfg["signals"])
        stacked = np.column_stack([np.asarray(data[sig].to_numpy(), dtype=float) for sig in signals])
        signal_strength = np.mean(np.abs(stacked), axis=1)
        if cfg["trigger_type"] == "volatility_decay":
            signal_strength = 1.0 / (1.0 + signal_strength)
        regime_scores[regime] = pd.Series(signal_strength, index=frame.index)
    score_frame = pd.DataFrame(regime_scores)
    transition_risk = score_frame.max(axis=1).clip(0.0, 1.0)
    return score_frame, transition_risk


def _predict_engine(frame: pd.DataFrame, train_end: int) -> tuple[pd.Series, pd.Series]:
    score_frame, transition_risk = _engine_scores(frame, train_end)
    predicted_regime = score_frame.idxmax(axis=1).astype(str)
    return predicted_regime, transition_risk


def _predict_volatility_only(frame: pd.DataFrame, train_end: int) -> tuple[pd.Series, pd.Series]:
    vol = frame["regime_vol_20"].astype(float)
    trend = frame["trend_gap_30_180"].astype(float)
    macro = frame["macro_pressure"].astype(float).abs()
    high_vol = float(vol.iloc[:train_end].quantile(0.8))
    low_vol = float(vol.iloc[:train_end].quantile(0.2))
    macro_high = float(macro.iloc[:train_end].quantile(0.8))
    regimes: list[str] = []
    risks: list[float] = []
    for idx in range(len(frame)):
        v = float(vol.iloc[idx])
        t = float(trend.iloc[idx])
        m = float(macro.iloc[idx])
        if v >= high_vol and m >= macro_high:
            regimes.append("crisis_dislocation")
        elif t >= 0:
            regimes.append("bull_trend")
        elif t < 0 and v >= low_vol:
            regimes.append("bear_unwind")
        elif v <= low_vol:
            regimes.append("calm_carry")
        else:
            regimes.append("range_compression")
        risks.append(min(1.0, max(0.0, (v / max(high_vol, 1e-6)) * 0.6 + (m / max(macro_high, 1e-6)) * 0.4)))
    return pd.Series(regimes, index=frame.index), pd.Series(risks, index=frame.index)


def _kmeans(points: NDArray[np.float64], k: int, iterations: int = 25) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    rng = np.random.default_rng(42)
    n = points.shape[0]
    if n < k:
        labels = np.arange(n, dtype=np.int64) % max(1, k)
        centers = np.zeros((k, points.shape[1]), dtype=float)
        for idx in range(k):
            subset = points[labels == idx]
            centers[idx] = subset.mean(axis=0) if len(subset) else points[0]
        return centers, labels
    initial_idx = rng.choice(np.arange(n), size=k, replace=False)
    centers = np.asarray(points[initial_idx], dtype=float)
    labels = np.zeros(n, dtype=np.int64)
    for _ in range(iterations):
        dists = np.sum((points[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        labels = np.argmin(dists, axis=1).astype(np.int64)
        new_centers = centers.copy()
        for cid in range(k):
            cluster = points[labels == cid]
            if len(cluster) > 0:
                new_centers[cid] = cluster.mean(axis=0)
        if np.allclose(new_centers, centers):
            break
        centers = new_centers
    return centers, labels


def _predict_hidden_markov(frame: pd.DataFrame, train_end: int) -> tuple[pd.Series, pd.Series]:
    cols = ["xau_return_1", "regime_vol_20", "macro_pressure", "dxy_return_1", "yield_10y_change_5"]
    features = frame[cols].astype(float).copy()
    for col in cols:
        features[col] = _zscore(features[col], train_end)
    x = np.asarray(features.to_numpy(), dtype=float)
    n_states = len(REGIME_ORDER)
    centers, states = _kmeans(np.asarray(x[:train_end], dtype=float), k=n_states)
    all_dists = np.sum((x[:, None, :] - centers[None, :, :]) ** 2, axis=2)
    emission_score = np.exp(-np.min(all_dists, axis=1))
    all_states = np.argmin(all_dists, axis=1).astype(np.int64)

    transition_counts = np.ones((n_states, n_states), dtype=float)
    for i in range(1, train_end):
        transition_counts[states[i - 1], states[i]] += 1.0
    transition_probs = transition_counts / transition_counts.sum(axis=1, keepdims=True)

    hidden = np.zeros(len(frame), dtype=np.int64)
    hidden[0] = int(all_states[0])
    for i in range(1, len(frame)):
        prev = hidden[i - 1]
        score = transition_probs[prev] * np.exp(-all_dists[i])
        hidden[i] = int(np.argmax(score))

    regime_map: dict[int, str] = {}
    regime_train = frame["regime"].iloc[:train_end].astype(str).to_numpy()
    for sid in range(n_states):
        votes = regime_train[np.asarray(states == sid, dtype=bool)]
        if len(votes) == 0:
            regime_map[sid] = REGIME_ORDER[sid]
        else:
            values, counts = np.unique(votes, return_counts=True)
            regime_map[sid] = str(values[int(np.argmax(counts))])
    pred = pd.Series([regime_map[int(s)] for s in hidden], index=frame.index)
    risk = pd.Series(np.clip(1.0 - emission_score, 0.0, 1.0), index=frame.index)
    return pred, risk


def _predict_markov(frame: pd.DataFrame, train_end: int) -> tuple[pd.Series, pd.Series]:
    mapping = _regime_to_int()
    inv = {v: k for k, v in mapping.items()}
    train = frame["regime"].iloc[:train_end].astype(str).map(mapping).to_numpy()
    n = len(REGIME_ORDER)
    counts = np.ones((n, n), dtype=float)
    for i in range(1, len(train)):
        counts[int(train[i - 1]), int(train[i])] += 1.0
    probs = counts / counts.sum(axis=1, keepdims=True)

    preds = np.zeros(len(frame), dtype=np.int64)
    preds[0] = int(train[0]) if len(train) > 0 else 0
    risk = np.zeros(len(frame), dtype=float)
    for i in range(1, len(frame)):
        prev = preds[i - 1]
        nxt = int(np.argmax(probs[prev]))
        preds[i] = nxt
        risk[i] = 1.0 - float(probs[prev, prev])
    return pd.Series([inv[int(x)] for x in preds], index=frame.index), pd.Series(np.clip(risk, 0.0, 1.0), index=frame.index)


def _predict_technical(frame: pd.DataFrame, train_end: int) -> tuple[pd.Series, pd.Series]:
    trend_fast = frame["trend_gap_20_120"].astype(float)
    trend_slow = frame["trend_gap_30_180"].astype(float)
    breakout = frame["breakout_60"].astype(float)
    breakdown = frame["breakdown_20"].astype(float)
    vol = frame["regime_vol_20"].astype(float)
    high_vol = float(vol.iloc[:train_end].quantile(0.8))
    low_vol = float(vol.iloc[:train_end].quantile(0.2))
    regimes: list[str] = []
    risks: list[float] = []
    for idx in range(len(frame)):
        tf = float(trend_fast.iloc[idx])
        ts = float(trend_slow.iloc[idx])
        bo = float(breakout.iloc[idx])
        bd = float(breakdown.iloc[idx])
        v = float(vol.iloc[idx])
        if bo > 0 and ts > 0:
            regime = "bull_trend"
        elif bd < 0.02 and ts < 0:
            regime = "bear_unwind"
        elif v >= high_vol:
            regime = "crisis_dislocation"
        elif abs(tf) < abs(ts) * 0.25 and v <= low_vol:
            regime = "range_compression"
        else:
            regime = "calm_carry"
        regimes.append(regime)
        risks.append(min(1.0, abs(tf - ts) + abs(bo) + abs(bd) + (v / max(high_vol, 1e-6)) * 0.2))
    return pd.Series(regimes, index=frame.index), pd.Series(np.clip(risks, 0.0, 1.0), index=frame.index)


def _predict_macro_only(frame: pd.DataFrame, train_end: int) -> tuple[pd.Series, pd.Series]:
    macro = _zscore(frame["macro_pressure"].astype(float), train_end)
    fed = frame["fed_surprise"].astype(float)
    dxy = _zscore(frame["dxy_return_5"].astype(float), train_end)
    yield_move = _zscore(frame["yield_10y_change_5"].astype(float), train_end)
    regimes: list[str] = []
    risks: list[float] = []
    for idx in range(len(frame)):
        m = float(macro.iloc[idx])
        f = float(fed.iloc[idx])
        u = float(dxy.iloc[idx])
        y = float(yield_move.iloc[idx])
        if abs(f) > 0 or abs(m) > 1.2:
            regime = "macro_transition"
        elif m > 0.7 and u > 0.2:
            regime = "bear_unwind"
        elif m < -0.7 and y < -0.2:
            regime = "bull_trend"
        elif abs(m) < 0.35:
            regime = "calm_carry"
        else:
            regime = "range_compression"
        regimes.append(regime)
        risks.append(min(1.0, (abs(m) * 0.6 + abs(u) * 0.2 + abs(y) * 0.2) / 2.0))
    return pd.Series(regimes, index=frame.index), pd.Series(np.clip(risks, 0.0, 1.0), index=frame.index)


def _predict_random(frame: pd.DataFrame, train_end: int) -> tuple[pd.Series, pd.Series]:
    rng = np.random.default_rng(42)
    mapping = _regime_to_int()
    inv = {v: k for k, v in mapping.items()}
    train = frame["regime"].iloc[:train_end].astype(str).map(mapping).to_numpy()
    n = len(REGIME_ORDER)
    counts = np.ones((n, n), dtype=float)
    for i in range(1, len(train)):
        counts[int(train[i - 1]), int(train[i])] += 1.0
    probs = counts / counts.sum(axis=1, keepdims=True)
    preds = np.zeros(len(frame), dtype=np.int64)
    preds[0] = int(train[0]) if len(train) else 0
    risks = np.zeros(len(frame), dtype=float)
    for i in range(1, len(frame)):
        prev = preds[i - 1]
        preds[i] = int(rng.choice(np.arange(n), p=probs[prev]))
        risks[i] = float(1.0 - probs[prev, prev])
    return pd.Series([inv[int(x)] for x in preds], index=frame.index), pd.Series(np.clip(risks, 0.0, 1.0), index=frame.index)


def _timing_error(actual: NDArray[np.bool_], predicted: NDArray[np.bool_]) -> float:
    actual_idx = _transition_days(actual)
    pred_idx = _transition_days(predicted)
    if len(actual_idx) == 0 or len(pred_idx) == 0:
        return float(len(actual_idx)) if len(actual_idx) else 0.0
    errors = []
    for day in actual_idx:
        errors.append(int(np.min(np.abs(pred_idx - day))))
    return float(np.mean(np.asarray(errors, dtype=float)))


def _transition_metrics(actual_regime: pd.Series, pred_regime: pd.Series, risk: pd.Series) -> dict[str, Any]:
    actual_transition = _actual_transitions(actual_regime)
    pred_transition = _actual_transitions(pred_regime)

    tp = int(np.sum(np.asarray(actual_transition & pred_transition, dtype=bool)))
    tn = int(np.sum(np.asarray((~actual_transition) & (~pred_transition), dtype=bool)))
    fp = int(np.sum(np.asarray((~actual_transition) & pred_transition, dtype=bool)))
    fn = int(np.sum(np.asarray(actual_transition & (~pred_transition), dtype=bool)))

    transition_detection_accuracy = (tp + tn) / max(1, len(actual_transition))
    false_transition_rate = fp / max(1, tp + fp)
    missed_transition_rate = fn / max(1, tp + fn)
    classification_accuracy = float((actual_regime == pred_regime).mean())

    transition_days = np.asarray(np.where(actual_transition)[0], dtype=np.int64)
    if len(transition_days) > 0:
        transition_class_hits = int(
            np.sum(
                np.asarray(
                    [
                        str(actual_regime.iloc[idx]) == str(pred_regime.iloc[idx])
                        for idx in transition_days
                    ],
                    dtype=bool,
                )
            )
        )
        transition_class_acc = transition_class_hits / len(transition_days)
    else:
        transition_class_acc = 0.0

    # Early warning lead time: latest risk>0.6 in prior 10 bars
    risk_arr = np.asarray(risk.to_numpy(), dtype=float)
    leads: list[int] = []
    for idx in transition_days:
        start = max(0, int(idx) - 10)
        window = risk_arr[start:int(idx)]
        if len(window) == 0:
            continue
        hit_idx = np.where(window > 0.6)[0]
        if len(hit_idx) == 0:
            continue
        leads.append(int(idx - (start + int(hit_idx[-1]))))
    early_warning_lead_time = float(np.mean(np.asarray(leads, dtype=float))) if leads else 0.0

    # Cross-regime consistency: mean per-regime recall
    recalls: list[float] = []
    for regime in REGIME_ORDER:
        mask = np.asarray(actual_regime == regime, dtype=bool)
        count = int(np.sum(mask))
        if count == 0:
            continue
        recalls.append(float(np.sum(np.asarray((pred_regime == regime) & mask, dtype=bool))) / count)
    cross_regime_consistency = float(np.mean(np.asarray(recalls, dtype=float))) if recalls else 0.0

    # Confidence calibration: Brier score on transition probability
    y_true = np.asarray(actual_transition, dtype=float)
    y_prob = np.clip(np.asarray(risk.to_numpy(), dtype=float), 0.0, 1.0)
    brier = float(np.mean((y_prob - y_true) ** 2))

    return {
        "transition_detection_accuracy": round(float(transition_detection_accuracy), 4),
        "transition_timing_error": round(_timing_error(actual_transition, pred_transition), 4),
        "transition_classification_accuracy": round(float(transition_class_acc), 4),
        "regime_classification_accuracy": round(float(classification_accuracy), 4),
        "early_warning_lead_time": round(float(early_warning_lead_time), 4),
        "false_transition_rate": round(float(false_transition_rate), 4),
        "missed_transition_rate": round(float(missed_transition_rate), 4),
        "cross_regime_consistency": round(float(cross_regime_consistency), 4),
        "confidence_calibration_brier": round(float(brier), 4),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def _computational_complexity(model_name: str) -> str:
    if model_name in {"random_transition_baseline", "markov_transition_model"}:
        return "low"
    if model_name in {"volatility_only_transition_model", "technical_trend_transition_heuristic", "macro_only_transition_model"}:
        return "low_to_medium"
    if model_name == "hidden_markov_model":
        return "medium"
    return "medium"


def _interpretability(model_name: str) -> str:
    if model_name in {"volatility_only_transition_model", "technical_trend_transition_heuristic", "macro_only_transition_model", "markov_transition_model"}:
        return "high"
    if model_name == "hidden_markov_model":
        return "medium"
    if model_name == "random_transition_baseline":
        return "low"
    return "high"


def _economic_plausibility(model_name: str) -> str:
    if model_name == "random_transition_baseline":
        return "low"
    if model_name in {"hidden_markov_model", "markov_transition_model"}:
        return "medium"
    return "high"


def _robustness_masks(frame: pd.DataFrame) -> dict[str, NDArray[np.bool_]]:
    idx = pd.DatetimeIndex(frame.index)
    masks: dict[str, NDArray[np.bool_]] = {}
    masks["fomc"] = np.asarray(np.abs(frame["fed_surprise"].astype(float).to_numpy()) > 0.0, dtype=bool)
    # CPI/NFP direct feeds are unavailable in this dataset, use macro-event pressure proxies.
    macro_abs = np.abs(frame["macro_pressure"].astype(float).to_numpy())
    macro_q = float(np.quantile(macro_abs, 0.85))
    masks["cpi_proxy"] = np.asarray(macro_abs >= macro_q, dtype=bool)
    masks["nfp_proxy"] = np.asarray(np.abs(frame["dxy_return_1"].astype(float).to_numpy()) >= float(np.quantile(np.abs(frame["dxy_return_1"].astype(float).to_numpy()), 0.9)), dtype=bool)

    for label, start, end in STRESS_WINDOWS:
        start_ts = pd.Timestamp(start, tz=idx.tz)
        end_ts = pd.Timestamp(end, tz=idx.tz)
        masks[label] = np.asarray((idx >= start_ts) & (idx <= end_ts), dtype=bool)

    ret = np.abs(frame["xau_return_1"].astype(float).to_numpy())
    masks["flash_crash_proxy"] = np.asarray(ret >= float(np.quantile(ret, 0.99)), dtype=bool)
    weekday = np.asarray(idx.weekday, dtype=int)
    masks["weekend_gap_proxy"] = np.asarray((weekday == 0) & (ret >= float(np.quantile(ret, 0.8))), dtype=bool)
    vol = frame["regime_vol_20"].astype(float).to_numpy()
    masks["liquidity_shock_proxy"] = np.asarray(vol >= float(np.quantile(vol, 0.9)), dtype=bool)
    masks["high_volatility"] = np.asarray(vol >= float(np.quantile(vol, 0.8)), dtype=bool)
    masks["low_volatility"] = np.asarray(vol <= float(np.quantile(vol, 0.2)), dtype=bool)

    split = int(len(frame) * 0.7)
    masks["out_of_sample"] = np.asarray(np.arange(len(frame)) >= split, dtype=bool)
    masks["long_replay_window"] = np.asarray(np.arange(len(frame)) >= max(0, len(frame) - 756), dtype=bool)
    return masks


def _subset_metrics(actual_regime: pd.Series, pred_regime: pd.Series, risk: pd.Series, mask: NDArray[np.bool_]) -> dict[str, float]:
    if int(np.sum(mask)) < 20:
        return {
            "transition_detection_accuracy": 0.0,
            "transition_classification_accuracy": 0.0,
            "false_transition_rate": 0.0,
            "missed_transition_rate": 0.0,
        }
    sub_actual = actual_regime.loc[mask]
    sub_pred = pred_regime.loc[mask]
    sub_risk = risk.loc[mask]
    metrics = _transition_metrics(sub_actual, sub_pred, sub_risk)
    return {
        "transition_detection_accuracy": float(metrics["transition_detection_accuracy"]),
        "transition_classification_accuracy": float(metrics["transition_classification_accuracy"]),
        "false_transition_rate": float(metrics["false_transition_rate"]),
        "missed_transition_rate": float(metrics["missed_transition_rate"]),
    }


def _robustness_report(actual_regime: pd.Series, predictions: dict[str, dict[str, pd.Series]]) -> dict[str, Any]:
    masks = _robustness_masks(_build_conditioned_frame())
    result: dict[str, Any] = {}
    for model_name, pred in predictions.items():
        scenario_rows: list[dict[str, Any]] = []
        for scenario, mask in masks.items():
            subset = _subset_metrics(actual_regime, pred["regime"], pred["risk"], mask)
            scenario_rows.append({"scenario": scenario, **subset})
        scenario_scores = [float(row["transition_detection_accuracy"]) for row in scenario_rows]
        result[model_name] = {
            "scenarios": scenario_rows,
            "mean_detection_accuracy": round(float(np.mean(np.asarray(scenario_scores, dtype=float))), 4),
            "min_detection_accuracy": round(float(np.min(np.asarray(scenario_scores, dtype=float))), 4),
        }
    return result


def _evaluate_models(frame: pd.DataFrame) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, pd.Series]]]:
    train_end = int(len(frame) * 0.7)
    actual_regime = frame["regime"].astype(str)

    predictors = {
        "institutional_transition_engine_v1": _predict_engine,
        "volatility_only_transition_model": _predict_volatility_only,
        "hidden_markov_model": _predict_hidden_markov,
        "markov_transition_model": _predict_markov,
        "technical_trend_transition_heuristic": _predict_technical,
        "macro_only_transition_model": _predict_macro_only,
        "random_transition_baseline": _predict_random,
    }

    predictions: dict[str, dict[str, pd.Series]] = {}
    evaluations: dict[str, dict[str, Any]] = {}
    for model_name, predictor in predictors.items():
        pred_regime, risk = predictor(frame, train_end)
        predictions[model_name] = {"regime": pred_regime, "risk": risk}
        metrics = _transition_metrics(actual_regime, pred_regime, risk)
        evaluations[model_name] = {
            "model": model_name,
            "metrics": metrics,
            "interpretability": _interpretability(model_name),
            "economic_plausibility": _economic_plausibility(model_name),
            "computational_complexity": _computational_complexity(model_name),
            "data_requirements": (
                "low"
                if model_name in {"random_transition_baseline", "markov_transition_model"}
                else "medium"
                if model_name in {"volatility_only_transition_model", "technical_trend_transition_heuristic"}
                else "high"
            ),
            "institutional_suitability": (
                "low"
                if model_name == "random_transition_baseline"
                else "medium"
                if model_name in {"hidden_markov_model", "markov_transition_model"}
                else "high"
            ),
        }
    return evaluations, predictions


def _comparison_rows(evaluations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model_name, data in evaluations.items():
        metrics = data["metrics"]
        rows.append(
            {
                "model": model_name,
                "transition_detection_accuracy": metrics["transition_detection_accuracy"],
                "transition_timing_error": metrics["transition_timing_error"],
                "transition_classification_accuracy": metrics["transition_classification_accuracy"],
                "early_warning_lead_time": metrics["early_warning_lead_time"],
                "false_transition_rate": metrics["false_transition_rate"],
                "missed_transition_rate": metrics["missed_transition_rate"],
                "cross_regime_consistency": metrics["cross_regime_consistency"],
                "confidence_calibration_brier": metrics["confidence_calibration_brier"],
                "interpretability": data["interpretability"],
                "economic_plausibility": data["economic_plausibility"],
                "computational_complexity": data["computational_complexity"],
                "data_requirements": data["data_requirements"],
                "institutional_suitability": data["institutional_suitability"],
            }
        )
    rows.sort(key=lambda row: (float(row["transition_detection_accuracy"]), -float(row["transition_timing_error"])), reverse=True)
    return rows


def _falsification_assessment(evaluations: dict[str, dict[str, Any]], robustness: dict[str, Any]) -> dict[str, Any]:
    engine = evaluations["institutional_transition_engine_v1"]["metrics"]
    baselines = [evaluations[name]["metrics"] for name in BASELINE_MODELS if name != "institutional_transition_engine_v1"]
    best_baseline = max(baselines, key=lambda item: float(item["transition_detection_accuracy"]))
    better_detection = float(engine["transition_detection_accuracy"]) - float(best_baseline["transition_detection_accuracy"])
    better_timing = float(best_baseline["transition_timing_error"]) - float(engine["transition_timing_error"])
    robustness_gap = float(robustness["institutional_transition_engine_v1"]["mean_detection_accuracy"]) - max(
        float(robustness[name]["mean_detection_accuracy"]) for name in robustness if name != "institutional_transition_engine_v1"
    )

    weaknesses: list[str] = []
    if float(engine["false_transition_rate"]) > 0.55:
        weaknesses.append("Elevated false-transition rate indicates over-sensitive trigger assumptions.")
    if float(engine["missed_transition_rate"]) > 0.45:
        weaknesses.append("Missed-transition rate indicates incomplete transition mechanism coverage.")
    if float(engine["confidence_calibration_brier"]) > 0.30:
        weaknesses.append("Confidence calibration is weak under transition-risk scoring.")
    if robustness_gap < 0.0:
        weaknesses.append("Robustness under stress/event subsets is weaker than at least one simpler baseline.")
    if better_detection < 0.0:
        weaknesses.append("Transition detection accuracy is not superior to simpler baselines.")
    if better_timing < 0.0:
        weaknesses.append("Transition timing error is not improved over the strongest baseline.")

    contradictions = [
        "CPI/NFP direct datasets unavailable; macro-event proxies were used.",
        "Some stress regimes show comparable baseline performance, reducing unique explanatory lift.",
    ]
    outcome = (
        "VERIFIED"
        if better_detection >= 0.03 and better_timing >= 0.2 and robustness_gap >= 0.02 and not weaknesses
        else "PARTIALLY VERIFIED"
        if better_detection >= 0.0 and robustness_gap >= -0.01
        else "REQUIRES REVISION"
    )
    if better_detection < -0.02 and better_timing < -0.2:
        outcome = "REJECTED"

    return {
        "outcome": outcome,
        "better_detection_margin": round(float(better_detection), 4),
        "better_timing_margin": round(float(better_timing), 4),
        "robustness_margin": round(float(robustness_gap), 4),
        "weaknesses": weaknesses,
        "contradictory_evidence": contradictions,
    }


def _knowledge_graph_payload(comparison: list[dict[str, Any]], falsification: dict[str, Any]) -> dict[str, Any]:
    model_nodes = [
        {
            "node_id": f"IKROS-PD1-MODEL-{row['model'].replace('_', '-').upper()}",
            "label": row["model"],
            "node_type": "MODEL",
            "attributes": {
                "transition_detection_accuracy": row["transition_detection_accuracy"],
                "timing_error": row["transition_timing_error"],
                "interpretability": row["interpretability"],
            },
        }
        for row in comparison
    ]
    verification_node = {
        "node_id": "IKROS-PD1-VALIDATION-20260802-0001",
        "label": "Institutional Transition Engine Verification",
        "node_type": "VALIDATION",
        "attributes": {"outcome": falsification["outcome"]},
    }
    failure_nodes = [
        {
            "node_id": f"IKROS-PD1-FAILURE-{idx + 1:04d}",
            "label": failure,
            "node_type": "FAILURE",
            "attributes": {"category": "falsification"},
        }
        for idx, failure in enumerate(cast(list[str], falsification["weaknesses"])[:10])
    ]
    edges = []
    for row in comparison:
        model_id = f"IKROS-PD1-MODEL-{row['model'].replace('_', '-').upper()}"
        edges.append({"source": model_id, "target": verification_node["node_id"], "relation": "EVALUATED", "confidence": row["transition_detection_accuracy"]})
    for node in failure_nodes:
        edges.append({"source": node["node_id"], "target": verification_node["node_id"], "relation": "CONTRADICTED_BY", "confidence": 0.7})
    return {
        "model_nodes": model_nodes,
        "verification_node": verification_node,
        "failure_nodes": failure_nodes,
        "edges": edges,
    }


def prepare_dc2_program_d_phase1_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    _ = prepare_dc2_program_c_phase1_artifacts(repo_root=repo_root)
    frame = _build_conditioned_frame()
    evaluations, predictions = _evaluate_models(frame)
    robustness = _robustness_report(frame["regime"].astype(str), predictions)
    comparison = _comparison_rows(evaluations)
    falsification = _falsification_assessment(evaluations, robustness)
    graph_payload = _knowledge_graph_payload(comparison, falsification)

    analysis = {
        "phase": "DC2_PROGRAM_D_PHASE1",
        "title": "Institutional Transition Engine Verification & Falsification",
        "models_evaluated": BASELINE_MODELS,
        "model_evaluation": evaluations,
        "baseline_comparison_matrix": comparison,
        "transition_accuracy_report": [
            {
                "model": row["model"],
                "transition_detection_accuracy": row["transition_detection_accuracy"],
                "transition_classification_accuracy": row["transition_classification_accuracy"],
                "false_transition_rate": row["false_transition_rate"],
                "missed_transition_rate": row["missed_transition_rate"],
            }
            for row in comparison
        ],
        "transition_timing_report": [
            {
                "model": row["model"],
                "transition_timing_error": row["transition_timing_error"],
                "early_warning_lead_time": row["early_warning_lead_time"],
            }
            for row in comparison
        ],
        "transition_robustness_report": robustness,
        "falsification_report": falsification,
        "failure_catalogue": cast(list[str], falsification["weaknesses"]),
        "evidence_summary": {
            "best_model_by_detection": comparison[0]["model"] if comparison else "",
            "transition_engine_rank": next((idx + 1 for idx, row in enumerate(comparison) if row["model"] == "institutional_transition_engine_v1"), 0),
            "contradictory_evidence": falsification["contradictory_evidence"],
            "dataset_limitations": ["CPI and NFP direct event feeds unavailable; proxy construction used."],
        },
        "research_recommendations": {
            "outcome": falsification["outcome"],
            "retain_as_governing_model": falsification["outcome"] in {"VERIFIED", "PARTIALLY VERIFIED"},
            "revision_priorities": cast(list[str], falsification["weaknesses"])[:5],
            "arb_recommendation": (
                "Retain the Institutional Transition Engine as governing model with explicit caveats and revision backlog."
                if falsification["outcome"] in {"VERIFIED", "PARTIALLY VERIFIED"}
                else "Transition Engine v1 should be revised before remaining the governing explanatory model."
            ),
        },
        "arb_recommendation": {
            "outcome": falsification["outcome"],
            "decision": (
                "MAINTAIN_WITH_CAVEATS"
                if falsification["outcome"] in {"VERIFIED", "PARTIALLY VERIFIED"}
                else "REVISE_MODEL"
            ),
            "rationale": (
                "; ".join(cast(list[str], falsification["weaknesses"]))
                if cast(list[str], falsification["weaknesses"])
                else "Engine remains strongest across multi-criterion comparison."
            ),
        },
        "ecology_knowledge_graph": graph_payload,
    }

    out_dir = (repo_root or Path(".")) / DC2_PROGRAM_D_PHASE1_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc2_program_d_verification_analysis.json", analysis)
    return analysis


def emit_dc2_program_d_phase1_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC2_PROGRAM_D_PHASE1_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    matrix = cast(list[dict[str, Any]], analysis["baseline_comparison_matrix"])
    robustness = cast(dict[str, Any], analysis["transition_robustness_report"])
    falsification = cast(dict[str, Any], analysis["falsification_report"])
    recommendations = cast(dict[str, Any], analysis["research_recommendations"])
    arb = cast(dict[str, Any], analysis["arb_recommendation"])

    verification_md = out_dir / "INSTITUTIONAL_TRANSITION_ENGINE_VERIFICATION_REPORT.md"
    ver_rows = [
        [row["model"], row["transition_detection_accuracy"], row["transition_timing_error"], row["transition_classification_accuracy"], row["cross_regime_consistency"]]
        for row in matrix
    ]
    write_markdown(
        verification_md,
        f"""# Institutional Transition Engine Verification Report
## Discovery Cycle 2 Program D Phase 1

{markdown_table(["Model", "Detection Acc", "Timing Error", "Class Acc", "Cross-Regime Consistency"], ver_rows)}

### Outcome
**{falsification["outcome"]}**
""",
    )
    written["verification_report"] = str(verification_md)

    baseline_md = out_dir / "BASELINE_COMPARISON_REPORT.md"
    baseline_rows = [
        [row["model"], row["interpretability"], row["data_requirements"], row["computational_complexity"], row["institutional_suitability"]]
        for row in matrix
    ]
    write_markdown(
        baseline_md,
        f"""# Baseline Comparison Report
## Discovery Cycle 2 Program D Phase 1

{markdown_table(["Model", "Interpretability", "Data Requirements", "Compute Cost", "Institutional Suitability"], baseline_rows)}
""",
    )
    written["baseline_comparison_report"] = str(baseline_md)

    accuracy_md = out_dir / "TRANSITION_ACCURACY_REPORT.md"
    acc_rows = [
        [row["model"], row["transition_detection_accuracy"], row["transition_classification_accuracy"], row["false_transition_rate"], row["missed_transition_rate"]]
        for row in matrix
    ]
    write_markdown(
        accuracy_md,
        f"""# Transition Accuracy Report
## Discovery Cycle 2 Program D Phase 1

{markdown_table(["Model", "Detection Acc", "Class Acc", "False Transition Rate", "Missed Transition Rate"], acc_rows)}
""",
    )
    written["transition_accuracy_report"] = str(accuracy_md)

    timing_md = out_dir / "TRANSITION_TIMING_REPORT.md"
    timing_rows = [
        [row["model"], row["transition_timing_error"], row["early_warning_lead_time"], row["confidence_calibration_brier"]]
        for row in matrix
    ]
    write_markdown(
        timing_md,
        f"""# Transition Timing Report
## Discovery Cycle 2 Program D Phase 1

{markdown_table(["Model", "Timing Error", "Early Warning Lead", "Brier"], timing_rows)}
""",
    )
    written["transition_timing_report"] = str(timing_md)

    robust_md = out_dir / "TRANSITION_ROBUSTNESS_REPORT.md"
    robust_rows: list[list[object]] = []
    for model_name, report in robustness.items():
        robust_rows.append([model_name, report["mean_detection_accuracy"], report["min_detection_accuracy"]])
    write_markdown(
        robust_md,
        f"""# Transition Robustness Report
## Discovery Cycle 2 Program D Phase 1

{markdown_table(["Model", "Mean Detection Accuracy", "Minimum Detection Accuracy"], robust_rows)}
""",
    )
    written["transition_robustness_report"] = str(robust_md)

    falsification_md = out_dir / "FALSIFICATION_REPORT.md"
    weaknesses = cast(list[str], falsification["weaknesses"])
    contradictions = cast(list[str], falsification["contradictory_evidence"])
    write_markdown(
        falsification_md,
        f"""# Falsification Report
## Discovery Cycle 2 Program D Phase 1

### Outcome
**{falsification["outcome"]}**

### Weaknesses
{chr(10).join(f"- {item}" for item in weaknesses) if weaknesses else "- None material under tested baselines."}

### Contradictory Evidence
{chr(10).join(f"- {item}" for item in contradictions)}
""",
    )
    written["falsification_report"] = str(falsification_md)

    failure_md = out_dir / "FAILURE_CATALOGUE.md"
    write_markdown(
        failure_md,
        f"""# Failure Catalogue
## Discovery Cycle 2 Program D Phase 1

{chr(10).join(f"- {item}" for item in cast(list[str], analysis["failure_catalogue"])) if cast(list[str], analysis["failure_catalogue"]) else "- No dominant failures detected beyond baseline noise."}
""",
    )
    written["failure_catalogue"] = str(failure_md)

    evidence_md = out_dir / "EVIDENCE_SUMMARY.md"
    evidence = cast(dict[str, Any], analysis["evidence_summary"])
    write_markdown(
        evidence_md,
        f"""# Evidence Summary
## Discovery Cycle 2 Program D Phase 1

- **Best model by transition detection:** {evidence["best_model_by_detection"]}
- **Transition engine rank:** {evidence["transition_engine_rank"]}
- **Dataset limitations:** {", ".join(cast(list[str], evidence["dataset_limitations"]))}
""",
    )
    written["evidence_summary"] = str(evidence_md)

    matrix_md = out_dir / "MODEL_COMPARISON_MATRIX.md"
    matrix_rows = [
        [row["model"], row["transition_detection_accuracy"], row["transition_timing_error"], row["interpretability"], row["economic_plausibility"], row["computational_complexity"], row["institutional_suitability"]]
        for row in matrix
    ]
    write_markdown(
        matrix_md,
        f"""# Model Comparison Matrix
## Discovery Cycle 2 Program D Phase 1

{markdown_table(["Model", "Detection Acc", "Timing Error", "Interpretability", "Economic Plausibility", "Compute", "Institutional Suitability"], matrix_rows)}
""",
    )
    written["model_comparison_matrix"] = str(matrix_md)

    rec_md = out_dir / "RESEARCH_RECOMMENDATIONS.md"
    write_markdown(
        rec_md,
        f"""# Research Recommendations
## Discovery Cycle 2 Program D Phase 1

- **Outcome:** {recommendations["outcome"]}
- **Retain as governing model:** {recommendations["retain_as_governing_model"]}

### Revision Priorities
{chr(10).join(f"- {item}" for item in cast(list[str], recommendations["revision_priorities"])) if cast(list[str], recommendations["revision_priorities"]) else "- None required at this stage."}

### ARB Recommendation
{recommendations["arb_recommendation"]}
""",
    )
    written["research_recommendations"] = str(rec_md)

    arb_md = out_dir / "ARB_RECOMMENDATION.md"
    write_markdown(
        arb_md,
        f"""# ARB Recommendation
## Discovery Cycle 2 Program D Phase 1

- **Outcome:** {arb["outcome"]}
- **Decision:** {arb["decision"]}
- **Rationale:** {arb["rationale"]}
""",
    )
    written["arb_recommendation"] = str(arb_md)

    write_json(out_dir / "baseline_comparison_matrix.json", matrix)
    write_json(out_dir / "transition_robustness_report.json", robustness)
    write_json(out_dir / "falsification_report.json", falsification)
    write_json(out_dir / "evidence_summary.json", analysis["evidence_summary"])
    write_json(out_dir / "arb_recommendation.json", arb)

    written["baseline_comparison_matrix_json"] = str(out_dir / "baseline_comparison_matrix.json")
    written["transition_robustness_report_json"] = str(out_dir / "transition_robustness_report.json")
    written["falsification_report_json"] = str(out_dir / "falsification_report.json")
    written["evidence_summary_json"] = str(out_dir / "evidence_summary.json")
    written["arb_recommendation_json"] = str(out_dir / "arb_recommendation.json")
    return written
