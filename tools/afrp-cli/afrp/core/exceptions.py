"""EOS exception taxonomy (WP-IMP-0003).

Every EOS failure surfaces as a typed :class:`AfrpError` subclass so callers
can react per failure mode (EDR-004: no bare/blanket exception handling).
"""

from __future__ import annotations


class AfrpError(Exception):
    """Base class for all AFRP Engineering OS errors."""

    exit_code: int = 1


class ContractReferenceError(AfrpError):
    """A governed artifact referenced by a contract is missing (ERR-CONTRACT-REFERENCE)."""

    exit_code: int = 2

    def __init__(self, artifact: str) -> None:
        self.artifact = artifact
        super().__init__(f"Missing governed artifact: {artifact}")


class ManifestValidationError(AfrpError):
    """REPOSITORY_MANIFEST.yaml is malformed or declares an unsupported schema."""

    exit_code: int = 2

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Repository manifest invalid: {reason}")


class InvariantError(AfrpError):
    """A constitutional invariant was breached (e.g. FIT-006 kernel word budget)."""

    exit_code: int = 3

    def __init__(self, invariant: str, detail: str) -> None:
        self.invariant = invariant
        self.detail = detail
        super().__init__(f"Invariant {invariant} breached: {detail}")


class BaselineIntegrityError(AfrpError):
    """SHA256 verification against BASELINE_FINGERPRINT.yaml failed."""

    exit_code: int = 4

    def __init__(self, mismatches: list[str]) -> None:
        self.mismatches = mismatches
        joined = ", ".join(mismatches)
        super().__init__(f"Baseline integrity failure: {joined}")
