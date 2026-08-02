"""``afrp evidence`` — FIT-005 boundary audit command (WP-IMP-0006, FR-004)."""

from __future__ import annotations

from pathlib import Path

import click
from afrp.core.evidence import (
    audit_boundaries,
    compose_boundary_evidence,
    load_evidence,
    modified_files,
    resolve_evidence_target,
    validate_existing_evidence,
    write_evidence,
)
from afrp.core.exceptions import AfrpError, ManifestValidationError
from afrp.core.orchestrator import _workspace_lock
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
    evidence_status = ""
    try:
        with _workspace_lock(root):
            wp = load_work_package(root, wp_id)
            bounded_with_evidence = tuple(
                dict.fromkeys((*wp.bounded_files, *wp.expected_evidence))
            )
            changed = modified_files(root, base_ref)
            audit = audit_boundaries(bounded_with_evidence, changed)
            if audit.compliant:
                if not wp.expected_evidence:
                    raise ManifestValidationError(
                        f"{wp.work_package_id} declares no expected evidence path"
                    )
                target = resolve_evidence_target(
                    root,
                    bounded_with_evidence,
                    wp.expected_evidence[0],
                    allow_existing_unbounded=wp.status == "Completed",
                )
                if target.exists():
                    record = load_evidence(root, target)
                    validate_existing_evidence(record, wp, target, audit)
                    evidence_status = (
                        f"validated existing evidence: {target.relative_to(root)}"
                    )
                else:
                    record = compose_boundary_evidence(wp, audit, ())
                    write_evidence(record, root, target)
                    evidence_status = f"emitted evidence: {target.relative_to(root)}"
    except AfrpError as exc:
        click.echo(f"HALTED: {exc}", err=True)
        raise SystemExit(exc.exit_code) from exc

    click.echo(f"work_package: {wp.work_package_id} ({wp.capability_id} v{wp.capability_version})")
    click.echo(f"bounded_files: {len(wp.bounded_files)}")
    click.echo(f"files_modified: {len(audit.files_modified)}")
    if audit.compliant:
        click.echo("fit_005: PASS (all changes within bounded_files)")
        click.echo(evidence_status)
        return
    click.echo(f"fit_005: FAIL ({len(audit.violations)} violation(s))")
    for name in audit.violations:
        click.echo(f"  OUT-OF-BOUNDS {name}")
    raise SystemExit(3)
