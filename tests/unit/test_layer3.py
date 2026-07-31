"""Unit tests for Layer 3: PCR5 core (oracles + properties), WRM, simulator."""

from __future__ import annotations

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import (
    THETA,
    CalibrationWeights,
    DomainBelief,
    WorldStateVector,
)
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer3.dsmt import (
    EMPTY,
    combine_all,
    combine_pcr5,
    discount,
    intersect,
    parse_label,
    pignistic,
    render_label,
)
from afrp_runtime.layer3.simulator import ScenarioSimulator
from afrp_runtime.layer3.worldmodel import EXPECTED_AGENTS, WorldModelKernel


def belief(
    agent_id: str,
    masses: dict[str, float],
    reliability: float = 1.0,
    degraded: bool = False,
) -> DomainBelief:
    return DomainBelief(
        envelope=make_envelope(
            producer_subsystem_id=agent_id,
            cognitive_cycle_id="c1",
            mission_profile_id="MP-04",
            payload_repr=f"{agent_id}:{sorted(masses.items())!r}",
        ),
        agent_id=agent_id,
        instrument="XAUUSD",
        masses=masses,
        reliability=reliability,
        degraded=degraded,
    )


class TestElementAlgebra:
    def test_parse_render_round_trip(self) -> None:
        for label in ("BULL", "BEAR|BULL", "BEAR&BULL", THETA, "BULL|RANGE"):
            assert render_label(parse_label(label)) == label

    def test_theta_intersection_is_identity(self) -> None:
        for label in ("BULL", "BEAR", "RANGE", "BEAR&BULL", "BEAR|BULL"):
            element = parse_label(label)
            assert intersect(parse_label(THETA), element) == element

    def test_directional_paradox_allowed(self) -> None:
        meet = intersect(parse_label("BULL"), parse_label("BEAR"))
        assert render_label(meet) == "BEAR&BULL"

    def test_range_direction_constrained_empty(self) -> None:
        assert intersect(parse_label("RANGE"), parse_label("BULL")) == EMPTY
        assert intersect(parse_label("RANGE"), parse_label("BEAR")) == EMPTY
        assert intersect(parse_label("RANGE"), parse_label("BEAR|BULL")) == EMPTY

    def test_absorption_law(self) -> None:
        meet = intersect(parse_label("BEAR|BULL"), parse_label("BULL"))
        assert render_label(meet) == "BULL"

    def test_constrained_label_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            parse_label("RANGE&BULL")

    def test_unknown_label_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            parse_label("SIDEWAYS")


class TestPcr5Oracles:
    """Hand-worked numeric oracles (MATH-001 §2, model M1)."""

    def test_directional_opposition_becomes_paradox_mass(self) -> None:
        fused, conflict = combine_pcr5(
            {"BULL": 0.6, THETA: 0.4}, {"BEAR": 0.5, THETA: 0.5}
        )
        assert conflict == pytest.approx(0.0)
        assert fused["BEAR&BULL"] == pytest.approx(0.30)
        assert fused["BULL"] == pytest.approx(0.30)
        assert fused["BEAR"] == pytest.approx(0.20)
        assert fused[THETA] == pytest.approx(0.20)

    def test_direction_vs_range_conflict_oracle(self) -> None:
        fused, conflict = combine_pcr5(
            {"BULL": 0.7, THETA: 0.3}, {"RANGE": 0.6, THETA: 0.4}
        )
        assert conflict == pytest.approx(0.42)
        assert fused["BULL"] == pytest.approx(0.28 + 0.49 * 0.6 / 1.3, rel=1e-9)
        assert fused["RANGE"] == pytest.approx(0.18 + 0.36 * 0.7 / 1.3, rel=1e-9)
        assert fused[THETA] == pytest.approx(0.12)

    def test_union_vs_range_conflict_oracle(self) -> None:
        fused, conflict = combine_pcr5(
            {"BEAR|BULL": 0.8, THETA: 0.2}, {"RANGE": 0.5, THETA: 0.5}
        )
        assert conflict == pytest.approx(0.40)
        assert fused["BEAR|BULL"] == pytest.approx(0.4 + 0.64 * 0.5 / 1.3, rel=1e-9)
        assert fused["RANGE"] == pytest.approx(0.1 + 0.25 * 0.8 / 1.3, rel=1e-9)
        assert fused[THETA] == pytest.approx(0.10)

    def test_vacuous_source_is_neutral(self) -> None:
        original = {"BULL": 0.55, "RANGE": 0.25, THETA: 0.20}
        fused, conflict = combine_pcr5(original, {THETA: 1.0})
        assert conflict == pytest.approx(0.0)
        for label, value in original.items():
            assert fused[label] == pytest.approx(value)


