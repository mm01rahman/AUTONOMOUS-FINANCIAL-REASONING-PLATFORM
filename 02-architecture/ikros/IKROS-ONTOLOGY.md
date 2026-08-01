# IKROS Knowledge Ontology

**Document ID:** AFRP-IKROS-ONTOLOGY-1.0.0
**Specification Authority:** SPEC-060 §3 — Institutional Ontology
**Work Package:** WP-IMP-0041
**Version:** 1.0.0
**Status:** Draft — Awaiting ARB Approval

---

## 1. Overview

The IKROS Knowledge Ontology defines all first-class research objects managed by IKROS. Every entity has governed attributes, versioning, lifecycle, and ownership.

The ontology uses a **typed entity model** where:
- Every entity has a unique `ikros_id` following `IKROS-{TYPE}-{YYYYMMDD}-{SEQ:04d}`
- Every entity has explicit `lifecycle_state` from the governed state machine
- Every entity has `confidence_score` (0.0–1.0) representing current epistemic certainty
- All relationships are typed and carry temporal validity intervals `[valid_from, valid_to)`

---

## 2. Entity Catalogue

### 2.1 ResearchQuestion

**Purpose:** A formal question motivating a research campaign. The root node of every research lineage.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-RQ-YYYYMMDD-NNNN` |
| `title` | String | Concise question statement |
| `motivation` | Text | Market observation triggering this question |
| `scope` | Enum | `MICRO`, `MACRO`, `REGIME`, `STRUCTURAL` |
| `instrument` | String | e.g., `XAU/USD` |
| `time_horizon` | String | e.g., `1H`, `1D`, `1W` |
| `status` | Enum | `OPEN`, `ACTIVE`, `ANSWERED`, `RETIRED` |
| `created_at` | ISO8601 | Creation timestamp |
| `created_by` | String | Agent or analyst ID |
| `version` | SemVer | Document version |
| `confidence_score` | Float[0,1] | Current answer confidence |

**Relationships:**
- `MOTIVATED_BY` → MarketEvent (what observation led to this question)
- `INFORMED_BY` → Literature (prior work)
- `DECOMPOSED_INTO` → ResearchQuestion (sub-questions)
- `ANSWERED_BY` → ResearchConclusion
- `GENERATED` → Hypothesis (one-to-many)

**Lifecycle:** `DRAFT` → `ACTIVE` → `ANSWERED` → `RETIRED`

---

### 2.2 EconomicThesis

**Purpose:** A macro-level causal narrative connecting economic conditions to asset price behaviour.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-THESIS-YYYYMMDD-NNNN` |
| `title` | String | Thesis name |
| `causal_chain` | Text | Narrative: cause → mechanism → prediction |
| `regime_conditions` | List[String] | Market regimes where thesis applies |
| `supporting_evidence` | List[IKROS-ID] | Evidence IDs |
| `contradicting_evidence` | List[IKROS-ID] | Contradiction IDs |
| `confidence_score` | Float[0,1] | Overall thesis confidence |
| `status` | Enum | `PROPOSED`, `SUPPORTED`, `REFUTED`, `CONTESTED`, `RETIRED` |

**Relationships:**
- `SUPPORTS` → Hypothesis
- `CONTRADICTED_BY` → ContradictoryEvidence
- `REFERENCES` → Literature
- `APPLIES_IN` → Regime

**Lifecycle:** `PROPOSED` → `UNDER_REVIEW` → `SUPPORTED` | `REFUTED` | `CONTESTED` → `RETIRED`

---

### 2.3 Literature

