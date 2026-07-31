"""WP-RT-1014 integration tests: CIO-04 + CIO-05A + CIO-10 → CIO-05B."""

from __future__ import annotations

from afrp_runtime.contracts.cio import THETA, DomainBelief, PortfolioState
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer3.simulator import ScenarioSimulator
from afrp_runtime.layer3.worldmodel import WorldModelKernel
from afrp_runtime.layer4.synthesizer import DecisionSynthesizer


def _belief(agent_id: str, masses: dict[str, float]) -> DomainBelief:
    return DomainBelief(
        envelope=make_envelope(agent_id, "c0", "MP-02", f"{agent_id}:belief"),
        agent_id=agent_id,
        instrument="XAUUSD",
        masses=masses,
        reliability=1.0,
        degraded=False,
    )


def _six_beliefs() -> list[DomainBelief]:
    return [
        _belief("L2-MAC", {"BULL": 0.7, "BEAR": 0.2, THETA: 0.1}),
        _belief("L2-MIC", {"BULL": 0.6, "RANGE": 0.3, THETA: 0.1}),
        _belief("L2-LIQ", {"RANGE": 0.5, "BEAR|BULL": 0.3, THETA: 0.2}),
        _belief("L2-REG", {"BEAR|BULL": 0.6, "RANGE": 0.2, THETA: 0.2}),
        _belief("L2-FOR", {"BULL": 0.5, THETA: 0.5}),
        _belief("L2-BEH", {"BEAR": 0.3, "BEAR&BULL": 0.2, THETA: 0.5}),
    ]


def _portfolio() -> PortfolioState:
    return PortfolioState(
        envelope=make_envelope("L5-EXE", "c0", "MP-02", "portfolio"),
        positions=(),
        cash=10_000.0,
        equity=10_000.0,
        gross_exposure=0.0,
        reconciled_at_ns=0,
    )


def test_full_pipeline_cio04_cio05a_to_cio05b() -> None:
    """L3-WRM → L3-SIM → L4-FUS produces a valid CIO-05B."""
    kernel = WorldModelKernel("MP-02")
    wsv = kernel.fuse("XAUUSD", _six_beliefs())
    sim = ScenarioSimulator("MP-02")
    scenarios = sim.simulate(wsv, spot_price=1800.0)
    synth = DecisionSynthesizer("MP-02")
    ctx = synth.synthesize(wsv, scenarios, _portfolio())

    assert ctx.instrument == "XAUUSD"
    assert ctx.world_state_id == wsv.envelope.message_id
    assert ctx.scenario_set_id == scenarios.envelope.message_id
    assert ctx.risk_aversion_lambda > 0.0


def test_decision_context_envelope_links_to_world_state() -> None:
    """CIO-05B envelope trace_id must match CIO-04 origin."""
    kernel = WorldModelKernel("MP-02")
    wsv = kernel.fuse("XAUUSD", _six_beliefs())
    sim = ScenarioSimulator("MP-02")
    scenarios = sim.simulate(wsv, spot_price=1800.0)
    synth = DecisionSynthesizer("MP-02")
    ctx = synth.synthesize(wsv, scenarios, _portfolio())
    assert ctx.envelope.trace_id == wsv.envelope.trace_id
    assert ctx.envelope.producer_subsystem_id == "L4-FUS"