class TestPcr5Properties:
    CASES = (
        ({"BULL": 0.6, THETA: 0.4}, {"BEAR": 0.5, THETA: 0.5}),
        ({"BULL": 0.7, THETA: 0.3}, {"RANGE": 0.6, THETA: 0.4}),
        ({"BEAR|BULL": 0.5, "RANGE": 0.3, THETA: 0.2}, {"BEAR": 0.4, THETA: 0.6}),
        ({"BEAR&BULL": 0.4, THETA: 0.6}, {"RANGE": 0.7, THETA: 0.3}),
        ({"BULL": 0.34, "BEAR": 0.33, "RANGE": 0.33}, {"BULL": 0.9, THETA: 0.1}),
    )

    @pytest.mark.parametrize("m1,m2", CASES)
    def test_masses_stay_normalized_and_nonnegative(
        self, m1: dict[str, float], m2: dict[str, float]
    ) -> None:
        fused, _ = combine_pcr5(m1, m2)
        assert all(value >= 0.0 for value in fused.values())
        assert sum(fused.values()) == pytest.approx(1.0)

    @pytest.mark.parametrize("m1,m2", CASES)
    def test_two_source_commutativity(
        self, m1: dict[str, float], m2: dict[str, float]
    ) -> None:
        ab, conflict_ab = combine_pcr5(m1, m2)
        ba, conflict_ba = combine_pcr5(m2, m1)
        assert conflict_ab == pytest.approx(conflict_ba)
        assert set(ab) == set(ba)
        for label in ab:
            assert ab[label] == pytest.approx(ba[label])

    def test_sequential_fold_accumulates_conflict(self) -> None:
        sources = [
            {"BULL": 0.6, THETA: 0.4},
            {"RANGE": 0.5, THETA: 0.5},
            {"BEAR": 0.4, THETA: 0.6},
        ]
        fused, conflict = combine_all(sources)
        assert sum(fused.values()) == pytest.approx(1.0)
        assert conflict > 0.0

    def test_empty_source_list_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            combine_all([])

    def test_invalid_bba_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            combine_pcr5({"BULL": 0.7}, {THETA: 1.0})  # does not sum to 1


class TestDiscounting:
    def test_discount_oracle(self) -> None:
        discounted = discount({"BULL": 0.7, THETA: 0.3}, 0.8)
        assert discounted["BULL"] == pytest.approx(0.56)
        assert discounted[THETA] == pytest.approx(0.44)

    def test_zero_weight_is_vacuous(self) -> None:
        assert discount({"BULL": 1.0}, 0.0) == {THETA: pytest.approx(1.0)}

    def test_unit_weight_is_identity(self) -> None:
        original = {"BULL": 0.7, THETA: 0.3}
        assert discount(original, 1.0)["BULL"] == pytest.approx(0.7)

    def test_out_of_range_weight_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            discount({THETA: 1.0}, 1.2)


class TestPignistic:
    def test_pignistic_oracle(self) -> None:
        betp = pignistic(
            {"BULL": 0.4, "BEAR|BULL": 0.2, "BEAR&BULL": 0.2, THETA: 0.2}
        )
        assert betp["BULL"] == pytest.approx(0.4 + 0.1 + 0.1 + 0.2 / 3)
        assert betp["BEAR"] == pytest.approx(0.1 + 0.1 + 0.2 / 3)
        assert betp["RANGE"] == pytest.approx(0.2 / 3)
        assert sum(betp.values()) == pytest.approx(1.0)


