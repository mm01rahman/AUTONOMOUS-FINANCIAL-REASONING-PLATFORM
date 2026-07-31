"""``afrp plan`` — capability DAG planner (WP-IMP-0004, FR-002, FIT-001)."""

from __future__ import annotations

from pathlib import Path

import click
from afrp.core.exceptions import AfrpError
from afrp.core.registry import (
    CapabilityStatus,
    assert_acyclic,
    load_registry,
    next_executable,
)

REGISTRY_RELPATH = Path("03-engineering") / "CAPABILITY_REGISTRY.yaml"


@click.command(name="plan")
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Repository root containing 03-engineering/CAPABILITY_REGISTRY.yaml.",
)
def plan_command(repo_root: Path) -> None:
    """Resolve the execution DAG, verify FIT-001, list next executable targets."""
    try:
        registry = load_registry(repo_root.resolve() / REGISTRY_RELPATH)
        order = assert_acyclic(registry)
        ready = next_executable(registry)
    except AfrpError as exc:
        click.echo(f"HALTED: {exc}", err=True)
        raise SystemExit(exc.exit_code) from exc

    total = len(registry.capabilities)
    complete = sum(
        1 for c in registry.capabilities if c.status is CapabilityStatus.COMPLETE
    )
    click.echo(f"registry: {registry.registry_id} (schema {registry.schema_version})")
    click.echo(f"capabilities: {total} total, {complete} complete")
    click.echo("fit_001: PASS (graph is acyclic)")
    click.echo(f"topological_order: {' -> '.join(order)}")
    if ready:
        click.echo("next_executable:")
        for cap in ready:
            wp = cap.work_package or "(no work package)"
            click.echo(f"  - {cap.id} v{cap.version} [{cap.status}] wp={wp}")
    else:
        click.echo("next_executable: none (all capabilities complete)")
