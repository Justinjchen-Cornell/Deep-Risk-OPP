---
name: signal-postmortem
description: Score falsifiable signals from signals_log.json against history.json and FRED credit caches. Returns hit/miss/open at 5/20/60-day horizons and a hit rate.
---

# Signal Postmortem

## When to use
- Weekly review; after a thesis reaches its horizon; before publishing a track-record update.
- After a public call, to mark it rather than defend it.

## Command
```bash
python skills/signal-postmortem/postmortem.py
python skills/signal-postmortem/postmortem.py --json
python skills/signal-postmortem/postmortem.py --update   # write status/evidence back
```

## Signal types
- `threshold`: metric crosses above/below a level within `horizon_days`.
- `contract`: metric reaches `target` before `deadline` (progress % reported).
- `direction`: metric moves in `expected` direction by `min_move_pct` within horizon.

Metrics: `wti`, `gold`, `brent`, `gor_wti`, `gor_brent`, `vix`, `dxy`, `us10y`,
`hy_oas`, `ccc_oas` (FRED, converted to bp).

## Contract
Append-only log. `--update` only writes status/last_eval/evidence; it never deletes signals.
