"""Dashboard generators for the AFRP observability platform.

Generates four output formats:
  - GitHub Actions Step Summary (Markdown via GITHUB_STEP_SUMMARY)
  - Standalone Markdown reports
  - Self-contained HTML dashboard
  - JSON export (handled by snapshot.to_dict())
"""

from __future__ import annotations

import html
import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.observability.scoring import HealthScore
    from tools.observability.snapshot import MetricsSnapshot

# ── Status helpers ─────────────────────────────────────────────────────────


def _status_icon(status: str) -> str:
    return {
        "PASS": "✅",
        "FAIL": "❌",
        "SKIPPED": "⏭️",
        "UNKNOWN": "❓",
        "CONFIGURED": "✅",
        "NOT_CONFIGURED": "⚠️",
        "UNAVAILABLE": "⚠️",
        "PARTIAL": "🟡",
    }.get(status.upper(), "❓")


def _pct_bar(pct: float, width: int = 20) -> str:
    """ASCII progress bar."""
    filled = int(pct / 100 * width)
    return "[" + "█" * filled + "░" * (width - filled) + f"] {pct:.1f}%"


# ── Markdown report ────────────────────────────────────────────────────────


def render_markdown(snap: MetricsSnapshot, score: HealthScore) -> str:
    """Render a comprehensive Markdown report from a MetricsSnapshot."""
    lines: list[str] = []
    a = lines.append

    a("# AFRP Repository Dashboard")
    a("")
    a(f"**Generated:** {snap.generated_at}")
    a(f"**Repository:** `{snap.repository_name}`")
    a(f"**Branch:** `{snap.git.current_branch}`")
    a("")

    # ── Health Score ──────────────────────────────────────────────────────
    a(f"## {score.grade.emoji} Repository Health: {score.grade.value} ({score.pct:.1f}%)")
    a("")
    a("| Dimension | Score | Weight | Contribution |")
    a("|-----------|-------|--------|-------------|")
    for d in score.dimensions:
        bar = _pct_bar(d.score * 100, 10)
        a(
            f"| {d.name} | {bar} | {d.weight:.0%} | "
            f"{d.weighted:.3f} |"
        )
    a("")

    # ── Repository Progress ───────────────────────────────────────────────
    repo = snap.repository
    a("## 📊 Repository Progress")
    a("")
    a("| Metric | Value |")
    a("|--------|-------|")
    a(f"| Total Capabilities | {repo.total} |")
    a(f"| Complete | {repo.complete} ({repo.completion_pct:.1f}%) |")
    a(f"| Available | {repo.available} |")
    a(f"| Locked | {repo.locked} |")
    a(f"| EOS Progress | {repo.eos_complete}/{repo.eos_total} ({repo.eos_completion_pct:.1f}%) |")
    a(
        f"| Runtime Progress | {repo.runtime_complete}/{repo.runtime_total} "
        f"({repo.runtime_completion_pct:.1f}%) |"
    )
    a("")
    a(f"{_pct_bar(repo.completion_pct)}")
    a("")

    # Layer breakdown
    if repo.layers:
        a("### By Layer")
        a("")
        a("| Layer | Complete | Total |")
        a("|-------|----------|-------|")
        for layer, stats in sorted(repo.layers.items()):
            a(f"| {layer} | {stats['complete']} | {stats['total']} |")
        a("")

    # ── Work Packages ─────────────────────────────────────────────────────
    wp = snap.work_packages
    a("## 📦 Work Package Burn-Down")
    a("")
    a("| Status | Count |")
    a("|--------|-------|")
    a(f"| ✅ Completed | {wp.completed} |")
    a(f"| 🔄 In Progress | {wp.in_progress} |")
    a(f"| 🚫 Blocked | {wp.blocked} |")
    a(f"| ⏳ Remaining | {wp.remaining} |")
    a(f"| **Total** | **{wp.total}** |")
    a("")
    a(f"**Burn:** {_pct_bar(wp.burn_pct)}")
    a("")

    # ── Quality ───────────────────────────────────────────────────────────
    q = snap.quality
    a("## 🔬 Code Quality")
    a("")
    a("| Gate | Status | Detail |")
    a("|------|--------|--------|")
    a(
        f"| Ruff (lint) | {_status_icon(q.ruff.status)} {q.ruff.status} "
        f"| {q.ruff.violations} violations |"
    )
    a(
        f"| Mypy (strict) | {_status_icon(q.mypy.status)} {q.mypy.status} | "
        f"{q.mypy.errors} errors, {q.mypy.files_checked} files |"
    )
    a(
        f"| Tests | {_status_icon(q.tests.status)} {q.tests.status} | "
        f"{q.tests.passed}/{q.tests.collected} passed ({q.tests.pass_rate:.1f}%) |"
    )
    a(
        f"| Coverage | {'✅' if q.coverage.line_pct >= 80 else '⚠️'} | "
        f"{q.coverage.line_pct:.1f}% lines, {q.coverage.branch_pct:.1f}% branches |"
    )
    a("")

    # ── Architecture ─────────────────────────────────────────────────────
    arch = snap.architecture
    a("## 🏗️ Architecture Health")
    a("")
    a("| Check | Status |")
    a("|-------|--------|")
    a(f"| DAG Acyclic (FIT-001) | {'✅ PASS' if arch.dag_acyclic else '❌ FAIL'} |")
    a(f"| Layer Violations | {arch.layer_violations} |")
    a(f"| Proto Compatible | {'✅ PASS' if arch.proto_compatible else '❌ FAIL'} |")
    a(f"| Fitness PASS | {arch.fit_pass} |")
    a(f"| Fitness FAIL | {arch.fit_fail} |")
    a("")
    if arch.fitness_functions:
        a("### Fitness Functions")
        a("")
        a("| ID | Status |")
        a("|----|--------|")
        for ff in arch.fitness_functions:
            a(f"| {ff.id} | {_status_icon(ff.status)} {ff.status} |")
        a("")

    # ── Governance ────────────────────────────────────────────────────────
    gov = snap.governance
    a("## 📋 Governance Health")
    a("")
    a("| Metric | Value |")
    a("|--------|-------|")
    a(
        f"| WPS Complete | {gov.wps_completed}/{gov.wps_total} "
        f"({gov.wps_completion_pct:.1f}%) |"
    )
    a(f"| Evidence Coverage | {gov.wps_with_evidence}/{gov.wps_completed} WPs have evidence |")
    a(f"| ERS Approved | {gov.ers_approved}/{gov.ers_total} |")
    a(
        f"| TVM Coverage | {gov.tvm_requirements_implemented}/{gov.tvm_requirements_total} "
        f"({gov.tvm_coverage_pct:.1f}%) |"
    )
    a(f"| ADRs | {gov.adr_total} total, {gov.adr_open} open |")
    a(f"| Completion Reports | {gov.completion_reports} |")
    a("")

    # Req type breakdown
    if gov.req_by_type:
        a("### Requirements by Type")
        a("")
        a("| Type | Count |")
        a("|------|-------|")
        for rtype, count in sorted(gov.req_by_type.items()):
            a(f"| {rtype} | {count} |")
        a("")

    # ── Security ──────────────────────────────────────────────────────────
    sec = snap.security
    a("## 🔒 Security Status")
    a("")
    a("| Tool | Status | Detail |")
    a("|------|--------|--------|")
    a(
        f"| Bandit (SAST) | {_status_icon(sec.bandit.status)} {sec.bandit.status} | "
        f"HIGH: {sec.bandit.high_severity}, MED: {sec.bandit.medium_severity} |"
    )
    a(
        f"| pip-audit | {_status_icon(sec.dependencies.status)} {sec.dependencies.status} | "
        f"{sec.dependencies.total_vulnerabilities} CVEs |"
    )
    a(f"| CodeQL | {_status_icon(sec.codeql_status)} {sec.codeql_status} | |")
    a(f"| Secret Scan | {_status_icon(sec.secret_scan_status)} {sec.secret_scan_status} | |")
    a("")

    # ── Release ───────────────────────────────────────────────────────────
    rel = snap.release
    a("## 🚀 Release Status")
    a("")
    a("| Metric | Value |")
    a("|--------|-------|")
    a(f"| Latest Tag | `{rel.latest_tag or 'none'}` |")
    a(f"| Total Tags | {rel.tag_count} |")
    a(f"| Completion Reports | {rel.completion_reports} |")
    a(f"| Evidence Records | {rel.evidence_records} |")
    a(f"| Release Manifest | {'✅' if rel.has_release_manifest else '⚠️'} |")
    a(f"| Release Readiness | {_pct_bar(rel.readiness_score, 10)} |")
    a("")
    if rel.readiness_blockers:
        a("**Blockers:**")
        for b in rel.readiness_blockers:
            a(f"- ⚠️ {b}")
        a("")

    # ── Git ───────────────────────────────────────────────────────────────
    git = snap.git
    a("## 📝 Git Metrics")
    a("")
    a("| Metric | Value |")
    a("|--------|-------|")
    a(f"| Total Commits | {git.total_commits} |")
    a(f"| Commits (7d) | {git.commits_last_7d} |")
    a(f"| Commits (30d) | {git.commits_last_30d} |")
    a(f"| Contributors | {git.contributors} |")
    a(f"| Tracked Files | {git.tracked_files} |")
    a(f"| Python Files | {git.python_files} |")
    cc_total = git.conventional_commits + git.non_conventional_commits
    a(
        f"| Conventional Commits | {git.conventional_commits}/{cc_total} "
        f"({git.convention_compliance_pct:.1f}%) |"
    )
    a(f"| Last Commit | `{git.last_commit_sha[:8]}` {git.last_commit_date[:10]} |")
    a("")

    a("---")
    a("*Generated by AFRP Engineering Observability Platform*")

    return "\n".join(lines)


