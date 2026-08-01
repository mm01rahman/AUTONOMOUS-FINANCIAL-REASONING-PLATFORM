"""AFRP evidence archive — packages evidence records for a release.

Collects:
  - All evidence YAML files under 05-work-packages/*/evidence/
  - All completion reports under 10-release/
  - Repository health snapshot

Usage:
  uv run python -m tools.evidence_archive --tag v2.0.0
  uv run python -m tools.evidence_archive --tag v2.0.0 --output my-archive.tar.gz
"""

from __future__ import annotations

import datetime
import io
import sys
import tarfile
from pathlib import Path
from typing import Any

import click
import yaml

_ROOT = Path(__file__).parent.parent


def _collect_evidence_files(root: Path) -> list[Path]:
    """Find all evidence YAML files in work packages."""
    evidence_files: list[Path] = []
    wp_dir = root / "05-work-packages"
    if wp_dir.exists():
        for wp in sorted(wp_dir.iterdir()):
            evidence_dir = wp / "evidence"
            if evidence_dir.is_dir():
                for f in sorted(evidence_dir.glob("*.yaml")):
                    evidence_files.append(f)
    return evidence_files


def _collect_completion_reports(root: Path) -> list[Path]:
    """Find all completion and evidence reports in 10-release/."""
    release_dir = root / "10-release"
    if not release_dir.exists():
        return []
    reports = sorted(release_dir.glob("*.md")) + sorted(release_dir.glob("*.yaml"))
    return reports


def _generate_manifest(
    tag: str,
    evidence_files: list[Path],
    completion_reports: list[Path],
    root: Path,
) -> str:
    """Generate archive manifest as YAML."""
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "archive_type": "AFRP-EVIDENCE-ARCHIVE",
        "tag": tag,
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "repository": "mm01rahman/AUTONOMOUS-FINANCIAL-REASONING-PLATFORM",
        "evidence_records": [str(f.relative_to(root)) for f in evidence_files],
        "completion_reports": [str(f.relative_to(root)) for f in completion_reports],
        "totals": {
            "evidence_records": len(evidence_files),
            "completion_reports": len(completion_reports),
        },
    }
    return yaml.dump(manifest, default_flow_style=False, allow_unicode=True)


def _add_string_to_tar(tar: tarfile.TarFile, name: str, content: str, tag: str) -> None:
    """Add an in-memory string as a file to the tarball."""
    encoded = content.encode("utf-8")
    info = tarfile.TarInfo(name=f"evidence-archive-{tag}/{name}")
    info.size = len(encoded)
    info.mtime = int(datetime.datetime.now(datetime.UTC).timestamp())
    tar.addfile(info, io.BytesIO(encoded))


def _add_file_to_tar(tar: tarfile.TarFile, path: Path, root: Path, tag: str) -> None:
    """Add a file from disk to the tarball."""
    arcname = f"evidence-archive-{tag}/{path.relative_to(root)}"
    tar.add(path, arcname=arcname)


@click.command()
@click.option("--tag", required=True, help="Release tag, e.g. v2.0.0")
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output filename. Defaults to evidence-archive-<tag>.tar.gz",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Repository root.",
)
def main(tag: str, output: Path | None, repo_root: Path) -> None:
    """Package AFRP evidence records and completion reports for a release."""
    root = repo_root.resolve()

    if output is None:
        output = root / f"evidence-archive-{tag}.tar.gz"

    click.echo(f"Packaging evidence archive for tag: {tag}")

    evidence_files = _collect_evidence_files(root)
    completion_reports = _collect_completion_reports(root)

    click.echo(f"  Evidence records:     {len(evidence_files)}")
    click.echo(f"  Completion reports:   {len(completion_reports)}")

    # Generate manifest
    manifest_content = _generate_manifest(tag, evidence_files, completion_reports, root)

    # Also include health snapshot if present
    health_file = root / "03-engineering" / "REPOSITORY_HEALTH.yaml"
    coverage_file = root / "coverage.json"

    with tarfile.open(output, "w:gz") as tar:
        # Manifest first
        _add_string_to_tar(tar, "ARCHIVE_MANIFEST.yaml", manifest_content, tag)

        # Evidence records
        for f in evidence_files:
            _add_file_to_tar(tar, f, root, tag)

        # Completion reports
        for f in completion_reports:
            _add_file_to_tar(tar, f, root, tag)

        # Health snapshot
        if health_file.exists():
            _add_file_to_tar(tar, health_file, root, tag)

        # Coverage report
        if coverage_file.exists():
            _add_file_to_tar(tar, coverage_file, root, tag)

    click.echo(f"\nEvidence archive: {output}")
    click.echo(f"Archive size:     {output.stat().st_size:,} bytes")
    click.echo("evidence_archive: PASS")


if __name__ == "__main__":
    sys.exit(main())
