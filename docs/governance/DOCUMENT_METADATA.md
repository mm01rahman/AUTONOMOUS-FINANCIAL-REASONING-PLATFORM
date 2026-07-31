---
document_id: AFRP-DOCUMENT-METADATA-GUIDE-001
title: AFRP Document Metadata Standard
version: 1.0.0
status: Approved
owner: Architecture Review Board
authority: Level 2 - Baseline Governance
approved_date: 2026-07-31
last_modified: 2026-07-31
change_policy: Governed by BASELINE_FREEZE_POLICY.md
dependencies:
  - docs/governance/DOCUMENT_METADATA.yaml
referenced_by:
  - docs/governance/BASELINE_MANIFEST.md
review_policy: Review at every architecture baseline release
---

# AFRP Document Metadata Standard

## 1. Findings

Existing protected documents use several valid header styles: Markdown authority
blocks, YAML schema fields, Protobuf package/options, and JSON Schema identifiers.
Prepending one new format to every file would:

- invalidate the existing genesis fingerprint;
- add non-Protobuf syntax to `.proto` files;
- add non-schema fields to JSON Schema contracts;
- risk changing Level-0/Level-1 content without an ADR.

The canonical metadata is therefore the sidecar registry
[`DOCUMENT_METADATA.yaml`](DOCUMENT_METADATA.yaml). YAML merge keys expand common
authority defaults, and every document resolves to the same required fields.

## 2. Standard Fields

Each protected baseline artifact has:

1. `document_id`
2. `title`
3. `version`
4. `status`
5. `owner`
6. `authority`
7. `approved_date`
8. `last_modified`
9. `change_policy`
10. `dependencies`
11. `referenced_by`
12. `review_policy`

The registry also records the canonical `path`. Path is identity-bearing: moving a
protected artifact is a baseline change.

## 3. Status Semantics

| Status | Meaning |
| --- | --- |
| `Frozen` | Byte content is part of Architecture Baseline v1.0.0 |
| `Controlled` | Template/ledger structure is protected; governed instances may evolve |
| `Superseded` | Retained for history; replacement is identified in metadata |

No baseline artifact may silently return from `Superseded` to `Frozen`.

## 4. Files Created in Step 4

- `docs/governance/DOCUMENT_METADATA.yaml`
- `docs/governance/DOCUMENT_METADATA.md`

## 5. Files Modified in Step 4

None of the pre-existing protected documents.

## 6. Rationale

The sidecar format gives every document complete, queryable metadata while preserving
approved content and current SHA256 values. Newly created Phase 1 Markdown documents
also carry the same metadata inline for human discovery.

## 7. Risks

- Sidecar/content drift must be blocked by a governance gate.
- YAML anchors must be resolved before required-field validation.
- Metadata cannot change document authority; it only records authority already derived
  from GOV-002 and the canonical source map.

## 8. Completion Status

**STEP 4: COMPLETE**

All planned protected baseline artifacts have standardized metadata without rewriting
approved architecture.
