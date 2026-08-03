"""Data Foundation V2 Tier 1 deterministic ingestion engine."""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import io
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import sleep
from typing import Any, Protocol, cast

import pandas as pd
from pydantic import BaseModel

from tools.alpha_research.institutional_observability import (
    DATASET_CATALOGUE,
    MARKET_STATE_DOMAINS,
)
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown
from tools.data_foundation.models import (
    CoverageRegistryEntry,
    DatasetFieldSchema,
    DatasetManifest,
    DatasetQualityMetrics,
    DatasetRegistryEntry,
    DatasetSpec,
    MarketStateRegistryEntry,
    ProviderLibraryEntry,
    ProviderRequest,
)

DATA_FOUNDATION_DIR = Path("data") / "data-foundation-v2"
DATA_FOUNDATION_REPORT_DIR = (
    Path("11-research") / "data-foundation-v2" / "phase-1-institutional-market-data-infrastructure"
)
DATA_FOUNDATION_SCHEMA_DIR = Path("schemas") / "data-foundation-v2"

_NOW = "2026-08-02T00:00:00Z"

_FRED_VIX_FIXTURE = """DATE,VALUE
2026-07-27,16.20
2026-07-28,15.80
2026-07-29,17.10
2026-07-30,18.40
2026-07-31,17.90
2026-08-01,16.75
"""

_FRED_TED_FIXTURE = """DATE,VALUE
2026-07-27,0.36
2026-07-28,0.35
2026-07-29,0.37
2026-07-30,0.41
2026-07-31,0.39
2026-08-01,0.38
"""

_FRED_BREAKEVEN_FIXTURE = """DATE,BREAKEVEN_5Y,BREAKEVEN_10Y
2026-07-27,2.11,2.23
2026-07-28,2.09,2.21
2026-07-29,2.15,2.27
2026-07-30,2.18,2.29
2026-07-31,2.16,2.28
2026-08-01,2.14,2.26
"""

_FRED_RATES_FIXTURE = """DATE,UST_2Y,TIPS_10Y_REAL_YIELD,FED_TARGET_UPPER
2026-07-27,4.42,1.86,4.50
2026-07-28,4.39,1.82,4.50
2026-07-29,4.48,1.90,4.50
2026-07-30,4.51,1.94,4.50
2026-07-31,4.47,1.91,4.50
2026-08-01,4.44,1.88,4.50
"""

_ETF_FIXTURE = """date,gld_shares_outstanding,gld_tonnes,iau_shares_outstanding,iau_tonnes
2026-07-27,285000000,892.1,510000000,412.4
2026-07-28,285500000,893.0,511000000,413.2
2026-07-29,286200000,894.8,512200000,414.6
2026-07-30,286800000,896.0,513100000,415.7
2026-07-31,287000000,896.4,513500000,416.2
2026-08-01,287600000,897.5,514300000,417.1
"""

_CFTC_FIXTURE = """date,non_commercial_long,non_commercial_short,non_commercial_net,dealer_long,dealer_short,dealer_net,commercial_long,commercial_short
2026-07-07,245120,118440,126680,104520,132880,-28360,215700,292140
2026-07-14,247300,119900,127400,105100,133700,-28600,216100,293500
2026-07-21,249880,121020,128860,106240,134900,-28660,217900,295500
2026-07-28,252140,122400,129740,107300,135950,-28650,219100,296750
"""

_CBOE_GVZ_FIXTURE = """DATE,VALUE
2026-07-27,19.8
2026-07-28,19.4
2026-07-29,20.1
2026-07-30,20.9
2026-07-31,20.4
2026-08-01,19.9
"""

_WGC_FIXTURE = """date,official_sector_net_tonnes,reported_central_bank_buyers
2026-04-30,28.1,12
2026-05-31,25.6,11
2026-06-30,31.3,13
2026-07-31,29.8,12
"""

_ACADEMIC_GPR_FIXTURE = """date,gpr_index
2026-04-30,128.4
2026-05-31,132.1
2026-06-30,136.9
2026-07-31,134.2
"""

_FIXTURES: dict[str, bytes] = {
    "fred_vix": _FRED_VIX_FIXTURE.encode("utf-8"),
    "fred_ted": _FRED_TED_FIXTURE.encode("utf-8"),
    "fred_breakeven": _FRED_BREAKEVEN_FIXTURE.encode("utf-8"),
    "fred_rates": _FRED_RATES_FIXTURE.encode("utf-8"),
    "etf_holdings": _ETF_FIXTURE.encode("utf-8"),
    "cftc_positions": _CFTC_FIXTURE.encode("utf-8"),
    "cboe_gvz": _CBOE_GVZ_FIXTURE.encode("utf-8"),
    "wgc_central_banks": _WGC_FIXTURE.encode("utf-8"),
    "academic_gpr": _ACADEMIC_GPR_FIXTURE.encode("utf-8"),
}


