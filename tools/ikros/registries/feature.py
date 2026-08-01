"""Feature Registry — manages Feature and FeatureFamily entities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.ikros.models import Feature, FeatureFamily, FeatureStatus, Stationarity
from tools.ikros.registries.base import BaseRegistry, RegistryError


class FeatureRegistry(BaseRegistry[Feature]):
    """Registry for Feature entities.

    Also manages FeatureFamily as a subordinate collection.
    Persists to ``{base_dir}/features/``.
    """

    entity_type = "Feature"

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__(base_dir)
        self._families: dict[str, FeatureFamily] = {}
        if base_dir is not None:
            self._load_families()

    # ------------------------------------------------------------------
    # FeatureFamily management
    # ------------------------------------------------------------------

    def register_family(self, family: FeatureFamily) -> str:
        """Register a FeatureFamily and return its ikros_id."""
        if family.ikros_id in self._families:
            raise RegistryError(f"Duplicate FeatureFamily '{family.ikros_id}'")
        self._families[family.ikros_id] = family
        if self._base_dir is not None:
            from tools.ikros.persistence import entity_path, write_entity

            path = entity_path(self._base_dir, "FeatureFamily", family.ikros_id)
            write_entity(path, family.to_dict())
        return family.ikros_id

    def get_family(self, family_id: str) -> FeatureFamily:
        if family_id not in self._families:
            raise KeyError(f"FeatureFamily '{family_id}' not found")
        return self._families[family_id]

    def list_families(self) -> list[FeatureFamily]:
        return list(self._families.values())

    def family_count(self) -> int:
        return len(self._families)

    # ------------------------------------------------------------------
    # Feature domain queries
    # ------------------------------------------------------------------

    def _deserialize(self, data: dict[str, Any]) -> Feature:
        return Feature.from_dict(data)

    def active(self) -> list[Feature]:
        """Return all active features."""
        return self.list_by_state(FeatureStatus.ACTIVE.value)

    def by_family(self, family_id: str) -> list[Feature]:
        """Return all features belonging to a family."""
        return self.find({"family_id": family_id})

    def stationary(self) -> list[Feature]:
        """Return features confirmed as stationary."""
        return self.find({"stationarity": Stationarity.STATIONARY.value})

    def high_information(self, threshold: float = 0.5) -> list[Feature]:
        """Return features with information content above the threshold."""
        return [f for f in self._store.values() if f.information_content >= threshold]

    def high_stability(self, threshold: float = 0.7) -> list[Feature]:
        """Return features with stability score above the threshold."""
        return [f for f in self._store.values() if f.stability_score >= threshold]

    def add_experiment_usage(self, feature_id: str, experiment_id: str) -> Feature:
        """Record that a feature was used in an experiment."""
        feat = self.get(feature_id)
        if experiment_id not in feat.used_in_experiments:
            updated = feat.used_in_experiments + [experiment_id]
            return self.update(feature_id, {"used_in_experiments": updated})
        return feat

    def supersede(self, old_id: str, new_id: str) -> Feature:
        """Mark old feature as superseded by new feature."""
        old = self.get(old_id)
        if not self.exists(new_id):
            raise RegistryError(f"Successor feature '{new_id}' not found in registry")
        self.update(old_id, {"superseded_by": new_id})
        successors = old.lineage.successors.to_dict()
        successors["superseded_by"] = new_id
        lineage = old.lineage.to_dict()
        lineage["successors"] = successors
        return self.update(old_id, {"lineage": lineage})

    def _load_families(self) -> None:
        assert self._base_dir is not None
        from tools.ikros.persistence import read_entity

        for yaml_file in self._base_dir.rglob("IKROS-FF-*.yaml"):
            try:
                data = read_entity(yaml_file)
                family = FeatureFamily.from_dict(data)
                self._families[family.ikros_id] = family
            except (KeyError, ValueError):
                pass
