"""``afrp validate`` — AST invariant checker command (WP-IMP-0005, FR-003)."""

from __future__ import annotations

from pathlib import Path

import click
from afrp.core.astcheck import scan_paths
from afrp.core.exceptions import AfrpError
from afrp.core.kernel import load_kernel

DEFAULT_SCAN_ROOTS = (
    Path("tools") / "afrp-cli",
    Path("06-runtime"),
    Path("07-research"),
    Path("tests"),
)
KERNEL_RELPATH = Path("00-governance") / "KERNEL.md"


@click.command(name="validate")
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Repository root to scan.",
)
def validate_command(repo_root: Path) -> None:
    """Run FIT-002/FIT-004 AST audits and re-assert FIT-006 kernel budget."""
    root = repo_root.resolve()
    try:
        kernel = load_kernel(root / KERNEL_RELPATH)
        violations = scan_paths([root / rel for rel in DEFAULT_SCAN_ROOTS])
    except AfrpError as exc:
        click.echo(f"HALTED: {exc}", err=True)
        raise SystemExit(exc.exit_code) from exc
    except SyntaxError as exc:
        click.echo(f"HALTED: syntax error in scanned source: {exc}", err=True)
        raise SystemExit(1) from exc

    click.echo(f"fit_006: PASS (kernel {kernel.word_count}/400 words)")
    if violations:
        click.echo(f"violations: {len(violations)}")
        for violation in violations:
            click.echo(f"  {violation.render()}")
        raise SystemExit(3)
    click.echo("fit_002: PASS (no illegal except handlers or untyped defs)")
    click.echo("fit_004: PASS (no cross-layer runtime imports)")
    click.echo("violations: 0")
