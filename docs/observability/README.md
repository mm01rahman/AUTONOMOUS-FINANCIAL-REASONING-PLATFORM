# Repository Metrics and Engineering Observability

The AFRP observability platform automatically collects, scores, and publishes engineering metrics across all repository dimensions.

## Quick Start

```bash
# Fast dashboard (skip subprocess checks)
uv run python -m tools.dashboard --fast

# Full dashboard (includes ruff/mypy/pytest)
uv run python -m tools.dashboard

# Single format
uv run python -m tools.dashboard --format json --output metrics.json
uv run python -m tools.dashboard --format html --output dashboard.html
uv run python -m tools.dashboard --format markdown --output dashboard.md

# All formats at once
uv run python -m tools.dashboard --format all --output-dir reports/

# Fail if health score below threshold (0.0–1.0)
uv run python -m tools.dashboard --threshold 0.80
```

## Architecture

```
tools/observability/
├── __init__.py
├── scoring.py          # HealthScore, HealthGrade, DimensionScore
├── snapshot.py         # MetricsSnapshot, collect_all()
├── dashboard.py        # render_markdown, render_html, render_github_summary
└── collectors/
    ├── repository.py   # CapabilityMetrics, WorkPackageMetrics
    ├── quality.py      # RuffMetrics, MypyMetrics, CoverageMetrics, TestMetrics
    ├── architecture.py # ArchitectureMetrics, FitnessResult
    ├── governance.py   # GovernanceMetrics
    ├── security.py     # SecurityMetrics, BanditMetrics, DependencyMetrics
    ├── release.py      # ReleaseMetrics
    └── git_metrics.py  # GitMetrics
```

## Health Score Model

The overall health score is a weighted composite of 10 dimensions:

| Dimension | Weight | How Measured |
|---|---|---|
| Architecture | 15% | Fitness gate pass rate (FIT-001–006) |
| Tests | 12% | pytest pass rate |
| Capabilities | 12% | Registry completion % |
| Mypy | 10% | 0 errors = 100%; errors reduce score |
| Coverage | 10% | Line coverage % |
| Traceability | 10% | TVM requirements implemented / total |
| Ruff | 8% | 0 violations = 100% |
| Governance | 8% | WPS + evidence completeness |
| Security | 8% | 0 high-severity findings = 100% |
| Release | 7% | Evidence + completion reports present |

**Grade thresholds:**

| Grade | Score |
|---|---|
| A+ | ≥ 95% |
| A | ≥ 85% |
| B | ≥ 70% |
| C | ≥ 55% |
| D | < 55% |

## GitHub Actions Integration

The `metrics.yml` workflow runs automatically after Quality Gates pass on `main`. It:

1. Downloads the coverage artifact from the quality workflow
2. Generates JSON, Markdown, and HTML dashboards
3. Uploads all reports as artifacts (90-day retention)
4. Writes a concise summary to `GITHUB_STEP_SUMMARY`

You can also trigger it manually via `workflow_dispatch` with the `fast` option to skip subprocess checks.

## Metric Definitions

### Repository Progress

- **total**: Number of capabilities in `CAPABILITY_REGISTRY.yaml`
- **complete**: Capabilities with `status: COMPLETE`
- **available**: Capabilities with `status: AVAILABLE`
- **locked**: Capabilities with `status: LOCKED`
- **completion_pct**: complete / total × 100
- **eos_completion_pct**: EOS capabilities (GOV-/EOS-/ENG-/REPO- prefixes) complete %
- **runtime_completion_pct**: Runtime capabilities (L1-/L6-/RT-) complete %

### Work Package Burn-Down

- **total**: WP YAML files found in `05-work-packages/`
- **completed**: WPs with `status: Completed`
- **burn_pct**: completed / total × 100

### Code Quality

- **ruff.violations**: Number of ruff lint violations
- **mypy.errors**: Number of mypy type errors
- **mypy.files_checked**: Files analysed by mypy
- **tests.collected**: pytest test count
- **tests.pass_rate**: passed / collected × 100
- **coverage.line_pct**: line coverage % from `coverage.json`

### Architecture

- **violations**: Count of `violations:` lines reporting > 0
- **fitness_results**: List of FIT-NNN pass/fail from gate output
- **gates_passed / gates_total**: Ratio

### Governance

- **wps_total / wps_completed**: WPS compliance
- **ers_total / ers_approved**: Evidence record compliance
- **tvm_coverage_pct**: Requirements with `status: implemented` %
- **adr_total / adr_accepted**: ADR tracking

### Security

- **bandit.high_severity**: High-severity Bandit findings
- **dependencies.total_vulnerabilities**: pip-audit vulnerability count
- **codeql_status**: CONFIGURED / NOT_CONFIGURED
- **secret_scan_status**: CONFIGURED / PARTIAL / NOT_CONFIGURED

### Release

- **tags**: Git tag count
- **completion_reports**: `10-release/*.md` count
- **evidence_records**: `10-release/*.yaml` count
- **readiness_score**: 0–100 composite release readiness

## Local Development

All collectors run without network access and do not modify repository state.

```python
from tools.observability.snapshot import collect_all
from tools.observability.scoring import compute_health_score

snap = collect_all(".", skip_quality_checks=True, skip_architecture_checks=True)
score = compute_health_score(snap)
print(f"{score.grade.value} — {score.pct:.1f}%")
```