def _tier1_specs() -> list[DatasetSpec]:
    return [
        DatasetSpec(
            dataset_id="DS-001",
            slug="vix-index",
            name="VIX Index",
            work_package="DF2-WP-001",
            domain="macro_stress",
            provider="FREDProvider",
            source="FRED",
            licensing="Free",
            history="1990-present",
            cadence="daily",
            source_kind="public_api",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC session timestamp"),
                DatasetFieldSchema(name="vix", dtype="float", description="VIX close"),
            ),
            market_state_variables=("vix", "macro_stress_proxy"),
            supported_families=("FAM-002", "FAM-003", "FAM-007"),
            supported_mechanisms=("liquidity_withdrawal", "safe_haven_migration", "regime_transition_chain"),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0006", "IKROS-PF1-PRINCIPLE-0010"),
            source_url="https://fred.stlouisfed.org/series/VIXCLS/downloaddata/VIXCLS.csv",
            source_fixture_key="fred_vix",
        ),
        DatasetSpec(
            dataset_id="DS-003",
            slug="ted-spread",
            name="TED Spread",
            work_package="DF2-WP-001",
            domain="macro_stress",
            provider="FREDProvider",
            source="FRED",
            licensing="Free",
            history="1986-present",
            cadence="daily",
            source_kind="public_api",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC session timestamp"),
                DatasetFieldSchema(name="ted_spread", dtype="float", description="TED spread"),
            ),
            market_state_variables=("ted_spread",),
            supported_families=("FAM-002", "FAM-003"),
            supported_mechanisms=("liquidity_withdrawal", "safe_haven_migration"),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0006", "IKROS-PF1-PRINCIPLE-0010"),
            source_url="https://fred.stlouisfed.org/series/TEDRATE/downloaddata/TEDRATE.csv",
            source_fixture_key="fred_ted",
        ),
        DatasetSpec(
            dataset_id="DS-012",
            slug="breakeven-inflation",
            name="Breakeven Inflation Rates (5Y, 10Y)",
            work_package="DF2-WP-001",
            domain="rates",
            provider="FREDProvider",
            source="FRED",
            licensing="Free",
            history="2003-present",
            cadence="daily",
            source_kind="public_api",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC session timestamp"),
                DatasetFieldSchema(name="breakeven_5y", dtype="float", description="5Y breakeven"),
                DatasetFieldSchema(name="breakeven_10y", dtype="float", description="10Y breakeven"),
            ),
            market_state_variables=("breakeven_inflation",),
            supported_families=("FAM-001", "FAM-005"),
            supported_mechanisms=("macro_repricing", "expectation_reset", "policy_repricing"),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0010",),
            source_url="https://fred.stlouisfed.org/series/T5YIE/downloaddata/T5YIE.csv",
            source_fixture_key="fred_breakeven",
        ),
        DatasetSpec(
            dataset_id="DS-018",
            slug="ust-2y-yield",
            name="US Treasury 2Y Yield",
            work_package="DF2-WP-003",
            domain="policy_expectations",
            provider="FREDProvider",
            source="FRED",
            licensing="Free",
            history="1976-present",
            cadence="daily",
            source_kind="public_api",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC session timestamp"),
                DatasetFieldSchema(name="ust_2y_yield", dtype="float", description="2Y Treasury yield"),
            ),
            market_state_variables=("us_treasury_2y_yield", "fomc_policy_anchor_public"),
            supported_families=("FAM-001", "FAM-005"),
            supported_mechanisms=("macro_repricing", "expectation_reset", "policy_repricing"),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0010",),
            source_url="https://fred.stlouisfed.org/series/DGS2/downloaddata/DGS2.csv",
            source_fixture_key="fred_rates",
        ),
        DatasetSpec(
            dataset_id="DS-019",
            slug="tips-10y-real-yield",
            name="TIPS 10Y Real Yield",
            work_package="DF2-WP-003",
            domain="policy_expectations",
            provider="FREDProvider",
            source="FRED",
            licensing="Free",
            history="2003-present",
            cadence="daily",
            source_kind="public_api",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC session timestamp"),
                DatasetFieldSchema(name="tips_10y_real_yield", dtype="float", description="10Y TIPS real yield"),
            ),
            market_state_variables=("real_yield_tip_direct",),
            supported_families=("FAM-001", "FAM-004"),
            supported_mechanisms=("cross_asset_transition", "macro_repricing", "policy_repricing"),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0010",),
            source_url="https://fred.stlouisfed.org/series/DFII10/downloaddata/DFII10.csv",
            source_fixture_key="fred_rates",
        ),
        DatasetSpec(
            dataset_id="DS-007",
            slug="gld-shares-outstanding",
            name="GLD ETF Shares Outstanding",
            work_package="DF2-WP-002",
            domain="etf_positioning",
            provider="ETFHoldingsProvider",
            source="SPDR",
            licensing="Free",
            history="2004-present",
            cadence="daily",
            source_kind="public_file",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC session timestamp"),
                DatasetFieldSchema(name="gld_shares_outstanding", dtype="float", description="GLD shares outstanding"),
                DatasetFieldSchema(name="gld_tonnes", dtype="float", description="GLD tonnes"),
            ),
            market_state_variables=("gld_shares_outstanding", "gld_etf_flows"),
            supported_families=("FAM-003", "FAM-004"),
            supported_mechanisms=("safe_haven_migration", "etf_flow_propagation", "adaptive_ecology_shift"),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0003", "IKROS-PF1-PRINCIPLE-0010"),
            source_url="https://www.spdrgoldshares.com/data/gld-holdings.csv",
            source_fixture_key="etf_holdings",
        ),
        DatasetSpec(
            dataset_id="DS-008",
            slug="iau-shares-outstanding",
            name="IAU ETF Shares Outstanding",
            work_package="DF2-WP-002",
            domain="etf_positioning",
            provider="ETFHoldingsProvider",
            source="iShares",
            licensing="Free",
            history="2005-present",
            cadence="daily",
            source_kind="public_file",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC session timestamp"),
                DatasetFieldSchema(name="iau_shares_outstanding", dtype="float", description="IAU shares outstanding"),
                DatasetFieldSchema(name="iau_tonnes", dtype="float", description="IAU tonnes"),
            ),
            market_state_variables=("iau_shares_outstanding", "iau_etf_flows"),
            supported_families=("FAM-003", "FAM-004"),
            supported_mechanisms=("safe_haven_migration", "etf_flow_propagation"),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0003", "IKROS-PF1-PRINCIPLE-0010"),
            source_url="https://www.ishares.com/data/iau-holdings.csv",
            source_fixture_key="etf_holdings",
        ),
        DatasetSpec(
            dataset_id="DS-009",
            slug="cot-non-commercial-positioning",
            name="COMEX Non-Commercial Positioning",
            work_package="DF2-WP-002",
            domain="institutional_positioning",
            provider="CFTCProvider",
            source="CFTC COT",
            licensing="Free",
            history="1986-present",
            cadence="weekly",
            source_kind="public_api",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC report timestamp"),
                DatasetFieldSchema(name="non_commercial_long", dtype="float", description="Long contracts"),
                DatasetFieldSchema(name="non_commercial_short", dtype="float", description="Short contracts"),
                DatasetFieldSchema(name="non_commercial_net", dtype="float", description="Net positioning"),
            ),
            market_state_variables=("comex_positioning_direct", "cot_participant_mix"),
            supported_families=("FAM-002", "FAM-004", "FAM-007"),
            supported_mechanisms=("cross_asset_transition", "dealer_inventory", "adaptive_ecology_shift"),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0003", "IKROS-PF1-PRINCIPLE-0010"),
            source_url="https://www.cftc.gov/dea/newcot/FinFutWk.txt",
            source_fixture_key="cftc_positions",
        ),
        DatasetSpec(
            dataset_id="DS-010",
            slug="cot-dealer-net-position",
            name="COMEX Dealer Net Position",
            work_package="DF2-WP-002",
            domain="institutional_positioning",
            provider="CFTCProvider",
            source="CFTC COT Disaggregated",
            licensing="Free",
            history="2006-present",
            cadence="weekly",
            source_kind="public_api",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC report timestamp"),
                DatasetFieldSchema(name="dealer_long", dtype="float", description="Dealer long contracts"),
                DatasetFieldSchema(name="dealer_short", dtype="float", description="Dealer short contracts"),
                DatasetFieldSchema(name="dealer_net", dtype="float", description="Dealer net positioning"),
            ),
            market_state_variables=("cot_dealers", "dealer_net_position_change"),
            supported_families=("FAM-002",),
            supported_mechanisms=("dealer_inventory", "adaptive_ecology_shift"),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0003", "IKROS-PF1-PRINCIPLE-0010"),
            source_url="https://www.cftc.gov/dea/newcot/Disagg.txt",
            source_fixture_key="cftc_positions",
        ),
        DatasetSpec(
            dataset_id="DS-011",
            slug="gvz-index",
            name="Gold Volatility Index (GVZ)",
            work_package="DF2-WP-002",
            domain="macro_stress",
            provider="CBOEProvider",
            source="CBOE",
            licensing="Free historical",
            history="2008-present",
            cadence="daily",
            source_kind="public_file",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC session timestamp"),
                DatasetFieldSchema(name="gvz", dtype="float", description="GVZ close"),
            ),
            market_state_variables=("vol_surface", "dealer_gamma"),
            supported_families=("FAM-002", "FAM-006"),
            supported_mechanisms=("dealer_inventory", "decision_cascade", "liquidity_withdrawal"),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0006", "IKROS-PF1-PRINCIPLE-0010"),
            source_url="https://cdn.cboe.com/api/global/us_indices/daily_prices/GVZ_History.csv",
            source_fixture_key="cboe_gvz",
        ),
        DatasetSpec(
            dataset_id="DS-014",
            slug="central-bank-gold-purchases",
            name="Central Bank Gold Purchases",
            work_package="DF2-WP-004",
            domain="structural_demand",
            provider="WGCProvider",
            source="World Gold Council",
            licensing="Free aggregated",
            history="2000-present",
            cadence="monthly",
            source_kind="public_file",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC month-end timestamp"),
                DatasetFieldSchema(name="official_sector_net_tonnes", dtype="float", description="Net central bank purchases"),
                DatasetFieldSchema(name="reported_central_bank_buyers", dtype="int", description="Buyer count"),
            ),
            market_state_variables=("central_bank_gold_purchases", "institutional_flow_direction"),
            supported_families=("FAM-003", "FAM-007"),
            supported_mechanisms=("safe_haven_migration", "adaptive_ecology_shift"),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0003", "IKROS-PF1-PRINCIPLE-0010"),
            source_url="https://www.gold.org/goldhub/data/central-bank-net-purchases.csv",
            source_fixture_key="wgc_central_banks",
        ),
        DatasetSpec(
            dataset_id="DS-017",
            slug="geopolitical-risk-index",
            name="Geopolitical Risk Index",
            work_package="DF2-WP-004",
            domain="structural_demand",
            provider="AcademicProvider",
            source="Caldara-Iacoviello",
            licensing="Free academic",
            history="1900-present",
            cadence="monthly",
            source_kind="public_file",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC month-end timestamp"),
                DatasetFieldSchema(name="gpr_index", dtype="float", description="Geopolitical risk index"),
            ),
            market_state_variables=("geopolitical_risk_index",),
            supported_families=("FAM-003",),
            supported_mechanisms=("safe_haven_migration",),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0010",),
            source_url="https://www.matteoiacoviello.com/gpr_files/GPR.csv",
            source_fixture_key="academic_gpr",
        ),
        DatasetSpec(
            dataset_id="DS-PUB-021",
            slug="policy-expectation-public-curve",
            name="Public Policy Expectation Curve",
            work_package="DF2-WP-003",
            domain="policy_expectations",
            provider="DerivedPolicyProvider",
            source="Derived from FRED Tier 1 series",
            licensing="Free derived",
            history="Derived from source series",
            cadence="derived",
            source_kind="derived",
            schema_fields=(
                DatasetFieldSchema(name="timestamp", dtype="datetime", description="UTC session timestamp"),
                DatasetFieldSchema(name="policy_expectation_public_curve", dtype="float", description="Public policy expectation proxy"),
            ),
            market_state_variables=("policy_expectation_proxy_public", "fomc_meeting_prob_public_proxy"),
            supported_families=("FAM-001", "FAM-005"),
            supported_mechanisms=("macro_repricing", "expectation_reset", "policy_repricing"),
            supported_axioms=("IKROS-PF1-PRINCIPLE-0010",),
            source_fixture_key="derived_policy_curve",
        ),
    ]


