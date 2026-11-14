---
name: backtest-harness
description: Toy GOR-zone allocation backtest on history.json with transaction costs, turnover and a 70/30 in-sample/out-of-sample split. Sanity-check only; not a validated edge.
---

# Backtest Harness

## When to use
- Sanity-check a rule change before touching `config.py`.
- Compare a GOR-zone rule against buy-and-hold gold, oil and 60/40.

## Command
```bash
python skills/backtest-harness/backtest.py
python skills/backtest-harness/backtest.py --cost-bps 20 --rebalance-days 10 --json
```

## Rules tested
- GOR ≥45: oil 38 / gold 10 / cash 52; red screener zeroes oil, yellow halves it.
- 30–45: oil 20 / gold 15 / cash 65.
- 20–30: oil 0 / gold 15 / cash 85.
- <20: oil 0 / gold 7 / cash 93.

## Limitations
- ~5 months of data; no A-shares/copper; cash return 0; daily gaps in early history.
- Results are a sanity check, not evidence of an edge. Do not publish CAGR/Sharpe without the caveat.
