"""L4-DEC — risk-adjusted utility optimizer (SLS-401, WP-IMP-0027).

Solves MATH-001 §4 over a pre-allocated candidate grid (NFR-008):

    U_r(a) = U(a) − λ·R(a),    a* = argmax_{a ∈ 𝒜} U_r(a)

U(a) is the scenario-expected P&L; R(a) is expected shortfall over the worst
tail plus stop-loss exposure. Deterministic tie-break by candidate index.
"""

from __future__ import annotations

from dataclasses import dataclass

from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import (
    DecisionContext,
    ExecutionCandidate,
    ScenarioSet,
)
from afrp_runtime.contracts.envelope import make_envelope

SUBSYSTEM_ID = "L4-DEC"

# Pre-allocated action grid (NFR-008): (direction, size_fraction, stop_frac).
_ACTION_GRID: tuple[tuple[float, float, float], ...] = tuple(
    (direction, size_fraction, stop_fraction)
    for direction in (1.0, -1.0)
    for size_fraction in (0.25, 0.5, 1.0)
    for stop_fraction in (0.004, 0.008)
)
_FLAT_ACTION: tuple[float, float, float] = (0.0, 0.0, 0.0)
_TAIL_SHARE = 0.1


@dataclass(frozen=True)
class _Evaluation:
    utility: float
    risk: float
    risk_adjusted: float


def _evaluate(
    direction: float,
    size: float,
    stop_distance: float,
    entry: float,
    scenario_set: ScenarioSet,
    risk_lambda: float,
) -> _Evaluation:
    pnls: list[float] = []
    for scenario in scenario_set.scenarios:
        raw_move = scenario.terminal_price - entry
        adverse = -scenario.max_drawdown if direction > 0 else scenario.max_runup
        if adverse >= stop_distance > 0.0:
            pnl = -stop_distance * size  # stop hit: bounded loss
        else:
            pnl = direction * raw_move * size
        pnls.append(pnl * scenario.probability * len(scenario_set.scenarios))

    expectation = sum(pnls) / len(pnls)
    ordered = sorted(pnls)
    tail_count = max(1, int(len(ordered) * _TAIL_SHARE))
    expected_shortfall = -sum(ordered[:tail_count]) / tail_count
    risk = max(0.0, expected_shortfall)
    return _Evaluation(
        utility=expectation,
        risk=risk,
        risk_adjusted=expectation - risk_lambda * risk,
    )


@dataclass
class UtilityOptimizer:
    """Deterministic CIO-06 producer over the fixed action grid."""

    mission_profile_id: str
    cognitive_cycle_id: str = "cycle-0"

    def optimize(
        self,
        context: DecisionContext,
        scenario_set: ScenarioSet,
        spot_price: float,
    ) -> ExecutionCandidate:
        """Return a* = argmax U_r as an unconstrained execution candidate.

        The flat action (no trade) is always in 𝒜 with U_r = 0; a* falls back
        to it when every sized action is dominated (Article VIII bias).

        Raises:
            ContractViolationError: mismatched scenario set or bad spot.
        """
        if context.scenario_set_id != scenario_set.envelope.message_id:
            raise ContractViolationError(
                "CIO-06", "decision context references a different scenario set"
            )
        if spot_price <= 0.0:
            raise ContractViolationError("CIO-06", f"spot must be positive: {spot_price}")

        best_index = -1
        best = _Evaluation(0.0, 0.0, 0.0)  # flat action baseline: U_r = 0
        best_action = _FLAT_ACTION

        for index, (direction, size_fraction, stop_fraction) in enumerate(_ACTION_GRID):
            size = context.max_position_size * size_fraction
            if size <= 0.0:
                continue
            stop_distance = spot_price * stop_fraction
            evaluation = _evaluate(
                direction, size, stop_distance, spot_price, scenario_set,
                context.risk_aversion_lambda,
            )
            if evaluation.risk_adjusted > best.risk_adjusted + 1e-12:
                best = evaluation
                best_index = index
                best_action = (direction, size, stop_fraction)

        direction, size, stop_fraction = best_action
        stop_price = (
            spot_price * (1.0 - stop_fraction)
            if direction > 0
            else spot_price * (1.0 + stop_fraction)
        ) if direction != 0.0 else 0.0
        target_price = (
            spot_price + direction * 2.0 * spot_price * stop_fraction
            if direction != 0.0
            else 0.0
        )

        envelope = make_envelope(
            producer_subsystem_id=SUBSYSTEM_ID,
            cognitive_cycle_id=self.cognitive_cycle_id,
            mission_profile_id=self.mission_profile_id,
            payload_repr=f"{context.instrument}:{best_index}:{best.risk_adjusted!r}",
            parent_cio_ids=(context.envelope.message_id,),
            trace_id=context.envelope.trace_id,
        )
        return ExecutionCandidate(
            envelope=envelope,
            instrument=context.instrument,
            direction=direction,
            size=size,
            entry_price=spot_price if direction != 0.0 else 0.0,
            stop_price=stop_price,
            target_price=target_price,
            expected_utility=best.utility,
            expected_risk=best.risk,
            risk_adjusted_utility=best.risk_adjusted,
        )