class TestWorldModelKernel:
    def full_belief_set(self) -> list[DomainBelief]:
        return [
            belief("L2-MAC", {"BULL": 0.5, THETA: 0.5}),
            belief("L2-MIC", {"BULL": 0.4, "RANGE": 0.2, THETA: 0.4}),
            belief("L2-LIQ", {"RANGE": 0.5, THETA: 0.5}),
            belief("L2-REG", {"BEAR|BULL": 0.6, THETA: 0.4}),
            belief("L2-FOR", {"BULL": 0.3, THETA: 0.7}),
            belief("L2-BEH", {"BEAR": 0.2, "BEAR&BULL": 0.1, THETA: 0.7}),
        ]

    def test_full_quorum_fusion(self) -> None:
        kernel = WorldModelKernel("MP-04")
        state = kernel.fuse("XAUUSD", self.full_belief_set())
        assert state.agent_quorum == 6
        assert sum(state.fused_masses.values()) == pytest.approx(1.0)
        assert state.epistemic_uncertainty == state.fused_masses.get(THETA, 0.0)
        assert len(state.fusion_trace) == 7  # six agents + pcr5 summary

    def test_missing_agents_padded_not_fatal(self) -> None:
        kernel = WorldModelKernel("MP-04")
        state = kernel.fuse("XAUUSD", self.full_belief_set()[:2])
        assert state.agent_quorum == 2
        padded = [line for line in state.fusion_trace if "MISSING" in line]
        assert len(padded) == 4

    def test_zero_healthy_sources_returns_vacuous_degraded_state(self) -> None:
        kernel = WorldModelKernel("MP-04")
        degraded = [
            belief(agent_id, {THETA: 1.0}, degraded=True)
            for agent_id in EXPECTED_AGENTS
        ]
        state = kernel.fuse("XAUUSD", degraded)
        assert state.agent_quorum == 0
        assert state.fused_masses == {THETA: pytest.approx(1.0)}
        assert state.regime_context == THETA
        assert state.active_hypotheses == ()

    def test_calibration_weights_discount_sources(self) -> None:
        kernel = WorldModelKernel("MP-04")
        beliefs = self.full_belief_set()
        weights = CalibrationWeights(
            envelope=make_envelope(
                producer_subsystem_id="L6-OPT",
                cognitive_cycle_id="c1",
                mission_profile_id="MP-04",
                payload_repr="w",
            ),
            agent_weights={agent_id: 0.0 for agent_id in EXPECTED_AGENTS},
            brier_scores={},
            window_cycles=10,
        )
        state = kernel.fuse("XAUUSD", beliefs, weights)
        # Full discounting collapses every source to vacuity.
        assert state.fused_masses[THETA] == pytest.approx(1.0)

    def test_determinism_same_inputs_same_masses(self) -> None:
        kernel = WorldModelKernel("MP-04")
        first = kernel.fuse("XAUUSD", self.full_belief_set())
        second = kernel.fuse("XAUUSD", self.full_belief_set())
        assert first.fused_masses == second.fused_masses


class TestScenarioSimulator:
    def world_state(self, masses: dict[str, float]) -> WorldStateVector:
        return WorldStateVector(
            envelope=make_envelope(
                producer_subsystem_id="L3-WRM",
                cognitive_cycle_id="c1",
                mission_profile_id="MP-04",
                payload_repr="ws",
            ),
            instrument="XAUUSD",
            fused_masses=masses,
            epistemic_uncertainty=masses.get(THETA, 0.0),
            conflict_mass=0.0,
            regime_context="BULL",
            active_hypotheses=("BULL",),
            agent_quorum=6,
            fusion_trace=(),
        )

    def test_scenarioset_is_valid_distribution(self) -> None:
        simulator = ScenarioSimulator("MP-04", n_paths=128)
        result = simulator.simulate(self.world_state({"BULL": 0.6, THETA: 0.4}), 2400.0)
        result.validate()
        assert result.random_seed == 42
        assert result.scenarios

    def test_deterministic_replay_same_cycle(self) -> None:
        simulator = ScenarioSimulator("MP-04", n_paths=64)
        state = self.world_state({"BULL": 0.6, THETA: 0.4})
        first = simulator.simulate(state, 2400.0, cycle=7)
        second = simulator.simulate(state, 2400.0, cycle=7)
        assert [s.terminal_price for s in first.scenarios] == [
            s.terminal_price for s in second.scenarios
        ]

    def test_cycles_are_independent(self) -> None:
        simulator = ScenarioSimulator("MP-04", n_paths=64)
        state = self.world_state({"BULL": 0.6, THETA: 0.4})
        first = simulator.simulate(state, 2400.0, cycle=1)
        second = simulator.simulate(state, 2400.0, cycle=2)
        assert [s.terminal_price for s in first.scenarios] != [
            s.terminal_price for s in second.scenarios
        ]

    def test_bullish_tilt_shifts_mean_terminal(self) -> None:
        simulator = ScenarioSimulator("MP-04", n_paths=256)
        bull = simulator.simulate(self.world_state({"BULL": 0.8, THETA: 0.2}), 2400.0)
        bear = simulator.simulate(self.world_state({"BEAR": 0.8, THETA: 0.2}), 2400.0)
        mean_bull = sum(s.terminal_price for s in bull.scenarios) / len(bull.scenarios)
        mean_bear = sum(s.terminal_price for s in bear.scenarios) / len(bear.scenarios)
        assert mean_bull > mean_bear

    def test_manifold_bound_respected(self) -> None:
        simulator = ScenarioSimulator("MP-04", n_paths=128, max_abs_log_move=0.02)
        result = simulator.simulate(self.world_state({THETA: 1.0}), 2400.0)
        import math

        bound_high = 2400.0 * math.exp(0.02)
        bound_low = 2400.0 * math.exp(-0.02)
        for scenario in result.scenarios:
            assert bound_low <= scenario.terminal_price <= bound_high

    def test_nonpositive_spot_rejected(self) -> None:
        simulator = ScenarioSimulator("MP-04")
        with pytest.raises(ContractViolationError):
            simulator.simulate(self.world_state({THETA: 1.0}), 0.0)
