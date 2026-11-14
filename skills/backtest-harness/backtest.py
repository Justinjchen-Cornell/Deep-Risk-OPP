#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Toy GOR-zone backtest harness.

Tests a simple gold/oil/cash allocation rule on history.json:
  GOR >=45: oil 38 / gold 10 / cash 52
  30-45:    oil 20 / gold 15 / cash 65
  20-30:    oil 0  / gold 15 / cash 85
  <20:      oil 0  / gold 7  / cash 93
Screener RED at GOR>=45 zeroes the oil leg; YELLOW halves it.
Rebalance every N rows or on zone change; costs in bps.

This is a *toy*: ~5 months of daily data, no A-shares/copper, cash return 0.
Use it to sanity-check rules, not to claim a validated edge.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ZONES = [(45, "extreme"), (30, "recovery"), (20, "fair"), (0, "bubble")]
BASE = {
    "extreme": {"oil": 0.38, "gold": 0.10, "cash": 0.52},
    "recovery": {"oil": 0.20, "gold": 0.15, "cash": 0.65},
    "fair": {"oil": 0.00, "gold": 0.15, "cash": 0.85},
    "bubble": {"oil": 0.00, "gold": 0.07, "cash": 0.93},
}


def zone_of(gor):
    for threshold, name in ZONES:
        if gor >= threshold:
            return name
    return "bubble"


def target_weights(row):
    z = zone_of(float(row.get("gor_brent") or row.get("gor_wti") or 0))
    w = dict(BASE[z])
    v = row.get("verdict")
    if z == "extreme" and v == "红":
        w["cash"] += w["oil"]; w["oil"] = 0.0
    elif z == "extreme" and v == "黄":
        half = w["oil"] / 2; w["oil"] -= half; w["cash"] += half
    return w


def metrics(equity: pd.Series):
    if len(equity) < 3:
        return {}
    ret = equity.pct_change().dropna()
    total = equity.iloc[-1] / equity.iloc[0] - 1
    vol = ret.std() * np.sqrt(252)
    sharpe = (ret.mean() / ret.std() * np.sqrt(252)) if ret.std() else 0
    dd = (equity / equity.cummax() - 1).min()
    return {"total_return_pct": round(total * 100, 2), "ann_vol_pct": round(vol * 100, 2),
            "sharpe": round(float(sharpe), 2), "max_drawdown_pct": round(float(dd) * 100, 2),
            "days": len(ret)}


def run(df, rebalance_days=5, cost_bps=10.0):
    rets = df[["gold", "wti"]].pct_change().fillna(0.0)
    equity = [1.0]; bench_gold = [1.0]; bench_oil = [1.0]; bench_6040 = [1.0]
    w = {"oil": 0.0, "gold": 0.0, "cash": 1.0}
    last_zone = None; turnover = 0.0
    for i in range(1, len(df)):
        row = df.iloc[i]
        new_w = target_weights(row)
        zone = zone_of(float(row.get("gor_brent") or row.get("gor_wti") or 0))
        rebal = (i % rebalance_days == 0) or (zone != last_zone)
        if rebal:
            delta = sum(abs(new_w[k] - w[k]) for k in ("oil", "gold", "cash"))
            turnover += delta
            equity[-1] *= (1 - delta * cost_bps / 10000.0)
            w = new_w; last_zone = zone
        pr = w["oil"] * rets["wti"].iloc[i] + w["gold"] * rets["gold"].iloc[i]
        equity.append(equity[-1] * (1 + pr))
        bench_gold.append(bench_gold[-1] * (1 + rets["gold"].iloc[i]))
        bench_oil.append(bench_oil[-1] * (1 + rets["wti"].iloc[i]))
        bench_6040.append(bench_6040[-1] * (1 + 0.6 * rets["gold"].iloc[i] + 0.4 * rets["wti"].iloc[i]))
    return {"strategy": pd.Series(equity), "gold": pd.Series(bench_gold),
            "oil": pd.Series(bench_oil), "60_40": pd.Series(bench_6040),
            "turnover": turnover}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Toy GOR-zone backtest")
    ap.add_argument("--rebalance-days", type=int, default=5)
    ap.add_argument("--cost-bps", type=float, default=10.0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = json.loads((ROOT / "history.json").read_text(encoding="utf-8"))["rows"]
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["gold"] = pd.to_numeric(df["gold"], errors="coerce")
    df["wti"] = pd.to_numeric(df["wti"], errors="coerce")
    df = df.dropna(subset=["gold", "wti"]).reset_index(drop=True)
    if len(df) < 30:
        print("not enough data"); return 1

    split = int(len(df) * 0.7)
    full = run(df, a.rebalance_days, a.cost_bps)
    ins = run(df.iloc[:split].reset_index(drop=True), a.rebalance_days, a.cost_bps)
    oos = run(df.iloc[split:].reset_index(drop=True), a.rebalance_days, a.cost_bps)
    out = {
        "warning": "toy backtest; ~5 months, no A-shares/copper, cash return 0",
        "window": {"start": str(df["date"].iloc[0].date()), "end": str(df["date"].iloc[-1].date()), "rows": len(df)},
        "params": {"rebalance_days": a.rebalance_days, "cost_bps": a.cost_bps},
        "full": {k: metrics(v) for k, v in full.items() if isinstance(v, pd.Series)},
        "in_sample": {k: metrics(v) for k, v in ins.items() if isinstance(v, pd.Series)},
        "out_of_sample": {k: metrics(v) for k, v in oos.items() if isinstance(v, pd.Series)},
        "turnover": {"full": round(full["turnover"], 2), "in_sample": round(ins["turnover"], 2), "out_of_sample": round(oos["turnover"], 2)},
    }
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print(f"Toy GOR-zone backtest | {out['window']['start']} -> {out['window']['end']} ({len(df)} rows)")
        print(f"cost={a.cost_bps}bps rebalance={a.rebalance_days}d\n")
        print(f"{'series':12} {'full':>10} {'IS':>10} {'OOS':>10} {'maxDD':>8} {'sharpe':>7}")
        for k in ("strategy", "gold", "oil", "60_40"):
            f = out["full"].get(k, {}); i = out["in_sample"].get(k, {}); o = out["out_of_sample"].get(k, {})
            print(f"{k:12} {f.get('total_return_pct', 0):>9.1f}% {i.get('total_return_pct', 0):>9.1f}% {o.get('total_return_pct', 0):>9.1f}% {f.get('max_drawdown_pct', 0):>7.1f}% {f.get('sharpe', 0):>7.2f}")
        print(f"\nturnover (x NAV): {out['turnover']['full']}")
        print("WARNING: toy backtest; not a validated edge.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
