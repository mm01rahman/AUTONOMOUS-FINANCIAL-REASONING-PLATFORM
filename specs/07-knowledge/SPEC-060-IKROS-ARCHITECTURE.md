# SPEC-060 — IKROS: Institutional Knowledge & Research Operating System Architecture

> **Specification ID:** `SPEC-060`
> **Version:** `0.9.0`
> **Level:** L7 (Knowledge & Intelligence Specification)
> **Status:** Draft (Awaiting ARB Approval)
> **Owner:** Architecture Review Board (ARB)
> **Approval Authority:** ARB
> **Work Package:** WP-IMP-0040 (import) / WP-IMP-0041 (implementation — BLOCKED pending ARB approval)
> **Canonical Source:** `AFRP-IKROS-ARCH-1.0.0` (external ARB document — IMPORTED)
> **Effective Date:** 2026-08-02
> **Supersedes:** None

---

## CURRENT STATE NOTE

AFRP has completed:
✓ Architecture, EOS, Runtime, V&V, Engineering Automation, Repository Metrics,
✓ Data Foundation, Alpha Research Infrastructure, Backtesting, Paper Trading.

The Runtime is FROZEN. The Engineering OS is FROZEN.

This specification establishes the permanent institutional knowledge system that
will power all future quantitative research.

**AWAITING ARB APPROVAL.** Do NOT implement until ARB approves this specification.

---

## 1. Mission

Design the Institutional Knowledge & Research Operating System (IKROS).

IKROS will become the scientific memory and reasoning foundation of AFRP.

Its purpose: ensure AFRP never loses knowledge, never repeats failed research
unnecessarily, and continuously accumulates validated institutional intelligence.

---

## 2. Knowledge Ontology

### Core Entities

| Entity | Purpose | Key Attributes | Lifecycle |
|--------|---------|----------------|-----------|
| **Research Question** | Motivating question for investigation | question, domain, source, status | Open → Answered → Archived |
| **Economic Thesis** | Causal mechanism claim | thesis, mechanism, evidence, confidence | Draft → Validated → Retired |
| **Market Mechanism** | Structural market behaviour | mechanism, conditions, evidence | Active → Superseded |
| **Literature Source** | Academic or institutional reference | title, authors, journal, year, relevance | Catalogued → Cited → Archived |
| **Dataset** | Data source definition | name, provider, frequency, coverage | Active → Deprecated |
| **Dataset Version** | Specific data snapshot | hash, rows, date_range, quality | Validated → Archived |
| **Feature** | Engineered signal | name, family, formula, stationarity | Active → Deprecated |
| **Feature Family** | Grouped feature set | name, agent, purpose | Active → Retired |
| **Feature Transformation** | Data preprocessing step | name, input, output, formula | Active → Deprecated |
| **Factor** | Persistent alpha driver | name, economic_rationale, evidence | Researching → Validated → Retired |
| **Indicator** | Technical or statistical signal | name, formula, parameters | Active → Deprecated |
| **Regime** | Market state classification | name, conditions, detection_method | Active → Superseded |
| **Market Event** | Significant market occurrence | event_id, type, date, impact | Recorded |
| **Experiment** | Structured test of a hypothesis | hypothesis, design, dataset, result | Planned → Running → Concluded |
| **Validation Run** | Formal validation execution | experiment_id, metrics, gates, verdict | Pending → Complete |
| **Backtest** | Historical performance simulation | strategy, period, parameters, results | Completed → Archived |
| **Walk-Forward Study** | OOS robustness test | strategy, folds, oos_sharpe | Completed → Archived |
| **Monte Carlo Study** | Statistical robustness test | strategy, simulations, ruin_prob | Completed → Archived |
| **Stress Test** | Regime/event robustness test | strategy, scenario, result | Completed → Archived |
| **Model** | Predictive or generative model | type, architecture, parameters | Draft → Production → Retired |
| **World Model** | Market state synthesis model | version, components, performance | Active → Retired |
| **Decision** | Trade decision record | action, rationale, outcome, regret | Recorded |
| **Policy** | Risk and execution policy | type, parameters, bounds | Active → Superseded |
| **Hypothesis** | Testable claim | claim, mechanism, expected_outcome | Draft → Testing → Confirmed/Rejected |
| **Alpha Candidate** | Potential alpha signal | signal, thesis, phase | Candidate → Validated/Rejected |
| **Alpha** | Validated edge | signal, evidence, conditions, decay | Active → Decaying → Retired |
| **Failure** | Failed experiment record | hypothesis, evidence, reason, lesson | Recorded → Learned |
| **Contradictory Evidence** | Evidence against a thesis | evidence, thesis_id, weight | Active |
| **Validation Evidence** | Evidence supporting a thesis | evidence, metrics, verdict | Active |
| **Performance Report** | Strategy/model performance | period, metrics, benchmarks | Completed |
| **Research Conclusion** | Formal research finding | question, finding, confidence, evidence | Draft → Published |

