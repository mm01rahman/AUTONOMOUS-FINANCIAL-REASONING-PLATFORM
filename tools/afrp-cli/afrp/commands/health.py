"""``afrp health`` — repository health analyzer (WP-IMP-0007, FR-005, FIT-007)."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import click
from afrp.core.exceptions import AfrpError, InvariantError, ManifestValidationError
from afrp.core.registry import CapabilityStatus, load_registry
from afrp.core.traceability import assert_full_coverage, load_matrix

TVM_RELPATH = Path("03-engineering") / "TRACEABILITY_MATRIX.yaml"
REGISTRY_RELPATH = Path("03-engineering") / "CAPABILITY_REGISTRY.yaml"
COVERAGE_RELPATH = Path("coverage.json")


def read_line_coverage(path: Path) -> float | None:
    """Read percent line coverage from a pytest-cov ``coverage.json`` artifact."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestValidationError(f"coverage.json is malformed: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("totals"), dict):
        raise ManifestValidationError("coverage.json totals must be an object")
    percent = data["totals"].get("percent_covered")
    if not isinstance(percent, int | float) or isinstance(percent, bool):
        raise ManifestValidationError("coverage.json percent_covered must be numeric")
    value = float(percent)
    if not 0.0 <= value <= 100.0:
        raise ManifestValidationError("coverage.json percent_covered is out of range")
    return value


def collect_coverage(
    repo_root: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> None:
    """Collect coverage in normal CLI use without invoking a shell."""
    try:
        result = runner(
            [
                "uv",
                "run",
                "pytest",
                "tests",
                "--cov",
                "--cov-report=json",
                "-q",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise InvariantError("EOS-HEALTH", f"coverage collector spawn failed: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip()[-2000:]
        raise InvariantError("EOS-HEALTH", f"coverage collection failed: {detail}")


def _running_under_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


@click.command(name="health")
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Repository root.",
)
@click.option(
    "--assert-full",
    is_flag=True,
    default=False,
    help="Fail (FIT-007) unless traceability coverage is 100%.",
)
def health_command(repo_root: Path, assert_full: bool) -> None:
    """Report TVM coverage (FIT-007), registry progress, and test coverage."""
    root = repo_root.resolve()
    try:
        matrix = load_matrix(root / TVM_RELPATH)
        registry = load_registry(root / REGISTRY_RELPATH)
        coverage_path = root / COVERAGE_RELPATH
        if not coverage_path.is_file() and not _running_under_pytest():
            collect_coverage(root)
        line_cov = read_line_coverage(coverage_path)
    except AfrpError as exc:
        click.echo(f"HALTED: {exc}", err=True)
        raise SystemExit(exc.exit_code) from exc

    total = len(matrix.requirements)
    covered = len(matrix.covered)
    click.echo(f"traceability: {covered}/{total} requirements covered "
               f"({matrix.coverage_ratio:.1%})")

    caps_total = len(registry.capabilities)
    caps_done = sum(
        1 for c in registry.capabilities if c.status is CapabilityStatus.COMPLETE
    )
    click.echo(f"capabilities: {caps_done}/{caps_total} complete "
               f"({caps_done / caps_total:.1%})" if caps_total else "capabilities: none")

    if line_cov is None:
        click.echo("test_coverage: n/a (coverage unavailable during pytest)")
    else:
        click.echo(f"test_coverage: {line_cov:.1f}% lines")

    if assert_full:
        try:
            assert_full_coverage(matrix)
            incomplete = [
                capability.id
                for capability in registry.capabilities
                if capability.status is not CapabilityStatus.COMPLETE
            ]
            if incomplete:
                raise InvariantError(
                    "FIT-007",
                    f"incomplete capabilities: {', '.join(incomplete)}",
                )
            if line_cov is None:
                raise InvariantError("FIT-007", "coverage.json is required")
        except AfrpError as exc:
            click.echo(f"fit_007: FAIL — {exc}", err=True)
            raise SystemExit(exc.exit_code) from exc
        click.echo("fit_007: PASS (100% requirement coverage)")
    else:
        verdict = "PASS" if covered == total else f"{total - covered} uncovered"
        click.echo(f"fit_007: {verdict}")
