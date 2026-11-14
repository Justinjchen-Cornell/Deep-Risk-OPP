#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Data-quality checker for Deep-Risk-OPP.

Validates the public card, history, model portfolio, performance ledger,
signal log and local caches before anything is published.
Advisory by default: exit 1 only on ERROR (use --strict to fail on WARN).
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISSUES = []


def add(sev, code, msg, file=None):
    ISSUES.append({"severity": sev, "code": code, "message": msg, "file": file})


def load_json(name):
    p = ROOT / name
    if not p.exists():
        add("ERROR", "missing_file", f"{name} not found", name); return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        add("ERROR", "invalid_json", f"{name}: {e}", name); return None


def parse_dt(s):
    if not s: return None
    s = str(s).strip().replace("Z", "+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d"):
        try: return datetime.strptime(s[:len(fmt) + 2], fmt)
        except ValueError: pass
    try: return datetime.fromisoformat(s)
    except ValueError: return None


def parse_date(s):
    dt = parse_dt(s); return dt.date() if dt else None


def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def check_card(card):
    if not card: return
    updated = parse_dt(card.get("updated"))
    if not updated:
        add("ERROR", "card_updated", "gor_latest.json: unparseable 'updated'", "gor_latest.json")
    else:
        age = (datetime.now() - updated).total_seconds() / 86400
        if age > 7: add("ERROR", "card_stale", f"card is {age:.1f} days old (>7)", "gor_latest.json")
        elif age > 2: add("WARN", "card_stale", f"card is {age:.1f} days old (>2)", "gor_latest.json")

    data = card.get("data") or {}
    ranges = {"黄金期货": (500, 12000), "WTI原油": (10, 250), "布伦特原油": (10, 260),
              "美元指数DXY": (60, 140), "10Y美债收益率": (-1, 15),
              "VIX恐慌指数": (5, 100), "COMEX铜": (1, 15)}
    prices = {}
    for key, (lo, hi) in ranges.items():
        v = num((data.get(key) or {}).get("price"))
        if v is None:
            add("ERROR", "card_missing_price", f"card.data.{key}.price missing", "gor_latest.json"); continue
        prices[key] = v
        if not (lo <= v <= hi):
            add("ERROR", "card_price_range", f"{key}={v} outside [{lo},{hi}]", "gor_latest.json")

    gw, gb = num(card.get("gor_wti")), num(card.get("gor_brent"))
    if prices.get("黄金期货") and prices.get("WTI原油") and gw:
        calc = prices["黄金期货"] / prices["WTI原油"]
        if abs(calc - gw) > 0.08: add("ERROR", "gor_inconsistent", f"gor_wti={gw} vs gold/wti={calc:.2f}", "gor_latest.json")
    if prices.get("黄金期货") and prices.get("布伦特原油") and gb:
        calc = prices["黄金期货"] / prices["布伦特原油"]
        if abs(calc - gb) > 0.08: add("ERROR", "gor_inconsistent", f"gor_brent={gb} vs gold/brent={calc:.2f}", "gor_latest.json")

    alloc = card.get("allocation") or {}
    vals = [num(v) for v in alloc.values()]
    if any(v is None for v in vals):
        add("ERROR", "alloc_nan", "allocation has non-numeric weights", "gor_latest.json")
    elif abs(sum(vals) - 100) > 0.1:
        add("ERROR", "alloc_sum", f"allocation sums to {sum(vals):.1f}, not 100", "gor_latest.json")
    fp = num(card.get("final_position"))
    if fp is None or not (0 <= fp <= 100):
        add("ERROR", "final_position", f"final_position={fp} outside [0,100]", "gor_latest.json")
    scr = card.get("screener") or {}
    if scr.get("verdict") not in ("绿", "黄", "红", None):
        add("WARN", "screener_verdict", f"unexpected verdict={scr.get('verdict')}", "gor_latest.json")


def check_history(hist, card):
    rows = (hist or {}).get("rows") or []
    if len(rows) < 30:
        add("ERROR", "history_short", f"history has only {len(rows)} rows", "history.json"); return
    dates = [parse_date(r.get("date")) for r in rows]
    if any(d is None for d in dates):
        add("ERROR", "history_date", "history has unparseable dates", "history.json"); return
    if dates != sorted(dates): add("ERROR", "history_order", "history dates are not sorted", "history.json")
    if len(set(dates)) != len(dates): add("WARN", "history_dupes", "duplicate dates in history", "history.json")
    last = rows[-1]
    for k in ("gold", "wti", "brent", "vix", "gor_wti", "gor_brent"):
        if num(last.get(k)) is None: add("ERROR", "history_field", f"last history row missing {k}", "history.json")
    if card:
        cdate = parse_date(card.get("updated"))
        if cdate and abs((cdate - dates[-1]).days) > 1:
            add("WARN", "card_history_date", f"card {cdate} vs history {dates[-1]}", "history.json")
        for hk, ck, tol in (("gold", "黄金期货", 0.01), ("wti", "WTI原油", 0.01),
                            ("brent", "布伦特原油", 0.01), ("vix", "VIX恐慌指数", 0.02)):
            hv = num(last.get(hk)); cv = num(((card.get("data") or {}).get(ck) or {}).get("price"))
            if hv and cv and abs(hv - cv) / max(abs(cv), 1e-9) > tol:
                add("WARN", "card_history_value", f"{hk}: history {hv} vs card {cv}", "history.json")


