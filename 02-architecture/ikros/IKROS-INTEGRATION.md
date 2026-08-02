# IKROS Integration Architecture

**Document ID:** AFRP-IKROS-INTEGRATION-1.0.0
**Specification Authority:** SPEC-060 §12 — Integration Architecture
**Work Package:** WP-IMP-0041
**Version:** 1.0.0
**Status:** Draft — Awaiting ARB Approval

---

## 1. Overview

IKROS is an **infrastructure service** that integrates with every AFRP system through well-defined ports and adapters. The integration architecture enforces Clean Architecture boundaries: no Runtime component may directly import IKROS internals.

See **ADR-IKROS-005** for coupling strategy rationale.

---

## 2. Integration Principles

### P-I-1: Ports and Adapters
All integration is through abstract interfaces. IKROS exposes:
- `IKROSWriter` — inbound port for writing research events
- `IKROSReader` — outbound port for querying institutional knowledge
- `IKROSEventBus` — publish/subscribe for knowledge state changes

### P-I-2: No Circular Dependencies
IKROS ← AFRP Systems (one-way)  
AFRP Systems may query IKROS  
IKROS never imports AFRP Runtime internals

### P-I-3: Async-First
All IKROS writes are asynchronous. Research events are queued and processed outside hot paths. IKROS reads may be synchronous for query operations.

### P-I-4: Schema Stability
IKROS integration contracts (IKROSWriter, IKROSReader) are versioned independently. Breaking changes require MAJOR version bump and migration period.

---

## 3. Integration Points

### 3.1 Specification Library Integration

**Direction:** Specification Library → IKROS (reads)

| Integration | Description |
|-------------|-------------|
| Spec-to-Hypothesis mapping | Every approved specification can generate Hypothesis templates |
| Conformance tracking | SPEC-060 requirements map to IKROS capability coverage |
| Spec change propagation | When a spec is revised, dependent KnowledgeObjects are flagged for review |

**Interface:**
```python
class SpecLibraryIKROSAdapter:
    def get_hypotheses_for_spec(self, spec_id: str) -> List[str]: ...
    def register_spec_revision(self, spec_id: str, version: str) -> None: ...
```

### 3.2 Capability Registry Integration

**Direction:** Bidirectional

| Integration | Description |
|-------------|-------------|
| Capability → ResearchQuestion | Each capability links to originating research questions |
| KnowledgeObject → Capability | Institutional knowledge informs future capability design |
| Coverage metrics | IKROS provides research coverage % for each capability |

**Interface:**
```python
class CapabilityRegistryIKROSAdapter:
    def get_research_coverage(self, capability_id: str) -> float: ...
    def link_capability_to_rq(self, capability_id: str, rq_id: str) -> None: ...
```

### 3.3 Work Package Integration

**Direction:** Work Package → IKROS (write on completion)

| Integration | Description |
|-------------|-------------|
| WP completion → Research events | Completed WPs write their research artifacts to IKROS |
| Evidence records → IKROS | ERS-1.0 evidence (EXEC-*.yaml) registered in IKROS |
| Bounded file audit | IKROS enforces that WP outputs match declared scope |

**Interface:**
```python
class WorkPackageIKROSAdapter:
    def register_wp_completion(self, wp_id: str, evidence_path: str) -> None: ...
    def register_research_artifacts(self, wp_id: str, artifacts: List[dict]) -> None: ...
```

### 3.4 Evidence Records Integration

**Direction:** ERS-1.0 → IKROS (write)

Every ERS-1.0 evidence record (EXEC-*.yaml) is registered in IKROS:
- The `Validation` registry stores the quality gate results
- The `Experiment` registry links to the WP that produced it
- The `evidence.ers_records` field on all entities points to the EXEC file

**Schema mapping:**
```
EXEC-*.yaml → IKROS-VAL-* (quality gate validations)
              IKROS-EXP-* (experiment producing this evidence)
```

### 3.5 Backtesting Integration

**Direction:** Backtesting Engine → IKROS (write); IKROS → Backtesting (read)

| Integration | Description |
|-------------|-------------|
| Backtest results → IKROS | All `Backtest`, `WalkForward`, `MonteCarlo` results written to registries |
| Dataset versions → IKROS | Exact data snapshots registered in Dataset Registry |
| Historical knowledge → Backtesting | IKROS provides regime definitions and failure history to guide backtests |

**Interface:**
```python
class BacktestIKROSAdapter:
    def register_backtest_result(self, bt: BacktestResult) -> str: ...  # Returns IKROS-BT-*
    def register_walk_forward(self, wf: WalkForwardResult) -> str: ...
    def get_regime_definitions(self) -> List[dict]: ...
    def get_failure_history(self, strategy_type: str) -> List[dict]: ...
```

**Phase E wiring:** All `11-research/phase-e/*.json` artifacts should be imported into IKROS as the first ingestion operation in WP-IMP-0042.

### 3.6 Paper Trading Integration

**Direction:** Paper Trading → IKROS (write)

