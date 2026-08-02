"""IKROS identifier generation and lifecycle state machine."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime

# ---------------------------------------------------------------------------
# Identifier generation
# ---------------------------------------------------------------------------

_TYPE_CODES: dict[str, str] = {
    "ResearchQuestion": "RQ",
    "Hypothesis": "HYP",
    "Experiment": "EXP",
    "Feature": "FEAT",
    "FeatureFamily": "FF",
    "AlphaCandidate": "ALPHACAND",
    "Alpha": "ALPHA",
    "Factor": "FACTOR",
    "Model": "MODEL",
    "Validation": "VAL",
    "Backtest": "BT",
    "WalkForward": "WF",
    "MonteCarlo": "MC",
    "Failure": "FAIL",
    "KnowledgeObject": "KO",
    "Dataset": "DS",
    "DatasetVersion": "DSV",
    "Regime": "REGIME",
    "MarketEvent": "EVENT",
    "EconomicThesis": "THESIS",
    "Literature": "LIT",
    "Decision": "DEC",
    "Policy": "POL",
    "ResearchConclusion": "CONCL",
    "ContradictoryEvidence": "CONTRA",
    "WorldModel": "WM",
    "StressTest": "STRESS",
}

_ID_PATTERN = re.compile(
    r"^IKROS-[A-Z]+(?:-[A-Z]+)*-\d{8}-\d{4}$"
)


def make_ikros_id(entity_type: str, date: datetime | None = None, seq: int = 1) -> str:
    """Generate a canonical IKROS identifier.

    Format: IKROS-{TYPE_CODE}-{YYYYMMDD}-{SEQ:04d}
    """
    code = _TYPE_CODES.get(entity_type, entity_type.upper())
    d = date or datetime.now(UTC)
    return f"IKROS-{code}-{d.strftime('%Y%m%d')}-{seq:04d}"


def is_valid_ikros_id(ikros_id: str) -> bool:
    """Return True if the given string matches the canonical IKROS ID pattern."""
    return bool(_ID_PATTERN.match(ikros_id))


def entity_type_from_id(ikros_id: str) -> str | None:
    """Extract entity type code from an IKROS ID, e.g. 'RQ' from IKROS-RQ-*."""
    parts = ikros_id.split("-")
    if len(parts) < 4:
        return None
    # Parts: ['IKROS', {TYPE...}, '{DATE}', '{SEQ}']
    # Type may span multiple parts (e.g. IKROS-ALPHACAND-...)
    return "-".join(parts[1:-2])


def compute_reproducibility_hash(data: dict[str, object]) -> str:
    """Compute a deterministic SHA-256 hash from a dict of experiment inputs."""
    import json

    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Lifecycle state machine
# ---------------------------------------------------------------------------

# Valid transitions per entity type.  Key = current state, value = allowed next states.

_RESEARCH_TRANSITIONS: dict[str, list[str]] = {
    "OPEN": ["ACTIVE"],
    "ACTIVE": ["ANSWERED", "RETIRED"],
    "ANSWERED": ["RETIRED"],
    "RETIRED": [],
}

_HYPOTHESIS_TRANSITIONS: dict[str, list[str]] = {
    "PROPOSED": ["UNDER_REVIEW", "RETIRED"],
    "UNDER_REVIEW": ["APPROVED_FOR_TESTING", "RETIRED"],
    "APPROVED_FOR_TESTING": ["TESTING", "RETIRED"],
    "TESTING": ["SUPPORTED", "REFUTED", "INCONCLUSIVE"],
    "SUPPORTED": ["RETIRED"],
    "REFUTED": ["RETIRED"],
    "INCONCLUSIVE": ["TESTING", "RETIRED"],
    "RETIRED": [],
}

_EXPERIMENT_TRANSITIONS: dict[str, list[str]] = {
    "DESIGNED": ["APPROVED", "INVALIDATED"],
    "APPROVED": ["RUNNING", "INVALIDATED"],
    "RUNNING": ["COMPLETE", "FAILED"],
    "COMPLETE": ["REVIEWED", "INVALIDATED"],
    "FAILED": ["REVIEWED"],
    "REVIEWED": ["ARCHIVED", "INVALIDATED"],
    "ARCHIVED": [],
    "INVALIDATED": [],
}

_FEATURE_TRANSITIONS: dict[str, list[str]] = {
    "DRAFT": ["VALIDATED", "RETIRED"],
    "VALIDATED": ["ACTIVE", "RETIRED"],
    "ACTIVE": ["DEPRECATED", "RETIRED"],
    "DEPRECATED": ["RETIRED"],
    "RETIRED": [],
}

_ALPHA_CANDIDATE_TRANSITIONS: dict[str, list[str]] = {
    "CANDIDATE": ["PROMOTED", "REJECTED", "RETIRED"],
    "PROMOTED": ["RETIRED"],
    "REJECTED": ["RETIRED"],
    "RETIRED": [],
}

_ALPHA_TRANSITIONS: dict[str, list[str]] = {
    "PROMOTED": ["RETIRED"],
    "RETIRED": [],
}

_TRANSITIONS: dict[str, dict[str, list[str]]] = {
    "ResearchQuestion": _RESEARCH_TRANSITIONS,
    "Hypothesis": _HYPOTHESIS_TRANSITIONS,
    "Experiment": _EXPERIMENT_TRANSITIONS,
    "Feature": _FEATURE_TRANSITIONS,
    "FeatureFamily": _FEATURE_TRANSITIONS,
    "AlphaCandidate": _ALPHA_CANDIDATE_TRANSITIONS,
    "Alpha": _ALPHA_TRANSITIONS,
}


class LifecycleError(ValueError):
    """Raised when an invalid lifecycle transition is attempted."""


def validate_transition(entity_type: str, current_state: str, new_state: str) -> None:
    """Raise LifecycleError if the transition is not allowed."""
    transitions = _TRANSITIONS.get(entity_type, {})
    allowed = transitions.get(current_state, [])
    if new_state not in allowed:
        raise LifecycleError(
            f"{entity_type}: transition '{current_state}' → '{new_state}' is not allowed. "
            f"Allowed: {allowed}"
        )


def allowed_transitions(entity_type: str, current_state: str) -> list[str]:
    """Return the list of allowed next states for the given entity and current state."""
    return list(_TRANSITIONS.get(entity_type, {}).get(current_state, []))
