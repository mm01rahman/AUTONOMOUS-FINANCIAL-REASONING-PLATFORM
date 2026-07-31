"""WP-RT-1011 unit tests for the Layer 2 behavioral belief agent."""

from __future__ import annotations

from afrp_runtime.contracts.cio import THETA
from afrp_runtime.contracts.features import FEATURE_SENTIMENT
from afrp_runtime.layer2.agents import BehavioralAgent
from afrp_runtime.layer2.base import intersection_label


def test_behavioral_positive_sentiment_is_contrarian_bear() -> None:
    agent = BehavioralAgent("MP-04")
    masses = agent.form_belief({FEATURE_SENTIMENT: 0.9})
    assert masses["BEAR"] > masses["BULL"]
    assert masses[THETA] >= 0.2


def test_behavioral_negative_sentiment_is_contrarian_bull() -> None:
    agent = BehavioralAgent("MP-04")
    masses = agent.form_belief({FEATURE_SENTIMENT: -0.9})
    assert masses["BULL"] > masses["BEAR"]
    assert masses[THETA] >= 0.2


def test_behavioral_mid_sentiment_allocates_paradox_mass() -> None:
    agent = BehavioralAgent("MP-04")
    masses = agent.form_belief({FEATURE_SENTIMENT: 0.0})
    paradox = intersection_label("BULL", "BEAR")
    assert masses[paradox] > 0.0
