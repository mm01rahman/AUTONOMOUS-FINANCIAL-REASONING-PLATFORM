"""Unit tests for Layer 4: synthesizer, optimizer (U_r), policy engine (Π_C)."""

from __future__ import annotations

import pytest
from afrp_runtime.common.errors import ConfigurationError, ContractViolationError
from afrp_runtime.common.statemachine import OperationalState
from afrp_runtime.contracts.cio import (
    THETA,
    AuthorizationVerdict,
    DecisionContext,
    ExecutionCandidate,
    PortfolioState,
    Scenario,
    ScenarioSet,
    WorldStateVector,
)
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer4.optimizer import UtilityOptimizer
from afrp_runtime.layer4.policy import PolicyEngine
from afrp_runtime.layer4.synthesizer import DecisionSynthesizer

SPOT = 2400.0


def env(producer: str) -> object:
    return make_envelope(
        producer_subsystem_id=producer,
        cognitive_cycle_id="c1",
        mission_profile_id="MP-02",
        payload_repr=producer,
    )


def world_state(quorum: int = 6) -> WorldStateVector:
    return WorldStateVector(
        envelope=make_envelope(
            producer_subsystem_id="L3-WRM",
            cognitive_cycle_id="c1",
            mission_profile_id="MP-02",
            payload_repr="ws",
        ),
        instrument="XAUUSD",
        fused_masses={"BULL": 0.6, THETA: 0.4},
        epistemic_uncertainty=0.4,
        conflict_mass=0.05,
        regime_context="BULL",
        active_hypotheses=("BULL",),
        agent_quorum=quorum,
        fusion_trace=(),
    )


def scenario_set(up_bias: float) -> ScenarioSet:
    """Three-scenario fixture; ``up_bias`` shifts terminal prices."""
    if up_bias >= 0.0:
        extrema = ((-6.0, 34.0), (-9.0, 12.0), (-18.0, 4.0))
    else:
        extrema = ((-34.0, 6.0), (-12.0, 9.0), (-4.0, 18.0))
    scenarios = (
        Scenario("s1", 0.5, SPOT + 30.0 * up_bias, *extrema[0]),
        Scenario("s2", 0.3, SPOT + 6.0 * up_bias, *extrema[1]),
        Scenario("s3", 0.2, SPOT - 12.0 * up_bias, *extrema[2]),
    )
    return ScenarioSet(
        envelope=make_envelope(
            producer_subsystem_id="L3-SIM",
            cognitive_cycle_id="c1",
            mission_profile_id="MP-02",
            payload_repr=f"scen:{up_bias}",
        ),
        instrument="XAUUSD",
        scenarios=scenarios,
        differential_entropy=1.0,
        horizon_seconds=3600,
        random_seed=42,
    )


def portfolio(cash: float = 100_000.0, exposure: float = 0.0) -> PortfolioState:
    return PortfolioState(
        envelope=make_envelope(
            producer_subsystem_id="L5-EXE",
            cognitive_cycle_id="c1",
            mission_profile_id="MP-02",
            payload_repr="pf",
        ),
        positions=(),
        cash=cash,
        equity=cash,
        gross_exposure=exposure,
        reconciled_at_ns=0,
    )


def context(up_bias: float = 1.0) -> tuple[DecisionContext, ScenarioSet]:
    scenarios = scenario_set(up_bias)
    ctx = DecisionSynthesizer("MP-02").synthesize(world_state(), scenarios, portfolio())
    return ctx, scenarios


def candidate_via_optimizer(up_bias: float = 1.0) -> ExecutionCandidate:
    ctx, scenarios = context(up_bias)
    return UtilityOptimizer("MP-02").optimize(ctx, scenarios, SPOT)


@pytest.fixture(autouse=True)
def _hmac_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AFRP_AUDIT_HMAC_KEY", "test-key-not-a-secret")


class TestSynthesizer:
    def test_context_joins_provenance(self) -> None:
        ctx, scenarios = context()
        assert ctx.world_state_id and ctx.scenario_set_id == scenarios.envelope.message_id
        assert ctx.risk_aversion_lambda == pytest.approx(2.0)  # MP-02 tolerance 1.0
        assert ctx.max_position_size == pytest.approx(2.0)

    def test_conservative_profile_raises_lambda(self) -> None:
        scenarios = scenario_set(1.0)
        ctx = DecisionSynthesizer("MP-01").synthesize(
            world_state(), scenarios, portfolio()
        )
        assert ctx.risk_aversion_lambda == pytest.approx(4.0)  # MP-01 tolerance 0.5

    def test_instrument_mismatch_rejected(self) -> None:
        scenarios = scenario_set(1.0)
        bad_world = WorldStateVector(
            envelope=make_envelope(
                producer_subsystem_id="L3-WRM",
                cognitive_cycle_id="c1",
                mission_profile_id="MP-02",
                payload_repr="ws2",
            ),
            instrument="EURUSD",
            fused_masses={THETA: 1.0},
            epistemic_uncertainty=1.0,
            conflict_mass=0.0,
            regime_context=THETA,
            active_hypotheses=(),
            agent_quorum=6,
            fusion_trace=(),
        )
        with pytest.raises(ContractViolationError):
            DecisionSynthesizer("MP-02").synthesize(bad_world, scenarios, portfolio())


