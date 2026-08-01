"""Research Registry — manages ResearchQuestion entities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.ikros.models import ResearchQuestion, ResearchStatus
from tools.ikros.registries.base import BaseRegistry


class ResearchRegistry(BaseRegistry[ResearchQuestion]):
    """Registry for ResearchQuestion entities.

    Persists to ``{base_dir}/research/IKROS-RQ-*.yaml``.
    """

    entity_type = "ResearchQuestion"

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__(base_dir)

    def _deserialize(self, data: dict[str, Any]) -> ResearchQuestion:
        return ResearchQuestion.from_dict(data)

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------

    def open_questions(self) -> list[ResearchQuestion]:
        """Return all unanswered research questions."""
        return self.list_by_state(ResearchStatus.OPEN.value)

    def active_questions(self) -> list[ResearchQuestion]:
        """Return all actively researched questions."""
        return self.list_by_state(ResearchStatus.ACTIVE.value)

    def answered_questions(self) -> list[ResearchQuestion]:
        """Return all answered research questions."""
        return self.list_by_state(ResearchStatus.ANSWERED.value)

    def by_instrument(self, instrument: str) -> list[ResearchQuestion]:
        """Return research questions for a specific instrument."""
        return self.find({"instrument": instrument})

    def by_campaign(self, campaign_tag: str) -> list[ResearchQuestion]:
        """Return all research questions belonging to a campaign."""
        return self.find({"campaign_tag": campaign_tag})

    def link_hypothesis(self, rq_id: str, hypothesis_id: str) -> ResearchQuestion:
        """Add a hypothesis ID to a research question's linked_hypotheses list."""
        entity = self.get(rq_id)
        if hypothesis_id not in entity.linked_hypotheses:
            updated_list = entity.linked_hypotheses + [hypothesis_id]
            return self.update(rq_id, {"linked_hypotheses": updated_list})
        return entity

    def link_conclusion(self, rq_id: str, conclusion_id: str) -> ResearchQuestion:
        """Add a conclusion ID to a research question's linked_conclusions list."""
        entity = self.get(rq_id)
        if conclusion_id not in entity.linked_conclusions:
            updated_list = entity.linked_conclusions + [conclusion_id]
            return self.update(rq_id, {"linked_conclusions": updated_list})
        return entity
