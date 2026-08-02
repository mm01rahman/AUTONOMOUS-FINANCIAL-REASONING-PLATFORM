# ADR-IKROS-001: Knowledge Graph Model Selection

**Document ID:** AFRP-ADR-IKROS-001
**Work Package:** WP-IMP-0041
**Date:** 2026-08-02
**Status:** Accepted
**Deciders:** Architecture Review Board (ARB)

---

## Context

IKROS requires a graph storage model to represent the knowledge graph with typed nodes, property-rich edges, and temporal validity.

**Options evaluated:**
1. RDF/OWL with SPARQL (e.g., Apache Jena, RDFLib)
2. Labelled Property Graph with Cypher (Neo4j, Kuzu)
3. NetworkX in-memory + YAML persistence
4. Custom adjacency list in Python dicts

## Decision

**Option 3 selected:** NetworkX in-memory graph with YAML persistence for Phase 1.

**Rationale:**
- Zero external dependencies (aligns with AFRP dependency philosophy)
- Full Python-native; no Docker or external service required
- YAML persistence integrates with existing EOS evidence standards
- NetworkX supports all required graph operations
- Clear migration path to Neo4j/Kuzu when scale requires it

**Migration trigger:** When node count exceeds 50,000 or query latency exceeds 500ms, migrate to Kuzu (embedded, no server required).

## Consequences

- Phase 1 IKROS has no query language — custom traversal methods required
- Maximum practical scale: ~10,000 nodes before performance degrades
- No ACID transactions in Phase 1 (mitigated by append-only event log)

---

# ADR-IKROS-002: Confidence Model Design

**Document ID:** AFRP-ADR-IKROS-002
**Work Package:** WP-IMP-0041
**Date:** 2026-08-02
**Status:** Accepted

## Context

IKROS must represent confidence in knowledge objects. Options:
1. Single scalar confidence (0–1)
2. Multi-dimensional confidence vector
3. Full Bayesian posterior distribution

## Decision

**Option 2 selected:** 8-dimensional confidence vector with weighted geometric mean for overall confidence.

**Rationale:**
- Single scalar loses information about WHY confidence is high or low
- Full Bayesian distribution is computationally expensive and requires distributional assumptions
- 8-dimensional vector captures the key uncertainty sources (statistical, economic, data, model, validation, replication, operational, prior) separately
- Geometric mean is appropriate for multiplicative independence assumption
- Weights per entity type allow domain-specific tuning

## Consequences

- Confidence updates require updating 1–8 dimensions rather than a single value
- Reporting must show dimension breakdown, not just overall score
- Weights must be calibrated as operational data accumulates

---

# ADR-IKROS-003: Memory Tier Architecture

**Document ID:** AFRP-ADR-IKROS-003
**Work Package:** WP-IMP-0041
**Date:** 2026-08-02
**Status:** Accepted

## Context

Research context spans from active computation (working memory) to permanent institutional knowledge. Options:
1. Single flat storage (all objects in one store)
2. Two-tier (active / archived)
3. Six-tier cognitive model (working → long-term)

## Decision

**Option 3 selected:** Six-tier memory architecture based on cognitive science.

**Rationale:**
- Financial research has natural memory tiers: active experiments, event history, factual assertions, procedures, research artifacts, and distilled institutional knowledge
- Clean separation simplifies retention policy enforcement
- Different tiers have different access patterns (T0: hot, T5: cold but always available)
- Maps naturally to IKROS object lifecycle states

## Consequences

- Consolidation logic must be maintained between tiers
- T0 cleanup on session end must be reliable
- T5 (Long-Term Memory) must be treated as immutable institutional record

---

# ADR-IKROS-004: Temporal Validity Model

**Document ID:** AFRP-ADR-IKROS-004
**Work Package:** WP-IMP-0041
**Date:** 2026-08-02
**Status:** Accepted

## Context

Knowledge changes over time. Options:
1. No temporal tracking (current state only)
2. Valid-time only (when was this true in the world?)
3. Bitemporal (valid-time + transaction-time)

## Decision

**Option 3 selected:** Bitemporal model on all edges.

**Rationale:**
- AFRP needs point-in-time queries ("what did we believe on 2026-01-01?") to understand historical research decisions
- Transaction time enables audit ("when did we record this belief?")
- Bitemporal model fully covers both needs at modest complexity cost
- Critical for regulatory audit trail if AFRP ever operates with real capital

## Consequences

- All edges carry both `valid_from`/`valid_to` and `asserted_at`/`retracted_at`
- Queries must explicitly specify time dimension when needed
- Storage overhead ~2x compared to current-state-only model

---

# ADR-IKROS-005: Integration Coupling Strategy

**Document ID:** AFRP-ADR-IKROS-005
**Work Package:** WP-IMP-0041
**Date:** 2026-08-02
**Status:** Accepted

## Context

IKROS must integrate with AFRP Runtime, backtesting, paper trading, and future systems. Options:
1. Direct import (tight coupling)
2. Shared database (data coupling)
3. Port and adapter pattern (clean architecture)
4. Event-driven (fully async, eventual consistency)

## Decision

**Option 3 selected:** Port and adapter pattern as primary integration strategy, with Option 4 (event bus) for non-critical notifications.

**Rationale:**
- Clean Architecture mandate prohibits tight coupling between Runtime and IKROS
- Shared database would create deployment dependency
- Pure event-driven introduces eventual consistency complexity for read-after-write patterns
- Ports and adapters allows synchronous reads where needed while keeping write paths async

## Consequences

- All IKROS integration code lives in adapter classes, not in Runtime or IKROS core
- Interface versioning required for all ports
- Testing uses mock implementations of `IKROSWriter` and `IKROSReader`