def _dataset_catalogue_lookup() -> dict[str, dict[str, Any]]:
    return {str(item["dataset_id"]): item for item in DATASET_CATALOGUE}


class SourceAdapter(Protocol):
    """Interface for deterministic historical source retrieval."""

    def fetch(self, request: ProviderRequest) -> bytes:
        ...


class FixtureSourceAdapter:
    """Fetches immutable fixture payloads for offline reproducibility."""

    def __init__(self, fixtures: dict[str, bytes]) -> None:
        self._fixtures = dict(fixtures)

    def fetch(self, request: ProviderRequest) -> bytes:
        if request.dataset_id not in self._fixtures:
            raise KeyError(f"missing fixture for {request.dataset_id}")
        return self._fixtures[request.dataset_id]


class UrlSourceAdapter:
    """Optional remote adapter for public historical sources."""

    def fetch(self, request: ProviderRequest) -> bytes:
        query = urllib.parse.urlencode(request.params)
        url = request.url if not query else f"{request.url}?{query}"
        attempt = 0
        while True:
            attempt += 1
            req = urllib.request.Request(url, headers=request.headers, method=request.method)
            try:
                with urllib.request.urlopen(req, timeout=request.timeout_seconds) as response:
                    return cast(bytes, response.read())
            except urllib.error.HTTPError as exc:
                if (
                    attempt >= request.retry_policy.attempts
                    or exc.code not in request.retry_policy.retryable_statuses
                ):
                    raise
                sleep(request.retry_policy.backoff_seconds * attempt)
            except urllib.error.URLError:
                if attempt >= request.retry_policy.attempts:
                    raise
                sleep(request.retry_policy.backoff_seconds * attempt)


