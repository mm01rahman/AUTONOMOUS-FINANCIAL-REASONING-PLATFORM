"""WP-RT-1008 unit tests for the Layer 2 liquidity belief agent."""

from __future__ import annotations

from afrp_runtime.contracts.cio import THETA
from afrp_runtime.contracts.features import FEATURE_SPREAD_BPS
from afrp_runtime.layer2.agents import LiquidityAgent
from afrp_runtime.layer2.base import union_label


def test_liquidity_tight_spread_prefers_range() -> None:
    agent = LiquidityAgent("MP-04")
    masses = agent.form_belief({FEATURE_SPREAD_BPS: 1.0})
    assert masses["RANGE"] > masses[THETA]


def test_liquidity_wide_spread_prefers_uncertainty() -> None:
    agent = LiquidityAgent("MP-04")
    masses = agent.form_belief({FEATURE_SPREAD_BPS: 10.0})
    assert masses[THETA] > masses["RANGE"]


def test_liquidity_includes_union_mass() -> None:
    agent = LiquidityAgent("MP-04")
    masses = agent.form_belief({FEATURE_SPREAD_BPS: 3.0})
    assert union_label("BULL", "BEAR") in masses
