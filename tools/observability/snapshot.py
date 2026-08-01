"""Metrics snapshot -- aggregates all collectors into a single object.

``collect_all()`` is the primary entry point for the observability platform.
It runs all collectors and returns a ``MetricsSnapshot``.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.observability.collectors.architecture import ArchitectureMetrics
from tools.observability.collectors.git_metrics import GitMetrics
from tools.observability.collectors.governance import GovernanceMetrics
from tools.observability.collectors.quality import (
    CoverageMetrics,
    MypyMetrics,
    RuffMetrics,
    TestMetrics,
)
from tools.observability.collectors.release import ReleaseMetrics
from tools.observability.collectors.repository import (
    CapabilityMetrics,
    WorkPackageMetrics,
)
from tools.observability.collectors.security import SecurityMetrics


@dataclass
class QualitySnapshot:
    """Aggregates quality collector results."""

    ruff: RuffMetrics = field(default_factory=RuffMetrics)
    mypy: MypyMetrics = field(default_factory=MypyMetrics)
    tests: TestMetrics = field(default_factory=TestMetrics)
    coverage: CoverageMetrics = field(default_factory=CoverageMetrics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ruff": self.ruff.to_dict(),
            "mypy": self.mypy.to_dict(),
            "tests": self.tests.to_dict(),
            "coverage": self.coverage.to_dict(),
        }


@dataclass
class MetricsSnapshot:
    generated_at: str = ""
    repository_name: str = "mm01rahman/AUTONOMOUS-FINANCIAL-REASONING-PLATFORM"
    repository: CapabilityMetrics = field(default_factory=CapabilityMetrics)
    work_packages: WorkPackageMetrics = field(default_factory=WorkPackageMetrics)
    quality: QualitySnapshot = field(default_factory=QualitySnapshot)
    architecture: ArchitectureMetrics = field(default_factory=ArchitectureMetrics)
    governance: GovernanceMetrics = field(default_factory=GovernanceMetrics)
    security: SecurityMetrics = field(default_factory=SecurityMetrics)
    release: ReleaseMetrics = field(default_factory=ReleaseMetrics)
    git: GitMetrics = field(default_factory=GitMetrics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "2.0",
            "generated_at": self.generated_at,
            "repository": self.repository_name,
            "metrics": {
                "repository": self.repository.to_dict(),
                "work_packages": self.work_packages.to_dict(),
                "quality": self.quality.to_dict(),
                "architecture": self.architecture.to_dict(),
                "governance": self.governance.to_dict(),
                "security": self.security.to_dict(),
                "release": self.release.to_dict(),
                "git": self.git.to_dict(),
            },
        }


def collect_all(
    root: Path,
    *,
    skip_quality_checks: bool = False,
    skip_architecture_checks: bool = False,
) -> MetricsSnapshot:
    """Collect all metrics into a MetricsSnapshot."""
    from tools.observability.collectors.architecture import collect_architecture
    from tools.observability.collectors.git_metrics import collect_git
    from tools.observability.collectors.governance import collect_governance
    from tools.observability.collectors.quality import (
        collect_coverage,
        collect_mypy,
        collect_ruff,
        collect_tests,
    )
    from tools.observability.collectors.release import collect_release
    from tools.observability.collectors.repository import (
        collect_capabilities,
        collect_work_packages,
    )
    from tools.observability.collectors.security import collect_security

    snap = MetricsSnapshot()
    snap.generated_at = datetime.datetime.now(datetime.UTC).isoformat()

    snap.repository = collect_capabilities(root)
    snap.work_packages = collect_work_packages(root)
    snap.governance = collect_governance(root)
    snap.security = collect_security(root)
    snap.release = collect_release(root)
    snap.git = collect_git(root)

    snap.quality.coverage = collect_coverage(root)
    if not skip_quality_checks:
        snap.quality.ruff = collect_ruff(root)
        snap.quality.mypy = collect_mypy(root)
        snap.quality.tests = collect_tests(root)
    else:
        snap.quality.ruff = RuffMetrics(status="SKIPPED")
        snap.quality.mypy = MypyMetrics(status="SKIPPED")
        snap.quality.tests = TestMetrics(status="SKIPPED")

    if not skip_architecture_checks:
        snap.architecture = collect_architecture(root)

    return snap
