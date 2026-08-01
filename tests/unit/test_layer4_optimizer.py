"""WP-RT-1014 unit tests for the Utility Optimizer."""

from __future__ import annotations

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import (
    DecisionContext,
    Scenario,
    ScenarioSet,
)
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer4.optimizer import UtilityOptimizer


def _make_scenarios(
    terminal_up: float = 110.0,
    terminal_down: float = 90.0,
    spot: float = 100.0,
) -> ScenarioSet:
    env = make_envelope("L3-SIM", "c0", "MP-02", "sim:scenarios")
    scenarios = (
        # max_drawdown=0.0 → stop never hit regardless of stop distance
        Scenario("s0000", 0.5, terminal_up, 0.0, terminal_up - spot),
        Scenario("s0001", 0.5, terminal_down, -(spot - terminal_down), 0.0),
    )
    return ScenarioSet(
        envelope=env,
        instrument="XAUUSD",
        scenarios=scenarios,
        differential_entropy=0.5,
        horizon_seconds=3600,
        random_seed=42,
    )


def _make_context(
    scenario_set: ScenarioSet,
    max_position_size: float = 2.0,
    risk_aversion_lambda: float = 2.0,
) -> DecisionContext:
    env = make_envelope("L4-FUS", "c0", "MP-02", "synth:context")
    return DecisionContext(
        envelope=env,
        instrument=scenario_set.instrument,
        world_state_id="wsv-id",
        scenario_set_id=scenario_set.envelope.message_id,
        portfolio_state_id="port-id",
        risk_aversion_lambda=risk_aversion_lambda,
        max_position_size=max_position_size,
        available_cash=10_000.0,
    )


# ── basic optimization ─────────────────────────────────────────────────────────


def test_optimizer_returns_execution_candidate() -> None:
    scenarios = _make_scenarios()
    ctx = _make_context(scenarios)
    opt = UtilityOptimizer("MP-02")
    candidate = opt.optimize(ctx, scenarios, spot_price=100.0)
    assert candidate.instrument == "XAUUSD"


def test_optimizer_direction_is_valid_value() -> None:
    scenarios = _make_scenarios()
    ctx = _make_context(scenarios)
    opt = UtilityOptimizer("MP-02")
    candidate = opt.optimize(ctx, scenarios, spot_price=100.0)
    assert candidate.direction in (-1.0, 0.0, 1.0)


def test_optimizer_bullish_scenarios_prefer_long() -> None:
    """Strong upward scenarios should yield a LONG candidate."""
    # terminal_up=120, terminal_down=99 → positive expected return
    scenarios = _make_scenarios(terminal_up=120.0, terminal_down=99.0, spot=100.0)
    ctx = _make_context(scenarios, risk_aversion_lambda=0.1)  # low risk aversion
    opt = UtilityOptimizer("MP-02")
    candidate = opt.optimize(ctx, scenarios, spot_price=100.0)
    assert candidate.direction == 1.0  # LONG selected


def test_optimizer_flat_when_no_edge() -> None:
    """Terminal == entry for all scenarios → no action beats flat (U_r=0)."""
    scenarios = _make_scenarios(terminal_up=100.0, terminal_down=100.0, spot=100.0)
    ctx = _make_context(scenarios, risk_aversion_lambda=2.0)
    opt = UtilityOptimizer("MP-02")
    candidate = opt.optimize(ctx, scenarios, spot_price=100.0)
    assert candidate.direction == 0.0


# ── determinism ────────────────────────────────────────────────────────────────


def test_optimizer_is_deterministic() -> None:
    scenarios = _make_scenarios()
    ctx = _make_context(scenarios)
    opt = UtilityOptimizer("MP-02")
    c1 = opt.optimize(ctx, scenarios, spot_price=100.0)
    c2 = opt.optimize(ctx, scenarios, spot_price=100.0)
    assert c1.direction == c2.direction
    assert c1.size == c2.size
    assert c1.risk_adjusted_utility == c2.risk_adjusted_utility


# ── risk_adjusted_utility fields ───────────────────────────────────────────────


def test_optimizer_utility_fields_are_finite() -> None:
    import math

    scenarios = _make_scenarios()
    ctx = _make_context(scenarios)
    opt = UtilityOptimizer("MP-02")
    c = opt.optimize(ctx, scenarios, spot_price=100.0)
    assert math.isfinite(c.expected_utility)
    assert math.isfinite(c.expected_risk)
    assert math.isfinite(c.risk_adjusted_utility)


# ── contract enforcement ───────────────────────────────────────────────────────


def test_mismatched_scenario_set_raises() -> None:
    scenarios = _make_scenarios()
    other_scenarios = _make_scenarios(terminal_up=115.0)
    ctx = _make_context(scenarios)  # context.scenario_set_id → scenarios.id
    opt = UtilityOptimizer("MP-02")
    with pytest.raises(ContractViolationError):
        opt.optimize(ctx, other_scenarios, spot_price=100.0)


def test_non_positive_spot_raises() -> None:
    scenarios = _make_scenarios()
    ctx = _make_context(scenarios)
    opt = UtilityOptimizer("MP-02")
    with pytest.raises(ContractViolationError):
        opt.optimize(ctx, scenarios, spot_price=0.0)
