# Contributing to AFRP

Thank you for contributing to the Autonomous Financial Reasoning Platform.
This guide explains how to set up your environment, make governed changes,
and get your code merged.

---

## Table of Contents

1. [Governance first](#governance-first)
2. [Development environment](#development-environment)
3. [Branching and workflow](#branching-and-workflow)
4. [Commit conventions](#commit-conventions)
5. [Quality gates](#quality-gates)
6. [Pull request process](#pull-request-process)
7. [Architecture rules](#architecture-rules)
8. [Evidence and traceability](#evidence-and-traceability)
9. [Security](#security)

---

## Governance first

AFRP operates under the **Engineering Governance Protocol (EGP-2.0)**.
Before writing code:

1. Review the [Architecture Baseline](02-architecture/) and [ADR-0001](02-architecture/).
2. Identify the [Capability Registry](03-engineering/CAPABILITY_REGISTRY.yaml) entry
   your change belongs to.
3. Identify the [Work Package](05-work-packages/) that governs your change.
4. Check the [Traceability Matrix](03-engineering/TRACEABILITY_MATRIX.yaml) for
   requirement coverage.

**Do not modify the Runtime** (Layer 1–6 implementations) unless directed by an
approved Work Package. The runtime is frozen.

---

## Development environment

### Prerequisites

- Python 3.11 or 3.12
- [uv](https://docs.astral.sh/uv/) (fast Python package manager)
- Git 2.40+
- (Optional) [buf](https://buf.build/docs/installation) for proto linting

### Setup

```bash
# Clone and enter the repository
git clone https://github.com/mm01rahman/AUTONOMOUS-FINANCIAL-REASONING-PLATFORM.git
cd AUTONOMOUS-FINANCIAL-REASONING-PLATFORM

# Install all dependencies (including dev)
uv sync --group dev

# Install pre-commit hooks
uv run pre-commit install --install-hooks

# Verify the installation
uv run afrp boot
uv run afrp validate
uv run afrp health
```

### Running quality gates locally

```bash
# Lint
uv run ruff check .
uv run ruff format --check .

# Type check
uv run mypy --strict tools 06-runtime 07-research tests

# Tests with coverage
uv run pytest tests --cov --cov-report=term -v

# Architecture gates
uv run python -m tools.baseline_gate
uv run python -m tools.ops_gate

# EOS gates
uv run afrp plan
uv run afrp validate
uv run afrp health --assert-full

# Traceability
uv run python -m tools.traceability_gate

# All metrics
uv run python -m tools.metrics --skip-checks
```

---

## Branching and workflow

| Branch | Purpose |
|--------|---------|
| `main` | Protected. No direct pushes. All changes via PR. |
| `feat/<capability>` | New capability work |
| `fix/<issue>` | Bug fixes |
| `chore/<topic>` | Maintenance, tooling |
| `security/<topic>` | Security fixes (may use private branch) |

### Workflow

```
main ──→ feat/your-feature ──→ PR ──→ CI gates ──→ review ──→ merge
```

---

## Commit conventions

AFRP uses [Conventional Commits](https://www.conventionalcommits.org/).
The pre-commit hook enforces this automatically.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
Co-authored-by: ...
```

### Types

| Type | Use |
|------|-----|
| `feat` | New capability or feature |
| `fix` | Bug fix |
| `chore` | Maintenance, tooling |
| `docs` | Documentation only |
| `test` | Tests only |
| `refactor` | Code restructure (no behavior change) |
| `perf` | Performance improvement |
| `ci` | CI/CD changes |
| `security` | Security fix |
| `governance` | Governance, registry, TVM updates |
| `evidence` | Evidence record generation |

### Examples

```
feat(L2-MAC): implement DSmT PCR5 macro agent fusion
fix(EOS-HEALTH): handle missing coverage.json gracefully
ci: add security workflow with CodeQL and pip-audit
governance(CAPABILITY_REGISTRY): mark L3-WRM as COMPLETE
evidence(WP-RT-1012): emit EXEC-012.yaml for L3-WRM
```

---

## Quality gates

**All quality gates must pass before a PR can merge.**

| Gate | Tool | Requirement |
|------|------|-------------|
| Formatting | `ruff format` | Zero violations |
| Linting | `ruff check` | Zero violations |
| Type safety | `mypy --strict` | Zero errors |
| Tests | `pytest` | All pass |
| Coverage | `pytest-cov` | ≥ 80% |
| Architecture | `baseline_gate` | PASS |
| Operations | `ops_gate` | PASS |
| System fitness | `system_gate` | PASS |
| EOS boot | `afrp boot` | PASS |
| EOS plan | `afrp plan` | PASS (acyclic DAG) |
| EOS validate | `afrp validate` | PASS |
| EOS health | `afrp health --assert-full` | PASS |

---

## Pull request process

1. Create your branch from `main`.
2. Make your changes following architecture rules.
3. Ensure all quality gates pass locally.
4. Push and open a PR using the [PR template](.github/PULL_REQUEST_TEMPLATE.md).
5. Fill in every section of the PR template.
6. CI will run all quality gates automatically.
7. Request review from the relevant capability owner.
8. Address all review comments.
9. Once approved and CI is green, the PR can be merged.

**PRs that fail any quality gate will not be merged.**

---

## Architecture rules

- **Do not modify** files in `00-governance/`, `01-vision/`, `02-architecture/`
  without ARB approval.
- **Do not break** the capability DAG (FIT-001: must remain acyclic).
- **Do not remove** existing requirements from the TVM.
- **Do not lower** test coverage below 80%.
- **Do not weaken** mypy strictness settings.
- **Do not bypass** the EOS fitness functions (FIT-001 through FIT-008).
- **Do not cross** layer boundaries without an approved ADR.

---

## Evidence and traceability

Every Work Package must produce an evidence record before it can be marked COMPLETE.

```bash
# Generate evidence for a work package
uv run afrp evidence --wp WP-IMP-XXXX

# Verify existing evidence
uv run afrp evidence --wp WP-IMP-XXXX --base-ref HEAD~1
```

Evidence records are automatically archived during releases.

---

## Security

- Never commit secrets, credentials, or API keys.
- The pre-commit hook includes `detect-private-key`.
- Run `pip-audit` before introducing new dependencies.
- Report vulnerabilities via [SECURITY.md](SECURITY.md).

For questions, open a [discussion](https://github.com/mm01rahman/AUTONOMOUS-FINANCIAL-REASONING-PLATFORM/discussions)
or file an [issue](https://github.com/mm01rahman/AUTONOMOUS-FINANCIAL-REASONING-PLATFORM/issues).
