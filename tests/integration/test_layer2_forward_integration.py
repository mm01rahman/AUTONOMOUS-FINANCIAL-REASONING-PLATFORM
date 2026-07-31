"""WP-RT-1010 integration tests for forward CIO-03 emission."""

from __future__ import annotations

from afrp_runtime.contracts.cio import DomainBelief, StandardFeature
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.contracts.features import FEATURE_FORWARD_SLOPE, FEATURE_MID
from afrp_runtime.layer2.agents import ForwardAgent


def _feature(feature_id: str, value: float, quality: float = 1.0) -> StandardFeature:
    return StandardFeature(
        envelope=make_envelope(
            producer_subsystem_id="L1-FST",
            cognitive_cycle_id="c1",
            mission_profile_id="MP-04",
            payload_repr=f"{feature_id}:{value}",
        ),
        feature_id=feature_id,
        instrument="XAUUSD",
        value=value,
        window_seconds=60,
        quality=quality,
        source_sequence=1,
    )


def test_forward_agent_emits_schema_valid_cio03() -> None:
    agent = ForwardAgent("MP-04")
    belief: DomainBelief = agent.evaluate(
        "XAUUSD",
        {
            FEATURE_FORWARD_SLOPE: _feature(FEATURE_FORWARD_SLOPE, 0.02),
            FEATURE_MID: _feature(FEATURE_MID, 2300.0),
        },
    )
    belief.validate()
    assert belief.agent_id == "L2-FOR"
    assert belief.degraded is False
