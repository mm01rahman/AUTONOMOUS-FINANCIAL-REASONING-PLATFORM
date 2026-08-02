"""Typed models for Data Foundation V2 Tier 1 infrastructure."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RetryPolicy(BaseModel):
    """Provider retry policy for deterministic historical ingestion."""

    model_config = ConfigDict(frozen=True)

    attempts: int = 3
    backoff_seconds: float = 0.5
    retryable_statuses: tuple[int, ...] = (408, 429, 500, 502, 503, 504)


class ProviderRequest(BaseModel):
    """A historical dataset request specification."""

    model_config = ConfigDict(frozen=True)

    dataset_id: str
    provider: str
    url: str
    method: Literal["GET"] = "GET"
    timeout_seconds: int = 30
    headers: dict[str, str] = Field(default_factory=dict)
    params: dict[str, str] = Field(default_factory=dict)
    credential_env_vars: tuple[str, ...] = ()
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)


class DatasetFieldSchema(BaseModel):
    """One canonical field in a Tier 1 dataset schema."""

    model_config = ConfigDict(frozen=True)

    name: str
    dtype: Literal["datetime", "float", "int", "str"]
    nullable: bool = False
    description: str


class DatasetSpec(BaseModel):
    """Canonical configuration for one Data Foundation V2 dataset."""

    model_config = ConfigDict(frozen=True)

    dataset_id: str
    slug: str
    name: str
    work_package: str
    domain: str
    provider: str
    source: str
    licensing: str
    history: str
    cadence: Literal["daily", "weekly", "monthly", "derived"]
    timezone: str = "UTC"
    source_kind: Literal["public_api", "public_file", "derived"]
    schema_fields: tuple[DatasetFieldSchema, ...]
    market_state_variables: tuple[str, ...]
    supported_families: tuple[str, ...]
    supported_mechanisms: tuple[str, ...]
    supported_axioms: tuple[str, ...]
    quality_weight: float = 0.8
    source_priority: str = "P1"
    requires_api_key: bool = False
    source_url: str = ""
    request_params: dict[str, str] = Field(default_factory=dict)
    request_headers: dict[str, str] = Field(default_factory=dict)
    credential_env_vars: tuple[str, ...] = ()
    source_fixture_key: str


class DatasetQualityMetrics(BaseModel):
    """Quality and confidence metrics required by Data Foundation V2."""

    model_config = ConfigDict(frozen=True)

    record_count: int
    coverage: float
    completeness: float
    freshness: float
    missing_rate: float
    duplicate_rate: float
    timestamp_consistency: float
    schema_conformity: float
    validation_score: float
    confidence_score: float
    start_timestamp: str
    end_timestamp: str


class DatasetManifest(BaseModel):
    """Deterministic dataset version manifest."""

    model_config = ConfigDict(frozen=True)

    dataset_id: str
    dataset_name: str
    version_id: str
    generated_at: str
    provider: str
    source: str
    source_url: str
    cadence: str
    timezone: str
    work_package: str
    storage_path: str
    row_count: int
    checksum_sha256: str
    raw_checksum_sha256: str
    covered_variables: tuple[str, ...]
    supported_mechanisms: tuple[str, ...]
    supported_families: tuple[str, ...]
    provenance: dict[str, str]
    quality: DatasetQualityMetrics


class DatasetRegistryEntry(BaseModel):
    """Registry summary for the latest version of a dataset."""

    model_config = ConfigDict(frozen=True)

    dataset_id: str
    name: str
    version_id: str
    provider: str
    domain: str
    cadence: str
    work_package: str
    storage_path: str
    manifest_path: str
    quality_score: float
    confidence_score: float
    covered_variables: tuple[str, ...]
    supported_mechanisms: tuple[str, ...]


class CoverageRegistryEntry(BaseModel):
    """Coverage and missing-data registry summary."""

    model_config = ConfigDict(frozen=True)

    dataset_id: str
    record_count: int
    coverage: float
    completeness: float
    missing_rate: float
    duplicate_rate: float
    start_timestamp: str
    end_timestamp: str


class MarketStateRegistryEntry(BaseModel):
    """Market-state variable coverage by dataset."""

    model_config = ConfigDict(frozen=True)

    domain: str
    variable: str
    dataset_ids: tuple[str, ...]
    status: Literal["OBSERVED", "PARTIAL", "UNMAPPED"]


class ProviderLibraryEntry(BaseModel):
    """Documented provider adapter capability."""

    model_config = ConfigDict(frozen=True)

    provider: str
    supported_source_kinds: tuple[str, ...]
    deterministic: bool
    historical_only: bool
    requires_api_key: bool
    retry_attempts: int
    checksum_enabled: bool