| Integration | Description |
|-------------|-------------|
| Paper trading decisions → IKROS | Every `Decision` entity registered in Decision Registry |
| Performance outcomes → IKROS | Outcome PnL updates `C_operational` confidence |
| Policy instances → IKROS | Active trading policies registered in Policy Registry |
| Paper trading Alpha → IKROS | When Alpha enters paper trading, `paper_trading_status` updated |

**Interface:**
```python
class PaperTradingIKROSAdapter:
    def register_decision(self, decision: TradeDecision) -> str: ...
    def update_decision_outcome(self, decision_id: str, pnl: float) -> None: ...
    def update_alpha_paper_status(self, alpha_id: str, status: str) -> None: ...
```

### 3.7 Future Alpha Discovery Integration

**Direction:** Bidirectional

IKROS provides the institutional prior for all future research campaigns:

| IKROS Provides | For Alpha Discovery |
|---------------|-------------------|
| Failure Registry | "Don't try these again without new evidence" |
| KnowledgeObject Registry | "These constraints must be respected" |
| Supported Hypotheses | "These have been validated; build on them" |
| Regime Definitions | "Use these regimes as features" |
| Feature Registry | "Use these validated features" |

**Interface:**
```python
class AlphaDiscoveryIKROSAdapter:
    def get_prior_failures(self, strategy_type: str) -> List[dict]: ...
    def get_institutional_constraints(self) -> List[dict]: ...
    def get_validated_features(self, family: str) -> List[dict]: ...
    def register_new_candidate(self, candidate: AlphaCandidate) -> str: ...
```

### 3.8 Future Meta Research Integration

When meta-research capabilities are implemented:
- IKROS graph becomes the primary data source for meta-learning
- Research patterns extracted from lineage chains
- Confidence model calibration from historical accuracy
- Automatic identification of research gaps

### 3.9 Future Autonomous Research Integration

IKROS is the central hub for autonomous research agents:
- Agents query IKROS for unanswered ResearchQuestions
- Agents register results in real-time via `IKROSWriter`
- Agents receive knowledge updates via `IKROSEventBus`
- IKROS governance gates prevent agents from bypassing quality controls

---

## 4. Event Bus

### 4.1 Event Types

| Event | Publisher | Subscribers |
|-------|-----------|------------|
| `hypothesis.supported` | LifecycleEngine | Alpha Discovery, Backtesting |
| `hypothesis.refuted` | LifecycleEngine | Research Planner |
| `alpha.promoted` | GovernanceGate | Paper Trading |
| `alpha.rejected` | GovernanceGate | Research Planner, Failure Registry |
| `contradiction.detected` | ConflictResolver | ARB Notifier |
| `contradiction.resolved` | ConflictResolver | Affected registries |
| `knowledge.institutionalised` | LifecycleEngine | All subscribers |
| `confidence.degraded` | ConfidenceEngine | Research Planner |
| `failure.recorded` | LifecycleEngine | Institutional Memory |

### 4.2 Event Schema

```yaml
event_id: str             # UUID
event_type: str
timestamp: ISO8601
source_id: IKROS-ID
payload:
  previous_state: str | null
  new_state: str
  confidence_delta: float | null
  metadata: dict
```

---

## 5. API Design (Future Implementation)

When implemented in WP-IMP-0042+, IKROS will expose:

### 5.1 REST API

```
POST /ikros/v1/register/{entity_type}   - Register new entity
GET  /ikros/v1/{entity_type}/{id}       - Fetch entity by ID
PATCH /ikros/v1/{entity_type}/{id}      - Update entity attributes
POST /ikros/v1/{entity_type}/{id}/transition - Lifecycle transition
GET  /ikros/v1/query                    - Institutional query
GET  /ikros/v1/lineage/{id}             - Full lineage chain
GET  /ikros/v1/health                   - IKROS health metrics
```

### 5.2 Python Library

```python
# tools/ikros/__init__.py (future implementation)
from tools.ikros.writer import IKROSWriter
from tools.ikros.reader import IKROSReader
from tools.ikros.models import Hypothesis, Experiment, Validation, ...

# Usage
writer = IKROSWriter()
hyp_id = writer.register_hypothesis(Hypothesis(...))

reader = IKROSReader()
failures = reader.get_failure_history(strategy_type='TREND')
```

---

## 6. Traceability

| Specification Section | Implemented By |
|----------------------|----------------|
| SPEC-060 §12 Integration | This document |
| SPEC-060 §12.1 Spec Library | §3.1 |
| SPEC-060 §12.2 Capability Registry | §3.2 |
| SPEC-060 §12.3 Work Packages | §3.3 |
| SPEC-060 §12.4 Evidence | §3.4 |
| SPEC-060 §12.5 Backtesting | §3.5 |
| SPEC-060 §12.6 Paper Trading | §3.6 |
| SPEC-060 §12.7 Future Alpha | §3.7 |
| SPEC-060 §12.8 Meta Research | §3.8 |
| SPEC-060 §12.9 Autonomous Research | §3.9 |
