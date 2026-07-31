"""Capability registry parser and execution DAG engine (WP-IMP-0004, FR-002).

Parses ``03-engineering/CAPABILITY_REGISTRY.yaml`` into typed models, builds
the execution DAG, enforces FIT-001 (acyclicity), and computes the next
executable targets for the orchestrator.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import yaml
from afrp.core.exceptions import (
    ContractReferenceError,
    InvariantError,
    ManifestValidationError,
)
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

SUPPORTED_SCHEMA_VERSION = "1.0"


class CapabilityStatus(StrEnum):
    """Lifecycle status of a capability inside the registry."""

    COMPLETE = "COMPLETE"
    AVAILABLE = "AVAILABLE"
    LOCKED = "LOCKED"


class Capability(BaseModel):
    """A single node of the capability execution DAG (GLOSS-001 item 12)."""

    model_config = ConfigDict(frozen=True)

    id: str
    version: str
    title: str
    owner: str
    status: CapabilityStatus
    depends_on: tuple[str, ...]
    work_package: str | None


class CapabilityRegistry(BaseModel):
    """The authoritative dependency graph ledger."""

    model_config = ConfigDict(frozen=True)

    schema_version: str
    registry_id: str
    capabilities: tuple[Capability, ...]

    @field_validator("schema_version")
    @classmethod
    def _schema_version_supported(cls, value: str) -> str:
        if value != SUPPORTED_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version {value!r}; expected {SUPPORTED_SCHEMA_VERSION!r}"
            )
        return value

    def by_id(self) -> dict[str, Capability]:
        """Index capabilities by id."""
        return {c.id: c for c in self.capabilities}


def load_registry(path: Path) -> CapabilityRegistry:
    """Load and validate the capability registry at ``path``.

    Raises:
        ContractReferenceError: the registry file does not exist.
        ManifestValidationError: YAML malformed, model invalid, duplicate ids,
            or dangling ``depends_on`` references.
    """
    if not path.is_file():
        raise ContractReferenceError(str(path))
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestValidationError(f"YAML parse failure: {exc}") from exc
    if not isinstance(raw, dict):
        raise ManifestValidationError("registry root must be a mapping")
    try:
        registry = CapabilityRegistry.model_validate(raw)
    except ValidationError as exc:
        raise ManifestValidationError(str(exc)) from exc

    seen: set[str] = set()
    for cap in registry.capabilities:
        if cap.id in seen:
            raise ManifestValidationError(f"duplicate capability id {cap.id!r}")
        seen.add(cap.id)
    for cap in registry.capabilities:
        for dep in cap.depends_on:
            if dep not in seen:
                raise ManifestValidationError(
                    f"capability {cap.id!r} depends on unknown capability {dep!r}"
                )
    return registry


def assert_acyclic(registry: CapabilityRegistry) -> tuple[str, ...]:
    """FIT-001: Kahn topological sort; return a valid execution order.

    Raises:
        InvariantError: the graph contains at least one dependency cycle;
            the offending capability ids are reported in the detail.
    """
    nodes = registry.by_id()
    indegree: dict[str, int] = {cid: len(cap.depends_on) for cid, cap in nodes.items()}
    dependents: dict[str, list[str]] = {cid: [] for cid in nodes}
    for cap in registry.capabilities:
        for dep in cap.depends_on:
            dependents[dep].append(cap.id)

    queue = sorted(cid for cid, deg in indegree.items() if deg == 0)
    order: list[str] = []
    while queue:
        current = queue.pop(0)
        order.append(current)
        for child in sorted(dependents[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
        queue.sort()

    if len(order) != len(nodes):
        cycle_members = sorted(cid for cid, deg in indegree.items() if deg > 0)
        raise InvariantError(
            "FIT-001",
            f"capability graph contains a cycle among: {', '.join(cycle_members)}",
        )
    return tuple(order)


def next_executable(registry: CapabilityRegistry) -> tuple[Capability, ...]:
    """Capabilities not COMPLETE whose dependencies are all COMPLETE."""
    nodes = registry.by_id()
    ready = [
        cap
        for cap in registry.capabilities
        if cap.status is not CapabilityStatus.COMPLETE
        and all(nodes[d].status is CapabilityStatus.COMPLETE for d in cap.depends_on)
    ]
    return tuple(sorted(ready, key=lambda c: c.id))
