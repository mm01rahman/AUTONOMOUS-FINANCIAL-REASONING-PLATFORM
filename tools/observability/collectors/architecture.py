"""Architecture metric collector.

Runs existing AFRP fitness gates and parses their output to extract
architecture health metrics without duplicating gate logic.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _run(cmd: list[str], cwd: Path, timeout: int = 60) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            check=False,
            timeout=timeout,
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)


@dataclass
class FitnessResult:
    id: str
    status: str  # PASS | FAIL | SKIPPED
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "status": self.status, "detail": self.detail}


@dataclass
class ArchitectureMetrics:
    # Fitness function results
    fitness_functions: list[FitnessResult] = field(default_factory=list)
    # Aggregate counts
    violations: int = 0
    fit_pass: int = 0
    fit_fail: int = 0
    # Specific checks
    dag_acyclic: bool = True
    layer_violations: int = 0
    import_cycles: int = 0
    public_api_violations: int = 0
    proto_compatible: bool = True
    # Raw gate outputs
    baseline_gate_status: str = "UNKNOWN"
    ops_gate_status: str = "UNKNOWN"
    proto_gate_status: str = "UNKNOWN"
    validate_status: str = "UNKNOWN"
    plan_status: str = "UNKNOWN"

    @property
    def overall_status(self) -> str:
        if self.fit_fail > 0 or self.violations > 0:
            return "FAIL"
        if self.fit_pass > 0:
            return "PASS"
        return "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "violations": self.violations,
            "fitness_functions": [f.to_dict() for f in self.fitness_functions],
            "fit_pass": self.fit_pass,
            "fit_fail": self.fit_fail,
            "dag_acyclic": self.dag_acyclic,
            "layer_violations": self.layer_violations,
            "import_cycles": self.import_cycles,
            "public_api_violations": self.public_api_violations,
            "proto_compatible": self.proto_compatible,
            "gates": {
                "baseline": self.baseline_gate_status,
                "ops": self.ops_gate_status,
                "proto": self.proto_gate_status,
                "validate": self.validate_status,
                "plan": self.plan_status,
            },
        }


def _parse_fit_result(output: str, fit_id: str) -> FitnessResult:
    """Extract a FIT-NNN result from gate output."""
    fit_lower = fit_id.lower()
    for line in output.splitlines():
        if fit_lower in line.lower():
            if "pass" in line.lower():
                return FitnessResult(fit_id, "PASS", line.strip())
            elif "fail" in line.lower():
                return FitnessResult(fit_id, "FAIL", line.strip())
    return FitnessResult(fit_id, "UNKNOWN")


def collect_architecture(root: Path) -> ArchitectureMetrics:
    """Run architecture gates and parse results."""
    m = ArchitectureMetrics()

    # ── baseline_gate (FIT-002, FIT-004, FIT-006) ────────────────────────
    rc, out = _run(["uv", "run", "python", "-m", "tools.baseline_gate"], root)
    m.baseline_gate_status = "PASS" if rc == 0 else "FAIL"
    for fit_id in ("FIT-002", "FIT-004", "FIT-006"):
        result = _parse_fit_result(out, fit_id)
        m.fitness_functions.append(result)
        if result.status == "PASS":
            m.fit_pass += 1
        elif result.status == "FAIL":
            m.fit_fail += 1
            m.violations += 1

    # ── ops_gate ──────────────────────────────────────────────────────────
    rc2, out2 = _run(["uv", "run", "python", "-m", "tools.ops_gate"], root)
    m.ops_gate_status = "PASS" if rc2 == 0 else "FAIL"

    # ── proto_gate ────────────────────────────────────────────────────────
    rc3, out3 = _run(["uv", "run", "python", "-m", "tools.proto_gate"], root)
    m.proto_gate_status = "PASS" if rc3 == 0 else "FAIL"
    m.proto_compatible = rc3 == 0
    for fit_id in ("FIT-003",):
        m.fitness_functions.append(
            FitnessResult(fit_id, "PASS" if rc3 == 0 else "FAIL", "proto gate")
        )
        if rc3 == 0:
            m.fit_pass += 1
        else:
            m.fit_fail += 1

    # ── afrp validate (FIT-002, FIT-004, FIT-006 via CLI) ─────────────────
    rc4, out4 = _run(["uv", "run", "afrp", "validate"], root)
    m.validate_status = "PASS" if rc4 == 0 else "FAIL"
    if "violations: 0" in out4:
        m.layer_violations = 0
    else:
        for line in out4.splitlines():
            if "violation" in line.lower():
                import re
                found = re.search(r"(\d+)\s+violation", line)
                if found:
                    m.layer_violations = int(found.group(1))

    # ── afrp plan (FIT-001) ───────────────────────────────────────────────
    rc5, out5 = _run(["uv", "run", "afrp", "plan"], root)
    m.plan_status = "PASS" if rc5 == 0 else "FAIL"
    m.dag_acyclic = rc5 == 0
    fit1 = FitnessResult(
        "FIT-001", "PASS" if rc5 == 0 else "FAIL", "DAG acyclicity"
    )
    m.fitness_functions.append(fit1)
    if rc5 == 0:
        m.fit_pass += 1
    else:
        m.fit_fail += 1
        m.violations += 1

    return m
