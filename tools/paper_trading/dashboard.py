"""Dashboard output renderers (JSON/Markdown/HTML) for operational review."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DashboardArtifacts:
    json_path: str
    markdown_path: str
    html_path: str


def render_dashboard(
    snapshot: dict[str, Any], performance: dict[str, Any], alerts: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "snapshot": snapshot,
        "performance": performance,
        "risk_alerts": alerts,
        "status": "degraded" if alerts else "healthy",
    }


def write_dashboard(output_dir: Path, payload: dict[str, Any]) -> DashboardArtifacts:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "dashboard.json"
    markdown_path = output_dir / "dashboard.md"
    html_path = output_dir / "dashboard.html"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md_lines = [
        "# Phase D Operational Dashboard",
        "",
        f"- Status: **{payload['status']}**",
        f"- Snapshot timestamp: `{payload['snapshot'].get('timestamp', 'N/A')}`",
        f"- Equity: `{payload['snapshot'].get('equity', 0.0):.2f}`",
        f"- Total return: `{payload['performance'].get('total_return', 0.0):.4f}`",
        "",
        "## Risk Alerts",
    ]
    if payload["risk_alerts"]:
        for alert in payload["risk_alerts"]:
            value = alert["value"]
            threshold = alert["threshold"]
            md_lines.append(
                f"- `{alert['code']}` {alert['message']} ({value:.4f} > {threshold:.4f})"
            )
    else:
        md_lines.append("- None")
    markdown_path.write_text("\n".join(md_lines), encoding="utf-8")

    html = (
        "<html><body><h1>Phase D Operational Dashboard</h1>"
        f"<p>Status: <strong>{payload['status']}</strong></p>"
        f"<p>Timestamp: {payload['snapshot'].get('timestamp', 'N/A')}</p>"
        f"<p>Equity: {payload['snapshot'].get('equity', 0.0):.2f}</p>"
        f"<p>Total Return: {payload['performance'].get('total_return', 0.0):.4f}</p>"
        "<h2>Risk Alerts</h2><ul>"
        + "".join(
            f"<li>{alert['code']}: {alert['message']}</li>" for alert in payload["risk_alerts"]
        )
        + "</ul></body></html>"
    )
    html_path.write_text(html, encoding="utf-8")
    return DashboardArtifacts(str(json_path), str(markdown_path), str(html_path))
