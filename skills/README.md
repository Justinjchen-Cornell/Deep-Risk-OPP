# Deep-Risk-OPP · Skills Toolkit

Adapted from the MIT-licensed `tradermonty/claude-trading-skills` project.
Only the **discipline / quality / research** layers are vendored here; the
equity-screening and short-term trading skills are intentionally excluded.

## Skills

| Skill | Priority | What it does | Command |
|---|---|---|---|
| `data-quality-checker` | P0 | Validates card/history/portfolio/performance data before publishing | `python skills/data-quality-checker/dq_check.py` |
| `signal-postmortem` | P0 | Scores market signals at 5/20/60-day horizons; hit/miss/open | `python skills/signal-postmortem/postmortem.py` |
| `pre-trade-discipline-gate` | P0 | Blocks planless, oversized, stale-data or regime-blocked adds | `python skills/pre-trade-discipline-gate/gate.py --help` |
| `scenario-analyzer` | P1 | Builds an 18-month 1st/2nd/3rd-order scenario pack from a headline | `python skills/scenario-analyzer/scenario.py --headline "..."` |
| `backtest-harness` | P1 | Toy backtest of GOR-zone allocation with costs + walk-forward split | `python skills/backtest-harness/backtest.py` |

## Data contracts

- `gor_latest.json` — unchanged; these tools only read it.
- `signals_log.json` — new; append-only log of falsifiable market signals.
- No new runtime dependencies beyond the existing `pandas` / `numpy`.

## Attribution

Source: https://github.com/tradermonty/claude-trading-skills (MIT).
See `NOTICE-skills.md`.
