"""AFRP Architecture Baseline v1.0.0 governance gate.

Validates protected artifact existence, standardized metadata, singular concern
ownership, acyclic ownership dependencies, Phase 1 front matter, exact SHA256
fingerprints, duplicate content, and the KERNEL word budget.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = REPO_ROOT / "docs" / "governance" / "DOCUMENT_METADATA.yaml"
SOURCE_MAP_PATH = REPO_ROOT / "docs" / "governance" / "CANONICAL_SOURCE_MAP.yaml"
FINGERPRINT_PATH = (
    REPO_ROOT / "docs" / "governance" / "ARCHITECTURE_BASELINE_FINGERPRINT.yaml"
)
SELF_FINGERPRINT_PATH = "docs/governance/ARCHITECTURE_BASELINE_FINGERPRINT.yaml"

_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping."""
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return loaded


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA256 digest of ``path``."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference_exists(reference: str, repo_root: Path = REPO_ROOT) -> bool:
    """Resolve a metadata path, directory, glob, or path fragment."""
    path = reference.split("#", maxsplit=1)[0].rstrip("/")
    if any(character in path for character in "*?["):
        return any(repo_root.glob(path))
    return (repo_root / path).exists()


def validate_metadata(
    data: dict[str, Any], repo_root: Path = REPO_ROOT
) -> list[str]:
    """Validate metadata schema, identity uniqueness, fields, and existence."""
    errors: list[str] = []
    if data.get("schema_version") != "1.0":
        errors.append("metadata: schema_version must be 1.0")
    required = data.get("required_fields")
    documents = data.get("documents")
    if not isinstance(required, list) or not all(
        isinstance(field, str) for field in required
    ):
        return [*errors, "metadata: required_fields must be a string list"]
    if not isinstance(documents, list):
        return [*errors, "metadata: documents must be a list"]

    paths: set[str] = set()
    document_ids: set[str] = set()
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            errors.append(f"metadata: document #{index} must be a mapping")
            continue
        path = document.get("path")
        document_id = document.get("document_id")
        if not isinstance(path, str) or not path:
            errors.append(f"metadata: document #{index} missing path")
            continue
        if path in paths:
            errors.append(f"metadata: duplicate path {path}")
        paths.add(path)
        if not isinstance(document_id, str) or not document_id:
            errors.append(f"metadata: {path} missing document_id")
        elif document_id in document_ids:
            errors.append(f"metadata: duplicate document_id {document_id}")
        else:
            document_ids.add(document_id)

        for field in required:
            if field not in document:
                errors.append(f"metadata: {path} missing {field}")
        for field in (
            "title",
            "version",
            "status",
            "owner",
            "authority",
            "approved_date",
            "last_modified",
            "change_policy",
            "review_policy",
        ):
            if not isinstance(document.get(field), str) or not document[field].strip():
                errors.append(f"metadata: {path} has empty/invalid {field}")
        for field in ("dependencies", "referenced_by"):
            if not isinstance(document.get(field), list):
                errors.append(f"metadata: {path} {field} must be a list")
                continue
            for reference in document[field]:
                if not isinstance(reference, str) or not reference:
                    errors.append(f"metadata: {path} has invalid {field} reference")
                elif not reference_exists(reference, repo_root):
                    errors.append(
                        f"metadata: {path} unresolved {field} reference: {reference}"
                    )
        if not (repo_root / path).is_file():
            errors.append(f"metadata: protected artifact missing: {path}")
    return errors


