# Institutional Research Orchestrator Guide

## Purpose

`tools/ikros/orchestrator/` implements the deterministic Institutional Research Orchestrator for WP-IMP-0048. It coordinates governed research campaigns over existing IKROS subsystems. It does **not** perform autonomous reasoning, natural-language planning, hypothesis generation, or Runtime modification.

## Components

- `models.py` — campaign, pipeline, task, completion report, and hash-chained audit models
- `validation.py` — campaign, task, pipeline, and audit validation
- `persistence.py` — deterministic YAML repositories for campaigns, reports, and audit entries
- `engine.py` — scheduler, dependency resolution, task dispatch, failure handling, completion reporting, and subsystem integration

## Campaign model

A `ResearchCampaign` contains:

- campaign metadata and objective
- one deterministic `ResearchPipeline`
- ordered `ResearchTask` definitions
- lifecycle state (`READY`, `RUNNING`, `FAILED`, `BLOCKED`, `COMPLETED`)
- bounded failure policy (`FAIL_FAST`, `CONTINUE`, `RETRY_ONCE`)
- specification, capability, work-package, and evidence references

Campaign progress is derived from task state and persisted with the campaign and completion report.

## Supported campaign types

- `LITERATURE_REVIEW`
- `HYPOTHESIS_VALIDATION`
- `FEATURE_EVALUATION`
- `DATASET_VALIDATION`
- `BACKTEST_CAMPAIGN`
- `REPLICATION_CAMPAIGN`
- `STRESS_CAMPAIGN`
- `BENCHMARK_CAMPAIGN`
- `RESEARCH_AUDIT`

`ResearchOrchestrator.build_campaign()` can materialize default deterministic pipelines for these campaign types.

## Supported task kinds

- `RESEARCH_QUESTION`
- `LITERATURE_INTAKE`
- `KNOWLEDGE_REGISTRATION`
- `HYPOTHESIS_REGISTRATION`
- `EXPERIMENT_REGISTRATION`
- `DATASET_SELECTION`
- `FEATURE_SELECTION`
- `VALIDATION_REQUEST`
- `STATISTICAL_EVALUATION`
- `CONFIDENCE_UPDATE`
- `BACKTEST_EXECUTION`
- `REPLICATION_EVALUATION`
- `STRESS_EVALUATION`
- `BENCHMARK_EVALUATION`
- `FINAL_REPORT`

Each task consumes structured payloads only. There is no freeform interpretation layer.

## Deterministic scheduling and dependency resolution

The scheduler executes tasks in ascending `(planned_order, task_id)` order once every dependency has completed. Validation rejects cyclic dependency graphs. Downstream tasks are marked `BLOCKED` when a dependency fails and the campaign cannot progress.

Selection tasks rank candidates deterministically by:

1. descending confidence
2. ascending identifier

## Integration surfaces

The orchestrator integrates through existing governed adapters:

- **Research registries** for question, hypothesis, experiment, feature, feature-family, alpha-candidate, and alpha registration
- **Research Ingestion Engine** for literature intake, knowledge registration, and validation/evidence artifact ingestion
- **Research Confidence Engine** for deterministic confidence updates from structured evidence
- **Knowledge Graph** for campaign, task, dependency, and completion-report lineage
- **Research Memory** for task-result and completion-report records
- **Institutional Query Engine** via query-visible graph and memory artifacts
- **Backtest harness** via the existing `07-research/afrp_research/backtest.py` engine, loaded through a bounded adapter

## Backtest, replication, stress, and benchmark execution

The bundled backtest adapter supports:

- `BUY_AND_HOLD`
- `MOVING_AVERAGE_CROSS`

Inputs are explicit price series plus structured config and strategy parameters. The adapter converts them into deterministic AFRP replay observations and returns:

- final equity
- total return
- max drawdown
- Sharpe
- trade count
- replay checksum
- seed

Replication compares the checksum of a rerun against an expected checksum or a baseline task.

## Failure handling

Campaigns support bounded failure handling:

- `FAIL_FAST` stops on the first failed task
- `CONTINUE` keeps executing independent ready tasks
- `RETRY_ONCE` allows a bounded second attempt

`resume_campaign()` resets failed or blocked tasks when attempts remain and continues from persisted state.

## Auditability and completion reporting

Every campaign transition emits a `CampaignAuditEntry` with:

- timestamp
- event type
- actor
- previous and new state
- related task
- output references
- hash chain (`previous_hash`, `entry_hash`)

Every run also produces a `CampaignCompletionReport` plus a T4 institutional memory record.

## Query and memory visibility

Completed campaign artifacts are visible through:

- graph nodes for campaigns, tasks, and completion reports
- episodic task-result memory records
- institutional completion-report memory records

This allows deterministic retrieval through the Institutional Query Engine without adding a separate natural-language interface.

## Limitations

- No LLMs
- No autonomous planning
- No semantic search
- No Runtime execution changes
- No direct trading logic
- Backtest execution is intentionally bounded to the existing deterministic research harness and supported benchmark strategies
