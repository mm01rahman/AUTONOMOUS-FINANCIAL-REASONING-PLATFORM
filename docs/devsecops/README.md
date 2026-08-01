# AFRP DevSecOps Platform

This directory documents the Engineering Automation platform for AFRP.

## Contents

| Document | Purpose |
|----------|---------|
| [CI_CD.md](CI_CD.md) | CI/CD workflows, gates, and configuration |
| [RELEASE_AUTOMATION.md](RELEASE_AUTOMATION.md) | Release process and automation |
| [DEVELOPER_ONBOARDING.md](DEVELOPER_ONBOARDING.md) | Developer environment setup |

## Workflows at a glance

| Workflow | File | Trigger |
|----------|------|---------|
| Quality gates | `.github/workflows/quality.yml` | PR, push to main |
| Security automation | `.github/workflows/security.yml` | PR, push, weekly |
| Protocol validation | `.github/workflows/proto.yml` | PR/push on proto changes |
| Release automation | `.github/workflows/release.yml` | Version tags |
| Scheduled maintenance | `.github/workflows/maintenance.yml` | Weekly Sunday 02:00 UTC |

## Quality gate chain

```
PR opened
    │
    ├─→ lint (ruff check + format)
    ├─→ typecheck (mypy --strict)
    ├─→ test (pytest + coverage ≥80%)
    ├─→ protocol (proto_gate)
    ├─→ architecture (baseline_gate + ops_gate + system_gate)
    └─→ eos (afrp boot/plan/validate/health --assert-full)
             │
             ↓
    All gates PASS → merge allowed
    Any gate FAIL  → merge blocked
```

## Security gate chain

```
PR opened / weekly schedule
    │
    ├─→ codeql (static analysis)
    ├─→ pip-audit (dependency CVEs)
    ├─→ bandit (SAST)
    └─→ trufflehog (secret scanning)
             │
             ↓
    All PASS → green
    HIGH finding → merge blocked
```

## Tools

| Tool | Location | Purpose |
|------|----------|---------|
| `tools/metrics.py` | `python -m tools.metrics` | Repository health metrics |
| `tools/traceability_gate.py` | `python -m tools.traceability_gate` | Traceability chain validation |
| `tools/evidence_archive.py` | `python -m tools.evidence_archive` | Evidence packaging for releases |
| `tools/commit_msg_hook.py` | Pre-commit | Commit message convention |
