"""Hypothesis Registry — manages Hypothesis entities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.ikros.models import Hypothesis, HypothesisStatus
from tools.ikros.registries.base import BaseRegistry


class HypothesisRegistry(BaseRegistry[Hypothesis]):
    """Registry for Hypothesis entities.

    Persists to ``{base_dir}/hypotheses/IKROS-HYP-*.yaml``.
    """

    entity_type = "Hypothesis"

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__(base_dir)

    def _deserialize(self, data: dict[str, Any]) -> Hypothesis:
        return Hypothesis.from_dict(data)

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------

    def supported(self) -> list[Hypothesis]:
        """Return all supported hypotheses."""
        return self.list_by_state(HypothesisStatus.SUPPORTED.value)

    def refuted(self) -> list[Hypothesis]:
        """Return all refuted hypotheses (institutional memory of failed ideas)."""
        return self.list_by_state(HypothesisStatus.REFUTED.value)

    def under_testing(self) -> list[Hypothesis]:
        """Return all hypotheses currently under test."""
        return self.list_by_state(HypothesisStatus.TESTING.value)

    def by_source_rq(self, rq_id: str) -> list[Hypothesis]:
        """Return hypotheses derived from a specific research question."""
        return self.find({"source_rq": rq_id})

    def update_posterior_confidence(
        self, hyp_id: str, posterior: float
    ) -> Hypothesis:
        """Update the posterior confidence after new evidence."""
        if not (0.0 <= posterior <= 1.0):
            raise ValueError(f"posterior must be in [0, 1], got {posterior}")
        return self.update(hyp_id, {"posterior_confidence": posterior})

    def add_experiment(self, hyp_id: str, experiment_id: str) -> Hypothesis:
        """Record that an experiment tests this hypothesis."""
        entity = self.get(hyp_id)
        if experiment_id not in entity.experiments:
            updated = entity.experiments + [experiment_id]
            entity = self.update(hyp_id, {"experiments": updated})
        # Also update lineage
        tested_in = entity.lineage.experiments.tested_in
        if experiment_id not in tested_in:
            lineage_data = entity.lineage.to_dict()
            lineage_data["experiments"]["tested_in"] = tested_in + [experiment_id]
            entity = self.update(hyp_id, {"lineage": lineage_data})
        return entity

    def add_validation(self, hyp_id: str, validation_id: str) -> Hypothesis:
        """Record that a validation supports or tests this hypothesis."""
        entity = self.get(hyp_id)
        if validation_id not in entity.validations:
            updated = entity.validations + [validation_id]
            entity = self.update(hyp_id, {"validations": updated})
        lineage_data = entity.lineage.to_dict()
        validated_by = lineage_data["experiments"]["validated_by"]
        if validation_id not in validated_by:
            lineage_data["experiments"]["validated_by"] = validated_by + [validation_id]
            entity = self.update(hyp_id, {"lineage": lineage_data})
        return entity
