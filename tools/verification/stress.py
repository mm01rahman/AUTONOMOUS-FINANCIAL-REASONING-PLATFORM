"""Stress testing suite (WP-B7)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools import system_gate


@dataclass(frozen=True)
class StressCaseResult:
    case_id: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class StressSuiteReport:
    cases: tuple[StressCaseResult, ...]
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_stress_suite(report_path: Path | None = None) -> StressSuiteReport:
    """Run deterministic stress cases without modifying runtime."""
    cases: list[StressCaseResult] = []

    chaos = system_gate.chaos_total_feed_loss()
    cases.append(
        StressCaseResult(
            case_id="STRESS-001",
            passed=chaos.agent_quorum == 0 and not chaos.trading_permitted,
            detail="total feed loss -> DEGRADED + a_null",
        )
    )

    snapshot = system_gate.semantic_replay()
    cases.append(
        StressCaseResult(
            case_id="STRESS-002",
            passed=len(snapshot.scenario_terminals) > 0,
            detail=f"scenario_paths={len(snapshot.scenario_terminals)}",
        )
    )

    p99 = system_gate.decision_latency_p99(120)
    cases.append(
        StressCaseResult(
            case_id="STRESS-003",
            passed=p99 <= 50.0,
            detail=f"decision_p99={p99:.4f}ms",
        )
    )

    long_replay_hashes = [system_gate.semantic_replay().checksum for _ in range(4)]
    cases.append(
        StressCaseResult(
            case_id="STRESS-004",
            passed=len(set(long_replay_hashes)) == 1,
            detail="long replay deterministic checksum",
        )
    )

    failures = tuple(case.case_id for case in cases if not case.passed)
    report = StressSuiteReport(cases=tuple(cases), failures=failures)
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return report
