# alerts/

Public audit trail for v3.0 alerting.

- `state.json` — last evaluated state (updated only on baseline or state transition)
- `log.jsonl` — append-only alert log (one JSON object per line; includes delivery status)

Design: [`docs/v3.0-alerting-design.md`](../docs/v3.0-alerting-design.md)
No secrets here. Channel credentials live in GitHub Actions Secrets only.
