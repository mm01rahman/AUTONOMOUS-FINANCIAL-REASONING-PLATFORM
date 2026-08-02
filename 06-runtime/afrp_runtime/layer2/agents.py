"""L2 domain agents (SLS-200, WP-IMP-0018..0023).

Six deterministic rule-based belief agents mapping L1-FST features onto DSmT
mass assignments over D^Θ, Θ = {BULL, BEAR, RANGE}. Each agent expresses a
distinct market lens (RUN-002); rules are simple, documented, and replaceable
without contract change (Core Principle 8).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from afrp_runtime.contracts.cio import THETA
from afrp_runtime.contracts.features import (
    FEATURE_DXY_RETURN,
    FEATURE_EWM_VOL,
    FEATURE_FORWARD_SLOPE,
    FEATURE_LOG_RETURN,
    FEATURE_MID,
    FEATURE_REAL_YIELD,
    FEATURE_SENTIMENT,
    FEATURE_SPREAD_BPS,
)
from afrp_runtime.layer2.base import BeliefAgent, intersection_label, union_label

__all__ = (
    "MacroAgent",
    "MicrostructureAgent",
    "LiquidityAgent",
    "RegimeAgent",
    "ForwardAgent",
    "BehavioralAgent",
    "ALL_AGENTS",
)

_BULL_BEAR = union_label("BULL", "BEAR")
_PARADOX = intersection_label("BULL", "BEAR")


def _squash(x: float, scale: float) -> float:
    """Map ℝ → (0, 1) with a logistic curve of characteristic ``scale``."""
    return 1.0 / (1.0 + math.exp(-x / scale))


@dataclass
class MacroAgent(BeliefAgent):
    """L2-MAC: real-yield and dollar dynamics drive gold direction.

    Falling real yields and a weakening dollar are constructive for gold
    (BULL); the converse favors BEAR.
    """

    @property
    def agent_id(self) -> str:
        return "L2-MAC"

    @property
    def required_features(self) -> tuple[str, ...]:
        return (FEATURE_REAL_YIELD, FEATURE_DXY_RETURN)

    def form_belief(self, features: dict[str, float]) -> dict[str, float]:
        bull_signal = _squash(-features[FEATURE_REAL_YIELD], 0.5)
        dollar_pressure = _squash(-features[FEATURE_DXY_RETURN], 0.01)
        conviction = abs(bull_signal - 0.5) + abs(dollar_pressure - 0.5)
        bull = 0.7 * bull_signal + 0.3 * dollar_pressure
        return {
            "BULL": bull * conviction,
            "BEAR": (1.0 - bull) * conviction,
            THETA: max(0.05, 1.0 - conviction),
        }


@dataclass
class MicrostructureAgent(BeliefAgent):
    """L2-MIC: short-horizon momentum from tick returns.

    Strong signed log returns imply directional continuation; weak returns
    imply RANGE.
    """

    @property
    def agent_id(self) -> str:
        return "L2-MIC"

    @property
    def required_features(self) -> tuple[str, ...]:
        return (FEATURE_LOG_RETURN, FEATURE_EWM_VOL)

    def form_belief(self, features: dict[str, float]) -> dict[str, float]:
        ret = features[FEATURE_LOG_RETURN]
        vol = max(features[FEATURE_EWM_VOL], 1e-6)
        signal = ret / (3.0 * vol)  # volatility-normalized momentum
        directional = min(0.9, abs(signal))
        if signal >= 0:
            bull, bear = directional, 0.0
        else:
            bull, bear = 0.0, directional
        return {
            "BULL": bull,
            "BEAR": bear,
            "RANGE": max(0.0, 0.8 - directional),
            THETA: 0.2,
        }


@dataclass
class LiquidityAgent(BeliefAgent):
    """L2-LIQ: spread stress gates conviction.

    Tight spreads support whatever structure exists (RANGE mass); wide
    spreads are informational stress — mass flows to Θ.
    """

    @property
    def agent_id(self) -> str:
        return "L2-LIQ"

    @property
    def required_features(self) -> tuple[str, ...]:
        return (FEATURE_SPREAD_BPS,)

    def form_belief(self, features: dict[str, float]) -> dict[str, float]:
        stress = _squash(features[FEATURE_SPREAD_BPS] - 3.0, 1.5)
        return {
            "RANGE": (1.0 - stress) * 0.7,
            _BULL_BEAR: (1.0 - stress) * 0.1,
            THETA: 0.2 + stress * 0.8,
        }


@dataclass
class RegimeAgent(BeliefAgent):
    """L2-REG: volatility regime classification.

    Low volatility → RANGE; high volatility → trending, but direction unknown
    to this agent, expressed as the BULL|BEAR union mass.
    """

    low_vol: float = 0.001
    high_vol: float = 0.004

    @property
    def agent_id(self) -> str:
        return "L2-REG"

    @property
    def required_features(self) -> tuple[str, ...]:
        return (FEATURE_EWM_VOL,)

    def form_belief(self, features: dict[str, float]) -> dict[str, float]:
        vol = features[FEATURE_EWM_VOL]
        span = max(self.high_vol - self.low_vol, 1e-9)
        trend_score = min(1.0, max(0.0, (vol - self.low_vol) / span))
        return {
            "RANGE": (1.0 - trend_score) * 0.8,
            _BULL_BEAR: trend_score * 0.8,
            THETA: 0.2,
        }


@dataclass
class ForwardAgent(BeliefAgent):
    """L2-FOR: forward-curve expectations.

    Positive forward slope (contango deepening vs spot) signals expected
    appreciation pressure; negative slope the reverse.
    """

    @property
    def agent_id(self) -> str:
        return "L2-FOR"

    @property
    def required_features(self) -> tuple[str, ...]:
        return (FEATURE_FORWARD_SLOPE, FEATURE_MID)

    def form_belief(self, features: dict[str, float]) -> dict[str, float]:
        slope = features[FEATURE_FORWARD_SLOPE]
        conviction = min(0.85, abs(slope) * 20.0)
        if slope >= 0:
            bull, bear = conviction, 0.0
        else:
            bull, bear = 0.0, conviction
        return {"BULL": bull, "BEAR": bear, THETA: max(0.15, 1.0 - conviction)}


@dataclass
class BehavioralAgent(BeliefAgent):
    """L2-BEH: contrarian positioning read.

    Extreme crowd positioning implies reversal risk against the crowd; the
    genuinely conflicted middle carries a paradoxical BULL&BEAR mass — the
    market simultaneously exhibits both impulses (DSmT allows it).
    """

    @property
    def agent_id(self) -> str:
        return "L2-BEH"

    @property
    def required_features(self) -> tuple[str, ...]:
        return (FEATURE_SENTIMENT,)

    def form_belief(self, features: dict[str, float]) -> dict[str, float]:
        sentiment = max(-1.0, min(1.0, features[FEATURE_SENTIMENT]))
        extremity = abs(sentiment)
        contrarian = 0.6 * extremity
        paradox = 0.2 * (1.0 - extremity)
        if sentiment > 0:  # crowd long → contrarian BEAR
            bull, bear = 0.0, contrarian
        else:
            bull, bear = contrarian, 0.0
        return {
            "BULL": bull,
            "BEAR": bear,
            _PARADOX: paradox,
            THETA: max(0.2, 1.0 - contrarian - paradox),
        }


ALL_AGENTS: tuple[type[BeliefAgent], ...] = (
    MacroAgent,
    MicrostructureAgent,
    LiquidityAgent,
    RegimeAgent,
    ForwardAgent,
    BehavioralAgent,
)
