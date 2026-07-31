"""WP-RT-1011 integration tests for behavioral CIO-03 emission."""

from __future__ import annotations

from afrp_runtime.contracts.cio import DomainBelief, StandardFeature
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.contracts.features import FEATURE_SENTIMENT
from afrp_runtime.layer2.agents import BehavioralAgent
from afrp_runtime.layer2.base import intersection_label


def _sentiment_feature(value: float, quality: float = 1.0) -> StandardFeature:
    return StandardFeature(
        envelope=make_envelope(
            producer_subsystem_id="L1-FST",
            cognitive_cycle_id="c1",
            mission_profile_id="MP-04",
            payload_repr=f"sentiment:{value}",
        ),
        feature_id=FEATURE_SENTIMENT,
        instrument="XAUUSD",
        value=value,
        window_seconds=60,
        quality=quality,
        source_sequence=1,
    )


def test_behavioral_agent_emits_schema_valid_cio03() -> None:
    agent = BehavioralAgent("MP-04")
    belief: DomainBelief = agent.evaluate(
        "XAUUSD", {FEATURE_SENTIMENT: _sentiment_feature(0.4)}
    )
    belief.validate()
    assert belief.agent_id == "L2-BEH"
    assert belief.degraded is False
    paradox = intersection_label("BULL", "BEAR")
    assert paradox in belief.masses
