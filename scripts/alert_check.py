#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3.0 alert check — dry-run by default; --intraday adds Yahoo quotes; --send delivers.

Usage:
  python scripts/alert_check.py                          # dry-run, daily card
  python scripts/alert_check.py --intraday               # dry-run, intraday quotes
  python scripts/alert_check.py --intraday --send --write # production (CI)
  python scripts/alert_check.py --json                   # machine-readable
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.alerts import (build_state, evaluate, load_state, save_state,
                                  append_log)
from data_pipeline.delivery import configured_channels, send_alert, has_any_success
from data_pipeline.quotes import fetch_quotes, provisional_card, quote_age_minutes

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CARD = os.path.join(BASE, "gor_latest.json")
DEFAULT_HISTORY = os.path.join(BASE, "wti_history.json")
DEFAULT_STATE = os.path.join(BASE, "alerts", "state.json")
DEFAULT_LOG = os.path.join(BASE, "alerts", "log.jsonl")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description="Deep-Risk-OPP v3.0 alert check")
    ap.add_argument("--card", default=DEFAULT_CARD)
    ap.add_argument("--history", default=DEFAULT_HISTORY)
    ap.add_argument("--state", default=DEFAULT_STATE)
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--intraday", action="store_true", help="fetch Yahoo intraday quotes")
    ap.add_argument("--send", action="store_true", help="deliver alerts to configured channels")
    ap.add_argument("--write", action="store_true", help="persist state/log on baseline or alerts")
    ap.add_argument("--json", action="store_true", help="print JSON only")
    ap.add_argument("--max-quote-age", type=float, default=45.0,
                    help="suppress intraday alerts if the WTI quote is older than N minutes")
    args = ap.parse_args()

    card = load_json(args.card)
    history = load_json(args.history) if os.path.exists(args.history) else None

    if args.intraday:
        try:
            quotes = fetch_quotes()
        except Exception as e:
            print("intraday quote fetch failed: " + str(e))
            sys.exit(1)
        age = quote_age_minutes(quotes.get("wti"))
        if age is not None and age > args.max_quote_age:
            print("stale quote: WTI is %.0f min old (> %.0f) — suppressing alerts" %
                  (age, args.max_quote_age))
            sys.exit(0)
        card = provisional_card(card, quotes)

    curr = build_state(card, history)
    prev_raw = load_state(args.state)
    mode_switch = bool(prev_raw and prev_raw.get("mode") != curr.get("mode"))
    prev = None if mode_switch else prev_raw
    alerts = evaluate(prev, curr, now=datetime.now(timezone.utc),
                      intraday=args.intraday)

    delivery = {}
    if args.send and alerts:
        channels = configured_channels()
        if not channels:
            print("send: no channels configured — alert not delivered")
            print("      set FEISHU_WEBHOOK / TELEGRAM_* / DINGTALK_WEBHOOK / SERVERCHAN_SENDKEY")
            sys.exit(1)
        for a in alerts:
            res = send_alert(a)
            a["delivery"] = res
            delivery[a["id"]] = res
            print("send " + a["id"] + ": " + json.dumps(res, ensure_ascii=False))
        if channels and not any(has_any_success(r) for r in delivery.values()):
            print("send: all configured channels failed")
            sys.exit(1)

    if args.json:
        print(json.dumps({"state": curr, "alerts": alerts, "delivery": delivery,
                          "baseline": prev is None}, ensure_ascii=False, indent=2))
    else:
        print("state: regime=%s position=%s verdict=%s gor=%s wti=%s hard_stop=%s completion=%s"
              % (curr["regime"], curr["position"], curr["verdict"], curr["gor_wti"],
                 curr["wti"], curr["hard_stop"], curr["contract_completion"]))
        print("source=%s quote_time=%s" % (curr.get("source"), curr.get("quote_time")))
        if mode_switch:
            print("baseline: mode switch (%s → %s) — rebaselined" %
                  (prev_raw.get("mode"), curr.get("mode")))
        elif prev is None:
            print("baseline: no previous state — no alerts (first run)")
        elif not alerts:
            print("no state transitions — silent")
        else:
            for a in alerts:
                print("[%s] %s · %s" % (a["severity"], a["rule"], a["title"]))
                print("      " + a["message"])
                print("      id=" + a["id"])

    if args.write and (prev_raw is None or mode_switch or alerts):
        save_state(args.state, curr)
        append_log(args.log, alerts)
        if not args.json:
            print("wrote state: " + args.state)
            if alerts:
                print("appended %d alert(s): %s" % (len(alerts), args.log))


if __name__ == "__main__":
    main()
