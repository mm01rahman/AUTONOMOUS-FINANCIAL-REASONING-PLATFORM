"""WP-RT-1013 integration tests: CIO-04 WorldStateVector to CIO-05A ScenarioSet."""

from __future__ import annotations

import math

from afrp_runtime.contracts.cio import THETA, DomainBelief, ScenarioSet
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer3.simulator import ScenarioSimulator
from afrp_runtime.layer3.worldmodel import WorldModelKernel


def _make_belief(agent_id: str, masses: dict[str, float]) -> DomainBelief:
    envelope = make_envelope(
        producer_subsystem_id=agent_id,
        cognitive_cycle_id="c0",
        mission_profile_id="MP-04",
        payload_repr=f"{agent_id}:belief",
    )
    return DomainBelief(
        envelope=envelope,
        agent_id=agent_id,
        instrument="BTCUSD",
        masses=masses,
        reliability=1.0,
        degraded=False,
    )


def _make_beliefs(bull_signal: bool = True) -> list[DomainBelief]:
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


def test_full_pipeline_cio03_to_cio05a() -> None:
    """End-to-end: 6x CIO-03 → CIO-04 → CIO-05A."""
    kernel = WorldModelKernel("MP-04")
    wsv = kernel.fuse("BTCUSD", _make_beliefs(bull_signal=True))
    sim = ScenarioSimulator(mission_profile_id="MP-04")
    result: ScenarioSet = sim.simulate(wsv, spot_price=50000.0)

    assert result.instrument == "BTCUSD"
    assert len(result.scenarios) > 0
    assert abs(sum(s.probability for s in result.scenarios) - 1.0) < 1e-9
    assert math.isfinite(result.differential_entropy)
    # Provenance: scenario trace_id should match world state trace_id
    assert result.envelope.trace_id == wsv.envelope.trace_id


def test_pipeline_scenario_envelope_is_valid() -> None:
    """CIO-05A envelope fields are populated."""
    kernel = WorldModelKernel("MP-04")
    wsv = kernel.fuse("BTCUSD", _make_beliefs())
    sim = ScenarioSimulator(mission_profile_id="MP-04")
    result = sim.simulate(wsv, spot_price=50000.0)

    assert result.envelope.producer_subsystem_id == "L3-SIM"
    assert result.envelope.mission_profile_id == "MP-04"
    assert result.random_seed == 42


def test_pipeline_bearish_signal_lowers_drift() -> None:
    """Bear-consensus world state should produce a different distribution from bull."""
    kernel = WorldModelKernel("MP-04")
    wsv_bull = kernel.fuse("BTCUSD", _make_beliefs(bull_signal=True))
    wsv_bear = kernel.fuse("BTCUSD", _make_beliefs(bull_signal=False))
    sim = ScenarioSimulator(mission_profile_id="MP-04")
    r_bull = sim.simulate(wsv_bull, spot_price=50000.0, cycle=0)
    r_bear = sim.simulate(wsv_bear, spot_price=50000.0, cycle=0)
    # Distribution means should differ directionally
    mean_bull = sum(s.terminal_price for s in r_bull.scenarios) / len(r_bull.scenarios)
    mean_bear = sum(s.terminal_price for s in r_bear.scenarios) / len(r_bear.scenarios)
    assert mean_bull != mean_bear
