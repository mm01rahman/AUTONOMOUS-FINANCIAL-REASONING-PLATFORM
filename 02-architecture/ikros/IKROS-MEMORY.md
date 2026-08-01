# IKROS Memory Architecture

**Document ID:** AFRP-IKROS-MEMORY-1.0.0
**Specification Authority:** SPEC-060 §6 — Memory Architecture
**Work Package:** WP-IMP-0041
**Version:** 1.0.0
**Status:** Draft — Awaiting ARB Approval

---

## 1. Overview

IKROS implements a **six-tier memory architecture** modelled on cognitive science principles adapted for institutional research. Each tier has distinct characteristics:

| Tier | Name | Retention | Capacity | Purpose |
|------|------|-----------|----------|---------|
| T0 | Working Memory | Session | Small | Active experiment context |
| T1 | Episodic Memory | Indefinite | Medium | Research event timeline |
| T2 | Semantic Memory | Permanent | Large | Factual knowledge |
| T3 | Procedural Memory | Permanent | Medium | Research methodology |
| T4 | Research Memory | Permanent | Large | All research artifacts |
| T5 | Long-Term Institutional Memory | Permanent | Unlimited | Distilled institutional knowledge |

See **ADR-IKROS-003** for tier architecture rationale.

---

## 2. Tier 0: Working Memory

**Purpose:** Active context for the current research session or experiment execution.

**Characteristics:**
- Session-scoped (cleared on session end)
- Fast in-memory access (no I/O)
- Holds current experiment configuration
- Holds active hypothesis under test
- Holds current feature set
- Holds partial results during execution

**Schema:**
```yaml
session_id: str
started_at: ISO8601
active_research_question: IKROS-ID | null
active_experiment: IKROS-ID | null
active_hypotheses: list[IKROS-ID]
active_features: list[IKROS-ID]
active_dataset_version: IKROS-ID | null
current_results: dict         # Intermediate results
current_confidence: float[0,1]
flags: dict                   # Session-level flags
```

**Lifecycle:**
- Created at session start
- Updated continuously during execution
- Consolidated to T1 (Episodic) at session end
- Cleared after consolidation

**Consolidation Trigger:**
Session end, experiment completion, or explicit `consolidate()` call.

---

## 3. Tier 1: Episodic Memory

**Purpose:** Chronological timeline of all research events and decisions.

**Characteristics:**
- Append-only event log
- Temporal ordering preserved
- Queryable by time range, agent, or event type
- Never modified or deleted

**Schema:**
```yaml
event_id: str                 # UUID
event_type: enum              # See event taxonomy below
timestamp: ISO8601
session_id: str
agent_id: str
description: str
object_ref: IKROS-ID | null   # Related knowledge object
parent_event: str | null      # Causal predecessor
metadata: dict
```

**Event Taxonomy:**
| Event Type | Trigger |
|-----------|---------|
| `RESEARCH_STARTED` | New ResearchQuestion created |
| `HYPOTHESIS_PROPOSED` | Hypothesis registered |
| `EXPERIMENT_DESIGNED` | Experiment design approved |
| `EXPERIMENT_STARTED` | Experiment execution begun |
| `EXPERIMENT_COMPLETED` | Results produced |
| `VALIDATION_COMPLETED` | Validation verdict issued |
| `HYPOTHESIS_SUPPORTED` | Evidence supports hypothesis |
| `HYPOTHESIS_REFUTED` | Evidence refutes hypothesis |
| `FAILURE_RECORDED` | Research failure captured |
| `ALPHA_CANDIDATE_EVALUATED` | Promotion assessment completed |
| `ALPHA_PROMOTED` | Alpha promotion approved |
| `ALPHA_REJECTED` | Alpha promotion rejected |
| `CONTRADICTION_DETECTED` | Contradictory evidence found |
| `CONTRADICTION_RESOLVED` | Contradiction resolution completed |
| `KNOWLEDGE_INSTITUTIONALISED` | KnowledgeObject ratified |
| `CONCLUSION_PUBLISHED` | ResearchConclusion approved |

**Episodic Memory File Layout:**
```
data/ikros/episodic/
├── events/
│   ├── 2026/
│   │   ├── 08/
│   │   │   └── EVENTS-20260802.yaml  # Daily event log
│   │   └── ...
└── EPISODIC_INDEX.yaml
```

---

## 4. Tier 2: Semantic Memory

**Purpose:** Factual, structured knowledge — the assertion store.

**Characteristics:**
- Entity-attribute-value store
- Backed by the Knowledge Graph
- Queryable by entity type, attribute, or value
- Versioned: every update creates a new version record
- No deletion; only version supersession

**Contents:**
- All knowledge graph nodes and their current attribute values
- All active relationships between entities
- Current confidence scores for all entities
- Regime definitions and characteristics
- Market event catalogue

**Semantic Memory Update Protocol:**
1. New assertion arrives
2. Conflict check: does this contradict existing semantic memory?
3. If conflict: create `ContradictoryEvidence`, trigger conflict resolution
4. If no conflict: write new version, update confidence, publish event

---

## 5. Tier 3: Procedural Memory

**Purpose:** Research methodologies, protocols, and procedures.

**Characteristics:**
- Versioned methodology templates
- Governs how experiments are designed
- Governs how features are computed
- Governs promotion criteria
- NOT updated during experiments; only updated by ARB review

**Schema:**
```yaml
procedure_id: str
procedure_name: str
procedure_type: enum   # EXPERIMENT_PROTOCOL | FEATURE_COMPUTATION | VALIDATION_PROTOCOL | PROMOTION_CRITERIA
version: semver
steps: list[str]
parameters: dict
constraints: list[str]
approved_at: ISO8601
approved_by: str
```

