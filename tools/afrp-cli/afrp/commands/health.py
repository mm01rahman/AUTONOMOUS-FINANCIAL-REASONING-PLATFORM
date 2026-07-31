"""``afrp health`` — repository health analyzer (WP-IMP-0007, FR-005, FIT-007)."""

from __future__ import annotations

import json
from pathlib import Path

import click
from afrp.core.exceptions import AfrpError
from afrp.core.registry import CapabilityStatus, load_registry
from afrp.core.traceability import assert_full_coverage, load_matrix

TVM_RELPATH = Path("03-engineering") / "TRACEABILITY_MATRIX.yaml"
REGISTRY_RELPATH = Path("03-engineering") / "CAPABILITY_REGISTRY.yaml"
COVERAGE_RELPATH = Path("coverage.json")


def read_line_coverage(path: Path) -> float | None:
    """Read percent line coverage from a pytest-cov ``coverage.json`` artifact."""
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    totals = data.get("totals", {})
    percent = totals.get("percent_covered")
    return float(percent) if isinstance(percent, int | float) else None


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

    line_cov = read_line_coverage(root / COVERAGE_RELPATH)
    if line_cov is None:
        click.echo("test_coverage: n/a (run pytest with --cov --cov-report=json)")
    else:
        click.echo(f"test_coverage: {line_cov:.1f}% lines")

    if assert_full:
        try:
            assert_full_coverage(matrix)
        except AfrpError as exc:
            click.echo(f"fit_007: FAIL — {exc}", err=True)
            raise SystemExit(exc.exit_code) from exc
        click.echo("fit_007: PASS (100% requirement coverage)")
    else:
        verdict = "PASS" if covered == total else f"{total - covered} uncovered"
        click.echo(f"fit_007: {verdict}")
