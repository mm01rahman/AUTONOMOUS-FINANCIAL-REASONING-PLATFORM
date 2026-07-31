"""WP-RT-1010 unit tests for the Layer 2 forward belief agent."""

from __future__ import annotations

from afrp_runtime.contracts.cio import THETA
from afrp_runtime.contracts.features import FEATURE_FORWARD_SLOPE, FEATURE_MID
from afrp_runtime.layer2.agents import ForwardAgent


def test_forward_positive_slope_prefers_bull() -> None:
    agent = ForwardAgent("MP-04")
    masses = agent.form_belief({FEATURE_FORWARD_SLOPE: 0.03, FEATURE_MID: 2300.0})
    assert masses["BULL"] > masses["BEAR"]
    assert masses[THETA] >= 0.15


def test_forward_negative_slope_prefers_bear() -> None:
    agent = ForwardAgent("MP-04")
    masses = agent.form_belief({FEATURE_FORWARD_SLOPE: -0.03, FEATURE_MID: 2300.0})
    assert masses["BEAR"] > masses["BULL"]
    assert masses[THETA] >= 0.15


def test_forward_zero_slope_keeps_uncertainty() -> None:
    agent = ForwardAgent("MP-04")
    masses = agent.form_belief({FEATURE_FORWARD_SLOPE: 0.0, FEATURE_MID: 2300.0})
    assert masses["BULL"] == 0.0
    assert masses["BEAR"] == 0.0
    assert masses[THETA] == 1.0
