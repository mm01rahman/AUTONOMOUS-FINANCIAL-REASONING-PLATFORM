"""Mathematical invariant verification (WP-B4)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from afrp_runtime.layer3.dsmt import combine_all, discount, pignistic
from afrp_runtime.layer6.learning import BrierCalibrator, multiclass_brier

from tools import system_gate


@dataclass(frozen=True)
class MathCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class MathVerificationReport:
    checks: tuple[MathCheck, ...]
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify_mathematics(report_path: Path | None = None) -> MathVerificationReport:
    """Verify PCR5, masses, utility and learning invariants."""
    checks: list[MathCheck] = []

    fused, conflict = combine_all(
        [
            {"BULL": 0.6, "BEAR": 0.2, "RANGE": 0.1, "THETA": 0.1},
            {"BULL": 0.5, "BEAR": 0.3, "RANGE": 0.1, "THETA": 0.1},
        ]
    )
    checks.append(
        MathCheck(
            name="PCR5 mass conservation",
            passed=abs(sum(fused.values()) - 1.0) < 1e-9,
            detail=f"sum={sum(fused.values()):.12f}, conflict={conflict:.12f}",
        )
    )
    discounted = discount({"BULL": 0.5, "BEAR": 0.2, "RANGE": 0.1, "THETA": 0.2}, 0.7)
    checks.append(
        MathCheck(
            name="Reliability discounting bounds",
            passed=all(0.0 <= mass <= 1.0 for mass in discounted.values())
            and abs(sum(discounted.values()) - 1.0) < 1e-9,
            detail=f"sum={sum(discounted.values()):.12f}",
        )
    )
    betp = pignistic(fused)
    checks.append(
        MathCheck(
            name="Pignistic transform normalization",
            passed=abs(sum(betp.values()) - 1.0) < 1e-9,
            detail=f"sum={sum(betp.values()):.12f}",
        )
    )

    brier = multiclass_brier({"BULL": 0.7, "BEAR": 0.2, "RANGE": 0.1}, "BULL")
    calibrator = BrierCalibrator("MP-04")
    calibrator.observe("L2-MAC", {"BULL": 0.7, "BEAR": 0.2, "RANGE": 0.1}, "BULL")
    weights = calibrator.weights()
    checks.append(
        MathCheck(
            name="Brier score and calibration bounds",
            passed=0.0 <= brier <= 2.0 and all(0.05 <= value <= 1.0 for value in weights.values()),
            detail=f"brier={brier:.6f}, weights={weights}",
        )
    )

    snapshot = system_gate.semantic_replay()
    world_mass_sum = sum(value for _, value in snapshot.world_masses)
    checks.append(
        MathCheck(
            name="Replay world mass sum",
            passed=abs(world_mass_sum - 1.0) < 1e-9,
            detail=f"sum={world_mass_sum:.12f}",
        )
    )

    failures = tuple(check.name for check in checks if not check.passed)
    report = MathVerificationReport(checks=tuple(checks), failures=failures)
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return report
