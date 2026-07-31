"""Unit tests for WP-IMP-0003: afrp boot, manifest parser, kernel parser."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from afrp.cli import cli
from afrp.commands.boot import render_repository_state, run_boot, verify_baseline
from afrp.core.exceptions import (
    BaselineIntegrityError,
    ContractReferenceError,
    InvariantError,
    ManifestValidationError,
)
from afrp.core.kernel import KERNEL_MAX_WORDS, count_words, load_kernel
from afrp.core.manifest import load_manifest
from click.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[2]

MINIMAL_MANIFEST: dict[str, object] = {
    "schema_version": "1.0",
    "manifest_id": "REPOSITORY_MANIFEST",
    "baseline": {
        "suite_id": "AFRP-BASELINE-1.0.0",
        "baseline_tag": "eos-baseline-v1.0",
        "genesis_commit_tag": "m1.1-start",
        "governance_protocol": "EGP-2.0",
        "repository_os": "ROS-1.0.0",
        "effective_date": "2026-07-31",
        "authority": "ARB",
    },
    "products": [{"id": "EOS", "name": "Engineering OS", "paths": ["tools/afrp-cli/"]}],
    "topology": [{"path": "00-governance/", "purpose": "governance"}],
    "document_index": {"KERNEL.md": "00-governance/KERNEL.md"},
    "integrity": {
        "fingerprint_ledger": "00-governance/BASELINE_FINGERPRINT.yaml",
        "hash_algorithm": "sha256",
    },
}


def write_manifest(path: Path, data: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


class TestManifestParser:
    def test_parses_real_repository_manifest(self) -> None:
        manifest = load_manifest(REPO_ROOT / "REPOSITORY_MANIFEST.yaml")
        assert manifest.schema_version == "1.0"
        assert manifest.baseline.suite_id == "AFRP-BASELINE-1.0.0"
        assert manifest.baseline.genesis_commit_tag == "m1.1-start"
        assert {p.id for p in manifest.products} == {"EOS", "RUNTIME", "RESEARCH"}

    def test_parses_minimal_manifest(self, tmp_path: Path) -> None:
        target = tmp_path / "REPOSITORY_MANIFEST.yaml"
        write_manifest(target, MINIMAL_MANIFEST)
        manifest = load_manifest(target)
        assert manifest.manifest_id == "REPOSITORY_MANIFEST"
        assert manifest.integrity.hash_algorithm == "sha256"

    def test_missing_file_raises_contract_reference(self, tmp_path: Path) -> None:
        with pytest.raises(ContractReferenceError):
            load_manifest(tmp_path / "absent.yaml")

    def test_wrong_schema_version_rejected(self, tmp_path: Path) -> None:
        bad = dict(MINIMAL_MANIFEST)
        bad["schema_version"] = "2.0"
        target = tmp_path / "REPOSITORY_MANIFEST.yaml"
        write_manifest(target, bad)
        with pytest.raises(ManifestValidationError):
            load_manifest(target)

    def test_malformed_yaml_rejected(self, tmp_path: Path) -> None:
        target = tmp_path / "REPOSITORY_MANIFEST.yaml"
        target.write_text("schema_version: [unclosed", encoding="utf-8")
        with pytest.raises(ManifestValidationError):
            load_manifest(target)

    def test_non_mapping_root_rejected(self, tmp_path: Path) -> None:
        target = tmp_path / "REPOSITORY_MANIFEST.yaml"
        target.write_text("- just\n- a\n- list\n", encoding="utf-8")
        with pytest.raises(ManifestValidationError):
            load_manifest(target)

    def test_document_index_resolution(self, tmp_path: Path) -> None:
        target = tmp_path / "REPOSITORY_MANIFEST.yaml"
        write_manifest(target, MINIMAL_MANIFEST)
        manifest = load_manifest(target)
        assert manifest.resolve_document("KERNEL.md") == "00-governance/KERNEL.md"
        with pytest.raises(ManifestValidationError):
            manifest.resolve_document("UNKNOWN.md")


class TestKernelParser:
    def test_parses_real_kernel_within_budget(self) -> None:
        kernel = load_kernel(REPO_ROOT / "00-governance" / "KERNEL.md")
        assert kernel.word_count <= KERNEL_MAX_WORDS
        assert kernel.title.startswith("KERNEL")
        assert kernel.sections

    def test_word_count_is_deterministic(self) -> None:
        assert count_words("alpha beta\n gamma") == 3
        assert count_words("") == 0

    def test_missing_kernel_raises_contract_reference(self, tmp_path: Path) -> None:
        with pytest.raises(ContractReferenceError):
            load_kernel(tmp_path / "KERNEL.md")

    def test_overlong_kernel_raises_invariant_error(self, tmp_path: Path) -> None:
        target = tmp_path / "KERNEL.md"
        target.write_text("# T\n\n" + ("word " * 401), encoding="utf-8")
        with pytest.raises(InvariantError) as excinfo:
            load_kernel(target)
        assert excinfo.value.invariant == "FIT-006"

    def test_kernel_without_heading_rejected(self, tmp_path: Path) -> None:
        target = tmp_path / "KERNEL.md"
        target.write_text("no headings here\n", encoding="utf-8")
        with pytest.raises(InvariantError):
            load_kernel(target)

    def test_custom_budget_boundary(self, tmp_path: Path) -> None:
        target = tmp_path / "KERNEL.md"
        target.write_text("# T\nw w w", encoding="utf-8")
        kernel = load_kernel(target, max_words=5)
        assert kernel.word_count == 5
        with pytest.raises(InvariantError):
            load_kernel(target, max_words=4)


class TestBaselineVerification:
    def test_real_baseline_verifies(self) -> None:
        ledger = REPO_ROOT / "00-governance" / "BASELINE_FINGERPRINT.yaml"
        verified = verify_baseline(REPO_ROOT, ledger)
        assert verified >= 20

    def test_tampered_artifact_detected(self, tmp_path: Path) -> None:
        artifact = tmp_path / "doc.md"
        artifact.write_text("original", encoding="utf-8")
        ledger = tmp_path / "ledger.yaml"
        ledger.write_text(
            yaml.safe_dump(
                {
                    "artifacts": [
                        {"path": "doc.md", "sha256": "0" * 64},
                    ]
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(BaselineIntegrityError) as excinfo:
            verify_baseline(tmp_path, ledger)
        assert "doc.md" in excinfo.value.mismatches

    def test_missing_ledger_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ContractReferenceError):
            verify_baseline(tmp_path, tmp_path / "absent.yaml")

    def test_missing_listed_artifact_raises(self, tmp_path: Path) -> None:
        ledger = tmp_path / "ledger.yaml"
        ledger.write_text(
            yaml.safe_dump({"artifacts": [{"path": "ghost.md", "sha256": "0" * 64}]}),
            encoding="utf-8",
        )
        with pytest.raises(ContractReferenceError):
            verify_baseline(tmp_path, ledger)

    def test_malformed_ledger_entry_raises_integrity_error(self, tmp_path: Path) -> None:
        ledger = tmp_path / "ledger.yaml"
        ledger.write_text(
            yaml.safe_dump({"artifacts": [{"sha256": "0" * 64}]}),
            encoding="utf-8",
        )
        with pytest.raises(BaselineIntegrityError):
            verify_baseline(tmp_path, ledger)


class TestBootCommand:
    def test_run_boot_reaches_baseline_verified(self) -> None:
        result = run_boot(REPO_ROOT)
        assert result.kernel.word_count <= KERNEL_MAX_WORDS
        assert result.verified_artifacts >= 20

    def test_repository_state_block_shape(self) -> None:
        result = run_boot(REPO_ROOT)
        state = yaml.safe_load(render_repository_state(result))["repository_state"]
        assert state["protocol_version"] == "EGP-2.0"
        assert state["lifecycle_state"] == "BASELINE_VERIFIED"
        assert state["verification"]["baseline_verified"] is True
        assert state["authorization"]["execution_authorized"] is False
        assert state["integrity"]["status"] == "PASS"
        assert state["termination"]["next_action"] == "LOAD_WORK_PACKAGE"

    def test_cli_boot_exits_zero_and_emits_state(self) -> None:
        runner = CliRunner()
        outcome = runner.invoke(cli, ["boot", "--repo-root", str(REPO_ROOT)])
        assert outcome.exit_code == 0, outcome.output
        assert "lifecycle_state: BASELINE_VERIFIED" in outcome.output

    def test_cli_boot_halts_on_empty_repository(self, tmp_path: Path) -> None:
        runner = CliRunner()
        outcome = runner.invoke(cli, ["boot", "--repo-root", str(tmp_path)])
        assert outcome.exit_code == 2
        assert "HALTED" in outcome.output
