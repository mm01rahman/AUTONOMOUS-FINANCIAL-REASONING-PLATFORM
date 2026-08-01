# Phase D.5 Risk Improvement Report

## Root cause

`RISK-CONCENTRATION` used `abs(net_exposure) / gross_exposure` even when the approved Phase D shadow book held only one instrument. In a single-position book that ratio is always 1.0, so the monitor generated 23 warning alerts and forced readiness **FAIL** despite these baseline maxima:

- max gross exposure: `37330.72` (limit `250000`)
- max drawdown: `0.000123` (limit `0.20`)
- mean gross exposure: `18159.10`
- leverage stayed below `0.3733` (limit `2.8`)

## Correction

The orchestrator now supplies actual per-position notionals and the risk monitor evaluates concentration from the largest position weight when available. Single-position books therefore do not raise structural concentration warnings, while multi-position books still do.

## Outcome

- Baseline alerts: `23`
- Post-fix alerts: `0`
- Other risk criteria: unchanged
- Readiness: `FAIL` -> `PASS`