class BaseProvider:
    """Base provider adapter."""

    name = "BaseProvider"

    def build_request(self, spec: DatasetSpec) -> ProviderRequest:
        return ProviderRequest(
            dataset_id=spec.source_fixture_key,
            provider=self.name,
            url=spec.source_url,
            headers=spec.request_headers,
            params=spec.request_params,
            credential_env_vars=spec.credential_env_vars,
        )

    def load_frame(self, spec: DatasetSpec, source: SourceAdapter) -> pd.DataFrame:
        raw = source.fetch(self.build_request(spec))
        return self.parse_bytes(spec, raw)

    def parse_bytes(self, spec: DatasetSpec, raw: bytes) -> pd.DataFrame:
        raise NotImplementedError


class FREDProvider(BaseProvider):
    name = "FREDProvider"

    def parse_bytes(self, spec: DatasetSpec, raw: bytes) -> pd.DataFrame:
        frame = pd.read_csv(io.StringIO(raw.decode("utf-8")))
        if spec.dataset_id == "DS-012":
            renamed = frame.rename(
                columns={
                    "DATE": "timestamp",
                    "BREAKEVEN_5Y": "breakeven_5y",
                    "BREAKEVEN_10Y": "breakeven_10y",
                }
            )
            return renamed[["timestamp", "breakeven_5y", "breakeven_10y"]]
        if spec.dataset_id == "DS-018":
            renamed = frame.rename(columns={"DATE": "timestamp", "UST_2Y": "ust_2y_yield"})
            return renamed[["timestamp", "ust_2y_yield"]]
        if spec.dataset_id == "DS-019":
            renamed = frame.rename(columns={"DATE": "timestamp", "TIPS_10Y_REAL_YIELD": "tips_10y_real_yield"})
            return renamed[["timestamp", "tips_10y_real_yield"]]
        column = "vix" if spec.dataset_id == "DS-001" else "ted_spread"
        renamed = frame.rename(columns={"DATE": "timestamp", "VALUE": column})
        return renamed[["timestamp", column]]


class ETFHoldingsProvider(BaseProvider):
    name = "ETFHoldingsProvider"

    def parse_bytes(self, spec: DatasetSpec, raw: bytes) -> pd.DataFrame:
        frame = pd.read_csv(io.StringIO(raw.decode("utf-8")))
        if spec.dataset_id == "DS-007":
            return frame.rename(columns={"date": "timestamp"})[
                ["timestamp", "gld_shares_outstanding", "gld_tonnes"]
            ]
        return frame.rename(columns={"date": "timestamp"})[
            ["timestamp", "iau_shares_outstanding", "iau_tonnes"]
        ]


class CFTCProvider(BaseProvider):
    name = "CFTCProvider"

    def parse_bytes(self, spec: DatasetSpec, raw: bytes) -> pd.DataFrame:
        frame = pd.read_csv(io.StringIO(raw.decode("utf-8")))
        if spec.dataset_id == "DS-009":
            return frame.rename(columns={"date": "timestamp"})[
                ["timestamp", "non_commercial_long", "non_commercial_short", "non_commercial_net"]
            ]
        return frame.rename(columns={"date": "timestamp"})[
            ["timestamp", "dealer_long", "dealer_short", "dealer_net"]
        ]


class CBOEProvider(BaseProvider):
    name = "CBOEProvider"

    def parse_bytes(self, spec: DatasetSpec, raw: bytes) -> pd.DataFrame:
        frame = pd.read_csv(io.StringIO(raw.decode("utf-8")))
        return frame.rename(columns={"DATE": "timestamp", "VALUE": "gvz"})[["timestamp", "gvz"]]


class WGCProvider(BaseProvider):
    name = "WGCProvider"

    def parse_bytes(self, spec: DatasetSpec, raw: bytes) -> pd.DataFrame:
        frame = pd.read_csv(io.StringIO(raw.decode("utf-8")))
        return frame.rename(columns={"date": "timestamp"})[
            ["timestamp", "official_sector_net_tonnes", "reported_central_bank_buyers"]
        ]


class AcademicProvider(BaseProvider):
    name = "AcademicProvider"

    def parse_bytes(self, spec: DatasetSpec, raw: bytes) -> pd.DataFrame:
        frame = pd.read_csv(io.StringIO(raw.decode("utf-8")))
        return frame.rename(columns={"date": "timestamp"})[["timestamp", "gpr_index"]]


@dataclass(frozen=True)
class IngestedDataset:
    spec: DatasetSpec
    frame: pd.DataFrame
    manifest: DatasetManifest
    manifest_path: Path
    data_path: Path
    raw_path: Path
    quality_path: Path


def _provider_library() -> dict[str, BaseProvider]:
    return {
        "FREDProvider": FREDProvider(),
        "ETFHoldingsProvider": ETFHoldingsProvider(),
        "CFTCProvider": CFTCProvider(),
        "CBOEProvider": CBOEProvider(),
        "WGCProvider": WGCProvider(),
        "AcademicProvider": AcademicProvider(),
    }


