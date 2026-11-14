---
name: scenario-analyzer
description: Build an 18-month scenario pack from a headline, pre-filled with the current GOR card, portfolio and credit data. Produces a structured 1st/2nd/3rd-order prompt sheet for analyst or Claude completion.
---

# Scenario Analyzer

## When to use
- A new macro/company headline needs a structured medium-term read.
- Before writing a deep report, to avoid mixing first-order reaction with third-order regime change.

## Command
```bash
python skills/scenario-analyzer/scenario.py \
  --headline "Nvidia CEO resigns; Duan Yongping clears common stock" \
  --horizon-months 18
```
Default output: `看板日志/reports/scenarios/scenario-YYYY-MM-DD.md`.

## Output
- Baseline table (card + FRED + portfolio, with vintages).
- 1st order prompts (0–3m).
- 2nd order table (suppliers, customers, competitors, credit, policy, positioning).
- 3rd order table (capex regime, governance, asset class, politics, geography).
- Base/upside/downside scenario table with signposts.
- Falsifiers and data sources.

## Contract
It does not invent conclusions. It assembles context and prompts; the analyst fills the verdicts.
