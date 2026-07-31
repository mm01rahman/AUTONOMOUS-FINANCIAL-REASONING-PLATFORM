"""WP-RT-1005 integration tests for Layer 2 base contracts."""

from __future__ import annotations

from afrp_runtime.contracts.cio import DomainBelief, StandardFeature
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.contracts.features import FEATURE_DXY_RETURN, FEATURE_REAL_YIELD
from afrp_runtime.layer2.base import BeliefAgent


def feature(feature_id: str, value: float, quality: float = 1.0) -> StandardFeature:
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


class _ReferenceAgent(BeliefAgent):
    @property
    def agent_id(self) -> str:
        return "L2-REF"

    @property
    def required_features(self) -> tuple[str, ...]:
        return (FEATURE_REAL_YIELD, FEATURE_DXY_RETURN)

    def form_belief(self, features: dict[str, float]) -> dict[str, float]:
        if features[FEATURE_REAL_YIELD] < 0 and features[FEATURE_DXY_RETURN] < 0:
            return {"BULL": 0.7, "BEAR": 0.2, "THETA": 0.1}
        return {"BULL": 0.2, "BEAR": 0.7, "THETA": 0.1}


def test_reference_agent_emits_schema_valid_cio03() -> None:
    agent = _ReferenceAgent("MP-04")
    features = {
        FEATURE_REAL_YIELD: feature(FEATURE_REAL_YIELD, -0.8),
        FEATURE_DXY_RETURN: feature(FEATURE_DXY_RETURN, -0.01),
    }
    belief: DomainBelief = agent.evaluate("XAUUSD", features)
    belief.validate()
    assert belief.agent_id == "L2-REF"
    assert belief.degraded is False
    assert abs(sum(belief.masses.values()) - 1.0) < 1e-9