**Purpose:** External published research, academic papers, industry reports, or data vendor documentation.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-LIT-YYYYMMDD-NNNN` |
| `title` | String | Publication title |
| `authors` | List[String] | Author list |
| `publication_date` | Date | Original publication date |
| `source` | String | Journal, conference, or source |
| `doi_or_url` | String | Permanent reference |
| `abstract` | Text | Summary |
| `relevance_tags` | List[String] | Topic tags |
| `ingested_at` | ISO8601 | When IKROS registered this |
| `quality_score` | Float[0,1] | Assessed methodological quality |

**Relationships:**
- `CITED_BY` → Hypothesis, EconomicThesis, ResearchConclusion
- `CONTRADICTS` → Literature (when findings conflict)
- `EXTENDS` → Literature (when building on prior work)

**Lifecycle:** `INGESTED` → `REVIEWED` → `REFERENCED` → `SUPERSEDED` | `ARCHIVED`

---

### 2.4 Dataset

**Purpose:** A versioned collection of market data used in research.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-DS-YYYYMMDD-NNNN` |
| `name` | String | Canonical dataset name |
| `instrument` | String | e.g., `XAU/USD` |
| `frequency` | String | e.g., `M1`, `H1`, `D1` |
| `date_range` | DateRange | `[start, end)` |
| `row_count` | Integer | Number of rows |
| `source` | String | Data vendor or exchange |
| `hash_sha256` | String | Content hash for integrity |
| `schema_version` | String | Column schema version |
| `quality_grade` | Enum | `A`, `B`, `C`, `UNVERIFIED` |
| `current_version` | String | Pointer to current DatasetVersion |

**Relationships:**
- `HAS_VERSION` → DatasetVersion (one-to-many)
- `DERIVED_FROM` → Dataset (for derived datasets)
- `USED_IN` → Experiment (many-to-many)

**Lifecycle:** `REGISTERED` → `VALIDATED` → `ACTIVE` → `DEPRECATED` → `ARCHIVED`

---

### 2.5 DatasetVersion

**Purpose:** An immutable snapshot of a Dataset at a specific point in time.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-DSV-YYYYMMDD-NNNN` |
| `dataset_id` | IKROS-ID | Parent dataset |
| `version` | String | Semantic version |
| `created_at` | ISO8601 | Snapshot timestamp |
| `hash_sha256` | String | Immutable content hash |
| `row_count` | Integer | Rows in this version |
| `change_summary` | Text | What changed from prior version |

**Relationships:**
- `VERSION_OF` → Dataset
- `SUPERSEDES` → DatasetVersion (previous version)

**Lifecycle:** `CREATED` → `ACTIVE` → `SUPERSEDED` → `ARCHIVED`

---

### 2.6 Feature

**Purpose:** A derived input signal computed from raw market data.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-FEAT-YYYYMMDD-NNNN` |
| `name` | String | Canonical feature name |
| `family` | String | Pointer to FeatureFamily |
| `computation` | Text | Mathematical or algorithmic definition |
| `inputs` | List[String] | Raw columns or parent features |
| `lookback` | String | Required history window |
| `normalization` | String | Normalization method |
| `stationarity` | Enum | `STATIONARY`, `NON_STATIONARY`, `UNKNOWN` |
| `information_content` | Float | Estimated mutual information with target |
| `stability_score` | Float[0,1] | Cross-regime stability |
| `version` | SemVer | Feature definition version |

**Relationships:**
- `MEMBER_OF` → FeatureFamily
- `COMPUTED_FROM` → Dataset, Feature (inputs)
- `USED_IN` → Experiment, Model
- `SUPERSEDED_BY` → Feature

**Lifecycle:** `DRAFT` → `VALIDATED` → `ACTIVE` → `DEPRECATED` → `RETIRED`

---

### 2.7 FeatureFamily

**Purpose:** A named group of related features sharing common theoretical motivation.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-FF-YYYYMMDD-NNNN` |
| `name` | String | e.g., `MICROSTRUCTURE`, `REGIME`, `MACRO` |
| `description` | Text | Theoretical basis |
| `feature_count` | Integer | Number of member features |
| `average_information_content` | Float | Family-level information summary |

**Relationships:**
- `CONTAINS` → Feature (one-to-many)
- `ALIGNED_WITH` → EconomicThesis

---

### 2.8 Factor

**Purpose:** A persistent, economically-motivated driver of returns with cross-instrument evidence.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-FACTOR-YYYYMMDD-NNNN` |
| `name` | String | e.g., `GOLD_INFLATION_HEDGE` |
| `economic_motivation` | Text | Why this factor should earn premium |
| `persistence_score` | Float[0,1] | Evidence of multi-regime persistence |
| `replication_count` | Integer | Number of independent replications |
| `last_validated_at` | ISO8601 | Most recent validation timestamp |

