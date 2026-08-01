# Phase D.5 Operational Failure Analysis

## D5-001 Operational Failure Analysis

- Baseline strict-readiness replay (`11-research/phase-d/d5-baseline`) failed solely because `RISK-CONCENTRATION` fired 23 times.
- No gross-exposure, leverage, drawdown, volatility, confidence-drift, or capital alerts were observed.
- The single traded instrument remained `XAUUSD`; therefore `abs(net_exposure)/gross_exposure` was structurally 1.0 whenever the book was non-flat.
- The published root decision log was also stale before D5: 48 lines were present while `decision_log_digest.json` claimed 24 records, proving append-on-rerun artifact contamination.

## D5-002 / D5-003 / D5-004 / D5-005 Assessment Summary

- World model stability: deterministic and bounded. Confidence stayed in [0.785, 0.855] with mean 0.791; no confidence-drift alerts.
- Decision engine behavior: 24/24 cycles authorized trades; signals were 21 buy / 3 sell, tracking deterministic momentum direction. This remained unchanged before vs after the fix.
- Execution assessment: {'partial': 6, 'failed': 4, 'filled': 14} with mean fill latency 42.35 ms and max latency 50 ms; broker calls remained zero. Execution friction degraded PnL but did not trigger operational risk gates.

## Per-cycle shadow trace

| Seq | Timestamp | Trend | Signal | Exec | Gross | Net | Drawdown | Total PnL |
|---:|---|---|---|---|---:|---:|---:|---:|
| 0 | 2026-01-01T00:00:00+00:00 | down | sell | partial | 2324.52 | -2324.52 | 0.000029 | -2.89 |
| 1 | 2026-01-01T00:05:00+00:00 | up | buy | failed | 2324.99 | -2324.99 | 0.000034 | -3.36 |
| 2 | 2026-01-01T00:10:00+00:00 | up | buy | filled | 0.00 | 0.00 | 0.000060 | -6.00 |
| 3 | 2026-01-01T00:15:00+00:00 | up | buy | filled | 2325.93 | 2325.93 | 0.000084 | -8.43 |
| 4 | 2026-01-01T00:20:00+00:00 | up | buy | filled | 4652.80 | 4652.80 | 0.000097 | -9.68 |
| 5 | 2026-01-01T00:25:00+00:00 | up | buy | filled | 6980.61 | 6980.61 | 0.000113 | -11.29 |
| 6 | 2026-01-01T00:30:00+00:00 | up | buy | filled | 9309.36 | 9309.36 | 0.000126 | -12.59 |
| 7 | 2026-01-01T00:35:00+00:00 | up | buy | failed | 9311.24 | 9311.24 | 0.000107 | -10.71 |
| 8 | 2026-01-01T00:40:00+00:00 | up | buy | filled | 11641.40 | 11641.40 | 0.000110 | -11.03 |
| 9 | 2026-01-01T00:45:00+00:00 | down | sell | failed | 11638.35 | 11638.35 | 0.000141 | -14.08 |
| 10 | 2026-01-01T00:50:00+00:00 | up | buy | partial | 13968.84 | 13968.84 | 0.000152 | -15.15 |
| 11 | 2026-01-01T00:55:00+00:00 | up | buy | filled | 16300.27 | 16300.27 | 0.000147 | -14.69 |
| 12 | 2026-01-01T01:00:00+00:00 | up | buy | partial | 18632.64 | 18632.64 | 0.000147 | -14.67 |
| 13 | 2026-01-01T01:05:00+00:00 | up | buy | partial | 20965.95 | 20965.95 | 0.000138 | -13.79 |
| 14 | 2026-01-01T01:10:00+00:00 | up | buy | filled | 23300.20 | 23300.20 | 0.000113 | -11.35 |
| 15 | 2026-01-01T01:15:00+00:00 | up | buy | filled | 25635.39 | 25635.39 | 0.000093 | -9.27 |
| 16 | 2026-01-01T01:20:00+00:00 | up | buy | filled | 27971.52 | 27971.52 | 0.000062 | -6.21 |
| 17 | 2026-01-01T01:25:00+00:00 | up | buy | filled | 30308.59 | 30308.59 | 0.000028 | -2.83 |
| 18 | 2026-01-01T01:30:00+00:00 | down | sell | filled | 27969.84 | 27969.84 | 0.000129 | -12.90 |
| 19 | 2026-01-01T01:35:00+00:00 | up | buy | partial | 30306.77 | 30306.77 | 0.000105 | -10.53 |
| 20 | 2026-01-01T01:40:00+00:00 | up | buy | filled | 32644.64 | 32644.64 | 0.000071 | -7.13 |
| 21 | 2026-01-01T01:45:00+00:00 | up | buy | partial | 34983.45 | 34983.45 | 0.000034 | -3.43 |
| 22 | 2026-01-01T01:50:00+00:00 | up | buy | failed | 34990.50 | 34990.50 | 0.000000 | 3.62 |
| 23 | 2026-01-01T01:55:00+00:00 | up | buy | filled | 37330.72 | 37330.72 | 0.000000 | 8.91 |