def _canonical_csv(frame: pd.DataFrame) -> bytes:
    ordered = frame.copy()
    ordered["timestamp"] = pd.to_datetime(ordered["timestamp"], utc=True)
    ordered = ordered.sort_values("timestamp").reset_index(drop=True)
    ordered["timestamp"] = ordered["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    csv_text = ordered.to_csv(index=False, lineterminator="\n", float_format="%.10f")
    return csv_text.encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _expected_periods(start: pd.Timestamp, end: pd.Timestamp, cadence: str) -> int:
    delta_days = max(0, int((end - start).days))
    if cadence in {"daily", "derived"}:
        return max(1, delta_days + 1)
    if cadence == "weekly":
        return max(1, delta_days // 7 + 1)
    months = (end.year - start.year) * 12 + end.month - start.month + 1
    return max(1, months)


def _normalize_frame(spec: DatasetSpec, frame: pd.DataFrame) -> pd.DataFrame:
    expected_columns = [field.name for field in spec.schema_fields]
    if list(frame.columns) != expected_columns:
        raise ValueError(f"{spec.dataset_id}: expected columns {expected_columns}, got {list(frame.columns)}")
    normalized = frame.copy()
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], utc=True)
    if normalized["timestamp"].isna().any():
        raise ValueError(f"{spec.dataset_id}: timestamp normalization failed")
    normalized = normalized.sort_values("timestamp").reset_index(drop=True)
    for field in spec.schema_fields:
        if field.name == "timestamp":
            continue
        if field.dtype in {"float", "int"}:
            normalized[field.name] = pd.to_numeric(normalized[field.name], errors="coerce")
        if not field.nullable and normalized[field.name].isna().any():
            raise ValueError(f"{spec.dataset_id}: non-nullable field {field.name} contains nulls")
        if field.dtype == "int":
            normalized[field.name] = normalized[field.name].astype(int)
        if field.dtype == "float":
            normalized[field.name] = normalized[field.name].astype(float)
    return normalized


