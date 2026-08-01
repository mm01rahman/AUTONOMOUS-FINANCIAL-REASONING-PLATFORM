"""AFRP observability package.

Provides metric collectors, health scoring, and dashboard generators
for the Engineering Metrics and Repository Observability platform.

Public API::

    from tools.observability import collect_all, HealthScore
"""

from __future__ import annotations

from tools.observability.scoring import HealthGrade, HealthScore
from tools.observability.snapshot import MetricsSnapshot, collect_all

__all__ = [
    "collect_all",
    "HealthGrade",
    "HealthScore",
    "MetricsSnapshot",
]