def validate_source_map(
    data: dict[str, Any], repo_root: Path = REPO_ROOT
) -> list[str]:
    """Validate unique concerns, owner resolution, dependencies, and acyclicity."""
    errors: list[str] = []
    concerns = data.get("concerns")
    if data.get("schema_version") != "1.0":
        errors.append("source_map: schema_version must be 1.0")
    if not isinstance(concerns, list):
        return [*errors, "source_map: concerns must be a list"]

    by_id: dict[str, dict[str, Any]] = {}
    for index, concern in enumerate(concerns):
        if not isinstance(concern, dict):
            errors.append(f"source_map: concern #{index} must be a mapping")
            continue
        concern_id = concern.get("id")
        if not isinstance(concern_id, str) or not concern_id:
            errors.append(f"source_map: concern #{index} missing id")
            continue
        if concern_id in by_id:
            errors.append(f"source_map: duplicate concern id {concern_id}")
        by_id[concern_id] = concern
        owner = concern.get("owner")
        if not isinstance(owner, str) or not owner:
            errors.append(f"source_map: {concern_id} must have exactly one owner")
            continue
        owner_path = owner.split("#", maxsplit=1)[0].rstrip("/")
        if not (repo_root / owner_path).exists():
            errors.append(f"source_map: {concern_id} owner does not exist: {owner}")

    indegree = {concern_id: 0 for concern_id in by_id}
    dependents: dict[str, list[str]] = {
        concern_id: [] for concern_id in by_id
    }
    for concern_id, concern in by_id.items():
        dependencies = concern.get("depends_on")
        if not isinstance(dependencies, list):
            errors.append(f"source_map: {concern_id} depends_on must be a list")
            continue
        for dependency in dependencies:
            if dependency not in by_id:
                errors.append(
                    f"source_map: {concern_id} depends on unknown concern {dependency}"
                )
                continue
            indegree[concern_id] += 1
            dependents[dependency].append(concern_id)

    queue = sorted(key for key, value in indegree.items() if value == 0)
    visited: list[str] = []
    while queue:
        current = queue.pop(0)
        visited.append(current)
        for child in sorted(dependents[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
        queue.sort()
    if len(visited) != len(by_id):
        cycle = sorted(key for key, value in indegree.items() if value > 0)
        errors.append(f"source_map: dependency cycle among {', '.join(cycle)}")
    return errors


def metadata_paths(data: dict[str, Any]) -> set[str]:
    """Return protected paths declared by the metadata registry."""
    documents = data.get("documents", [])
    return {
        str(document["path"])
        for document in documents
        if isinstance(document, dict) and "path" in document
    }


def validate_fingerprint(
    data: dict[str, Any],
    protected_paths: set[str],
    repo_root: Path = REPO_ROOT,
) -> list[str]:
    """Validate fingerprint coverage and SHA256 values."""
    errors: list[str] = []
    if data.get("schema_version") != "1.0":
        errors.append("fingerprint: schema_version must be 1.0")
    if data.get("hash_algorithm") != "sha256":
        errors.append("fingerprint: hash_algorithm must be sha256")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        return [*errors, "fingerprint: artifacts must be a list"]

    expected = protected_paths - {SELF_FINGERPRINT_PATH}
    seen: set[str] = set()
    hashes: dict[str, list[str]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            errors.append("fingerprint: artifact must be a mapping")
            continue
        path = artifact.get("path")
        digest = artifact.get("sha256")
        if not isinstance(path, str) or not isinstance(digest, str):
            errors.append("fingerprint: artifact path/sha256 must be strings")
            continue
        if path in seen:
            errors.append(f"fingerprint: duplicate path {path}")
        seen.add(path)
        target = repo_root / path
        if not target.is_file():
            errors.append(f"fingerprint: protected artifact missing: {path}")
            continue
        actual = sha256_file(target)
        if actual != digest:
            errors.append(f"fingerprint: digest mismatch: {path}")
        hashes.setdefault(actual, []).append(path)

    missing = sorted(expected - seen)
    extra = sorted(seen - expected)
    for path in missing:
        errors.append(f"fingerprint: metadata path not fingerprinted: {path}")
    for path in extra:
        errors.append(f"fingerprint: undeclared path fingerprinted: {path}")
    for digest, paths in hashes.items():
        if len(paths) > 1:
            errors.append(
                f"fingerprint: exact duplicate content {digest}: {', '.join(paths)}"
            )
    return errors


def validate_phase1_front_matter(
    metadata: dict[str, Any], repo_root: Path = REPO_ROOT
) -> list[str]:
    """Require complete inline metadata on new protected Phase 1 Markdown."""
    errors: list[str] = []
    required = set(metadata.get("required_fields", []))
    for document in metadata.get("documents", []):
        if not isinstance(document, dict):
            continue
        path = str(document.get("path", ""))
        if not path.startswith("docs/governance/") or not path.endswith(".md"):
            continue
        target = repo_root / path
        if not target.is_file():
            continue
        match = _FRONT_MATTER.match(target.read_text(encoding="utf-8"))
        if match is None:
            errors.append(f"front_matter: missing in {path}")
            continue
        front = yaml.safe_load(match.group(1))
        if not isinstance(front, dict):
            errors.append(f"front_matter: invalid mapping in {path}")
            continue
        missing = sorted(required - set(front))
        if missing:
            errors.append(
                f"front_matter: {path} missing {', '.join(missing)}"
            )
    return errors


def validate_kernel(repo_root: Path = REPO_ROOT) -> list[str]:
    """Reassert FIT-006 without importing EOS."""
    kernel = repo_root / "00-governance" / "KERNEL.md"
    words = len(re.findall(r"\S+", kernel.read_text(encoding="utf-8")))
    return [] if words <= 400 else [f"FIT-006: KERNEL has {words} words"]


def validate_repository(repo_root: Path = REPO_ROOT) -> list[str]:
    """Run every Architecture Baseline governance check."""
    metadata = load_yaml(repo_root / METADATA_PATH.relative_to(REPO_ROOT))
    source_map = load_yaml(repo_root / SOURCE_MAP_PATH.relative_to(REPO_ROOT))
    fingerprint = load_yaml(repo_root / FINGERPRINT_PATH.relative_to(REPO_ROOT))
    return [
        *validate_metadata(metadata, repo_root),
        *validate_source_map(source_map, repo_root),
        *validate_fingerprint(fingerprint, metadata_paths(metadata), repo_root),
        *validate_phase1_front_matter(metadata, repo_root),
        *validate_kernel(repo_root),
    ]


def main() -> int:
    """CLI entry point."""
    errors = validate_repository()
    if errors:
        print(f"baseline_gate: FAIL ({len(errors)} violation(s))")
        for error in errors:
            print(f"  {error}")
        return 1
    metadata = load_yaml(METADATA_PATH)
    source_map = load_yaml(SOURCE_MAP_PATH)
    fingerprint = load_yaml(FINGERPRINT_PATH)
    print("baseline_gate: PASS")
    print(f"  protected artifacts: {len(metadata_paths(metadata))}")
    print(f"  fingerprinted artifacts: {len(fingerprint['artifacts'])}")
    print(f"  canonical concerns: {len(source_map['concerns'])}")
    print("  metadata: complete and unique")
    print("  dependencies: acyclic")
    print("  duplicate protected content: none")
    print("  KERNEL: <=400 words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
