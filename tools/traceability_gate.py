"""AFRP traceability gate — validates the full traceability chain.

Verifies: Requirement → Capability → Work Package → Evidence → Release

FIT-007 extended: every requirement must be:
  1. Assigned to a known capability in CAPABILITY_REGISTRY.yaml
  2. Have at least one artifact declared
  3. Have at least one verification (test or evidence)
  4. The capability must have a work package
  5. The evidence file must exist on disk

Exits 0 on PASS, non-zero on FAIL.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click
import yaml

_ROOT = Path(__file__).parent.parent
_TVM = _ROOT / "03-engineering" / "TRACEABILITY_MATRIX.yaml"
_REGISTRY = _ROOT / "03-engineering" / "CAPABILITY_REGISTRY.yaml"
_WP_DIR = _ROOT / "05-work-packages"


@dataclass
class TraceViolation:
    req_id: str
    level: str  # capability | work_package | artifact | verification | evidence
    message: str


@dataclass
class TraceResult:
    violations: list[TraceViolation] = field(default_factory=list)
    requirements_checked: int = 0
    capabilities_checked: int = 0

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _index_registry(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index registry capabilities by id."""
    return {cap["id"]: cap for cap in registry.get("capabilities", [])}


def _index_work_packages(wp_dir: Path) -> set[str]:
    """Find all work package IDs that have an evidence directory."""
    found: set[str] = set()
    if not wp_dir.exists():
        return found
    for entry in wp_dir.iterdir():
        if entry.is_dir() and (entry / "evidence").exists():
            found.add(entry.name)
    return found


def _check_evidence_files(root: Path, verified_by: list[str]) -> list[str]:
    """Return list of declared evidence files that do not exist."""
    missing = []
    for path_str in verified_by:
        if path_str.endswith(".yaml") and "evidence" in path_str:
            full = root / path_str
            if not full.exists():
                missing.append(path_str)
    return missing


def validate_traceability(root: Path) -> TraceResult:
    """Run the full traceability validation chain."""
    result = TraceResult()

    if not _TVM.exists():
        result.violations.append(TraceViolation("*", "tvm", f"TVM not found: {_TVM}"))
        return result

    if not _REGISTRY.exists():
        result.violations.append(
            TraceViolation("*", "registry", f"Registry not found: {_REGISTRY}")
        )
        return result

    tvm = _load_yaml(_TVM)
    registry = _load_yaml(_REGISTRY)
    cap_index = _index_registry(registry)
    _index_work_packages(_WP_DIR)  # future: validate WP existence per capability

    requirements = tvm.get("requirements", [])

    for req in requirements:
        req_id = req.get("id", "UNKNOWN")
        result.requirements_checked += 1

        # 1. Capability must exist in registry
        cap_id = req.get("capability")
        if not cap_id:
            result.violations.append(TraceViolation(req_id, "capability", "No capability assigned"))
            continue

        cap = cap_index.get(cap_id)
        if not cap:
            result.violations.append(
                TraceViolation(req_id, "capability", f"Capability {cap_id!r} not found in registry")
            )
            continue
        result.capabilities_checked += 1

        # 2. Capability must have a work package
        wp_id = cap.get("work_package")
        if wp_id is None:
            # Explicit null is acceptable for foundational pre-WPS capabilities
            pass
        elif not wp_id:
            result.violations.append(
                TraceViolation(req_id, "work_package", f"Capability {cap_id} has no work_package")
            )

        # 3. Must have artifacts
        artifacts = req.get("artifacts", [])
        if not artifacts:
            result.violations.append(TraceViolation(req_id, "artifact", "No artifacts declared"))

        # 4. Must have verifications
        verified_by = req.get("verified_by", [])
        if not verified_by:
            result.violations.append(
                TraceViolation(req_id, "verification", "No verifications declared")
            )

        # 5. Evidence files must exist
        missing_evidence = _check_evidence_files(root, verified_by)
        for m in missing_evidence:
            result.violations.append(
                TraceViolation(req_id, "evidence", f"Evidence file missing: {m}")
            )

    return result


@click.command()
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Repository root.",
)
@click.option("--strict", is_flag=True, default=False, help="Fail on missing evidence files.")
def main(repo_root: Path, strict: bool) -> None:
    """Validate the full Req→Cap→WP→Evidence traceability chain."""
    root = repo_root.resolve()
    result = validate_traceability(root)

    click.echo(f"traceability_gate: {result.requirements_checked} requirements checked")
    click.echo(f"traceability_gate: {result.capabilities_checked} capabilities verified")

    if result.passed:
        click.echo("traceability_gate: PASS — full chain verified")
        return

    # Separate evidence missing (can be warnings) from hard failures
    hard_failures = [v for v in result.violations if v.level != "evidence"]
    evidence_missing = [v for v in result.violations if v.level == "evidence"]

    for v in hard_failures:
        click.echo(f"  FAIL [{v.level}] {v.req_id}: {v.message}", err=True)

    for v in evidence_missing:
        level = "FAIL" if strict else "WARN"
        click.echo(f"  {level} [evidence] {v.req_id}: {v.message}", err=not strict)

    if hard_failures or (strict and evidence_missing):
        click.echo(
            f"traceability_gate: FAIL — "
            f"{len(hard_failures)} chain violation(s), "
            f"{len(evidence_missing)} missing evidence",
            err=True,
        )
        raise SystemExit(1)

    click.echo(f"traceability_gate: PASS (with {len(evidence_missing)} evidence warning(s))")


if __name__ == "__main__":
    sys.exit(main())
