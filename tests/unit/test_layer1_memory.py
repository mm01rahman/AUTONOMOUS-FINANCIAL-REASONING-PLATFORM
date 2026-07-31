"""WP-RT-1004 unit tests for Layer 1 vector memory."""

from __future__ import annotations

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.layer1.memory import MemoryRecord, VectorMemory, cosine_similarity


def test_store_and_topk_query() -> None:
    memory = VectorMemory(dimension=3)
    memory.store(MemoryRecord("a", (1.0, 0.0, 0.0), "trend", 0, 1))
    memory.store(MemoryRecord("b", (0.0, 1.0, 0.0), "range", 0, 1))
    memory.store(MemoryRecord("c", (0.9, 0.1, 0.0), "trend", 0, 1))
    results = memory.query((1.0, 0.0, 0.0), top_k=2)
    assert results[0][0] == "a" and results[1][0] == "c"


def test_dimension_mismatch_rejected() -> None:
    memory = VectorMemory(dimension=2)
    with pytest.raises(ContractViolationError):
        memory.store(MemoryRecord("x", (1.0,), "r", 0, 1))
    with pytest.raises(ContractViolationError):
        memory.query((1.0, 2.0, 3.0))


def test_null_vector_similarity_zero() -> None:
    assert cosine_similarity((0.0, 0.0), (1.0, 1.0)) == 0.0


def test_deterministic_tie_break() -> None:
    memory = VectorMemory(dimension=2)
    memory.store(MemoryRecord("z", (1.0, 0.0), "r", 0, 1))
    memory.store(MemoryRecord("a", (1.0, 0.0), "r", 0, 1))
    results = memory.query((1.0, 0.0), top_k=2)
    assert [record_id for record_id, _score in results] == ["a", "z"]


def test_query_top_k_bounds_and_get() -> None:
    memory = VectorMemory(dimension=2)
    memory.store(MemoryRecord("a", (1.0, 0.0), "trend", 10, 20))
    memory.store(MemoryRecord("b", (0.5, 0.5), "range", 20, 30))
    assert len(memory.query((1.0, 0.0), top_k=-1)) == 0
    assert len(memory.query((1.0, 0.0), top_k=10)) == 2
    assert memory.get("a") is not None
    assert memory.get("missing") is None
