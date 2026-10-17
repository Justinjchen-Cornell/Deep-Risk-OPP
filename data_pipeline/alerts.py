# -*- coding: utf-8 -*-
"""Alert state engine (v3.0 MVP) — state-diff, dry-run friendly.

Design: docs/v3.0-alerting-design.md
Rule: alerts fire on STATE TRANSITIONS, never on every price tick.
No delivery here; scripts/alert_check.py handles CLI + optional persistence.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

CONTRACT_BASE = 69.87
CONTRACT_TARGET = 107.60
CONTRACT_REQUIRED = CONTRACT_TARGET / CONTRACT_BASE - 1.0
HARD_STOP_MA = 60
HARD_STOP_MULT = 0.85
HARD_STOP_FLOOR = 60.0
GOR_WATCH_LEVELS = (42.0, 40.0, 38.0)


def _num(x):
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _price(card, key):
    return _num(((card.get("data") or {}).get(key) or {}).get("price"))


def hard_stop_threshold(history):
    if not history:
        return None
    vals = [r.get("wti") for r in history if isinstance(r.get("wti"), (int, float))]
    if len(vals) < HARD_STOP_MA:
        return None
    sma = sum(vals[-HARD_STOP_MA:]) / HARD_STOP_MA
    return round(sma * HARD_STOP_MULT, 2)


def build_state(card, history=None):
    s = card.get("screener") or {}
    wti = _price(card, "WTI原油") or _num(s.get("oil"))
    gold = _price(card, "黄金期货")
    thr = hard_stop_threshold(history)
    hs = False
    if wti is not None and thr is not None:
        hs = bool(wti < thr or wti < HARD_STOP_FLOOR)
    completion = None
    if wti is not None:
        completion = round((wti / CONTRACT_BASE - 1.0) / CONTRACT_REQUIRED, 3)
    return {
        "updated": card.get("updated"),
        "regime": card.get("regime"),
        "position": _num(card.get("final_position")),
        "verdict": s.get("verdict"),
        "npass": s.get("npass"),
        "vix": _num(s.get("vix")),
        "vix_thr": _num(s.get("vix_thr")),
        "oil_pctl": _num(s.get("oil_pctl")),
        "s2": s.get("s2"),
        "s3": s.get("s3"),
        "gor_wti": _num(card.get("gor_wti")),
        "gor_brent": _num(card.get("gor_brent")),
        "wti": wti,
        "gold": gold,
        "hard_stop": hs,
        "hard_stop_thr": thr,
        "contract_completion": completion,
        "contract_target_hit": bool(wti is not None and wti >= CONTRACT_TARGET),
        "source": card.get("_source", "daily-card"),
        "quote_time": card.get("updated"),
        "mode": card.get("_mode", "daily"),
    }


def _severity(rule):
    if rule in ("hard_stop", "capitulation", "data_failure"):
        return "P0"
    if rule in ("regime_change", "position_change", "verdict_change",
                "contract_target", "contract_90", "contract_100"):
        return "P1"
    if rule.startswith("gor_"):
        return "P2"
    return "P3"


def _alert(rule, now, title, message, curr, prev):
    return {
        "id": now.strftime('%Y-%m-%dT%H:%MZ') + "-" + rule,
        "rule": rule,
        "severity": _severity(rule),
        "title": title,
        "message": message,
        "created": now.isoformat(),
        "current": {k: curr.get(k) for k in
                    ("regime", "position", "verdict", "gor_wti", "gor_brent",
                     "wti", "vix", "oil_pctl", "hard_stop", "contract_completion")},
        "previous": {k: prev.get(k) for k in
                     ("regime", "position", "verdict", "gor_wti", "gor_brent",
                      "wti", "vix", "oil_pctl", "hard_stop", "contract_completion")},
    }


def evaluate(prev, curr, now=None, intraday=False):
    """Return alerts for state transitions. First run (prev=None) is a baseline: no alerts."""
    if prev is None:
        return []
    if now is None:
        now = datetime.now(timezone.utc)
    out = []

    if curr.get("hard_stop") and not prev.get("hard_stop"):
        out.append(_alert(
            "hard_stop", now, "硬止损触发",
            "WTI $" + str(curr.get("wti")) + " < 阈值 $" + str(curr.get("hard_stop_thr")) +
            "（60日均线×0.85 或绝对底 $60）— 油气仓位应降至 5%。",
            curr, prev))

    cap_prev = bool(prev.get("s2") and prev.get("s3"))
    cap_curr = bool(curr.get("s2") and curr.get("s3"))
    if cap_curr and not cap_prev:
        out.append(_alert(
            "capitulation", now, "投降签名打印",
            "VIX " + str(curr.get("vix")) + " ≥ 门槛 " + str(curr.get("vix_thr")) +
            "，且油分位 " + str(curr.get("oil_pctl")) + " ≤ 0.25 — 机器扳机成立。",
            curr, prev))

    if curr.get("contract_target_hit") and not prev.get("contract_target_hit"):
        out.append(_alert(
            "contract_target", now, "合同目标触及",
            "WTI $" + str(curr.get("wti")) + " ≥ $107.60 — 公开证伪合同达成。",
            curr, prev))
    c_prev, c_curr = prev.get("contract_completion"), curr.get("contract_completion")
    if isinstance(c_prev, (int, float)) and isinstance(c_curr, (int, float)):
        for lvl in (0.90, 1.00):
            if c_prev < lvl <= c_curr:
                rule = "contract_90" if lvl == 0.90 else "contract_100"
                out.append(_alert(
                    rule, now, "合同完成度 ≥ " + str(int(lvl * 100)) + "%",
                    "完成度 " + f"{c_prev:.1%}" + " → " + f"{c_curr:.1%}" +
                    "（WTI $" + str(curr.get("wti")) + "）。",
                    curr, prev))

    if intraday:
        return out

    if curr.get("regime") != prev.get("regime"):
        out.append(_alert(
            "regime_change", now, "GOR 区间切换",
            str(prev.get("regime")) + " → " + str(curr.get("regime")) +
            "（GOR " + str(prev.get("gor_wti")) + " → " + str(curr.get("gor_wti")) + "）。",
            curr, prev))
    p0, p1 = prev.get("position"), curr.get("position")
    if isinstance(p0, (int, float)) and isinstance(p1, (int, float)) and abs(p1 - p0) >= 10:
        out.append(_alert(
            "position_change", now, "仓位变化 ≥10pt",
            "仓位 " + f"{p0:.0f}%" + " → " + f"{p1:.0f}%" + "。", curr, prev))
    if curr.get("verdict") != prev.get("verdict") and prev.get("verdict") and curr.get("verdict"):
        out.append(_alert(
            "verdict_change", now, "筛选器裁决变化",
            str(prev.get("verdict")) + " → " + str(curr.get("verdict")) +
            "（npass " + str(prev.get("npass")) + " → " + str(curr.get("npass")) + "）。",
            curr, prev))

    a, b = prev.get("gor_wti"), curr.get("gor_wti")
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        for lvl in GOR_WATCH_LEVELS:
            if a > lvl >= b:
                out.append(_alert(
                    "gor_below_" + str(int(lvl)), now, "GOR 跌破 " + f"{lvl:g}",
                    "GOR(WTI) " + str(a) + " → " + str(b) + "。", curr, prev))
            elif a < lvl <= b:
                out.append(_alert(
                    "gor_above_" + str(int(lvl)), now, "GOR 升破 " + f"{lvl:g}",
                    "GOR(WTI) " + str(a) + " → " + str(b) + "。", curr, prev))
    return out


def load_state(path):
    p = Path(path)
    if not p.exists():
        return None
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(obj, dict) and isinstance(obj.get("state"), dict):
        return obj["state"]
    return obj if isinstance(obj, dict) else None


def save_state(path, state):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"saved": datetime.now(timezone.utc).isoformat(),
                             "state": state}, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(path, alerts):
    if not alerts:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        for a in alerts:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")
