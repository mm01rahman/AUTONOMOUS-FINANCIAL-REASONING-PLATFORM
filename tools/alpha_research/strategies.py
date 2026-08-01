"""Strategy families and signal generation for Phase E."""

from __future__ import annotations

from dataclasses import replace
from typing import Final

import numpy as np
import pandas as pd

from tools.alpha_research.models import StrategyParameters

BASELINE_NAME: Final[str] = "baseline_afrp"
REQUIRED_STRATEGIES: Final[tuple[str, ...]] = (
    "trend_following",
    "mean_reversion",
    "liquidity_sweep",
    "macro_only",
    "technical_only",
    "hybrid",
)
ALL_STRATEGIES: Final[tuple[str, ...]] = (BASELINE_NAME, *REQUIRED_STRATEGIES)
_COMPONENT_COLUMNS: Final[tuple[str, ...]] = (
    "macro_score",
    "microstructure_score",
    "liquidity_score",
    "regime_score",
    "forward_score",
    "behavioral_score",
    "technical_score",
)


def _clamp(values: pd.Series, low: float = -1.0, high: float = 1.0) -> pd.Series:
    return values.clip(lower=low, upper=high).fillna(0.0)


def build_component_frame(
    strategy_name: str, frame: pd.DataFrame, parameters: StrategyParameters
) -> pd.DataFrame:
    """Build raw component scores before fusion/policy stages."""
    technical = pd.Series(0.0, index=frame.index)
    macro = pd.Series(0.0, index=frame.index)
    micro = pd.Series(0.0, index=frame.index)
    liquidity = pd.Series(0.0, index=frame.index)
    regime = pd.Series(0.0, index=frame.index)
    forward = pd.Series(0.0, index=frame.index)
    behavioral = pd.Series(0.0, index=frame.index)

    if strategy_name == BASELINE_NAME:
        technical = _clamp(frame["trend_gap_20_120"] * 120.0 + frame["xau_return_1"] * 35.0)
        regime = _clamp(frame["regime_return_60"] * 4.0)
        micro = _clamp(frame["micro_momentum"] * 0.25)
    elif strategy_name == "trend_following":
        technical = _clamp(frame["trend_gap_30_180"] * 140.0 + frame["breakout_60"] * 50.0)
        regime = _clamp(frame["regime_return_60"] * 5.0)
        micro = _clamp(frame["micro_momentum"] * 0.35)
    elif strategy_name == "mean_reversion":
        behavioral = _clamp(-frame["zscore_20"] / max(parameters.threshold, 0.5))
        technical = _clamp(-frame["xau_return_5"] * 18.0)
        regime = _clamp(-frame["regime_return_60"].abs() * 4.0 + 0.50)
    elif strategy_name == "liquidity_sweep":
        liquidity = _clamp(
            (frame["liquidity_sweep_long"] - frame["liquidity_sweep_short"])
            * (1.0 + frame["range_zscore_20"].clip(lower=0.0))
        )
        micro = _clamp(-frame["micro_momentum"] * 0.35)
        regime = _clamp(-frame["regime_vol_20"] * 25.0 + 0.50)
    elif strategy_name == "macro_only":
        macro = _clamp(frame["macro_pressure"] * 0.75)
        forward = _clamp(frame["forward_expectation"] * 0.60)
        regime = _clamp(frame["geo_severity"] * 0.50 + frame["calendar_event"] * 0.20)
    elif strategy_name == "technical_only":
        technical = _clamp(
            frame["trend_gap_30_180"] * 110.0
            + frame["breakout_20"] * 35.0
            + frame["breakout_60"] * 25.0
        )
        micro = _clamp(frame["micro_momentum"] * 0.30)
        behavioral = _clamp(-frame["zscore_20"] * 0.20)
        regime = _clamp(frame["regime_return_60"] * 3.0)
    elif strategy_name == "hybrid":
        technical = _clamp(frame["trend_gap_30_180"] * 100.0 + frame["breakout_20"] * 25.0)
        macro = _clamp(frame["macro_pressure"] * 0.65)
        micro = _clamp(frame["micro_momentum"] * 0.25)
        liquidity = _clamp(frame["liquidity_sweep_long"] - frame["liquidity_sweep_short"])
        regime = _clamp(frame["regime_return_60"] * 3.0 - frame["regime_vol_20"] * 20.0)
        forward = _clamp(frame["forward_expectation"] * 0.50)
        behavioral = _clamp(-frame["zscore_20"] * 0.25)
    else:
        raise ValueError(f"unknown strategy: {strategy_name}")

    return pd.DataFrame(
        {
            "macro_score": macro,
            "microstructure_score": micro,
            "liquidity_score": liquidity,
            "regime_score": regime,
            "forward_score": forward,
            "behavioral_score": behavioral,
            "technical_score": technical,
        },
        index=frame.index,
    )