**Relationships:**
- `IMPLEMENTED_BY` → Feature (features that proxy this factor)
- `SUPPORTED_BY` → Literature, Validation
- `CAPTURED_IN` → Alpha

---

### 2.9 Hypothesis

**Purpose:** A testable, falsifiable prediction about market behaviour.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-HYP-YYYYMMDD-NNNN` |
| `statement` | Text | Precise, falsifiable prediction |
| `null_hypothesis` | Text | H₀ that experiments attempt to reject |
| `alternative_hypothesis` | Text | H₁ |
| `significance_level` | Float | Alpha threshold (e.g., 0.05) |
| `power` | Float | Statistical power target |
| `prior_confidence` | Float[0,1] | Confidence before evidence |
| `posterior_confidence` | Float[0,1] | Confidence after evidence |
| `status` | Enum | `PROPOSED`, `TESTING`, `SUPPORTED`, `REFUTED`, `INCONCLUSIVE`, `RETIRED` |
| `version` | SemVer | Hypothesis version |

**Relationships:**
- `GENERATED_FROM` → ResearchQuestion
- `MOTIVATED_BY` → EconomicThesis
- `TESTED_BY` → Experiment (one-to-many)
- `SUPPORTED_BY` → Validation
- `CONTRADICTED_BY` → ContradictoryEvidence
- `REFINED_INTO` → Hypothesis (successor)

**Lifecycle:** `PROPOSED` → `UNDER_REVIEW` → `APPROVED_FOR_TESTING` → `TESTING` → `SUPPORTED` | `REFUTED` | `INCONCLUSIVE` → `RETIRED`

---

### 2.10 Experiment

**Purpose:** A governed research execution that tests one or more hypotheses.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-EXP-YYYYMMDD-NNNN` |
| `title` | String | Experiment name |
| `hypotheses` | List[IKROS-ID] | Hypotheses under test |
| `protocol` | Text | Methodology description |
| `dataset_versions` | List[IKROS-ID] | Exact dataset versions used |
| `feature_versions` | List[IKROS-ID] | Features used |
| `parameters` | Map | All parameter values |
| `random_seed` | Integer | For reproducibility |
| `in_sample_range` | DateRange | IS period |
| `out_of_sample_range` | DateRange | OOS period |
| `status` | Enum | `DESIGNED`, `RUNNING`, `COMPLETE`, `FAILED`, `INVALIDATED` |
| `reproducibility_hash` | String | Hash of all inputs for exact replay |

**Relationships:**
- `TESTS` → Hypothesis
- `USES` → DatasetVersion, Feature
- `PRODUCES` → Validation, Failure
- `PART_OF` → ResearchQuestion lineage

**Lifecycle:** `DESIGNED` → `APPROVED` → `RUNNING` → `COMPLETE` | `FAILED` → `REVIEWED` → `ARCHIVED` | `INVALIDATED`

---

### 2.11 Validation

**Purpose:** A formal evidence record confirming or rejecting a hypothesis or model.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-VAL-YYYYMMDD-NNNN` |
| `experiment_id` | IKROS-ID | Source experiment |
| `verdict` | Enum | `PASS`, `FAIL`, `INCONCLUSIVE` |
| `method` | Enum | `STATISTICAL`, `WALK_FORWARD`, `MONTE_CARLO`, `STRESS_TEST`, `REGIME_ANALYSIS` |
| `metric_results` | Map | All computed metrics |
| `p_value` | Float | Statistical significance |
| `effect_size` | Float | Practical significance |
| `confidence_interval` | Tuple[Float, Float] | 95% CI |
| `overfitting_score` | Float[0,1] | 0 = no overfitting |
| `regime_stability` | Float[0,1] | Cross-regime consistency |

**Relationships:**
- `VALIDATES` → Hypothesis, Model, Alpha
- `PRODUCED_BY` → Experiment
- `LINKED_TO` → EvidenceRecord (ERS-1.0)

---

### 2.12 Model

**Purpose:** A trained predictive model mapping features to signals.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-MODEL-YYYYMMDD-NNNN` |
| `architecture` | String | Model type (e.g., `GRADIENT_BOOST`, `LSTM`, `ENSEMBLE`) |
| `features_used` | List[IKROS-ID] | Feature IDs |
| `training_dataset` | IKROS-ID | DatasetVersion used |
| `hyperparameters` | Map | All hyperparameter values |
| `training_hash` | String | Reproducibility hash |
| `in_sample_metrics` | Map | Training performance |
| `out_of_sample_metrics` | Map | Validation performance |
| `sharpe_is` | Float | In-sample Sharpe |
| `sharpe_oos` | Float | Out-of-sample Sharpe |
| `max_drawdown` | Float | Maximum drawdown |
| `overfitting_index` | Float | `sharpe_is / sharpe_oos` (1.0 = ideal) |

