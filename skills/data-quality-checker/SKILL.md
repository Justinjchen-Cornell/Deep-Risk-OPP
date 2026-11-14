---
name: data-quality-checker
description: Validate Deep-Risk-OPP card, history, portfolio, performance, signal and cache data before publication. Flags stale vintages, GOR inconsistencies, allocation sums, unit/price-scale errors and missing metrics.
---

# Data Quality Checker

## When to use
- Before publishing the daily card, a LinkedIn post or a report.
- After a data refresh (FRED/EIA/market) and before regenerating `performance_latest.json`.
- When numbers from different vintages are about to be mixed.

## Command
```bash
python skills/data-quality-checker/dq_check.py
python skills/data-quality-checker/dq_check.py --json
python skills/data-quality-checker/dq_check.py --strict   # warnings fail
```

## Checks
- Card freshness (>2d warn, >7d error), price ranges, GOR consistency, allocation sum.
- History sort/duplicates, last-row fields, card-vs-history values.
- Model portfolio weights/NAV and card alignment.
- Performance ledger: measured entries need impressions/measured_at; no negative metrics.
- Signal log schema and duplicate ids.
- FRED/EIA cache staleness.

## Contract
Read-only. It never edits data; `--strict` is for CI/publication gates.
