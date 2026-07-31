"""WP-RT-1004 integration tests for vector store/query lifecycle."""

from __future__ import annotations

from afrp_runtime.layer1.memory import MemoryRecord, VectorMemory


def test_vector_memory_lifecycle_with_regime_embeddings() -> None:
    memory = VectorMemory(dimension=4)
    memory.store(MemoryRecord("bull-1", (0.9, 0.1, 0.0, 0.0), "bull", 1, 10))
    memory.store(MemoryRecord("range-1", (0.2, 0.8, 0.0, 0.0), "range", 11, 20))
    memory.store(MemoryRecord("bull-2", (0.85, 0.15, 0.0, 0.0), "bull", 21, 30))

    results = memory.query((1.0, 0.0, 0.0, 0.0), top_k=2)
    assert [record_id for record_id, _score in results] == ["bull-1", "bull-2"]
    assert len(memory) == 3
