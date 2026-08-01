"""Scenario validation library loader (Phase B / WP-B2)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCENARIO_DIR = Path(__file__).resolve().parents[2] / "09-validation" / "scenarios"

REQUIRED_SCENARIO_IDS: tuple[str, ...] = (
    "VAL-001",
    "VAL-002",
    "VAL-003",
    "VAL-004",
    "VAL-005",
    "VAL-006",
    "VAL-007",
    "VAL-008",
    "VAL-009",
    "VAL-010",
    "VAL-011",
    "VAL-012",
    "VAL-013",
    "VAL-014",
)


@dataclass(frozen=True)
class ValidationScenario:
    """Scenario specification for replay/regression."""

    scenario_id: str
    title: str
    description: str
    category: str
    date_range_start: str
    date_range_end: str
    datasets: tuple[dict[str, str], ...]
    expected_runtime_behavior: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    validation_notes: tuple[str, ...]
    tags: tuple[str, ...]


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"scenario field {key!r} is required")
    return value


def load_scenarios(directory: Path = SCENARIO_DIR) -> list[ValidationScenario]:
    """Load all scenario YAML files."""
    scenarios: list[ValidationScenario] = []
    for path in sorted(directory.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{path} must contain a YAML object")
        date_range = data.get("date_range", {})
        if not isinstance(date_range, dict):
            raise ValueError(f"{path}: date_range must be object")
        datasets = data.get("datasets", [])
        if not isinstance(datasets, list):
            raise ValueError(f"{path}: datasets must be list")
        scenario = ValidationScenario(
            scenario_id=_required_str(data, "scenario_id"),
            title=_required_str(data, "title"),
            description=_required_str(data, "description"),
            category=_required_str(data, "category"),
            date_range_start=_required_str(date_range, "start"),
            date_range_end=_required_str(date_range, "end"),
            datasets=tuple(
                entry
                for entry in datasets
                if isinstance(entry, dict)
                and isinstance(entry.get("dataset"), str)
                and isinstance(entry.get("path"), str)
            ),
            expected_runtime_behavior=tuple(
                item
                for item in data.get("expected_runtime_behavior", [])
                if isinstance(item, str)
            ),
            acceptance_criteria=tuple(
                item for item in data.get("acceptance_criteria", []) if isinstance(item, str)
            ),
            expected_outputs=tuple(
                item for item in data.get("expected_outputs", []) if isinstance(item, str)
            ),
            validation_notes=tuple(
                item for item in data.get("validation_notes", []) if isinstance(item, str)
            ),
            tags=tuple(item for item in data.get("tags", []) if isinstance(item, str)),
        )
        scenarios.append(scenario)

    found = {scenario.scenario_id for scenario in scenarios}
    missing = [req for req in REQUIRED_SCENARIO_IDS if req not in found]
    if missing:
        raise ValueError(f"missing required scenarios: {', '.join(missing)}")
    return scenarios
