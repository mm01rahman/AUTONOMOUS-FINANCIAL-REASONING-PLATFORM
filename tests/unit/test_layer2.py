"""Unit tests for Layer 2 (SLS-200): DSmT base library and the six agents."""

from __future__ import annotations

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import THETA, StandardFeature
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.contracts.features import (
    FEATURE_DXY_RETURN,
    FEATURE_EWM_VOL,
    FEATURE_FORWARD_SLOPE,
    FEATURE_LOG_RETURN,
    FEATURE_MID,
    FEATURE_REAL_YIELD,
    FEATURE_SENTIMENT,
    FEATURE_SPREAD_BPS,
)
from afrp_runtime.layer2.agents import (
    ALL_AGENTS,
    BehavioralAgent,
    ForwardAgent,
    LiquidityAgent,
    MacroAgent,
    MicrostructureAgent,
    RegimeAgent,
)
from afrp_runtime.layer2.base import (
    intersection_label,
    normalize_masses,
    pad_ignorance,
    union_label,
    vacuous_bba,
)


def feature(feature_id: str, value: float, quality: float = 1.0) -> StandardFeature:
    return StandardFeature(
        envelope=make_envelope(
            producer_subsystem_id="L1-FST",
            cognitive_cycle_id="c1",
            mission_profile_id="MP-04",
            payload_repr=f"{feature_id}:{value}",
        ),
        feature_id=feature_id,
        instrument="XAUUSD",
        value=value,
        window_seconds=60,
        quality=quality,
        source_sequence=1,
    )


def feature_map(**values: float) -> dict[str, StandardFeature]:
    return {fid: feature(fid, val) for fid, val in values.items()}


class TestFocalLabels:
    def test_union_canonical_ordering(self) -> None:
        assert union_label("BULL", "BEAR") == "BEAR|BULL"
        assert union_label("BEAR", "BULL") == "BEAR|BULL"

    def test_intersection_canonical_ordering(self) -> None:
        assert intersection_label("BULL", "BEAR") == "BEAR&BULL"

    def test_unknown_elements_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            union_label("BULL", "SIDEWAYS")


class TestMassAlgebra:
    def test_normalize_sums_to_one(self) -> None:
        masses = normalize_masses({"BULL": 2.0, "BEAR": 1.0, THETA: 1.0})
        assert sum(masses.values()) == pytest.approx(1.0)
        assert masses["BULL"] == pytest.approx(0.5)

    def test_negative_mass_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            normalize_masses({"BULL": -0.1, THETA: 1.1})

    def test_zero_total_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            normalize_masses({"BULL": 0.0})

    def test_vacuous_is_pure_theta(self) -> None:
        assert vacuous_bba() == {THETA: 1.0}

    def test_pad_ignorance_shifts_to_theta(self) -> None:
        padded = pad_ignorance({"BULL": 1.0}, confidence=0.6)
        assert padded["BULL"] == pytest.approx(0.6)
        assert padded[THETA] == pytest.approx(0.4)

    def test_pad_full_confidence_is_identity(self) -> None:
        padded = pad_ignorance({"BULL": 0.7, THETA: 0.3}, confidence=1.0)
        assert padded["BULL"] == pytest.approx(0.7)

    def test_pad_zero_confidence_is_vacuous(self) -> None:
        padded = pad_ignorance({"BULL": 1.0}, confidence=0.0)
        assert padded == {THETA: pytest.approx(1.0)}

    def test_pad_rejects_bad_confidence(self) -> None:
        with pytest.raises(ContractViolationError):
            pad_ignorance({"BULL": 1.0}, confidence=1.5)


class TestDegradationPath:
    def test_missing_feature_degrades_not_crashes(self) -> None:
        agent = MacroAgent("MP-04")
        belief = agent.evaluate("XAUUSD", {})  # zero telemetry
        assert belief.degraded is True
        assert belief.masses == {THETA: pytest.approx(1.0)}

    def test_low_quality_feature_degrades(self) -> None:
        agent = MicrostructureAgent("MP-04")
        features = {
            FEATURE_LOG_RETURN: feature(FEATURE_LOG_RETURN, 0.001, quality=0.05),
            FEATURE_EWM_VOL: feature(FEATURE_EWM_VOL, 0.002),
        }
        belief = agent.evaluate("XAUUSD", features)
        assert belief.degraded is True

    def test_all_agents_survive_empty_telemetry(self) -> None:
        for agent_cls in ALL_AGENTS:
            belief = agent_cls("MP-04").evaluate("XAUUSD", {})
            belief.validate()
            assert belief.degraded is True


