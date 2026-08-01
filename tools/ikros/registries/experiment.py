"""Experiment Registry — manages Experiment entities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.ikros.models import Experiment, ExperimentStatus
from tools.ikros.registries.base import BaseRegistry


class ExperimentRegistry(BaseRegistry[Experiment]):
    """Registry for Experiment entities.

    Persists to ``{base_dir}/experiments/IKROS-EXP-*.yaml``.
    """

    entity_type = "Experiment"

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__(base_dir)

    def _deserialize(self, data: dict[str, Any]) -> Experiment:
        return Experiment.from_dict(data)

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------

    def complete(self) -> list[Experiment]:
        """Return all completed experiments."""
        return self.list_by_state(ExperimentStatus.COMPLETE.value)

    def running(self) -> list[Experiment]:
        """Return all currently running experiments."""
        return self.list_by_state(ExperimentStatus.RUNNING.value)

    def by_hypothesis(self, hypothesis_id: str) -> list[Experiment]:
        """Return all experiments testing a given hypothesis."""
        return [e for e in self._store.values() if hypothesis_id in e.hypotheses]

    def by_reproducibility_hash(self, hash_value: str) -> Experiment | None:
        """Look up an experiment by reproducibility hash for exact replay."""
        for exp in self._store.values():
            if exp.reproducibility_hash == hash_value:
                return exp
        return None

    def add_validation(self, exp_id: str, validation_id: str) -> Experiment:
        """Record that this experiment produced a validation artifact."""
        entity = self.get(exp_id)
        if validation_id not in entity.validations_produced:
            updated = entity.validations_produced + [validation_id]
            return self.update(exp_id, {"validations_produced": updated})
        return entity

    def add_failure(self, exp_id: str, failure_id: str) -> Experiment:
        """Record that this experiment produced a failure record."""
        entity = self.get(exp_id)
        if failure_id not in entity.failures_produced:
            updated = entity.failures_produced + [failure_id]
            return self.update(exp_id, {"failures_produced": updated})
        return entity

    def get_reproducible_inputs(self, exp_id: str) -> dict[str, Any]:
        """Return all deterministic inputs needed to replay this experiment."""
        exp = self.get(exp_id)
        return {
            "ikros_id": exp.ikros_id,
            "dataset_versions": exp.dataset_versions,
            "feature_versions": exp.feature_versions,
            "parameters": exp.parameters,
            "random_seed": exp.random_seed,
            "in_sample_start": exp.in_sample_start,
            "in_sample_end": exp.in_sample_end,
            "out_of_sample_start": exp.out_of_sample_start,
            "out_of_sample_end": exp.out_of_sample_end,
            "git_commit": exp.git_commit,
        }
