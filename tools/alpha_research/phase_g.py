"""Phase G governed campaign execution for institutional XAU/USD alpha research."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Protocol, cast

from tools.alpha_research.diagnostic_experiments import (
    emit_diagnostic_experiment_reports,
    prepare_phase_g_diagnostic_experiment_artifacts,
)
from tools.alpha_research.failure_analysis import (
    emit_failure_analysis_reports,
    prepare_phase_g_failure_analysis_artifacts,
)
from tools.alpha_research.feature_discovery import (
    emit_feature_discovery_reports,
    prepare_phase_g_feature_discovery_artifacts,
)
from tools.alpha_research.hypothesis_discovery import (
    HYPOTHESIS_BLUEPRINTS,
    emit_hypothesis_discovery_reports,
    prepare_phase_g_hypothesis_discovery_artifacts,
)
from tools.alpha_research.regime_discovery import (
    emit_regime_discovery_reports,
    load_phase_g_regime_discovery_analysis,
)
from tools.alpha_research.reporting import write_json
from tools.alpha_research.scientific_validation import (
    emit_scientific_validation_reports,
    prepare_phase_g_scientific_validation_artifacts,
)
from tools.ikros.confidence import (
    ConfidenceEvidence,
    ConfidenceEvidenceType,
    ContradictionSeverity,
    EvidenceReferences,
    EvidenceRelation,
)
from tools.ikros.identifiers import compute_reproducibility_hash
from tools.ikros.models import AlphaCandidate, Experiment, Hypothesis, IKROSEntity, ResearchQuestion
from tools.ikros.orchestrator import (
    FailurePolicy,
    ResearchCampaign,
    ResearchOrchestrator,
    TaskKind,
)
from tools.ikros.registries.alpha import AlphaRegistry
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.hypothesis import HypothesisRegistry
from tools.ikros.registries.research import ResearchRegistry

PHASE_G_MACRO_ALPHA_MANIFEST = (
    Path("11-research") / "phase-g" / "macro-alpha" / "macro_alpha_campaign_manifest.json"
)
PHASE_G_REGIME_DISCOVERY_MANIFEST = (
    Path("11-research") / "phase-g" / "regime-discovery" / "regime_discovery_campaign_manifest.json"
)
PHASE_G_FEATURE_DISCOVERY_MANIFEST = (
    Path("11-research")
    / "phase-g"
    / "feature-discovery"
    / "feature_discovery_campaign_manifest.json"
)
PHASE_G_HYPOTHESIS_DISCOVERY_MANIFEST = (
    Path("11-research")
    / "phase-g"
    / "hypothesis-discovery"
    / "hypothesis_discovery_campaign_manifest.json"
)
PHASE_G_SCIENTIFIC_VALIDATION_MANIFEST = (
    Path("11-research")
    / "phase-g"
    / "scientific-validation"
    / "scientific_validation_campaign_manifest.json"
)
PHASE_G_FAILURE_ANALYSIS_MANIFEST = (
    Path("11-research")
    / "phase-g"
    / "failure-analysis"
    / "failure_analysis_campaign_manifest.json"
)
PHASE_G_DIAGNOSTIC_EXPERIMENTS_MANIFEST = (
    Path("11-research")
    / "phase-g"
    / "diagnostic-experiments"
    / "diagnostic_experiment_campaign_manifest.json"
)


def load_phase_g_macro_alpha_manifest(repo_root: Path) -> dict[str, Any]:
    manifest_path = repo_root / PHASE_G_MACRO_ALPHA_MANIFEST
    return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))


def load_phase_g_regime_discovery_manifest(repo_root: Path) -> dict[str, Any]:
    manifest_path = repo_root / PHASE_G_REGIME_DISCOVERY_MANIFEST
    return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))


def load_phase_g_feature_discovery_manifest(repo_root: Path) -> dict[str, Any]:
    manifest_path = repo_root / PHASE_G_FEATURE_DISCOVERY_MANIFEST
    return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))


def load_phase_g_hypothesis_discovery_manifest(repo_root: Path) -> dict[str, Any]:
    manifest_path = repo_root / PHASE_G_HYPOTHESIS_DISCOVERY_MANIFEST
    return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))


def load_phase_g_scientific_validation_manifest(repo_root: Path) -> dict[str, Any]:
    manifest_path = repo_root / PHASE_G_SCIENTIFIC_VALIDATION_MANIFEST
    return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))


def load_phase_g_failure_analysis_manifest(repo_root: Path) -> dict[str, Any]:
    manifest_path = repo_root / PHASE_G_FAILURE_ANALYSIS_MANIFEST
    return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))


def load_phase_g_diagnostic_experiments_manifest(repo_root: Path) -> dict[str, Any]:
    manifest_path = repo_root / PHASE_G_DIAGNOSTIC_EXPERIMENTS_MANIFEST
    return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))


def run_phase_g_macro_alpha_campaign(
    repo_root: Path,
    *,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    manifest = load_phase_g_macro_alpha_manifest(repo_root)
    resolved_base = (base_dir or (repo_root / "data" / "ikros")).resolve()
    orchestrator = ResearchOrchestrator(base_dir=resolved_base)

    research_question = ResearchQuestion.from_dict(manifest["entities"]["research_question"])
    hypothesis_data = dict(manifest["entities"]["hypothesis"])
    hypothesis = Hypothesis.from_dict(hypothesis_data)
    experiment = Experiment.from_dict(
        _with_reproducibility_hash(manifest["entities"]["experiment"])
    )

    task_payloads = _resolve_task_payloads(repo_root, manifest["task_payloads"])
    task_payloads[TaskKind.RESEARCH_QUESTION.value] = {
        "entity_type": "ResearchQuestion",
        "entity": research_question.to_dict(),
    }
    task_payloads[TaskKind.HYPOTHESIS_REGISTRATION.value] = {
        "entity_type": "Hypothesis",
        "entity": hypothesis.to_dict(),
    }
    task_payloads[TaskKind.EXPERIMENT_REGISTRATION.value] = {
        "entity_type": "Experiment",
        "entity": experiment.to_dict(),
    }

    campaign_spec = manifest["campaign"]
    campaign = orchestrator.build_campaign(
        title=str(campaign_spec["title"]),
        objective=str(campaign_spec["objective"]),
        campaign_type=str(campaign_spec["campaign_type"]),
        task_payloads=task_payloads,
        failure_policy=str(campaign_spec.get("failure_policy", FailurePolicy.FAIL_FAST.value)),
    )
    campaign.specification_refs = list(campaign_spec.get("specification_refs", []))
    campaign.capability_refs = list(campaign_spec.get("capability_refs", []))
    campaign.work_package_refs = list(campaign_spec.get("work_package_refs", []))
    campaign.evidence_refs = list(campaign_spec.get("evidence_refs", []))

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    completed_campaign = orchestrator.get_campaign(campaign.campaign_id)

    research_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    hypothesis_registry = cast(HypothesisRegistry, orchestrator._registries["Hypothesis"])
    experiment_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    alpha_registry = cast(AlphaRegistry, orchestrator._registries["AlphaCandidate"])

    if not research_registry.exists(research_question.ikros_id):
        research_registry.register(research_question)
    if not hypothesis_registry.exists(hypothesis.ikros_id):
        hypothesis_registry.register(hypothesis)
    if not experiment_registry.exists(experiment.ikros_id):
        experiment_registry.register(experiment)

    ids = manifest["ids"]
    research_registry.link_hypothesis(research_question.ikros_id, hypothesis.ikros_id)
    research_registry.link_conclusion(
        research_question.ikros_id,
        str(ids["research_conclusion_id"]),
    )
    research_registry.transition(
        research_question.ikros_id,
        str(manifest["post_run"]["research_question_state"]),
        note="Phase G Macro Alpha baseline review completed.",
    )

    hypothesis_registry.add_experiment(hypothesis.ikros_id, experiment.ikros_id)
    hypothesis_registry.add_validation(hypothesis.ikros_id, str(ids["validation_id"]))
    for state in manifest["post_run"]["hypothesis_states"]:
        hypothesis_registry.transition(
            hypothesis.ikros_id,
            str(state),
            note="Phase E macro-only evidence contradicts the thesis.",
        )
    hypothesis_registry.update_posterior_confidence(
        hypothesis.ikros_id,
        hypothesis_registry.get(hypothesis.ikros_id).confidence.overall(),
    )

    experiment_registry.add_validation(experiment.ikros_id, str(ids["validation_id"]))
    for state in manifest["post_run"]["experiment_states"]:
        experiment_registry.transition(experiment.ikros_id, str(state))

    candidate_id = str(ids["alpha_candidate_id"])
    candidate_assessment = orchestrator._confidence_engine.assess(
        candidate_id,
        [ConfidenceEvidence.from_dict(item) for item in manifest["candidate_confidence_evidence"]],
        reason="Phase G Macro Alpha candidate review",
    )
    alpha_candidate = alpha_registry.reject(
        candidate_id,
        [str(item) for item in manifest["post_run"]["alpha_rejection_reasons"]],
    )
    stored_candidate = alpha_registry.get(candidate_id)

    return {
        "campaign_id": campaign.campaign_id,
        "report": report.to_dict(),
        "progress": report.progress,
        "research_question": research_registry.get(research_question.ikros_id).to_dict(),
        "hypothesis": hypothesis_registry.get(hypothesis.ikros_id).to_dict(),
        "experiment": experiment_registry.get(experiment.ikros_id).to_dict(),
        "alpha_candidate": stored_candidate.to_dict(),
        "assessment_ids": {
            "candidate": candidate_assessment.assessment_id,
            "hypothesis": _confidence_assessment_id(
                completed_campaign,
                TaskKind.CONFIDENCE_UPDATE.value,
            ),
        },
        "validation_summary": {
            "conclusion_id": str(ids["research_conclusion_id"]),
            "contradictory_evidence_id": str(ids["contradictory_evidence_id"]),
            "validation_id": str(ids["validation_id"]),
            "promotion_decision": alpha_candidate.promotion_status,
        },
    }


def run_phase_g_regime_discovery_campaign(
    repo_root: Path,
    *,
    base_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    manifest = load_phase_g_regime_discovery_manifest(repo_root)
    analysis = load_phase_g_regime_discovery_analysis(repo_root)
    resolved_base = (base_dir or (repo_root / "data" / "ikros")).resolve()
    resolved_output = (
        output_dir or (repo_root / "11-research" / "phase-g" / "regime-discovery")
    ).resolve()
    orchestrator = ResearchOrchestrator(base_dir=resolved_base)

    research_question = ResearchQuestion.from_dict(manifest["entities"]["research_question"])
    hypothesis = Hypothesis.from_dict(dict(manifest["entities"]["hypothesis"]))
    experiment = Experiment.from_dict(
        _with_reproducibility_hash(manifest["entities"]["experiment"])
    )

    task_payloads = _resolve_task_payloads(repo_root, manifest["task_payloads"])
    task_payloads[TaskKind.RESEARCH_QUESTION.value] = {
        "entity_type": "ResearchQuestion",
        "entity": research_question.to_dict(),
    }
    task_payloads[TaskKind.HYPOTHESIS_REGISTRATION.value] = {
        "entity_type": "Hypothesis",
        "entity": hypothesis.to_dict(),
    }
    task_payloads[TaskKind.EXPERIMENT_REGISTRATION.value] = {
        "entity_type": "Experiment",
        "entity": experiment.to_dict(),
    }

    campaign_spec = manifest["campaign"]
    campaign = orchestrator.build_campaign(
        title=str(campaign_spec["title"]),
        objective=str(campaign_spec["objective"]),
        campaign_type=str(campaign_spec["campaign_type"]),
        task_payloads=task_payloads,
        failure_policy=str(campaign_spec.get("failure_policy", FailurePolicy.FAIL_FAST.value)),
    )
    campaign.specification_refs = list(campaign_spec.get("specification_refs", []))
    campaign.capability_refs = list(campaign_spec.get("capability_refs", []))
    campaign.work_package_refs = list(campaign_spec.get("work_package_refs", []))
    campaign.evidence_refs = list(campaign_spec.get("evidence_refs", []))

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    completed_campaign = orchestrator.get_campaign(campaign.campaign_id)

    research_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    hypothesis_registry = cast(HypothesisRegistry, orchestrator._registries["Hypothesis"])
    experiment_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])

    ids = manifest["ids"]
    research_registry.link_hypothesis(research_question.ikros_id, hypothesis.ikros_id)
    research_registry.link_conclusion(
        research_question.ikros_id,
        str(ids["research_conclusion_id"]),
    )
    research_registry.transition(
        research_question.ikros_id,
        str(manifest["post_run"]["research_question_state"]),
        note="Campaign 0002 regime taxonomy review completed.",
    )

    hypothesis_registry.add_experiment(hypothesis.ikros_id, experiment.ikros_id)
    hypothesis_registry.add_validation(hypothesis.ikros_id, str(ids["validation_id"]))
    for state in manifest["post_run"]["hypothesis_states"]:
        hypothesis_registry.transition(
            hypothesis.ikros_id,
            str(state),
            note="Campaign 0002 regime utility evidence supports the taxonomy.",
        )
    hypothesis_registry.update_posterior_confidence(
        hypothesis.ikros_id,
        hypothesis_registry.get(hypothesis.ikros_id).confidence.overall(),
    )

    experiment_registry.add_validation(experiment.ikros_id, str(ids["validation_id"]))
    for state in manifest["post_run"]["experiment_states"]:
        experiment_registry.transition(experiment.ikros_id, str(state))

    result: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "report": report.to_dict(),
        "progress": report.progress,
        "research_question": research_registry.get(research_question.ikros_id).to_dict(),
        "hypothesis": hypothesis_registry.get(hypothesis.ikros_id).to_dict(),
        "experiment": experiment_registry.get(experiment.ikros_id).to_dict(),
        "assessment_ids": {
            "hypothesis": _confidence_assessment_id(
                completed_campaign,
                TaskKind.CONFIDENCE_UPDATE.value,
            ),
        },
        "validation_summary": {
            "conclusion_id": str(ids["research_conclusion_id"]),
            "contradictory_evidence_id": str(ids["contradictory_evidence_id"]),
            "validation_id": str(ids["validation_id"]),
            "arb_recommendation": str(manifest["post_run"]["arb_recommendation"]),
            "accepted_taxonomy": str(analysis["accepted_taxonomy"]["name"]),
        },
    }
    result["report_paths"] = emit_regime_discovery_reports(
        repo_root=repo_root,
        output_dir=resolved_output,
        analysis=analysis,
        campaign_result=result,
    )
    result_path = resolved_output / "regime_discovery_campaign_result.json"
    write_json(result_path, result)
    result["report_paths"]["campaign_result"] = str(result_path)
    return result


def run_phase_g_feature_discovery_campaign(
    repo_root: Path,
    *,
    base_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    manifest = load_phase_g_feature_discovery_manifest(repo_root)
    resolved_base = (base_dir or (repo_root / "data" / "ikros")).resolve()
    resolved_output = (
        output_dir or (repo_root / "11-research" / "phase-g" / "feature-discovery")
    ).resolve()
    prepared = prepare_phase_g_feature_discovery_artifacts(
        repo_root=repo_root,
        output_dir=resolved_output,
    )
    analysis = cast(dict[str, Any], prepared["analysis"])
    orchestrator = ResearchOrchestrator(base_dir=resolved_base)

    research_question = ResearchQuestion.from_dict(manifest["entities"]["research_question"])
    hypothesis = Hypothesis.from_dict(dict(manifest["entities"]["hypothesis"]))
    experiment = Experiment.from_dict(
        _with_reproducibility_hash(manifest["entities"]["experiment"])
    )

    task_payloads = _resolve_task_payloads(repo_root, manifest["task_payloads"])
    task_payloads[TaskKind.KNOWLEDGE_REGISTRATION.value]["source_path"] = str(
        prepared["paths"]["knowledge"]
    )
    task_payloads[TaskKind.VALIDATION_REQUEST.value]["source_path"] = str(
        prepared["paths"]["validation"]
    )
    task_payloads[TaskKind.RESEARCH_QUESTION.value] = {
        "entity_type": "ResearchQuestion",
        "entity": research_question.to_dict(),
    }
    task_payloads[TaskKind.HYPOTHESIS_REGISTRATION.value] = {
        "entity_type": "Hypothesis",
        "entity": hypothesis.to_dict(),
    }
    task_payloads[TaskKind.EXPERIMENT_REGISTRATION.value] = {
        "entity_type": "Experiment",
        "entity": experiment.to_dict(),
    }

    campaign_spec = manifest["campaign"]
    campaign = orchestrator.build_campaign(
        title=str(campaign_spec["title"]),
        objective=str(campaign_spec["objective"]),
        campaign_type=str(campaign_spec["campaign_type"]),
        task_payloads=task_payloads,
        failure_policy=str(campaign_spec.get("failure_policy", FailurePolicy.FAIL_FAST.value)),
    )
    campaign.specification_refs = list(campaign_spec.get("specification_refs", []))
    campaign.capability_refs = list(campaign_spec.get("capability_refs", []))
    campaign.work_package_refs = list(campaign_spec.get("work_package_refs", []))
    campaign.evidence_refs = [
        str(prepared["paths"]["analysis"]),
        *[
            str(item)
            for item in campaign_spec.get("evidence_refs", [])
            if "feature_discovery_analysis.json" not in str(item)
        ],
    ]

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    completed_campaign = orchestrator.get_campaign(campaign.campaign_id)

    research_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    hypothesis_registry = cast(HypothesisRegistry, orchestrator._registries["Hypothesis"])
    experiment_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])

    ids = manifest["ids"]
    research_registry.link_hypothesis(research_question.ikros_id, hypothesis.ikros_id)
    research_registry.link_conclusion(
        research_question.ikros_id,
        str(ids["research_conclusion_id"]),
    )
    research_registry.transition(
        research_question.ikros_id,
        str(manifest["post_run"]["research_question_state"]),
        note="Campaign 0003 feature catalogue review completed.",
    )

    hypothesis_registry.add_experiment(hypothesis.ikros_id, experiment.ikros_id)
    hypothesis_registry.add_validation(hypothesis.ikros_id, str(ids["validation_id"]))
    for state in manifest["post_run"]["hypothesis_states"]:
        hypothesis_registry.transition(
            hypothesis.ikros_id,
            str(state),
            note="Campaign 0003 regime-conditioned evidence supports the approved catalogue.",
        )
    hypothesis_registry.update_posterior_confidence(
        hypothesis.ikros_id,
        hypothesis_registry.get(hypothesis.ikros_id).confidence.overall(),
    )

    experiment_registry.add_validation(experiment.ikros_id, str(ids["validation_id"]))
    for state in manifest["post_run"]["experiment_states"]:
        experiment_registry.transition(experiment.ikros_id, str(state))

    result: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "report": report.to_dict(),
        "progress": report.progress,
        "research_question": research_registry.get(research_question.ikros_id).to_dict(),
        "hypothesis": hypothesis_registry.get(hypothesis.ikros_id).to_dict(),
        "experiment": experiment_registry.get(experiment.ikros_id).to_dict(),
        "assessment_ids": {
            "hypothesis": _confidence_assessment_id(
                completed_campaign,
                TaskKind.CONFIDENCE_UPDATE.value,
            ),
        },
        "validation_summary": {
            "conclusion_id": str(ids["research_conclusion_id"]),
            "contradictory_evidence_id": str(ids["contradictory_evidence_id"]),
            "validation_id": str(ids["validation_id"]),
            "arb_recommendation": str(manifest["post_run"]["arb_recommendation"]),
            "approved_catalogue": str(analysis["campaign"]["approved_catalogue"]),
            "approved_feature_count": int(analysis["campaign"]["approved_feature_count"]),
        },
    }
    result["report_paths"] = emit_feature_discovery_reports(
        output_dir=resolved_output,
        analysis=analysis,
        campaign_result=result,
    )
    result_path = resolved_output / "feature_discovery_campaign_result.json"
    write_json(result_path, result)
    result["report_paths"]["campaign_result"] = str(result_path)
    return result


def run_phase_g_hypothesis_discovery_campaign(
    repo_root: Path,
    *,
    base_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    manifest = load_phase_g_hypothesis_discovery_manifest(repo_root)
    resolved_base = (base_dir or (repo_root / "data" / "ikros")).resolve()
    resolved_output = (
        output_dir or (repo_root / "11-research" / "phase-g" / "hypothesis-discovery")
    ).resolve()
    prepared = prepare_phase_g_hypothesis_discovery_artifacts(
        repo_root=repo_root,
        output_dir=resolved_output,
    )
    analysis = cast(dict[str, Any], prepared["analysis"])
    orchestrator = ResearchOrchestrator(base_dir=resolved_base)

    research_question = ResearchQuestion.from_dict(manifest["entities"]["research_question"])
    hypothesis = Hypothesis.from_dict(dict(manifest["entities"]["hypothesis"]))
    experiment = Experiment.from_dict(
        _with_reproducibility_hash(manifest["entities"]["experiment"])
    )

    task_payloads = _resolve_task_payloads(repo_root, manifest["task_payloads"])
    task_payloads[TaskKind.KNOWLEDGE_REGISTRATION.value]["source_path"] = str(
        prepared["paths"]["knowledge"]
    )
    task_payloads[TaskKind.RESEARCH_QUESTION.value] = {
        "entity_type": "ResearchQuestion",
        "entity": research_question.to_dict(),
    }
    task_payloads[TaskKind.HYPOTHESIS_REGISTRATION.value] = {
        "entity_type": "Hypothesis",
        "entity": hypothesis.to_dict(),
    }
    task_payloads[TaskKind.EXPERIMENT_REGISTRATION.value] = {
        "entity_type": "Experiment",
        "entity": experiment.to_dict(),
    }

    campaign_spec = manifest["campaign"]
    campaign = orchestrator.build_campaign(
        title=str(campaign_spec["title"]),
        objective=str(campaign_spec["objective"]),
        campaign_type=str(campaign_spec["campaign_type"]),
        task_payloads=task_payloads,
        failure_policy=str(campaign_spec.get("failure_policy", FailurePolicy.FAIL_FAST.value)),
    )
    _select_campaign_pipeline(
        campaign,
        [
            TaskKind.RESEARCH_QUESTION.value,
            TaskKind.LITERATURE_INTAKE.value,
            TaskKind.KNOWLEDGE_REGISTRATION.value,
            TaskKind.HYPOTHESIS_REGISTRATION.value,
            TaskKind.EXPERIMENT_REGISTRATION.value,
            TaskKind.DATASET_SELECTION.value,
            TaskKind.FEATURE_SELECTION.value,
            TaskKind.FINAL_REPORT.value,
        ],
    )
    campaign.specification_refs = list(campaign_spec.get("specification_refs", []))
    campaign.capability_refs = list(campaign_spec.get("capability_refs", []))
    campaign.work_package_refs = list(campaign_spec.get("work_package_refs", []))
    campaign.evidence_refs = [
        str(prepared["paths"]["analysis"]),
        *[
            str(item)
            for item in campaign_spec.get("evidence_refs", [])
            if "hypothesis_discovery_analysis.json" not in str(item)
        ],
    ]

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)

    research_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    hypothesis_registry = cast(HypothesisRegistry, orchestrator._registries["Hypothesis"])
    experiment_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])

    ids = manifest["ids"]
    research_registry.link_hypothesis(research_question.ikros_id, hypothesis.ikros_id)
    research_registry.link_conclusion(
        research_question.ikros_id,
        str(ids["research_conclusion_id"]),
    )
    research_registry.transition(
        research_question.ikros_id,
        str(manifest["post_run"]["research_question_state"]),
        note="Campaign 0004 hypothesis catalogue completed.",
    )

    hypothesis_registry.add_experiment(hypothesis.ikros_id, experiment.ikros_id)
    for state in manifest["post_run"]["hypothesis_states"]:
        hypothesis_registry.transition(
            hypothesis.ikros_id,
            str(state),
            note="Campaign 0004 produced a governed hypothesis catalogue awaiting validation.",
        )

    for state in manifest["post_run"]["experiment_states"]:
        experiment_registry.transition(experiment.ikros_id, str(state))

    result: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "report": report.to_dict(),
        "progress": report.progress,
        "research_question": research_registry.get(research_question.ikros_id).to_dict(),
        "hypothesis": hypothesis_registry.get(hypothesis.ikros_id).to_dict(),
        "experiment": experiment_registry.get(experiment.ikros_id).to_dict(),
        "assessment_ids": {},
        "catalogue_summary": {
            "conclusion_id": str(ids["research_conclusion_id"]),
            "contradictory_evidence_id": str(ids["contradictory_evidence_id"]),
            "evidence_id": str(ids["evidence_bundle_id"]),
            "arb_recommendation": str(manifest["post_run"]["arb_recommendation"]),
            "hypothesis_catalogue": str(analysis["campaign"]["hypothesis_catalogue"]),
            "recommended_hypotheses": list(analysis["recommended_hypotheses"]),
        },
    }
    result["report_paths"] = emit_hypothesis_discovery_reports(
        output_dir=resolved_output,
        analysis=analysis,
        campaign_result=result,
    )
    result_path = resolved_output / "hypothesis_discovery_campaign_result.json"
    write_json(result_path, result)
    result["report_paths"]["campaign_result"] = str(result_path)
    return result


def run_phase_g_scientific_validation_campaign(
    repo_root: Path,
    *,
    base_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    manifest = load_phase_g_scientific_validation_manifest(repo_root)
    resolved_base = (base_dir or (repo_root / "data" / "ikros")).resolve()
    resolved_output = (
        output_dir or (repo_root / "11-research" / "phase-g" / "scientific-validation")
    ).resolve()
    prepared = prepare_phase_g_scientific_validation_artifacts(
        repo_root=repo_root,
        output_dir=resolved_output,
    )
    analysis = cast(dict[str, Any], prepared["analysis"])
    orchestrator = ResearchOrchestrator(base_dir=resolved_base)

    research_question = ResearchQuestion.from_dict(manifest["entities"]["research_question"])
    hypothesis = Hypothesis.from_dict(dict(manifest["entities"]["hypothesis"]))
    experiment = Experiment.from_dict(
        _with_reproducibility_hash(manifest["entities"]["experiment"])
    )

    task_payloads = _resolve_task_payloads(repo_root, manifest["task_payloads"])
    task_payloads[TaskKind.KNOWLEDGE_REGISTRATION.value]["source_path"] = str(
        prepared["paths"]["knowledge"]
    )
    task_payloads[TaskKind.VALIDATION_REQUEST.value]["source_path"] = str(
        prepared["paths"]["validation"]
    )
    task_payloads[TaskKind.RESEARCH_QUESTION.value] = {
        "entity_type": "ResearchQuestion",
        "entity": research_question.to_dict(),
    }
    task_payloads[TaskKind.HYPOTHESIS_REGISTRATION.value] = {
        "entity_type": "Hypothesis",
        "entity": hypothesis.to_dict(),
    }
    task_payloads[TaskKind.EXPERIMENT_REGISTRATION.value] = {
        "entity_type": "Experiment",
        "entity": experiment.to_dict(),
    }

    campaign_spec = manifest["campaign"]
    campaign = orchestrator.build_campaign(
        title=str(campaign_spec["title"]),
        objective=str(campaign_spec["objective"]),
        campaign_type=str(campaign_spec["campaign_type"]),
        task_payloads=task_payloads,
        failure_policy=str(campaign_spec.get("failure_policy", FailurePolicy.FAIL_FAST.value)),
    )
    _select_campaign_pipeline(
        campaign,
        [
            TaskKind.RESEARCH_QUESTION.value,
            TaskKind.KNOWLEDGE_REGISTRATION.value,
            TaskKind.HYPOTHESIS_REGISTRATION.value,
            TaskKind.EXPERIMENT_REGISTRATION.value,
            TaskKind.VALIDATION_REQUEST.value,
            TaskKind.FINAL_REPORT.value,
        ],
    )
    campaign.specification_refs = list(campaign_spec.get("specification_refs", []))
    campaign.capability_refs = list(campaign_spec.get("capability_refs", []))
    campaign.work_package_refs = list(campaign_spec.get("work_package_refs", []))
    campaign.evidence_refs = [
        str(prepared["paths"]["analysis"]),
        *[
            str(item)
            for item in campaign_spec.get("evidence_refs", [])
            if "scientific_validation_analysis.json" not in str(item)
        ],
    ]

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)

    research_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    hypothesis_registry = cast(HypothesisRegistry, orchestrator._registries["Hypothesis"])
    experiment_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    alpha_registry = cast(AlphaRegistry, orchestrator._registries["AlphaCandidate"])

    if not research_registry.exists(research_question.ikros_id):
        research_registry.register(research_question)
    if not hypothesis_registry.exists(hypothesis.ikros_id):
        hypothesis_registry.register(hypothesis)
    if not experiment_registry.exists(experiment.ikros_id):
        experiment_registry.register(experiment)

    ids = manifest["ids"]
    research_registry.link_hypothesis(research_question.ikros_id, hypothesis.ikros_id)
    research_registry.link_conclusion(
        research_question.ikros_id,
        str(ids["research_conclusion_id"]),
    )
    _transition_if_needed(
        research_registry,
        research_question.ikros_id,
        str(manifest["post_run"]["research_question_state"]),
        note="Campaign 0005 scientific validation completed.",
    )

    hypothesis_registry.add_experiment(hypothesis.ikros_id, experiment.ikros_id)
    hypothesis_registry.add_validation(hypothesis.ikros_id, str(ids["validation_id"]))
    _transition_if_needed(
        hypothesis_registry,
        hypothesis.ikros_id,
        "TESTING",
        note="Campaign 0005 entered governed scientific validation.",
    )
    for state in manifest["post_run"]["hypothesis_states"]:
        _transition_if_needed(
            hypothesis_registry,
            hypothesis.ikros_id,
            str(state),
            note="Campaign 0005 completed the governed validation partition.",
        )
    hypothesis_registry.update_posterior_confidence(
        hypothesis.ikros_id,
        hypothesis_registry.get(hypothesis.ikros_id).confidence.overall(),
    )

    experiment_registry.add_validation(experiment.ikros_id, str(ids["validation_id"]))
    for state in manifest["post_run"]["experiment_states"]:
        _transition_if_needed(experiment_registry, experiment.ikros_id, str(state))

    assessment_ids: dict[str, str] = {}
    promoted_hypotheses: list[str] = []
    rejected_hypotheses: list[str] = []
    further_research_hypotheses: list[str] = []
    alpha_candidates: list[dict[str, Any]] = []

    for item in analysis["hypothesis_validations"]:
        hypothesis_id = str(item["hypothesis_id"])
        _ensure_subordinate_hypothesis(
            hypothesis_registry=hypothesis_registry,
            hypothesis_id=hypothesis_id,
            title=str(item["title"]),
            statement=str(item["research_question"]),
            alternative=str(item["economic_rationale"]),
            source_rq=f"IKROS-RQ-{hypothesis_id.split('-')[-1]}",
            prior=float(item["confidence_prior"]),
            analysis_path=str(prepared["paths"]["analysis"]),
        )
        hypothesis_registry.add_experiment(hypothesis_id, experiment.ikros_id)
        validation_id = _validation_id_for_hypothesis(hypothesis_id)
        hypothesis_registry.add_validation(hypothesis_id, validation_id)

        outcome = str(item["decision"]["outcome"])
        if outcome == "PROMOTED_TO_ALPHA_CANDIDATE":
            if hypothesis_registry.get(hypothesis_id).lifecycle_state == "APPROVED_FOR_TESTING":
                _transition_if_needed(
                    hypothesis_registry,
                    hypothesis_id,
                    "TESTING",
                    note="Campaign 0005 began subordinate hypothesis validation.",
                )
            _transition_if_needed(
                hypothesis_registry,
                hypothesis_id,
                "SUPPORTED",
                note="Campaign 0005 promoted the hypothesis to Alpha Candidate status.",
            )
            promoted_hypotheses.append(hypothesis_id)
            candidate = _register_alpha_candidate(alpha_registry, item)
            alpha_candidates.append(candidate.to_dict())
        elif outcome == "REJECTED":
            if hypothesis_registry.get(hypothesis_id).lifecycle_state == "APPROVED_FOR_TESTING":
                _transition_if_needed(
                    hypothesis_registry,
                    hypothesis_id,
                    "TESTING",
                    note="Campaign 0005 began subordinate hypothesis validation.",
                )
            _transition_if_needed(
                hypothesis_registry,
                hypothesis_id,
                "REFUTED",
                note="Campaign 0005 rejected the hypothesis after governed scientific validation.",
            )
            rejected_hypotheses.append(hypothesis_id)
        else:
            if hypothesis_registry.get(hypothesis_id).lifecycle_state == "APPROVED_FOR_TESTING":
                _transition_if_needed(
                    hypothesis_registry,
                    hypothesis_id,
                    "TESTING",
                    note="Campaign 0005 began subordinate hypothesis validation.",
                )
            _transition_if_needed(
                hypothesis_registry,
                hypothesis_id,
                "INCONCLUSIVE",
                note="Campaign 0005 kept the hypothesis in further-research status.",
            )
            further_research_hypotheses.append(hypothesis_id)
        hypothesis_registry.update_posterior_confidence(
            hypothesis_id,
            float(item["suggested_posterior_confidence"]),
        )
        assessment_ids[hypothesis_id] = validation_id

    result: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "report": report.to_dict(),
        "progress": report.progress,
        "research_question": research_registry.get(research_question.ikros_id).to_dict(),
        "hypothesis": hypothesis_registry.get(hypothesis.ikros_id).to_dict(),
        "experiment": experiment_registry.get(experiment.ikros_id).to_dict(),
        "assessment_ids": assessment_ids,
        "validation_summary": {
            "conclusion_id": str(ids["research_conclusion_id"]),
            "contradictory_evidence_id": str(ids["contradictory_evidence_id"]),
            "evidence_id": str(ids["evidence_bundle_id"]),
            "validation_id": str(ids["validation_id"]),
            "arb_recommendation": str(manifest["post_run"]["arb_recommendation"]),
            "promoted_hypotheses": promoted_hypotheses,
            "rejected_hypotheses": rejected_hypotheses,
            "further_research_hypotheses": further_research_hypotheses,
            "alpha_candidates": alpha_candidates,
        },
    }
    result["report_paths"] = emit_scientific_validation_reports(
        output_dir=resolved_output,
        analysis=analysis,
        campaign_result=result,
    )
    result_path = resolved_output / "scientific_validation_campaign_result.json"
    write_json(result_path, result)
    result["report_paths"]["campaign_result"] = str(result_path)
    return result


def run_phase_g_failure_analysis_campaign(
    repo_root: Path,
    *,
    base_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    manifest = load_phase_g_failure_analysis_manifest(repo_root)
    resolved_base = (base_dir or (repo_root / "data" / "ikros")).resolve()
    resolved_output = (
        output_dir or (repo_root / "11-research" / "phase-g" / "failure-analysis")
    ).resolve()
    prepared = prepare_phase_g_failure_analysis_artifacts(
        repo_root=repo_root,
        output_dir=resolved_output,
    )
    analysis = cast(dict[str, Any], prepared["analysis"])
    orchestrator = ResearchOrchestrator(base_dir=resolved_base)

    research_question = ResearchQuestion.from_dict(manifest["entities"]["research_question"])
    hypothesis = Hypothesis.from_dict(dict(manifest["entities"]["hypothesis"]))
    experiment = Experiment.from_dict(
        _with_reproducibility_hash(manifest["entities"]["experiment"])
    )

    task_payloads = _resolve_task_payloads(repo_root, manifest["task_payloads"])
    task_payloads[TaskKind.KNOWLEDGE_REGISTRATION.value]["source_path"] = str(
        prepared["paths"]["knowledge"]
    )
    task_payloads[TaskKind.RESEARCH_QUESTION.value] = {
        "entity_type": "ResearchQuestion",
        "entity": research_question.to_dict(),
    }
    task_payloads[TaskKind.HYPOTHESIS_REGISTRATION.value] = {
        "entity_type": "Hypothesis",
        "entity": hypothesis.to_dict(),
    }
    task_payloads[TaskKind.EXPERIMENT_REGISTRATION.value] = {
        "entity_type": "Experiment",
        "entity": experiment.to_dict(),
    }

    campaign_spec = manifest["campaign"]
    campaign = orchestrator.build_campaign(
        title=str(campaign_spec["title"]),
        objective=str(campaign_spec["objective"]),
        campaign_type=str(campaign_spec["campaign_type"]),
        task_payloads=task_payloads,
        failure_policy=str(campaign_spec.get("failure_policy", FailurePolicy.FAIL_FAST.value)),
    )
    _select_campaign_pipeline(
        campaign,
        [
            TaskKind.RESEARCH_QUESTION.value,
            TaskKind.KNOWLEDGE_REGISTRATION.value,
            TaskKind.HYPOTHESIS_REGISTRATION.value,
            TaskKind.EXPERIMENT_REGISTRATION.value,
            TaskKind.FINAL_REPORT.value,
        ],
    )
    campaign.specification_refs = list(campaign_spec.get("specification_refs", []))
    campaign.capability_refs = list(campaign_spec.get("capability_refs", []))
    campaign.work_package_refs = list(campaign_spec.get("work_package_refs", []))
    campaign.evidence_refs = [
        str(prepared["paths"]["analysis"]),
        *[
            str(item)
            for item in campaign_spec.get("evidence_refs", [])
            if "failure_analysis_analysis.json" not in str(item)
        ],
    ]

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)

    research_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    hypothesis_registry = cast(HypothesisRegistry, orchestrator._registries["Hypothesis"])
    experiment_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])

    if not research_registry.exists(research_question.ikros_id):
        research_registry.register(research_question)
    if not hypothesis_registry.exists(hypothesis.ikros_id):
        hypothesis_registry.register(hypothesis)
    if not experiment_registry.exists(experiment.ikros_id):
        experiment_registry.register(experiment)

    ids = manifest["ids"]
    research_registry.link_hypothesis(research_question.ikros_id, hypothesis.ikros_id)
    research_registry.link_conclusion(
        research_question.ikros_id,
        str(ids["research_conclusion_id"]),
    )
    _transition_if_needed(
        research_registry,
        research_question.ikros_id,
        str(manifest["post_run"]["research_question_state"]),
        note="Campaign 0006 failure analysis completed.",
    )

    hypothesis_registry.add_experiment(hypothesis.ikros_id, experiment.ikros_id)
    _transition_if_needed(
        hypothesis_registry,
        hypothesis.ikros_id,
        "TESTING",
        note="Campaign 0006 entered governed failure analysis.",
    )
    for state in manifest["post_run"]["hypothesis_states"]:
        _transition_if_needed(
            hypothesis_registry,
            hypothesis.ikros_id,
            str(state),
            note="Campaign 0006 completed the governed failure-analysis pass.",
        )
    hypothesis_registry.update_posterior_confidence(
        hypothesis.ikros_id,
        hypothesis_registry.get(hypothesis.ikros_id).confidence.overall(),
    )

    for state in manifest["post_run"]["experiment_states"]:
        _transition_if_needed(experiment_registry, experiment.ikros_id, str(state))

    retained_hypotheses: list[str] = []
    adjusted_confidence: dict[str, float] = {}
    blueprints = {item["identifier"]: item for item in HYPOTHESIS_BLUEPRINTS}
    for item in analysis["retained_hypotheses"]:
        hypothesis_id = str(item["hypothesis_id"])
        blueprint = blueprints[hypothesis_id]
        _ensure_subordinate_hypothesis(
            hypothesis_registry=hypothesis_registry,
            hypothesis_id=hypothesis_id,
            title=str(blueprint["title"]),
            statement=str(blueprint["research_question"]),
            alternative=str(blueprint["economic_theory"]),
            source_rq=f"IKROS-RQ-{hypothesis_id.split('-')[-1]}",
            prior=float(blueprint["confidence_prior"]),
            analysis_path=str(prepared["paths"]["analysis"]),
        )
        retained_hypotheses.append(hypothesis_id)
        hypothesis_registry.add_experiment(hypothesis_id, experiment.ikros_id)
        hypothesis_registry.update_posterior_confidence(
            hypothesis_id,
            float(item["updated_confidence"]["analysis_adjusted_confidence"]),
        )
        adjusted_confidence[hypothesis_id] = float(
            item["updated_confidence"]["analysis_adjusted_confidence"]
        )

    result: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "report": report.to_dict(),
        "progress": report.progress,
        "research_question": research_registry.get(research_question.ikros_id).to_dict(),
        "hypothesis": hypothesis_registry.get(hypothesis.ikros_id).to_dict(),
        "experiment": experiment_registry.get(experiment.ikros_id).to_dict(),
        "failure_analysis_summary": {
            "conclusion_id": str(ids["research_conclusion_id"]),
            "contradictory_evidence_id": str(ids["contradictory_evidence_id"]),
            "evidence_id": str(ids["evidence_bundle_id"]),
            "arb_recommendation": str(manifest["post_run"]["arb_recommendation"]),
            "retained_hypotheses": retained_hypotheses,
            "adjusted_confidence": adjusted_confidence,
            "recommended_experiment_count": len(
                analysis["recommended_experiment_backlog"]
            ),
        },
    }
    result["report_paths"] = emit_failure_analysis_reports(
        output_dir=resolved_output,
        analysis=analysis,
        campaign_result=result,
    )
    result_path = resolved_output / "failure_analysis_campaign_result.json"
    write_json(result_path, result)
    result["report_paths"]["campaign_result"] = str(result_path)
    return result


def run_phase_g_diagnostic_experiment_campaign(
    repo_root: Path,
    *,
    base_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    manifest = load_phase_g_diagnostic_experiments_manifest(repo_root)
    resolved_base = (base_dir or (repo_root / "data" / "ikros")).resolve()
    resolved_output = (
        output_dir or (repo_root / "11-research" / "phase-g" / "diagnostic-experiments")
    ).resolve()
    prepared = prepare_phase_g_diagnostic_experiment_artifacts(
        repo_root=repo_root,
        output_dir=resolved_output,
    )
    analysis = cast(dict[str, Any], prepared["analysis"])
    orchestrator = ResearchOrchestrator(base_dir=resolved_base)

    research_question = ResearchQuestion.from_dict(manifest["entities"]["research_question"])
    hypothesis = Hypothesis.from_dict(dict(manifest["entities"]["hypothesis"]))
    experiment = Experiment.from_dict(
        _with_reproducibility_hash(manifest["entities"]["experiment"])
    )

    task_payloads = _resolve_task_payloads(repo_root, manifest["task_payloads"])
    task_payloads[TaskKind.KNOWLEDGE_REGISTRATION.value]["source_path"] = str(
        prepared["paths"]["knowledge"]
    )
    task_payloads[TaskKind.RESEARCH_QUESTION.value] = {
        "entity_type": "ResearchQuestion",
        "entity": research_question.to_dict(),
    }
    task_payloads[TaskKind.HYPOTHESIS_REGISTRATION.value] = {
        "entity_type": "Hypothesis",
        "entity": hypothesis.to_dict(),
    }
    task_payloads[TaskKind.EXPERIMENT_REGISTRATION.value] = {
        "entity_type": "Experiment",
        "entity": experiment.to_dict(),
    }

    campaign_spec = manifest["campaign"]
    campaign = orchestrator.build_campaign(
        title=str(campaign_spec["title"]),
        objective=str(campaign_spec["objective"]),
        campaign_type=str(campaign_spec["campaign_type"]),
        task_payloads=task_payloads,
        failure_policy=str(campaign_spec.get("failure_policy", FailurePolicy.FAIL_FAST.value)),
    )
    _select_campaign_pipeline(
        campaign,
        [
            TaskKind.RESEARCH_QUESTION.value,
            TaskKind.KNOWLEDGE_REGISTRATION.value,
            TaskKind.HYPOTHESIS_REGISTRATION.value,
            TaskKind.EXPERIMENT_REGISTRATION.value,
            TaskKind.FINAL_REPORT.value,
        ],
    )
    campaign.specification_refs = list(campaign_spec.get("specification_refs", []))
    campaign.capability_refs = list(campaign_spec.get("capability_refs", []))
    campaign.work_package_refs = list(campaign_spec.get("work_package_refs", []))
    campaign.evidence_refs = [
        str(prepared["paths"]["analysis"]),
        *[
            str(item)
            for item in campaign_spec.get("evidence_refs", [])
            if "diagnostic_experiment_analysis.json" not in str(item)
        ],
    ]

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)

    research_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    hypothesis_registry = cast(HypothesisRegistry, orchestrator._registries["Hypothesis"])
    experiment_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])

    if not research_registry.exists(research_question.ikros_id):
        research_registry.register(research_question)
    if not hypothesis_registry.exists(hypothesis.ikros_id):
        hypothesis_registry.register(hypothesis)
    if not experiment_registry.exists(experiment.ikros_id):
        experiment_registry.register(experiment)

    ids = manifest["ids"]
    research_registry.link_hypothesis(research_question.ikros_id, hypothesis.ikros_id)
    research_registry.link_conclusion(
        research_question.ikros_id,
        str(ids["research_conclusion_id"]),
    )
    _transition_if_needed(
        research_registry,
        research_question.ikros_id,
        str(manifest["post_run"]["research_question_state"]),
        note="Campaign 0007 diagnostic experiment program completed.",
    )

    hypothesis_registry.add_experiment(hypothesis.ikros_id, experiment.ikros_id)
    _transition_if_needed(
        hypothesis_registry,
        hypothesis.ikros_id,
        "TESTING",
        note="Campaign 0007 entered governed diagnostic experimentation.",
    )
    for state in manifest["post_run"]["hypothesis_states"]:
        _transition_if_needed(
            hypothesis_registry,
            hypothesis.ikros_id,
            str(state),
            note="Campaign 0007 completed the diagnostic experiment program.",
        )
    hypothesis_registry.update_posterior_confidence(
        hypothesis.ikros_id,
        hypothesis_registry.get(hypothesis.ikros_id).confidence.overall(),
    )

    for state in manifest["post_run"]["experiment_states"]:
        _transition_if_needed(experiment_registry, experiment.ikros_id, str(state))

    blueprints = {item["identifier"]: item for item in HYPOTHESIS_BLUEPRINTS}
    subordinate_experiments: list[str] = []
    updated_confidence: dict[str, float] = {}
    recommendation_matrix = {
        item["hypothesis_id"]: item for item in analysis["recommendation_matrix"]
    }

    for item in analysis["diagnostic_experiments"]:
        experiment_id = str(item["experiment_id"])
        hypothesis_id = str(item["target_hypothesis"])
        blueprint = blueprints[hypothesis_id]
        _ensure_subordinate_hypothesis(
            hypothesis_registry=hypothesis_registry,
            hypothesis_id=hypothesis_id,
            title=str(blueprint["title"]),
            statement=str(blueprint["research_question"]),
            alternative=str(blueprint["economic_theory"]),
            source_rq=f"IKROS-RQ-{hypothesis_id.split('-')[-1]}",
            prior=float(blueprint["confidence_prior"]),
            analysis_path=str(prepared["paths"]["analysis"]),
        )
        subordinate_experiments.append(experiment_id)
        hypothesis_registry.add_experiment(hypothesis_id, experiment_id)
        _register_subordinate_experiment(
            experiment_registry=experiment_registry,
            experiment_id=experiment_id,
            hypothesis_id=hypothesis_id,
            item=item,
            analysis_path=str(prepared["paths"]["analysis"]),
        )

    for hypothesis_id, recommendation in recommendation_matrix.items():
        hypothesis_registry.update_posterior_confidence(
            hypothesis_id,
            float(recommendation["campaign_0007_confidence"]),
        )
        updated_confidence[hypothesis_id] = float(recommendation["campaign_0007_confidence"])

    result: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "report": report.to_dict(),
        "progress": report.progress,
        "research_question": research_registry.get(research_question.ikros_id).to_dict(),
        "hypothesis": hypothesis_registry.get(hypothesis.ikros_id).to_dict(),
        "experiment": experiment_registry.get(experiment.ikros_id).to_dict(),
        "diagnostic_summary": {
            "conclusion_id": str(ids["research_conclusion_id"]),
            "contradictory_evidence_id": str(ids["contradictory_evidence_id"]),
            "evidence_id": str(ids["evidence_bundle_id"]),
            "arb_recommendation": str(manifest["post_run"]["arb_recommendation"]),
            "executed_experiments": subordinate_experiments,
            "return_for_validation": list(analysis["campaign"]["return_for_validation"]),
            "remain_in_testing": list(analysis["campaign"]["remain_in_testing"]),
            "rejected": list(analysis["campaign"]["rejected"]),
            "updated_confidence": updated_confidence,
        },
    }
    result["report_paths"] = emit_diagnostic_experiment_reports(
        output_dir=resolved_output,
        analysis=analysis,
        campaign_result=result,
    )
    result_path = resolved_output / "diagnostic_experiment_campaign_result.json"
    write_json(result_path, result)
    result["report_paths"]["campaign_result"] = str(result_path)
    return result


def _resolve_task_payloads(
    repo_root: Path,
    task_payloads: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    resolved: dict[str, dict[str, Any]] = {}
    for task_kind, raw_payload in task_payloads.items():
        payload = deepcopy(dict(raw_payload))
        source_path = payload.get("source_path")
        if source_path:
            payload["source_path"] = str((repo_root / Path(str(source_path))).resolve())
        resolved[str(task_kind)] = payload
    return resolved


def _with_reproducibility_hash(experiment_data: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(experiment_data)
    if normalized.get("reproducibility_hash"):
        return normalized
    normalized["reproducibility_hash"] = compute_reproducibility_hash(
        {
            "dataset_versions": normalized.get("dataset_versions", []),
            "feature_versions": normalized.get("feature_versions", []),
            "parameters": normalized.get("parameters", {}),
            "random_seed": normalized.get("random_seed", 42),
            "out_of_sample_start": normalized.get("out_of_sample_start", ""),
            "out_of_sample_end": normalized.get("out_of_sample_end", ""),
            "protocol": normalized.get("protocol", ""),
        }
    )
    return normalized


def _confidence_assessment_id(campaign: ResearchCampaign, task_kind: str) -> str | None:
    for task in campaign.tasks:
        if task.kind == task_kind and task.result is not None and task.result.output_refs:
            return str(task.result.output_refs[0])
    return None


def _select_campaign_pipeline(
    campaign: ResearchCampaign,
    ordered_kinds: list[str],
) -> None:
    task_by_kind = {task.kind: task for task in campaign.tasks}
    selected_tasks = [task_by_kind[kind] for kind in ordered_kinds]
    previous_id: str | None = None
    for index, task in enumerate(selected_tasks, start=1):
        task.planned_order = index
        task.depends_on = [] if previous_id is None else [previous_id]
        previous_id = task.task_id
    campaign.tasks = selected_tasks
    campaign.pipeline.stages = [task.kind for task in selected_tasks]
    campaign.pipeline.task_ids = [task.task_id for task in selected_tasks]


def _ensure_subordinate_hypothesis(
    *,
    hypothesis_registry: HypothesisRegistry,
    hypothesis_id: str,
    title: str,
    statement: str,
    alternative: str,
    source_rq: str,
    prior: float,
    analysis_path: str,
) -> None:
    if hypothesis_registry.exists(hypothesis_id):
        return
    hypothesis_registry.register(
        Hypothesis.from_dict(
            {
                "ikros_id": hypothesis_id,
                "entity_type": "Hypothesis",
                "version": "1.0.0",
                "lifecycle_state": "APPROVED_FOR_TESTING",
                "confidence": {
                    "prior": prior,
                    "statistical": prior,
                    "economic": prior,
                    "data": prior,
                    "model": 0.0,
                    "validation": 0.0,
                    "replication": prior,
                    "operational": 0.0,
                },
                "lineage": {
                    "origin": {
                        "created_by": "campaign-0005-scientific-validation",
                        "created_at": "2026-08-02T00:00:00Z",
                        "creation_context": "Campaign 0005 scientific validation",
                        "motivation": f"Temporary hypothesis registration for {title}.",
                    },
                    "dependencies": {
                        "inputs": [source_rq],
                        "datasets": [],
                        "features": [],
                        "models": [],
                        "external_refs": [analysis_path],
                    },
                    "experiments": {"tested_in": [], "validated_by": []},
                    "evidence": {"supporting": [], "contradicting": [], "ers_records": []},
                },
                "spec_refs": ["SPEC-012", "SPEC-060"],
                "capability_refs": [],
                "work_package_refs": [],
                "version_history": [],
                "statement": statement,
                "null_hypothesis": (
                    "The described mechanism does not produce a persistent "
                    "regime-conditioned predictive relationship."
                ),
                "alternative_hypothesis": alternative,
                "significance_level": 0.05,
                "power": 0.8,
                "prior_confidence": prior,
                "posterior_confidence": 0.0,
                "source_rq": source_rq,
                "motivating_theses": [],
                "experiments": [],
                "validations": [],
                "contradictions": [],
            }
        )
    )


def _validation_id_for_hypothesis(hypothesis_id: str) -> str:
    return "IKROS-VAL-20260802-" + hypothesis_id.split("-")[-1]


def _register_subordinate_experiment(
    *,
    experiment_registry: ExperimentRegistry,
    experiment_id: str,
    hypothesis_id: str,
    item: dict[str, Any],
    analysis_path: str,
) -> Experiment:
    if experiment_registry.exists(experiment_id):
        experiment = experiment_registry.get(experiment_id)
    else:
        experiment = Experiment.from_dict(
            _with_reproducibility_hash(
                {
                    "ikros_id": experiment_id,
                    "entity_type": "Experiment",
                    "version": "1.0.0",
                    "lifecycle_state": "RUNNING",
                    "confidence": {
                        "prior": 0.55,
                        "statistical": 0.0,
                        "economic": 0.68,
                        "data": 0.80,
                        "model": 0.0,
                        "validation": 0.0,
                        "replication": 0.0,
                        "operational": 0.71,
                        "last_updated": "2026-08-02T00:00:00Z",
                    },
                    "lineage": {
                        "origin": {
                            "created_by": "campaign-0007-diagnostic-experiment",
                            "created_at": "2026-08-02T00:00:00Z",
                            "creation_context": "Campaign 0007 diagnostic experiment program",
                            "motivation": str(item["scientific_motivation"]),
                        },
                        "dependencies": {
                            "inputs": [hypothesis_id],
                            "datasets": list(item["required_datasets"]),
                            "features": list(item["required_features"]),
                            "models": ["institutional_six_state_overlay_taxonomy_v1"],
                            "external_refs": [analysis_path],
                        },
                        "experiments": {"tested_in": [], "validated_by": []},
                        "evidence": {"supporting": [], "contradicting": [], "ers_records": []},
                    },
                    "spec_refs": ["SPEC-012", "SPEC-060"],
                    "capability_refs": ["ALPHA-RESEARCH", "IKROS-ORCHESTRATOR", "IKROS-INGESTION"],
                    "work_package_refs": [],
                    "version_history": [],
                    "title": str(item["title"]),
                    "hypotheses": [hypothesis_id],
                    "protocol": str(item["experimental_design"]),
                    "dataset_versions": list(item["required_datasets"]),
                    "feature_versions": list(item["required_features"]),
                    "parameters": {
                        "recommendation": str(item["recommendation"]),
                        "validation_method": str(item["validation_method"]),
                        "support_classification": str(
                            item["supports_or_contradicts_current_hypothesis"]
                        ),
                    },
                    "random_seed": 42,
                    "in_sample_start": "",
                    "in_sample_end": "",
                    "out_of_sample_start": "",
                    "out_of_sample_end": "",
                    "reproducibility_hash": "",
                    "git_commit": "",
                    "completed_at": None,
                    "validations_produced": [],
                    "failures_produced": [],
                }
            )
        )
        experiment_registry.register(experiment)
    _transition_if_needed(
        experiment_registry,
        experiment_id,
        "COMPLETE",
        note="Campaign 0007 diagnostic experiment execution completed.",
    )
    _transition_if_needed(
        experiment_registry,
        experiment_id,
        "REVIEWED",
        note="Campaign 0007 diagnostic experiment reviewed for ARB recommendation.",
    )
    return experiment_registry.get(experiment_id)


class _TransitionRegistry(Protocol):
    def get(self, ikros_id: str) -> IKROSEntity: ...

    def transition(self, ikros_id: str, new_state: str, note: str = "") -> IKROSEntity: ...


def _transition_if_needed(
    registry: _TransitionRegistry,
    ikros_id: str,
    new_state: str,
    *,
    note: str | None = None,
) -> None:
    entity = registry.get(ikros_id)
    if entity.lifecycle_state == new_state:
        return
    current_rank = _state_rank(entity.entity_type, entity.lifecycle_state)
    new_rank = _state_rank(entity.entity_type, new_state)
    if current_rank is not None and new_rank is not None and current_rank >= new_rank:
        return
    if note is None:
        registry.transition(ikros_id, new_state)
    else:
        registry.transition(ikros_id, new_state, note=note)


def _state_rank(entity_type: str, lifecycle_state: str) -> int | None:
    ordering: dict[str, dict[str, int]] = {
        "ResearchQuestion": {"OPEN": 0, "ACTIVE": 1, "ANSWERED": 2, "RETIRED": 3},
        "Hypothesis": {
            "PROPOSED": 0,
            "UNDER_REVIEW": 1,
            "APPROVED_FOR_TESTING": 2,
            "TESTING": 3,
            "INCONCLUSIVE": 4,
            "SUPPORTED": 5,
            "REFUTED": 5,
            "RETIRED": 6,
        },
        "Experiment": {
            "DESIGNED": 0,
            "APPROVED": 1,
            "RUNNING": 2,
            "COMPLETE": 3,
            "REVIEWED": 4,
            "ARCHIVED": 5,
            "FAILED": 5,
            "INVALIDATED": 5,
        },
    }
    return ordering.get(entity_type, {}).get(lifecycle_state)


def _register_alpha_candidate(
    alpha_registry: AlphaRegistry,
    item: dict[str, Any],
) -> AlphaCandidate:
    candidate_id = "IKROS-ALPHACAND-20260802-" + item["hypothesis_id"].split("-")[-1]
    if alpha_registry.exists(candidate_id):
        return alpha_registry.get(candidate_id)
    candidate = AlphaCandidate.from_dict(
        {
            "ikros_id": candidate_id,
            "entity_type": "AlphaCandidate",
            "version": "1.0.0",
            "lifecycle_state": "CANDIDATE",
            "confidence": {
                "prior": item["suggested_posterior_confidence"],
                "statistical": item["suggested_posterior_confidence"],
                "economic": item["suggested_posterior_confidence"],
                "data": item["suggested_posterior_confidence"],
                "model": item["suggested_posterior_confidence"],
                "validation": item["suggested_posterior_confidence"],
                "replication": item["suggested_posterior_confidence"],
                "operational": item["suggested_posterior_confidence"],
            },
            "lineage": {
                "origin": {
                    "created_by": "campaign-0005-scientific-validation",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "Campaign 0005 scientific validation",
                    "motivation": f"Alpha candidate registration for {item['hypothesis_id']}.",
                },
                "dependencies": {
                    "inputs": [item["hypothesis_id"]],
                    "datasets": ["IKROS-DSV-20260802-0005"],
                    "features": [],
                    "models": [],
                    "external_refs": [],
                },
                "experiments": {
                    "tested_in": [],
                    "validated_by": [_validation_id_for_hypothesis(item["hypothesis_id"])],
                },
                "evidence": {
                    "supporting": ["IKROS-EVIDENCE-20260802-0005"],
                    "contradicting": [],
                    "ers_records": [],
                },
            },
            "spec_refs": ["SPEC-012", "SPEC-060"],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "name": item["title"],
            "strategy_type": "HYBRID",
            "sharpe_oos": item["statistics"]["trade_sharpe"],
            "max_drawdown": max(0.0, -item["monte_carlo"]["p05_total_return"]),
            "direction_accuracy": item["statistics"]["win_rate"],
            "win_rate": item["statistics"]["win_rate"],
            "promotion_score": item["suggested_posterior_confidence"],
            "promotion_status": "CANDIDATE",
            "rejection_reasons": [],
            "backtests": [],
            "walk_forwards": [],
            "monte_carlos": [],
            "implements_hypotheses": [item["hypothesis_id"]],
        }
    )
    alpha_registry.register(candidate)
    return candidate


def _confidence_evidence(
    *,
    hypothesis_id: str,
    experiment_id: str,
    validation_id: str,
    item: dict[str, Any],
    relation: str,
) -> list[ConfidenceEvidence]:
    contradiction_severity = None
    if relation == EvidenceRelation.CONTRADICTS.value:
        contradiction_severity = ContradictionSeverity.MAJOR.value
    references = EvidenceReferences(
        specification_ids=["SPEC-012", "SPEC-060"],
        experiment_ids=[experiment_id],
        validation_ids=[validation_id],
        research_report_ids=["IKROS-CONCL-20260802-0005"],
    )
    return [
        ConfidenceEvidence(
            evidence_id=f"{validation_id}-validation",
            evidence_type=ConfidenceEvidenceType.VALIDATION.value,
            relation=relation,
            references=references,
            confidence_weight=0.95,
            contradiction_severity=contradiction_severity,
            metrics={
                "mean_return": item["statistics"]["mean_return"],
                "bootstrap_probability_positive": item["bootstrap"]["probability_positive"],
                "walk_forward_positive_fold_ratio": item["walk_forward"]["positive_fold_ratio"],
            },
            notes=f"Campaign 0005 outcome for {hypothesis_id}: {item['decision']['outcome']}",
        ),
        ConfidenceEvidence(
            evidence_id=f"{validation_id}-walk-forward",
            evidence_type=ConfidenceEvidenceType.WALK_FORWARD_STUDY.value,
            relation=relation,
            references=references,
            confidence_weight=0.85,
            contradiction_severity=contradiction_severity,
            metrics=item["walk_forward"],
            notes="Walk-forward stability evidence",
        ),
        ConfidenceEvidence(
            evidence_id=f"{validation_id}-monte-carlo",
            evidence_type=ConfidenceEvidenceType.MONTE_CARLO_STUDY.value,
            relation=relation,
            references=references,
            confidence_weight=0.8,
            contradiction_severity=contradiction_severity,
            metrics=item["monte_carlo"],
            notes="Monte Carlo path robustness evidence",
        ),
    ]