**Relationships:**
- `TRAINED_ON` → DatasetVersion
- `USES` → Feature
- `VALIDATED_BY` → Validation
- `INCORPORATED_IN` → Alpha, WorldModel
- `SUPERSEDED_BY` → Model

**Lifecycle:** `TRAINED` → `VALIDATED` → `APPROVED` | `REJECTED` → `ACTIVE` | `DEPRECATED` → `RETIRED`

---

### 2.13 WorldModel

**Purpose:** A holistic probabilistic belief state about market conditions, regimes, and dynamics.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-WM-YYYYMMDD-NNNN` |
| `regime_beliefs` | Map[Regime, Float] | Probability distribution over regimes |
| `volatility_estimate` | Float | Current volatility estimate |
| `trend_estimate` | Float | Current trend estimate |
| `liquidity_estimate` | Float | Current liquidity estimate |
| `macro_state` | Map | Key macro indicator estimates |
| `uncertainty_total` | Float | Total world model uncertainty |
| `valid_from` | ISO8601 | Temporal validity start |
| `valid_to` | ISO8601 | Temporal validity end |

**Relationships:**
- `INFORMS` → Decision, Policy
- `INCORPORATES` → Model
- `CONDITIONED_ON` → Regime

---

### 2.14 Decision

**Purpose:** A governed trading decision produced by the AFRP Decision Engine.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-DEC-YYYYMMDD-NNNN` |
| `signal` | Float | Normalised signal (-1 to +1) |
| `direction` | Enum | `LONG`, `SHORT`, `FLAT` |
| `confidence` | Float[0,1] | Decision confidence |
| `rationale` | Text | Explainability narrative |
| `world_model_id` | IKROS-ID | WorldModel used |
| `policy_id` | IKROS-ID | Policy governing this decision |
| `timestamp` | ISO8601 | Decision timestamp |
| `outcome` | Enum | `PROFITABLE`, `LOSS`, `FLAT`, `UNKNOWN` |
| `outcome_pnl` | Float | Realised PnL |

**Relationships:**
- `PRODUCED_BY` → Policy
- `INFORMED_BY` → WorldModel
- `GOVERNED_BY` → Policy
- `PART_OF` → Alpha (contributes to alpha track record)

---

### 2.15 Policy

**Purpose:** A governed set of rules or learned strategy controlling decision-making.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-POL-YYYYMMDD-NNNN` |
| `policy_type` | Enum | `RULE_BASED`, `LEARNED`, `HYBRID` |
| `rules` | List | Rule definitions |
| `model_id` | IKROS-ID | Associated model (if learned) |
| `risk_constraints` | Map | Risk limit definitions |
| `approval_status` | Enum | `DRAFT`, `APPROVED`, `ACTIVE`, `SUSPENDED`, `RETIRED` |
| `approved_by` | String | ARB approval reference |

**Relationships:**
- `GOVERNS` → Decision
- `IMPLEMENTS` → Alpha
- `VALIDATED_BY` → Validation

---

### 2.16 Backtest

**Purpose:** A historical simulation of a strategy against past data.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-BT-YYYYMMDD-NNNN` |
| `strategy_id` | IKROS-ID | Alpha or Policy under test |
| `dataset_version` | IKROS-ID | Exact data snapshot |
| `start_date` | Date | Simulation start |
| `end_date` | Date | Simulation end |
| `sharpe_ratio` | Float | Annualised Sharpe |
| `max_drawdown` | Float | Maximum drawdown (%) |
| `total_return` | Float | Total return (%) |
| `win_rate` | Float | Fraction of profitable trades |
| `direction_accuracy` | Float | Fraction of correct directional calls |
| `transaction_costs` | Float | Assumed per-trade cost |
| `slippage_model` | String | Slippage assumption |

