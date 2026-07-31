"""Tests for the Architecture Baseline governance gate."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = REPO_ROOT / "tools" / "baseline_gate.py"


def load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("baseline_gate", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GATE = load_gate()


def test_real_architecture_baseline_passes() -> None:
    assert GATE.validate_repository(REPO_ROOT) == []


def test_metadata_has_unique_paths_and_ids() -> None:
    metadata = GATE.load_yaml(GATE.METADATA_PATH)
    documents = metadata["documents"]
    assert len({document["path"] for document in documents}) == len(documents)
    assert len({document["document_id"] for document in documents}) == len(
        documents
    )


def test_missing_metadata_field_detected(tmp_path: Path) -> None:
    artifact = tmp_path / "a.md"
    artifact.write_text("x", encoding="utf-8")
    data: dict[str, Any] = {
        "schema_version": "1.0",
        "required_fields": ["title", "owner"],
        "documents": [
            {
                "path": "a.md",
                "document_id": "A",
                "title": "A",
                "version": "1",
                "status": "Frozen",
                "owner": "ARB",
                "authority": "L1",
                "approved_date": "2026-07-31",
                "last_modified": "2026-07-31",
                "change_policy": "ADR",
                "dependencies": [],
                "referenced_by": [],
                "review_policy": "release",
            }
        ],
    }
    del data["documents"][0]["owner"]
    assert any("missing owner" in error for error in GATE.validate_metadata(data, tmp_path))


def test_duplicate_document_identity_detected(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    document: dict[str, Any] = {
        "path": "a.md",
        "document_id": "A",
        "title": "A",
        "version": "1",
        "status": "Frozen",
        "owner": "ARB",
        "authority": "L1",
        "approved_date": "2026-07-31",
        "last_modified": "2026-07-31",
        "change_policy": "ADR",
        "dependencies": [],
        "referenced_by": [],
        "review_policy": "release",
    }
    data: dict[str, Any] = {
        "schema_version": "1.0",
        "required_fields": ["title"],
        "documents": [document, copy.deepcopy(document)],
    }
    errors = GATE.validate_metadata(data, tmp_path)
    assert any("duplicate path" in error for error in errors)
    assert any("duplicate document_id" in error for error in errors)


def test_unresolved_metadata_reference_detected(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    document: dict[str, Any] = {
        "path": "a.md",
        "document_id": "A",
        "title": "A",
        "version": "1",
        "status": "Frozen",
        "owner": "ARB",
        "authority": "L1",
        "approved_date": "2026-07-31",
        "last_modified": "2026-07-31",
        "change_policy": "ADR",
        "dependencies": ["missing.md"],
        "referenced_by": [],
        "review_policy": "release",
    }
    data: dict[str, Any] = {
        "schema_version": "1.0",
        "required_fields": ["title"],
        "documents": [document],
    }
    assert any(
        "unresolved dependencies reference" in error
        for error in GATE.validate_metadata(data, tmp_path)
    )


def test_source_map_cycle_detected(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    (tmp_path / "b.md").write_text("b", encoding="utf-8")
    data = {
        "schema_version": "1.0",
        "concerns": [
            {"id": "a", "owner": "a.md", "depends_on": ["b"]},
            {"id": "b", "owner": "b.md", "depends_on": ["a"]},
        ],
    }
    assert any("cycle" in error for error in GATE.validate_source_map(data, tmp_path))


def test_unknown_owner_detected(tmp_path: Path) -> None:
    data = {
        "schema_version": "1.0",
        "concerns": [{"id": "a", "owner": "missing.md", "depends_on": []}],
    }
    assert any(
        "owner does not exist" in error
        for error in GATE.validate_source_map(data, tmp_path)
    )


def test_fingerprint_tamper_detected(tmp_path: Path) -> None:
    artifact = tmp_path / "a.md"
    artifact.write_text("original", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    data = {
        "schema_version": "1.0",
        "hash_algorithm": "sha256",
        "artifacts": [{"path": "a.md", "sha256": digest}],
    }
    assert GATE.validate_fingerprint(data, {"a.md"}, tmp_path) == []
    artifact.write_text("tampered", encoding="utf-8")
    assert any(
        "digest mismatch" in error
        for error in GATE.validate_fingerprint(data, {"a.md"}, tmp_path)
    )


def test_fingerprint_coverage_gap_detected(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    (tmp_path / "b.md").write_text("b", encoding="utf-8")
    digest = hashlib.sha256((tmp_path / "a.md").read_bytes()).hexdigest()
    data = {
        "schema_version": "1.0",
        "hash_algorithm": "sha256",
        "artifacts": [{"path": "a.md", "sha256": digest}],
    }
    assert any(
        "not fingerprinted: b.md" in error
        for error in GATE.validate_fingerprint(data, {"a.md", "b.md"}, tmp_path)
    )


def test_front_matter_present_on_phase1_documents() -> None:
    metadata = GATE.load_yaml(GATE.METADATA_PATH)
    assert GATE.validate_phase1_front_matter(metadata, REPO_ROOT) == []


def test_kernel_budget_reasserted() -> None:
    assert GATE.validate_kernel(REPO_ROOT) == []


@pytest.mark.parametrize(
    "path",
    [
        "docs/governance/BASELINE_MANIFEST.md",
        "docs/governance/BASELINE_FREEZE_POLICY.md",
        "docs/governance/ARCHITECTURE_REVIEW_CHECKLIST.md",
        "docs/governance/DEFINITION_OF_DONE.md",
    ],
)
def test_required_governance_document_exists(path: str) -> None:
    assert (REPO_ROOT / path).is_file()
