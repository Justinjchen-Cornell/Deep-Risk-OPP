#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update the public model portfolio (paper) from the daily card — v2.

Method
------
- Fixed base NAV 100; weights from the public card allocation.
- Daily returns: oil = WTI (CL=F), gold = GC=F, A-shares = ASHR (CSI 300
  A-share ETF, USD), copper = HG=F. Cash earns 0.
- Benchmarks: SPY and 60/40 = 60% SPY + 40% AGG (daily constant mix,
  frictionless — documented, not hidden).
- Costs: cost_bps per side on one-way turnover at rebalance; a one-time
  inception cost is charged on the invested share. No tax, no leverage.
- History is keyed by Beijing date; same-day reruns are idempotent.

This is a model portfolio, not a real account. No personal capital is disclosed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
PF = os.path.join(BASE, "model_portfolio.json")
CARD = os.path.join(BASE, "gor_latest.json")
DEFAULT_COST_BPS = 5.0

# portfolio label -> (price key, Yahoo symbol)
ASSETS = {
    "油气": ("wti", "CL=F"),
    "黄金": ("gold", "GC=F"),
    "A股": ("ashare", "ASHR"),
    "铜": ("copper", "HG=F"),
}
BENCH = {"spy": "SPY", "agg": "AGG"}
CARD_PRICE_KEYS = {"wti": "WTI原油", "gold": "黄金期货", "copper": "COMEX铜"}
WEIGHT_KEYS = ("油气", "黄金", "现金", "A股", "铜")


def bj_today():
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _price(prices, key):
    """Accept {'key': {'price': x}} or {'key': x}; return float or None."""
    q = (prices or {}).get(key)
    if q is None:
        return None
    if isinstance(q, dict):
        q = q.get("price")
    try:
        return float(q)
    except (TypeError, ValueError):
        return None


def fetch_prices():
    """Fetch all portfolio/benchmark prices from Yahoo chart API.

    Returns {'wti': {'price':..., 'time':..., 'source':'yahoo', 'symbol':'CL=F'}, ...}.
    Missing symbols are simply absent; callers fall back to the card / last price.
    """
    from data_pipeline.quotes import _yahoo

    symbols = {key: sym for key, sym in ASSETS.values()}
    symbols.update(BENCH)
    out = {}
    for key, sym in symbols.items():
        for attempt in (1, 2):
            try:
                q = _yahoo(sym)
                out[key] = {"price": float(q["price"]), "time": q.get("time"),
                            "source": "yahoo", "symbol": sym}
                break
            except Exception as e:
                if attempt == 2:
                    print("  price %-6s %-6s MISSING (%s)" % (key, sym, str(e)[:80]))
                else:
                    time.sleep(1)
        time.sleep(0.15)
    return out


def _upsert_history(pf, row):
    hist = pf.setdefault("history", [])
    idx = next((i for i, h in enumerate(hist) if h.get("date") == row["date"]), None)
    if idx is None:
        hist.append(row)
        hist.sort(key=lambda h: h.get("date", ""))
        return True
    old = hist[idx]
    changed = any(old.get(k) != row.get(k) for k in row)
    old.update(row)
    hist.sort(key=lambda h: h.get("date", ""))
    return changed