**Relationships:**
- `EVALUATES` → Alpha, Policy
- `USES` → DatasetVersion
- `PRODUCES` → Validation

---

### 2.17 WalkForward

**Purpose:** A walk-forward validation splitting data into rolling IS/OOS windows.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-WF-YYYYMMDD-NNNN` |
| `parent_experiment` | IKROS-ID | Containing experiment |
| `window_count` | Integer | Number of WF windows |
| `is_window_size` | String | In-sample window size |
| `oos_window_size` | String | Out-of-sample window size |
| `mean_oos_sharpe` | Float | Average OOS Sharpe |
| `sharpe_degradation` | Float | IS vs OOS Sharpe ratio |
| `consistency_score` | Float[0,1] | Fraction of positive OOS windows |

**Relationships:**
- `VALIDATES` → Model, Alpha
- `PART_OF` → Experiment

---

### 2.18 StressTest

**Purpose:** A performance evaluation under adverse or extreme market conditions.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-STRESS-YYYYMMDD-NNNN` |
| `scenario` | String | Stress scenario name |
| `scenario_description` | Text | What conditions are being simulated |
| `max_drawdown_under_stress` | Float | Drawdown under stress |
| `recovery_time` | String | Estimated recovery duration |
| `passed` | Boolean | Whether strategy survived |

---

### 2.19 MonteCarlo

**Purpose:** A statistical significance test via bootstrap simulation.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-MC-YYYYMMDD-NNNN` |
| `simulation_count` | Integer | Number of Monte Carlo runs |
| `sharpe_distribution` | Map | Mean, std, percentiles |
| `p_value` | Float | Probability of achieving this Sharpe by chance |
| `significance_level` | Float | Threshold used |
| `passed` | Boolean | `p_value < significance_level` |

---

### 2.20 Regime

**Purpose:** A labelled market regime characterised by distinct statistical properties.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-REGIME-YYYYMMDD-NNNN` |
| `name` | String | e.g., `RISK_OFF`, `INFLATION`, `TRENDING`, `MEAN_REVERTING` |
| `characteristics` | Map | Defining statistical properties |
| `detection_features` | List[IKROS-ID] | Features used to detect this regime |
| `historical_occurrences` | List[DateRange] | Known historical periods |
| `transition_probabilities` | Map[Regime, Float] | Markov transition matrix |

**Relationships:**
- `DETECTED_BY` → Feature
- `AFFECTS` → Alpha, Model performance
- `PART_OF` → WorldModel beliefs

---

### 2.21 MarketEvent

**Purpose:** A significant discrete market event with lasting institutional significance.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-EVENT-YYYYMMDD-NNNN` |
| `name` | String | Event name |
| `category` | Enum | `MACRO`, `GEOPOLITICAL`, `POLICY`, `CRISIS`, `STRUCTURAL` |
| `date` | Date | Event date |
| `impact_summary` | Text | Observed market impact |
| `gold_impact` | Float | XAU/USD price change (%) |
| `regime_change` | Boolean | Whether this triggered a regime transition |

**Relationships:**
- `TRIGGERED` → Regime transition
- `MOTIVATES` → ResearchQuestion
- `REFERENCED_IN` → EconomicThesis

---

### 2.22 AlphaCandidate

**Purpose:** A strategy that has completed research but has NOT yet met promotion criteria.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-ALPHACAND-YYYYMMDD-NNNN` |
| `name` | String | Strategy name |
| `strategy_type` | Enum | `TREND`, `MEAN_REVERSION`, `LIQUIDITY`, `MACRO`, `HYBRID` |
| `sharpe_oos` | Float | Out-of-sample Sharpe |
| `max_drawdown` | Float | Maximum drawdown |
| `direction_accuracy` | Float | Directional accuracy |
| `promotion_score` | Float[0,1] | Weighted promotion score |
| `promotion_status` | Enum | `CANDIDATE`, `PROMOTED`, `REJECTED`, `RETIRED` |
| `rejection_reasons` | List[String] | Why promotion was refused |

