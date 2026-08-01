"""WP-RT-1016 integration tests: full pipeline through CIO-07 authorization."""

from __future__ import annotations

import pytest
from afrp_runtime.contracts.cio import (
    THETA,
    AuthorizationVerdict,
    AuthorizedAction,
    DomainBelief,
    PortfolioState,
)
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer3.simulator import ScenarioSimulator
from afrp_runtime.layer3.worldmodel import WorldModelKernel
from afrp_runtime.layer4.optimizer import UtilityOptimizer
from afrp_runtime.layer4.policy import PolicyEngine
from afrp_runtime.layer4.synthesizer import DecisionSynthesizer

_TEST_KEY = "integration-test-hmac-key"


def _belief(agent_id: str, masses: dict[str, float], instrument: str = "XAUUSD") -> DomainBelief:
    return DomainBelief(
        envelope=make_envelope(agent_id, "c0", "MP-02", f"{agent_id}:belief"),
        agent_id=agent_id,
        instrument=instrument,
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


def _portfolio(gross_exposure: float = 0.0) -> PortfolioState:
    return PortfolioState(
        envelope=make_envelope("L5-EXE", "c0", "MP-02", "portfolio"),
        positions=(),
        cash=10_000.0,
        equity=10_000.0,
        gross_exposure=gross_exposure,
        reconciled_at_ns=0,
    )


def _run_full_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    profile: str = "MP-02",
    gross_exposure: float = 0.0,
) -> AuthorizedAction:
    monkeypatch.setenv("AFRP_AUDIT_HMAC_KEY", _TEST_KEY)
    kernel = WorldModelKernel(profile)
    wsv = kernel.fuse("XAUUSD", _six_beliefs())
    sim = ScenarioSimulator(profile)
    scenarios = sim.simulate(wsv, spot_price=1800.0)
    synth = DecisionSynthesizer(profile)
    ctx = synth.synthesize(wsv, scenarios, _portfolio(gross_exposure))
    opt = UtilityOptimizer(profile)
    candidate = opt.optimize(ctx, scenarios, spot_price=1800.0)
    engine = PolicyEngine(profile)
    return engine.authorize(candidate, wsv, _portfolio(gross_exposure), spread_bps=1.0)


def test_full_pipeline_produces_cio07(monkeypatch: pytest.MonkeyPatch) -> None:
    """End-to-end: L2-* → L3-WRM → L3-SIM → L4-FUS → L4-DEC → L4-VAL → CIO-07."""
    result = _run_full_pipeline(monkeypatch)
    assert result.instrument == "XAUUSD"
    assert result.verdict in AuthorizationVerdict
    assert len(result.hmac_signature) == 32  # SHA-256 = 32 bytes


def test_mp04_pipeline_always_null_trade(monkeypatch: pytest.MonkeyPatch) -> None:
    """MP-04 disables trading — full pipeline must produce NULL_TRADE."""
    result = _run_full_pipeline(monkeypatch, profile="MP-04")
    assert result.verdict is AuthorizationVerdict.NULL_TRADE


def test_cio07_envelope_traces_back_to_world_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """CIO-07 trace_id must match the originating CIO-04 world state."""
    monkeypatch.setenv("AFRP_AUDIT_HMAC_KEY", _TEST_KEY)
    kernel = WorldModelKernel("MP-02")
    wsv = kernel.fuse("XAUUSD", _six_beliefs())
    sim = ScenarioSimulator("MP-02")
    scenarios = sim.simulate(wsv, spot_price=1800.0)
    synth = DecisionSynthesizer("MP-02")
    ctx = synth.synthesize(wsv, scenarios, _portfolio())
    opt = UtilityOptimizer("MP-02")
    candidate = opt.optimize(ctx, scenarios, spot_price=1800.0)
    engine = PolicyEngine("MP-02")
    result = engine.authorize(candidate, wsv, _portfolio(), spread_bps=1.0)
    assert result.envelope.trace_id == wsv.envelope.trace_id
    assert result.envelope.producer_subsystem_id == "L4-VAL"
