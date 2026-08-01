"""Commit message convention validator for AFRP pre-commit hook.

Enforces Conventional Commits format with AFRP-specific type extensions.
Called by pre-commit with the commit-msg stage.

Allowed types:
  feat, fix, chore, docs, style, refactor, perf, test, build, ci,
  revert, security, governance, evidence
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Conventional commits pattern with AFRP-specific types
_TYPES = (
    "feat",
    "fix",
    "chore",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "revert",
    "security",
    "governance",
    "evidence",
)

# Pattern: type(optional-scope)!: description
# Example: feat(L2-MAC): add DSmT agent
# Example: fix!: correct CIO-04 schema
_PATTERN = re.compile(r"^(" + "|".join(_TYPES) + r")(\([a-zA-Z0-9_\-./]+\))?(!)?: .{1,100}$")

# Lines to skip (merge commits, revert commits, etc.)
_SKIP_PATTERNS = (
    re.compile(r"^Merge (branch|pull request|remote-tracking)"),
    re.compile(r"^Revert \""),
    re.compile(r"^Initial commit"),
    re.compile(r"^Co-authored-by:"),
)


def _read_commit_msg(path: Path) -> str:
    """Read commit message, stripping comments."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    return "\n".join(lines).strip()


def main() -> int:
    """Validate commit message. Returns 0 on success, 1 on failure."""
    # Pre-commit passes the commit message file as the first argument
    # when stage is commit-msg. When called without args (e.g. manually),
    # read from .git/COMMIT_EDITMSG.
    if len(sys.argv) > 1:
        msg_file = Path(sys.argv[1])
    else:
        msg_file = Path(".git") / "COMMIT_EDITMSG"

    if not msg_file.exists():
        print("commit-msg: no commit message file found, skipping", file=sys.stderr)
        return 0

    msg = _read_commit_msg(msg_file)
    if not msg:
        print("commit-msg: empty commit message", file=sys.stderr)
        return 1

    subject = msg.splitlines()[0]

    # Allow special commit patterns
    for skip in _SKIP_PATTERNS:
        if skip.match(subject):
            return 0

    if _PATTERN.match(subject):
        return 0

    print(
        f"commit-msg: FAIL — subject does not follow Conventional Commits format:\n"
        f"  got:      {subject!r}\n"
        f"  expected: <type>(<scope>): <description>\n"
        f"  types:    {', '.join(_TYPES)}\n"
        f"  example:  feat(L2-MAC): add DSmT macro agent fusion\n",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
