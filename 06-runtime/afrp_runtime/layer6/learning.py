"""L6-OPT — out-of-band calibration and episodic embeddings (SLS-600).

The learning loop never changes safety policy. It emits bounded reliability
modifiers (CIO-11) from rolling multiclass Brier scores and deterministic
feature embeddings (CIO-12). L3-WRM may discount beliefs with CIO-11, while
L4-VAL independently re-validates every action (Article VIII).
"""

from __future__ import annotations

import hashlib
import math
from collections import deque
from dataclasses import dataclass, field

from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import CalibrationWeights, EpisodicEmbedding
from afrp_runtime.contracts.envelope import make_envelope

SUBSYSTEM_ID = "L6-OPT"
OUTCOMES: tuple[str, ...] = ("BULL", "BEAR", "RANGE")
_SUM_TOLERANCE = 1e-9


def multiclass_brier(probabilities: dict[str, float], outcome: str) -> float:
    """Multiclass Brier score in [0, 2] for the three-state frame.

    Raises:
        ContractViolationError: unsupported outcome or malformed probability
            distribution.
    """
    if outcome not in OUTCOMES:
        raise ContractViolationError("CIO-11", f"unknown outcome {outcome!r}")
    if set(probabilities) != set(OUTCOMES):
        raise ContractViolationError(
            "CIO-11", f"probabilities must cover exactly {OUTCOMES!r}"
        )
    if any(not 0.0 <= value <= 1.0 for value in probabilities.values()):
        raise ContractViolationError("CIO-11", "probabilities outside [0, 1]")
    total = sum(probabilities.values())
    if abs(total - 1.0) > _SUM_TOLERANCE:
        raise ContractViolationError("CIO-11", f"probabilities sum to {total!r}")
    return sum(
        (probabilities[label] - (1.0 if label == outcome else 0.0)) ** 2
        for label in OUTCOMES
    )


@dataclass
class BrierCalibrator:
    """Rolling agent calibration producing bounded discounting weights."""

    mission_profile_id: str
    window_cycles: int = 100
    weight_floor: float = 0.05
    cognitive_cycle_id: str = "cycle-0"
    _scores: dict[str, deque[float]] = field(default_factory=dict)
    _parents: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.window_cycles <= 0:
            raise ContractViolationError("CIO-11", "window_cycles must be positive")
        if not 0.0 <= self.weight_floor <= 1.0:
            raise ContractViolationError("CIO-11", "weight_floor outside [0, 1]")

    def observe(
        self,
        agent_id: str,
        probabilities: dict[str, float],
        outcome: str,
        parent_cio_id: str = "",
    ) -> float:
        """Record one resolved forecast and return its Brier score."""
        if not agent_id:
            raise ContractViolationError("CIO-11", "agent_id must be non-empty")
        score = multiclass_brier(probabilities, outcome)
        history = self._scores.setdefault(
            agent_id, deque(maxlen=self.window_cycles)
        )
        history.append(score)
        if parent_cio_id:
            self._parents.append(parent_cio_id)
        return score

    def mean_scores(self) -> dict[str, float]:
        """Rolling mean Brier score per agent."""
        return {
            agent_id: sum(history) / len(history)
            for agent_id, history in sorted(self._scores.items())
            if history
        }

    def weights(self) -> dict[str, float]:
        """Map mean Brier score [0,2] to bounded reliability [floor,1]."""
        return {
            agent_id: max(self.weight_floor, min(1.0, 1.0 - score / 2.0))
            for agent_id, score in self.mean_scores().items()
        }

    def emit(self, generated_at_ns: int | None = None) -> CalibrationWeights:
        """Emit CIO-11 from the current rolling windows."""
        scores = self.mean_scores()
        weights = self.weights()
        envelope = make_envelope(
            producer_subsystem_id=SUBSYSTEM_ID,
            cognitive_cycle_id=self.cognitive_cycle_id,
            mission_profile_id=self.mission_profile_id,
            payload_repr=f"{sorted(scores.items())!r}:{self.window_cycles}",
            parent_cio_ids=tuple(self._parents[-self.window_cycles :]),
            generated_at_ns=generated_at_ns,
        )
        return CalibrationWeights(
            envelope=envelope,
            agent_weights=weights,
            brier_scores=scores,
            window_cycles=self.window_cycles,
        )


def _projection_sign(feature_id: str, dimension: int) -> float:
    digest = hashlib.blake2b(
        f"{feature_id}:{dimension}:42".encode(), digest_size=1
    ).digest()
    return 1.0 if digest[0] & 1 else -1.0


@dataclass(frozen=True)
class RegimeEmbedder:
    """Stable hash-projection embedder for episodic regime memory."""

    dimension: int = 16

    def __post_init__(self) -> None:
        if self.dimension <= 0:
            raise ContractViolationError("CIO-12", "dimension must be positive")

    def embed(self, features: dict[str, float]) -> tuple[float, ...]:
        """Project named scalar features to an L2-normalized vector.

        Feature iteration is sorted, so mapping insertion order cannot affect
        the result (NFR-004).
        """
        if not features:
            raise ContractViolationError("CIO-12", "cannot embed an empty feature map")
        if any(not math.isfinite(value) for value in features.values()):
            raise ContractViolationError("CIO-12", "features must be finite")

        vector = [0.0] * self.dimension
        scale = 1.0 / math.sqrt(len(features))
        for feature_id, value in sorted(features.items()):
            for index in range(self.dimension):
                vector[index] += value * _projection_sign(feature_id, index) * scale
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return tuple(vector)
        return tuple(value / norm for value in vector)

    def emit(
        self,
        mission_profile_id: str,
        instrument: str,
        features: dict[str, float],
        regime_label: str,
        window_start_ns: int,
        window_end_ns: int,
        parent_cio_ids: tuple[str, ...] = (),
        cognitive_cycle_id: str = "cycle-0",
    ) -> EpisodicEmbedding:
        """Emit a deterministic CIO-12 episode."""
        if window_end_ns < window_start_ns:
            raise ContractViolationError("CIO-12", "window end precedes start")
        vector = self.embed(features)
        envelope = make_envelope(
            producer_subsystem_id=SUBSYSTEM_ID,
            cognitive_cycle_id=cognitive_cycle_id,
            mission_profile_id=mission_profile_id,
            payload_repr=(
                f"{instrument}:{regime_label}:{window_start_ns}:{window_end_ns}:"
                f"{vector!r}"
            ),
            parent_cio_ids=parent_cio_ids,
            generated_at_ns=window_end_ns,
        )
        return EpisodicEmbedding(
            envelope=envelope,
            instrument=instrument,
            vector=vector,
            regime_label=regime_label,
            window_start_ns=window_start_ns,
            window_end_ns=window_end_ns,
        )
