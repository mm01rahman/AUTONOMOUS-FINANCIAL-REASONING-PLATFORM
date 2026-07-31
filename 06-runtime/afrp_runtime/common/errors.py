"""Runtime exception taxonomy (RT-COMMON, EDR-004).

Every runtime failure is a typed :class:`AfrpRuntimeError` subclass. Catching
bare ``except:`` or swallowing generic ``Exception`` is prohibited across
``06-runtime/`` (enforced by FIT-002).
"""

from __future__ import annotations


class AfrpRuntimeError(Exception):
    """Base class for all AFRP runtime faults."""


class ContractViolationError(AfrpRuntimeError):
    """A CIO payload failed structural or semantic validation."""

    def __init__(self, cio: str, reason: str) -> None:
        self.cio = cio
        self.reason = reason
        super().__init__(f"{cio}: {reason}")


class ConfigurationError(AfrpRuntimeError):
    """Configuration is missing, malformed, or violates policy (EDR-005/008)."""

    def __init__(self, key: str, reason: str) -> None:
        self.key = key
        self.reason = reason
        super().__init__(f"config {key!r}: {reason}")


class StateTransitionError(AfrpRuntimeError):
    """An illegal SYS-03 operational state transition was requested."""

    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"illegal SYS-03 transition {current} -> {target}")


class QuorumError(AfrpRuntimeError):
    """Agent quorum fell below the mission profile requirement (NFR-003)."""

    def __init__(self, have: int, need: int) -> None:
        self.have = have
        self.need = need
        super().__init__(f"quorum {have}/{need} below mission requirement")


class DeterminismError(AfrpRuntimeError):
    """A deterministic code path produced irreproducible output (NFR-004)."""

    def __init__(self, component: str, detail: str) -> None:
        self.component = component
        self.detail = detail
        super().__init__(f"determinism breach in {component}: {detail}")
