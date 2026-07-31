"""L4-VAL — policy engine (SLS-402, WP-IMP-0028).

Projects the unconstrained candidate a* onto the feasible constraint set 𝒞
(MATH-001 §4):  a_e = Π_𝒞(a*). When projection fails, when the mission
profile forbids trading, or when the operational state is not NORMAL, the
authorized action defaults to a_null — No Trade over a Poor Trade
(Article VIII). Every authorization carries an HMAC signature (NFR-007);
the signing key arrives via environment only (EDR-008).
"""

from __future__ import annotations

import hmac
import os
from dataclasses import dataclass
from hashlib import sha256

from afrp_runtime.common.config import MissionProfile, load_mission_profile
from afrp_runtime.common.errors import ConfigurationError
from afrp_runtime.common.statemachine import OperationalState
from afrp_runtime.contracts.cio import (
    AuthorizationVerdict,
    AuthorizedAction,
    ExecutionCandidate,
    PortfolioState,
    WorldStateVector,
)
from afrp_runtime.contracts.envelope import make_envelope

SUBSYSTEM_ID = "L4-VAL"
_HMAC_ENV_VAR = "AFRP_AUDIT_HMAC_KEY"


def _signing_key() -> bytes:
    key = os.environ.get(_HMAC_ENV_VAR, "")
    if not key:
        raise ConfigurationError(
            _HMAC_ENV_VAR, "audit HMAC key must be provided via environment (EDR-008)"
        )
    return key.encode("utf-8")


def sign_action(payload: str) -> bytes:
    """HMAC-SHA256 signature over the action payload (NFR-007)."""
    return hmac.new(_signing_key(), payload.encode("utf-8"), sha256).digest()


@dataclass
class PolicyEngine:
    """Deterministic CIO-07 producer enforcing the feasible set 𝒞."""

    mission_profile_id: str
    cognitive_cycle_id: str = "cycle-0"

    def authorize(
        self,
        candidate: ExecutionCandidate,
        world_state: WorldStateVector,
        portfolio: PortfolioState,
        spread_bps: float,
        operational_state: OperationalState = OperationalState.NORMAL,
    ) -> AuthorizedAction:
        """Validate/project a* into a_e, defaulting to a_null on any breach."""
        profile = load_mission_profile(self.mission_profile_id)
        diagnostics: list[str] = []

        direction = candidate.direction
        size = candidate.size
        verdict = AuthorizationVerdict.AUTHORIZED

        if direction == 0.0 or size <= 0.0:
            diagnostics.append("candidate is flat: a_null by construction")
            verdict = AuthorizationVerdict.NULL_TRADE
        if operational_state is not OperationalState.NORMAL:
            diagnostics.append(
                f"SYS-03 state {operational_state}: trading requires NORMAL"
            )
            verdict = AuthorizationVerdict.NULL_TRADE
        if not profile.allow_trading:
            diagnostics.append(f"mission profile {profile.profile_id} forbids trading")
            verdict = AuthorizationVerdict.NULL_TRADE
        if world_state.agent_quorum < profile.required_quorum:
            diagnostics.append(
                f"quorum {world_state.agent_quorum} < required {profile.required_quorum}"
            )
            verdict = AuthorizationVerdict.NULL_TRADE
        if spread_bps > profile.max_spread_bps:
            diagnostics.append(
                f"spread {spread_bps:.2f}bps exceeds limit {profile.max_spread_bps}bps"
            )
            verdict = AuthorizationVerdict.NULL_TRADE
        if candidate.risk_adjusted_utility <= 0.0 and direction != 0.0:
            diagnostics.append("non-positive risk-adjusted utility: no edge")
            verdict = AuthorizationVerdict.NULL_TRADE
        if direction != 0.0 and candidate.stop_price <= 0.0:
            diagnostics.append("stop-loss mandatory for sized actions")
            verdict = AuthorizationVerdict.NULL_TRADE

        if verdict is AuthorizationVerdict.AUTHORIZED:
            # Π_𝒞 size projection: position and exposure caps.
            projected_size = min(size, profile.max_position_size)
            headroom = max(0.0, profile.max_position_size - portfolio.gross_exposure)
            projected_size = min(projected_size, headroom)
            if projected_size <= 0.0:
                diagnostics.append("exposure cap leaves no headroom: a_null")
                verdict = AuthorizationVerdict.NULL_TRADE
                size = 0.0
            elif projected_size < size:
                diagnostics.append(
                    f"size projected {size:.4f} -> {projected_size:.4f} (Pi_C)"
                )
                verdict = AuthorizationVerdict.PROJECTED
                size = projected_size

        if verdict is AuthorizationVerdict.NULL_TRADE:
            direction = 0.0
            size = 0.0
            entry = 0.0
            stop = 0.0
        else:
            entry = candidate.entry_price
            stop = candidate.stop_price

        payload = (
            f"{candidate.envelope.message_id}:{verdict}:{direction}:{size}:{entry}:{stop}"
        )
        envelope = make_envelope(
            producer_subsystem_id=SUBSYSTEM_ID,
            cognitive_cycle_id=self.cognitive_cycle_id,
            mission_profile_id=self.mission_profile_id,
            payload_repr=payload,
            parent_cio_ids=(
                candidate.envelope.message_id,
                world_state.envelope.message_id,
            ),
            trace_id=candidate.envelope.trace_id,
        )
        return AuthorizedAction(
            envelope=envelope,
            candidate_id=candidate.envelope.message_id,
            verdict=verdict,
            instrument=candidate.instrument,
            direction=direction,
            size=size,
            entry_price=entry,
            stop_price=stop,
            mission_profile_id=self.mission_profile_id,
            constraint_diagnostics=tuple(diagnostics),
            hmac_signature=sign_action(payload),
        )


def null_action_for(profile: MissionProfile) -> str:
    """Human-readable a_null rationale for a profile (Article VIII)."""
    return f"a_null under {profile.profile_id}: No Trade preferred over Poor Trade"
