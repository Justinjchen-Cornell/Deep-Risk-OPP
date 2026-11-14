#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre-trade discipline gate (GOR edition).

Blocks planless, oversized, stale-data or regime-blocked adds.
Reads gor_latest.json, model_portfolio.json, history.json and FRED caches.
Never places orders.

Example:
  python skills/pre-trade-discipline-gate/gate.py --action add --asset oil --weight 5 \
    --thesis "GOR>45 alarm, oil cheap vs gold" --invalidation "WTI<80 or GOR<40" \
    --horizon "3m" --max-loss 2
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
try:
    import config
except Exception:
    config = None

ASSETS = {"oil": "油气", "gold": "黄金", "a_shares": "A股", "copper": "铜", "cash": "现金"}
CFG = {
    "asset_caps": {"oil": 30.0, "gold": 20.0, "a_shares": 20.0, "copper": 5.0, "cash": 100.0},
    "max_single_add": 5.0,
    "min_cash": 20.0,
    "max_loss_pct": 2.0,
    "vix_block": 25.0,
    "vix_warn": 22.5,
    "hy_block_bp": 400.0,
    "ccc_block_bp": 1500.0,
    "stale_days_block": 2,
    "drawdown_block_pct": 10.0,
    "dxy_warn": 99.0,
    "yield_warn": 4.3,
}
RULES = []


def rule(name, status, msg):
    RULES.append({"rule": name, "status": status, "message": msg})


def load_json(name, default=None):
    p = ROOT / name
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def card_price(card, key):
    try:
        return float(card["data"][key]["price"])
    except Exception:
        return None


def parse_dt(s):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(s)[:len(fmt) + 2], fmt)
        except ValueError:
            pass
    return None


def fred_bp(series):
    p = ROOT / "看板日志" / "cache" / f"fred_{series}.csv"
    try:
        lines = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        return float(lines[-1].split(",")[1]) * 100.0
    except Exception:
        return None


def zone_of(card):
    gor_b = card.get("gor_brent") or 0
    gor_w = card.get("gor_wti") or 0
    if config:
        zones = config.GOR_ZONES
        for name in ("extreme", "recovery", "fair_value", "oil_bubble"):
            z = zones.get(name) or {}
            if z.get("min", 0) <= gor_b < z.get("max", 999):
                return name
        for name in ("extreme", "recovery", "fair_value", "oil_bubble"):
            z = zones.get(name) or {}
            if z.get("min", 0) <= gor_w < z.get("max", 999):
                return name
    return "recovery"


def zone_cap(zone):
    if config:
        try:
            return float(config.BASE_ALLOCATION[zone]["total"])
        except Exception:
            pass
    return {"extreme": 70.0, "recovery": 50.0, "fair_value": 30.0, "oil_bubble": 10.0}.get(zone, 50.0)


def current_weights(mp, card):
    w = (mp or {}).get("weights") or (card or {}).get("allocation") or {}
    return {
        "oil": float(w.get("油气", 0) or 0),
        "gold": float(w.get("黄金", 0) or 0),
        "a_shares": float(w.get("A股", 0) or 0),
        "copper": float(w.get("铜", 0) or 0),
        "cash": float(w.get("现金", 0) or 0),
    }


