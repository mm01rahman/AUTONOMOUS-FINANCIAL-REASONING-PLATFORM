# Developer Onboarding Guide

Welcome to AFRP. This guide gets you from zero to a working development
environment that passes all quality gates.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11 or 3.12 | 3.13+ not yet supported |
| uv | latest | Install from https://docs.astral.sh/uv/ |
| Git | 2.40+ | Required for pre-commit hooks |
| buf (optional) | latest | For proto linting |

### Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

---

## First-time setup

```bash
# 1. Clone the repository
git clone https://github.com/mm01rahman/AUTONOMOUS-FINANCIAL-REASONING-PLATFORM.git
cd AUTONOMOUS-FINANCIAL-REASONING-PLATFORM

# 2. Install all dependencies
uv sync --group dev

# 3. Install pre-commit hooks
uv run pre-commit install --install-hooks

# 4. Verify the development environment
uv run afrp boot        # Should print: manifest: PASS, kernel: PASS
uv run afrp plan        # Should show DAG with all capabilities
uv run afrp validate    # Should print: FIT-002/004/006: PASS
uv run afrp health      # Should show traceability and coverage summary
```

---

## Running the full quality gate locally

```bash
# Exact commands that CI runs — run these before every PR
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict tools 06-runtime 07-research tests
uv run pytest tests --cov --cov-report=term --cov-fail-under=80 -v
uv run python -m tools.proto_gate
uv run python -m tools.baseline_gate
uv run python -m tools.ops_gate
AFRP_AUDIT_HMAC_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  uv run python -m tools.system_gate
uv run afrp boot
uv run afrp plan
uv run afrp validate
uv run afrp health --assert-full
uv run python -m tools.traceability_gate
```

Or use the convenience target (runs all gates sequentially):

```bash
uv run python -m tools.metrics --skip-checks   # Quick health overview
```

---

## Repository structure

```
AUTONOMOUS-FINANCIAL-REASONING-PLATFORM/
├── 00-governance/          Architecture governance corpus
├── 01-vision/              Product vision and requirements
├── 02-architecture/        Architecture baseline and ADRs
├── 03-engineering/         EOS: capability registry, TVM, build profile
├── 04-ai-framework/        AI model specifications
├── 05-work-packages/       Work packages and evidence records
├── 06-runtime/             Runtime layers 1–6 (FROZEN)
├── 07-research/            Research harness (offline backtest)
├── 08-operations/          Deployment and operational config
├── 09-validation/          Test contracts, schemas, fixtures
├── 10-release/             Completion reports and evidence archives
├── docs/
│   └── devsecops/          CI/CD and DevSecOps documentation
├── proto/                  Protocol buffer definitions
├── tests/                  All tests (unit, integration, chaos, performance)
├── tools/
│   ├── afrp-cli/           AFRP CLI (afrp command)
│   ├── baseline_gate.py    Architecture baseline fitness gate
│   ├── ops_gate.py         Operations fitness gate
│   ├── proto_gate.py       Protocol fitness gate
│   ├── system_gate.py      System fitness gate (FIT-008)
│   ├── metrics.py          Repository metrics generator
│   ├── traceability_gate.py Traceability chain validator
│   ├── evidence_archive.py  Evidence packager for releases
│   └── commit_msg_hook.py  Commit message validator
├── .github/
│   ├── workflows/          GitHub Actions workflows
│   ├── ISSUE_TEMPLATE/     Issue templates
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml
├── .pre-commit-config.yaml Pre-commit hook configuration
├── CONTRIBUTING.md         Contribution guide
├── SECURITY.md             Security policy
└── pyproject.toml          Python project configuration
```

---

## Key concepts

### Capability Registry
`03-engineering/CAPABILITY_REGISTRY.yaml` — The authoritative DAG of all
implementation capabilities. Status: `COMPLETE | AVAILABLE | LOCKED`.

### Work Packages
`05-work-packages/WP-*/` — Each capability has a work package that defines
bounded files, expected evidence, and acceptance criteria.

### Traceability Matrix (TVM)
`03-engineering/TRACEABILITY_MATRIX.yaml` — Maps every requirement to its
implementing capability, artifacts, and verifications.

### Fitness Functions (FIT-001–008)
Automated invariants that run in every CI build:
- FIT-001: Capability DAG is acyclic
- FIT-002: No import cycles across layer boundaries
- FIT-004: All modules declare explicit `__all__`
- FIT-005: All changes bounded by Work Package `bounded_files`
- FIT-006: No magic numbers in critical paths
- FIT-007: 100% TVM requirement coverage
- FIT-008: Deterministic replay with seeded RNG

---

## Getting help

- **Documentation**: `docs/` and layer-specific README files
- **Architecture questions**: Review `02-architecture/` and `00-governance/`
- **CI failures**: Check the Actions tab and workflow logs
- **Security**: See [SECURITY.md](../../SECURITY.md)
- **Contributing**: See [CONTRIBUTING.md](../../CONTRIBUTING.md)
