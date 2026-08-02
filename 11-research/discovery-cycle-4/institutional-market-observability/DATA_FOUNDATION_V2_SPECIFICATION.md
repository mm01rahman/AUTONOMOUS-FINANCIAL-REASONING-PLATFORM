# Data Foundation V2 Specification
## Version 2.0.0

### Principles
- Every dataset must trace to at least one scientific hypothesis.
- All datasets are versioned with SHA-256 content hash.
- All ingestion pipelines are deterministic and reproducible.
- No live broker connections; offline data only.
- All datasets include quality scores, provenance, and update audit trail.
- Time synchronisation: all timestamps normalized to UTC.
- Schema validation is mandatory before any dataset enters the research layer.

### Pipeline Stages
| Stage | Components | Description |
| --- | --- | --- |
| ACQUISITION | SourceAdapter, RetryPolicy, ChecksumVerifier | Deterministic download from authorised sources; retry logic; checksum verificati |
| VALIDATION | SchemaValidator, RangeChecker, MissingValueAuditor, OutlierDetector | Schema validation, range checks, missing-value audits, outlier detection. |
| NORMALIZATION | TimestampNormalizer, UnitConverter, CalendarAdjuster, FrequencyHarmonizer | UTC timestamp alignment, unit normalization, calendar adjustment, frequency harm |
| VERSIONING | DataVersionStore, ContentHasher, SnapshotRegistry | Immutable versioned snapshots with SHA-256 hash, git-like ancestry, tagged relea |
| METADATA | MetadataStore, ProvenanceTracker, LicenseRegistry | Source provenance, license, acquisition date, data quality score, update cadence |
| EVIDENCE_TRACKING | EvidenceEmitter, IKROSLinker | IKROS evidence linkage: every dataset update creates an evidence record. |
| QUALITY_SCORING | DataQualityScorer, CompletenessChecker, TimelinessMonitor | Automated quality score: completeness × timeliness × consistency × lineage. |

### Priority Datasets
DS-001, DS-003, DS-007, DS-009, DS-010, DS-011, DS-012, DS-018, DS-019

Offline only: True | Live broker prohibited: True
