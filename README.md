# Autonomous Financial Reasoning Platform (AFRP)

AI-native autonomous financial reasoning and execution system governed by
machine-verifiable evidence (AFRP-BASELINE-1.0.0, EGP-2.0).

**Release:** 1.0.0 · **Core readiness:** GO · **Live-money activation:** conditional

## Entry Points

- **Bootloader:** [`00-governance/KERNEL.md`](00-governance/KERNEL.md) — read first.
- **Constitution:** [`00-governance/000_ENGINEERING_CONSTITUTION.md`](00-governance/000_ENGINEERING_CONSTITUTION.md)
- **Topology & document index:** [`REPOSITORY_MANIFEST.yaml`](REPOSITORY_MANIFEST.yaml)
- **Execution DAG:** [`03-engineering/CAPABILITY_REGISTRY.yaml`](03-engineering/CAPABILITY_REGISTRY.yaml)

## Products

| Product | Path | Purpose |
| --- | --- | --- |
| Engineering OS | `tools/afrp-cli/` | Governs agent execution: `afrp boot · plan · validate · evidence · health · run` |
| Runtime Platform | `06-runtime/` | Six cognitive layers, Protobuf-only interconnect |
| Research Platform | `07-research/` | Offline backtesting and calibration |

## Quickstart

```bash
uv sync --group dev
uv run afrp boot      # EGP-2.0 zero-write handshake
uv run afrp plan      # next executable work packages
uv run pytest tests   # full test suite
uv run python -m tools.proto_gate
uv run python -m tools.ops_gate
```

See [`10-release/ARCHITECTURE_REVIEW_REPORT_v1.0.md`](10-release/ARCHITECTURE_REVIEW_REPORT_v1.0.md)
for measured quality, evidence, technical debt, and live-deployment prerequisites.
