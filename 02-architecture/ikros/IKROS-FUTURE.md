# IKROS Future Evolution Roadmap

**Document ID:** AFRP-IKROS-FUTURE-1.0.0
**Specification Authority:** SPEC-060 §13 — Future Evolution
**Work Package:** WP-IMP-0041
**Version:** 1.0.0
**Status:** Draft — Awaiting ARB Approval

---

## 1. Design for Future

The IKROS architecture is designed from inception to accommodate the following advanced capabilities without requiring breaking changes to the core ontology or graph schema.

---

## 2. Graph Neural Networks

**Target WP:** WP-IMP-0060+

The IKROS knowledge graph is structured to be directly consumable by GNN frameworks:
- Every node carries a fixed-dimension feature vector (attributes normalised to embedding space)
- Every edge carries a type embedding and weight
- Temporal edges support time-series GNN architectures

**Future capability:** Learn patterns in the research graph itself — predict which hypotheses are likely to be supported based on graph structure, or predict alpha promotion probability from experiment lineage patterns.

---

## 3. Knowledge Graph AI

**Target WP:** WP-IMP-0065+

IKROS is the knowledge source for an AI assistant with full institutional context:
- Agent can answer: "Has this alpha been tried before?"
- Agent can answer: "What do we know about XAU/USD in risk-off regimes?"
- Agent can synthesise: "Given our failure history, what approach should we try next?"

**Required:** IKROS ontology schema must be exposed as LLM context. The `IKROSReader` interface provides the data; an LLM adapter translates natural language to graph queries.

---

## 4. Automatic Literature Review

**Target WP:** WP-IMP-0055+

IKROS will eventually manage an automated literature ingestion pipeline:
1. Crawl ArXiv, SSRN, and institutional research databases
2. Parse abstracts and extract research claims
3. Map claims to IKROS ontology (Hypothesis, EconomicThesis, etc.)
4. Detect conflicts with existing institutional knowledge
5. Queue for human review

**Required:** `Literature` registry is already designed to hold external research. The ingestion pipeline is the only addition needed.

---

## 5. Automatic Hypothesis Generation

**Target WP:** WP-IMP-0070+

Given a ResearchQuestion, IKROS can generate candidate Hypotheses by:
1. Querying similar ResearchQuestions in the graph
2. Inspecting what Hypotheses were generated from those questions
3. Adapting successful patterns to the new question
4. Generating hypotheses from EconomicThesis combinations
5. Consulting the KnowledgeObject registry for applicable principles

**Required:** No schema changes needed. The generator uses existing graph traversal.

---

## 6. Research Gap Detection

**Target WP:** WP-IMP-0058+

IKROS can automatically identify:
- ResearchQuestions with no Experiments (`OPEN` and `ACTIVE` but `tested_in = []`)
- Hypotheses that are `SUPPORTED` but have low `C_rep` (tested only once)
- Regimes with no corresponding Hypotheses
- Features with no corresponding Factors
- Literature with no corresponding Hypotheses (cited but not operationalised)

**Required:** New scheduled job running against existing IKROS graph. No schema changes.

---

## 7. Meta-Learning

**Target WP:** WP-IMP-0075+

IKROS accumulates the data needed for meta-learning:
- Which Hypothesis patterns tend to be supported vs. refuted?
- Which Feature families tend to produce stable Models?
- Which economic conditions correlate with alpha success?
- What confidence threshold is predictive of paper trading success?

**Required:** Export IKROS registry data to ML training pipeline. IKROS provides the labels; the meta-learner provides the patterns.

---

## 8. Research Assistants

**Target WP:** WP-IMP-0080+

Specialised AI agents operating within IKROS governance:
- `LiteratureAgent`: Ingests and categorises new literature
- `HypothesisAgent`: Generates and refines hypotheses
- `ExperimentAgent`: Designs experiments, selects features and datasets
- `ValidationAgent`: Interprets validation results and updates confidence
- `ReportingAgent`: Generates research reports from IKROS state

**Required:** `IKROSWriter` interface is designed for agent use. Governance gates ensure agent output is quality-controlled.

---

## 9. Autonomous Experiment Planning

**Target WP:** WP-IMP-0085+

Given a Research Priority Queue (from Gap Detection), IKROS orchestrates:
1. Select highest-priority unanswered ResearchQuestion
2. Generate candidate Hypotheses (see §5)
3. Identify optimal features and datasets for each hypothesis
4. Design minimal experiment(s) to distinguish hypotheses
5. Execute experiment via AFRP backtesting engine
6. Record results to IKROS
7. Update confidence, publish events
8. Repeat

**Required:** Integration between IKROS GovernanceGate and AFRP Orchestrator (L6-OPT). No schema changes. Requires explicit ARB authorisation to enable autonomous mode.

---

## 10. Extensibility Guarantees

The IKROS architecture makes the following forward-compatibility guarantees:

| Feature | Guarantee |
|---------|-----------|
| New entity types | Can be added as new ontology classes without modifying existing entities |
| New relationship types | Can be added to the graph schema without affecting existing queries |
| New registry | Can be added without affecting existing registries |
| New memory tier | Can be added without affecting existing tiers |
| New confidence dimension | Can be added with a MINOR schema version bump |
| New query patterns | Can be implemented as new traversal methods |

---

## 11. Traceability

| Specification Section | Implemented By |
|----------------------|----------------|
| SPEC-060 §13 Future Evolution | This document |
| SPEC-060 §13.1 GNN | §2 |
| SPEC-060 §13.2 Knowledge Graph AI | §3 |
| SPEC-060 §13.3 Literature Review | §4 |
| SPEC-060 §13.4 Hypothesis Generation | §5 |
| SPEC-060 §13.5 Gap Detection | §6 |
| SPEC-060 §13.6 Meta-Learning | §7 |
| SPEC-060 §13.7 Research Assistants | §8 |
| SPEC-060 §13.8 Autonomous Research | §9 |
