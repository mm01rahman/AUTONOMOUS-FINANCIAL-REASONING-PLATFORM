# ADR-0002 — Genesis Normalizations and Toolchain Waivers

**Status:** Accepted · **Date:** 2026-07-31 · **Level:** 0 (Genesis, single-shot)

## Context

Materializing AFRP-BASELINE-1.0.0 onto a Windows host exposed naming inconsistencies
inside the suite and two host toolchain gaps. These must be resolved once, at genesis,
and recorded permanently.

## Decisions

### N-1 Constitution filename

GOV-002 references `00-governance/000_CPG_CONSTITUTION.md`; the suite's own document
header names it `000_ENGINEERING_CONSTITUTION.md`. The document header wins:
canonical path is `00-governance/000_ENGINEERING_CONSTITUTION.md`. The GOV-002 name
is a recorded alias; no file by the alias name exists.

### N-2 Document placement

Docs are placed per GOV-002/IMP-001 intent: 000 → `00-governance/`; 050/100/110/130/200
→ `02-architecture/`; 120/300 → `03-engineering/`. Bare document names are resolved
through `REPOSITORY_MANIFEST.yaml` `document_index`.

### N-3 Windows bootstrap

`bootstrap_m1.sh` (doc 300 §2) is a bash script; the host is Windows. The skeleton,
`pyproject.toml`, and `Cargo.toml` were produced by a faithful PowerShell equivalent
with identical outputs. The `pyproject.toml` is completed with a build target and the
`afrp` console script (the doc 300 §2 fragment alone is not installable); dev tools
(ruff, mypy, pytest, et al.) live in a `dev` dependency group, not runtime dependencies.

### W-001 buf waiver

`buf` is unavailable on the host. Contract validation is performed by compiling
`proto/afrp/v1` with `grpcio-tools` plus a repository FIT-003 checker; wire
compatibility (NFR-010/EDR-010) is enforced by contract snapshot comparison under
`09-validation/`. `buf` gates are restored verbatim when the tool becomes available.

### W-002 cargo waiver

`cargo`/Rust is unavailable on the host. The Rust workspace manifest remains declared
with zero members; the EDR-003 CPU-bound branch is satisfied with process pools.
Rust extension slots can be adopted later without architectural change.

## Consequences

Recorded in `03-engineering/BUILD_PROFILE.yaml` (`toolchain_waivers`). All other
suite content is adopted verbatim; no requirement was weakened — only the enforcing
tool substituted, with the substitution itself gated and tested.
