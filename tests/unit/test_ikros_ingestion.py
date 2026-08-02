"""Unit tests for the IKROS Institutional Research Ingestion Engine."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from tools.ikros.graph import EdgeType, NodeType
from tools.ikros.ingestion import (
    IngestionStatus,
    IngestionValidationError,
    ResearchIngestionEngine,
    SourceKind,
    SourceLoader,
)
from tools.ikros.memory import MemoryTier


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _write_yaml(path: Path, text: str) -> Path:
    path.write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")
    return path


def _write_markdown(path: Path, text: str) -> Path:
    path.write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")
    return path


def _research_report_payload() -> dict[str, object]:
    return {
        "metadata": {
            "source_kind": "INTERNAL_RESEARCH_REPORT",
            "title": "Structured gold persistence report",
            "work_package_id": "WP-IMP-0046",
            "specification_refs": ["SPEC-060"],
        },
        "ikros_objects": [
            {
                "identifier": "IKROS-RQ-20260802-0001",
                "type": "ResearchQuestion",
                "title": "Does gold regime persistence predict continuation?",
                "summary": "Institutional question imported from structured report.",
                "lifecycle_state": "OPEN",
                "confidence": 0.72,
                "capability_refs": ["IKROS-INGESTION"],
                "work_package_refs": ["WP-IMP-0046"],
                "attributes": {
                    "motivation": "Governed ingestion test fixture",
                    "instrument": "XAU/USD",
                    "scope": "MACRO",
                    "time_horizon": "1D",
                    "campaign_tag": "WP46",
                },
            },
            {
                "identifier": "IKROS-HYP-20260802-0001",
                "type": "Hypothesis",
                "title": "Regime persistence supports continuation",
                "summary": "Imported hypothesis for ingestion integration testing.",
                "lifecycle_state": "PROPOSED",
                "confidence": 0.68,
                "source_ids": ["IKROS-RQ-20260802-0001"],
                "capability_refs": ["IKROS-INGESTION"],
                "work_package_refs": ["WP-IMP-0046"],
                "attributes": {
                    "statement": "Regime persistence predicts XAU/USD continuation.",
                    "null_hypothesis": "H0: No continuation effect exists.",
                    "alternative_hypothesis": "H1: Continuation effect exists.",
                    "significance_level": 0.05,
                    "power": 0.8,
                    "prior_confidence": 0.45,
                    "source_rq": "IKROS-RQ-20260802-0001",
                },
            },
        ],
    }


class TestSourceLoader:
    def test_loads_markdown_front_matter_and_fenced_objects(self, tmp_path: Path) -> None:
        source = _write_markdown(
            tmp_path / "ingestion-spec.md",
            """
            ---
            metadata:
              source_kind: SPECIFICATION
              specification_id: SPEC-060
              work_package_id: WP-IMP-0046
            ---
            # Structured Ingestion Spec

            ## Overview
            Deterministic object import rules.

            ```yaml
            ikros_objects:
              - identifier: IKROS-KO-20260802-0001
                type: KnowledgeObject
                title: Structured ingestion rule
                summary: Parsed from fenced YAML.
                lifecycle_state: ACTIVE
                confidence: 0.8
                specification_refs: [SPEC-060]
                attributes:
                  category: procedure
            ```
            """,
        )

        document = SourceLoader().load_path(source)

        assert document.source_kind == SourceKind.SPECIFICATION
        assert document.source_format == "MARKDOWN"
        assert document.title == "Structured Ingestion Spec"
        assert document.object_specs[0]["type"] == "KnowledgeObject"

    def test_infers_evidence_record_from_yaml(self, tmp_path: Path) -> None:
        source = _write_yaml(
            tmp_path / "EXEC-900.yaml",
            """
            schema_version: "ERS-1.0"
            evidence_id: "EXEC-900"
            work_package_id: "WP-IMP-0046"
            quality_gates:
              - gate: "pytest"
                result: "PASS"
            """,
        )

        document = SourceLoader().load_path(source)

        assert document.source_kind == SourceKind.EVIDENCE_RECORD
        assert document.payload["evidence_id"] == "EXEC-900"


class TestResearchIngestionEngine:
    def test_ingests_registry_backed_objects_into_registries_graph_memory_and_query(
        self,
        tmp_path: Path,
    ) -> None:
        source = _write_json(
            tmp_path / "research-report.json",
            _research_report_payload(),
        )
        engine = ResearchIngestionEngine(base_dir=tmp_path / "ikros")

        result = engine.ingest_path(source)

        assert result.status == IngestionStatus.INGESTED
        assert result.report.object_ids == [
            "IKROS-RQ-20260802-0001",
            "IKROS-HYP-20260802-0001",
        ]
        query = engine.build_query_engine().execute(
            "GET ENTITY IKROS-HYP-20260802-0001"
        )
        assert {item.source for item in query.results} == {"registry", "graph"}
        memory_query = engine.build_query_engine().execute(
            f"GET ENTITY {result.report.memory_ids[1]}"
        )
        assert {item.source for item in memory_query.results} == {"memory"}
        assert (
            engine._graph.get_node("IKROS-HYP-20260802-0001").node_type
            == NodeType.HYPOTHESIS
        )
        assert any(
            edge.source_id == "IKROS-HYP-20260802-0001"
            and edge.target_id == "IKROS-RQ-20260802-0001"
            and edge.edge_type == EdgeType.DEPENDS_ON
            for edge in engine._graph.edges()
        )
        assert engine._memory.summary()["record_count"] == 2

    def test_ingests_evidence_record_into_graph_and_memory(self, tmp_path: Path) -> None:
        source = _write_yaml(
            tmp_path / "EXEC-901.yaml",
            """
            schema_version: "ERS-1.0"
            evidence_id: "EXEC-901"
            work_package_id: "WP-IMP-0046"
            capability:
              id: "IKROS-INGESTION"
            quality_gates:
              - gate: "ruff"
                result: "PASS"
              - gate: "pytest"
                result: "PASS"
            verdict:
              all_gates_passed: true
            """,
        )
        engine = ResearchIngestionEngine(base_dir=tmp_path / "ikros")

        result = engine.ingest_path(source)

        assert result.status == IngestionStatus.INGESTED
        assert len(result.report.object_ids) == 2
        assert engine._memory.summary()["record_count"] == 2
        assert {
            engine._graph.get_node(node_id).node_type for node_id in result.report.object_ids
        } == {NodeType.EVIDENCE, NodeType.VALIDATION}

    def test_duplicate_source_is_skipped_deterministically(self, tmp_path: Path) -> None:
        source = _write_json(
            tmp_path / "research-report.json",
            _research_report_payload(),
        )
        engine = ResearchIngestionEngine(base_dir=tmp_path / "ikros")

        first = engine.ingest_path(source)
        second = engine.ingest_path(source)

        assert first.status == IngestionStatus.INGESTED
        assert second.status == IngestionStatus.SKIPPED_DUPLICATE
        assert second.report.ingestion_id == first.report.ingestion_id

    def test_duplicate_content_from_different_source_is_rejected(
        self,
        tmp_path: Path,
    ) -> None:
        payload = _research_report_payload()
        first = _write_json(tmp_path / "report-one.json", payload)
        second = _write_json(tmp_path / "report-two.json", payload)
        engine = ResearchIngestionEngine(base_dir=tmp_path / "ikros")

        engine.ingest_path(first)
        with pytest.raises(IngestionValidationError):
            engine.ingest_path(second)

    def test_missing_reference_is_rejected(self, tmp_path: Path) -> None:
        source = _write_json(
            tmp_path / "bad-report.json",
            {
                "metadata": {
                    "source_kind": "INTERNAL_RESEARCH_REPORT",
                    "title": "Bad reference report",
                    "specification_refs": ["SPEC-060"],
                },
                "ikros_objects": [
                    {
                        "identifier": "IKROS-HYP-20260802-0999",
                        "type": "Hypothesis",
                        "title": "Invalid hypothesis",
                        "summary": "References a missing research question.",
                        "lifecycle_state": "PROPOSED",
                        "confidence": 0.5,
                        "source_ids": ["IKROS-RQ-20260802-0999"],
                        "attributes": {
                            "statement": "Missing RQ invalidates ingestion.",
                            "null_hypothesis": "H0",
                            "alternative_hypothesis": "H1",
                        },
                    }
                ],
            },
        )
        engine = ResearchIngestionEngine(base_dir=tmp_path / "ikros")

        with pytest.raises(IngestionValidationError):
            engine.ingest_path(source)

    def test_invalid_non_registry_lifecycle_is_rejected(self, tmp_path: Path) -> None:
        source = _write_json(
            tmp_path / "bad-lifecycle.json",
            {
                "metadata": {
                    "source_kind": "STATISTICAL_REPORT",
                    "title": "Invalid lifecycle report",
                    "specification_refs": ["SPEC-060"],
                },
                "ikros_objects": [
                    {
                        "identifier": "IKROS-CONCL-20260802-0001",
                        "type": "ResearchConclusion",
                        "title": "Bad conclusion state",
                        "summary": "Invalid lifecycle for deterministic validation.",
                        "lifecycle_state": "ACTIVE",
                        "confidence": 0.7,
                    }
                ],
            },
        )
        engine = ResearchIngestionEngine(base_dir=tmp_path / "ikros")

        with pytest.raises(IngestionValidationError):
            engine.ingest_path(source)

    def test_markdown_without_explicit_objects_ingests_as_knowledge_object(
        self,
        tmp_path: Path,
    ) -> None:
        source = _write_markdown(
            tmp_path / "ADR-IKROS-INGESTION.md",
            """
            # ADR IKROS Ingestion

            **Specification Authority:** SPEC-060
            **Work Package ID:** WP-IMP-0046

            ## Overview
            Deterministic import policy for structured research documents.
            """,
        )
        engine = ResearchIngestionEngine(base_dir=tmp_path / "ikros")

        result = engine.ingest_path(source)

        assert result.status == IngestionStatus.INGESTED
        memory_id = result.report.memory_ids[0]
        assert engine._memory.get(memory_id).tier == MemoryTier.PROCEDURAL
        assert (
            engine._graph.get_node(result.report.object_ids[0]).node_type
            == NodeType.KNOWLEDGE_OBJECT
        )
