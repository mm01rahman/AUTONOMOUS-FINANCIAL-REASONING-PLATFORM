"""L4-FUS — decision synthesizer (SLS-400, WP-IMP-0026).

Contextualizes CIO-04 world state, CIO-05A scenarios and CIO-10 portfolio
into the CIO-05B :class:`DecisionContext` optimization payload. λ derives
from the mission profile risk tolerance (EDR-005 configuration authority).
"""

from __future__ import annotations

from dataclasses import dataclass

from afrp_runtime.common.config import load_mission_profile
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import (
    DecisionContext,
    PortfolioState,
    ScenarioSet,
    WorldStateVector,
)
from afrp_runtime.contracts.envelope import make_envelope

SUBSYSTEM_ID = "L4-FUS"

_BASE_LAMBDA = 2.0


@dataclass
class DecisionSynthesizer:
    """Deterministic CIO-05B producer."""

    mission_profile_id: str
    cognitive_cycle_id: str = "cycle-0"

    def synthesize(
        self,
        world_state: WorldStateVector,
        scenario_set: ScenarioSet,
        portfolio: PortfolioState,
    ) -> DecisionContext:
        """Join the three upstream payloads into one optimization context.

        Raises:
            ContractViolationError: instrument mismatch between inputs.
        """
        if world_state.instrument != scenario_set.instrument:
            raise ContractViolationError(
                "CIO-05B",
                f"instrument mismatch: world={world_state.instrument} "
                f"scenarios={scenario_set.instrument}",
            )
        profile = load_mission_profile(self.mission_profile_id)
        # Higher risk tolerance lowers the effective risk penalty λ.
        risk_lambda = _BASE_LAMBDA / max(profile.risk_tolerance, 0.25)

        envelope = make_envelope(
            producer_subsystem_id=SUBSYSTEM_ID,
            cognitive_cycle_id=self.cognitive_cycle_id,
            mission_profile_id=self.mission_profile_id,
            payload_repr=(
                f"{world_state.instrument}:{world_state.envelope.message_id}"
                f":{scenario_set.envelope.message_id}"
            ),
            parent_cio_ids=(
                world_state.envelope.message_id,
                scenario_set.envelope.message_id,
                portfolio.envelope.message_id,
            ),
            trace_id=world_state.envelope.trace_id,
        )
        return DecisionContext(
            envelope=envelope,
            instrument=world_state.instrument,
            world_state_id=world_state.envelope.message_id,
            scenario_set_id=scenario_set.envelope.message_id,
            portfolio_state_id=portfolio.envelope.message_id,
            risk_aversion_lambda=risk_lambda,
            max_position_size=profile.max_position_size,
            available_cash=portfolio.cash,
        )
