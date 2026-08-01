# Release Automation

## Overview

AFRP releases are triggered by pushing a version tag to `main`.
All release steps are automated via `.github/workflows/release.yml`.

---

## Release naming convention

| Format | Example | Type |
|--------|---------|------|
| `vMAJOR.MINOR.PATCH` | `v2.0.0` | Stable release |
| `vMAJOR.MINOR.PATCH-label` | `v2.0.0-layer3` | Pre-release / milestone |

---

## Release process

### Step 1: Prepare the release

```bash
# Ensure main is clean and all gates pass
git checkout main
git pull origin main
uv run pytest tests --cov --cov-fail-under=80 -q
uv run afrp health --assert-full
uv run python -m tools.traceability_gate
```

### Step 2: Update version and changelog

```bash
# Update version in pyproject.toml
# Update CHANGELOG.md with release notes
# Commit with:
git commit -am "chore: prepare release v2.1.0"
git push origin main
```

### Step 3: Tag the release

```bash
git tag v2.1.0 -a -m "AFRP v2.1.0 — <milestone name>"
git push origin v2.1.0
```

This triggers `release.yml` automatically.

---

## Automated release pipeline

```
tag pushed
    │
    ├─→ [validate] Full quality gates (all CI checks repeated)
    │       ├─ ruff, mypy --strict
    │       ├─ pytest --cov-fail-under=80
    │       ├─ architecture gates
    │       ├─ EOS gates
    │       └─ traceability_gate
    │
    ├─→ [build] Python wheel and sdist
    │       └─ uv build → dist/*.whl, dist/*.tar.gz
    │
    ├─→ [archive-evidence] Package evidence
    │       └─ evidence_archive.py → evidence-archive-<tag>.tar.gz
    │
    ├─→ [release-notes] Generate release notes
    │       └─ git log, quality status, evidence summary
    │
    └─→ [publish] GitHub Release
            ├─ Wheel and sdist
            ├─ Evidence archive
            └─ Metrics report (metrics.json)
```

---

## Release artifacts

| Artifact | Contents |
|----------|---------|
| `*.whl` | Python wheel for installation |
| `*.tar.gz` (sdist) | Source distribution |
| `evidence-archive-<tag>.tar.gz` | All evidence records + completion reports |
| `metrics.json` | Repository health metrics at release time |

---

## Evidence archive contents

The evidence archive (`evidence-archive-<tag>.tar.gz`) contains:

```
evidence-archive-<tag>/
├── ARCHIVE_MANIFEST.yaml          ← Index of all included files
├── 05-work-packages/
│   └── */evidence/*.yaml          ← All work package evidence records
├── 10-release/
│   ├── *_COMPLETION_REPORT*.md    ← Completion reports
│   └── *_EVIDENCE_RECORD*.yaml    ← Evidence records
├── 03-engineering/
│   └── REPOSITORY_HEALTH.yaml     ← Health snapshot
└── coverage.json                  ← Coverage report
```

---

## Pre-release vs stable

Tags containing a hyphen (e.g. `v2.0.0-layer3`) are automatically published
as **pre-releases** on GitHub. Tags without a hyphen are **stable releases**.

---

## Manual release trigger

For emergency releases or re-runs:

```
GitHub Actions → release.yml → Run workflow
Input: tag = v2.1.0
```