---

## 3. Knowledge Graph Design

### 3.1 Node Types

- `ResearchQuestion`, `EconomicThesis`, `MarketMechanism`, `LiteratureSource`
- `Dataset`, `DatasetVersion`, `Feature`, `FeatureFamily`
- `Experiment`, `ValidationRun`, `Backtest`, `WalkForward`, `MonteCarlo`
- `Hypothesis`, `AlphaCandidate`, `Alpha`, `Failure`
- `Model`, `WorldModel`, `Decision`, `Policy`
- `Regime`, `MarketEvent`, `ResearchConclusion`

### 3.2 Relationship Types

| Relationship | From | To | Meaning |
|-------------|------|----|---------|
| `MOTIVATES` | MarketEvent | ResearchQuestion | Event prompts investigation |
| `TESTS` | Experiment | Hypothesis | Experiment evaluates hypothesis |
| `USES` | Experiment | Dataset | Dataset used in experiment |
| `USES` | Experiment | Feature | Feature used in experiment |
| `PRODUCES` | Experiment | Failure / Alpha | Experiment outcome |
| `VALIDATES` | ValidationRun | Alpha | Validation confirms alpha |
| `CONTRADICTS` | Evidence | Hypothesis | Evidence against hypothesis |
| `DERIVES_FROM` | Feature | Dataset | Feature computed from data |
| `SUPERSEDES` | Hypothesis | Hypothesis | New hypothesis replaces prior |
| `INFORMS` | Alpha | Policy | Alpha drives policy parameter |
| `TRAINED_ON` | Model | Dataset | Model trained on data |
| `EXPLAINS` | Model | Decision | Model explains decision |

### 3.3 Graph Constraints

- All nodes must have unique IDs
- All edges must have timestamps
- Provenance required on every node (creator, creation_date, source_WP)
- No orphan nodes — all knowledge must be connected to at least one other node

### 3.4 Confidence Propagation

Confidence flows through the graph:
- Confidence of downstream nodes limited by minimum confidence of upstream dependencies
- Contradictory evidence reduces confidence proportionally
- Validated replications increase confidence

---

## 4. Registry Architecture

| Registry | Stores | Primary Key | Query Capabilities |
|---------|--------|-------------|-------------------|
| **Research Registry** | Research questions + lifecycle | research_id | By domain, status, date |
| **Hypothesis Registry** | All hypotheses + test results | hypothesis_id | By status, domain, evidence |
| **Dataset Registry** | Dataset versions + checksums | dataset_id + version | By frequency, coverage, hash |
| **Feature Registry** | All features + families | feature_id | By family, agent, importance |
| **Factor Registry** | Validated factors | factor_id | By domain, evidence strength |
| **Experiment Registry** | All experiments | experiment_id | By hypothesis, result |
| **Validation Registry** | All validation runs | validation_id | By experiment, verdict |
| **Model Registry** | All models | model_id | By type, performance |
| **Alpha Registry** | Validated alpha signals | alpha_id | By regime, performance |
| **Failure Registry** | Failed experiments | failure_id | By hypothesis, reason |
| **Literature Registry** | Academic references | source_id | By domain, relevance |
| **Decision Registry** | Trade decisions | decision_id | By date, outcome, regret |
| **Knowledge Registry** | Consolidated conclusions | knowledge_id | By confidence, domain |

