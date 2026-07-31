"""WP-RT-1006 unit tests for the Layer 2 macro belief agent."""

from __future__ import annotations

from afrp_runtime.contracts.cio import THETA
from afrp_runtime.contracts.features import FEATURE_DXY_RETURN, FEATURE_REAL_YIELD
from afrp_runtime.layer2.agents import MacroAgent


def test_macro_falling_yields_and_weaker_dollar_prefers_bull() -> None:
    agent = MacroAgent("MP-04")
    masses = agent.form_belief({FEATURE_REAL_YIELD: -0.8, FEATURE_DXY_RETURN: -0.02})
    assert masses["BULL"] > masses["BEAR"]
    assert masses[THETA] >= 0.05


def test_macro_rising_yields_and_stronger_dollar_prefers_bear() -> None:
    agent = MacroAgent("MP-04")
    masses = agent.form_belief({FEATURE_REAL_YIELD: 0.8, FEATURE_DXY_RETURN: 0.02})
    assert masses["BEAR"] > masses["BULL"]
    assert masses[THETA] >= 0.05
