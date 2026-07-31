"""WP-RT-1013 unit tests for the Sigma_EWM scenario simulator."""

from __future__ import annotations

import pytest

from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import THETA, ScenarioSet, WorldStateVector
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer3.simulator import ScenarioSimulator


def _make_wsv(
    fused_masses: dict[str, float],
    *,
    instrument: str = "XAUUSD",
    epistemic_uncertainty: float = 0.1,
    conflict_mass: float = 0.0,
    regime_context: str = "BULL",
    active_hypotheses: tuple[str, ...] = ("BULL",),
    agent_quorum: int = 6,
) -> WorldStateVector:
    envelope = make_envelope(
        producer_subsystem_id="L3-WRM",
        cognitive_cycle_id="c0",
        mission_profile_id="MP-04",
        payload_repr=f"{instrument}:test",
    )
    return WorldStateVector(
        envelope=envelope,
        instrument=instrument,
        fused_masses=fused_masses,
        epistemic_uncertainty=epistemic_uncertainty,
        conflict_mass=conflict_mass,
        regime_context=regime_context,
        active_hypotheses=active_hypotheses,
        agent_quorum=agent_quorum,
        fusion_trace=("test",),
    )


def _bull_wsv() -> WorldStateVector:
    return _make_wsv({"BULL": 0.7, "BEAR": 0.2, THETA: 0.1})


def _vacuous_wsv() -> WorldStateVector:
    return _make_wsv(
        {THETA: 1.0},
        epistemic_uncertainty=1.0,
        regime_context=THETA,
        active_hypotheses=(),
        agent_quorum=0,
    )


# ── basic simulation ────────────────────────────────────────────────────────────


def test_simulate_returns_scenario_set() -> None:
    sim = ScenarioSimulator(mission_profile_id="MP-04")
    result: ScenarioSet = sim.simulate(_bull_wsv(), spot_price=1800.0)
    assert isinstance(result, ScenarioSet)
    assert result.instrument == "XAUUSD"
    assert len(result.scenarios) > 0


def test_simulate_probability_sums_to_one() -> None:
    sim = ScenarioSimulator(mission_profile_id="MP-04")
    result = sim.simulate(_bull_wsv(), spot_price=1800.0)
    total = sum(s.probability for s in result.scenarios)
    assert abs(total - 1.0) < 1e-9


def test_simulate_all_terminal_prices_positive() -> None:
    sim = ScenarioSimulator(mission_profile_id="MP-04")
    result = sim.simulate(_bull_wsv(), spot_price=1800.0)
    assert all(s.terminal_price > 0.0 for s in result.scenarios)


def test_simulate_entropy_is_finite_float() -> None:
    sim = ScenarioSimulator(mission_profile_id="MP-04")
    result = sim.simulate(_bull_wsv(), spot_price=1800.0)
    import math

    assert math.isfinite(result.differential_entropy)


# ── determinism ────────────────────────────────────────────────────────────────


def test_simulate_is_deterministic_same_cycle() -> None:
    """Same cycle → identical ScenarioSet (EDR-009/NFR-004)."""
    sim = ScenarioSimulator(mission_profile_id="MP-04")
    wsv = _bull_wsv()
    r1 = sim.simulate(wsv, spot_price=1800.0, cycle=0)
    r2 = sim.simulate(wsv, spot_price=1800.0, cycle=0)
    # Probabilities and terminal prices must be identical
    assert len(r1.scenarios) == len(r2.scenarios)
    for s1, s2 in zip(r1.scenarios, r2.scenarios, strict=True):
        assert s1.terminal_price == s2.terminal_price
        assert s1.probability == s2.probability


def test_simulate_different_cycles_differ() -> None:
    """Different cycle → different random stream → different outcomes expected."""
    sim = ScenarioSimulator(mission_profile_id="MP-04")
    wsv = _bull_wsv()
    r0 = sim.simulate(wsv, spot_price=1800.0, cycle=0)
    r1 = sim.simulate(wsv, spot_price=1800.0, cycle=1)
    terminals_0 = [s.terminal_price for s in r0.scenarios]
    terminals_1 = [s.terminal_price for s in r1.scenarios]
    assert terminals_0 != terminals_1


# ── contract enforcement ───────────────────────────────────────────────────────


def test_simulate_negative_spot_raises() -> None:
    sim = ScenarioSimulator(mission_profile_id="MP-04")
    with pytest.raises(ContractViolationError):
        sim.simulate(_bull_wsv(), spot_price=-100.0)


def test_simulate_zero_spot_raises() -> None:
    sim = ScenarioSimulator(mission_profile_id="MP-04")
    with pytest.raises(ContractViolationError):
        sim.simulate(_bull_wsv(), spot_price=0.0)


# ── equilibrium manifold ───────────────────────────────────────────────────────


def test_simulate_vacuous_state_still_produces_scenarios() -> None:
    """Zero confidence world state: drift=0, higher vol; should still admit paths."""
    sim = ScenarioSimulator(mission_profile_id="MP-04", max_abs_log_move=0.10)
    result = sim.simulate(_vacuous_wsv(), spot_price=100.0)
    assert len(result.scenarios) > 0
    assert abs(sum(s.probability for s in result.scenarios) - 1.0) < 1e-9