def _compute_quality(spec: DatasetSpec, frame: pd.DataFrame) -> DatasetQualityMetrics:
    start = cast(pd.Timestamp, frame["timestamp"].min())
    end = cast(pd.Timestamp, frame["timestamp"].max())
    expected = _expected_periods(start, end, spec.cadence)
    record_count = int(len(frame))
    coverage = min(record_count / max(1, expected), 1.0)
    value_frame = frame.drop(columns=["timestamp"])
    total_cells = max(1, int(value_frame.shape[0] * value_frame.shape[1]))
    missing_cells = int(value_frame.isna().sum().sum())
    completeness = 1.0 - (missing_cells / total_cells)
    duplicate_rate = float(frame["timestamp"].duplicated().mean()) if record_count > 0 else 0.0
    monotonic = bool(frame["timestamp"].is_monotonic_increasing)
    timestamp_consistency = 1.0 if monotonic and duplicate_rate == 0.0 else 0.5
    end_ts = end.to_pydatetime().replace(tzinfo=UTC)
    now_ts = datetime.fromisoformat(_NOW.replace("Z", "+00:00"))
    age_days = max(0.0, (now_ts - end_ts).total_seconds() / 86400.0)
    freshness_window = {"daily": 10.0, "weekly": 35.0, "monthly": 120.0, "derived": 10.0}[spec.cadence]
    freshness = max(0.0, 1.0 - age_days / freshness_window)
    schema_conformity = 1.0
    validation_score = (
        coverage + completeness + freshness + (1.0 - duplicate_rate) + timestamp_consistency + schema_conformity
    ) / 6.0
    confidence_score = (
        0.35 * validation_score
        + 0.20 * coverage
        + 0.20 * completeness
        + 0.15 * freshness
        + 0.10 * spec.quality_weight
    )
    return DatasetQualityMetrics(
        record_count=record_count,
        coverage=round(coverage, 4),
        completeness=round(completeness, 4),
        freshness=round(freshness, 4),
        missing_rate=round(missing_cells / total_cells, 4),
        duplicate_rate=round(duplicate_rate, 4),
        timestamp_consistency=round(timestamp_consistency, 4),
        schema_conformity=round(schema_conformity, 4),
        validation_score=round(validation_score, 4),
        confidence_score=round(confidence_score, 4),
        start_timestamp=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_timestamp=end.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _write_dataset_artifacts(
    repo_root: Path,
    spec: DatasetSpec,
    frame: pd.DataFrame,
    raw: bytes,
) -> IngestedDataset:
    canonical = _canonical_csv(frame)
    checksum = _sha256(canonical)
    raw_checksum = _sha256(raw)
    latest_ts = cast(pd.Timestamp, frame["timestamp"].max()).strftime("%Y%m%d")
    version_id = f"DF2-{spec.dataset_id.replace('-', '')}-{latest_ts}-{checksum[:8]}"
    dataset_dir = repo_root / DATA_FOUNDATION_DIR / "datasets" / spec.dataset_id / version_id
    dataset_dir.mkdir(parents=True, exist_ok=True)
    data_path = dataset_dir / "data.csv"
    raw_path = dataset_dir / "raw_snapshot.csv"
    quality_path = dataset_dir / "quality.json"
    manifest_path = dataset_dir / "manifest.json"
    checksum_path = dataset_dir / "checksum.sha256"
    data_path.write_bytes(canonical)
    raw_path.write_bytes(raw)
    quality = _compute_quality(spec, frame)
    write_json(quality_path, quality.model_dump())
    provenance = {
        "retrieved_at": _NOW,
        "source_kind": spec.source_kind,
        "fixture_or_remote": "fixture",
        "timezone": spec.timezone,
    }
    manifest = DatasetManifest(
        dataset_id=spec.dataset_id,
        dataset_name=spec.name,
        version_id=version_id,
        generated_at=_NOW,
        provider=spec.provider,
        source=spec.source,
        source_url=spec.source_url,
        cadence=spec.cadence,
        timezone=spec.timezone,
        work_package=spec.work_package,
        storage_path=str(data_path.relative_to(repo_root)),
        row_count=len(frame),
        checksum_sha256=checksum,
        raw_checksum_sha256=raw_checksum,
        covered_variables=spec.market_state_variables,
        supported_mechanisms=spec.supported_mechanisms,
        supported_families=spec.supported_families,
        provenance=provenance,
        quality=quality,
    )
    write_json(manifest_path, manifest.model_dump())
    checksum_path.write_text(f"{checksum}  data.csv\n", encoding="utf-8")
    return IngestedDataset(
        spec=spec,
        frame=frame,
        manifest=manifest,
        manifest_path=manifest_path,
        data_path=data_path,
        raw_path=raw_path,
        quality_path=quality_path,
    )


def _build_policy_curve(
    repo_root: Path,
    spec: DatasetSpec,
    dataset_map: dict[str, IngestedDataset],
) -> IngestedDataset:
    breakevens = dataset_map["DS-012"].frame.copy()
    treasury = dataset_map["DS-018"].frame.copy()
    tips = dataset_map["DS-019"].frame.copy()
    merged = breakevens.merge(treasury, on="timestamp", how="inner").merge(tips, on="timestamp", how="inner")
    merged["policy_expectation_public_curve"] = (
        merged["ust_2y_yield"] - merged["tips_10y_real_yield"] - 0.5 * merged["breakeven_5y"]
    )
    normalized = _normalize_frame(spec, merged[["timestamp", "policy_expectation_public_curve"]])
    raw = _canonical_csv(normalized)
    return _write_dataset_artifacts(repo_root, spec, normalized, raw)


def _registry_entries(dataset: IngestedDataset) -> tuple[DatasetRegistryEntry, CoverageRegistryEntry]:
    quality = dataset.manifest.quality
    manifest_rel = str(Path(dataset.manifest.storage_path).with_name("manifest.json"))
    return (
        DatasetRegistryEntry(
            dataset_id=dataset.spec.dataset_id,
            name=dataset.spec.name,
            version_id=dataset.manifest.version_id,
            provider=dataset.spec.provider,
            domain=dataset.spec.domain,
            cadence=dataset.spec.cadence,
            work_package=dataset.spec.work_package,
            storage_path=dataset.manifest.storage_path,
            manifest_path=manifest_rel,
            quality_score=quality.validation_score,
            confidence_score=quality.confidence_score,
            covered_variables=dataset.spec.market_state_variables,
            supported_mechanisms=dataset.spec.supported_mechanisms,
        ),
        CoverageRegistryEntry(
            dataset_id=dataset.spec.dataset_id,
            record_count=quality.record_count,
            coverage=quality.coverage,
            completeness=quality.completeness,
            missing_rate=quality.missing_rate,
            duplicate_rate=quality.duplicate_rate,
            start_timestamp=quality.start_timestamp,
            end_timestamp=quality.end_timestamp,
        ),
    )


def _market_state_registry(specs: list[DatasetSpec]) -> list[MarketStateRegistryEntry]:
    variable_to_datasets: dict[str, list[str]] = {}
    for spec in specs:
        for variable in spec.market_state_variables:
            variable_to_datasets.setdefault(variable, []).append(spec.dataset_id)
    entries: list[MarketStateRegistryEntry] = []
    for domain in MARKET_STATE_DOMAINS:
        domain_name = str(domain["name"])
        for variable in cast(list[str], domain["variables"]):
            datasets = tuple(sorted(variable_to_datasets.get(variable, [])))
            status: str = "UNMAPPED"
            if datasets:
                status = "OBSERVED"
            elif any(variable in spec.market_state_variables for spec in specs):
                status = "PARTIAL"
            entries.append(
                MarketStateRegistryEntry(
                    domain=domain_name,
                    variable=variable,
                    dataset_ids=datasets,
                    status=cast(Any, status),
                )
            )
    return entries


def _implemented_dataset_map(specs: list[DatasetSpec]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for spec in specs:
        for variable in spec.market_state_variables:
            mapping[variable] = spec.dataset_id
    mapping["comex_positioning"] = "DS-009"
    mapping["gld_etf_flows"] = "DS-007"
    mapping["iau_etf_flows"] = "DS-008"
    mapping["cot_dealers"] = "DS-010"
    mapping["real_yield_tip_direct"] = "DS-019"
    mapping["geopolitical_risk_index"] = "DS-017"
    mapping["institutional_flow_direction"] = "DS-014"
    mapping["dealer_gamma"] = "DS-011"
    return mapping


def _observation_registry(specs: list[DatasetSpec]) -> list[dict[str, Any]]:
    from tools.alpha_research.institutional_observability import _MECHANISM_OBSERVABILITY

    implemented = _implemented_dataset_map(specs)
    registry: list[dict[str, Any]] = []
    for mechanism, payload in _MECHANISM_OBSERVABILITY.items():
        required = cast(list[str], payload["required"])
        observed_before = set(cast(list[str], payload["observed"]))
        observed_after = set(observed_before)
        remaining = []
        newly_observed = []
        for item in required:
            if item in observed_before:
                continue
            if item in implemented:
                observed_after.add(item)
                newly_observed.append(item)
            else:
                remaining.append(item)
        proxy_dependence_before = len(cast(list[str], payload["proxies"]))
        proxy_dependence_after = max(0, proxy_dependence_before - len(newly_observed))
        registry.append(
            {
                "mechanism_type": mechanism,
                "family_id": payload["family"],
                "required_count": len(required),
                "observed_before": len(observed_before),
                "observed_after": len(observed_after),
                "newly_observed_variables": newly_observed,
                "remaining_unavailable": remaining,
                "proxy_dependence_before": proxy_dependence_before,
                "proxy_dependence_after": proxy_dependence_after,
                "still_blocked": len(remaining) > 0,
            }
        )
    return registry


def _provider_library_entries(specs: list[DatasetSpec]) -> list[ProviderLibraryEntry]:
    grouped: dict[str, list[DatasetSpec]] = {}
    for spec in specs:
        grouped.setdefault(spec.provider, []).append(spec)
    return [
        ProviderLibraryEntry(
            provider=provider,
            supported_source_kinds=tuple(sorted({spec.source_kind for spec in provider_specs})),
            deterministic=True,
            historical_only=True,
            requires_api_key=any(spec.requires_api_key for spec in provider_specs),
            retry_attempts=3,
            checksum_enabled=True,
        )
        for provider, provider_specs in sorted(grouped.items())
    ]


def _emit_schemas(repo_root: Path) -> dict[str, str]:
    DATA_FOUNDATION_SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    model_map: dict[str, type[BaseModel]] = {
        "dataset-spec.schema.json": DatasetSpec,
        "dataset-manifest.schema.json": DatasetManifest,
        "dataset-quality.schema.json": DatasetQualityMetrics,
        "dataset-registry-entry.schema.json": DatasetRegistryEntry,
        "coverage-registry-entry.schema.json": CoverageRegistryEntry,
        "market-state-registry-entry.schema.json": MarketStateRegistryEntry,
        "provider-library-entry.schema.json": ProviderLibraryEntry,
    }
    written: dict[str, str] = {}
    for filename, model in model_map.items():
        path = repo_root / DATA_FOUNDATION_SCHEMA_DIR / filename
        write_json(path, model.model_json_schema())
        written[filename] = str(path.relative_to(repo_root))
    return written


def _emit_reports(repo_root: Path, summary: dict[str, Any]) -> dict[str, str]:
    report_dir = repo_root / DATA_FOUNDATION_REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    datasets = cast(list[dict[str, Any]], summary["dataset_registry"])
    quality = cast(list[dict[str, Any]], summary["quality_registry"])
    coverage = cast(list[dict[str, Any]], summary["coverage_registry"])
    observations = cast(list[dict[str, Any]], summary["observation_registry"])
    market_state = cast(list[dict[str, Any]], summary["market_state_registry"])
    providers = cast(list[dict[str, Any]], summary["provider_library"])

    dataset_registry_md = report_dir / "DATASET_REGISTRY.md"
    dataset_rows = [
        [item["dataset_id"], item["name"], item["provider"], item["work_package"], item["quality_score"], item["confidence_score"]]
        for item in datasets
    ]
    write_markdown(dataset_registry_md, f"# Dataset Registry\n\n{markdown_table(['ID', 'Dataset', 'Provider', 'WP', 'Quality', 'Confidence'], dataset_rows)}\n")
    written["dataset_registry"] = str(dataset_registry_md.relative_to(repo_root))

    quality_md = report_dir / "QUALITY_DASHBOARD.md"
    quality_rows = [
        [item["dataset_id"], item["validation_score"], item["confidence_score"], item["missing_rate"], item["duplicate_rate"], item["freshness"]]
        for item in quality
    ]
    write_markdown(quality_md, f"# Quality Dashboard\n\n{markdown_table(['ID', 'Validation', 'Confidence', 'Missing', 'Duplicate', 'Freshness'], quality_rows)}\n")
    written["quality_dashboard"] = str(quality_md.relative_to(repo_root))

    coverage_md = report_dir / "COVERAGE_DASHBOARD.md"
    coverage_rows = [
        [item["dataset_id"], item["record_count"], item["coverage"], item["completeness"], item["start_timestamp"], item["end_timestamp"]]
        for item in coverage
    ]
    write_markdown(coverage_md, f"# Coverage Dashboard\n\n{markdown_table(['ID', 'Records', 'Coverage', 'Completeness', 'Start', 'End'], coverage_rows)}\n")
    written["coverage_dashboard"] = str(coverage_md.relative_to(repo_root))

    metadata_md = report_dir / "METADATA_CATALOGUE.md"
    metadata_rows = [
        [item["dataset_id"], item["provider"], item["domain"], ", ".join(cast(list[str], item["covered_variables"])), item["storage_path"]]
        for item in datasets
    ]
    write_markdown(metadata_md, f"# Metadata Catalogue\n\n{markdown_table(['ID', 'Provider', 'Domain', 'Variables', 'Storage'], metadata_rows)}\n")
    written["metadata_catalogue"] = str(metadata_md.relative_to(repo_root))

    provider_md = report_dir / "PROVIDER_LIBRARY.md"
    provider_rows = [
        [item["provider"], ", ".join(cast(list[str], item["supported_source_kinds"])), item["historical_only"], item["checksum_enabled"]]
        for item in providers
    ]
    write_markdown(provider_md, f"# Provider Library\n\n{markdown_table(['Provider', 'Source Kinds', 'Historical Only', 'Checksums'], provider_rows)}\n")
    written["provider_library"] = str(provider_md.relative_to(repo_root))

    schema_md = report_dir / "JSON_SCHEMA_LIBRARY.md"
    schema_rows: list[list[object]] = [
        [name, path]
        for name, path in sorted(cast(dict[str, str], summary["schema_paths"]).items())
    ]
    write_markdown(schema_md, f"# JSON Schema Library\n\n{markdown_table(['Schema', 'Path'], schema_rows)}\n")
    written["json_schema_library"] = str(schema_md.relative_to(repo_root))

    manifest_md = report_dir / "MANIFEST_CATALOGUE.md"
    manifest_rows = [
        [item["dataset_id"], item["version_id"], item["manifest_path"], item["quality_score"], item["confidence_score"]]
        for item in datasets
    ]
    write_markdown(manifest_md, f"# Manifest Catalogue\n\n{markdown_table(['ID', 'Version', 'Manifest', 'Quality', 'Confidence'], manifest_rows)}\n")
    written["manifest_catalogue"] = str(manifest_md.relative_to(repo_root))

    observation_md = report_dir / "OBSERVABILITY_IMPROVEMENT_REPORT.md"
    observation_rows = [
        [item["mechanism_type"], item["observed_before"], item["observed_after"], item["proxy_dependence_before"], item["proxy_dependence_after"], "BLOCKED" if item["still_blocked"] else "READY"]
        for item in observations
    ]
    write_markdown(observation_md, f"# Observability Improvement Report\n\n{markdown_table(['Mechanism', 'Observed Before', 'Observed After', 'Proxy Before', 'Proxy After', 'Status'], observation_rows)}\n")
    written["observability_improvement_report"] = str(observation_md.relative_to(repo_root))

    market_state_md = report_dir / "MARKET_STATE_REGISTRY.md"
    market_rows = [
        [item["domain"], item["variable"], ", ".join(cast(list[str], item["dataset_ids"])), item["status"]]
        for item in market_state
        if item["status"] != "UNMAPPED"
    ]
    write_markdown(market_state_md, f"# Market State Registry\n\n{markdown_table(['Domain', 'Variable', 'Datasets', 'Status'], market_rows)}\n")
    written["market_state_registry"] = str(market_state_md.relative_to(repo_root))

    arb_md = report_dir / "ARB_RECOMMENDATION_DATA_FOUNDATION_V2_PHASE1.md"
    blocked_families = "\n".join(f"- {item}" for item in cast(list[str], summary["remaining_blocked_families"]))
    commercial_gaps = "\n".join(f"- {item}" for item in cast(list[str], summary["remaining_commercial_only_gaps"]))
    write_markdown(
        arb_md,
        f"""# ARB Recommendation — Data Foundation V2 Phase 1

- Tier 1 datasets implemented: {summary['dataset_count']}
- Market variables covered: {summary['covered_variable_count']}
- Proxy dependence reduction: {summary['proxy_dependence_reduction']}
- Ready mechanisms after Tier 1: {summary['ready_mechanisms_after_tier1']}

## Remaining Blocked Alpha Families
{blocked_families}

## Remaining Commercial-Only Gaps
{commercial_gaps}

## Recommendation
Await ARB approval before Discovery Cycle 5. Do not implement commercial or microstructure datasets and do not resume alpha validation.
""",
    )
    written["arb_recommendation"] = str(arb_md.relative_to(repo_root))
    return written


def build_data_foundation_v2_tier1(repo_root: Path, source: SourceAdapter | None = None) -> dict[str, Any]:
    specs = _tier1_specs()
    fixture_source = source or FixtureSourceAdapter(_FIXTURES)
    providers = _provider_library()
    ingested: dict[str, IngestedDataset] = {}

    for spec in specs:
        if spec.provider == "DerivedPolicyProvider":
            continue
        provider = providers[spec.provider]
        raw = fixture_source.fetch(provider.build_request(spec))
        frame = _normalize_frame(spec, provider.parse_bytes(spec, raw))
        ingested[spec.dataset_id] = _write_dataset_artifacts(repo_root, spec, frame, raw)

    derived_spec = next(spec for spec in specs if spec.provider == "DerivedPolicyProvider")
    ingested[derived_spec.dataset_id] = _build_policy_curve(repo_root, derived_spec, ingested)

    dataset_registry: list[dict[str, Any]] = []
    coverage_registry: list[dict[str, Any]] = []
    quality_registry: list[dict[str, Any]] = []
    manifest_catalogue: list[dict[str, Any]] = []
    for dataset_id in sorted(ingested):
        ingested_dataset = ingested[dataset_id]
        registry_entry, coverage_entry = _registry_entries(ingested_dataset)
        dataset_registry.append(registry_entry.model_dump())
        coverage_registry.append(coverage_entry.model_dump())
        quality_registry.append(
            {"dataset_id": dataset_id, **ingested_dataset.manifest.quality.model_dump()}
        )
        manifest_catalogue.append(
            {
                "dataset_id": dataset_id,
                "version_id": ingested_dataset.manifest.version_id,
                "manifest_path": str(ingested_dataset.manifest_path.relative_to(repo_root)),
                "checksum": ingested_dataset.manifest.checksum_sha256,
                "raw_checksum": ingested_dataset.manifest.raw_checksum_sha256,
            }
        )

    market_state_registry = [entry.model_dump() for entry in _market_state_registry(specs)]
    observation_registry = _observation_registry(specs)
    provider_library = [entry.model_dump() for entry in _provider_library_entries(specs)]
    schemas = _emit_schemas(repo_root)

    data_dir = repo_root / DATA_FOUNDATION_DIR / "registries"
    data_dir.mkdir(parents=True, exist_ok=True)
    write_json(data_dir / "dataset_registry.json", dataset_registry)
    write_json(data_dir / "coverage_registry.json", coverage_registry)
    write_json(data_dir / "quality_registry.json", quality_registry)
    write_json(data_dir / "observation_registry.json", observation_registry)
    write_json(data_dir / "market_state_registry.json", market_state_registry)
    write_json(data_dir / "metadata_catalogue.json", dataset_registry)
    write_json(data_dir / "provider_library.json", provider_library)
    write_json(data_dir / "manifest_catalogue.json", manifest_catalogue)

    implemented_ids = {spec.dataset_id for spec in specs}
    commercial_gaps = sorted(
        item["dataset_id"]
        for item in DATASET_CATALOGUE
        if str(item["dataset_id"]) not in implemented_ids and "commercial" in str(item["licensing"]).lower()
    )
    ready_mechanisms = sorted(
        item["mechanism_type"] for item in observation_registry if not bool(item["still_blocked"])
    )
    remaining_blocked_families = sorted(
        {
            str(item["family_id"])
            for item in observation_registry
            if bool(item["still_blocked"])
        }
    )
    proxy_before = sum(int(item["proxy_dependence_before"]) for item in observation_registry)
    proxy_after = sum(int(item["proxy_dependence_after"]) for item in observation_registry)
    summary: dict[str, Any] = {
        "phase": "DATA_FOUNDATION_V2_PHASE_1",
        "generated_at": _NOW,
        "dataset_count": len(specs),
        "supported_datasets": [spec.dataset_id for spec in specs],
        "dataset_registry": dataset_registry,
        "coverage_registry": coverage_registry,
        "quality_registry": quality_registry,
        "observation_registry": observation_registry,
        "market_state_registry": market_state_registry,
        "provider_library": provider_library,
        "manifest_catalogue": manifest_catalogue,
        "schema_paths": schemas,
        "covered_variable_count": len({variable for spec in specs for variable in spec.market_state_variables}),
        "proxy_dependence_reduction": proxy_before - proxy_after,
        "ready_mechanisms_after_tier1": ready_mechanisms,
        "remaining_blocked_families": remaining_blocked_families,
        "remaining_commercial_only_gaps": commercial_gaps,
        "no_runtime_changes": True,
        "no_broker_connectivity": True,
        "no_alpha_validation": True,
    }
    report_paths = _emit_reports(repo_root, summary)
    summary["report_paths"] = report_paths
    write_json(repo_root / DATA_FOUNDATION_REPORT_DIR / "data_foundation_v2_phase1_summary.json", summary)
    return summary
