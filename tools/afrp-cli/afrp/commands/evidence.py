"""``afrp evidence`` — FIT-005 boundary audit command (WP-IMP-0006, FR-004)."""

from __future__ import annotations

from pathlib import Path

import click
from afrp.core.evidence import audit_boundaries, modified_files
from afrp.core.exceptions import AfrpError
from afrp.core.workpackage import load_work_package


@click.command(name="evidence")
@click.option("--wp", "wp_id", required=True, help="Work Package id, e.g. WP-IMP-0006.")
@click.option(
    "--base-ref",
    default="HEAD",
    show_default=True,
    help="Git ref the working tree is diffed against.",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Repository root.",
)
def evidence_command(wp_id: str, base_ref: str, repo_root: Path) -> None:
    """Audit working-tree changes against the Work Package bounded_files."""
    root = repo_root.resolve()
    try:
        wp = load_work_package(root, wp_id)
        changed = modified_files(root, base_ref)
        audit = audit_boundaries(wp.bounded_files, changed)
    except AfrpError as exc:
        click.echo(f"HALTED: {exc}", err=True)
        raise SystemExit(exc.exit_code) from exc

    click.echo(f"work_package: {wp.work_package_id} ({wp.capability_id} v{wp.capability_version})")
    click.echo(f"bounded_files: {len(wp.bounded_files)}")
    click.echo(f"files_modified: {len(audit.files_modified)}")
    if audit.compliant:
        click.echo("fit_005: PASS (all changes within bounded_files)")
        return
    click.echo(f"fit_005: FAIL ({len(audit.violations)} violation(s))")
    for name in audit.violations:
        click.echo(f"  OUT-OF-BOUNDS {name}")
    raise SystemExit(3)
