"""CLI for AFRP Phase B verification framework."""

from __future__ import annotations

from pathlib import Path

import click

from tools.verification.dashboard import (
    build_bundle,
    publish_github_summary,
    render_html,
    render_json,
    render_markdown,
)
from tools.verification.math_checks import verify_mathematics
from tools.verification.performance import benchmark_performance
from tools.verification.regression import run_regression_suite
from tools.verification.statistical import evaluate_statistics
from tools.verification.stress import run_stress_suite
from tools.verification.verifier import verify_runtime


@click.command()
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("09-validation/reports"),
    show_default=True,
)
@click.option("--github-summary", is_flag=True, default=False)
def main(output_dir: Path, github_summary: bool) -> None:
    """Run complete Phase B validation and emit JSON/Markdown/HTML reports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime = verify_runtime(output_dir / "runtime_verification.json")
    mathematics = verify_mathematics(output_dir / "mathematical_verification.json")
    stress = run_stress_suite(output_dir / "stress_report.json")
    performance = benchmark_performance(output_dir / "performance_report.json")
    statistics = evaluate_statistics(output_dir / "statistical_report.json")
    regression = run_regression_suite(output_dir / "regression_report.json")
    bundle = build_bundle(runtime, mathematics, stress, performance, statistics, regression)

    json_text = render_json(bundle)
    md_text = render_markdown(bundle)
    html_text = render_html(bundle)

    (output_dir / "validation_dashboard.json").write_text(json_text, encoding="utf-8")
    (output_dir / "validation_dashboard.md").write_text(md_text, encoding="utf-8")
    (output_dir / "validation_dashboard.html").write_text(html_text, encoding="utf-8")

    click.echo(md_text)
    if github_summary:
        publish_github_summary(md_text)

    if not regression.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