---

## 5. Research Lifecycle

```
Observation
    ↓
Research Question  →  Literature Review
    ↓
Economic Thesis
    ↓
Hypothesis  ←─── Prior Knowledge (Failure Registry)
    ↓
Experiment Design
    ↓
Dataset Selection  (Dataset Registry)
    ↓
Feature Engineering  (Feature Registry)
    ↓
Validation  (Validation Registry)
    ↓
Statistical Evaluation
    ↓
Conclusion  →  Knowledge Registration (Knowledge Registry)
    ↓
Monitoring  →  Alpha Registry (if promoted)
    ↓
Retirement
```

Every transition must be governed by EGP-2.0 with evidence records.

---

## 6. Memory Architecture

### 6.1 Short-Term Research Memory

- Active experiment context
- Current working hypothesis
- In-progress dataset analyses
- Retention: session duration

### 6.2 Working Memory

- Active hypothesis under test
- Feature set being evaluated
- Current validation state
- Retention: experiment lifecycle

### 6.3 Semantic Memory

- Consolidated market knowledge
- Validated mechanisms
- Economic theses with confidence scores
- Retention: permanent until superseded

### 6.4 Episodic Memory

- Experiment history with outcomes
- Market event sequences
- Strategy performance by regime
- Retention: permanent

### 6.5 Procedural Memory

- Research methodology steps
- Experiment design templates
- Validation procedures
- Retention: permanent, versioned

### 6.6 Long-Term Research Memory

- Validated institutional knowledge
- Published research conclusions
- Alpha registry entries
- Retention: permanent archive

### 6.7 Memory Interactions

- Short-term → Long-term: via Knowledge Registration
- Episodic → Semantic: via Consolidation Engine
- Failure memory → Hypothesis generation: via Failure Registry query
- Memory retrieval: graph-traversal based on relevance

---

## 7. Lineage Model

Every IKROS object must record full lineage:

```yaml
lineage:
  origin: <source dataset or event>
  created_by: <WP or agent>
  created_at: <timestamp>
  dependencies:
    - <object_id>
  experiments:
    - <experiment_id>
  datasets:
    - <dataset_id + version>
  features:
    - <feature_id>
  models:
    - <model_id>
  validation:
    - <validation_id>
  successors:
    - <object_id>
  retirement:
    reason: <deprecation reason>
    superseded_by: <successor_id>
```

---

## 8. Confidence & Uncertainty Model

### 8.1 Confidence Components

| Component | Definition | Range |
|-----------|-----------|-------|
| Prior Confidence | Domain expert prior belief | [0, 1] |
| Statistical Confidence | p-value / effect size evidence | [0, 1] |
| Economic Confidence | Mechanistic plausibility | [0, 1] |
| Data Confidence | Data quality and coverage | [0, 1] |
| Model Confidence | Model calibration quality | [0, 1] |
| Validation Confidence | Out-of-sample validation | [0, 1] |
| Replication Confidence | Independent replication | [0, 1] |

### 8.2 Overall Confidence

```
overall_confidence = weighted_geometric_mean(all_components)
```

Minimum component sets the ceiling (weakest link principle).

### 8.3 Uncertainty Types (per SPEC-003 principles)

| Type | Description | Storage |
|------|-------------|---------|
| Aleatoric | Irreducible market randomness | Sigma_EWM entropy |
| Epistemic | Knowledge gaps / missing data | m(Θ) in DSmT |
| Regime | Structural market change | Regime node in graph |
| Data | Data quality issues | Dataset version flags |
| Model | Model specification error | Model calibration metrics |
| Operational | Execution/latency risks | System health metrics |

---

## 9. Knowledge Governance

