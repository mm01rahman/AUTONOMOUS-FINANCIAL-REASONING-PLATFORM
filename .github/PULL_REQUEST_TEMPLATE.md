## Why

<!-- Explain the requirement, user need, or governed capability this addresses. -->

## Approach

<!-- Summarize the design and how it preserves canonical architecture. -->

## Governance

| Field | Value |
|-------|-------|
| Work Package | WP-xxx-xxxx |
| Requirements / TVM rows | FR-xxx, NFR-xxx |
| Capability | CAP-ID from CAPABILITY_REGISTRY.yaml |
| ADR required | Yes / No |
| Baseline impact | None / Patch / Minor / Major |
| Protected files changed | Yes / No (list them if yes) |
| Runtime modified | Yes / No (must be No unless ARB approved) |

## Quality gate checklist

- [ ] `ruff check .` — zero violations
- [ ] `ruff format --check .` — no formatting changes
- [ ] `mypy --strict` — zero type errors
- [ ] `pytest --cov --cov-fail-under=80` — all tests pass, coverage ≥ 80%
- [ ] `python -m tools.baseline_gate` — PASS
- [ ] `python -m tools.ops_gate` — PASS
- [ ] `python -m tools.proto_gate` — PASS (if proto changed)
- [ ] `afrp boot` — PASS
- [ ] `afrp plan` — PASS (DAG acyclic)
- [ ] `afrp validate` — PASS
- [ ] `afrp health --assert-full` — PASS
- [ ] `python -m tools.traceability_gate` — PASS

## Architecture Review

- [ ] No layer boundary violations introduced
- [ ] No import cycles introduced (FIT-002)
- [ ] Capability DAG remains acyclic (FIT-001)
- [ ] TVM updated if new requirements are introduced
- [ ] CAPABILITY_REGISTRY.yaml updated if capability status changed
- [ ] No unresolved architecture violation

## Evidence

- [ ] Evidence record generated (`afrp evidence --wp WP-xxx`)
  or N/A (no Work Package boundary changes)
- [ ] Work Package status updated in CAPABILITY_REGISTRY.yaml

## Risks and Rollback

<!-- State compatibility, operational, safety, and rollback considerations.
     For runtime changes: how is the previous behavior preserved?
     For schema changes: is the change backward-compatible? -->
