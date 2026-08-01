"""WP-RT-1014 unit tests for the Decision Context Synthesizer."""

from __future__ import annotations

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import (
    THETA,
    PortfolioState,
    Scenario,
    ScenarioSet,
    WorldStateVector,
)
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer4.synthesizer import DecisionSynthesizer


def _envelope(subsystem: str) -> object:
    return make_envelope(
        producer_subsystem_id=subsystem,
        cognitive_cycle_id="c0",
        mission_profile_id="MP-02",
        payload_repr=f"{subsystem}:test",
    )


def _wsv(instrument: str = "XAUUSD") -> WorldStateVector:
    env = make_envelope("L3-WRM", "c0", "MP-02", f"{instrument}:wsv")
    return WorldStateVector(
        envelope=env,
        instrument=instrument,
        fused_masses={"BULL": 0.7, "BEAR": 0.2, THETA: 0.1},
        epistemic_uncertainty=0.1,
        conflict_mass=0.0,
        regime_context="BULL",
        active_hypotheses=("BULL",),
        agent_quorum=6,
        fusion_trace=("ok",),
    )


def _scenarios(instrument: str = "XAUUSD") -> ScenarioSet:
    env = make_envelope("L3-SIM", "c0", "MP-02", f"{instrument}:scenarios")
    scenarios = (
        Scenario("s0000", 0.5, 101.0, -0.2, 1.2),
        Scenario("s0001", 0.5, 99.5, -0.5, 0.3),
    )
    return ScenarioSet(
        envelope=env,
        instrument=instrument,
        scenarios=scenarios,
        differential_entropy=0.5,
        horizon_seconds=3600,
        random_seed=42,
    )


def _portfolio(cash: float = 10_000.0, gross_exposure: float = 0.0) -> PortfolioState:
    env = make_envelope("L5-EXE", "c0", "MP-02", "portfolio:test")
    return PortfolioState(
        envelope=env,
        positions=(),
        cash=cash,
        equity=cash,
        gross_exposure=gross_exposure,
        reconciled_at_ns=0,
    )


# ── basic synthesis ────────────────────────────────────────────────────────────


def test_synthesizer_returns_decision_context() -> None:
    synth = DecisionSynthesizer("MP-02")
    ctx = synth.synthesize(_wsv(), _scenarios(), _portfolio())
    assert ctx.instrument == "XAUUSD"


def test_synthesizer_preserves_available_cash() -> None:
    synth = DecisionSynthesizer("MP-02")
    ctx = synth.synthesize(_wsv(), _scenarios(), _portfolio(cash=5000.0))
    assert ctx.available_cash == 5000.0


def test_synthesizer_sets_max_position_size_from_profile() -> None:
    # MP-02 max_position_size = 2.0
    synth = DecisionSynthesizer("MP-02")
    ctx = synth.synthesize(_wsv(), _scenarios(), _portfolio())
    assert ctx.max_position_size == 2.0


# ── risk lambda ────────────────────────────────────────────────────────────────


def test_risk_lambda_mp02_is_base_over_tolerance() -> None:
    # MP-02 risk_tolerance=1.0 → lambda = 2.0/1.0 = 2.0
    synth = DecisionSynthesizer("MP-02")
    ctx = synth.synthesize(_wsv(), _scenarios(), _portfolio())
    assert ctx.risk_aversion_lambda == pytest.approx(2.0)


def test_risk_lambda_mp03_lower_than_mp02() -> None:
    # MP-03 risk_tolerance=1.5 → lambda = 2.0/1.5 ≈ 1.333
    synth = DecisionSynthesizer("MP-03")
    ctx = synth.synthesize(_wsv(), _scenarios(), _portfolio())
    # More tolerant profile → lower lambda
    assert ctx.risk_aversion_lambda < 2.0


def test_risk_lambda_mp01_higher_than_mp02() -> None:
    # MP-01 risk_tolerance=0.5 → lambda = 2.0/0.5 = 4.0
    synth = DecisionSynthesizer("MP-01")
    ctx = synth.synthesize(_wsv(), _scenarios(), _portfolio())
    assert ctx.risk_aversion_lambda == pytest.approx(4.0)


# ── provenance ─────────────────────────────────────────────────────────────────


def test_synthesizer_propagates_trace_id() -> None:
    wsv = _wsv()
    synth = DecisionSynthesizer("MP-02")
    ctx = synth.synthesize(wsv, _scenarios(), _portfolio())
    assert ctx.envelope.trace_id == wsv.envelope.trace_id


def test_synthesizer_links_all_parent_ids() -> None:
    wsv = _wsv()
    scen = _scenarios()
    port = _portfolio()
    synth = DecisionSynthesizer("MP-02")
    ctx = synth.synthesize(wsv, scen, port)
    assert wsv.envelope.message_id in ctx.world_state_id
    assert scen.envelope.message_id in ctx.scenario_set_id
    assert port.envelope.message_id in ctx.portfolio_state_id


# ── contract enforcement ───────────────────────────────────────────────────────


def test_instrument_mismatch_raises() -> None:
    synth = DecisionSynthesizer("MP-02")
    with pytest.raises(ContractViolationError):
        synth.synthesize(_wsv("XAUUSD"), _scenarios("BTCUSD"), _portfolio())
