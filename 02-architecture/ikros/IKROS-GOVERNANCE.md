# IKROS Governance Model

**Document ID:** AFRP-IKROS-GOVERNANCE-1.0.0
**Specification Authority:** SPEC-060 §10 — Knowledge Governance
**Work Package:** WP-IMP-0041
**Version:** 1.0.0
**Status:** Draft — Awaiting ARB Approval

---

## 1. Overview

IKROS governance ensures that institutional knowledge maintains rigorous standards. Every knowledge object that reaches institutional status has been through a governed approval process.

**Governance authority hierarchy:**
1. Architecture Review Board (ARB) — highest authority
2. Research Review Gate (RRG) — automated quality gate
3. Peer Review — human expert review
4. Agent Review — automated agent checks

---

## 2. Approval Workflows

### 2.1 Hypothesis Approval

```
PROPOSED
    ↓ Auto-check: statement is falsifiable, significance_level set
PEER_REVIEW (human)
    ↓ Reviewer signs off
APPROVED_FOR_TESTING
    ↓ Experiment executed; Validation produced
TESTING
    ↓ RRG: verdict ≠ INCONCLUSIVE required
SUPPORTED | REFUTED | INCONCLUSIVE
    ↓ If REFUTED: auto-create Failure record
    ↓ If SUPPORTED: ARB acknowledgment for C_overall > 0.50
INSTITUTIONALISED (T5) | RETIRED
```

### 2.2 Alpha Promotion Approval

The most critical governance gate in AFRP:

```
CANDIDATE
    ↓ RRG Gate: all metrics computed
EVALUATION_COMPLETE
    ↓ Mandatory criteria check (all must pass):
    │  ✓ OOS Sharpe ≥ 1.0
    │  ✓ Max drawdown ≤ 20%
    │  ✓ Direction accuracy ≥ 0.52
    │  ✓ WF consistency_score ≥ 0.60
    │  ✓ MC p_value ≤ 0.05
    │  ✓ overfitting_index ≤ 2.0
    │  ✓ C_overall ≥ 0.50
PROMOTION_ELIGIBLE | REJECTED
    ↓ If PROMOTION_ELIGIBLE: ARB formal review
ARB_REVIEW
    ↓ ARB approves or rejects
PROMOTED | REJECTED
    ↓ If REJECTED: Failure record created automatically
    ↓ If PROMOTED: Alpha entity created, paper trading authorised
```

**Note from Phase E:** All 6 Phase E candidates were REJECTED at the EVALUATION_COMPLETE gate. No ARB review was required because no candidate was PROMOTION_ELIGIBLE.

### 2.3 Knowledge Object Institutionalisation

```
EXTRACTED (from Failure or Conclusion)
    ↓ RRG: confidence ≥ 0.40 required
VALIDATED
    ↓ Peer review: applicability confirmed
INSTITUTIONALISED
    ↓ Monitoring: confidence tracking
MONITORING
    ↓ Periodic review (every 90 days)
    ↓ If confidence drops below 0.30: RETIREMENT_PROPOSED
RETIRED
```

### 2.4 ARB Review Types

| Review Type | Trigger | Turnaround |
|------------|---------|-----------|
| `ALPHA_PROMOTION` | AlphaCandidate reaches PROMOTION_ELIGIBLE | 5 business days |
| `CONTRADICTION_MAJOR` | ContradictoryEvidence severity = MAJOR | 7 calendar days |
| `CONTRADICTION_INVALIDATING` | ContradictoryEvidence severity = INVALIDATING | 1 business day |
| `INSTITUTIONALISATION` | KnowledgeObject reaches VALIDATED | 10 business days |
| `ARCHITECTURE_CHANGE` | Any IKROS schema change | 14 calendar days |
| `SPEC_REVISION` | Specification update request | 21 calendar days |

---

## 3. Versioning Policy

### 3.1 Semantic Versioning

All IKROS entities and schemas use Semantic Versioning (SemVer `MAJOR.MINOR.PATCH`):

| Change Type | Version Bump | Example |
|------------|-------------|---------|
| Backward-incompatible schema change | MAJOR | 1.0.0 → 2.0.0 |
| New optional field added | MINOR | 1.0.0 → 1.1.0 |
| Bug fix, documentation update | PATCH | 1.0.0 → 1.0.1 |
| Content update (Hypothesis refined) | PATCH | 1.0.0 → 1.0.1 |
| Significant factual update | MINOR | 1.0.0 → 1.1.0 |
| Contradiction invalidates core | MAJOR | 1.0.0 → 2.0.0 |

### 3.2 Version History

Every entity maintains an append-only version history:

```yaml
version_history:
  - version: "1.0.0"
    changed_at: ISO8601
    changed_by: str
    change_summary: str
    confidence_at_time: float
```

### 3.3 Schema Versioning

IKROS registry schemas are versioned independently. Schema changes require:
- MINOR bump: backward-compatible (additive only)
- MAJOR bump: migration script required, ARB approval needed

---

## 4. Duplicate Detection

### 4.1 Detection Algorithm

