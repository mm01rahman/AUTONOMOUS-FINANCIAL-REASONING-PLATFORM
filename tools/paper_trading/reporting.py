"""Daily/weekly/monthly and run-level reporting for paper trading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReportArtifacts:
    daily_json: str
    weekly_json: str
    monthly_json: str
    daily_md: str
    weekly_md: str
    monthly_md: str
    runtime_json: str
    learning_json: str
    risk_json: str
    log_digest_json: str


def _write_period_markdown(path: Path, title: str, summary: dict[str, float]) -> None:
    body = "\n".join(
        [
            f"# {title}",
            "",
            f"- Periods: {summary.get('periods', 0):.0f}",
            f"- Avg Return: {summary.get('avg_return', 0.0):.6f}",
            f"- Best Return: {summary.get('best_return', 0.0):.6f}",
            f"- Worst Return: {summary.get('worst_return', 0.0):.6f}",
        ]
    )
    path.write_text(body, encoding="utf-8")


def _write_period_html(path: Path, title: str, summary: dict[str, float]) -> None:
    html = (
        f"<html><body><h1>{title}</h1>"
        f"<p>Periods: {summary.get('periods', 0):.0f}</p>"
        f"<p>Avg Return: {summary.get('avg_return', 0.0):.6f}</p>"
        f"<p>Best Return: {summary.get('best_return', 0.0):.6f}</p>"
        f"<p>Worst Return: {summary.get('worst_return', 0.0):.6f}</p>"
        "</body></html>"
    )
    path.write_text(html, encoding="utf-8")


def write_reports(
    output_dir: Path,
    period_summary: dict[str, dict[str, float]],
    performance: dict[str, Any],
    risk_alerts: list[dict[str, Any]],
    log_digest: dict[str, Any],
    runtime_health: dict[str, Any],
    learning_summary: dict[str, Any],
) -> ReportArtifacts:
    output_dir.mkdir(parents=True, exist_ok=True)

    daily_json = output_dir / "report_daily.json"
    weekly_json = output_dir / "report_weekly.json"
    monthly_json = output_dir / "report_monthly.json"
    daily_md = output_dir / "report_daily.md"
    weekly_md = output_dir / "report_weekly.md"
    monthly_md = output_dir / "report_monthly.md"
    daily_html = output_dir / "report_daily.html"
    weekly_html = output_dir / "report_weekly.html"
    monthly_html = output_dir / "report_monthly.html"
    runtime_json = output_dir / "runtime_health.json"
    learning_json = output_dir / "learning_summary.json"
    risk_json = output_dir / "risk_alerts.json"
    log_digest_json = output_dir / "decision_log_digest.json"

    daily_json.write_text(json.dumps(period_summary.get("daily", {}), indent=2), encoding="utf-8")
    weekly_json.write_text(json.dumps(period_summary.get("weekly", {}), indent=2), encoding="utf-8")
    monthly_json.write_text(
        json.dumps(period_summary.get("monthly", {}), indent=2), encoding="utf-8"
    )
    _write_period_markdown(daily_md, "Daily Paper Trading Report", period_summary.get("daily", {}))
    _write_period_markdown(
        weekly_md, "Weekly Paper Trading Report", period_summary.get("weekly", {})
    )
    _write_period_markdown(
        monthly_md, "Monthly Paper Trading Report", period_summary.get("monthly", {})
    )
    _write_period_html(daily_html, "Daily Paper Trading Report", period_summary.get("daily", {}))
    _write_period_html(weekly_html, "Weekly Paper Trading Report", period_summary.get("weekly", {}))
    _write_period_html(
        monthly_html, "Monthly Paper Trading Report", period_summary.get("monthly", {})
    )

    runtime_payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "runtime": runtime_health,
        "performance": performance,
    }
    runtime_json.write_text(json.dumps(runtime_payload, indent=2), encoding="utf-8")
    learning_json.write_text(json.dumps(learning_summary, indent=2), encoding="utf-8")
    risk_json.write_text(json.dumps(risk_alerts, indent=2), encoding="utf-8")
    log_digest_json.write_text(json.dumps(log_digest, indent=2), encoding="utf-8")

    return ReportArtifacts(
        daily_json=str(daily_json),
        weekly_json=str(weekly_json),
        monthly_json=str(monthly_json),
        daily_md=str(daily_md),
        weekly_md=str(weekly_md),
        monthly_md=str(monthly_md),
        runtime_json=str(runtime_json),
        learning_json=str(learning_json),
        risk_json=str(risk_json),
        log_digest_json=str(log_digest_json),
    )