def run(pf, card, prices, today, cost_bps=DEFAULT_COST_BPS):
    """Advance the portfolio one Beijing date. Mutates pf; returns (changed, notes)."""
    d = card.get("data") or {}
    alloc = card.get("allocation") or {}

    old_weights = {k: float(v) for k, v in (pf.get("weights") or {}).items()}
    weights = {}
    for k in WEIGHT_KEYS:
        if k in alloc:
            weights[k] = float(alloc.get(k) or 0)
        elif k in old_weights:
            weights[k] = float(old_weights[k])
        else:
            weights[k] = 0.0
    if not old_weights:
        old_weights = dict(weights)

    last = (pf.get("history") or [{}])[-1]
    same_day = last.get("date") == today
    last_prices = pf.setdefault("last_prices", {})
    nav = float(pf.get("nav") or pf.get("base_nav") or 100.0)

    bench = pf.setdefault("benchmarks", {})
    spy = bench.setdefault("spy", {"nav": 100.0, "start": today})
    b6040 = bench.setdefault("6040", {"nav": 100.0, "start": today,
                                      "mix": "60% SPY + 40% AGG"})
    notes = []
    changed = False
    first_run = not pf.get("inception_cost_paid")

    if not same_day:
        rets = {}
        for name, (key, _sym) in ASSETS.items():
            p, prev = _price(prices, key), last_prices.get(key)
            rets[name] = (p / prev - 1.0) if (p is not None and prev) else 0.0
        day_ret = sum(old_weights.get(name, 0.0) / 100.0 * rets[name] for name in ASSETS)
        nav *= 1.0 + day_ret
        notes.append("ret %+.3f%% (oil %+.2f%% / gold %+.2f%% / A %+.2f%% / copper %+.2f%%)" % (
            day_ret * 100, rets["油气"] * 100, rets["黄金"] * 100,
            rets["A股"] * 100, rets["铜"] * 100))

        spy_p, agg_p = _price(prices, "spy"), _price(prices, "agg")
        r_spy = (spy_p / spy["last_price"] - 1.0) if (spy_p is not None and spy.get("last_price")) else 0.0
        r_agg = (agg_p / b6040["last_price_agg"] - 1.0) if (agg_p is not None and b6040.get("last_price_agg")) else 0.0
        r_6040 = 0.6 * r_spy + 0.4 * r_agg
        spy["nav"] = float(spy.get("nav", 100.0)) * (1.0 + r_spy)
        b6040["nav"] = float(b6040.get("nav", 100.0)) * (1.0 + r_6040)
        notes.append("bench SPY %+.2f%% / 60-40 %+.2f%%" % (r_spy * 100, r_6040 * 100))
    else:
        notes.append("init" if first_run else "same-day rerun")

    # Mark prices to market. Commodity legs use the public card close (the
    # published mark); A-shares/benchmarks use Yahoo. Fallback across both.
    for key, card_key in CARD_PRICE_KEYS.items():
        p = (d.get(card_key) or {}).get("price")
        if p is None:
            p = _price(prices, key)
        if p is not None:
            last_prices[key] = float(p)
    for key in ("ashare", "spy", "agg"):
        p = _price(prices, key)
        if p is not None:
            last_prices[key] = float(p)
    if _price(prices, "spy") is not None:
        spy["last_price"] = _price(prices, "spy")
        b6040["last_price_spy"] = _price(prices, "spy")
    if _price(prices, "agg") is not None:
        b6040["last_price_agg"] = _price(prices, "agg")

    # Rebalance only on a new date; card weights are targets, not daily drift.
    diff = max([abs(weights.get(k, 0.0) - old_weights.get(k, 0.0))
                for k in set(weights) | set(old_weights)] or [0.0])
    turnover = sum(abs(weights.get(k, 0.0) - old_weights.get(k, 0.0))
                   for k in set(weights) | set(old_weights)) / 2.0 / 100.0
    if not same_day and diff >= 1.0:
        cost = nav * turnover * cost_bps / 10000.0
        nav -= cost
        pf["costs_paid"] = round(float(pf.get("costs_paid") or 0.0) + cost, 6)
        pf.setdefault("trades", []).append({
            "date": today,
            "action": "rebalance",
            "nav": round(nav, 4),
            "turnover_pct": round(turnover * 100, 2),
            "cost": round(cost, 4),
            "cost_bps": cost_bps,
            "note": "weights %s -> %s; turnover %.1f%%; cost %.4f" % (
                old_weights, weights, turnover * 100, cost),
        })
        pf["weights"] = dict(weights)
        changed = True
        notes.append("rebalance turnover %.1f%% cost %.4f" % (turnover * 100, cost))

    # One-time entry cost: buying the initial allocation from cash.
    if not pf.get("inception_cost_paid"):
        invested = sum(max(0.0, weights.get(k, 0.0)) for k in ASSETS) / 100.0
        cost = nav * invested * cost_bps / 10000.0
        nav -= cost
        pf["costs_paid"] = round(float(pf.get("costs_paid") or 0.0) + cost, 6)
        pf["inception_cost_paid"] = True
        pf.setdefault("trades", []).append({
            "date": today,
            "action": "inception",
            "nav": round(nav, 4),
            "turnover_pct": round(invested * 100, 2),
            "cost": round(cost, 4),
            "cost_bps": cost_bps,
            "note": "initial allocation: %.0f%% invested x %.0f bps" % (invested * 100, cost_bps),
        })
        changed = True
        notes.append("inception cost %.4f" % cost)

    row = {
        "date": today,
        "nav": round(nav, 4),
        "bench_spy": round(float(spy.get("nav", 100.0)), 4),
        "bench_6040": round(float(b6040.get("nav", 100.0)), 4),
        "note": "; ".join(notes),
    }
    changed = _upsert_history(pf, row) or changed

    pf["nav"] = round(nav, 4)
    pf["weights"] = {k: weights.get(k, 0.0) for k in WEIGHT_KEYS}
    pf["benchmark"] = "SPY / 60-40（60% SPY + 40% AGG，每日再平衡、不计成本）"
    pf["cost_bps"] = cost_bps
    pf["updated"] = today
    pf["history"] = pf["history"][-500:]
    pf["data_sources"] = {
        "油气": "卡片 WTI 收盘（Yahoo CL=F 兜底）",
        "黄金": "卡片黄金期货收盘（Yahoo GC=F 兜底）",
        "A股": "Yahoo ASHR（CSI 300 A 股 ETF，美元计价）",
        "铜": "卡片 COMEX 铜收盘（Yahoo HG=F 兜底）",
        "现金": "0% 收益",
        "SPY": "Yahoo SPY",
        "60-40": "60% SPY + 40% AGG，每日常数混合",
        "cost": "%g bps/边，再平衡与建仓时计入" % cost_bps,
    }
    pf["notes"] = [
        "油/金/铜用公开卡片的收盘价；A股用 ASHR（CSI 300 A 股 ETF，美元计价）；现金 0% 收益。",
        "基准：SPY；60-40 = 60% SPY + 40% AGG（每日再平衡、不计成本）。",
        "成本 %g bps/边，按单边换手在再平衡与建仓时计入；不计税、不加杠杆。" % cost_bps,
        "这是模型组合，不是真实账户；不公开任何个人资金规模。",
    ]
    return changed, notes


def main(argv=None):
    ap = argparse.ArgumentParser(description="Update the Deep-Risk-OPP paper model portfolio")
    ap.add_argument("--pf", default=PF)
    ap.add_argument("--card", default=CARD)
    ap.add_argument("--cost-bps", type=float, default=DEFAULT_COST_BPS)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    pf = _load(args.pf)
    card = _load(args.card)
    prices = fetch_prices()
    changed, notes = run(pf, card, prices, bj_today(), args.cost_bps)

    print("model portfolio %s · NAV %.4f · SPY %.2f · 60-40 %.2f" % (
        bj_today(), pf["nav"], pf["benchmarks"]["spy"]["nav"],
        pf["benchmarks"]["6040"]["nav"]))
    for n in notes:
        print("  " + n)
    if changed and not args.dry_run:
        with open(args.pf, "w", encoding="utf-8") as f:
            json.dump(pf, f, ensure_ascii=False, indent=1)
        print("  saved:", args.pf)
    elif not changed:
        print("  unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
