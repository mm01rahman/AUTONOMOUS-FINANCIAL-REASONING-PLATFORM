"""AFRP repository metrics generator.

Collects and publishes:
  - test count and status
  - coverage percentage
  - mypy status
  - ruff status
  - security findings
  - dependency status
  - repository health score
  - capability completion ratio
  - traceability coverage

Usage:
  uv run python -m tools.metrics
  uv run python -m tools.metrics --output metrics.json
"""

from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import click
import yaml

_ROOT = Path(__file__).parent.parent


def _run(cmd: list[str], cwd: Path = _ROOT) -> tuple[int, str]:
    """Run a command and return (returncode, output)."""
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, check=False)
    return result.returncode, (result.stdout + result.stderr).strip()


def _read_coverage(root: Path) -> dict[str, Any]:
    """Read coverage.json metrics."""
    coverage_file = root / "coverage.json"
    if not coverage_file.exists():
        return {"available": False, "percent": None}
    try:
        data = json.loads(coverage_file.read_text(encoding="utf-8"))
        totals = data.get("totals", {})
        return {
            "available": True,
            "percent": round(totals.get("percent_covered", 0.0), 2),
            "lines_covered": totals.get("covered_lines", 0),
            "lines_total": totals.get("num_statements", 0),
            "branches_covered": totals.get("covered_branches", 0),
            "branches_total": totals.get("num_branches", 0),
        }
    except (OSError, json.JSONDecodeError):
        return {"available": False, "percent": None}


def _load_registry(root: Path) -> dict[str, Any]:
    """Load capability registry metrics."""
    registry_file = root / "03-engineering" / "CAPABILITY_REGISTRY.yaml"
    if not registry_file.exists():
        return {"total": 0, "complete": 0, "completion_ratio": 0.0}
    try:
        data = yaml.safe_load(registry_file.read_text(encoding="utf-8"))
        caps = data.get("capabilities", [])
        total = len(caps)
        complete = sum(1 for c in caps if c.get("status") == "COMPLETE")
        return {
            "total": total,
            "complete": complete,
            "completion_ratio": round(complete / total, 4) if total else 0.0,
        }
    except (OSError, yaml.YAMLError):
        return {"total": 0, "complete": 0, "completion_ratio": 0.0}


def _load_traceability(root: Path) -> dict[str, Any]:
    """Load traceability matrix metrics."""
    tvm_file = root / "03-engineering" / "TRACEABILITY_MATRIX.yaml"
    if not tvm_file.exists():
        return {"total": 0, "implemented": 0, "coverage": 0.0}
    try:
        data = yaml.safe_load(tvm_file.read_text(encoding="utf-8"))
        reqs = data.get("requirements", [])
        total = len(reqs)
        implemented = sum(1 for r in reqs if r.get("status") == "implemented")
        return {
            "total": total,
            "implemented": implemented,
            "coverage": round(implemented / total, 4) if total else 0.0,
        }
    except (OSError, yaml.YAMLError):
        return {"total": 0, "implemented": 0, "coverage": 0.0}


def _check_ruff(root: Path) -> dict[str, Any]:
    """Run ruff check and return status."""
    rc, out = _run(["uv", "run", "ruff", "check", "."], root)
    return {"status": "PASS" if rc == 0 else "FAIL", "exit_code": rc}


def _check_mypy(root: Path) -> dict[str, Any]:
    """Run mypy --strict and return status."""
    rc, out = _run(
        ["uv", "run", "mypy", "--strict", "tools", "06-runtime", "07-research", "tests"],
        root,
    )
    return {"status": "PASS" if rc == 0 else "FAIL", "exit_code": rc}


def _check_pytest(root: Path) -> dict[str, Any]:
    """Run pytest and return test count and status."""
    rc, out = _run(
        ["uv", "run", "pytest", "tests", "--co", "-q", "--no-header"],
        root,
    )
    # Count test items from collection output
    test_count = 0
    for line in out.splitlines():
        if " selected" in line or "test session starts" in line:
            continue
        if line.strip() and not line.startswith(("=", "E", "W", "collected")):
            test_count += 1
    # Re-run to get collected count
    rc2, out2 = _run(
        ["uv", "run", "pytest", "tests", "--co", "-q", "--no-header", "--tb=no"],
        root,
    )
    for line in out2.splitlines():
        if "selected" in line:
            parts = line.split()
            for _i, p in enumerate(parts):
                if p.isdigit():
                    test_count = int(p)
                    break
    return {
        "status": "PASS" if rc == 0 else "FAIL",
        "exit_code": rc,
        "collected": test_count,
    }


