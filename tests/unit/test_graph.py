"""Unit tests for WP-IMP-0004: afrp plan and the capability DAG engine."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from afrp.cli import cli
from afrp.core.exceptions import (
    ContractReferenceError,
    InvariantError,
    ManifestValidationError,
)
from afrp.core.registry import (
    CapabilityStatus,
    assert_acyclic,
    load_registry,
    next_executable,
)
from click.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[2]


def make_registry(caps: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "registry_id": "CAPABILITY_REGISTRY",
        "capabilities": caps,
    }


def cap(
    cid: str,
    deps: list[str],
    status: str = "LOCKED",
    wp: str | None = None,
) -> dict[str, object]:
    return {
        "id": cid,
        "version": "1.0",
        "title": f"capability {cid}",
        "owner": "TEST",
        "status": status,
        "depends_on": deps,
        "work_package": wp,
    }


def write_registry(path: Path, data: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


class TestRegistryParser:
    def test_parses_real_repository_registry(self) -> None:
        registry = load_registry(REPO_ROOT / "03-engineering" / "CAPABILITY_REGISTRY.yaml")
        ids = {c.id for c in registry.capabilities}
        assert {"GOV-BASELINE", "EOS-BOOT", "EOS-CONTEXT", "L3-WRM", "L5-EXE"} <= ids
        assert registry.by_id()["EOS-CONTEXT"].status is CapabilityStatus.COMPLETE

    def test_missing_registry_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ContractReferenceError):
            load_registry(tmp_path / "absent.yaml")

    def test_wrong_schema_version_rejected(self, tmp_path: Path) -> None:
        data = make_registry([cap("A", [])])
        data["schema_version"] = "9.9"
        target = tmp_path / "reg.yaml"
        write_registry(target, data)
        with pytest.raises(ManifestValidationError):
            load_registry(target)

    def test_duplicate_ids_rejected(self, tmp_path: Path) -> None:
        target = tmp_path / "reg.yaml"
        write_registry(target, make_registry([cap("A", []), cap("A", [])]))
        with pytest.raises(ManifestValidationError, match="duplicate"):
            load_registry(target)

    def test_dangling_dependency_rejected(self, tmp_path: Path) -> None:
        target = tmp_path / "reg.yaml"
        write_registry(target, make_registry([cap("A", ["GHOST"])]))
        with pytest.raises(ManifestValidationError, match="unknown capability"):
            load_registry(target)

    def test_invalid_status_rejected(self, tmp_path: Path) -> None:
        target = tmp_path / "reg.yaml"
        write_registry(target, make_registry([cap("A", [], status="WEIRD")]))
        with pytest.raises(ManifestValidationError):
            load_registry(target)


class TestFit001Acyclicity:
    def test_real_registry_is_acyclic(self) -> None:
        registry = load_registry(REPO_ROOT / "03-engineering" / "CAPABILITY_REGISTRY.yaml")
        order = assert_acyclic(registry)
        assert len(order) == len(registry.capabilities)
        # dependency order respected
        pos = {cid: i for i, cid in enumerate(order)}
        for c in registry.capabilities:
            for dep in c.depends_on:
                assert pos[dep] < pos[c.id]

    def test_simple_cycle_detected(self, tmp_path: Path) -> None:
        target = tmp_path / "reg.yaml"
        write_registry(
            target,
            make_registry([cap("A", ["B"]), cap("B", ["A"])]),
        )
        registry = load_registry(target)
        with pytest.raises(InvariantError) as excinfo:
            assert_acyclic(registry)
        assert excinfo.value.invariant == "FIT-001"
        assert "A" in excinfo.value.detail and "B" in excinfo.value.detail

    def test_self_loop_detected(self, tmp_path: Path) -> None:
        target = tmp_path / "reg.yaml"
        write_registry(target, make_registry([cap("A", ["A"])]))
        registry = load_registry(target)
        with pytest.raises(InvariantError):
            assert_acyclic(registry)

    def test_three_node_cycle_reports_members(self, tmp_path: Path) -> None:
        target = tmp_path / "reg.yaml"
        write_registry(
            target,
            make_registry(
                [cap("A", ["C"]), cap("B", ["A"]), cap("C", ["B"]), cap("D", [])]
            ),
        )
        registry = load_registry(target)
        with pytest.raises(InvariantError) as excinfo:
            assert_acyclic(registry)
        for member in ("A", "B", "C"):
            assert member in excinfo.value.detail
        assert "D" not in excinfo.value.detail

    def test_topological_order_deterministic(self, tmp_path: Path) -> None:
        target = tmp_path / "reg.yaml"
        write_registry(
            target,
            make_registry([cap("B", []), cap("A", []), cap("C", ["A", "B"])]),
        )
        registry = load_registry(target)
        assert assert_acyclic(registry) == ("A", "B", "C")


class TestNextExecutable:
    def test_ready_set_requires_all_deps_complete(self, tmp_path: Path) -> None:
        target = tmp_path / "reg.yaml"
        write_registry(
            target,
            make_registry(
                [
                    cap("A", [], status="COMPLETE"),
                    cap("B", ["A"], status="AVAILABLE", wp="WP-IMP-9001"),
                    cap("C", ["B"], status="LOCKED"),
                    cap("D", ["A"], status="LOCKED"),
                ]
            ),
        )
        registry = load_registry(target)
        ready = next_executable(registry)
        assert [c.id for c in ready] == ["B", "D"]

    def test_all_complete_yields_empty(self, tmp_path: Path) -> None:
        target = tmp_path / "reg.yaml"
        write_registry(
            target,
            make_registry([cap("A", [], status="COMPLETE")]),
        )
        assert next_executable(load_registry(target)) == ()

    def test_real_registry_next_targets(self) -> None:
        registry = load_registry(REPO_ROOT / "03-engineering" / "CAPABILITY_REGISTRY.yaml")
        ready = next_executable(registry)
        nodes = registry.by_id()
        # Stable invariant: every ready target is not COMPLETE and has only
        # COMPLETE dependencies, regardless of build progress.
        for capability in ready:
            assert capability.status is not CapabilityStatus.COMPLETE
            for dep in capability.depends_on:
                assert nodes[dep].status is CapabilityStatus.COMPLETE
        incomplete = [c for c in registry.capabilities if c.status is not CapabilityStatus.COMPLETE]
        assert bool(ready) == bool(incomplete)


class TestPlanCommand:
    def test_plan_passes_on_real_repository(self) -> None:
        runner = CliRunner()
        outcome = runner.invoke(cli, ["plan", "--repo-root", str(REPO_ROOT)])
        assert outcome.exit_code == 0, outcome.output
        assert "fit_001: PASS" in outcome.output
        assert "next_executable:" in outcome.output

    def test_plan_halts_on_cyclic_registry(self, tmp_path: Path) -> None:
        eng = tmp_path / "03-engineering"
        eng.mkdir()
        write_registry(
            eng / "CAPABILITY_REGISTRY.yaml",
            make_registry([cap("A", ["B"]), cap("B", ["A"])]),
        )
        runner = CliRunner()
        outcome = runner.invoke(cli, ["plan", "--repo-root", str(tmp_path)])
        assert outcome.exit_code == 3
        assert "HALTED" in outcome.output
        assert "FIT-001" in outcome.output

    def test_plan_halts_on_missing_registry(self, tmp_path: Path) -> None:
        runner = CliRunner()
        outcome = runner.invoke(cli, ["plan", "--repo-root", str(tmp_path)])
        assert outcome.exit_code == 2
        assert "HALTED" in outcome.output
