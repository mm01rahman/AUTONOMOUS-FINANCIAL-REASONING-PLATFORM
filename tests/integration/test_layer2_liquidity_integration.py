"""WP-RT-1008 integration tests for liquidity CIO-03 emission."""

from __future__ import annotations

from afrp_runtime.contracts.cio import DomainBelief, StandardFeature
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.contracts.features import FEATURE_SPREAD_BPS
from afrp_runtime.layer2.agents import LiquidityAgent


def _spread_feature(value: float, quality: float = 1.0) -> StandardFeature:
    return StandardFeature(
        envelope=make_envelope(
            producer_subsystem_id="L1-FST",
            cognitive_cycle_id="c1",
            mission_profile_id="MP-04",
            payload_repr=f"spread_bps:{value}",
        ),
        feature_id=FEATURE_SPREAD_BPS,
        instrument="XAUUSD",
        value=value,
        window_seconds=60,
        quality=quality,
        source_sequence=1,
    )


def test_liquidity_agent_emits_schema_valid_cio03() -> None:
    agent = LiquidityAgent("MP-04")
    belief: DomainBelief = agent.evaluate(
        "XAUUSD", {FEATURE_SPREAD_BPS: _spread_feature(2.5)}
    )
    belief.validate()
    assert belief.agent_id == "L2-LIQ"
    assert belief.degraded is False
