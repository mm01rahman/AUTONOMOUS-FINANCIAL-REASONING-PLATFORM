"""Governance metric collector.

Measures WPS completeness, ERS completeness, evidence coverage,
capability registry consistency, ADR count, and TVM completeness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class GovernanceMetrics:
    # Work Package Schema completeness
    wps_total: int = 0
    wps_completed: int = 0
    wps_with_evidence: int = 0
    # Evidence Record Schema completeness
    ers_total: int = 0
    ers_approved: int = 0
    # Capability registry
    registry_consistent: bool = True
    capabilities_with_wp: int = 0
    capabilities_without_wp: int = 0
    # Traceability
    tvm_requirements_total: int = 0
    tvm_requirements_implemented: int = 0
    tvm_coverage_pct: float = 0.0
    # ADRs
    adr_total: int = 0
    adr_open: int = 0
    adr_accepted: int = 0
    # Completion reports
    completion_reports: int = 0
    # Requirement type breakdown
    req_by_type: dict[str, int] = field(default_factory=dict)

    @property
    def wps_completion_pct(self) -> float:
        return round(self.wps_completed / self.wps_total * 100, 2) if self.wps_total else 0.0

    @property
    def evidence_coverage_pct(self) -> float:
        return (
            round(self.wps_with_evidence / self.wps_completed * 100, 2)
            if self.wps_completed
            else 0.0
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "work_packages": {
                "total": self.wps_total,
                "completed": self.wps_completed,
                "completion_pct": self.wps_completion_pct,
                "with_evidence": self.wps_with_evidence,
                "evidence_coverage_pct": self.evidence_coverage_pct,
            },
            "evidence_records": {
                "total": self.ers_total,
                "approved": self.ers_approved,
            },
            "capability_registry": {
                "consistent": self.registry_consistent,
                "with_work_package": self.capabilities_with_wp,
                "without_work_package": self.capabilities_without_wp,
            },
            "traceability": {
                "requirements_total": self.tvm_requirements_total,
                "requirements_implemented": self.tvm_requirements_implemented,
                "coverage_pct": self.tvm_coverage_pct,
                "by_type": self.req_by_type,
            },
            "adrs": {
                "total": self.adr_total,
                "open": self.adr_open,
                "accepted": self.adr_accepted,
            },
            "completion_reports": self.completion_reports,
        }


def collect_governance(root: Path) -> GovernanceMetrics:
    """Measure governance health across WPS, ERS, TVM, ADRs."""
    m = GovernanceMetrics()

    # ── Work Package Schema metrics ────────────────────────────────────────
    wp_dir = root / "05-work-packages"
    if wp_dir.exists():
        for wp_file in wp_dir.glob("WP-*.yaml"):
            try:
                data: dict[str, Any] = (
                    yaml.safe_load(wp_file.read_text(encoding="utf-8")) or {}
                )
            except yaml.YAMLError:
                continue
            m.wps_total += 1
            status = (data.get("status") or "").lower()
            if status == "completed":
                m.wps_completed += 1
                # Check if evidence directory exists and has files
                wp_id = data.get("work_package_id", wp_file.stem)
                ev_dir = wp_dir / wp_id / "evidence"
                if ev_dir.exists() and any(ev_dir.glob("*.yaml")):
                    m.wps_with_evidence += 1

    # ── Evidence Record Schema metrics ─────────────────────────────────────
    if wp_dir.exists():
        for ev_file in wp_dir.rglob("evidence/*.yaml"):
            try:
                data2: dict[str, Any] = (
                    yaml.safe_load(ev_file.read_text(encoding="utf-8")) or {}
                )
            except yaml.YAMLError:
                continue
            m.ers_total += 1
            # Evidence files use either top-level `status: APPROVED` or
            # `lifecycle.final_state` (ERS-1.0 schema).
            top_status = (data2.get("status") or "").upper()
            lifecycle_state = (
                (data2.get("lifecycle") or {}).get("final_state") or ""
            ).upper()
            if top_status == "APPROVED" or lifecycle_state in (
                "APPROVED",
                "REVIEW_PENDING",
                "COMPLETED",
            ):
                m.ers_approved += 1

    # ── Capability Registry consistency ───────────────────────────────────
    registry_file = root / "03-engineering" / "CAPABILITY_REGISTRY.yaml"
    if registry_file.exists():
        try:
            reg_data: dict[str, Any] = (
                yaml.safe_load(registry_file.read_text(encoding="utf-8")) or {}
            )
            for cap in reg_data.get("capabilities", []):
                wp = cap.get("work_package")
                if wp is not None and wp:
                    m.capabilities_with_wp += 1
                elif wp is None:
                    # Explicit null = foundational (acceptable)
                    m.capabilities_with_wp += 1
                else:
                    m.capabilities_without_wp += 1
        except yaml.YAMLError:
            m.registry_consistent = False

    # ── Traceability Matrix ────────────────────────────────────────────────
    tvm_file = root / "03-engineering" / "TRACEABILITY_MATRIX.yaml"
    if tvm_file.exists():
        try:
            tvm_data: dict[str, Any] = (
                yaml.safe_load(tvm_file.read_text(encoding="utf-8")) or {}
            )
            reqs = tvm_data.get("requirements", [])
            m.tvm_requirements_total = len(reqs)
            for req in reqs:
                if req.get("status") == "implemented":
                    m.tvm_requirements_implemented += 1
                # Count by type prefix
                req_id: str = req.get("id", "")
                prefix = req_id.split("-")[0] if "-" in req_id else req_id
                m.req_by_type[prefix] = m.req_by_type.get(prefix, 0) + 1
            if m.tvm_requirements_total:
                m.tvm_coverage_pct = round(
                    m.tvm_requirements_implemented / m.tvm_requirements_total * 100, 2
                )
        except yaml.YAMLError:
            pass

    # ── ADR count ─────────────────────────────────────────────────────────
    for adr_dir in [root / "02-architecture", root / "00-governance"]:
        if adr_dir.exists():
            for f in adr_dir.rglob("ADR-*.md"):
                m.adr_total += 1
                text = f.read_text(encoding="utf-8", errors="replace").lower()
                if "status: accepted" in text or "## status\naccepted" in text:
                    m.adr_accepted += 1
                elif "status: proposed" in text or "status: open" in text:
                    m.adr_open += 1

    # ── Completion reports ─────────────────────────────────────────────────
    release_dir = root / "10-release"
    if release_dir.exists():
        m.completion_reports = len(list(release_dir.glob("*COMPLETION_REPORT*.md")))

    return m