IKROS runs duplicate detection when a new entity is registered:

1. **Semantic similarity**: compute embedding similarity against existing entities of same type
2. **Structural similarity**: compare key attributes (hypothesis statement, feature computation, etc.)
3. **Threshold**: if similarity > 0.85, flag as potential duplicate

### 4.2 Duplicate Handling

| Similarity | Action |
|-----------|--------|
| > 0.95 | Block registration; link to existing entity |
| 0.85–0.95 | Warn; require explicit confirmation to proceed |
| 0.70–0.85 | Log as related; register with cross-reference |
| < 0.70 | Register without warning |

### 4.3 Intentional Duplication

When the same hypothesis is independently derived by two agents:
1. Register both (confirm is a human deliberate action)
2. Link with `INDEPENDENTLY_DERIVED` edge
3. When both are tested, replication_count increments for both
4. This is the replication mechanism supporting C_rep confidence

---

## 5. Knowledge Supersession

When a new, better-supported object replaces an existing one:

```
Old Object (SUPPORTED, C_overall = 0.70)
    ↓ New experiment with stronger evidence
New Object (SUPPORTED, C_overall = 0.85)
    ↓ Governance gates pass
Old Object → lifecycle: SUPERSEDED
New Object → lifecycle: SUPPORTED
SUPERSEDED_BY edge: Old → New
```

**Supersession rules:**
1. The new object must have higher `C_overall` than the old
2. The new object must cite the old object in its lineage
3. ARB approval required for T5 (Long-Term Memory) objects
4. Old object remains queryable permanently (point-in-time queries)

---

## 6. Contradiction Resolution Protocol

See also `IKROS-KNOWLEDGE-GRAPH.md §7`.

### 6.1 Escalation Matrix

| Severity | Detector | Resolver | SLA |
|----------|---------|---------|-----|
| MINOR | Automated | Automated (log only) | 30 days |
| MODERATE | Automated | Peer Review | 14 days |
| MAJOR | Automated | ARB | 7 days |
| INVALIDATING | Automated | ARB (emergency) | 1 day |

### 6.2 Resolution Options

1. **Accept and update**: New evidence is correct; reduce old object's `C_overall`
2. **Reject with justification**: New evidence is flawed; record quality concerns
3. **Scope refinement**: Both are correct under different conditions; narrow scope of old object
4. **Defer**: Insufficient evidence to resolve; mark as `ACCEPTED_CONTRADICTION`

---

## 7. Audit Trail

### 7.1 Audit Log Schema

```yaml
audit_id: str
event_type: str           # CREATED | UPDATED | TRANSITIONED | APPROVED | REJECTED | RETIRED
object_id: IKROS-ID
object_type: str
timestamp: ISO8601
actor: str
previous_state: str | null
new_state: str
change_summary: str
evidence_ref: str | null
```

### 7.2 Audit Retention

| Category | Retention |
|---------|-----------|
| Standard objects | 7 years |
| Alpha decisions | 10 years |
| Failure records | Permanent |
| Contradiction resolutions | 10 years |
| ARB decisions | Permanent |

### 7.3 Audit Integrity

The audit log is:
- Append-only (no modifications permitted)
- SHA256 hash-chained (each entry includes hash of previous)
- Stored separately from registries
- Backed up on every commit

---

## 8. Retention and Archival

### 8.1 Retention Schedule

| Object Type | Minimum Retention | Maximum Action |
|------------|------------------|---------------|
| Active objects | Indefinite | Supersession allowed |
| Retired objects | 7 years | Archive allowed |
| Failure records | Permanent | Never archived |
| ARB decisions | Permanent | Never archived |

### 8.2 Archival Process

1. Object marked `ARCHIVED`
2. Full YAML snapshot written to `data/ikros/archive/`
3. Graph edges updated with `valid_to = archive_date`
4. Object removed from active registry indices (but stays in graph)
5. Archive record created with all cross-references preserved

---

## 9. Governance Health Metrics

IKROS exposes governance health metrics for `afrp health`:

```yaml
governance_health:
  objects_pending_review: int
  overdue_reviews: int
  open_contradictions: int
  orphan_objects: int           # Objects without lineage
  duplicate_candidates: int
  retirement_candidates: int
  audit_log_integrity: bool     # Hash chain valid
  arb_queue_depth: int
  arb_queue_oldest_days: int
```

---

## 10. Traceability

| Specification Section | Implemented By |
|----------------------|----------------|
| SPEC-060 §10 Governance | This document |
| SPEC-060 §10.1 Approvals | §2 Approval Workflows |
| SPEC-060 §10.2 Reviews | §2 ARB Review Types |
| SPEC-060 §10.3 Versioning | §3 Versioning Policy |
| SPEC-060 §10.4 Duplicates | §4 Duplicate Detection |
| SPEC-060 §10.5 Supersession | §5 Knowledge Supersession |
| SPEC-060 §10.6 Contradictions | §6 Contradiction Resolution |
| SPEC-060 §10.7 Audit | §7 Audit Trail |
| SPEC-060 §10.8 Retention | §8 Retention and Archival |
