"""WP-RT-1009 integration tests for regime CIO-03 emission."""

from __future__ import annotations

from afrp_runtime.contracts.cio import DomainBelief, StandardFeature
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.contracts.features import FEATURE_EWM_VOL
from afrp_runtime.layer2.agents import RegimeAgent
from afrp_runtime.layer2.base import union_label


def _vol_feature(value: float, quality: float = 1.0) -> StandardFeature:
    return StandardFeature(
        envelope=make_envelope(
            producer_subsystem_id="L1-FST",
            cognitive_cycle_id="c1",
            mission_profile_id="MP-04",
            payload_repr=f"ewm_vol:{value}",
        ),
        feature_id=FEATURE_EWM_VOL,
        instrument="XAUUSD",
        value=value,
        window_seconds=60,
        quality=quality,
        source_sequence=1,
    )


def test_regime_agent_emits_schema_valid_cio03() -> None:
    agent = RegimeAgent("MP-04")
    belief: DomainBelief = agent.evaluate("XAUUSD", {FEATURE_EWM_VOL: _vol_feature(0.0035)})
    belief.validate()
    assert belief.agent_id == "L2-REG"
    assert union_label("BULL", "BEAR") in belief.masses
