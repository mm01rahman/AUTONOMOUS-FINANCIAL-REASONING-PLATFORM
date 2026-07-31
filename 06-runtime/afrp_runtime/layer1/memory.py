"""L1-MEM — vector memory (SLS-100, WP-IMP-0016).

Deterministic episodic vector store: fixed-dimension embeddings with cosine
similarity retrieval. Consumed by L6-OPT (CIO-12) and research workloads.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from afrp_runtime.common.errors import ContractViolationError


@dataclass(frozen=True)
class MemoryRecord:
    """One stored episode."""

    record_id: str
    vector: tuple[float, ...]
    regime_label: str
    window_start_ns: int
    window_end_ns: int


def cosine_similarity(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    """Cosine similarity; 0.0 when either vector is null."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class VectorMemory:
    """Fixed-dimension in-process vector store with top-k retrieval."""

    dimension: int
    _records: dict[str, MemoryRecord] = field(default_factory=dict)

    def store(self, record: MemoryRecord) -> None:
        """Insert or replace a record.

        Raises:
            ContractViolationError: wrong dimensionality or empty id.
        """
        if not record.record_id:
            raise ContractViolationError("CIO-12", "record_id must be non-empty")
        if len(record.vector) != self.dimension:
            raise ContractViolationError(
                "CIO-12",
                f"vector dimension {len(record.vector)} != store dimension {self.dimension}",
            )
        self._records[record.record_id] = record

    def query(self, vector: tuple[float, ...], top_k: int = 5) -> list[tuple[str, float]]:
        """Top-k ``(record_id, similarity)`` sorted desc, id-ordered on ties.

        Raises:
            ContractViolationError: wrong query dimensionality.
        """
        if len(vector) != self.dimension:
            raise ContractViolationError(
                "CIO-12", f"query dimension {len(vector)} != {self.dimension}"
            )
        scored = [
            (record.record_id, cosine_similarity(vector, record.vector))
            for record in self._records.values()
        ]
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        return scored[: max(0, top_k)]

    def get(self, record_id: str) -> MemoryRecord | None:
        """Fetch a record by id."""
        return self._records.get(record_id)

    def __len__(self) -> int:
        return len(self._records)