| Policy | Rule |
|--------|------|
| Versioning | Every knowledge object gets semantic version on update |
| Approvals | Tier-based: conclusions need ARB review; hypothesis updates need researcher |
| Evidence | Every node requires evidence_id from ERS-1.0 |
| Review | Periodic (quarterly) review of long-term memory for staleness |
| Retirement | Deprecated knowledge preserved in archive; never deleted |
| Supersession | New conclusions must explicitly link to and supersede prior |
| Duplicate Detection | Graph traversal for semantic similarity before new node creation |
| Contradiction Handling | Both contradictory nodes preserved; marked with `CONTRADICTS` edge |
| Auditability | All changes logged with timestamp, agent_id, evidence_id |

---

## 10. Query System

IKROS must answer the following institutional questions:

| Query | Description |
|-------|-------------|
| `"What hypotheses exist for inflation?"` | Graph: `ResearchQuestion → Hypothesis` filter by domain=inflation |
| `"Which experiments failed?"` | `Failure Registry` query by status=FAILED |
| `"Which alpha candidates were rejected?"` | `Alpha Registry` filter by status=REJECTED |
| `"What evidence supports this feature?"` | `Feature → Experiment → ValidationRun` traversal |
| `"What research contradicts this result?"` | `CONTRADICTS` edge traversal from node |
| `"What datasets have been used for this hypothesis?"` | `Hypothesis → Experiment → Dataset` traversal |
| `"What alpha performs best during high-volatility regimes?"` | `Alpha` filter by best_regime=high_volatility |
| `"What have we learned from Phase E?"` | `Failure Registry` query for Phase E experiments |

---

## 11. Integration Architecture

| System | Integration Pattern |
|--------|-------------------|
| Engineering OS | WP completion triggers Knowledge Registration |
| Capability Registry | Capabilities link to producing experiments/validations |
| Work Packages | WP.produces links to IKROS knowledge objects |
| Evidence Records | ERS-1.0 evidence_ids link to IKROS validation nodes |
| Validation Framework | Validation runs create ValidationRun nodes |
| Backtesting | Backtest results create Backtest + Performance nodes |
| Paper Trading | Live simulation creates Decision nodes |
| Repository Metrics | Health scores tracked as operational metrics |
| Alpha Discovery Engine | Future: auto-generates Hypothesis nodes |
| Meta-Research Engine | Future: queries knowledge graph for patterns |
| Causal Research Engine | Future: adds CAUSES edges to graph |
| Explainable AI | Future: Decision → Explanation nodes |

---

## 12. Future Extensibility

| Extension | Description | Priority |
|-----------|-------------|----------|
| Knowledge Graph AI | GNN reasoning over research history | Tier 4 |
| Automatic Literature Review | Semantic search + summarization | Tier 4 |
| Automatic Hypothesis Generation | Generate hypotheses from failure patterns | Tier 3 |
| Automatic Experiment Planning | Prioritize next experiments by expected value | Tier 3 |
| Research Gap Detection | Identify unexplored areas | Tier 3 |
| Knowledge Consolidation | Merge related knowledge into higher-level conclusions | Tier 2 |
| Institutional Research Assistants | LLM interface to knowledge graph | Tier 4 |

---

## 13. IKROS Implementation Plan (WP-IMP-0041 Scope)

**BLOCKED UNTIL ARB APPROVAL OF THIS SPECIFICATION.**

Planned deliverables for WP-IMP-0041:
1. IKROS Architecture Specification (this document — approved)
2. Knowledge Ontology YAML schema
3. Knowledge Graph Design (storage: graph DB or YAML-based DAG)
4. Registry Architecture (13 registries)
5. Memory Architecture implementation
6. Research Lifecycle Specification
7. Lineage Specification
8. Confidence & Uncertainty Model
9. Governance Model
10. Query Architecture
11. Integration Architecture
12. Future Evolution Roadmap

---

## 14. Traceability

Requirements NFR-033 (spec library canonical), NFR-034 (all caps trace to spec),
NFR-035 (spec lifecycle management) in TVM-001.

---

## 15. Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.9.0 | 2026-08-02 | Imported from AFRP-IKROS-ARCH-1.0.0; awaiting ARB approval |
