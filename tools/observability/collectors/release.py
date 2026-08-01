"""Release metric collector.

Measures release count, tags, evidence archives, completion reports,
and release readiness from git history and repository structure.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, check=False, timeout=30
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)


@dataclass
class ReleaseMetrics:
    # Tags
    tag_count: int = 0
    latest_tag: str = ""
    version_tags: list[str] = field(default_factory=list)
    pre_release_tags: list[str] = field(default_factory=list)
    # Evidence
    evidence_archives: int = 0
    completion_reports: int = 0
    evidence_records: int = 0
    # Readiness
    readiness_score: float = 0.0
    readiness_blockers: list[str] = field(default_factory=list)
    # Release manifest
    has_release_manifest: bool = False
    release_manifest_status: str = "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tags": {
                "total": self.tag_count,
                "latest": self.latest_tag,
                "version_tags": self.version_tags[:20],
                "pre_release_count": len(self.pre_release_tags),
            },
            "evidence": {
                "archives": self.evidence_archives,
                "completion_reports": self.completion_reports,
                "evidence_records": self.evidence_records,
            },
            "readiness": {
                "score": self.readiness_score,
                "blockers": self.readiness_blockers,
            },
            "release_manifest": {
                "present": self.has_release_manifest,
                "status": self.release_manifest_status,
            },
        }


def collect_release(root: Path) -> ReleaseMetrics:
    """Collect release metrics from git and repository structure."""
    m = ReleaseMetrics()

    # ── Git tags ──────────────────────────────────────────────────────────
    rc, out = _run(["git", "tag", "--sort=-version:refname"], root)
    if rc == 0 and out:
        all_tags = [t.strip() for t in out.splitlines() if t.strip()]
        m.tag_count = len(all_tags)
        for tag in all_tags:
            if re.match(r"^v\d+\.\d+\.\d+", tag):
                if "-" in tag.split("v", 1)[-1]:
                    m.pre_release_tags.append(tag)
                else:
                    m.version_tags.append(tag)
        m.latest_tag = all_tags[0] if all_tags else ""

    # ── Release artifacts in repo ─────────────────────────────────────────
    release_dir = root / "10-release"
    if release_dir.exists():
        m.completion_reports = len(list(release_dir.glob("*COMPLETION_REPORT*.md")))
        # Evidence records in 10-release
        m.evidence_records = len(list(release_dir.glob("*EVIDENCE_RECORD*.yaml")))
        # Archived tarballs (if any were committed)
        m.evidence_archives = len(list(root.glob("evidence-archive-*.tar.gz")))

    # Also count all evidence records under 05-work-packages
    wp_dir = root / "05-work-packages"
    if wp_dir.exists():
        m.evidence_records += len(list(wp_dir.rglob("evidence/*.yaml")))

    # ── Release manifest ──────────────────────────────────────────────────
    manifest_file = root / "10-release" / "RELEASE_MANIFEST_v1.0.yaml"
    if manifest_file.exists():
        m.has_release_manifest = True
        try:
            mdata: dict[str, Any] = (
                yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
            )
            m.release_manifest_status = mdata.get("status", "PRESENT")
        except yaml.YAMLError:
            m.release_manifest_status = "PARSE_ERROR"

    # ── Readiness scoring ─────────────────────────────────────────────────
    score = 0.0
    max_score = 5.0
    if m.completion_reports >= 1:
        score += 1.0
    else:
        m.readiness_blockers.append("No completion reports in 10-release/")
    if m.evidence_records >= 1:
        score += 1.0
    else:
        m.readiness_blockers.append("No evidence records found")
    if m.has_release_manifest:
        score += 1.0
    else:
        m.readiness_blockers.append("No release manifest in 10-release/")
    if m.tag_count >= 1:
        score += 1.0
    # Check for workflow
    release_workflow = root / ".github" / "workflows" / "release.yml"
    if release_workflow.exists():
        score += 1.0
    else:
        m.readiness_blockers.append("No release.yml workflow")
    m.readiness_score = round(score / max_score * 100, 2)

    return m
