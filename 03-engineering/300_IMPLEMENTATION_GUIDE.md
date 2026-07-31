# DOCUMENT 300 — `300_IMPLEMENTATION_GUIDE.md`

> **Authority Level:** Level 2 (Operable) | **Specification ID:** `IMP-001`
> 

## 1. Monorepo Directory Topology

```text
afrp-platform/
├── 00-governance/          # Constitutional rules, KERNEL bootloader, BASELINE_FINGERPRINT.yaml
├── 01-vision/              # Charter and product mission objectives
├── 02-architecture/        # Specifications, SLS docs, ADR ledger, ADR template
├── 03-engineering/         # CAPABILITY_REGISTRY, TRACEABILITY_MATRIX, REPOSITORY_HEALTH
├── 04-ai-framework/        # AI Engineer Playbook, ORCHESTRATOR.md, Role Taxonomy
├── 05-work-packages/       # Task contracts (WP-*.yaml) and evidence ledgers
├── 06-runtime/             # Production runtime source code (Layers 1-6 + common)
├── 07-research/            # Offline notebooks, training scripts, backtest harnesses
├── 08-operations/          # Infrastructure as Code, Dockerfiles, deployment configs
├── 09-validation/          # Test suites, chaos tests, JSON/YAML schemas
├── 10-release/             # Release manifests, tagged deployment baselines
├── proto/                  # Protobuf v3 wire contracts and custom annotations
├── tests/                  # Global unit and integration test runners
├── tools/                  # Source code for afrp-cli toolchain
├── REPOSITORY_MANIFEST.yaml# Top-level repository topology manifest
├── pyproject.toml          # Python workspace configuration
└── Cargo.toml              # Rust workspace cargo configuration

```

## 2. Bootstrapping Script (`bootstrap_m1.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Initializing AFRP Monorepo Skeleton (m1.1-start)..."

mkdir -p 00-governance 01-vision 02-architecture/specs 03-engineering \
         04-ai-framework 05-work-packages/WP-IMP-0003/evidence 06-runtime \
         07-research 08-operations 09-validation/schemas 10-release \
         proto/afrp/v1 tests/unit tools/afrp-cli/afrp/commands tools/afrp-cli/afrp/core

