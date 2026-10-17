# -*- coding: utf-8 -*-
"""Daily card history + change log (public audit trail).

history.json        — daily snapshots (upsert by Beijing date)
history_changes.jsonl — append-only change records (only changed fields)
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY = os.path.join(BASE, "history.json")
CHANGES = os.path.join(BASE, "history_changes.jsonl")
WEEKLY = os.path.join(BASE, "history_weekly.json")
WEEKLY_CHANGES = os.path.join(BASE, "weekly_changes.jsonl")
FIELDS = ("gor_wti", "gor_brent", "gold", "wti", "brent", "vix", "dxy",
          "us10y", "position", "regime", "verdict", "contract_completion")


def _bj_now():
    return datetime.now(timezone(timedelta(hours=8)))


def _load():
    try:
        with open(HISTORY, encoding="utf-8") as f:
            obj = json.load(f)
        return obj.get("rows", []) if isinstance(obj, dict) else []
    except Exception:
        return []


def week_key(date_str):
    try:
        y, m, d = [int(x) for x in date_str.split("-")]
        iso = datetime(y, m, d).isocalendar()
        return str(iso[0]) + "-W" + str(iso[1]).zfill(2)
    except Exception:
        return date_str


def _load_weekly():
    try:
        with open(WEEKLY, encoding="utf-8") as f:
            obj = json.load(f)
        return obj.get("rows", []) if isinstance(obj, dict) else []
    except Exception:
        return []


def _save_weekly(rows):
    rows = rows[-260:]
    with open(WEEKLY, "w", encoding="utf-8") as f:
        json.dump({"updated": _bj_now().strftime("%Y-%m-%d %H:%M"), "rows": rows},
                  f, ensure_ascii=False, indent=1)


def _save(rows):
    rows = rows[-1000:]
    with open(HISTORY, "w", encoding="utf-8") as f:
        json.dump({"updated": _bj_now().strftime("%Y-%m-%d %H:%M"), "rows": rows},
                  f, ensure_ascii=False, indent=1)


def _row_from_output(gor_output, cf_output=None):
    d = gor_output.get("data") or {}
    def price(k):
        return ((d.get(k) or {}).get("price"))
    wti = price("WTI原油")
    comp = None
    if isinstance(wti, (int, float)):
        comp = round((wti / 69.87 - 1) / (107.60 / 69.87 - 1), 3)
    s = gor_output.get("screener") or {}
    c = gor_output.get("capital_three_flows") or {}
    return {
        "date": _bj_now().strftime("%Y-%m-%d"),
        "time": _bj_now().strftime("%H:%M"),
        "gor_wti": gor_output.get("gor_wti"),
        "gor_brent": gor_output.get("gor_brent"),
        "gold": price("黄金期货"),
        "wti": wti,
        "brent": price("布伦特原油"),
        "vix": price("VIX恐慌指数"),
        "dxy": price("美元指数DXY"),
        "us10y": price("10Y美债收益率"),
        "position": gor_output.get("final_position"),
        "regime": gor_output.get("regime"),
        "verdict": s.get("verdict"),
        "contract_completion": comp,
        "flow": {"total": c.get("total"), "direction": c.get("direction"), "speed": c.get("speed")},
        "source": "daily",
    }


def record(gor_output, cf_output=None):
    rows = _load()
    row = _row_from_output(gor_output, cf_output)
    today = row["date"]
    prev = None
    for r in reversed(rows):
        if r.get("date") != today:
            prev = r
            break
    old_today = None
    for r in rows:
        if r.get("date") == today:
            old_today = r
            break
    base = old_today or prev or {}
    changes = {}
    for k in FIELDS:
        a, b = base.get(k), row.get(k)
        if a != b:
            changes[k] = {"from": a, "to": b}
    if old_today:
        rows = [r for r in rows if r.get("date") != today]
    rows.append(row)
    rows.sort(key=lambda r: r.get("date", ""))
    _save(rows)
    if changes:
        rec = {"ts": _bj_now().strftime("%Y-%m-%d %H:%M"), "date": today,
               "source": "daily", "changes": changes}
        with open(CHANGES, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return row, changes