def check_portfolio(mp, card):
    if not mp: return
    weights = mp.get("weights") or {}
    vals = [num(v) for v in weights.values()]
    if any(v is None for v in vals):
        add("ERROR", "portfolio_nan", "model_portfolio weights non-numeric", "model_portfolio.json")
    elif abs(sum(vals) - 100) > 0.1:
        add("ERROR", "portfolio_sum", f"portfolio weights sum {sum(vals):.1f}", "model_portfolio.json")
    if num(mp.get("nav")) is None or num(mp.get("nav")) <= 0:
        add("ERROR", "portfolio_nav", "model_portfolio nav invalid", "model_portfolio.json")
    upd = parse_date(mp.get("updated"))
    if upd and (date.today() - upd).days > 7:
        add("WARN", "portfolio_stale", f"portfolio updated {upd}", "model_portfolio.json")
    if card:
        alloc = card.get("allocation") or {}
        for k in ("油气", "黄金", "现金", "A股", "铜"):
            a, b = num(weights.get(k)), num(alloc.get(k))
            if a is not None and b is not None and abs(a - b) > 0.1:
                add("WARN", "portfolio_card_mismatch", f"{k}: portfolio {a} vs card {b}", "model_portfolio.json")


def check_performance(pl):
    entries = (pl or {}).get("entries") or []
    if not entries:
        add("ERROR", "perf_empty", "performance_log has no entries", "performance_log.json"); return
    ids = set()
    for e in entries:
        eid = e.get("id")
        if not eid: add("ERROR", "perf_id", "entry without id", "performance_log.json")
        elif eid in ids: add("ERROR", "perf_dupe", f"duplicate id {eid}", "performance_log.json")
        ids.add(eid)
        pub = parse_date(e.get("publish_date"))
        if pub and pub > date.today() and e.get("status") != "planned":
            add("WARN", "perf_future", f"{eid} publish_date {pub} is future", "performance_log.json")
        if e.get("status") == "measured":
            if e.get("impressions") is None: add("ERROR", "perf_measured", f"{eid} measured without impressions", "performance_log.json")
            if not e.get("measured_at"): add("WARN", "perf_measured_at", f"{eid} measured without measured_at", "performance_log.json")
        for k in ("impressions", "likes", "comments", "shares", "followers", "clicks"):
            v = num(e.get(k))
            if v is not None and v < 0: add("ERROR", "perf_negative", f"{eid}.{k}={v}", "performance_log.json")


def check_signals(sig):
    signals = (sig or {}).get("signals") or []
    if not signals:
        add("WARN", "signals_empty", "signals_log has no signals", "signals_log.json"); return
    ids = set()
    for s in signals:
        sid = s.get("id")
        if not sid: add("ERROR", "signal_id", "signal without id", "signals_log.json")
        elif sid in ids: add("ERROR", "signal_dupe", f"duplicate signal id {sid}", "signals_log.json")
        ids.add(sid)
        if s.get("type") not in ("contract", "threshold", "direction"):
            add("ERROR", "signal_type", f"{sid}: type={s.get('type')}", "signals_log.json")
        if not parse_date(s.get("date")): add("ERROR", "signal_date", f"{sid}: bad date", "signals_log.json")
        if s.get("type") == "threshold":
            if num(s.get("threshold")) is None or s.get("condition") not in ("above", "below"):
                add("ERROR", "signal_threshold", f"{sid}: bad threshold/condition", "signals_log.json")
        if s.get("type") == "contract":
            if num(s.get("baseline")) is None or num(s.get("target")) is None:
                add("ERROR", "signal_contract", f"{sid}: bad baseline/target", "signals_log.json")


def check_cache():
    fred_daily = ["BAMLH0A0HYM2", "BAMLH0A3HYC", "BAMLC0A0CM", "VIXCLS", "DGS10"]
    for s in fred_daily:
        p = ROOT / "看板日志" / "cache" / f"fred_{s}.csv"
        if not p.exists():
            add("WARN", "cache_missing", f"fred_{s}.csv missing", str(p)); continue
        lines = [ln.strip() for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip()]
        if len(lines) < 2:
            add("WARN", "cache_empty", f"fred_{s}.csv empty", str(p)); continue
        d = parse_date(lines[-1].split(",")[0])
        if d and (date.today() - d).days > 14:
            add("WARN", "cache_stale", f"fred_{s} last {d}", str(p))
    eia = ROOT / "看板日志" / "cache" / "eia"
    if eia.exists():
        for p in sorted(eia.glob("*.csv")):
            lines = [ln.strip() for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip()]
            if len(lines) < 2: continue
            d = parse_date(lines[-1].split(",")[0])
            if d and (date.today() - d).days > 28:
                add("WARN", "eia_stale", f"{p.name} last {d}", str(p))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deep-Risk-OPP data-quality checker")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    a = ap.parse_args(argv)
    ISSUES.clear()

    card = load_json("gor_latest.json")
    hist = load_json("history.json")
    mp = load_json("model_portfolio.json")
    pl = load_json("performance_log.json")
    sig = load_json("signals_log.json")

    check_card(card or {})
    check_history(hist or {}, card or {})
    check_portfolio(mp or {}, card or {})
    check_performance(pl or {})
    check_signals(sig or {})
    check_cache()

    errors = [i for i in ISSUES if i["severity"] == "ERROR"]
    warns = [i for i in ISSUES if i["severity"] == "WARN"]
    if a.json:
        print(json.dumps({"errors": len(errors), "warnings": len(warns), "issues": ISSUES},
                         ensure_ascii=False, indent=1))
    else:
        for i in ISSUES:
            print(f"[{i['severity']}] {i['code']}: {i['message']}")
        print(f"\n{len(errors)} error(s), {len(warns)} warning(s)")
    if errors or (a.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