cat << 'EOF' > pyproject.toml
[project]
name = "afrp-platform"
version = "0.1.0"
description = "Autonomous Financial Reasoning Platform"
requires-python = ">=3.11,<3.13"
dependencies = ["click>=8.1.0", "pydantic>=2.0.0", "pyyaml>=6.0.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
strict = true
python_version = "3.11"
EOF

cat << 'EOF' > Cargo.toml
[workspace]
resolver = "2"
members = []

[workspace.package]
version = "0.1.0"
edition = "2021"
EOF

echo "✓ Skeleton and workspace configurations initialized successfully."

```

## 3. First Executable Task Contract (`05-work-packages/WP-IMP-0003.yaml`)

```yaml
schema_version: "WPS-1.0"
work_package_id: "WP-IMP-0003"
capability_id:
  id: "EOS-CONTEXT"
  version: "1.0"
title: "Implement afrp boot command & Manifest/Kernel Parsers"
status: "Assigned"
is_immutable: true

governance:
  target_subsystem: "EOS-CLI"
  traceability:
    implements_req: ["FR-001", "OBS-01"]
    trace_sls: "ROS-1.0.0"
    trace_adr: ["ADR-0001"]
    trace_vvc: "TVM-001"

preconditions:
  - predicate: "git.tag == 'm1.1-start'"
  - predicate: "file.exists('REPOSITORY_MANIFEST.yaml')"
  - predicate: "file.exists('00-governance/KERNEL.md')"

resources:
  cpu: "low"
  memory: "512MB"
  network: false
  filesystem:
    write:
      - "tools/afrp-cli/afrp/"
      - "tests/unit/"
      - "05-work-packages/WP-IMP-0003/evidence/"
    read:
      - "REPOSITORY_MANIFEST.yaml"
      - "00-governance/KERNEL.md"

execution:
  priority: "high"
  estimated_complexity: "small"
  estimated_duration: "1h"
  parallelizable: false
  deterministic: true

rollback:
  strategy: "git_checkout_bounded_files"
  restore_tag: "HEAD"

inputs:
  required_files:
    - "REPOSITORY_MANIFEST.yaml"
    - "00-governance/KERNEL.md"

outputs:
  expected_source_files:
    - "tools/afrp-cli/afrp/cli.py"
    - "tools/afrp-cli/afrp/commands/boot.py"
    - "tools/afrp-cli/afrp/core/manifest.py"
    - "tools/afrp-cli/afrp/core/kernel.py"
    - "tools/afrp-cli/afrp/core/exceptions.py"
    - "tests/unit/test_bootloader.py"
  expected_evidence:
    - "05-work-packages/WP-IMP-0003/evidence/EXEC-001.yaml"

execution_results:
  source_files_modified: []
  evidence_generated: []

produces:
  capability:
    id: "EOS-CONTEXT"
    version: "1.0"
  unlocks:
    - id: "EOS-GRAPH"
      version: "1.0"

scope:
  bounded_files:
    - "tools/afrp-cli/afrp/cli.py"
    - "tools/afrp-cli/afrp/commands/boot.py"
    - "tools/afrp-cli/afrp/core/manifest.py"
    - "tools/afrp-cli/afrp/core/kernel.py"
    - "tools/afrp-cli/afrp/core/exceptions.py"
    - "tests/unit/test_bootloader.py"

  non_goals:
    - "Do not implement dependency DAG parsing (deferred to IMP-0004)."
    - "Do not implement AST linter checking (deferred to IMP-0005)."

requirements:
  boot_parser:
    module: "tools/afrp-cli/afrp/core/manifest.py"
    rules:
      - "Parse REPOSITORY_MANIFEST.yaml into Pydantic model RepositoryManifest."
      - "Validate schema_version == '1.0'."
  kernel_parser:
    module: "tools/afrp-cli/afrp/core/kernel.py"
    rules:
      - "Parse 00-governance/KERNEL.md."
      - "Assert word count <= 400. Raise InvariantError if breached."

quality_gates:
  ruff_lint:
    required: true
    command: "uv run ruff check tools/afrp-cli/"
  mypy_typecheck:
    required: true
    command: "uv run mypy --strict tools/afrp-cli/"
  pytest_units:
    required: true
    command: "uv run pytest tests/unit/test_bootloader.py -v"

completion:
  success_requires:
    - "'afrp boot' command registered and executable."
    - "100% unit tests passing."
    - "Quality gates pass with zero errors."

failure_modes:
  ERR-CONTRACT-REFERENCE: "Missing REPOSITORY_MANIFEST.yaml or KERNEL.md."
  ERR-CONTRACT-AMBIGUITY: "KERNEL.md word count exceeds 400."
  ERR-EXEC-BOUNDARY: "Touched files outside bounded_files."

execution_prompt: |
  You are an autonomous AI Software Engineer executing Work Package WP-IMP-0003 in role AEF-02.
  Implement afrp boot command, manifest parser, and kernel parser strictly within bounded_files.
  Run quality gates and generate EXEC-001.yaml evidence record upon completion.

```

## 4. Agent Dispatch Prompt (Copy & Paste to Claude Code)

```text
========================================================================================
                 CLAUDE CODE FRESH START HANDOFF & EXECUTION DIRECTIVE
========================================================================================
You are an autonomous AI Software Engineer operating inside the `afrp-platform` monorepo 
in the Engineer role (AEF-02). 

Your operational context is governed strictly by 000_ENGINEERING_CONSTITUTION.md, 
100_SYSTEM_ARCHITECTURE.md, 110_RUNTIME_ARCHITECTURE.md, 120_ENGINEERING_OPERATING_SYSTEM.md,
130_MATHEMATICAL_FOUNDATION.md, 200_REFERENCE_SPECIFICATION.md, 00-governance/KERNEL.md, 
REPOSITORY_MANIFEST.yaml, and 03-engineering/CAPABILITY_REGISTRY.yaml.

----------------------------------------------------------------------------------------
PHASE 1: EGP-2.0 ZERO-WRITE HANDSHAKE (DO NOT WRITE CODE YET)
----------------------------------------------------------------------------------------
Perform a zero-write environment handshake by traversing EGP-2.0 state transitions:
  1. Read 00-governance/KERNEL.md (< 400 words bootloader).
  2. Ingest REPOSITORY_MANIFEST.yaml and 03-engineering/CAPABILITY_REGISTRY.yaml.
  3. Compute SHA256 digests of baseline artifacts and verify against BASELINE_FINGERPRINT.yaml.
  4. Confirm lifecycle state is BASELINE_VERIFIED and emit the required `repository_state` 
     YAML diagnostic block.

----------------------------------------------------------------------------------------
PHASE 2: WORK PACKAGE ASSIGNMENT & EXECUTION (WP-IMP-0003)
----------------------------------------------------------------------------------------
Upon completing Phase 1, load Work Package contract: 05-work-packages/WP-IMP-0003.yaml

Execute the following steps:
  1. Verify all preconditions in WP-IMP-0003.yaml evaluate to PASSED.
  2. Transition state to EXECUTION_AUTHORIZED (Write access locked exclusively to bounded_files).
  3. Implement the `afrp boot` CLI command, manifest parser, and kernel parser strictly within:
       - tools/afrp-cli/afrp/cli.py
       - tools/afrp-cli/afrp/commands/boot.py
       - tools/afrp-cli/afrp/core/manifest.py
       - tools/afrp-cli/afrp/core/kernel.py
       - tools/afrp-cli/afrp/core/exceptions.py
       - tests/unit/test_bootloader.py
  4. Run automated quality gates sequentially:
       - uv run ruff check tools/afrp-cli/
       - uv run mypy --strict tools/afrp-cli/
       - uv run pytest tests/unit/test_bootloader.py -v
  5. Generate ERS-1.0 compliant evidence record at 05-work-packages/WP-IMP-0003/evidence/EXEC-001.yaml.
  6. Halt execution and request human ARB review.

Acknowledge these instructions and execute Phase 1 (EGP-2.0 Handshake).
========================================================================================

```

