"""RSM-1.0 repository lifecycle state machine (WP-IMP-0008).

Models the EGP-2.0 lifecycle: INITIAL → BASELINE_VERIFIED →
WORK_PACKAGE_LOADED → PRECONDITIONS_VERIFIED → EXECUTION_AUTHORIZED →
EXECUTING → VALIDATING → EVIDENCE_GENERATED → REVIEW_PENDING →
COMPLETED | HALTED. Any state may transition to HALTED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from afrp.core.exceptions import InvariantError


class LifecycleState(StrEnum):
    """RSM-1.0 lifecycle states."""

    INITIAL = "INITIAL"
    BASELINE_VERIFIED = "BASELINE_VERIFIED"
    WORK_PACKAGE_LOADED = "WORK_PACKAGE_LOADED"
    PRECONDITIONS_VERIFIED = "PRECONDITIONS_VERIFIED"
    EXECUTION_AUTHORIZED = "EXECUTION_AUTHORIZED"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    EVIDENCE_GENERATED = "EVIDENCE_GENERATED"
    REVIEW_PENDING = "REVIEW_PENDING"
    COMPLETED = "COMPLETED"
    HALTED = "HALTED"


_FORWARD: dict[LifecycleState, tuple[LifecycleState, ...]] = {
    LifecycleState.INITIAL: (LifecycleState.BASELINE_VERIFIED,),
    LifecycleState.BASELINE_VERIFIED: (LifecycleState.WORK_PACKAGE_LOADED,),
    LifecycleState.WORK_PACKAGE_LOADED: (LifecycleState.PRECONDITIONS_VERIFIED,),
    LifecycleState.PRECONDITIONS_VERIFIED: (LifecycleState.EXECUTION_AUTHORIZED,),
    LifecycleState.EXECUTION_AUTHORIZED: (LifecycleState.EXECUTING,),
    LifecycleState.EXECUTING: (LifecycleState.VALIDATING,),
    LifecycleState.VALIDATING: (LifecycleState.EVIDENCE_GENERATED,),
    LifecycleState.EVIDENCE_GENERATED: (LifecycleState.REVIEW_PENDING,),
    LifecycleState.REVIEW_PENDING: (LifecycleState.COMPLETED,),
    LifecycleState.COMPLETED: (),
    LifecycleState.HALTED: (),
}


def legal_transitions(state: LifecycleState) -> tuple[LifecycleState, ...]:
    """Legal successors of ``state`` (HALTED reachable from any live state)."""
    forward = _FORWARD[state]
    if state in (LifecycleState.COMPLETED, LifecycleState.HALTED):
        return forward
    return (*forward, LifecycleState.HALTED)


@dataclass
class LifecycleMachine:
    """Mutable lifecycle tracker enforcing the RSM-1.0 transition table."""

    state: LifecycleState = LifecycleState.INITIAL
    history: list[tuple[LifecycleState, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.history:
            self.history.append((self.state, "initialized"))

    def advance(self, target: LifecycleState, note: str = "") -> None:
        """Transition to ``target``.

        Raises:
            InvariantError: the transition is not in the RSM-1.0 table.
        """
        if target not in legal_transitions(self.state):
            raise InvariantError(
                "RSM-1.0",
                f"illegal transition {self.state} -> {target}",
            )
        self.state = target
        self.history.append((target, note))

    def halt(self, reason: str) -> None:
        """Transition to HALTED from any live state."""
        self.advance(LifecycleState.HALTED, reason)

    @property
    def terminal(self) -> bool:
        """True in COMPLETED or HALTED."""
        return self.state in (LifecycleState.COMPLETED, LifecycleState.HALTED)
