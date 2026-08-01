# CI/CD Documentation

## Overview

AFRP CI/CD is implemented entirely via GitHub Actions. Every pull request
must pass all quality gates before it can merge. This is enforced by branch
protection rules on `main`.

---

## Workflow: quality.yml

**Triggers:** Pull requests, pushes to `main`, manual dispatch.

**Jobs (run in parallel where possible):**

### `lint` — ruff check & format
- Runs `ruff check .` (linting)
- Runs `ruff format --check .` (formatting)
- Fails on any violation

### `typecheck` — mypy --strict
- Runs `mypy --strict` over all production and test code
- Fails on any type error
- Uses Python 3.11

### `test` — pytest with coverage
- Runs full test suite
- Enforces ≥ 80% line coverage
- Uploads `coverage.json` and `coverage.xml` as artifacts
- Retained for 30 days

### `protocol` — proto validation
- Runs `tools.proto_gate` (grpcio-tools compile validation)
- Validates all `.proto` files compile without error

### `architecture` — fitness gates
- Runs `tools.baseline_gate` (FIT-002, FIT-004, FIT-006)
- Runs `tools.ops_gate` (operations fitness)
- Runs `tools.system_gate` (FIT-008, deterministic replay)

### `eos` — EOS CLI gates
- Requires `test` job to pass first (needs coverage artifact)
- Runs `afrp boot`, `afrp plan`, `afrp validate`, `afrp health --assert-full`
- FIT-007: 100% requirement traceability required

### `quality` — Summary gate
- Aggregates all job results
- Reports failure if any job fails or is cancelled
- This is the required status check for branch protection

---

## Caching strategy

- **uv cache**: `astral-sh/setup-uv@v5` with `enable-cache: true`
- Cache key based on `uv.lock` hash (automatic)
- Dramatically reduces cold-start time

---

## Workflow: security.yml

**Triggers:** Pull requests to `main`, pushes to `main`, weekly Monday 06:00 UTC.

See [../SECURITY_AUTOMATION.md](../SECURITY_AUTOMATION.md) for full details.

---

## Workflow: proto.yml

**Triggers:** PRs/pushes that modify `proto/**` or `tools/proto_gate.py`.

- **buf lint**: Validates proto style (Google API guide compliance)
- **buf breaking**: Detects backward-incompatible proto changes against `main`
- **proto-compile**: Validates protos compile via grpcio-tools (W-001 waiver)

Breaking proto changes **block merges** on pull requests.

---

## Branch protection rules

Configure on `main`:

```
✅ Require status checks before merging
  Required checks:
    - All quality gates passed    (quality.yml / quality job)
    - All security gates passed   (security.yml / security-gate job)

✅ Require branches to be up to date before merging
✅ Require conversation resolution before merging
✅ Restrict who can push to matching branches
✅ Require signed commits (recommended)
```

---

## Artifact retention

| Artifact | Retention |
|----------|-----------|
| coverage-report | 30 days |
| pip-audit-report | 30 days |
| bandit-report | 30 days |
| dependency-reports | 90 days |
| health-report | 90 days |
| dist (release) | 90 days |
| evidence-archive | 365 days |
| release-notes | 365 days |
| pre-release-reports | 90 days |

---

## Adding new quality gates

1. Add the check as a new step in the appropriate job in `quality.yml`.
2. If it's an independent check, consider a new parallel job.
3. Add it to the `needs` list of the `quality` summary job.
4. Document it in this file.
5. Update the PR template checklist.
