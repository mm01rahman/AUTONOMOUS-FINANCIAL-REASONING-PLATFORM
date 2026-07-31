"""WP-RT-1007 integration tests for microstructure CIO-03 emission."""

from __future__ import annotations

from afrp_runtime.contracts.cio import DomainBelief, StandardFeature
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.contracts.features import FEATURE_EWM_VOL, FEATURE_LOG_RETURN
from afrp_runtime.layer2.agents import MicrostructureAgent


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


def test_microstructure_agent_emits_schema_valid_cio03() -> None:
    agent = MicrostructureAgent("MP-04")
    belief: DomainBelief = agent.evaluate(
        "XAUUSD",
        {
            FEATURE_LOG_RETURN: _feature(FEATURE_LOG_RETURN, 0.003),
            FEATURE_EWM_VOL: _feature(FEATURE_EWM_VOL, 0.0015),
        },
    )
    belief.validate()
    assert belief.agent_id == "L2-MIC"
    assert belief.degraded is False