def portfolio_drawdown(mp):
    hist = (mp or {}).get("history") or []
    navs = [float(h["nav"]) for h in hist if h.get("nav") is not None]
    if not navs:
        return 0.0
    peak = max(navs)
    return (navs[-1] / peak - 1.0) * 100.0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pre-trade discipline gate (GOR edition)")
    ap.add_argument("--action", choices=["add", "reduce", "set"], default="add")
    ap.add_argument("--asset", choices=list(ASSETS), required=True)
    ap.add_argument("--weight", type=float, required=True, help="percent of portfolio")
    ap.add_argument("--thesis")
    ap.add_argument("--invalidation")
    ap.add_argument("--horizon")
    ap.add_argument("--max-loss", type=float, dest="max_loss")
    ap.add_argument("--override", help="reason to downgrade blocks to warnings")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    RULES.clear()

    card = load_json("gor_latest.json", {}) or {}
    mp = load_json("model_portfolio.json", {}) or {}
    w = current_weights(mp, card)
    zone = zone_of(card)

    if a.weight <= 0:
        rule("weight_valid", "BLOCK", f"weight must be > 0 (got {a.weight})")

    # 1) plan completeness
    if a.action == "add":
        missing = [k for k, v in (("thesis", a.thesis), ("invalidation", a.invalidation),
                                  ("horizon", a.horizon), ("max_loss", a.max_loss)) if v in (None, "")]
        if missing:
            rule("plan_completeness", "BLOCK", "missing " + ", ".join(missing))
        else:
            rule("plan_completeness", "PASS", "thesis / invalidation / horizon / max-loss present")
        if a.max_loss is not None:
            if a.max_loss <= 0 or a.max_loss > CFG["max_loss_pct"]:
                rule("max_loss", "BLOCK", f"max_loss={a.max_loss}% outside (0,{CFG['max_loss_pct']}]")
            else:
                rule("max_loss", "PASS", f"max_loss={a.max_loss}%")
        if a.weight > CFG["max_single_add"]:
            rule("single_add", "BLOCK", f"single add {a.weight}% > {CFG['max_single_add']}%")
        else:
            rule("single_add", "PASS", f"single add {a.weight}% <= {CFG['max_single_add']}%")

    # 2) data freshness
    upd = parse_dt(card.get("updated"))
    age = (datetime.now() - upd).days if upd else 999
    if age > CFG["stale_days_block"]:
        rule("data_freshness", "BLOCK", f"card is {age} days old (max {CFG['stale_days_block']})")
    else:
        rule("data_freshness", "PASS", f"card age {age} day(s)")

    # 3) proposed weights
    post = dict(w)
    if a.action == "add":
        post[a.asset] = post.get(a.asset, 0) + a.weight
    elif a.action == "reduce":
        post[a.asset] = max(0.0, post.get(a.asset, 0) - a.weight)
    else:
        post[a.asset] = a.weight
    invested = sum(v for k, v in post.items() if k != "cash")
    cap = zone_cap(zone)
    if invested > cap + 1e-6:
        rule("zone_cap", "BLOCK", f"invested {invested:.1f}% > {zone} cap {cap:.0f}%")
    else:
        rule("zone_cap", "PASS", f"invested {invested:.1f}% <= {zone} cap {cap:.0f}%")

    acap = CFG["asset_caps"].get(a.asset, 100.0)
    if post.get(a.asset, 0) > acap:
        rule("asset_cap", "BLOCK", f"{a.asset} {post[a.asset]:.1f}% > cap {acap:.0f}%")
    else:
        rule("asset_cap", "PASS", f"{a.asset} {post[a.asset]:.1f}% <= cap {acap:.0f}%")

    if post.get("cash", 0) < CFG["min_cash"]:
        rule("cash_floor", "BLOCK", f"cash {post['cash']:.1f}% < floor {CFG['min_cash']:.0f}%")
    else:
        rule("cash_floor", "PASS", f"cash {post['cash']:.1f}% >= {CFG['min_cash']:.0f}%")

    # 4) volatility gate
    vix = card_price(card, "VIX恐慌指数")
    if vix is not None:
        if vix >= CFG["vix_block"] and a.action == "add":
            rule("vix_gate", "BLOCK", f"VIX {vix:.1f} >= {CFG['vix_block']} (panic)")
        elif vix >= CFG["vix_warn"]:
            rule("vix_gate", "WARN", f"VIX {vix:.1f} >= {CFG['vix_warn']}")
        else:
            rule("vix_gate", "PASS", f"VIX {vix:.1f}")

    # 5) credit gate
    hy = fred_bp("BAMLH0A0HYM2"); ccc = fred_bp("BAMLH0A3HYC")
    if a.action == "add":
        if hy is not None and hy >= CFG["hy_block_bp"]:
            rule("credit_gate", "BLOCK", f"HY OAS {hy:.0f}bp >= {CFG['hy_block_bp']:.0f}bp")
        elif ccc is not None and ccc >= CFG["ccc_block_bp"]:
            rule("credit_gate", "BLOCK", f"CCC OAS {ccc:.0f}bp >= {CFG['ccc_block_bp']:.0f}bp")
        else:
            rule("credit_gate", "PASS", f"HY {hy:.0f}bp / CCC {ccc:.0f}bp" if hy and ccc else "credit data unavailable")

    # 6) GOR oil gate
    if a.asset == "oil" and a.action == "add":
        gor = float(card.get("gor_wti") or 0)
        verdict = (card.get("screener") or {}).get("verdict")
        if gor >= 45:
            if verdict == "红":
                rule("gor_oil_gate", "BLOCK", f"GOR(WTI) {gor:.1f} >=45 with screener RED")
            elif verdict == "黄":
                rule("gor_oil_gate", "WARN", f"GOR(WTI) {gor:.1f} >=45 with screener YELLOW")
            else:
                rule("gor_oil_gate", "PASS", f"GOR(WTI) {gor:.1f} >=45 with screener GREEN")
        else:
            rule("gor_oil_gate", "PASS", f"GOR(WTI) {gor:.1f} <45")

    # 7) drawdown
    dd = portfolio_drawdown(mp)
    if dd <= -CFG["drawdown_block_pct"] and a.action == "add":
        rule("drawdown", "BLOCK", f"portfolio drawdown {dd:.1f}% <= -{CFG['drawdown_block_pct']:.0f}%")
    else:
        rule("drawdown", "PASS", f"portfolio drawdown {dd:.1f}%")

    # 8) macro alerts (advisory)
    dxy = card_price(card, "美元指数DXY"); y10 = card_price(card, "10Y美债收益率")
    if dxy is not None and dxy > CFG["dxy_warn"]:
        rule("dxy_alert", "WARN", f"DXY {dxy:.2f} > {CFG['dxy_warn']} (framework -10%)")
    if y10 is not None and y10 > CFG["yield_warn"]:
        rule("yield_alert", "WARN", f"10Y {y10:.2f}% > {CFG['yield_warn']}% (framework -10%)")

    blocks = [r for r in RULES if r["status"] == "BLOCK"]
    warns = [r for r in RULES if r["status"] == "WARN"]
    if blocks and a.override:
        for r in blocks:
            r["status"] = "WARN"; r["message"] += f" [override: {a.override}]"
        decision = "ALLOW_WITH_OVERRIDE"
    elif blocks:
        decision = "BLOCK"
    elif warns:
        decision = "ALLOW_WITH_WARNINGS"
    else:
        decision = "ALLOW"

    out = {"decision": decision, "action": a.action, "asset": a.asset, "weight": a.weight,
           "zone": zone, "zone_cap": cap, "weights_before": w, "weights_after": post,
           "rules": RULES}
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print(f"DECISION: {decision}")
        print(f"  {a.action} {a.asset} {a.weight:+.1f}% | zone={zone} cap={cap:.0f}% | invested {invested:.1f}%")
        for r in RULES:
            print(f"  [{r['status']}] {r['rule']}: {r['message']}")
    return 1 if decision == "BLOCK" else 0


if __name__ == "__main__":
    sys.exit(main())
