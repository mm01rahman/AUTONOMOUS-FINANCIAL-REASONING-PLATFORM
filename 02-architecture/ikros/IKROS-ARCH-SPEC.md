# IKROS Architecture Specification

**Document ID:** AFRP-IKROS-ARCH-SPEC-1.0.0
**Specification Authority:** SPEC-060 — IKROS Architecture
**Work Package:** WP-IMP-0041
**Version:** 1.0.0
**Status:** Draft — Awaiting ARB Approval
**Author:** Architecture Review Board (ARB)
**Date:** 2026-08-02

---

## 1. Executive Summary

The Institutional Knowledge & Research Operating System (IKROS) is the institutional memory, reasoning, lineage, and knowledge infrastructure for the Autonomous Financial Reasoning Platform (AFRP).

IKROS addresses the highest-priority architectural gap identified in the WP-IMP-0040 ARB Conformance Audit: the absence of a governed system for capturing, indexing, propagating, and retiring institutional research knowledge.

Without IKROS, AFRP is stateless between research campaigns. Phase E failures are not encoded as institutional memory. Future agents repeat past mistakes. Contradictory evidence cannot be detected. Knowledge does not accumulate.

With IKROS, every research artifact produced during the lifetime of AFRP is managed, versioned, linked, and queryable. Institutional intelligence compounds.

---

## 2. Architectural Mandate

IKROS derives from **Constitutional Article IX** of the AFRP Engineering Constitution:

> *All research failures shall become institutional memory. No failure shall be repeated. Knowledge shall compound.*

IKROS implements this mandate by providing:

- A governed **Knowledge Ontology** of all first-class research objects
- A **Knowledge Graph** linking all objects with typed, temporal edges
- A set of **Institutional Registries** for every object class
- A **Research Lifecycle** governing every knowledge state transition
- A **Memory Architecture** spanning working to long-term memory
- A **Lineage Model** recording complete provenance of every object
- A **Confidence Model** representing and propagating epistemic state
- A **Governance System** enforcing institutional quality standards
- A **Query Architecture** enabling institutional intelligence queries
- An **Integration Architecture** connecting IKROS to all AFRP systems

---

## 3. Architectural Principles

### P-1: No Knowledge Is Lost
Every research artifact — including failures, contradictions, and retracted conclusions — is retained, versioned, and queryable. Deletion is prohibited; only archival and retirement are permitted.

### P-2: Every Object Has Provenance
No knowledge object may exist without complete lineage: origin, dependencies, evidence, validation, and successor chain.

### P-3: Confidence Is Explicit
Every knowledge object carries explicit confidence scores across multiple dimensions. Implicit confidence is prohibited. Uncertainty is a first-class citizen.

### P-4: Contradictions Are Resolved, Not Silenced
When new evidence contradicts existing knowledge, the contradiction is registered, investigated, and resolved through governed process. Resolution evidence is stored permanently.

### P-5: Governance Precedes Promotion
No research artifact may advance to institutional status without satisfying defined governance gates. Promotion is never implicit.

### P-6: Temporal Integrity
Every edge in the knowledge graph carries a valid-time interval. The knowledge graph accurately represents what was believed at every point in time.

### P-7: Clean Architecture Integration
IKROS integrates with AFRP Runtime through defined ports and adapters. No IKROS component directly imports Runtime implementation. No Runtime component directly imports IKROS implementation.

### P-8: Future-Proof Extensibility
IKROS ontology, graph schema, registry schema, and query system are designed to accommodate Graph Neural Networks, automatic literature review, autonomous hypothesis generation, and meta-learning without breaking changes.

---

## 4. System Boundaries

```
╔══════════════════════════════════════════════════════════════════╗
║                         AFRP RUNTIME                             ║
║  (FROZEN — no IKROS code inside Runtime layers)                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ┌─────────────────────────────────────────────────────────┐    ║
║  │                      IKROS BOUNDARY                     │    ║
║  │                                                         │    ║
║  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    ║
║  │  │  Knowledge   │  │  Registries  │  │   Memory    │  │    ║
║  │  │    Graph     │  │  (13 types)  │  │ Architecture│  │    ║
║  │  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘  │    ║
║  │         └────────────────┬┴───────────────────┘         │    ║
║  │                  ┌───────┴──────┐                        │    ║
║  │                  │  IKROS Core  │                        │    ║
║  │                  │  (Ontology + │                        │    ║
║  │                  │  Governance) │                        │    ║
║  │                  └───────┬──────┘                        │    ║
║  └──────────────────────────┼────────────────────────────┘    ║
║                             │ Port                              ║
║  ╔══════════════════════════╪═══════════════════════════════╗  ║
║  ║          AFRP INTEGRATION LAYER (Adapters)              ║  ║
║  ╚═══════════════════════════════════════════════════════════╝  ║
╚══════════════════════════════════════════════════════════════════╝
```

