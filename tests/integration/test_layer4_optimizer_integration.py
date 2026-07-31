"""WP-RT-1015 integration tests: CIO-05B → CIO-06 via full pipeline."""

from __future__ import annotations

from afrp_runtime.contracts.cio import THETA, DomainBelief, PortfolioState
from afrp_runtime.contracts.cio import ExecutionCandidate
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer3.simulator import ScenarioSimulator
from afrp_runtime.layer3.worldmodel import WorldModelKernel
from afrp_runtime.layer4.optimizer import UtilityOptimizer
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


def _six_beliefs(bull: bool = True) -> list[DomainBelief]:
    d = "BULL" if bull else "BEAR"
    o = "BEAR" if bull else "BULL"
    return [
        _belief("L2-MAC", {d: 0.7, o: 0.2, THETA: 0.1}),
        _belief("L2-MIC", {d: 0.6, "RANGE": 0.3, THETA: 0.1}),
        _belief("L2-LIQ", {"RANGE": 0.5, "BEAR|BULL": 0.3, THETA: 0.2}),
        _belief("L2-REG", {"BEAR|BULL": 0.6, "RANGE": 0.2, THETA: 0.2}),
        _belief("L2-FOR", {d: 0.5, THETA: 0.5}),
        _belief("L2-BEH", {o: 0.3, "BEAR&BULL": 0.2, THETA: 0.5}),
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


def _build_pipeline(bull: bool = True) -> ExecutionCandidate:
    kernel = WorldModelKernel("MP-02")
    wsv = kernel.fuse("XAUUSD", _six_beliefs(bull=bull))
    sim = ScenarioSimulator("MP-02")
    scenarios = sim.simulate(wsv, spot_price=1800.0)
    synth = DecisionSynthesizer("MP-02")
    ctx = synth.synthesize(wsv, scenarios, _portfolio())
    opt = UtilityOptimizer("MP-02")
    return opt.optimize(ctx, scenarios, spot_price=1800.0)


def test_full_pipeline_cio05b_to_cio06() -> None:
    """CIO-03 x6 → CIO-04 → CIO-05A → CIO-05B → CIO-06."""
    candidate = _build_pipeline()
    assert candidate.instrument == "XAUUSD"
    assert candidate.direction in (-1.0, 0.0, 1.0)
    assert candidate.envelope.producer_subsystem_id == "L4-DEC"


def test_pipeline_cio06_provenance() -> None:
    """CIO-06 trace_id follows the parent CIO-05B chain."""
    kernel = WorldModelKernel("MP-02")
    wsv = kernel.fuse("XAUUSD", _six_beliefs())
    sim = ScenarioSimulator("MP-02")
    scenarios = sim.simulate(wsv, spot_price=1800.0)
    synth = DecisionSynthesizer("MP-02")
    ctx = synth.synthesize(wsv, scenarios, _portfolio())
    opt = UtilityOptimizer("MP-02")
    candidate = opt.optimize(ctx, scenarios, spot_price=1800.0)
    assert candidate.envelope.trace_id == ctx.envelope.trace_id
