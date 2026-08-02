"""Unit tests for the IKROS Institutional Research Orchestrator."""

from __future__ import annotations

import textwrap
from pathlib import Path

from tools.ikros.confidence import (
    ConfidenceEvidence,
    ConfidenceEvidenceType,
    EvidenceReferences,
    EvidenceRelation,
)
from tools.ikros.graph import GraphNode, NodeType
from tools.ikros.memory import MemoryQuery
from tools.ikros.models import (
    ConfidenceVector,
    Feature,
    Hypothesis,
    HypothesisStatus,
    LineageDependencies,
    LineageEvidence,
    LineageOrigin,
    LineageRecord,
    ResearchQuestion,
    ResearchStatus,
    Stationarity,
)
from tools.ikros.orchestrator import (
    CampaignLifecycleState,
    CampaignType,
    FailurePolicy,
    ResearchCampaign,
    ResearchOrchestrator,
    ResearchPipeline,
    ResearchTask,
    TaskKind,
    validate_campaign,
)


def _origin(context: str) -> LineageOrigin:
    return LineageOrigin(
        created_by="orchestrator-test",
        created_at="2026-08-02T00:00:00Z",
        creation_context=context,
        motivation="wp48 deterministic fixture",
    )


def _confidence(level: float) -> ConfidenceVector:
    return ConfidenceVector(
        prior=max(level - 0.10, 0.0),
        statistical=level,
        economic=max(level - 0.05, 0.0),
        data=level,
        model=level,
        validation=max(level - 0.02, 0.0),
        replication=max(level - 0.08, 0.0),
        operational=max(level - 0.10, 0.0),
    )


def _research_question(ikros_id: str = "IKROS-RQ-20260802-0001") -> ResearchQuestion:
    return ResearchQuestion(
        ikros_id=ikros_id,
        entity_type="ResearchQuestion",
        version="1.0.0",
        lifecycle_state=ResearchStatus.OPEN.value,
        confidence=_confidence(0.55),
        lineage=LineageRecord(origin=_origin("wp48-rq")),
        title="Does governed orchestration preserve research traceability?",
        instrument="XAU/USD",
        scope="MACRO",
        time_horizon="1D",
        campaign_tag="WP48",
        motivation="Institutional research orchestration",
    )


def _hypothesis(ikros_id: str = "IKROS-HYP-20260802-0001") -> Hypothesis:
    return Hypothesis(
        ikros_id=ikros_id,
        entity_type="Hypothesis",
        version="1.0.0",
        lifecycle_state=HypothesisStatus.PROPOSED.value,
        confidence=_confidence(0.42),
        lineage=LineageRecord(
            origin=_origin("wp48-hyp"),
            dependencies=LineageDependencies(inputs=["IKROS-RQ-20260802-0001"]),
            evidence=LineageEvidence(ers_records=["EXEC-050"]),
        ),
        spec_refs=["SPEC-060"],
        capability_refs=["IKROS-ORCHESTRATOR"],
        work_package_refs=["WP-IMP-0048"],
        statement="Governed validation artifacts should increase institutional confidence.",
        null_hypothesis="H0: Validation artifacts do not increase confidence.",
        alternative_hypothesis="H1: Validation artifacts increase confidence.",
        significance_level=0.05,
        power=0.80,
        prior_confidence=0.35,
        source_rq="IKROS-RQ-20260802-0001",
    )


def _feature(ikros_id: str = "IKROS-FEAT-20260802-0001") -> Feature:
    return Feature(
        ikros_id=ikros_id,
        entity_type="Feature",
        version="1.0.0",
        lifecycle_state="ACTIVE",
        confidence=_confidence(0.73),
        lineage=LineageRecord(
            origin=_origin("wp48-feature"),
            dependencies=LineageDependencies(inputs=["close"]),
        ),
        name="regime_persistence_feature",
        family_id="IKROS-FF-20260802-0001",
        computation="close.diff().rolling(5).mean()",
        inputs=["close"],
        lookback="5 bars",
        normalization="z-score",
        stationarity=Stationarity.STATIONARY.value,
        information_content=0.41,
        stability_score=0.77,
    )


