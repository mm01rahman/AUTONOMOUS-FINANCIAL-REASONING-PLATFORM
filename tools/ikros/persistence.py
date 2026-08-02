"""IKROS persistence — deterministic YAML serialization for all entities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# YAML serialization helpers
# ---------------------------------------------------------------------------


def _represent_none(dumper: yaml.Dumper, _data: None) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:null", "null")


def _make_dumper() -> type[yaml.Dumper]:
    """Return a Dumper that represents None as 'null' and preserves key order."""
    dumper = yaml.Dumper
    dumper.add_representer(type(None), _represent_none)
    return dumper


def _normalize_for_yaml(value: object) -> object:
    if isinstance(value, dict):
        return {key: _normalize_for_yaml(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_normalize_for_yaml(item) for item in value]
    if isinstance(value, list):
        return [_normalize_for_yaml(item) for item in value]
    return value


def to_yaml(data: dict[str, Any]) -> str:
    """Serialize a dict to a canonical YAML string (deterministic, sorted keys)."""
    return yaml.dump(
        _normalize_for_yaml(data),
        Dumper=_make_dumper(),
        default_flow_style=False,
        sort_keys=True,
        allow_unicode=True,
    )


def from_yaml(text: str) -> dict[str, Any]:
    """Deserialize YAML text to a dict."""
    result = yaml.safe_load(text)
    if not isinstance(result, dict):
        raise ValueError(f"Expected YAML mapping, got {type(result).__name__}")
    return result


# ---------------------------------------------------------------------------
# File-level persistence
# ---------------------------------------------------------------------------


def write_entity(path: Path, data: dict[str, Any]) -> None:
    """Write a single entity dict to a YAML file (creates parent dirs)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_yaml(data), encoding="utf-8")


def read_entity(path: Path) -> dict[str, Any]:
    """Read a YAML file and return the entity dict."""
    return from_yaml(path.read_text(encoding="utf-8"))


def entity_path(base_dir: Path, entity_type: str, ikros_id: str) -> Path:
    """Return the canonical file path for an entity."""
    subdir = _TYPE_SUBDIRS.get(entity_type, entity_type.lower())
    return base_dir / subdir / f"{ikros_id}.yaml"


_TYPE_SUBDIRS: dict[str, str] = {
    "ResearchQuestion": "research",
    "Hypothesis": "hypotheses",
    "Experiment": "experiments",
    "Feature": "features",
    "FeatureFamily": "features",
    "AlphaCandidate": "alphas",
    "Alpha": "alphas",
}
