#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre-crisis watch — B/C-family indicators (daily, explanatory only).

Covers what the machine's A-family trigger (VIX P80 + oil P25) does not:
term premium / real rates / credit spreads / VIX term structure / FX funding /
haven failure / physical stress.

Usage:
  python scripts/precrisis_watch.py            # print
  python scripts/precrisis_watch.py --write    # write dated md + latest json

No channels, no position changes. See docs/v3.0-alerting-design.md §12.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE, ".env"))
from fredapi import Fred

OUT_DIR = os.path.join(BASE, "看板日志", "reports", "special")
CARD = os.path.join(BASE, "gor_latest.json")
HIST = os.path.join(BASE, "wti_history.json")
DIESEL = os.path.join(BASE, "看板日志", "cache", "eia", "柴油裂解价差.csv")

GREEN, AMBER, RED = "🟢", "🟠", "🔴"
PTS = {GREEN: 0, AMBER: 1, RED: 2}


def fred_series(fred, sid, start="2016-01-01"):
    s = fred.get_series(sid, observation_start=start).dropna()
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


def pct_rank(s, value):
    return float((s <= value).mean())


def chg(s, periods=20):
    if len(s) <= periods:
        return None
    return float(s.iloc[-1] - s.iloc[-periods - 1])


def chg_pct(s, periods=20):
    if len(s) <= periods or s.iloc[-periods - 1] == 0:
        return None
    return float(s.iloc[-1] / s.iloc[-periods - 1] - 1.0)


def edge(level, amber, red):
    if level >= red:
        return RED
    if level >= amber:
        return AMBER
    return GREEN


def classify_real(v, d):
    if v >= 2.8 and d is not None and d >= 0.20:
        return RED
    if v >= 2.7 or (d is not None and d >= 0.15):
        return AMBER
    return GREEN


def classify_hy(v, d, rank):
    if (d is not None and d >= 0.50) or rank >= 0.90:
        return RED
    if (d is not None and d >= 0.30) or rank >= 0.75:
        return AMBER
    return GREEN


def classify_nominal(v):
    return edge(v, 5.00, 5.25)


def classify_vix(v, rank, vix3m):
    if rank >= 0.80 or (vix3m is not None and v > vix3m):
        return RED
    if rank >= 0.60:
        return AMBER
    return GREEN


def classify_fx(krw, jpy):
    worst = max([x for x in (krw, jpy) if x is not None] or [0.0])
    if worst >= 0.03:
        return RED
    if worst >= 0.015:
        return AMBER
    return GREEN


def classify_haven(corr, spx_ret):
    if corr is None or spx_ret is None:
        return AMBER
    if corr >= 0.30 and spx_ret <= -0.03:
        return RED
    if corr >= 0.15 and spx_ret <= -0.01:
        return AMBER
    return GREEN