**Relationships:**
- `EVALUATED_IN` → Backtest, WalkForward, MonteCarlo
- `IMPLEMENTS` → Hypothesis
- `PROMOTED_TO` → Alpha (if promoted)

---

### 2.23 Alpha

**Purpose:** A strategy that has passed all promotion criteria and is approved for paper trading.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-ALPHA-YYYYMMDD-NNNN` |
| `promoted_from` | IKROS-ID | AlphaCandidate ID |
| `promotion_date` | Date | ARB approval date |
| `min_sharpe_threshold` | Float | Promotion threshold met |
| `paper_trading_status` | Enum | `NOT_STARTED`, `ACTIVE`, `COMPLETED`, `FAILED` |
| `live_eligible` | Boolean | Whether live deployment is permitted |

**Relationships:**
- `PROMOTED_FROM` → AlphaCandidate
- `TRACKED_IN` → Backtest, PaperTrading
- `IMPLEMENTED_BY` → Policy

---

### 2.24 Failure

**Purpose:** A governed record of a research failure, stored permanently as institutional memory.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-FAIL-YYYYMMDD-NNNN` |
| `failed_object_id` | IKROS-ID | What failed |
| `failure_type` | Enum | `STATISTICAL`, `ECONOMIC`, `OVERFITTING`, `DATA_QUALITY`, `REGIME_INSTABILITY` |
| `failure_description` | Text | What went wrong |
| `root_cause` | Text | Causal analysis |
| `lessons_learned` | Text | Institutional knowledge extracted |
| `prevents_repetition` | Text | How this failure prevents future repetition |
| `created_at` | ISO8601 | When failure was recorded |

**Relationships:**
- `RECORDS_FAILURE_OF` → Experiment, Model, AlphaCandidate
- `GENERATES` → KnowledgeObject (lessons)
- `MOTIVATES` → ResearchQuestion (follow-up research)

**Lifecycle:** `RECORDED` → `ANALYSED` → `INSTITUTIONALISED` (permanent)

> **IMPORTANT:** Failure records are IMMUTABLE and PERMANENT. They cannot be deleted or superseded, only supplemented.

---

### 2.25 ContradictoryEvidence

**Purpose:** Evidence that directly contradicts an existing belief, hypothesis, or conclusion.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-CONTRA-YYYYMMDD-NNNN` |
| `contradicts` | IKROS-ID | Object being contradicted |
| `evidence_type` | Enum | `STATISTICAL`, `EMPIRICAL`, `THEORETICAL`, `REPLICATION_FAILURE` |
| `evidence_description` | Text | Nature of the contradiction |
| `severity` | Enum | `MINOR`, `MODERATE`, `MAJOR`, `INVALIDATING` |
| `resolution_status` | Enum | `OPEN`, `UNDER_INVESTIGATION`, `RESOLVED`, `ACCEPTED_CONTRADICTION` |
| `resolution_notes` | Text | How contradiction was resolved |

**Relationships:**
- `CONTRADICTS` → Hypothesis, EconomicThesis, ResearchConclusion, Alpha
- `RESOLVED_BY` → Validation, ResearchConclusion
- `GENERATED_BY` → Experiment

---

### 2.26 ResearchConclusion

**Purpose:** A governed, approved statement of what was learned from a research campaign.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-CONCL-YYYYMMDD-NNNN` |
| `statement` | Text | Precise conclusion |
| `confidence` | Float[0,1] | Conclusion confidence |
| `supporting_evidence` | List[IKROS-ID] | All supporting artifacts |
| `contradicting_evidence` | List[IKROS-ID] | Known contradictions |
| `scope` | Text | Conditions under which conclusion holds |
| `limitations` | Text | Known limitations |
| `approval_status` | Enum | `DRAFT`, `APPROVED`, `SUPERSEDED`, `RETIRED` |

