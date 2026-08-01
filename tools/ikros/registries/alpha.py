"""Alpha Registry — manages AlphaCandidate and Alpha entities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.ikros.models import Alpha, AlphaCandidate, PromotionStatus
from tools.ikros.registries.base import BaseRegistry, RegistryError


class AlphaRegistry(BaseRegistry[AlphaCandidate]):
    """Registry for AlphaCandidate and promoted Alpha entities.

    Persists to ``{base_dir}/alphas/``.
    AlphaCandidates and Alphas share a directory with distinct IKROS ID prefixes.
    """

    entity_type = "AlphaCandidate"

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__(base_dir)
        self._alphas: dict[str, Alpha] = {}
        if base_dir is not None:
            self._load_alphas()

    def _deserialize(self, data: dict[str, Any]) -> AlphaCandidate:
        return AlphaCandidate.from_dict(data)

    # ------------------------------------------------------------------
    # AlphaCandidate queries
    # ------------------------------------------------------------------

    def candidates(self) -> list[AlphaCandidate]:
        """Return all active candidates."""
        return self.list_by_state(PromotionStatus.CANDIDATE.value)

    def rejected(self) -> list[AlphaCandidate]:
        """Return all rejected candidates (permanent institutional memory)."""
        return self.list_by_state(PromotionStatus.REJECTED.value)

    def by_strategy_type(self, strategy_type: str) -> list[AlphaCandidate]:
        return self.find({"strategy_type": strategy_type})

    def promotion_eligible(
        self,
        min_sharpe: float = 1.0,
        max_drawdown: float = 0.20,
        min_direction_accuracy: float = 0.52,
    ) -> list[AlphaCandidate]:
        """Return candidates meeting minimum promotion criteria."""
        return [
            c
            for c in self._store.values()
            if c.promotion_status == PromotionStatus.CANDIDATE.value
            and c.sharpe_oos >= min_sharpe
            and c.max_drawdown <= max_drawdown
            and c.direction_accuracy >= min_direction_accuracy
        ]

    def reject(self, candidate_id: str, reasons: list[str]) -> AlphaCandidate:
        """Reject a candidate with documented reasons (creates permanent record)."""
        if not reasons:
            raise RegistryError("rejection_reasons must be non-empty")
        entity = self.get(candidate_id)
        if entity.promotion_status != PromotionStatus.CANDIDATE.value:
            raise RegistryError(
                f"Cannot reject candidate in state '{entity.promotion_status}'"
            )
        return self.update(
            candidate_id,
            {
                "promotion_status": PromotionStatus.REJECTED.value,
                "rejection_reasons": reasons,
                "lifecycle_state": PromotionStatus.REJECTED.value,
            },
        )

    # ------------------------------------------------------------------
    # Alpha (promoted) management
    # ------------------------------------------------------------------

    def promote(self, candidate_id: str, alpha: Alpha) -> str:
        """Promote a candidate to Alpha status. Returns the alpha's ikros_id."""
        candidate = self.get(candidate_id)
        if candidate.promotion_status != PromotionStatus.CANDIDATE.value:
            raise RegistryError(
                f"Cannot promote candidate in state '{candidate.promotion_status}'"
            )
        if not alpha.lineage.evidence.ers_records:
            raise RegistryError("Alpha promotion requires ERS evidence records (LIN-006)")
        if alpha.ikros_id in self._alphas:
            raise RegistryError(f"Duplicate Alpha '{alpha.ikros_id}'")
        # Attach ERS evidence to the candidate before marking it PROMOTED (LIN-006)
        candidate_lineage = candidate.lineage.to_dict()
        candidate_lineage["evidence"]["ers_records"] = list(alpha.lineage.evidence.ers_records)
        self.update(candidate_id, {"lineage": candidate_lineage})
        # Update candidate to PROMOTED state
        self.update(
            candidate_id,
            {
                "promotion_status": PromotionStatus.PROMOTED.value,
                "lifecycle_state": PromotionStatus.PROMOTED.value,
            },
        )
        # Store alpha
        self._alphas[alpha.ikros_id] = alpha
        if self._base_dir is not None:
            from tools.ikros.persistence import entity_path, write_entity

            path = entity_path(self._base_dir, "Alpha", alpha.ikros_id)
            write_entity(path, alpha.to_dict())
        return alpha.ikros_id

    def get_alpha(self, alpha_id: str) -> Alpha:
        if alpha_id not in self._alphas:
            raise KeyError(f"Alpha '{alpha_id}' not found")
        return self._alphas[alpha_id]

    def list_alphas(self) -> list[Alpha]:
        return list(self._alphas.values())

    def alpha_count(self) -> int:
        return len(self._alphas)

    def _load_alphas(self) -> None:
        assert self._base_dir is not None
        from tools.ikros.persistence import read_entity

        for yaml_file in self._base_dir.rglob("IKROS-ALPHA-*.yaml"):
            try:
                data = read_entity(yaml_file)
                alpha = Alpha.from_dict(data)
                self._alphas[alpha.ikros_id] = alpha
            except (KeyError, ValueError):
                pass