**Examples:**
- `PROC-WF-001`: Walk-forward validation protocol
- `PROC-PROMO-001`: Alpha promotion criteria
- `PROC-FEAT-001`: Feature computation and validation protocol
- `PROC-CONTRA-001`: Contradiction resolution process

**Procedural Memory File Layout:**
```
data/ikros/procedural/
├── PROC-WF-001.yaml
├── PROC-PROMO-001.yaml
├── PROC-FEAT-001.yaml
└── PROC-CONTRA-001.yaml
```

---

## 6. Tier 4: Research Memory

**Purpose:** Complete archive of all research artifacts.

**Characteristics:**
- Maps directly to all 13 IKROS registries
- Immutable once an artifact is COMPLETE or ARCHIVED
- Full history of every state transition
- Queryable by any attribute
- Search indexed

**Contents:**
All 13 registries (see `IKROS-REGISTRIES.md`)

**Research Memory Index:**
```yaml
# data/ikros/RESEARCH_INDEX.yaml
total_research_questions: int
total_hypotheses: int
total_experiments: int
total_validations: int
total_models: int
total_alpha_candidates: int
total_alphas_promoted: int
total_failures: int
total_knowledge_objects: int
last_updated: ISO8601
index_version: str
```

---

## 7. Tier 5: Long-Term Institutional Memory

**Purpose:** Distilled, ratified, high-confidence institutional knowledge that persists indefinitely.

**Characteristics:**
- Highest quality threshold (requires ARB approval)
- Rarely changes (only when superseded by stronger evidence)
- Forms the institutional prior for future research
- Always available and never evicted
- Searchable by semantic similarity

**Contents:**
- All `KnowledgeObject` entities with `status = INSTITUTIONALISED`
- All `ResearchConclusion` entities with `approval_status = APPROVED`
- All `Failure` entities (permanent, immutable)
- All `EconomicThesis` entities with `status = SUPPORTED`
- Regime definitions with `status = ACTIVE`
- Factor catalogue with `status = ACTIVE`

**Institutional Knowledge Index:**
```yaml
# data/ikros/institutional/INSTITUTIONAL_INDEX.yaml
total_knowledge_objects: int
total_conclusions: int
total_failures: int           # Always cumulative
total_supported_theses: int
total_active_factors: int
institutional_confidence: float[0,1]  # Overall confidence in institutional knowledge
last_reviewed: ISO8601
next_review_due: ISO8601
```

---

## 8. Knowledge Consolidation Pipeline

### 8.1 Consolidation Flow

```
T0 Working Memory
    ↓ (session end)
T1 Episodic Memory (event logged)
    ↓ (experiment complete)
T4 Research Memory (registry entry created)
    ↓ (validation approved)
T2 Semantic Memory (graph updated)
    ↓ (conclusion approved by ARB)
T5 Long-Term Institutional Memory (institutionalised)
```

### 8.2 Consolidation Rules

| Transition | Trigger | Required Gate |
|-----------|---------|--------------|
| T0 → T1 | Session end or experiment complete | None (automatic) |
| T0/T1 → T4 | Object achieves COMPLETE lifecycle state | Schema validation |
| T4 → T2 | Object is approved and linked to graph | Conflict check |
| T4 → T5 | ARB approves institutionalisation | ARB sign-off |
| T4 (Failure) → T5 | Failure is ANALYSED | Automatic (no gate) |

### 8.3 Failure Fast Path

Failure records bypass normal consolidation gates and go directly to T5:

```
Failure Recorded (T4)
    ↓ (automatic, no approval needed)
Failure Institutionalised (T5)
```

This ensures Constitutional Article IX compliance: failures become institutional memory immediately.

---

## 9. Knowledge Retirement

### 9.1 Retirement Conditions

An object may be retired when:
1. A successor object with higher confidence supersedes it
2. The underlying dataset is no longer valid
3. Market structure change makes the knowledge inapplicable
4. ARB determines the knowledge is misleading

### 9.2 Retirement Process

1. `RetirementProposal` filed with reason and successor reference
2. ARB review (mandatory for T5 objects)
3. Transition to `RETIRED` state (never deleted)
4. All graph edges updated with `valid_to = retirement_date`
5. Successor edges created from retired to new object

### 9.3 Retirement Preservation

All retired objects remain queryable for:
- Historical analysis
- Regime-specific recall (retired strategies may be valid under specific regimes)
- Contradiction detection (retired conclusions may still contradict new proposals)

---

## 10. Memory Statistics

IKROS tracks memory health metrics:

```yaml
memory_health:
  working_memory_age_hours: float
  episodic_events_today: int
  semantic_memory_nodes: int
  semantic_memory_edges: int
  research_memory_objects: int
  institutional_memory_objects: int
  institutional_confidence: float[0,1]
  failures_recorded_total: int
  contradictions_open: int
  contradictions_pending_resolution: int
  knowledge_coverage: float[0,1]  # % of research questions with concluded answers
```

---

## 11. Traceability

| Specification Section | Implemented By |
|----------------------|----------------|
| SPEC-060 §6 Memory Architecture | This document |
| SPEC-060 §6.1 Working Memory | §2 Tier 0 |
| SPEC-060 §6.2 Semantic Memory | §4 Tier 2 |
| SPEC-060 §6.3 Episodic Memory | §3 Tier 1 |
| SPEC-060 §6.4 Procedural Memory | §5 Tier 3 |
| SPEC-060 §6.5 Research Memory | §6 Tier 4 |
| SPEC-060 §6.6 Long-Term Memory | §7 Tier 5 |
| SPEC-060 §6.7 Consolidation | §8 |
| SPEC-060 §6.8 Retirement | §9 |