**Relationships:**
- `ANSWERS` → ResearchQuestion
- `GENERATED_FROM` → Experiment, Validation
- `SUPERSEDED_BY` → ResearchConclusion

**Lifecycle:** `DRAFT` → `PEER_REVIEW` → `APPROVED` → `INSTITUTIONALISED` → `SUPERSEDED` | `RETIRED`

---

### 2.27 KnowledgeObject

**Purpose:** A distilled, reusable piece of institutional knowledge extracted from research.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `ikros_id` | String | `IKROS-KO-YYYYMMDD-NNNN` |
| `title` | String | Knowledge object title |
| `content` | Text | The knowledge statement |
| `category` | Enum | `PATTERN`, `PRINCIPLE`, `CONSTRAINT`, `HEURISTIC`, `ANOMALY` |
| `applicability` | Text | When and where this applies |
| `confidence` | Float[0,1] | Overall confidence |
| `replication_count` | Integer | Times independently confirmed |
| `last_validated` | ISO8601 | Most recent validation |

**Relationships:**
- `EXTRACTED_FROM` → ResearchConclusion, Failure
- `REFERENCES` → Hypothesis, Alpha, Factor
- `APPLIED_IN` → Experiment, Policy

**Lifecycle:** `EXTRACTED` → `VALIDATED` → `INSTITUTIONALISED` → `MONITORING` → `RETIRED`

---

## 3. Entity Summary

| Entity | IKROS Type Code | Count (Phase E) |
|--------|----------------|----------------|
| ResearchQuestion | `RQ` | 1 |
| EconomicThesis | `THESIS` | 3 |
| Literature | `LIT` | 0 (pending import) |
| Dataset | `DS` | 2 |
| DatasetVersion | `DSV` | 4 |
| Feature | `FEAT` | 47 |
| FeatureFamily | `FF` | 9 |
| Factor | `FACTOR` | 6 |
| Hypothesis | `HYP` | 6 |
| Experiment | `EXP` | 6 |
| Validation | `VAL` | 18 |
| Model | `MODEL` | 6 |
| WorldModel | `WM` | 0 |
| Decision | `DEC` | 0 |
| Policy | `POL` | 0 |
| Backtest | `BT` | 6 |
| WalkForward | `WF` | 6 |
| StressTest | `STRESS` | 0 |
| MonteCarlo | `MC` | 6 |
| Regime | `REGIME` | 4 |
| MarketEvent | `EVENT` | 0 |
| AlphaCandidate | `ALPHACAND` | 6 |
| Alpha | `ALPHA` | 0 (none promoted) |
| Failure | `FAIL` | 6 |
| ContradictoryEvidence | `CONTRA` | 0 |
| ResearchConclusion | `CONCL` | 1 |
| KnowledgeObject | `KO` | 6 |

**Total entities to initialise from Phase E:** ~127

---

## 4. Ontology Constraints

1. Every entity MUST have a valid `ikros_id` matching the canonical pattern
2. Every entity MUST have a `lifecycle_state` consistent with its lifecycle definition
3. Every relationship MUST carry `valid_from` timestamp
4. `Failure` entities MUST NOT be deleted or superseded
5. `AlphaCandidate` with `promotion_status: REJECTED` must have non-empty `rejection_reasons`
6. `ResearchConclusion` MUST reference at least one `Validation` as supporting evidence
7. `Hypothesis` `posterior_confidence` MUST be updated after each validating `Experiment`
8. `ContradictoryEvidence` with `severity: INVALIDATING` MUST trigger ARB review

---

## 5. Traceability

| Specification Section | Implemented By |
|----------------------|----------------|
| SPEC-060 §3 Ontology | This document |
| SPEC-060 §3.1 Entities | §2 Entity Catalogue |
| SPEC-060 §3.2 Relationships | §2 Relationships per entity |
| SPEC-060 §3.3 Versioning | §2 Lifecycle per entity |
