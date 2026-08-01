"""Performance benchmark suite (WP-B8)."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools import system_gate


@dataclass(frozen=True)
class PerformanceReport:
    replay_speed_events_per_sec: float
    decision_p99_ms: float
    throughput_paths: int
    benchmark_samples: int
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def benchmark_performance(report_path: Path | None = None) -> PerformanceReport:
    """Benchmark replay and decision path latency."""
    started = time.perf_counter()
    snapshot = system_gate.semantic_replay()
    elapsed = max(time.perf_counter() - started, 1e-9)
    events = len(snapshot.features) + len(snapshot.scenario_terminals)
    replay_speed = events / elapsed
    p99 = system_gate.decision_latency_p99(180)
    report = PerformanceReport(
        replay_speed_events_per_sec=replay_speed,
        decision_p99_ms=p99,
        throughput_paths=len(snapshot.scenario_terminals),
        benchmark_samples=180,
        passed=p99 <= 50.0,
    )
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return report
