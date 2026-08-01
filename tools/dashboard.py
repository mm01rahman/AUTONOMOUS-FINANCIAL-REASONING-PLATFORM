"""AFRP Engineering Dashboard — main CLI entry point.

Generates the complete Engineering Metrics and Repository Observability
dashboard in all supported formats.

Usage::

    uv run python -m tools.dashboard
    uv run python -m tools.dashboard --format markdown --output dashboard.md
    uv run python -m tools.dashboard --format html --output dashboard.html
    uv run python -m tools.dashboard --format json --output metrics.json
    uv run python -m tools.dashboard --format all --output-dir reports/
    uv run python -m tools.dashboard --fast       # skip slow subprocess checks
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

_ROOT = Path(__file__).parent.parent


@click.command()
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["markdown", "html", "json", "summary", "all"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output file (used for single-format modes).",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("reports"),
    show_default=True,
    help="Output directory for --format=all.",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Repository root.",
)
@click.option(
    "--fast",
    is_flag=True,
    default=False,
    help="Skip slow subprocess checks (ruff/mypy/pytest/architecture gates).",
)
@click.option(
    "--threshold",
    type=float,
    default=0.0,
    show_default=True,
    help="Minimum health score (0.0–1.0). Fail if score falls below this.",
)
@click.option(
    "--github-summary",
    is_flag=True,
    default=False,
    help="Write to GITHUB_STEP_SUMMARY if set.",
)
def main(
    fmt: str,
    output: Path | None,
    output_dir: Path,
    repo_root: Path,
    fast: bool,
    threshold: float,
    github_summary: bool,
) -> None:
    """Generate AFRP Engineering Dashboard and Repository Metrics."""
    from tools.observability.dashboard import (
        publish_to_github_summary,
        render_github_summary,
        render_html,
        render_markdown,
    )
    from tools.observability.scoring import compute_health_score
    from tools.observability.snapshot import collect_all

    root = repo_root.resolve()

    click.echo("🔍 Collecting repository metrics...", err=True)
    snap = collect_all(
        root,
        skip_quality_checks=fast,
        skip_architecture_checks=fast,
    )

    click.echo("📐 Computing health score...", err=True)
    score = compute_health_score(snap)

    click.echo(
        f"✅ Health: {score.grade.emoji} {score.grade.value} ({score.pct:.1f}%)", err=True
    )

    # ── Generate outputs ──────────────────────────────────────────────────
    fmt_lower = fmt.lower()

    if fmt_lower in ("markdown", "all"):
        md = render_markdown(snap, score)
        if fmt_lower == "markdown" and output:
            output.write_text(md, encoding="utf-8")
            click.echo(f"📄 Markdown: {output}")
        elif fmt_lower == "all":
            out_md = output_dir / "dashboard.md"
            output_dir.mkdir(parents=True, exist_ok=True)
            out_md.write_text(md, encoding="utf-8")
            click.echo(f"📄 Markdown: {out_md}")
        else:
            click.echo(md)

    if fmt_lower in ("html", "all"):
        htm = render_html(snap, score)
        if fmt_lower == "html" and output:
            output.write_text(htm, encoding="utf-8")
            click.echo(f"🌐 HTML: {output}")
        elif fmt_lower == "all":
            out_html = output_dir / "dashboard.html"
            output_dir.mkdir(parents=True, exist_ok=True)
            out_html.write_text(htm, encoding="utf-8")
            click.echo(f"🌐 HTML: {out_html}")
        else:
            click.echo(htm)

    if fmt_lower in ("json", "all"):
        data = snap.to_dict()
        data["health"] = score.to_dict()
        js = json.dumps(data, indent=2)
        if fmt_lower == "json" and output:
            output.write_text(js, encoding="utf-8")
            click.echo(f"📊 JSON: {output}")
        elif fmt_lower == "all":
            out_json = output_dir / "metrics.json"
            output_dir.mkdir(parents=True, exist_ok=True)
            out_json.write_text(js, encoding="utf-8")
            click.echo(f"📊 JSON: {out_json}")
        else:
            click.echo(js)

    if fmt_lower in ("summary", "all"):
        summary = render_github_summary(snap, score)
        if fmt_lower == "summary" and output:
            output.write_text(summary, encoding="utf-8")
            click.echo(f"📋 Summary: {output}")
        elif fmt_lower == "all":
            out_sum = output_dir / "summary.md"
            output_dir.mkdir(parents=True, exist_ok=True)
            out_sum.write_text(summary, encoding="utf-8")
            click.echo(f"📋 Summary: {out_sum}")
        else:
            click.echo(summary)

    if github_summary:
        summary_md = render_github_summary(snap, score)
        publish_to_github_summary(summary_md)
        click.echo("📢 GitHub Actions summary updated.", err=True)

    # ── Threshold check ───────────────────────────────────────────────────
    if threshold > 0 and score.total < threshold:
        click.echo(
            f"\n❌ Health score {score.pct:.1f}% below threshold {threshold*100:.1f}%",
            err=True,
        )
        sys.exit(1)

    click.echo("\n✅ Dashboard generation complete.", err=True)


if __name__ == "__main__":
    sys.exit(main())