IKROS is an **infrastructure service** external to the Runtime. It communicates through:
- **Inbound port:** `IKROSWriter` — Runtime pushes research events to IKROS
- **Outbound port:** `IKROSReader` — Agents query IKROS for institutional knowledge
- **Event bus:** `IKROSEventBus` — IKROS publishes knowledge state change events

---

## 5. Component Architecture

### 5.1 IKROS Core Components

| Component | Responsibility |
|-----------|---------------|
| `OntologyEngine` | Enforces ontology constraints on all knowledge objects |
| `GraphStore` | Manages the knowledge graph (nodes, edges, temporal validity) |
| `RegistryManager` | Routes reads/writes to the 13 institutional registries |
| `LifecycleEngine` | Governs all state transitions for every object |
| `LineageRecorder` | Records and verifies complete object provenance |
| `ConfidenceEngine` | Computes and propagates confidence scores |
| `GovernanceGate` | Enforces promotion criteria and approval workflows |
| `QueryEngine` | Executes institutional intelligence queries |
| `ConflictResolver` | Detects and manages contradictory evidence |
| `MemoryManager` | Manages memory tiers (working → long-term) |
| `EventBus` | Publishes all IKROS state changes to subscribers |

### 5.2 Dependency Order

```
OntologyEngine
    ↓
GraphStore ← LineageRecorder
    ↓
RegistryManager → ConfidenceEngine
    ↓
LifecycleEngine → GovernanceGate
    ↓
MemoryManager → ConflictResolver
    ↓
QueryEngine
    ↓
EventBus
```

---

## 6. Data Architecture

### 6.1 Persistence Strategy

| Data Layer | Technology | Purpose |
|------------|-----------|---------|
| Knowledge Graph | Graph database (RDF/LPG) | Node/edge relationships, temporal validity |
| Registries | Structured store (YAML/JSON/RDBMS) | Schema-validated objects per type |
| Event Log | Append-only log | All IKROS state transitions |
| Search Index | Full-text index | Natural language query support |
| Evidence Store | Flat file (YAML) | ERS-1.0 compliant evidence records |

### 6.2 Naming Conventions

All IKROS persistent identifiers follow:

```
IKROS-{TYPE}-{YYYYMMDD}-{SEQ:04d}
```

Examples:
- `IKROS-HYP-20260101-0001` — Hypothesis
- `IKROS-EXP-20260801-0042` — Experiment
- `IKROS-ALPHA-20260801-0003` — Alpha Candidate

---

## 7. Architecture Decisions

See `ADR-IKROS-001.md` through `ADR-IKROS-005.md` for all major architectural decisions with rationale.

---

## 8. Document Index

| Document | Contents |
|----------|---------|
| `IKROS-ARCH-SPEC.md` | This document — system overview and architectural principles |
| `IKROS-ONTOLOGY.md` | Complete knowledge ontology (30 entities, all attributes and relationships) |
| `IKROS-KNOWLEDGE-GRAPH.md` | Graph model, node types, edge types, constraints, temporal model |
| `IKROS-REGISTRIES.md` | 13 institutional registries — schema, lifecycle, queries |
| `IKROS-MEMORY.md` | Memory architecture — 6 tiers from working to long-term |
| `IKROS-LINEAGE.md` | Lineage model — provenance, dependencies, successor chains |
| `IKROS-CONFIDENCE.md` | Confidence and uncertainty models with propagation rules |
| `IKROS-GOVERNANCE.md` | Governance model — approvals, reviews, contradiction resolution |
| `IKROS-INTEGRATION.md` | Integration architecture with all AFRP systems |
| `IKROS-FUTURE.md` | Future evolution roadmap — GNN, autonomous research, meta-learning |
| `ADR-IKROS-001.md` | ADR: Graph model selection |
| `ADR-IKROS-002.md` | ADR: Confidence model design |
| `ADR-IKROS-003.md` | ADR: Memory tier architecture |
| `ADR-IKROS-004.md` | ADR: Temporal validity model |
| `ADR-IKROS-005.md` | ADR: Integration coupling strategy |

---

## 9. Traceability

| Requirement | Source | Status |
|------------|--------|--------|
| NFR-036 | SPEC-060 §2 | Implemented by IKROS-ARCH-SPEC |
| NFR-037 | SPEC-060 §4 | Implemented by IKROS-ONTOLOGY |
| NFR-038 | SPEC-060 §5 | Implemented by IKROS-KNOWLEDGE-GRAPH |

---

## 10. Stop Condition

This document represents an **architecture design** only.

No Python implementation code shall be written for IKROS until:
1. ARB approves WP-IMP-0041 and all architecture documents
2. WP-IMP-0042 (IKROS Core Registries) is issued

**STOP: Awaiting ARB approval before WP-IMP-0042.**
