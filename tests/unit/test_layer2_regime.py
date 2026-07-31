"""WP-RT-1009 unit tests for the Layer 2 regime belief agent."""

from __future__ import annotations

from afrp_runtime.contracts.cio import THETA
from afrp_runtime.contracts.features import FEATURE_EWM_VOL
from afrp_runtime.layer2.agents import RegimeAgent
from afrp_runtime.layer2.base import union_label


def test_regime_low_volatility_prefers_range() -> None:
    agent = RegimeAgent("MP-04")
    masses = agent.form_belief({FEATURE_EWM_VOL: 0.0008})
    assert masses["RANGE"] > masses[union_label("BULL", "BEAR")]


def test_regime_high_volatility_prefers_union() -> None:
    agent = RegimeAgent("MP-04")
    masses = agent.form_belief({FEATURE_EWM_VOL: 0.005})
    assert masses[union_label("BULL", "BEAR")] > masses["RANGE"]
    assert masses[THETA] == 0.2
