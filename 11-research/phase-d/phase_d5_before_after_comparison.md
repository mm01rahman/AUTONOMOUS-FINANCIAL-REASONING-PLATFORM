# Phase D.5 Before vs After Comparison

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| Readiness | FAIL | PASS | n/a |
| Risk codes | {"RISK-CONCENTRATION": 23} | {} | n/a |
| Risk alerts | 23.000000 | 0.000000 | -23.000000 |
| Total return | 0.000118 | 0.000118 | 0.000000 |
| Sharpe | -15.688426 | -15.688426 | 0.000000 |
| Max drawdown | 0.000123 | 0.000123 | 0.000000 |
| Mean gross exposure | 18159.105000 | 18159.105000 | 0.000000 |
| Final equity | 100008.911971 | 100008.911971 | 0.000000 |
| Decision-log records | 24.000000 | 24.000000 | 0.000000 |

- Decision-log checksum was intentionally unchanged across fresh runs, demonstrating no strategy-path mutation.
- Risk readiness improved because only the alert calibration changed; portfolio path and PnL were preserved.
- Pre-fix root artifact contamination observation: {"observed_at": "2026-08-01T19:17:00+06:00", "decision_log_lines": 48, "decision_log_unique_sequences": 24, "decision_log_digest_records": 24, "decision_log_file_sha256": "44d7850d25be5634e527037043d3f0b24e83a1dfdd674f72ea952b76ba156370", "decision_log_digest_checksum": "9d4c65dcf8e1e1d3ba42ec28ef3634ce9551f939f45eedfea2c6f252b889123b"}