class TestUtilityOptimizer:
    def test_bullish_scenarios_produce_long(self) -> None:
        candidate = candidate_via_optimizer(up_bias=1.0)
        assert candidate.direction == 1.0
        assert candidate.size > 0.0
        assert candidate.risk_adjusted_utility > 0.0
        assert candidate.stop_price < candidate.entry_price

    def test_bearish_scenarios_produce_short(self) -> None:
        candidate = candidate_via_optimizer(up_bias=-1.0)
        assert candidate.direction == -1.0
        assert candidate.stop_price > candidate.entry_price

    def test_flat_fallback_when_dominated(self) -> None:
        # Symmetric, tiny-move scenarios: any sized action carries tail risk
        # with negligible edge -> flat action must win (Article VIII).
        scenarios = ScenarioSet(
            envelope=make_envelope(
                producer_subsystem_id="L3-SIM",
                cognitive_cycle_id="c1",
                mission_profile_id="MP-02",
                payload_repr="flat",
            ),
            instrument="XAUUSD",
            scenarios=(
                Scenario("s1", 0.5, SPOT + 0.5, -8.0, 8.0),
                Scenario("s2", 0.5, SPOT - 0.5, -8.0, 8.0),
            ),
            differential_entropy=0.5,
            horizon_seconds=3600,
            random_seed=42,
        )
        ctx = DecisionSynthesizer("MP-01").synthesize(
            world_state(), scenarios, portfolio()
        )
        candidate = UtilityOptimizer("MP-01").optimize(ctx, scenarios, SPOT)
        assert candidate.direction == 0.0
        assert candidate.risk_adjusted_utility == 0.0

    def test_determinism(self) -> None:
        first = candidate_via_optimizer()
        second = candidate_via_optimizer()
        assert first.direction == second.direction
        assert first.size == second.size
        assert first.risk_adjusted_utility == pytest.approx(
            second.risk_adjusted_utility
        )

    def test_mismatched_context_rejected(self) -> None:
        ctx, _ = context()
        other_scenarios = scenario_set(1.0)
        with pytest.raises(ContractViolationError):
            UtilityOptimizer("MP-02").optimize(ctx, other_scenarios, SPOT)

    def test_bad_spot_rejected(self) -> None:
        ctx, scenarios = context()
        with pytest.raises(ContractViolationError):
            UtilityOptimizer("MP-02").optimize(ctx, scenarios, -1.0)


class TestPolicyEngine:
    def test_healthy_candidate_authorized_with_signature(self) -> None:
        candidate = candidate_via_optimizer()
        action = PolicyEngine("MP-02").authorize(
            candidate, world_state(), portfolio(), spread_bps=1.0
        )
        assert action.verdict is AuthorizationVerdict.AUTHORIZED
        assert action.size == candidate.size
        assert len(action.hmac_signature) == 32
        assert action.candidate_id == candidate.envelope.message_id

    def test_quorum_shortfall_yields_null(self) -> None:
        candidate = candidate_via_optimizer()
        action = PolicyEngine("MP-02").authorize(
            candidate, world_state(quorum=2), portfolio(), spread_bps=1.0
        )
        assert action.verdict is AuthorizationVerdict.NULL_TRADE
        assert action.direction == 0.0 and action.size == 0.0
        assert any("quorum" in d for d in action.constraint_diagnostics)

    def test_spread_breach_yields_null(self) -> None:
        candidate = candidate_via_optimizer()
        action = PolicyEngine("MP-02").authorize(
            candidate, world_state(), portfolio(), spread_bps=50.0
        )
        assert action.verdict is AuthorizationVerdict.NULL_TRADE

    def test_non_trading_profile_yields_null(self) -> None:
        candidate = candidate_via_optimizer()
        action = PolicyEngine("MP-05").authorize(
            candidate, world_state(), portfolio(), spread_bps=0.0
        )
        assert action.verdict is AuthorizationVerdict.NULL_TRADE

    def test_degraded_operational_state_yields_null(self) -> None:
        candidate = candidate_via_optimizer()
        action = PolicyEngine("MP-02").authorize(
            candidate,
            world_state(),
            portfolio(),
            spread_bps=1.0,
            operational_state=OperationalState.DEGRADED,
        )
        assert action.verdict is AuthorizationVerdict.NULL_TRADE

    def test_exposure_headroom_projection(self) -> None:
        candidate = candidate_via_optimizer()
        assert candidate.size == pytest.approx(2.0)  # MP-02 full size preferred
        action = PolicyEngine("MP-02").authorize(
            candidate, world_state(), portfolio(exposure=1.5), spread_bps=1.0
        )
        assert action.verdict is AuthorizationVerdict.PROJECTED
        assert action.size == pytest.approx(0.5)
        assert any("Pi_C" in d for d in action.constraint_diagnostics)

    def test_zero_headroom_yields_null(self) -> None:
        candidate = candidate_via_optimizer()
        action = PolicyEngine("MP-02").authorize(
            candidate, world_state(), portfolio(exposure=2.0), spread_bps=1.0
        )
        assert action.verdict is AuthorizationVerdict.NULL_TRADE

    def test_missing_hmac_key_is_configuration_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("AFRP_AUDIT_HMAC_KEY", raising=False)
        candidate = candidate_via_optimizer()
        with pytest.raises(ConfigurationError):
            PolicyEngine("MP-02").authorize(
                candidate, world_state(), portfolio(), spread_bps=1.0
            )

    def test_null_actions_still_signed_and_explained(self) -> None:
        candidate = candidate_via_optimizer()
        action = PolicyEngine("MP-05").authorize(
            candidate, world_state(), portfolio(), spread_bps=0.0
        )
        assert action.hmac_signature  # audit trail even for a_null (NFR-007)
        assert action.constraint_diagnostics  # explainability (Article III)
