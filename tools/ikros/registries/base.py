"""IKROS base registry — generic CRUD, persistence, and validation for all registries."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar, Generic, TypeVar

from tools.ikros.identifiers import (
    LifecycleError,
    make_ikros_id,
    validate_transition,
)
from tools.ikros.models import IKROSEntity
from tools.ikros.persistence import entity_path, read_entity, write_entity
from tools.ikros.validation import assert_valid

T = TypeVar("T", bound=IKROSEntity)


class RegistryError(RuntimeError):
    """Raised for registry-level errors (duplicate ID, referential integrity, etc.)."""


class BaseRegistry(Generic[T]):
    """Generic CRUD, persistence, and validation for IKROS registries.

    Subclasses must override :meth:`_deserialize` to return the correct entity type.
    """

    entity_type: ClassVar[str] = "IKROSEntity"

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir: Path | None = base_dir
        self._store: dict[str, T] = {}
        if base_dir is not None:
            self._load_from_disk()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def register(self, entity: T) -> str:
        """Validate and store entity. Returns ikros_id."""
        assert_valid(entity)
        if entity.ikros_id in self._store:
            raise RegistryError(
                f"Duplicate: {entity.entity_type} '{entity.ikros_id}' already registered"
            )
        self._store[entity.ikros_id] = entity
        if self._base_dir is not None:
            self._persist(entity)
        return entity.ikros_id

    def get(self, ikros_id: str) -> T:
        """Return entity by ID, raising KeyError if not found."""
        if ikros_id not in self._store:
            raise KeyError(f"{self.entity_type} '{ikros_id}' not found")
        return self._store[ikros_id]

    def exists(self, ikros_id: str) -> bool:
        return ikros_id in self._store

    def update(self, ikros_id: str, delta: dict[str, Any]) -> T:
        """Apply delta to a mutable copy and re-validate. Returns updated entity."""
        entity = self.get(ikros_id)
        data = entity.to_dict()
        data.update(delta)
        self._record_version(data, entity)
        updated = self._deserialize(data)
        assert_valid(updated)
        self._store[ikros_id] = updated
        if self._base_dir is not None:
            self._persist(updated)
        return updated

    def transition(self, ikros_id: str, new_state: str, note: str = "") -> T:
        """Advance an entity's lifecycle state through the governed state machine."""
        entity = self.get(ikros_id)
        validate_transition(entity.entity_type, entity.lifecycle_state, new_state)
        data = entity.to_dict()
        data["lifecycle_state"] = new_state
        self._record_version(data, entity, change_summary=f"State → {new_state}. {note}".strip())
        updated = self._deserialize(data)
        assert_valid(updated)
        self._store[ikros_id] = updated
        if self._base_dir is not None:
            self._persist(updated)
        return updated

    def retire(self, ikros_id: str, reason: str) -> T:
        """Retire an entity, recording the retirement reason in lineage."""
        entity = self.get(ikros_id)
        data = entity.to_dict()
        retirement = data.setdefault("lineage", {}).setdefault("retirement", {})
        retirement["retired_at"] = _now_iso()
        retirement["retirement_reason"] = reason
        try:
            validate_transition(entity.entity_type, entity.lifecycle_state, "RETIRED")
            data["lifecycle_state"] = "RETIRED"
        except LifecycleError:
            pass  # Some states have no RETIRED transition; just update retirement metadata
        updated = self._deserialize(data)
        self._store[ikros_id] = updated
        if self._base_dir is not None:
            self._persist(updated)
        return updated

    def list_all(self) -> list[T]:
        return list(self._store.values())

    def list_by_state(self, state: str) -> list[T]:
        return [e for e in self._store.values() if e.lifecycle_state == state]

    def find(self, filter_kwargs: dict[str, Any]) -> list[T]:
        """Return entities matching all given attribute filters."""
        results = []
        for entity in self._store.values():
            if all(getattr(entity, k, None) == v for k, v in filter_kwargs.items()):
                results.append(entity)
        return results

    def count(self) -> int:
        return len(self._store)

    def next_id(self, date: datetime | None = None) -> str:
        """Generate the next sequential IKROS ID for this registry."""
        seq = self.count() + 1
        while True:
            candidate = make_ikros_id(self.entity_type, date, seq)
            if candidate not in self._store:
                return candidate
            seq += 1

    # ------------------------------------------------------------------
    # Subclass interface
    # ------------------------------------------------------------------

    def _deserialize(self, data: dict[str, Any]) -> T:
        """Subclasses must implement this to return the correct entity type."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _persist(self, entity: T) -> None:
        assert self._base_dir is not None
        path = entity_path(self._base_dir, entity.entity_type, entity.ikros_id)
        write_entity(path, entity.to_dict())

    def _load_from_disk(self) -> None:
        assert self._base_dir is not None
        for yaml_file in self._base_dir.rglob("IKROS-*.yaml"):
            try:
                data = read_entity(yaml_file)
                entity = self._deserialize(data)
                self._store[entity.ikros_id] = entity
            except (KeyError, ValueError):
                pass  # Skip malformed files; let explicit register() enforce schema

    def _record_version(
        self, data: dict[str, Any], old: T, change_summary: str = "Field update"
    ) -> None:
        history: list[dict[str, Any]] = list(data.get("version_history", []))
        history.append(
            {
                "version": old.version,
                "changed_at": _now_iso(),
                "change_summary": change_summary,
                "confidence_at_time": old.confidence.overall(),
            }
        )
        data["version_history"] = history


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
