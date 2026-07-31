"""``afrp run`` — Work Package orchestrator command (WP-IMP-0008, FR-006)."""

from __future__ import annotations

from pathlib import Path

import click
from afrp.core.lifecycle import LifecycleState
from afrp.core.orchestrator import orchestrate


@click.command(name="run")
@click.option("--wp", "wp_id", required=True, help="Work Package id, e.g. WP-IMP-0009.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Evaluate baseline/contract/preconditions only; never execute.")
@click.option("--skip-gates", is_flag=True, default=False,
              help="Record gates as externally executed (post-hoc audit mode).")
@click.option("--base-ref", default="HEAD", show_default=True,
              help="Git ref used for FIT-005 diff and rollback.")
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Repository root.",
)
def run_command(
    wp_id: str, dry_run: bool, skip_gates: bool, base_ref: str, repo_root: Path
) -> None:
    """Drive a Work Package through the RSM-1.0 lifecycle under EGP-2.0."""
    report = orchestrate(
        repo_root.resolve(),
        wp_id,
        dry_run=dry_run,
        skip_gates=skip_gates,
        base_ref=base_ref,
    )
    click.echo(f"work_package: {report.work_package_id}")
    for state, note in report.transitions:
        suffix = f" — {note}" if note else ""
        click.echo(f"  -> {state}{suffix}")
    for pre in report.preconditions:
        click.echo(f"precondition [{'PASS' if pre.passed else 'FAIL'}] {pre.predicate}")
    for gate in report.gates:
        click.echo(f"gate [{'PASS' if gate.passed else 'FAIL'}] {gate.gate}: {gate.detail}")
    for name in report.boundary_violations:
        click.echo(f"OUT-OF-BOUNDS {name}")
    click.echo(f"final_state: {report.final_state}")
    if report.final_state is LifecycleState.HALTED and not dry_run:
        raise SystemExit(3)
