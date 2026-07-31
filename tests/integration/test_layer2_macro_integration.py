"""WP-RT-1006 integration tests for macro CIO-03 emission."""

from __future__ import annotations

from afrp_runtime.contracts.cio import DomainBelief, StandardFeature
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.contracts.features import FEATURE_DXY_RETURN, FEATURE_REAL_YIELD
from afrp_runtime.layer2.agents import MacroAgent


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


def test_macro_agent_emits_schema_valid_cio03() -> None:
    agent = MacroAgent("MP-04")
    belief: DomainBelief = agent.evaluate(
        "XAUUSD",
        {
            FEATURE_REAL_YIELD: _feature(FEATURE_REAL_YIELD, -0.7),
            FEATURE_DXY_RETURN: _feature(FEATURE_DXY_RETURN, -0.015),
        },
    )
    belief.validate()
    assert belief.agent_id == "L2-MAC"
    assert belief.degraded is False
