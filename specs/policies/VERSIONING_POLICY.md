# AFRP Specification Versioning Policy

> **Document ID:** `SPEC-POL-VER-1.0` | **Authority:** ARB | **Status:** Active
> **Work Package:** WP-IMP-0040

## 1. Purpose

This policy governs the complete lifecycle of every AFRP specification, from initial
draft through final archival. It ensures specifications are versioned, traceable, and
reproducible.

## 2. Specification Lifecycle States

```
Draft ──► Review ──► Approved ──► Implemented ──► Validated ──► Deprecated ──► Archived
  │                    │                               │                │
  │                    └── Rejected ──► Draft          │                └── Superseded
  └── Abandoned                                        └── Regression ──► Review
```

### State Definitions

| State | Description | Entry Condition | Exit Condition |
|-------|-------------|-----------------|----------------|
| `Draft` | Work in progress; no implementation permitted | New spec created | Author submits for review |
| `Review` | Under ARB/technical review | Author submits | ARB approves or rejects |
| `Approved` | Formally approved; implementation may begin | ARB approves | Implementation completes |
| `Implemented` | All required capabilities implemented | Work Packages complete | Validation passes |
| `Validated` | Implementation verified against spec | All quality gates pass | — (stable state) |
| `Deprecated` | Superseded or phased out | ARB decision | Grace period ends |
| `Archived` | No longer active; preserved for audit | Deprecation grace period ends | — (terminal state) |

## 3. Promotion Rules

### Draft → Review

- Spec author completes all required sections (see Repository Organization Standard)
- Spec registered in `SPECIFICATION_REGISTRY.yaml`
- Pull Request opened with `[SPEC-REVIEW]` prefix

### Review → Approved

- **Level 0:** Unanimous ARB + Principal Architect sign-off
- **Level 1:** ARB majority + Architecture sign-off
- **Level 2:** Principal Quantitative Researcher + ARB review
- **Level 3:** Lead Engineer + Tech Lead review
- **Level 4-7:** EGP-2.0 compliance + ARB awareness

### Approved → Implemented

- At least one Work Package referencing the spec reaches status `Completed`
- All bounded capabilities in `CAPABILITY_REGISTRY.yaml` set to `COMPLETE`
- Evidence record `EXEC-NNN.yaml` present with `verdict.all_gates_passed: true`

### Implemented → Validated

- All quality gates pass: ruff, mypy --strict, pytest, coverage >= 80%
- `afrp validate`, `afrp plan`, `afrp health`, `afrp evidence` all PASS
- No regression against any higher-level specification

### Validated → Deprecated

- Superseding specification reaches `Approved` state
- ARB issues formal deprecation notice
- One-minor-version grace period before all consumers must migrate (EDR-012)

### Deprecated → Archived

- Grace period elapsed
- All consuming specs/capabilities updated to reference successor
- File moved to `specs/XX-level/archive/` with `ARCHIVED-` prefix

## 4. Versioning Scheme

Specifications use semantic versioning: `MAJOR.MINOR.PATCH`

| Component | Increment Rule |
|-----------|----------------|
| `MAJOR` | Breaking change to spec (incompatible requirements) |
| `MINOR` | Additive change (new sections, new requirements) |
| `PATCH` | Clarification, correction, no requirement change |

### Version Examples

- `1.0.0` → First approved version
- `1.1.0` → New section added (minor increment)
- `1.1.1` → Typo correction (patch)
- `2.0.0` → Breaking restructuring requiring implementation re-work

## 5. Pending Import Policy

For specifications that exist outside the repository (`Pending_Import` status):

1. Create stub spec document with proper metadata header
2. Register in `SPECIFICATION_REGISTRY.yaml` with `import_status: Pending_Import`
3. Document what content is expected and where it will come from
4. Record which capabilities depend on the missing specification
5. Assign import as Tier 1 or Tier 2 priority in conformance matrix
6. **No capability may be created without a corresponding approved spec**

Import promotion path: `Pending_Import → Draft → Review → Approved`

## 6. Specification Integrity Rules

1. **Immutability:** Approved specifications are immutable without version bump
2. **Traceability:** Every spec version must trace to TVM requirements
3. **No orphan specs:** Specs without implementing capabilities after 2 minor versions
   must be re-reviewed by ARB
4. **Conflict resolution:** Level hierarchy resolves conflicts (INHERIT-002)
5. **Archive preservation:** Archived specs are NEVER deleted; git history is permanent
   record

## 7. Automatic Version Tracking

All version history is captured by git. The specification registry records current
versions. To view a spec's history:

```bash
git log --follow specs/XX-level/SPEC-NNN-*.md
```

To view what changed between versions:

```bash
git diff <tag1>..<tag2> -- specs/XX-level/SPEC-NNN-*.md
```
