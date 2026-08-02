"""IKROS memory persistence — storage-independent YAML repository."""

from __future__ import annotations

import abc
from pathlib import Path

from tools.ikros.memory.models import MemoryRecord, MemoryTier
from tools.ikros.persistence import read_entity, write_entity


class MemoryRepository(abc.ABC):
    """Abstract persistence port for the IKROS memory subsystem."""

    @abc.abstractmethod
    def save(self, records: dict[str, MemoryRecord]) -> None:
        """Persist the full memory store."""

    @abc.abstractmethod
    def load(self) -> list[MemoryRecord]:
        """Load and return all memory records."""

    @abc.abstractmethod
    def save_record(self, record: MemoryRecord) -> None:
        """Upsert a single record."""

    @abc.abstractmethod
    def record_ids(self) -> list[str]:
        """Return all stored IDs in deterministic order."""


_TIER_DIRS: dict[str, str] = {
    MemoryTier.WORKING: "t0-working",
    MemoryTier.EPISODIC: "t1-episodic",
    MemoryTier.SEMANTIC: "t2-semantic",
    MemoryTier.PROCEDURAL: "t3-procedural",
    MemoryTier.INSTITUTIONAL: "t4-institutional",
    MemoryTier.ARCHIVE: "t5-archive",
}


class YAMLMemoryRepository(MemoryRepository):
    """Deterministic YAML repository for memory records."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def save(self, records: dict[str, MemoryRecord]) -> None:
        for record in sorted(records.values(), key=lambda item: item.memory_id):
            self.save_record(record)

    def load(self) -> list[MemoryRecord]:
        records: list[MemoryRecord] = []
        for tier in MemoryTier:
            tier_dir = self._tier_dir(tier.value)
            if not tier_dir.exists():
                continue
            for path in sorted(tier_dir.glob("IKMEM-*.yaml")):
                data = read_entity(path)
                records.append(MemoryRecord.from_dict(data))
        return records

    def save_record(self, record: MemoryRecord) -> None:
        write_entity(self._path_for_record(record), record.to_dict())

    def record_ids(self) -> list[str]:
        ids: list[str] = []
        for tier in MemoryTier:
            tier_dir = self._tier_dir(tier.value)
            if not tier_dir.exists():
                continue
            ids.extend(sorted(path.stem for path in tier_dir.glob("IKMEM-*.yaml")))
        return sorted(ids)

    def _path_for_record(self, record: MemoryRecord) -> Path:
        return self._tier_dir(record.tier) / f"{record.memory_id}.yaml"

    def _tier_dir(self, tier: str) -> Path:
        subdir = _TIER_DIRS.get(tier, tier.lower())
        return self._base_dir / subdir