# ── GitHub Actions Summary ─────────────────────────────────────────────────


def render_github_summary(snap: MetricsSnapshot, score: HealthScore) -> str:
    """Render a concise GitHub Actions Step Summary."""
    lines: list[str] = []
    a = lines.append

    a(f"## {score.grade.emoji} AFRP Repository Health: **{score.grade.value}** ({score.pct:.1f}%)")
    a("")

    repo = snap.repository
    q = snap.quality
    arch = snap.architecture
    gov = snap.governance
    sec = snap.security
    rel = snap.release

    a("| Category | Status | Key Metric |")
    a("|----------|--------|------------|")
    a(
        f"| Progress | {_pct_bar(repo.completion_pct, 10)} | "
        f"{repo.complete}/{repo.total} capabilities |"
    )
    a(
        f"| Lint | {_status_icon(q.ruff.status)} {q.ruff.status} | "
        f"{q.ruff.violations} violations |"
    )
    a(
        f"| Types | {_status_icon(q.mypy.status)} {q.mypy.status} | "
        f"{q.mypy.errors} errors |"
    )
    a(
        f"| Tests | {_status_icon(q.tests.status)} {q.tests.status} | "
        f"{q.tests.passed} passed |"
    )
    a(
        f"| Coverage | {'✅' if q.coverage.line_pct >= 80 else '⚠️'} | "
        f"{q.coverage.line_pct:.1f}% |"
    )
    a(
        f"| Architecture | {'✅' if arch.fit_fail == 0 else '❌'} | "
        f"{arch.fit_pass}/{arch.fit_pass + arch.fit_fail} FIT PASS |"
    )
    a(
        f"| Traceability | {'✅' if gov.tvm_coverage_pct >= 100 else '⚠️'} | "
        f"{gov.tvm_requirements_implemented}/{gov.tvm_requirements_total} reqs |"
    )
    a(
        f"| Security | {_status_icon(sec.overall_status)} {sec.overall_status} | "
        f"bandit={sec.bandit.status} |"
    )
    a(
        f"| Release | {_pct_bar(rel.readiness_score, 10)} | "
        f"tag={rel.latest_tag or 'none'} |"
    )
    a("")
    a(f"**Branch:** `{snap.git.current_branch}` | "
      f"**Commits:** {snap.git.total_commits} | "
      f"**Last:** {snap.git.last_commit_date[:10]}")

    return "\n".join(lines)