def _supporting_evidence() -> list[dict[str, object]]:
    evidence = ConfidenceEvidence(
        evidence_id="EVID-VAL-001",
        evidence_type=ConfidenceEvidenceType.VALIDATION,
        relation=EvidenceRelation.SUPPORTS,
        references=EvidenceReferences(
            specification_ids=["SPEC-060"],
            validation_ids=["IKROS-VAL-20260802-0001"],
            work_package_ids=["WP-IMP-0048"],
            capability_ids=["IKROS-ORCHESTRATOR"],
            evidence_record_ids=["EXEC-050"],
        ),
        confidence_weight=1.0,
        independent_source="qa-desk",
        temporal_bucket="2026Q3",
        observed_at="2026-08-02T00:00:00Z",
        metrics={
            "p_value": 0.02,
            "consistency_score": 0.86,
            "sharpe_degradation": 0.08,
            "verdict": "PASS",
            "oos_confirmed": True,
        },
    )
    return [evidence.to_dict()]


def _write_validation_record(path: Path) -> Path:
    path.write_text(
        textwrap.dedent(
            """
            schema_version: "ERS-1.0"
            evidence_id: "EXEC-050"
            work_package_id: "WP-IMP-0048"
            capability:
              id: "IKROS-ORCHESTRATOR"
            quality_gates:
              - gate: "pytest"
                result: "PASS"
              - gate: "afrp health"
                result: "PASS"
            verdict:
              all_gates_passed: true
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return path


def _campaign(
    *,
    campaign_id: str,
    title: str,
    tasks: list[ResearchTask],
    failure_policy: str = FailurePolicy.FAIL_FAST.value,
    campaign_type: str = CampaignType.HYPOTHESIS_VALIDATION.value,
) -> ResearchCampaign:
    return ResearchCampaign(
        campaign_id=campaign_id,
        campaign_type=campaign_type,
        title=title,
        objective="Deterministic orchestration test",
        pipeline=ResearchPipeline(
            pipeline_id=campaign_id.replace("RESEARCHCAMPAIGN", "RESEARCHPIPELINE"),
            name=f"{title} pipeline",
            stages=[task.kind for task in tasks],
            task_ids=[task.task_id for task in tasks],
        ),
        tasks=tasks,
        lifecycle_state=CampaignLifecycleState.READY.value,
        failure_policy=failure_policy,
    )


class TestResearchOrchestrator:
    def test_backtest_campaign_runs_to_completion_and_is_query_visible(
        self,
        tmp_path: Path,
    ) -> None:
        orchestrator = ResearchOrchestrator(base_dir=tmp_path / "ikros")
        campaign = orchestrator.build_campaign(
            title="Governed backtest campaign",
            objective="Replay deterministic benchmark under orchestration",
            campaign_type=CampaignType.BACKTEST_CAMPAIGN.value,
            task_payloads={
                TaskKind.RESEARCH_QUESTION.value: {
                    "entity_type": "ResearchQuestion",
                    "entity": _research_question().to_dict(),
                },
                TaskKind.BACKTEST_EXECUTION.value: {
                    "prices": [100.0, 102.0, 105.0],
                    "strategy": "BUY_AND_HOLD",
                    "config": {"fee_bps": 0.0, "slippage_bps": 0.0},
                },
                TaskKind.STATISTICAL_EVALUATION.value: {
                    "p_value": 0.03,
                    "effect_size": 0.42,
                    "consistency_score": 0.83,
                    "sharpe_degradation": 0.06,
                    "overfitting_index": 1.05,
                    "data_quality_grade": "A",
                },
            },
            failure_policy=FailurePolicy.FAIL_FAST.value,
        )

        orchestrator.register_campaign(campaign)
        report = orchestrator.run_campaign(campaign.campaign_id)

        assert report.lifecycle_state == CampaignLifecycleState.COMPLETED.value
        assert report.progress["completed"] == 4
        assert report.output_refs
        query = orchestrator.build_query_engine().execute(
            f"GET ENTITY {report.memory_record_ids[-1]}"
        )
        assert {item.source for item in query.results} == {"memory"}
        task_memories = orchestrator._memory.retrieve(
            MemoryQuery(entity_type="ResearchTaskResult")
        )
        assert len(task_memories) == 4
        audit_entries = orchestrator._audit_log.list_entries()
        assert len(audit_entries) >= 6
        for previous, current in zip(audit_entries, audit_entries[1:], strict=False):
            if previous.campaign_id == current.campaign_id:
                assert current.previous_hash == previous.entry_hash

    def test_campaign_integrates_validation_ingestion_and_confidence_update(
        self,
        tmp_path: Path,
    ) -> None:
        orchestrator = ResearchOrchestrator(base_dir=tmp_path / "ikros")
        hypothesis = _hypothesis()
        orchestrator._registries["Hypothesis"].register(hypothesis)
        orchestrator._graph.add_node(
            GraphNode(
                node_id=hypothesis.ikros_id,
                node_type=NodeType.HYPOTHESIS,
                ikros_id=hypothesis.ikros_id,
                label="Validation hypothesis",
                confidence=hypothesis.confidence.overall(),
                attributes={"entity_type": "Hypothesis"},
                spec_refs=["SPEC-060"],
                wp_refs=["WP-IMP-0048"],
            )
        )
        evidence_file = _write_validation_record(tmp_path / "EXEC-050.yaml")
        previous_overall = hypothesis.confidence.overall()
        campaign = _campaign(
            campaign_id="IKROS-RESEARCHCAMPAIGN-20260802-0001",
            title="Validation confidence campaign",
            tasks=[
                ResearchTask(
                    task_id="IKROS-RESEARCHTASK-20260802-0001",
                    kind=TaskKind.RESEARCH_QUESTION.value,
                    title="Register research question",
                    payload={
                        "entity_type": "ResearchQuestion",
                        "entity": _research_question().to_dict(),
                    },
                    planned_order=1,
                ),
                ResearchTask(
                    task_id="IKROS-RESEARCHTASK-20260802-0002",
                    kind=TaskKind.VALIDATION_REQUEST.value,
                    title="Ingest validation artifact",
                    payload={"source_path": str(evidence_file)},
                    depends_on=["IKROS-RESEARCHTASK-20260802-0001"],
                    planned_order=2,
                ),
                ResearchTask(
                    task_id="IKROS-RESEARCHTASK-20260802-0003",
                    kind=TaskKind.STATISTICAL_EVALUATION.value,
                    title="Compute deterministic validation metrics",
                    payload={
                        "p_value": 0.02,
                        "effect_size": 0.37,
                        "consistency_score": 0.88,
                        "sharpe_degradation": 0.07,
                        "overfitting_index": 1.02,
                        "data_quality_grade": "A",
                    },
                    depends_on=["IKROS-RESEARCHTASK-20260802-0002"],
                    planned_order=3,
                ),
                ResearchTask(
                    task_id="IKROS-RESEARCHTASK-20260802-0004",
                    kind=TaskKind.CONFIDENCE_UPDATE.value,
                    title="Apply confidence update",
                    payload={
                        "target_id": hypothesis.ikros_id,
                        "reason": "Validation artifact passed orchestrated quality gates",
                        "evidence": _supporting_evidence(),
                    },
                    depends_on=["IKROS-RESEARCHTASK-20260802-0003"],
                    planned_order=4,
                ),
                ResearchTask(
                    task_id="IKROS-RESEARCHTASK-20260802-0005",
                    kind=TaskKind.FINAL_REPORT.value,
                    title="Generate final report",
                    depends_on=["IKROS-RESEARCHTASK-20260802-0004"],
                    planned_order=5,
                ),
            ],
        )

        orchestrator.register_campaign(campaign)
        report = orchestrator.run_campaign(campaign.campaign_id)

        updated = orchestrator._registries["Hypothesis"].get(hypothesis.ikros_id)
        assert report.lifecycle_state == CampaignLifecycleState.COMPLETED.value
        assert updated.confidence.overall() > previous_overall
        assert "EXEC-050" in report.output_refs
        confidence_memories = orchestrator._memory.retrieve(
            MemoryQuery(entity_type="CampaignCompletionReport")
        )
        assert len(confidence_memories) == 1

    def test_resume_campaign_after_dataset_selection_failure(
        self,
        tmp_path: Path,
    ) -> None:
        orchestrator = ResearchOrchestrator(base_dir=tmp_path / "ikros")
        feature = _feature()
        orchestrator._registries["Feature"].register(feature)
        orchestrator._graph.add_node(
            GraphNode(
                node_id="IKROS-DSV-20260802-0001",
                node_type=NodeType.DATASET_VERSION,
                ikros_id="IKROS-DSV-20260802-0001",
                label="Lower confidence dataset",
                confidence=0.52,
                attributes={"entity_type": "DatasetVersion"},
                spec_refs=["SPEC-060"],
                wp_refs=["WP-IMP-0048"],
            )
        )
        orchestrator._graph.add_node(
            GraphNode(
                node_id="IKROS-DSV-20260802-0002",
                node_type=NodeType.DATASET_VERSION,
                ikros_id="IKROS-DSV-20260802-0002",
                label="Higher confidence dataset",
                confidence=0.81,
                attributes={"entity_type": "DatasetVersion"},
                spec_refs=["SPEC-060"],
                wp_refs=["WP-IMP-0048"],
            )
        )
        campaign = _campaign(
            campaign_id="IKROS-RESEARCHCAMPAIGN-20260802-0002",
            title="Selection recovery campaign",
            failure_policy=FailurePolicy.FAIL_FAST.value,
            campaign_type=CampaignType.DATASET_VALIDATION.value,
            tasks=[
                ResearchTask(
                    task_id="IKROS-RESEARCHTASK-20260802-0101",
                    kind=TaskKind.RESEARCH_QUESTION.value,
                    title="Register research question",
                    payload={
                        "entity_type": "ResearchQuestion",
                        "entity": _research_question("IKROS-RQ-20260802-0002").to_dict(),
                    },
                    planned_order=1,
                ),
                ResearchTask(
                    task_id="IKROS-RESEARCHTASK-20260802-0102",
                    kind=TaskKind.DATASET_SELECTION.value,
                    title="Select dataset",
                    payload={
                        "candidate_dataset_ids": ["IKROS-DSV-20260802-9999"],
                        "top_k": 1,
                    },
                    depends_on=["IKROS-RESEARCHTASK-20260802-0101"],
                    planned_order=2,
                    max_attempts=2,
                ),
                ResearchTask(
                    task_id="IKROS-RESEARCHTASK-20260802-0103",
                    kind=TaskKind.FEATURE_SELECTION.value,
                    title="Select feature",
                    payload={
                        "candidate_feature_ids": [feature.ikros_id],
                        "top_k": 1,
                    },
                    depends_on=["IKROS-RESEARCHTASK-20260802-0102"],
                    planned_order=3,
                ),
                ResearchTask(
                    task_id="IKROS-RESEARCHTASK-20260802-0104",
                    kind=TaskKind.FINAL_REPORT.value,
                    title="Generate final report",
                    depends_on=["IKROS-RESEARCHTASK-20260802-0103"],
                    planned_order=4,
                ),
            ],
        )

        orchestrator.register_campaign(campaign)
        first_report = orchestrator.run_campaign(campaign.campaign_id)

        assert first_report.lifecycle_state == CampaignLifecycleState.FAILED.value
        assert "IKROS-RESEARCHTASK-20260802-0102" in first_report.failed_task_ids

        orchestrator.update_task_payload(
            campaign.campaign_id,
            "IKROS-RESEARCHTASK-20260802-0102",
            {
                "candidate_dataset_ids": [
                    "IKROS-DSV-20260802-0001",
                    "IKROS-DSV-20260802-0002",
                ],
                "top_k": 1,
            },
        )
        resumed_report = orchestrator.resume_campaign(campaign.campaign_id)
        resumed_campaign = orchestrator.get_campaign(campaign.campaign_id)
        dataset_task = next(
            task
            for task in resumed_campaign.tasks
            if task.task_id == "IKROS-RESEARCHTASK-20260802-0102"
        )

        assert resumed_report.lifecycle_state == CampaignLifecycleState.COMPLETED.value
        assert dataset_task.result is not None
        assert dataset_task.result.selected_ids == ["IKROS-DSV-20260802-0002"]

    def test_validate_campaign_rejects_cycles(self) -> None:
        cyclic = _campaign(
            campaign_id="IKROS-RESEARCHCAMPAIGN-20260802-0099",
            title="Cyclic campaign",
            tasks=[
                ResearchTask(
                    task_id="IKROS-RESEARCHTASK-20260802-0901",
                    kind=TaskKind.RESEARCH_QUESTION.value,
                    title="Task A",
                    depends_on=["IKROS-RESEARCHTASK-20260802-0902"],
                    planned_order=1,
                ),
                ResearchTask(
                    task_id="IKROS-RESEARCHTASK-20260802-0902",
                    kind=TaskKind.FINAL_REPORT.value,
                    title="Task B",
                    depends_on=["IKROS-RESEARCHTASK-20260802-0901"],
                    planned_order=2,
                ),
            ],
        )

        errors = validate_campaign(cyclic)

        assert any("acyclic" in error for error in errors)
