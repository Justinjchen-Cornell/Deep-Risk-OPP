---
name: pre-trade-discipline-gate
description: Mechanical pre-trade checklist for the GOR framework. Blocks planless, oversized, stale-data, panic-VIX, credit-stress or regime-blocked adds; downgrades blocks only with an explicit override reason.
---

# Pre-Trade Discipline Gate

## When to use
- Immediately before any manual position change.
- Before publishing a model-portfolio rebalance.

## Command
```bash
python skills/pre-trade-discipline-gate/gate.py --action add --asset oil --weight 5 \
  --thesis "GOR>45 alarm, oil cheap vs gold" \
  --invalidation "WTI<80 or GOR<40" --horizon "3m" --max-loss 2
```

Assets: `oil`, `gold`, `a_shares`, `copper`, `cash`.

## Rules
1. Plan completeness (thesis / invalidation / horizon / max-loss) for adds.
2. Max loss ≤2%; single add ≤5%.
3. Data freshness (card ≤2 days).
4. Zone cap from `config.BASE_ALLOCATION`; per-asset caps; cash floor 20%.
5. VIX ≥25 blocks adds; ≥22.5 warns.
6. HY ≥400bp or CCC ≥1500bp blocks adds.
7. Oil add with GOR(WTI) ≥45: red screener blocks, yellow warns.
8. Portfolio drawdown ≤−10% blocks adds.
9. DXY/10Y framework alerts are advisory warnings.
10. `--override "reason"` downgrades blocks to warnings and records the reason.

## Contract
Read-only, offline. It never places orders or changes weights.
