# alerts/

Public audit trail for v3.0 alerting.

- `state_daily.json` — last daily-close state (regime/position/verdict P1)
- `state_intraday.json` — last intraday state (P0/contract only)
- `log.jsonl` — append-only alert log (one JSON object per line; includes delivery status)
- `digest_state.json` — last 08:30 digest timestamp

Design: [`docs/v3.0-alerting-design.md`](../docs/v3.0-alerting-design.md)
No secrets here. Channel credentials live in GitHub Actions Secrets only.
