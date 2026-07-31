"""Unit tests for Stage C contracts: proto gate, FIT-003, NFR-010 compat."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = REPO_ROOT / "tools" / "proto_gate.py"
SNAPSHOT_PATH = REPO_ROOT / "09-validation" / "contracts" / "afrp_v1.snapshot.json"


def load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("proto_gate", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> ModuleType:
    return load_gate()


@pytest.fixture(scope="module")
def manifest(gate: ModuleType) -> dict[str, Any]:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        descriptor = gate.compile_protos(Path(tmp))
        result: dict[str, Any] = gate.build_manifest(descriptor)
    return result


class TestProtoCompilation:
    def test_full_gate_passes_via_module_invocation(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "tools.proto_gate"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "fit_003: PASS" in proc.stdout
        assert "nfr_010: PASS" in proc.stdout

    def test_fit_003_clean_on_repository(self, gate: ModuleType) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            gate.compile_protos(Path(tmp))
            assert gate.check_fit_003(Path(tmp)) == []


class TestManifestShape:
    def test_all_cio_messages_present(self, manifest: dict[str, Any]) -> None:
        names = set(manifest["messages"])
        expected = {
            "afrp.v1.CognitiveEnvelope",
            "afrp.v1.RawObservation",
            "afrp.v1.StandardFeature",
            "afrp.v1.DomainBelief",
            "afrp.v1.WorldStateVector",
            "afrp.v1.ScenarioSet",
            "afrp.v1.ScenarioSet.Scenario",
            "afrp.v1.DecisionContext",
            "afrp.v1.ExecutionCandidate",
            "afrp.v1.AuthorizedAction",
            "afrp.v1.ExecutionIntent",
            "afrp.v1.ExecutionReport",
            "afrp.v1.PortfolioState",
            "afrp.v1.PortfolioState.Position",
            "afrp.v1.CalibrationWeights",
            "afrp.v1.EpisodicEmbedding",
        }
        assert expected <= names

    def test_envelope_matches_ref_001(self, manifest: dict[str, Any]) -> None:
        envelope = manifest["messages"]["afrp.v1.CognitiveEnvelope"]
        assert envelope["1"][0] == "message_id"
        assert envelope["2"][0] == "cognitive_cycle_id"
        assert envelope["9"] == ["payload_hash", "TYPE_BYTES", "LABEL_OPTIONAL"]
        assert envelope["10"][0] == "trace_id"
        assert envelope["11"][0] == "span_id"
        assert len(envelope) == 11

    def test_snapshot_matches_current_contracts(self, manifest: dict[str, Any]) -> None:
        snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        assert snapshot["messages"] == manifest["messages"]


class TestNfr010Compatibility:
    def test_identity_is_compatible(self, gate: ModuleType, manifest: dict[str, Any]) -> None:
        assert gate.check_compatibility(manifest, manifest) == []

    def test_added_field_is_compatible(self, gate: ModuleType, manifest: dict[str, Any]) -> None:
        grown = copy.deepcopy(manifest)
        grown["messages"]["afrp.v1.RawObservation"]["99"] = [
            "extra", "TYPE_STRING", "LABEL_OPTIONAL",
        ]
        assert gate.check_compatibility(grown, manifest) == []

    def test_removed_message_detected(self, gate: ModuleType, manifest: dict[str, Any]) -> None:
        broken = copy.deepcopy(manifest)
        del broken["messages"]["afrp.v1.DomainBelief"]
        problems = gate.check_compatibility(broken, manifest)
        assert any("message removed" in p for p in problems)

    def test_removed_field_detected(self, gate: ModuleType, manifest: dict[str, Any]) -> None:
        broken = copy.deepcopy(manifest)
        del broken["messages"]["afrp.v1.CognitiveEnvelope"]["9"]
        problems = gate.check_compatibility(broken, manifest)
        assert any("payload_hash" in p for p in problems)

    def test_retyped_field_detected(self, gate: ModuleType, manifest: dict[str, Any]) -> None:
        broken = copy.deepcopy(manifest)
        broken["messages"]["afrp.v1.CognitiveEnvelope"]["1"] = [
            "message_id", "TYPE_INT64", "LABEL_OPTIONAL",
        ]
        problems = gate.check_compatibility(broken, manifest)
        assert any("changed" in p for p in problems)

    def test_renamed_field_detected(self, gate: ModuleType, manifest: dict[str, Any]) -> None:
        broken = copy.deepcopy(manifest)
        broken["messages"]["afrp.v1.CognitiveEnvelope"]["1"] = [
            "msg_id", "TYPE_STRING", "LABEL_OPTIONAL",
        ]
        problems = gate.check_compatibility(broken, manifest)
        assert any("changed" in p for p in problems)
