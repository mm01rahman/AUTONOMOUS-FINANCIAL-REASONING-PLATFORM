# AFRP Specification Repository Organization Standard

> **Document ID:** `SPEC-POL-ORG-1.0` | **Authority:** ARB | **Status:** Active
> **Work Package:** WP-IMP-0040

## 1. Directory Structure

```
specs/
├── README.md                                   # Documentation index
├── registry/
│   ├── SPECIFICATION_REGISTRY.yaml             # Authoritative catalog
│   ├── SPECIFICATION_HIERARCHY.md              # Authority chain
│   ├── SPECIFICATION_DEPENDENCY_GRAPH.md       # Dependency relationships
│   └── CONFORMANCE_MATRIX.md                   # ARB audit report
├── policies/
│   ├── VERSIONING_POLICY.md                    # Lifecycle rules
│   └── REPOSITORY_ORGANIZATION_STANDARD.md    # This document
├── 00-constitution/                            # Level 0 — Constitutional
├── 01-architecture/                            # Level 1 — Architecture
├── 02-research/                                # Level 2 — Research
├── 03-engineering/                             # Level 3 — Engineering
├── 04-runtime/                                 # Level 4 — Runtime/Implementation
├── 05-validation/                              # Level 5 — Validation
├── 06-operations/                              # Level 6 — Operational
└── 07-knowledge/                               # Level 7 — Knowledge/Intelligence
```

## 2. Naming Convention

### Specification Files

```
SPEC-NNN-<KEBAB-TITLE>.md
```

Where:
- `NNN` = 3-digit numeric ID (000-999)
- `KEBAB-TITLE` = Kebab-case title

Examples:
- `SPEC-000-INSTITUTIONAL-CONSTITUTION.md`
- `SPEC-010-RESEARCH-STANDARD-RS10.md`
- `SPEC-060-IKROS-ARCHITECTURE.md`

### Archived Files

```
ARCHIVED-SPEC-NNN-<KEBAB-TITLE>-v<VERSION>.md
```

## 3. Required Specification Header

Every specification document MUST begin with the following header block:

```markdown
# SPEC-NNN — <Title>

> **Specification ID:** `SPEC-NNN`
> **Version:** `MAJOR.MINOR.PATCH`
> **Level:** L0 | L1 | L2 | L3 | L4 | L5 | L6 | L7
> **Status:** Draft | Review | Approved | Implemented | Validated | Deprecated | Archived
> **Owner:** <Team/Role>
> **Approval Authority:** <ARB | Principal Researcher | Lead Engineer>
> **Work Package:** WP-IMP-XXXX
> **Canonical Source:** <path or "Original"> 
> **Effective Date:** YYYY-MM-DD
> **Supersedes:** SPEC-XXX | None
```

## 4. Required Sections by Specification Level

### All Levels (Minimum Required)

1. Purpose
2. Scope
3. Authority & Governance
4. Requirements (normative)
5. Traceability
6. Conformance Evidence
7. Revision History

### Level 2 Research Specifications (Additional)

8. Research Methodology
9. Validation Criteria
10. Failure Modes
11. Known Limitations

### Level 4 Runtime Specifications (Additional)

8. Component Interfaces
9. Data Contracts (CIO references)
10. Error Handling
11. Performance Requirements

## 5. Quality Standards

All specification documents must:

| Standard | Rule |
|----------|------|
| Searchability | Use consistent terminology defined in `GLOSS-001` |
| Versionability | Every change produces a version bump per versioning policy |
| Traceability | Every requirement traces to `TRACEABILITY_MATRIX.yaml` |
| Reproducibility | Mathematical claims cite `MATH-001` section references |
| Automation support | Machine-readable data lives in `SPECIFICATION_REGISTRY.yaml` |

## 6. Integration Requirements

Specifications must support:

- **Capability Registry integration:** Each spec references its capabilities in the registry
- **Work Package generation:** WPs reference `implements_spec` field
- **Repository metrics:** Spec status tracked by observability collectors
- **IKROS integration:** Once built, IKROS knowledge graph nodes link to specs

## 7. Searchability Standard

Specifications are full-text searchable via:

```bash
# Find all specs mentioning a term
grep -r "DSmT" specs/

# Find all approved specs
grep -r "Status.*Approved" specs/

# Find specs for a capability
grep -r "L3-WRM" specs/
```

## 8. Registry Synchronization

After every specification state change:

1. Update `specs/registry/SPECIFICATION_REGISTRY.yaml` with new status/version
2. Update `specs/README.md` quick navigation table
3. If coverage changed, update `specs/registry/CONFORMANCE_MATRIX.md`
4. If new spec added, update `specs/registry/SPECIFICATION_DEPENDENCY_GRAPH.md`
