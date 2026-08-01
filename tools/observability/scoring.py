"""Repository health scoring engine.

Computes a weighted composite health score (0.0–1.0) and maps it
to a letter grade (A+/A/B/C/D).

Weight model:
  Ruff (lint)             8%
  Mypy (types)           10%
  Tests (pass/fail)      12%
  Coverage               10%
  Architecture           15%
  Traceability           10%
  Governance (WPS)        8%
  Capabilities           12%
  Security                8%
  Release readiness       7%
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tools.observability.snapshot import MetricsSnapshot


class HealthGrade(StrEnum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"

    @classmethod
    def from_score(cls, score: float) -> HealthGrade:
        if score >= 0.95:
            return cls.A_PLUS
        elif score >= 0.85:
            return cls.A
        elif score >= 0.70:
            return cls.B
        elif score >= 0.55:
            return cls.C
        else:
            return cls.D

    @property
    def emoji(self) -> str:
        return {
            "A+": "🏆",
            "A": "✅",
            "B": "🟡",
            "C": "🟠",
            "D": "🔴",
        }.get(self.value, "❓")


@dataclass
class DimensionScore:
    name: str
    score: float  # 0.0–1.0
    weight: float
    weighted: float
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 4),
            "weight": self.weight,
            "weighted_contribution": round(self.weighted, 4),
            "detail": self.detail,
        }


@dataclass
class HealthScore:
    total: float  # 0.0–1.0
    grade: HealthGrade
    dimensions: list[DimensionScore]

    @property
    def pct(self) -> float:
        return round(self.total * 100, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.total, 4),
            "score_pct": self.pct,
            "grade": self.grade.value,
            "emoji": self.grade.emoji,
            "dimensions": [d.to_dict() for d in self.dimensions],
        }


def _gate(status: str) -> float:
    """Convert PASS/FAIL/UNKNOWN to 0.0–1.0."""
    return 1.0 if status == "PASS" else 0.0


def compute_health_score(snapshot: MetricsSnapshot) -> HealthScore:
    """Compute the composite health score from all metric dimensions."""

    dimensions: list[DimensionScore] = []

    # ── Ruff (lint) — weight 0.08 ─────────────────────────────────────────
    ruff_score = _gate(snapshot.quality.ruff.status)
    dimensions.append(
        DimensionScore("lint_ruff", ruff_score, 0.08, ruff_score * 0.08, "ruff check")
    )

    # ── Mypy (types) — weight 0.10 ────────────────────────────────────────
    mypy_score = _gate(snapshot.quality.mypy.status)
    dimensions.append(
        DimensionScore("types_mypy", mypy_score, 0.10, mypy_score * 0.10, "mypy --strict")
    )

    # ── Tests — weight 0.12 ───────────────────────────────────────────────
    test_score = _gate(snapshot.quality.tests.status)
    dimensions.append(
        DimensionScore(
            "tests",
            test_score,
            0.12,
            test_score * 0.12,
            f"{snapshot.quality.tests.passed}/{snapshot.quality.tests.collected} passed",
        )
    )

    # ── Coverage — weight 0.10 ────────────────────────────────────────────
    cov_pct = snapshot.quality.coverage.line_pct
    # Scale: 80% coverage → 1.0, below 60% → 0.0
    cov_score = min(max((cov_pct - 60.0) / 20.0, 0.0), 1.0) if cov_pct > 0 else 0.0
    dimensions.append(
        DimensionScore(
            "coverage",
            cov_score,
            0.10,
            cov_score * 0.10,
            f"{cov_pct:.1f}% line coverage",
        )
    )

    # ── Architecture — weight 0.15 ────────────────────────────────────────
    arch = snapshot.architecture
    arch_pass = arch.fit_pass
    arch_fail = arch.fit_fail
    arch_total = arch_pass + arch_fail
    arch_score = arch_pass / arch_total if arch_total else 0.5
    dimensions.append(
        DimensionScore(
            "architecture",
            arch_score,
            0.15,
            arch_score * 0.15,
            f"{arch_pass}/{arch_total} fitness functions PASS",
        )
    )

    # ── Governance (TVM coverage) — weight 0.10 ───────────────────────────
    tvm_cov = snapshot.governance.tvm_coverage_pct / 100.0
    dimensions.append(
        DimensionScore(
            "traceability",
            tvm_cov,
            0.10,
            tvm_cov * 0.10,
            f"{snapshot.governance.tvm_requirements_implemented}/"
            f"{snapshot.governance.tvm_requirements_total} requirements",
        )
    )

    # ── WPS/ERS completeness — weight 0.08 ────────────────────────────────
    gov_score = snapshot.governance.wps_completion_pct / 100.0
    dimensions.append(
        DimensionScore(
            "governance_wps",
            gov_score,
            0.08,
            gov_score * 0.08,
            f"{snapshot.governance.wps_completed}/{snapshot.governance.wps_total} WPs complete",
        )
    )

    # ── Capability completion — weight 0.12 ───────────────────────────────
    cap_score = snapshot.repository.completion_pct / 100.0
    dimensions.append(
        DimensionScore(
            "capabilities",
            cap_score,
            0.12,
            cap_score * 0.12,
            f"{snapshot.repository.complete}/{snapshot.repository.total} capabilities COMPLETE",
        )
    )

    # ── Security — weight 0.08 ────────────────────────────────────────────
    sec = snapshot.security
    if sec.overall_status == "PASS":
        sec_score = 1.0
    elif sec.overall_status == "FAIL":
        sec_score = 0.0
    else:
        # Unknown/configured — partial credit based on tooling presence
        tooling_score = 0.0
        if sec.codeql_status == "CONFIGURED":
            tooling_score += 0.5
        if sec.secret_scan_status in ("CONFIGURED", "PARTIAL"):
            tooling_score += 0.5
        sec_score = tooling_score
    dimensions.append(
        DimensionScore(
            "security",
            sec_score,
            0.08,
            sec_score * 0.08,
            f"overall={sec.overall_status}, codeql={sec.codeql_status}",
        )
    )

    # ── Release readiness — weight 0.07 ──────────────────────────────────
    rel_score = snapshot.release.readiness_score / 100.0
    dimensions.append(
        DimensionScore(
            "release_readiness",
            rel_score,
            0.07,
            rel_score * 0.07,
            f"{snapshot.release.readiness_score:.0f}% ready",
        )
    )

    total = sum(d.weighted for d in dimensions)
    total = round(min(total, 1.0), 4)
    grade = HealthGrade.from_score(total)
    return HealthScore(total=total, grade=grade, dimensions=dimensions)
