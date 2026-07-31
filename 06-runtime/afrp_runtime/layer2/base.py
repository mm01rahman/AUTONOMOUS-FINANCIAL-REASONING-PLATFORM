"""L2-BASE — DSmT belief foundation for domain agents (SLS-200, WP-IMP-0017).

Frame of discernment Θ = {BULL, BEAR, RANGE}. Focal elements live on
Dedekind's lattice D^Θ and are addressed by canonical labels: singletons
("BULL"), unions ("BEAR|BULL", alphabetical), intersections ("BEAR&BULL",
alphabetical), and "THETA" for total ignorance.

NFR-003: agents never crash on missing telemetry — they degrade to the
vacuous belief m(Θ) = 1 with ``degraded=True``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import THETA, DomainBelief, StandardFeature
from afrp_runtime.contracts.envelope import make_envelope

FRAME: tuple[str, ...] = ("BULL", "BEAR", "RANGE")

_MASS_EPS = 1e-12


def union_label(*singletons: str) -> str:
    """Canonical union label, alphabetically sorted (e.g. 'BEAR|BULL')."""
    _assert_singletons(singletons)
    return "|".join(sorted(set(singletons)))


def intersection_label(*singletons: str) -> str:
    """Canonical intersection label, alphabetically sorted (e.g. 'BEAR&BULL')."""
    _assert_singletons(singletons)
    return "&".join(sorted(set(singletons)))


def _assert_singletons(parts: tuple[str, ...]) -> None:
    unknown = [p for p in parts if p not in FRAME]
    if unknown:
        raise ContractViolationError("CIO-03", f"unknown frame elements: {unknown}")
    if len(parts) < 1:
        raise ContractViolationError("CIO-03", "label requires at least one element")


def normalize_masses(masses: dict[str, float]) -> dict[str, float]:
    """Drop epsilon dust and renormalize to Σ = 1.

    Raises:
        ContractViolationError: negative mass or zero total.
    """
    negative = {k: v for k, v in masses.items() if v < 0.0}
    if negative:
        raise ContractViolationError("CIO-03", f"negative masses: {negative}")
    cleaned = {k: v for k, v in masses.items() if v > _MASS_EPS}
    total = sum(cleaned.values())
    if total <= 0.0:
        raise ContractViolationError("CIO-03", "mass assignment sums to zero")
    return {k: v / total for k, v in sorted(cleaned.items())}


def vacuous_bba() -> dict[str, float]:
    """Total ignorance: m(Θ) = 1."""
    return {THETA: 1.0}


def pad_ignorance(masses: dict[str, float], confidence: float) -> dict[str, float]:
    """NFR-003 degradation: scale masses by ``confidence`` and pad Θ.

    ``confidence`` ∈ [0, 1]; the complement flows into m(Θ).

    Raises:
        ContractViolationError: confidence outside [0, 1].
    """
    if not 0.0 <= confidence <= 1.0:
        raise ContractViolationError("CIO-03", f"confidence {confidence} outside [0, 1]")
    normalized = normalize_masses(masses)
    padded = {k: v * confidence for k, v in normalized.items()}
    padded[THETA] = padded.get(THETA, 0.0) + (1.0 - confidence)
    return normalize_masses(padded)


@dataclass
class BeliefAgent(ABC):
    """Template for L2 domain agents producing CIO-03 beliefs.

    Subclasses declare ``agent_id`` and ``required_features`` and implement
    :meth:`form_belief` over a complete feature map. Missing or low-quality
    telemetry short-circuits into a degraded vacuous belief (NFR-003).
    """

    mission_profile_id: str
    cognitive_cycle_id: str = "cycle-0"
    reliability: float = field(default=1.0)
    min_quality: float = 0.25

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Stable subsystem identity, e.g. 'L2-MAC'."""

    @property
    @abstractmethod
    def required_features(self) -> tuple[str, ...]:
        """Feature ids that must be present and healthy."""

    @abstractmethod
    def form_belief(self, features: dict[str, float]) -> dict[str, float]:
        """Map a complete feature-value dict to a BBA over D^Θ."""

    def evaluate(
        self, instrument: str, feature_map: dict[str, StandardFeature]
    ) -> DomainBelief:
        """Produce a validated CIO-03, degrading instead of failing (NFR-003)."""
        missing = [f for f in self.required_features if f not in feature_map]
        unhealthy = [
            f
            for f in self.required_features
            if f in feature_map and feature_map[f].quality < self.min_quality
        ]
        parents = tuple(
            feature_map[f].envelope.message_id
            for f in self.required_features
            if f in feature_map
        )

        if missing or unhealthy:
            masses = vacuous_bba()
            degraded = True
        else:
            values = {f: feature_map[f].value for f in self.required_features}
            masses = normalize_masses(self.form_belief(values))
            degraded = False

        envelope = make_envelope(
            producer_subsystem_id=self.agent_id,
            cognitive_cycle_id=self.cognitive_cycle_id,
            mission_profile_id=self.mission_profile_id,
            payload_repr=f"{self.agent_id}:{instrument}:{sorted(masses.items())!r}",
            parent_cio_ids=parents,
        )
        belief = DomainBelief(
            envelope=envelope,
            agent_id=self.agent_id,
            instrument=instrument,
            masses=masses,
            reliability=self.reliability,
            degraded=degraded,
        )
        belief.validate()
        return belief