def compose_decision_frame(
    frame: pd.DataFrame,
    parameters: StrategyParameters,
    strategy_name: str,
    component_frame: pd.DataFrame,
    *,
    bypass_utility: bool = False,
    bypass_policy: bool = False,
    fusion_mode: str = "weighted",
) -> pd.DataFrame:
    """Compose fused world-model, utility, and policy stages."""
    scores = component_frame.copy()
    if fusion_mode == "max_component":
        best_component = scores.abs().idxmax(axis=1)
        world_model = pd.Series(0.0, index=frame.index)
        for column in _COMPONENT_COLUMNS:
            mask = best_component == column
            world_model.loc[mask] = scores.loc[mask, column]
    else:
        world_model = (
            scores["macro_score"] * parameters.macro_weight
            + scores["microstructure_score"] * parameters.microstructure_weight
            + scores["liquidity_score"] * parameters.liquidity_weight
            + scores["regime_score"] * parameters.regime_weight
            + scores["forward_score"] * parameters.forward_weight
            + scores["behavioral_score"] * parameters.behavioral_weight
            + scores["technical_score"] * parameters.technical_weight
        )
    agreement = (scores.abs() > 0.05).sum(axis=1).astype(float)
    confidence = (0.50 + world_model.abs() * 0.20 + agreement * 0.03).clip(0.50, 0.99)
    if bypass_utility:
        utility = world_model.copy()
    else:
        vol_adjustment = (1.0 - frame["regime_vol_20"] / parameters.vol_ceiling).clip(0.0, 1.0)
        utility = (
            world_model * parameters.position_scale * parameters.utility_weight * vol_adjustment
        )
    raw_position = utility.clip(-parameters.max_position, parameters.max_position)
    policy_ok = (
        (confidence >= parameters.confidence_threshold)
        & (frame["regime_vol_20"] <= parameters.vol_ceiling)
        & (raw_position.abs() >= parameters.score_threshold)
        & (world_model.abs() <= max(parameters.policy_limit, 0.10) * 2.0)
    )
    position = raw_position if bypass_policy else raw_position.where(policy_ok, 0.0)
    action = np.where(position > 0.0, "long", np.where(position < 0.0, "short", "flat"))
    primary_reason = scores.abs().idxmax(axis=1).map(lambda value: value.removesuffix("_score"))
    rejection = np.where(
        confidence < parameters.confidence_threshold,
        "low_confidence",
        np.where(
            frame["regime_vol_20"] > parameters.vol_ceiling,
            "volatility_cap",
            np.where(raw_position.abs() < parameters.score_threshold, "low_score", "authorized"),
        ),
    )
    result = scores.copy()
    result["world_model_score"] = world_model
    result["utility_score"] = utility
    result["confidence"] = confidence
    result["authorized"] = position != 0.0
    result["position_target"] = position
    result["action"] = action
    result["primary_reason"] = primary_reason
    result["policy_reason"] = rejection
    result["strategy_name"] = strategy_name
    return result


def generate_strategy_signal_frame(
    strategy_name: str, frame: pd.DataFrame, parameters: StrategyParameters
) -> pd.DataFrame:
    """Generate the full deterministic decision frame for one strategy family."""
    components = build_component_frame(strategy_name, frame, parameters)
    return compose_decision_frame(frame, parameters, strategy_name, components)


