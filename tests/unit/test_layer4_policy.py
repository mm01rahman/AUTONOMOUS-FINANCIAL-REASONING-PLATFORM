"""WP-RT-1016 unit tests for the Policy Engine."""

from __future__ import annotations

import os

import pytest

from afrp_runtime.common.errors import ConfigurationError
from afrp_runtime.contracts.cio import (
    AuthorizationVerdict,
    ExecutionCandidate,
    PortfolioState,
    WorldStateVector,
    THETA,
)
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.common.statemachine import OperationalState
from afrp_runtime.layer4.policy import PolicyEngine

_TEST_KEY = "test-hmac-key-for-unit-tests"


def _set_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AFRP_AUDIT_HMAC_KEY", _TEST_KEY)


def _wsv(quorum: int = 6) -> WorldStateVector:
    env = make_envelope("L3-WRM", "c0", "MP-02", "wsv:test")
    return WorldStateVector(
        envelope=env,
        instrument="XAUUSD",
        fused_masses={"BULL": 0.7, "BEAR": 0.2, THETA: 0.1},
        epistemic_uncertainty=0.1,
        conflict_mass=0.0,
        regime_context="BULL",
        active_hypotheses=("BULL",),
        agent_quorum=quorum,
        fusion_trace=("ok",),
    )


def _candidate(
    direction: float = 1.0,
    size: float = 1.0,
    stop_price: float = 99.2,
    risk_adjusted_utility: float = 5.0,
) -> ExecutionCandidate:
    env = make_envelope("L4-DEC", "c0", "MP-02", "dec:candidate")
    spot = 100.0
    return ExecutionCandidate(
        envelope=env,
        instrument="XAUUSD",
        direction=direction,
        size=size,
        entry_price=spot if direction != 0.0 else 0.0,
        stop_price=stop_price,
        target_price=spot * 1.01 if direction > 0 else (spot * 0.99 if direction < 0 else 0.0),
        expected_utility=5.5,
        expected_risk=0.5,
        risk_adjusted_utility=risk_adjusted_utility,
    )


def _portfolio(gross_exposure: float = 0.0) -> PortfolioState:
    env = make_envelope("L5-EXE", "c0", "MP-02", "portfolio:test")
    return PortfolioState(
        envelope=env,
        positions=(),
        cash=10_000.0,
        equity=10_000.0,
        gross_exposure=gross_exposure,
        reconciled_at_ns=0,
    )


# ── null-trade enforcement ─────────────────────────────────────────────────────


def test_mp04_no_trading_gives_null_trade(monkeypatch: pytest.MonkeyPatch) -> None:
    """MP-04 (allow_trading=False) must produce NULL_TRADE."""
    _set_key(monkeypatch)
    engine = PolicyEngine("MP-04")
    result = engine.authorize(_candidate(), _wsv(), _portfolio(), spread_bps=1.0)
    assert result.verdict is AuthorizationVerdict.NULL_TRADE
    assert result.direction == 0.0
    assert result.size == 0.0


def test_non_normal_state_gives_null_trade(monkeypatch: pytest.MonkeyPatch) -> None:
    """EMERGENCY_STOP state must produce NULL_TRADE."""
    _set_key(monkeypatch)
    engine = PolicyEngine("MP-02")
    result = engine.authorize(
        _candidate(), _wsv(), _portfolio(), spread_bps=1.0,
        operational_state=OperationalState.EMERGENCY_STOP,
    )
    assert result.verdict is AuthorizationVerdict.NULL_TRADE


def test_insufficient_quorum_gives_null_trade(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quorum below required_quorum=4 (MP-02) must produce NULL_TRADE."""
    _set_key(monkeypatch)
    engine = PolicyEngine("MP-02")  # required_quorum=4
    result = engine.authorize(_candidate(), _wsv(quorum=2), _portfolio(), spread_bps=1.0)
    assert result.verdict is AuthorizationVerdict.NULL_TRADE
    assert any("quorum" in d for d in result.constraint_diagnostics)


def test_spread_exceeds_max_gives_null_trade(monkeypatch: pytest.MonkeyPatch) -> None:
    """Spread above max_spread_bps=2.5 (MP-02) must produce NULL_TRADE."""
    _set_key(monkeypatch)
    engine = PolicyEngine("MP-02")  # max_spread_bps=2.5
    result = engine.authorize(_candidate(), _wsv(), _portfolio(), spread_bps=5.0)
    assert result.verdict is AuthorizationVerdict.NULL_TRADE


def test_flat_candidate_gives_null_trade(monkeypatch: pytest.MonkeyPatch) -> None:
    """Flat direction (a_null) must remain NULL_TRADE."""
    _set_key(monkeypatch)
    engine = PolicyEngine("MP-02")
    result = engine.authorize(_candidate(direction=0.0, size=0.0, stop_price=0.0), _wsv(), _portfolio(), spread_bps=1.0)
    assert result.verdict is AuthorizationVerdict.NULL_TRADE


def test_non_positive_utility_gives_null_trade(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-positive risk-adjusted utility must produce NULL_TRADE."""
    _set_key(monkeypatch)
    engine = PolicyEngine("MP-02")
    result = engine.authorize(
        _candidate(risk_adjusted_utility=-1.0), _wsv(), _portfolio(), spread_bps=1.0
    )
    assert result.verdict is AuthorizationVerdict.NULL_TRADE


# ── authorized / projected ─────────────────────────────────────────────────────


def test_valid_candidate_authorized(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valid candidate with MP-02, NORMAL state, good quorum → AUTHORIZED."""
    _set_key(monkeypatch)
    engine = PolicyEngine("MP-02")  # allow_trading=True, required_quorum=4
    result = engine.authorize(_candidate(), _wsv(quorum=5), _portfolio(), spread_bps=1.0)
    assert result.verdict in (AuthorizationVerdict.AUTHORIZED, AuthorizationVerdict.PROJECTED)
    assert result.instrument == "XAUUSD"


def test_pi_c_projection_caps_size(monkeypatch: pytest.MonkeyPatch) -> None:
    """Size exceeding max_position_size must be projected downward."""
    _set_key(monkeypatch)
    engine = PolicyEngine("MP-02")  # max_position_size=2.0
    # gross_exposure = 1.5 → headroom = 2.0 - 1.5 = 0.5
    result = engine.authorize(
        _candidate(size=1.0), _wsv(quorum=5), _portfolio(gross_exposure=1.5), spread_bps=1.0
    )
    assert result.verdict is AuthorizationVerdict.PROJECTED
    assert result.size == pytest.approx(0.5)


# ── HMAC signature ─────────────────────────────────────────────────────────────


def test_authorized_action_has_hmac_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every CIO-07 must carry a non-empty HMAC signature (NFR-007)."""
    _set_key(monkeypatch)
    engine = PolicyEngine("MP-02")
    result = engine.authorize(_candidate(), _wsv(quorum=5), _portfolio(), spread_bps=1.0)
    assert isinstance(result.hmac_signature, bytes)
    assert len(result.hmac_signature) > 0


def test_missing_hmac_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing AFRP_AUDIT_HMAC_KEY must raise ConfigurationError (EDR-008)."""
    monkeypatch.delenv("AFRP_AUDIT_HMAC_KEY", raising=False)
    engine = PolicyEngine("MP-02")
    with pytest.raises(ConfigurationError):
        engine.authorize(_candidate(), _wsv(quorum=5), _portfolio(), spread_bps=1.0)
