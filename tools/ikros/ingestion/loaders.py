"""IKROS ingestion source loaders for Markdown, YAML, and JSON documents."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from tools.ikros.ingestion.models import SourceDocument, SourceFormat, SourceKind
from tools.ikros.persistence import from_yaml

_FRONT_MATTER_PATTERN = re.compile(
    r"\A---\r?\n(.*?)\r?\n---\r?\n?",
    re.DOTALL,
)
_FENCED_BLOCK_PATTERN = re.compile(
    r"```(?P<lang>yaml|yml|json)\r?\n(?P<body>.*?)\r?\n```",
    re.DOTALL | re.IGNORECASE,
)
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_METADATA_LINE_PATTERN = re.compile(r"^\s*>?\s*\*\*(.+?)\*\*:\s*(.+?)\s*$")


class SourceLoader:
    """Deterministic structured-document loader."""

    def load_path(self, path: Path) -> SourceDocument:
        raw = path.read_text(encoding="utf-8")
        content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        if path.suffix.lower() in {".yaml", ".yml"}:
            payload = from_yaml(raw)
            metadata = self._mapping_metadata(payload)
            return SourceDocument(
                source_ref=str(path),
                source_kind=str(self._infer_source_kind(path, metadata, payload)),
                source_format=str(SourceFormat.YAML),
                title=self._mapping_title(path, metadata, payload),
                content_hash=content_hash,
                version=str(metadata.get("version", metadata.get("schema_version", "1.0.0"))),
                metadata=metadata,
                sections={},
                object_specs=self._mapping_object_specs(payload),
                payload=payload,
            )
        if path.suffix.lower() == ".json":
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError("JSON source must contain a top-level object")
            metadata = self._mapping_metadata(payload)
            return SourceDocument(
                source_ref=str(path),
                source_kind=str(self._infer_source_kind(path, metadata, payload)),
                source_format=str(SourceFormat.JSON),
                title=self._mapping_title(path, metadata, payload),
                content_hash=content_hash,
                version=str(metadata.get("version", payload.get("version", "1.0.0"))),
                metadata=metadata,
                sections={},
                object_specs=self._mapping_object_specs(payload),
                payload=payload,
            )
        if path.suffix.lower() == ".md":
            return self._load_markdown(path, raw, content_hash)
        raise ValueError(f"Unsupported ingestion source format '{path.suffix}'")

    def _load_markdown(
        self,
        path: Path,
        raw: str,
        content_hash: str,
    ) -> SourceDocument:
        front_matter, body = self._split_front_matter(raw)
        front_mapping = from_yaml(front_matter) if front_matter else {}
        metadata = dict(front_mapping.get("metadata", {}))
        metadata.update(self._markdown_metadata_lines(body))
        if "title" in front_mapping and "title" not in metadata:
            metadata["title"] = front_mapping["title"]
        sections = self._markdown_sections(body)
        object_specs = self._mapping_object_specs(front_mapping)
        if not object_specs:
            object_specs = self._markdown_object_specs(body)
        title = str(
            metadata.get("title")
            or self._first_heading(body)
            or path.stem
        )
        return SourceDocument(
            source_ref=str(path),
            source_kind=str(self._infer_source_kind(path, metadata, front_mapping)),
            source_format=str(SourceFormat.MARKDOWN),
            title=title,
            content_hash=content_hash,
            version=str(metadata.get("version", front_mapping.get("version", "1.0.0"))),
            metadata=metadata,
            sections=sections,
            object_specs=object_specs,
            payload=front_mapping,
        )

    def _split_front_matter(self, raw: str) -> tuple[str | None, str]:
        match = _FRONT_MATTER_PATTERN.match(raw)
        if match is None:
            return None, raw
        return match.group(1), raw[match.end() :]

    def _mapping_metadata(self, payload: dict[str, Any]) -> dict[str, Any]:
        metadata = payload.get("metadata", {})
        if isinstance(metadata, dict):
            result = dict(metadata)
        else:
            result = {}
        for key in (
            "schema_version",
            "title",
            "document_id",
            "specification_id",
            "specification_authority",
            "work_package_id",
            "version",
            "source_kind",
        ):
            if key in payload and key not in result:
                result[key] = payload[key]
        return result

    def _mapping_title(
        self,
        path: Path,
        metadata: dict[str, Any],
        payload: dict[str, Any],
    ) -> str:
        for key in ("title", "document_id", "specification_id", "evidence_id"):
            value = metadata.get(key, payload.get(key))
            if value:
                return str(value)
        return path.stem

    def _mapping_object_specs(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("ikros_objects", "knowledge_objects", "objects"):
            value = payload.get(key)
            if isinstance(value, list):
                return [dict(item) for item in value if isinstance(item, dict)]
        return []

    def _markdown_object_specs(self, body: str) -> list[dict[str, Any]]:
        for match in _FENCED_BLOCK_PATTERN.finditer(body):
            lang = match.group("lang").lower()
            block = match.group("body")
            try:
                parsed: Any
                if lang == "json":
                    parsed = json.loads(block)
                else:
                    parsed = from_yaml(block)
            except (ValueError, json.JSONDecodeError):
                continue
            if isinstance(parsed, dict):
                specs = self._mapping_object_specs(parsed)
                if specs:
                    return specs
        return []

    def _markdown_metadata_lines(self, body: str) -> dict[str, str]:
        metadata: dict[str, str] = {}
        for line in body.splitlines()[:40]:
            match = _METADATA_LINE_PATTERN.match(line)
            if match is None:
                continue
            key = match.group(1).strip().lower().replace(" ", "_")
            metadata[key] = match.group(2).strip()
        return metadata

    def _markdown_sections(self, body: str) -> dict[str, str]:
        matches = list(_HEADING_PATTERN.finditer(body))
        if not matches:
            return {}
        sections: dict[str, str] = {}
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
            sections[match.group(2).strip()] = body[start:end].strip()
        return sections

    def _first_heading(self, body: str) -> str | None:
        match = _HEADING_PATTERN.search(body)
        if match is None:
            return None
        return match.group(2).strip()

    def _infer_source_kind(
        self,
        path: Path,
        metadata: dict[str, Any],
        payload: dict[str, Any],
    ) -> str:
        explicit = metadata.get("source_kind") or payload.get("source_kind")
        if explicit:
            return str(explicit)
        schema_version = str(payload.get("schema_version", ""))
        name = path.name.upper()
        if schema_version == "ERS-1.0" or name.startswith("EXEC-"):
            return SourceKind.EVIDENCE_RECORD
        if name.startswith("ADR-") or "adr" in name.lower():
            return SourceKind.ADR
        if name.startswith("SPEC-") or "specification_id" in metadata:
            return SourceKind.SPECIFICATION
        lowered = path.stem.lower()
        if "experiment" in lowered:
            return SourceKind.EXPERIMENT_REPORT
        if "validation" in lowered:
            return SourceKind.VALIDATION_REPORT
        if "backtest" in lowered:
            return SourceKind.BACKTEST_REPORT
        if "stat" in lowered:
            return SourceKind.STATISTICAL_REPORT
        if path.suffix.lower() == ".md":
            return SourceKind.MARKDOWN
        if path.suffix.lower() in {".yaml", ".yml"}:
            return SourceKind.YAML
        return SourceKind.JSON