class TestAgentBeliefs:
    def test_macro_dovish_yields_bullish(self) -> None:
        agent = MacroAgent("MP-04")
        belief = agent.evaluate(
            "XAUUSD",
            feature_map(**{FEATURE_REAL_YIELD: -1.0, FEATURE_DXY_RETURN: -0.02}),
        )
        assert belief.masses.get("BULL", 0.0) > belief.masses.get("BEAR", 0.0)
        assert belief.degraded is False

    def test_macro_hawkish_yields_bearish(self) -> None:
        agent = MacroAgent("MP-04")
        belief = agent.evaluate(
            "XAUUSD",
            feature_map(**{FEATURE_REAL_YIELD: 1.5, FEATURE_DXY_RETURN: 0.02}),
        )
        assert belief.masses.get("BEAR", 0.0) > belief.masses.get("BULL", 0.0)

    def test_micro_momentum_direction(self) -> None:
        agent = MicrostructureAgent("MP-04")
        up = agent.evaluate(
            "XAUUSD",
            feature_map(**{FEATURE_LOG_RETURN: 0.01, FEATURE_EWM_VOL: 0.002}),
        )
        down = agent.evaluate(
            "XAUUSD",
            feature_map(**{FEATURE_LOG_RETURN: -0.01, FEATURE_EWM_VOL: 0.002}),
        )
        assert up.masses.get("BULL", 0.0) > 0.0 and up.masses.get("BEAR", 0.0) == 0.0
        assert down.masses.get("BEAR", 0.0) > 0.0

    def test_micro_flat_market_is_rangebound(self) -> None:
        agent = MicrostructureAgent("MP-04")
        belief = agent.evaluate(
            "XAUUSD",
            feature_map(**{FEATURE_LOG_RETURN: 0.0, FEATURE_EWM_VOL: 0.002}),
        )
        assert belief.masses.get("RANGE", 0.0) > 0.4

    def test_liquidity_stress_flows_to_theta(self) -> None:
        agent = LiquidityAgent("MP-04")
        calm = agent.evaluate("XAUUSD", feature_map(**{FEATURE_SPREAD_BPS: 1.0}))
        stressed = agent.evaluate("XAUUSD", feature_map(**{FEATURE_SPREAD_BPS: 12.0}))
        assert stressed.masses[THETA] > calm.masses[THETA]

    def test_regime_low_vol_is_range(self) -> None:
        agent = RegimeAgent("MP-04")
        belief = agent.evaluate("XAUUSD", feature_map(**{FEATURE_EWM_VOL: 0.0005}))
        assert belief.masses.get("RANGE", 0.0) > 0.5

    def test_regime_high_vol_is_trending_unknown_direction(self) -> None:
        agent = RegimeAgent("MP-04")
        belief = agent.evaluate("XAUUSD", feature_map(**{FEATURE_EWM_VOL: 0.01}))
        assert belief.masses.get("BEAR|BULL", 0.0) > 0.5

    def test_forward_slope_direction(self) -> None:
        contango = ForwardAgent("MP-04").evaluate(
            "XAUUSD",
            feature_map(**{FEATURE_FORWARD_SLOPE: 0.03, FEATURE_MID: 2400.0}),
        )
        backwardation = ForwardAgent("MP-04").evaluate(
            "XAUUSD",
            feature_map(**{FEATURE_FORWARD_SLOPE: -0.03, FEATURE_MID: 2400.0}),
        )
        assert contango.masses.get("BULL", 0.0) > 0.0
        assert backwardation.masses.get("BEAR", 0.0) > 0.0

    def test_behavioral_contrarian_and_paradox(self) -> None:
        agent = BehavioralAgent("MP-04")
        crowded_long = agent.evaluate(
            "XAUUSD", feature_map(**{FEATURE_SENTIMENT: 0.9})
        )
        conflicted = agent.evaluate("XAUUSD", feature_map(**{FEATURE_SENTIMENT: 0.0}))
        assert crowded_long.masses.get("BEAR", 0.0) > 0.0  # contrarian
        assert conflicted.masses.get("BEAR&BULL", 0.0) > 0.0  # paradoxical mass

    def test_all_beliefs_are_valid_bbas(self) -> None:
        values = {
            FEATURE_REAL_YIELD: -0.5,
            FEATURE_DXY_RETURN: 0.005,
            FEATURE_LOG_RETURN: 0.002,
            FEATURE_EWM_VOL: 0.003,
            FEATURE_SPREAD_BPS: 2.0,
            FEATURE_FORWARD_SLOPE: 0.01,
            FEATURE_SENTIMENT: -0.4,
            FEATURE_MID: 2400.0,
        }
        features = feature_map(**values)
        for agent_cls in ALL_AGENTS:
            belief = agent_cls("MP-04").evaluate("XAUUSD", features)
            belief.validate()
            assert sum(belief.masses.values()) == pytest.approx(1.0)
            assert belief.degraded is False

    def test_determinism_same_inputs_same_masses(self) -> None:
        features = feature_map(**{FEATURE_SPREAD_BPS: 2.5})
        first = LiquidityAgent("MP-04").evaluate("XAUUSD", features)
        second = LiquidityAgent("MP-04").evaluate("XAUUSD", features)
        assert first.masses == second.masses
