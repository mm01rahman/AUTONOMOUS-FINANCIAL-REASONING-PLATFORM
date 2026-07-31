"""Machine-enforced AFRP operations posture (WP-IMP-0032).

Validates NFR-002/005/006/007 operational policy, the non-root production
image, and CI coverage of every mandatory repository gate.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = REPO_ROOT / "08-operations" / "policies"


def _load(name: str) -> dict[str, Any]:
    path = POLICY_DIR / name
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{name}: root must be a mapping")
    if loaded.get("schema_version") != "1.0":
        raise ValueError(f"{name}: schema_version must be '1.0'")
    return loaded


def validate_security(policy: dict[str, Any]) -> list[str]:
    """NFR-006 and EDR-008 posture."""
    errors: list[str] = []
    zero = policy.get("zero_trust", {})
    tls = zero.get("tls", {})
    identity = zero.get("workload_identity", {})
    if zero.get("default_deny") is not True:
        errors.append("security: default_deny must be true")
    if zero.get("internal_transport") != "grpc":
        errors.append("security: internal_transport must be grpc")
    if tls.get("minimum_version") != "1.3":
        errors.append("security: TLS minimum must be 1.3")
    if tls.get("mutual_authentication_required") is not True:
        errors.append("security: mTLS is mandatory")
    if identity.get("provider") != "SPIFFE":
        errors.append("security: workload identity provider must be SPIFFE")
    if not str(identity.get("trust_domain", "")).strip():
        errors.append("security: SPIFFE trust domain is required")
    if int(identity.get("certificate_ttl_seconds", 0)) > 3600:
        errors.append("security: workload certificates must rotate within one hour")
    sources = set(zero.get("secret_sources", []))
    if not sources or not sources <= {"Vault", "environment"}:
        errors.append("security: secrets may come only from Vault/environment")
    if zero.get("hardcoded_secrets_allowed") is not False:
        errors.append("security: hardcoded secrets must be prohibited")
    return errors


def validate_availability(policy: dict[str, Any]) -> list[str]:
    """NFR-002 active-passive availability posture."""
    errors: list[str] = []
    availability = policy.get("availability", {})
    election = availability.get("leader_election", {})
    failover = availability.get("failover", {})
    if float(availability.get("target_percent", 0.0)) < 99.99:
        errors.append("availability: target must be at least 99.99%")
    if availability.get("topology") != "active-passive":
        errors.append("availability: topology must be active-passive")
    if int(availability.get("minimum_replicas", 0)) < 2:
        errors.append("availability: at least two replicas required")
    if availability.get("anti_affinity_required") is not True:
        errors.append("availability: replica anti-affinity required")
    if election.get("mechanism") != "durable-lease":
        errors.append("availability: durable leader lease required")
    if election.get("fencing_token_required") is not True:
        errors.append("availability: fencing token required")
    ttl = int(election.get("lease_ttl_seconds", 0))
    heartbeat = int(election.get("heartbeat_seconds", 0))
    if ttl <= 0 or heartbeat <= 0 or heartbeat >= ttl:
        errors.append("availability: require 0 < heartbeat < lease TTL")
    if int(failover.get("maximum_seconds", 60)) >= 60:
        errors.append("availability: failover must complete in under 60s")
    if failover.get("readiness_validation_required") is not True:
        errors.append("availability: readiness validation required")
    return errors


def validate_recovery(policy: dict[str, Any]) -> list[str]:
    """NFR-005 recovery posture."""
    errors: list[str] = []
    recovery = policy.get("recovery", {})
    if int(recovery.get("rpo_lost_trades", -1)) != 0:
        errors.append("recovery: RPO must be zero lost trades")
    if not 0 < int(recovery.get("rto_seconds", 0)) < 60:
        errors.append("recovery: RTO must be in (0,60) seconds")
    if recovery.get("order_event_writes") != "synchronous":
        errors.append("recovery: order event writes must be synchronous")
    if recovery.get("sqlite_synchronous_mode") != "FULL":
        errors.append("recovery: SQLite synchronous mode must be FULL")
    if recovery.get("checkpoint_every_order_event") is not True:
        errors.append("recovery: every order event must checkpoint")
    if recovery.get("restore_validation_required") is not True:
        errors.append("recovery: restore validation required")
    return errors


def validate_observability(policy: dict[str, Any]) -> list[str]:
    """EDR-006 and NFR-007 observability posture."""
    errors: list[str] = []
    obs = policy.get("observability", {})
    if obs.get("log_schema") != "OBS-01":
        errors.append("observability: OBS-01 required")
    for key in (
        "structured_json_required",
        "opentelemetry_required",
        "trace_every_order",
        "hmac_audit_every_order",
    ):
        if obs.get(key) is not True:
            errors.append(f"observability: {key} must be true")
    return errors


def validate_container(dockerfile: str) -> list[str]:
    """Non-root, pinned-build production image posture."""
    errors: list[str] = []
    if "FROM python:3.11-slim" not in dockerfile:
        errors.append("container: Python base must pin the 3.11 line")
    if "uv sync --frozen --no-dev" not in dockerfile:
        errors.append("container: production dependencies must use frozen lock")
    if "USER 10001:10001" not in dockerfile:
        errors.append("container: runtime must use non-root uid/gid 10001")
    if "HEALTHCHECK" not in dockerfile or 'CMD ["afrp", "boot"]' not in dockerfile:
        errors.append("container: governed afrp boot healthcheck required")
    return errors


def validate_ci(workflow: str) -> list[str]:
    """Ensure CI runs every mandatory quality/fitness gate."""
    required = (
        "uv sync --frozen --group dev",
        "uv run ruff check .",
        "uv run mypy --strict",
        "uv run pytest tests",
        "uv run python -m tools.proto_gate",
        "uv run python -m tools.ops_gate",
        "uv run afrp boot",
        "uv run afrp plan",
        "uv run afrp validate",
        "uv run afrp health",
    )
    return [f"ci: missing command {command!r}" for command in required if command not in workflow]


def validate_repository(repo_root: Path = REPO_ROOT) -> list[str]:
    """Run all operations checks and return violations."""
    errors = [
        *validate_security(_load("security.yaml")),
        *validate_availability(_load("high-availability.yaml")),
        *validate_recovery(_load("recovery.yaml")),
        *validate_observability(_load("observability.yaml")),
    ]
    dockerfile = (
        repo_root / "08-operations" / "docker" / "Dockerfile"
    ).read_text(encoding="utf-8")
    workflow = (
        repo_root / ".github" / "workflows" / "quality.yml"
    ).read_text(encoding="utf-8")
    errors.extend(validate_container(dockerfile))
    errors.extend(validate_ci(workflow))
    return errors


def main() -> int:
    """CLI entry point."""
    errors = validate_repository()
    if errors:
        print(f"ops_gate: FAIL ({len(errors)} violation(s))")
        for error in errors:
            print(f"  {error}")
        return 1
    print("ops_gate: PASS")
    print("  NFR-002: active-passive 99.99% posture")
    print("  NFR-005: RPO=0 / RTO<60s posture")
    print("  NFR-006: TLS1.3 mTLS + SPIFFE posture")
    print("  NFR-007: HMAC + OpenTelemetry order posture")
    print("  container: non-root frozen build")
    print("  ci: mandatory quality and fitness gates present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
