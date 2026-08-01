"""Git metrics collector.

Measures commit history, branch info, and build success rate
from local git history without requiring network access.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, check=False, timeout=30
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)


@dataclass
class GitMetrics:
    # Commit stats
    total_commits: int = 0
    commits_last_7d: int = 0
    commits_last_30d: int = 0
    last_commit_sha: str = ""
    last_commit_date: str = ""
    last_commit_author: str = ""
    last_commit_message: str = ""
    # Branch info
    current_branch: str = ""
    # Contributors
    contributors: int = 0
    # Conventional commit compliance
    conventional_commits: int = 0
    non_conventional_commits: int = 0
    convention_compliance_pct: float = 0.0
    # Recent activity
    recent_feat_commits: int = 0
    recent_fix_commits: int = 0
    recent_ci_commits: int = 0
    # Files
    tracked_files: int = 0
    python_files: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "commits": {
                "total": self.total_commits,
                "last_7d": self.commits_last_7d,
                "last_30d": self.commits_last_30d,
                "last_sha": self.last_commit_sha[:8] if self.last_commit_sha else "",
                "last_date": self.last_commit_date,
                "last_author": self.last_commit_author,
                "last_message": self.last_commit_message[:80],
            },
            "branch": self.current_branch,
            "contributors": self.contributors,
            "conventional_commits": {
                "compliant": self.conventional_commits,
                "non_compliant": self.non_conventional_commits,
                "compliance_pct": self.convention_compliance_pct,
            },
            "activity": {
                "feat": self.recent_feat_commits,
                "fix": self.recent_fix_commits,
                "ci": self.recent_ci_commits,
            },
            "files": {
                "tracked": self.tracked_files,
                "python": self.python_files,
            },
        }


# Conventional commits pattern
_CC_PATTERN = re.compile(
    r"^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert|security|"
    r"governance|evidence)(\([^)]+\))?(!)?: .+"
)


def collect_git(root: Path) -> GitMetrics:
    """Collect git metrics from local history."""
    m = GitMetrics()

    # ── Current branch ────────────────────────────────────────────────────
    _, branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root)
    m.current_branch = branch.strip()

    # ── Total commits ──────────────────────────────────────────────────────
    _, total = _run(["git", "rev-list", "--count", "HEAD"], root)
    if total.strip().isdigit():
        m.total_commits = int(total.strip())

    # ── Last commit info ──────────────────────────────────────────────────
    _, last = _run(
        ["git", "log", "-1", "--format=%H|%ci|%an|%s"],
        root,
    )
    if last and "|" in last:
        parts = last.split("|", 3)
        if len(parts) == 4:
            m.last_commit_sha, m.last_commit_date, m.last_commit_author, m.last_commit_message = (
                parts[0].strip(),
                parts[1].strip(),
                parts[2].strip(),
                parts[3].strip(),
            )

    # ── Commits last 7 / 30 days ──────────────────────────────────────────
    _, c7 = _run(
        ["git", "rev-list", "--count", "--after=7 days ago", "HEAD"],
        root,
    )
    if c7.strip().isdigit():
        m.commits_last_7d = int(c7.strip())
    _, c30 = _run(
        ["git", "rev-list", "--count", "--after=30 days ago", "HEAD"],
        root,
    )
    if c30.strip().isdigit():
        m.commits_last_30d = int(c30.strip())

    # ── Contributors ──────────────────────────────────────────────────────
    _, contrib = _run(["git", "log", "--format=%ae"], root)
    if contrib:
        m.contributors = len(set(contrib.splitlines()))

    # ── Conventional commits analysis (last 100) ──────────────────────────
    _, log = _run(["git", "log", "--format=%s", "-100"], root)
    if log:
        subjects = [s.strip() for s in log.splitlines() if s.strip()]
        for subj in subjects:
            if _CC_PATTERN.match(subj):
                m.conventional_commits += 1
                # Count by type
                match = _CC_PATTERN.match(subj)
                if match:
                    t = match.group(1)
                    if t == "feat":
                        m.recent_feat_commits += 1
                    elif t == "fix":
                        m.recent_fix_commits += 1
                    elif t == "ci":
                        m.recent_ci_commits += 1
            else:
                m.non_conventional_commits += 1
        total_analyzed = len(subjects)
        if total_analyzed:
            m.convention_compliance_pct = round(
                m.conventional_commits / total_analyzed * 100, 2
            )

    # ── File count ────────────────────────────────────────────────────────
    _, file_list = _run(["git", "ls-files"], root)
    if file_list:
        files = [f.strip() for f in file_list.splitlines() if f.strip()]
        m.tracked_files = len(files)
        m.python_files = sum(1 for f in files if f.endswith(".py"))

    return m