def _health_score(
    coverage: dict[str, Any],
    ruff: dict[str, Any],
    mypy: dict[str, Any],
    pytest: dict[str, Any],
    registry: dict[str, Any],
    traceability: dict[str, Any],
) -> float:
    """Compute composite repository health score (0.0–1.0)."""
    scores = []

    # Coverage: weight 0.20
    cov_pct = coverage.get("percent") or 0.0
    scores.append(("coverage", min(cov_pct / 80.0, 1.0) * 0.20))

    # Lint: weight 0.15
    scores.append(("ruff", (1.0 if ruff["status"] == "PASS" else 0.0) * 0.15))

    # Types: weight 0.15
    scores.append(("mypy", (1.0 if mypy["status"] == "PASS" else 0.0) * 0.15))

    # Tests: weight 0.20
    scores.append(("pytest", (1.0 if pytest["status"] == "PASS" else 0.0) * 0.20))

    # Capability completion: weight 0.15
    scores.append(("capabilities", registry.get("completion_ratio", 0.0) * 0.15))

    # Traceability: weight 0.15
    scores.append(("traceability", traceability.get("coverage", 0.0) * 0.15))

    total = sum(v for _, v in scores)
    return round(total, 4)


@click.command()
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Write metrics JSON to this file.",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Repository root.",
)
@click.option("--skip-checks", is_flag=True, default=False, help="Skip running ruff/mypy/pytest.")
def main(output: Path | None, repo_root: Path, skip_checks: bool) -> None:
    """Generate AFRP repository metrics report."""
    root = repo_root.resolve()

    click.echo("Collecting repository metrics...")

    coverage = _read_coverage(root)
    registry = _load_registry(root)
    traceability = _load_traceability(root)

    if skip_checks:
        ruff = {"status": "SKIPPED", "exit_code": -1}
        mypy = {"status": "SKIPPED", "exit_code": -1}
        pytest_m = {"status": "SKIPPED", "exit_code": -1, "collected": 0}
    else:
        click.echo("  Running ruff...")
        ruff = _check_ruff(root)
        click.echo("  Running mypy...")
        mypy = _check_mypy(root)
        click.echo("  Collecting pytest...")
        pytest_m = _check_pytest(root)

    score = _health_score(coverage, ruff, mypy, pytest_m, registry, traceability)

    metrics: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "repository": "mm01rahman/AUTONOMOUS-FINANCIAL-REASONING-PLATFORM",
        "health_score": score,
        "health_grade": (
            "A" if score >= 0.90 else "B" if score >= 0.75 else "C" if score >= 0.60 else "D"
        ),
        "quality": {
            "ruff": ruff,
            "mypy_strict": mypy,
            "pytest": pytest_m,
            "coverage": coverage,
        },
        "capabilities": registry,
        "traceability": traceability,
        "summary": {
            "health_score": score,
            "coverage_pct": coverage.get("percent"),
            "capabilities_complete": registry["complete"],
            "capabilities_total": registry["total"],
            "requirements_implemented": traceability["implemented"],
            "requirements_total": traceability["total"],
        },
    }

    # Print summary
    click.echo(f"\nRepository Health Score: {score:.1%} ({metrics['health_grade']})")
    click.echo(f"  Coverage:      {coverage.get('percent', 'n/a')}%")
    click.echo(f"  Ruff:          {ruff['status']}")
    click.echo(f"  Mypy:          {mypy['status']}")
    click.echo(f"  Pytest:        {pytest_m['status']}")
    click.echo(
        f"  Capabilities:  {registry['complete']}/{registry['total']} "
        f"({registry['completion_ratio']:.1%})"
    )
    click.echo(
        f"  Traceability:  {traceability['implemented']}/{traceability['total']} "
        f"({traceability['coverage']:.1%})"
    )

    if output:
        output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        click.echo(f"\nMetrics written to: {output}")
    else:
        click.echo("\n" + json.dumps(metrics, indent=2))


if __name__ == "__main__":
    sys.exit(main())