def strategy_parameter_grid(strategy_name: str) -> list[StrategyParameters]:
    """Deterministic compact search grids for each strategy family."""
    base = StrategyParameters()
    if strategy_name == BASELINE_NAME:
        return [
            replace(base, confidence_threshold=0.55, vol_ceiling=0.015, position_scale=0.75),
            replace(base, confidence_threshold=0.60, vol_ceiling=0.015, position_scale=0.75),
            replace(base, confidence_threshold=0.55, vol_ceiling=0.018, position_scale=1.00),
            replace(base, confidence_threshold=0.60, vol_ceiling=0.018, position_scale=1.00),
        ]
    if strategy_name == "trend_following":
        return [
            replace(
                base, fast_window=20, slow_window=120, confidence_threshold=0.55, vol_ceiling=0.012
            ),
            replace(
                base, fast_window=20, slow_window=120, confidence_threshold=0.60, vol_ceiling=0.018
            ),
            replace(
                base, fast_window=30, slow_window=180, confidence_threshold=0.55, vol_ceiling=0.012
            ),
            replace(
                base, fast_window=30, slow_window=180, confidence_threshold=0.60, vol_ceiling=0.018
            ),
        ]
    if strategy_name == "mean_reversion":
        return [
            replace(
                base, lookback=10, threshold=1.25, confidence_threshold=0.55, vol_ceiling=0.012
            ),
            replace(
                base, lookback=10, threshold=1.75, confidence_threshold=0.55, vol_ceiling=0.018
            ),
            replace(
                base, lookback=20, threshold=1.25, confidence_threshold=0.60, vol_ceiling=0.012
            ),
            replace(
                base, lookback=20, threshold=1.75, confidence_threshold=0.60, vol_ceiling=0.018
            ),
        ]
    if strategy_name == "liquidity_sweep":
        return [
            replace(
                base,
                lookback=10,
                confidence_threshold=0.55,
                vol_ceiling=0.015,
                score_threshold=0.05,
            ),
            replace(
                base,
                lookback=10,
                confidence_threshold=0.60,
                vol_ceiling=0.018,
                score_threshold=0.05,
            ),
            replace(
                base,
                lookback=20,
                confidence_threshold=0.55,
                vol_ceiling=0.015,
                score_threshold=0.10,
            ),
            replace(
                base,
                lookback=20,
                confidence_threshold=0.60,
                vol_ceiling=0.018,
                score_threshold=0.10,
            ),
        ]
    if strategy_name == "macro_only":
        return [
            replace(
                base,
                confidence_threshold=0.50,
                vol_ceiling=0.020,
                macro_weight=0.60,
                forward_weight=0.40,
                technical_weight=0.0,
            ),
            replace(
                base,
                confidence_threshold=0.55,
                vol_ceiling=0.020,
                macro_weight=0.55,
                forward_weight=0.45,
                technical_weight=0.0,
            ),
            replace(
                base,
                confidence_threshold=0.50,
                vol_ceiling=0.015,
                macro_weight=0.65,
                forward_weight=0.35,
                technical_weight=0.0,
            ),
            replace(
                base,
                confidence_threshold=0.55,
                vol_ceiling=0.015,
                macro_weight=0.50,
                forward_weight=0.50,
                technical_weight=0.0,
            ),
        ]
    if strategy_name == "technical_only":
        return [
            replace(
                base,
                confidence_threshold=0.55,
                vol_ceiling=0.012,
                technical_weight=0.70,
                microstructure_weight=0.20,
                behavioral_weight=0.10,
            ),
            replace(
                base,
                confidence_threshold=0.60,
                vol_ceiling=0.012,
                technical_weight=0.75,
                microstructure_weight=0.15,
                behavioral_weight=0.10,
            ),
            replace(
                base,
                confidence_threshold=0.55,
                vol_ceiling=0.018,
                technical_weight=0.70,
                microstructure_weight=0.20,
                behavioral_weight=0.10,
            ),
            replace(
                base,
                confidence_threshold=0.60,
                vol_ceiling=0.018,
                technical_weight=0.75,
                microstructure_weight=0.15,
                behavioral_weight=0.10,
            ),
        ]
    if strategy_name == "hybrid":
        return [
            replace(
                base,
                confidence_threshold=0.55,
                vol_ceiling=0.012,
                macro_weight=0.35,
                technical_weight=0.40,
                liquidity_weight=0.15,
                regime_weight=0.15,
                forward_weight=0.10,
                behavioral_weight=0.10,
            ),
            replace(
                base,
                confidence_threshold=0.55,
                vol_ceiling=0.015,
                macro_weight=0.40,
                technical_weight=0.35,
                liquidity_weight=0.15,
                regime_weight=0.15,
                forward_weight=0.10,
                behavioral_weight=0.10,
            ),
            replace(
                base,
                confidence_threshold=0.60,
                vol_ceiling=0.012,
                macro_weight=0.30,
                technical_weight=0.45,
                liquidity_weight=0.10,
                regime_weight=0.15,
                forward_weight=0.10,
                behavioral_weight=0.10,
            ),
            replace(
                base,
                confidence_threshold=0.60,
                vol_ceiling=0.015,
                macro_weight=0.35,
                technical_weight=0.40,
                liquidity_weight=0.10,
                regime_weight=0.20,
                forward_weight=0.10,
                behavioral_weight=0.10,
            ),
        ]
    raise ValueError(f"unknown strategy: {strategy_name}")
