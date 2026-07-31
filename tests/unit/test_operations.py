"""Tests for machine-enforced AFRP operations posture."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
OPS_GATE_PATH = REPO_ROOT / "tools" / "ops_gate.py"

def load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("ops_gate", OPS_GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OPS = load_gate()
POLICY_DIR: Path = OPS.POLICY_DIR


def policy(name: str) -> dict[str, Any]:
    loaded = yaml.safe_load((POLICY_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


class TestRealPosture:
    def test_repository_operations_gate_passes(self) -> None:
        assert OPS.validate_repository(REPO_ROOT) == []

    def test_security_policy_passes(self) -> None:
        assert OPS.validate_security(policy("security.yaml")) == []

    def test_availability_policy_passes(self) -> None:
        assert OPS.validate_availability(policy("high-availability.yaml")) == []

    def test_recovery_policy_passes(self) -> None:
        assert OPS.validate_recovery(policy("recovery.yaml")) == []

    def test_observability_policy_passes(self) -> None:
        assert OPS.validate_observability(policy("observability.yaml")) == []


class TestSecurityFailures:
    def test_tls_downgrade_detected(self) -> None:
        candidate = copy.deepcopy(policy("security.yaml"))
        candidate["zero_trust"]["tls"]["minimum_version"] = "1.2"
        assert any("TLS" in error for error in OPS.validate_security(candidate))

    def test_mtls_disable_detected(self) -> None:
        candidate = copy.deepcopy(policy("security.yaml"))
        candidate["zero_trust"]["tls"]["mutual_authentication_required"] = False
        assert any("mTLS" in error for error in OPS.validate_security(candidate))

    def test_non_spiffe_identity_detected(self) -> None:
        candidate = copy.deepcopy(policy("security.yaml"))
        candidate["zero_trust"]["workload_identity"]["provider"] = "static-cert"
        assert any("SPIFFE" in error for error in OPS.validate_security(candidate))

    def test_illegal_secret_source_detected(self) -> None:
        candidate = copy.deepcopy(policy("security.yaml"))
        candidate["zero_trust"]["secret_sources"].append("source-code")
        assert any("secrets" in error for error in OPS.validate_security(candidate))


class TestAvailabilityFailures:
    def test_single_replica_detected(self) -> None:
        candidate = copy.deepcopy(policy("high-availability.yaml"))
        candidate["availability"]["minimum_replicas"] = 1
        assert OPS.validate_availability(candidate)

    def test_active_active_detected(self) -> None:
        candidate = copy.deepcopy(policy("high-availability.yaml"))
        candidate["availability"]["topology"] = "active-active"
        assert any(
            "active-passive" in error
            for error in OPS.validate_availability(candidate)
        )

    def test_bad_lease_timing_detected(self) -> None:
        candidate = copy.deepcopy(policy("high-availability.yaml"))
        candidate["availability"]["leader_election"]["heartbeat_seconds"] = 20
        assert any(
            "heartbeat" in error
            for error in OPS.validate_availability(candidate)
        )

    def test_slow_failover_detected(self) -> None:
        candidate = copy.deepcopy(policy("high-availability.yaml"))
        candidate["availability"]["failover"]["maximum_seconds"] = 60
        assert any(
            "under 60" in error
            for error in OPS.validate_availability(candidate)
        )


class TestRecoveryAndObservabilityFailures:
    def test_nonzero_rpo_detected(self) -> None:
        candidate = copy.deepcopy(policy("recovery.yaml"))
        candidate["recovery"]["rpo_lost_trades"] = 1
        assert any("RPO" in error for error in OPS.validate_recovery(candidate))

    def test_rto_boundary_detected(self) -> None:
        candidate = copy.deepcopy(policy("recovery.yaml"))
        candidate["recovery"]["rto_seconds"] = 60
        assert any("RTO" in error for error in OPS.validate_recovery(candidate))

    def test_async_write_detected(self) -> None:
        candidate = copy.deepcopy(policy("recovery.yaml"))
        candidate["recovery"]["order_event_writes"] = "asynchronous"
        assert any(
            "synchronous" in error for error in OPS.validate_recovery(candidate)
        )

    def test_missing_order_trace_detected(self) -> None:
        candidate = copy.deepcopy(policy("observability.yaml"))
        candidate["observability"]["trace_every_order"] = False
        assert any(
            "trace_every_order" in error
            for error in OPS.validate_observability(candidate)
        )


class TestContainerAndCi:
    def test_root_container_detected(self) -> None:
        dockerfile = "FROM python:3.11-slim\nRUN uv sync --frozen --no-dev\n"
        errors = OPS.validate_container(dockerfile)
        assert any("non-root" in error for error in errors)

    def test_missing_ci_gate_detected(self) -> None:
        workflow = "uv sync --frozen --group dev\nuv run pytest tests\n"
        errors = OPS.validate_ci(workflow)
        assert any("ruff" in error for error in errors)
