"""SYS-03 operational state machine (RT-COMMON, RUN-001 §2).

INITIALIZING → NORMAL; NORMAL ⇄ OBSERVATION; OBSERVATION ⇄ DEGRADED;
DEGRADED → RECOVERY → NORMAL; {NORMAL, OBSERVATION, DEGRADED, RECOVERY} →
EMERGENCY_STOP; EMERGENCY_STOP requires a manual operator reset.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from afrp_runtime.common.errors import StateTransitionError


class OperationalState(StrEnum):
    """SYS-03 states."""

    INITIALIZING = "INITIALIZING"
    NORMAL = "NORMAL"
    OBSERVATION = "OBSERVATION"
    DEGRADED = "DEGRADED"
    RECOVERY = "RECOVERY"
    EMERGENCY_STOP = "EMERGENCY_STOP"


_LEGAL: dict[OperationalState, tuple[OperationalState, ...]] = {
    OperationalState.INITIALIZING: (OperationalState.NORMAL,),
    OperationalState.NORMAL: (
        OperationalState.OBSERVATION,
        OperationalState.EMERGENCY_STOP,
    ),
    OperationalState.OBSERVATION: (
        OperationalState.NORMAL,
        OperationalState.DEGRADED,
        OperationalState.EMERGENCY_STOP,
    ),
    OperationalState.DEGRADED: (
        OperationalState.OBSERVATION,
        OperationalState.RECOVERY,
        OperationalState.EMERGENCY_STOP,
    ),
    OperationalState.RECOVERY: (
        OperationalState.NORMAL,
        OperationalState.EMERGENCY_STOP,
    ),
    OperationalState.EMERGENCY_STOP: (),
}


def legal_targets(state: OperationalState) -> tuple[OperationalState, ...]:
    """Legal successor states of ``state`` per SYS-03."""
    return _LEGAL[state]


@dataclass
class OperationalStateMachine:
    """Mutable SYS-03 tracker with transition history."""

    state: OperationalState = OperationalState.INITIALIZING
    history: list[tuple[OperationalState, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.history:
            self.history.append((self.state, "boot"))

    def transition(self, target: OperationalState, reason: str) -> None:
        """Move to ``target``.

        Raises:
            StateTransitionError: the transition is not in the SYS-03 table.
        """
        if target not in _LEGAL[self.state]:
            raise StateTransitionError(self.state.value, target.value)
        self.state = target
        self.history.append((target, reason))

    def manual_reset(self, operator_id: str) -> None:
        """Operator-only reset out of EMERGENCY_STOP back to INITIALIZING.

        Raises:
            StateTransitionError: called outside EMERGENCY_STOP or without id.
        """
        if self.state is not OperationalState.EMERGENCY_STOP:
            raise StateTransitionError(self.state.value, OperationalState.INITIALIZING.value)
        if not operator_id:
            raise StateTransitionError("EMERGENCY_STOP", "INITIALIZING (missing operator)")
        self.state = OperationalState.INITIALIZING
        self.history.append(
            (OperationalState.INITIALIZING, f"manual reset by {operator_id}")
        )

    @property
    def trading_permitted(self) -> bool:
        """Trading requires NORMAL (Article VIII bias to safety)."""
        return self.state is OperationalState.NORMAL