def publish_to_github_summary(content: str) -> None:
    """Write content to GITHUB_STEP_SUMMARY if running in GitHub Actions."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(content + "\n")


# ── HTML dashboard ─────────────────────────────────────────────────────────


def render_html(snap: MetricsSnapshot, score: HealthScore) -> str:
    """Render a self-contained HTML dashboard."""
    data = snap.to_dict()
    data_json = html.escape(json.dumps(data, indent=2))
    repo = snap.repository
    q = snap.quality
    gov = snap.governance
    sec = snap.security
    rel = snap.release
    git = snap.git
    arch = snap.architecture

    grade_color = {
        "A+": "#22c55e",
        "A": "#4ade80",
        "B": "#facc15",
        "C": "#fb923c",
        "D": "#ef4444",
    }.get(score.grade.value, "#94a3b8")

    def metric_card(title: str, value: str, sub: str = "") -> str:
        return f"""
        <div class="card">
          <div class="card-title">{html.escape(title)}</div>
          <div class="card-value">{html.escape(value)}</div>
          {"<div class='card-sub'>" + html.escape(sub) + "</div>" if sub else ""}
        </div>"""

    def status_badge(status: str) -> str:
        colors = {
            "PASS": "#22c55e",
            "FAIL": "#ef4444",
            "SKIPPED": "#94a3b8",
            "UNKNOWN": "#94a3b8",
            "CONFIGURED": "#22c55e",
            "NOT_CONFIGURED": "#f59e0b",
            "UNAVAILABLE": "#f59e0b",
        }
        color = colors.get(status.upper(), "#94a3b8")
        return f'<span class="badge" style="background:{color}">{html.escape(status)}</span>'

    cards_html = "".join(
        [
            metric_card(
                "Health Score",
                f"{score.grade.value} ({score.pct:.1f}%)",
                score.grade.emoji,
            ),
            metric_card(
                "Capabilities",
                f"{repo.complete}/{repo.total}",
                f"{repo.completion_pct:.1f}% complete",
            ),
            metric_card(
                "Coverage",
                f"{q.coverage.line_pct:.1f}%",
                "line coverage",
            ),
            metric_card(
                "Tests",
                f"{q.tests.passed}",
                f"{q.tests.status}",
            ),
            metric_card(
                "TVM Coverage",
                f"{gov.tvm_requirements_implemented}/{gov.tvm_requirements_total}",
                f"{gov.tvm_coverage_pct:.1f}%",
            ),
            metric_card(
                "Architecture",
                f"{arch.fit_pass} FIT PASS",
                f"{arch.fit_fail} FAIL",
            ),
            metric_card("Security", sec.overall_status, f"bandit={sec.bandit.status}"),
            metric_card(
                "Release",
                rel.latest_tag or "no tags",
                f"{rel.readiness_score:.0f}% ready",
            ),
            metric_card("Commits", str(git.total_commits), f"{git.commits_last_7d} last 7d"),
        ]
    )

    dim_rows = "".join(
        f"<tr><td>{html.escape(d.name)}</td>"
        f"<td>{d.score*100:.1f}%</td>"
        f"<td>{d.weight:.0%}</td>"
        f"<td>{d.weighted:.3f}</td>"
        f"</tr>"
        for d in score.dimensions
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AFRP Engineering Dashboard</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0f172a; color: #e2e8f0; padding: 24px; }}
    h1 {{ font-size: 1.8rem; margin-bottom: 4px; }}
    h2 {{ font-size: 1.2rem; margin: 24px 0 12px; color: #94a3b8; text-transform: uppercase;
          letter-spacing: 0.05em; }}
    .subtitle {{ color: #94a3b8; font-size: 0.9rem; margin-bottom: 24px; }}
    .grade {{ font-size: 3rem; font-weight: 700; color: {grade_color}; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
              gap: 16px; margin-bottom: 32px; }}
    .card {{ background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }}
    .card-title {{ font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;
                   letter-spacing: 0.05em; margin-bottom: 8px; }}
    .card-value {{ font-size: 1.6rem; font-weight: 600; }}
    .card-sub {{ font-size: 0.8rem; color: #64748b; margin-top: 4px; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px;
              font-size: 0.75rem; font-weight: 600; color: white; }}
    table {{ width: 100%; border-collapse: collapse; background: #1e293b;
             border-radius: 8px; overflow: hidden; }}
    th {{ background: #334155; padding: 10px 16px; text-align: left; font-size: 0.85rem; }}
    td {{ padding: 10px 16px; border-top: 1px solid #334155; font-size: 0.9rem; }}
    tr:hover td {{ background: #263248; }}
    .json-block {{ background: #1e293b; border-radius: 8px; padding: 16px; overflow: auto;
                   font-family: monospace; font-size: 0.8rem; max-height: 400px;
                   color: #94a3b8; border: 1px solid #334155; }}
    footer {{ margin-top: 32px; color: #475569; font-size: 0.8rem; text-align: center; }}
  </style>
</head>
<body>
  <h1>AFRP Engineering Dashboard</h1>
  <div class="subtitle">
    <span class="grade">{html.escape(score.grade.value)}</span>
    &nbsp; {score.pct:.1f}% health score &nbsp;|&nbsp;
    {html.escape(snap.generated_at[:19])} UTC &nbsp;|&nbsp;
    branch: {html.escape(git.current_branch)}
  </div>

  <div class="cards">{cards_html}</div>

  <h2>Health Score Dimensions</h2>
  <table>
    <thead>
      <tr><th>Dimension</th><th>Score</th><th>Weight</th><th>Contribution</th></tr>
    </thead>
    <tbody>{dim_rows}</tbody>
  </table>

  <h2>Raw Metrics (JSON)</h2>
  <pre class="json-block">{data_json}</pre>

  <footer>Generated by AFRP Engineering Observability Platform &mdash; WP-IMP-0035</footer>
</body>
</html>"""
