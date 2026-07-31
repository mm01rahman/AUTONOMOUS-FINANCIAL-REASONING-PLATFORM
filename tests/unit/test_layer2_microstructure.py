"""WP-RT-1007 unit tests for the Layer 2 microstructure belief agent."""

from __future__ import annotations

from afrp_runtime.contracts.cio import THETA
from afrp_runtime.contracts.features import FEATURE_EWM_VOL, FEATURE_LOG_RETURN
from afrp_runtime.layer2.agents import MicrostructureAgent


def test_microstructure_positive_return_prefers_bull() -> None:
    agent = MicrostructureAgent("MP-04")
    masses = agent.form_belief({FEATURE_LOG_RETURN: 0.004, FEATURE_EWM_VOL: 0.001})
    assert masses["BULL"] > masses["BEAR"]
    assert masses[THETA] == 0.2


def test_microstructure_negative_return_prefers_bear() -> None:
    agent = MicrostructureAgent("MP-04")
    masses = agent.form_belief({FEATURE_LOG_RETURN: -0.004, FEATURE_EWM_VOL: 0.001})
    assert masses["BEAR"] > masses["BULL"]
    assert masses[THETA] == 0.2


def test_microstructure_weak_signal_keeps_range_mass() -> None:
    agent = MicrostructureAgent("MP-04")
    masses = agent.form_belief({FEATURE_LOG_RETURN: 0.0001, FEATURE_EWM_VOL: 0.005})
    assert masses["RANGE"] > 0.0
