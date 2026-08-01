"""Repository progress metric collector.

Measures capability completion, work-package progress, and overall
implementation maturity from the CAPABILITY_REGISTRY.yaml and
WPS work package YAML files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CapabilityMetrics:
    total: int = 0
    complete: int = 0
    available: int = 0
    locked: int = 0
    # by stage
    eos_total: int = 0
    eos_complete: int = 0
    runtime_total: int = 0
    runtime_complete: int = 0
    infra_total: int = 0
    infra_complete: int = 0
    # layer breakdown
    layers: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def completion_pct(self) -> float:
        return round(self.complete / self.total * 100, 2) if self.total else 0.0

    @property
    def eos_completion_pct(self) -> float:
        return round(self.eos_complete / self.eos_total * 100, 2) if self.eos_total else 0.0

    @property
    def runtime_completion_pct(self) -> float:
        return (
            round(self.runtime_complete / self.runtime_total * 100, 2)
            if self.runtime_total
            else 0.0
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "complete": self.complete,
            "available": self.available,
            "locked": self.locked,
            "completion_pct": self.completion_pct,
            "eos": {
                "total": self.eos_total,
                "complete": self.eos_complete,
                "completion_pct": self.eos_completion_pct,
            },
            "runtime": {
                "total": self.runtime_total,
                "complete": self.runtime_complete,
                "completion_pct": self.runtime_completion_pct,
            },
            "layers": self.layers,
        }


@dataclass
class WorkPackageMetrics:
    total: int = 0
    completed: int = 0
    in_progress: int = 0
    blocked: int = 0
    remaining: int = 0
    # WP IDs by status
    completed_ids: list[str] = field(default_factory=list)
    in_progress_ids: list[str] = field(default_factory=list)
    blocked_ids: list[str] = field(default_factory=list)

    @property
    def burn_pct(self) -> float:
        return round(self.completed / self.total * 100, 2) if self.total else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "completed": self.completed,
            "in_progress": self.in_progress,
            "blocked": self.blocked,
            "remaining": self.remaining,
            "burn_pct": self.burn_pct,
            "completed_ids": self.completed_ids,
            "in_progress_ids": self.in_progress_ids,
            "blocked_ids": self.blocked_ids,
        }


def collect_capabilities(root: Path) -> CapabilityMetrics:
    """Parse CAPABILITY_REGISTRY.yaml and compute capability metrics."""
    registry_file = root / "03-engineering" / "CAPABILITY_REGISTRY.yaml"
    m = CapabilityMetrics()
    if not registry_file.exists():
        return m
    try:
        data: dict[str, Any] = yaml.safe_load(registry_file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return m

    caps: list[dict[str, Any]] = data.get("capabilities", [])
    m.total = len(caps)

    # Layer name → EOS/Runtime/Infra classification
    eos_prefixes = ("GOV-", "EOS-", "ENG-")
    runtime_prefixes = ("L1-", "L2-", "L3-", "L4-", "L5-", "L6-", "RT-")

    for cap in caps:
        cap_id: str = cap.get("id", "")
        status: str = cap.get("status", "")
        layer: str | None = cap.get("layer")

        if status == "COMPLETE":
            m.complete += 1
        elif status == "AVAILABLE":
            m.available += 1
        elif status == "LOCKED":
            m.locked += 1

        # EOS classification
        if any(cap_id.startswith(p) for p in eos_prefixes):
            m.eos_total += 1
            if status == "COMPLETE":
                m.eos_complete += 1
        # Runtime classification
        elif any(cap_id.startswith(p) for p in runtime_prefixes):
            m.runtime_total += 1
            if status == "COMPLETE":
                m.runtime_complete += 1
        else:
            m.infra_total += 1
            if status == "COMPLETE":
                m.infra_complete += 1

        # Layer breakdown
        if layer:
            if layer not in m.layers:
                m.layers[layer] = {"total": 0, "complete": 0}
            m.layers[layer]["total"] += 1
            if status == "COMPLETE":
                m.layers[layer]["complete"] += 1

    return m


def collect_work_packages(root: Path) -> WorkPackageMetrics:
    """Scan 05-work-packages/*.yaml files and compute WP metrics."""
    wp_dir = root / "05-work-packages"
    m = WorkPackageMetrics()
    if not wp_dir.exists():
        return m

    for wp_file in sorted(wp_dir.glob("WP-*.yaml")):
        try:
            data: dict[str, Any] = yaml.safe_load(wp_file.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        wp_id = data.get("work_package_id", wp_file.stem)
        status: str = (data.get("status") or "").lower()
        m.total += 1
        if status == "completed":
            m.completed += 1
            m.completed_ids.append(wp_id)
        elif status == "in_progress":
            m.in_progress += 1
            m.in_progress_ids.append(wp_id)
        elif status == "blocked":
            m.blocked += 1
            m.blocked_ids.append(wp_id)
        else:
            m.remaining += 1

    return m