def classify_physical(crack, chg20, sigma20, stale_days):
    if stale_days is not None and stale_days > 14:
        return AMBER
    if chg20 is None or sigma20 in (None, 0):
        return AMBER
    if chg20 >= 2 * sigma20:
        return RED if stale_days <= 7 else AMBER
    if chg20 >= sigma20:
        return AMBER
    return GREEN


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description="Pre-crisis watch (B/C family)")
    ap.add_argument("--write", action="store_true", help="write dated md + latest json")
    args = ap.parse_args()

    key = os.environ.get("FRED_API_KEY")
    if not key:
        raise SystemExit("FRED_API_KEY missing — put it in .env (local only)")
    fred = Fred(api_key=key)

    real = fred_series(fred, "DFII10")
    hy = fred_series(fred, "BAMLH0A0HYM2")
    nom = fred_series(fred, "DGS10")
    vix = fred_series(fred, "VIXCLS")
    vix3m = fred_series(fred, "VXVCLS")
    krw = fred_series(fred, "DEXKOUS")
    jpy = fred_series(fred, "DEXJPUS")
    spx = fred_series(fred, "SP500", start="2024-01-01")

    card = load_json(CARD)
    hist = load_json(HIST)

    # Haven failure: 20d gold/SPX return correlation + SPX 20d return
    g = pd.Series({pd.to_datetime(r["date"]): r.get("gold") for r in hist}).dropna()
    dfh = pd.concat([g.rename("gold"), spx.rename("spx")], axis=1).dropna().sort_index()
    corr = None
    spx_ret = None
    if len(dfh) >= 21:
        rets = dfh.pct_change().dropna().tail(21)
        corr = float(rets["gold"].corr(rets["spx"]))
        spx_ret = float(dfh["spx"].iloc[-1] / dfh["spx"].iloc[-21] - 1.0)

    # Physical: diesel crack (WTI) 20d change vs 1y sigma of 20d changes
    crack = chg20 = sigma20 = None
    diesel_date = None
    stale_days = None
    if os.path.exists(DIESEL):
        d = pd.read_csv(DIESEL, parse_dates=["date"]).dropna(subset=["crack_diesel_wti"]).sort_values("date")
        s = d.set_index("date")["crack_diesel_wti"]
        crack = float(s.iloc[-1])
        diesel_date = s.index[-1].date()
        chg20 = float(s.iloc[-1] - s.iloc[-21]) if len(s) > 21 else None
        sigma20 = float(s.diff(20).tail(252).std()) if len(s) > 252 else None
        stale_days = (datetime.now(timezone.utc).date() - diesel_date).days

    rows = []

    v = float(real.iloc[-1]); d = chg(real)
    rows.append(("real10", "10Y 实际利率", f"{v:.2f}%", f"{d:+.2f}pp / 20d" if d is not None else "—",
                 classify_real(v, d), f"十年分位 {pct_rank(real, v)*100:.0f}% · {real.index[-1].date()}"))

    v = float(hy.iloc[-1]); d = chg(hy); rk = pct_rank(hy, v)
    rows.append(("hy_oas", "HY 信用利差", f"{v:.2f}%", f"{d:+.2f}pp / 20d" if d is not None else "—",
                 classify_hy(v, d, rk), f"十年分位 {rk*100:.0f}% · {hy.index[-1].date()}"))

    v = float(nom.iloc[-1]); d = chg(nom)
    rows.append(("nominal10", "10Y 名义利率", f"{v:.2f}%", f"{d:+.2f}pp / 20d" if d is not None else "—",
                 classify_nominal(v), f"{nom.index[-1].date()}"))

    v = float(vix.iloc[-1]); rk = pct_rank(vix, v); v3 = float(vix3m.iloc[-1]) if len(vix3m) else None
    rows.append(("vix_term", "VIX / 期限结构", f"{v:.2f}" + (f" vs {v3:.2f}" if v3 else ""),
                 f"分位 {rk*100:.0f}%", classify_vix(v, rk, v3),
                 f"{vix.index[-1].date()}" + (" · 倒挂" if v3 and v > v3 else "")))

    krw_raw = chg_pct(krw)
    jpy_raw = chg_pct(jpy)
    jpy_stress = -jpy_raw if jpy_raw is not None else None
    def _fx_txt(v):
        return ("贬值" if v > 0 else "升值") if v is not None else "—"
    rows.append(("fx_funding", "FX 融资压力（KRW/JPY）",
                 f"KRW {krw_raw*100:+.1f}%（{_fx_txt(krw_raw)}） · JPY {jpy_raw*100:+.1f}%（{_fx_txt(jpy_raw)}）" if krw_raw is not None and jpy_raw is not None else "—",
                 "20d 变化（压力：KRW 贬 / JPY 升）", classify_fx(krw_raw, jpy_stress),
                 f"{krw.index[-1].date()} / {jpy.index[-1].date()}（FRED 滞后 ~1 周）"))

    rows.append(("haven", "避险失效（金—股）",
                 f"corr {corr:+.2f} · SPX {spx_ret*100:+.1f}%" if corr is not None else "—",
                 "20d 相关性 / 股指", classify_haven(corr, spx_ret),
                 f"金—股日收益相关性；{dfh.index[-1].date()}"))

    rows.append(("physical", "实物压力（柴油裂解）",
                 f"${crack:.1f}" if crack is not None else "—",
                 f"{chg20:+.1f} / 20d" if chg20 is not None else "—",
                 classify_physical(crack, chg20, sigma20, stale_days or 99),
                 f"{diesel_date} · 数据 {stale_days} 天前" if diesel_date else "无缓存"))

    score = sum(PTS[r[4]] for r in rows)
    band = RED if score >= 7 else (AMBER if score >= 4 else GREEN)
    band_txt = {RED: "红色（多项压力共振）", AMBER: "琥珀（压力在积累）", GREEN: "绿色（未共振）"}[band]
    as_of = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    s = card.get("screener") or {}
    a_on = bool(s.get("s2") and s.get("s3"))
    print(f"Pre-crisis watch · {as_of} · score {score}/14 · {band_txt}")
    print(f"  A-family trigger: {'ON' if a_on else 'OFF'} (VIX {s.get('vix')} vs {s.get('vix_thr')}; oil pctl {s.get('oil_pctl')})")
    for rid, name, val, chg_txt, st, note in rows:
        print(f"  {st} {name:18s} {val:28s} {chg_txt:16s} {note}")

    if args.write:
        os.makedirs(OUT_DIR, exist_ok=True)
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        md = [f"# 危机前哨 · {day}", "",
              f"> 评分 **{score}/14** · {band_txt} · {as_of}",
              "> 解释层：不改变仓位；A 类扳机仍以 VIX P80 + 油 P25 为准。",
              f"> A-family trigger: {'ON' if a_on else 'OFF'}", "",
              "| 指标 | 现值 | 变化 | 状态 | 备注 |", "|---|---:|---:|:--:|---|"]
        for rid, name, val, chg_txt, st, note in rows:
            md.append(f"| {name} | {val} | {chg_txt} | {st} | {note} |")
        md += ["", "---", "*数据：FRED（DFII10 / BAMLH0A0HYM2 / DGS10 / VIXCLS / VXVCLS / DEXKOUS / DEXJPUS / SP500）；柴油裂解 EIA 缓存；金价 wti_history。*"]
        md_path = os.path.join(OUT_DIR, f"precrisis_watch_{day}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n")
        payload = {"as_of": as_of, "score": score, "band": band_txt,
                   "indicators": [dict(id=r[0], name=r[1], value=r[2], change=r[3],
                                       status=r[4], note=r[5]) for r in rows]}
        with open(os.path.join(OUT_DIR, "precrisis_watch_latest.json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print("wrote:", md_path)


if __name__ == "__main__":
    main()
