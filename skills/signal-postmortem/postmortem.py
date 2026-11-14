#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal postmortem for Deep-Risk-OPP.

Scores the falsifiable signals in `signals_log.json` against `history.json`
and FRED credit caches. Outcomes: hit / miss / open.

Usage:
  python skills/signal-postmortem/postmortem.py
  python skills/signal-postmortem/postmortem.py --json
  python skills/signal-postmortem/postmortem.py --update   # write status back
"""
from __future__ import annotations
import argparse, json, sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HIST_FIELDS = {"wti", "gold", "brent", "gor_wti", "gor_brent", "vix", "dxy", "us10y"}
FRED_FILES = {"hy_oas": "fred_BAMLH0A0HYM2.csv", "ccc_oas": "fred_BAMLH0A3HYC.csv"}


def d(s):
    return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()


def load_history():
    rows = json.loads((ROOT / "history.json").read_text(encoding="utf-8"))["rows"]
    rows = [r for r in rows if r.get("date")]
    rows.sort(key=lambda r: r["date"])
    return rows


def load_fred(metric):
    p = ROOT / "看板日志" / "cache" / FRED_FILES[metric]
    if not p.exists():
        return {}
    out = {}
    for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines()[1:]:
        parts = ln.strip().split(",")
        if len(parts) < 2 or not parts[1] or parts[1] == ".":
            continue
        try:
            out[d(parts[0])] = float(parts[1]) * 100.0  # percent -> bp
        except ValueError:
            pass
    return out


def series_for(metric, rows, fred_cache):
    if metric in FRED_FILES:
        return fred_cache.setdefault(metric, load_fred(metric))
    return {d(r["date"]): float(r[metric]) for r in rows if r.get(metric) is not None}


def eval_threshold(sig, ser):
    start = d(sig["date"]); end = start + timedelta(days=int(sig.get("horizon_days", 5)))
    thr = float(sig["threshold"]); cond = sig["condition"]
    points = sorted((k, v) for k, v in ser.items() if start <= k <= end)
    hit = None
    for k, v in points:
        if (cond == "above" and v > thr) or (cond == "below" and v < thr):
            hit = (k, v); break
    if hit:
        return "hit", f"{hit[0]} value {hit[1]:.2f} {cond} {thr:g}"
    if date.today() >= end:
        last = f"last {points[-1][0]} {points[-1][1]:.2f}" if points else "no data"
        return "miss", f"no {cond} {thr:g} by {end}; {last}"
    return "open", f"window ends {end}"


def eval_contract(sig, ser):
    if not ser:
        return "open", "no price data"
    latest_d, latest_v = max(ser.items())
    base, target = float(sig["baseline"]), float(sig["target"])
    deadline = d(sig.get("deadline", "2099-12-31"))
    prog = (latest_v - base) / (target - base) if target != base else 0.0
    if (target >= base and latest_v >= target) or (target < base and latest_v <= target):
        return "hit", f"{latest_d} {latest_v:.2f} reached target {target:g}"
    if date.today() > deadline:
        return "miss", f"deadline {deadline}; latest {latest_d} {latest_v:.2f} ({prog*100:.1f}%)"
    return "open", f"{latest_d} {latest_v:.2f}; {prog*100:.1f}% of distance to {target:g}"


def eval_direction(sig, ser):
    start = d(sig["date"]); end = start + timedelta(days=int(sig.get("horizon_days", 5)))
    points = sorted((k, v) for k, v in ser.items() if start <= k <= end)
    if not points:
        return ("open", f"no data; window ends {end}") if date.today() < end else ("miss", "no data")
    first, last = points[0], points[-1]
    ret = (last[1] / first[1] - 1.0) * 100.0 if first[1] else 0.0
    expected = sig.get("expected", "up")
    min_move = float(sig.get("min_move_pct", 0.0))
    ok = (ret > 0 and expected == "up") or (ret < 0 and expected == "down")
    if abs(ret) >= min_move and ok:
        return "hit", f"{ret:+.2f}% by {last[0]}"
    if date.today() >= end:
        return "miss", f"{ret:+.2f}% by {last[0]}; expected {expected}"
    return "open", f"{ret:+.2f}% so far; window ends {end}"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Signal postmortem")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--update", action="store_true", help="write outcome back to signals_log.json")
    ap.add_argument("--out", help="write markdown report to this path")
    a = ap.parse_args(argv)

    log_path = ROOT / "signals_log.json"
    log = json.loads(log_path.read_text(encoding="utf-8"))
    rows = load_history()
    fred_cache = {}
    results = []

    for sig in log.get("signals", []):
        ser = series_for(sig["metric"], rows, fred_cache)
        typ = sig.get("type")
        if typ == "threshold":
            status, evidence = eval_threshold(sig, ser)
        elif typ == "contract":
            status, evidence = eval_contract(sig, ser)
        elif typ == "direction":
            status, evidence = eval_direction(sig, ser)
        else:
            status, evidence = "open", "unknown type"
        results.append({"id": sig["id"], "date": sig["date"], "type": typ,
                        "metric": sig["metric"], "status": status, "evidence": evidence,
                        "note": sig.get("note", "")})
        if a.update:
            sig["status"] = status
            sig["last_eval"] = date.today().isoformat()
            sig["evidence"] = evidence

    hits = sum(1 for r in results if r["status"] == "hit")
    misses = sum(1 for r in results if r["status"] == "miss")
    opens = sum(1 for r in results if r["status"] == "open")
    rate = (100.0 * hits / (hits + misses)) if (hits + misses) else None

    if a.update:
        log["updated"] = date.today().isoformat()
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")

    if a.json:
        print(json.dumps({"as_of": date.today().isoformat(), "hit": hits, "miss": misses,
                          "open": opens, "hit_rate_pct": round(rate, 1) if rate is not None else None,
                          "results": results}, ensure_ascii=False, indent=1))
        return 0

    lines = [f"# Signal Postmortem — {date.today().isoformat()}", "",
             f"**Hit {hits} · Miss {misses} · Open {opens}"
             + (f" · Hit rate {rate:.1f}%" if rate is not None else "") + "**", "",
             "| id | date | type | metric | outcome | evidence |", "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| `{r['id']}` | {r['date']} | {r['type']} | {r['metric']} | **{r['status']}** | {r['evidence']} |")
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
