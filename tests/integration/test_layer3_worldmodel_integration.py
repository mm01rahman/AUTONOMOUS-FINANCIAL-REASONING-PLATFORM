"""WP-RT-1012 integration tests: six-agent CIO-03 stream to CIO-04."""

from __future__ import annotations

import pytest
from afrp_runtime.contracts.cio import THETA, DomainBelief, WorldStateVector
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer3.worldmodel import EXPECTED_AGENTS, WorldModelKernel


def _make_belief(
    agent_id: str,
    masses: dict[str, float],
    *,
    degraded: bool = False,
    reliability: float = 1.0,
) -> DomainBelief:
    envelope = make_envelope(
        producer_subsystem_id=agent_id,
        cognitive_cycle_id="c1",
        mission_profile_id="MP-04",
        payload_repr=f"{agent_id}:belief",
    )
    return DomainBelief(
        envelope=envelope,
        agent_id=agent_id,
        instrument="XAUUSD",
        masses=masses,
        reliability=reliability,
        degraded=degraded,
    )


def _full_belief_set(bull_signal: bool = True) -> list[DomainBelief]:
    """Return a schema-valid six-agent belief list."""
    direction = "BULL" if bull_signal else "BEAR"
    opposite = "BEAR" if bull_signal else "BULL"
    return [
        _make_belief("L2-MAC", {direction: 0.7, opposite: 0.2, THETA: 0.1}),
        _make_belief("L2-MIC", {direction: 0.6, "RANGE": 0.3, THETA: 0.1}),
        _make_belief("L2-LIQ", {"RANGE": 0.5, "BEAR|BULL": 0.3, THETA: 0.2}),
        _make_belief("L2-REG", {"BEAR|BULL": 0.6, "RANGE": 0.2, THETA: 0.2}),
        _make_belief("L2-FOR", {direction: 0.5, THETA: 0.5}),
        _make_belief("L2-BEH", {opposite: 0.3, "BEAR&BULL": 0.2, THETA: 0.5}),
    ]


def test_world_model_produces_cio04() -> None:
    kernel = WorldModelKernel("MP-04")
    wsv: WorldStateVector = kernel.fuse("XAUUSD", _full_belief_set())
    assert wsv.instrument == "XAUUSD"
    assert abs(sum(wsv.fused_masses.values()) - 1.0) < 1e-9
    assert wsv.agent_quorum == 6


def test_world_model_bullish_consensus_resolved() -> None:
    kernel = WorldModelKernel("MP-04")
    wsv = kernel.fuse("XAUUSD", _full_belief_set(bull_signal=True))
    assert wsv.regime_context != THETA
    assert wsv.agent_quorum > 0


def test_world_model_missing_agents_degrades_gracefully() -> None:
    """Only two agents provided — quorum is 2, no crash (NFR-003)."""
    kernel = WorldModelKernel("MP-04")
    beliefs = [
        _make_belief("L2-MAC", {"BULL": 0.8, THETA: 0.2}),
        _make_belief("L2-MIC", {"BULL": 0.7, THETA: 0.3}),
    ]
    wsv = kernel.fuse("XAUUSD", beliefs)
    assert wsv.agent_quorum == 2
    assert abs(sum(wsv.fused_masses.values()) - 1.0) < 1e-9


def test_world_model_fully_missing_produces_vacuous() -> None:
    """Zero agents provided — result is vacuous m(THETA)=1, quorum=0."""
    kernel = WorldModelKernel("MP-04")
    wsv = kernel.fuse("XAUUSD", [])
    assert wsv.agent_quorum == 0
    assert wsv.fused_masses.get(THETA, 0.0) == pytest.approx(1.0)
    assert wsv.regime_context == THETA


def test_world_model_degraded_belief_does_not_raise() -> None:
    """A degraded belief is accepted; its masses = m(THETA)=1 (NFR-003)."""
    kernel = WorldModelKernel("MP-04")
    beliefs = [_make_belief("L2-MAC", {THETA: 1.0}, degraded=True)]
    wsv = kernel.fuse("XAUUSD", beliefs)
    assert wsv.agent_quorum == 0  # degraded does not count toward healthy quorum


def test_world_model_all_expected_agents_present() -> None:
    """Ensure EXPECTED_AGENTS matches the six canonical L2 agents."""
    assert set(EXPECTED_AGENTS) == {"L2-MAC", "L2-MIC", "L2-LIQ", "L2-REG", "L2-FOR", "L2-BEH"}
    assert len(EXPECTED_AGENTS) == 6
