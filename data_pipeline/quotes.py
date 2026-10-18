# -*- coding: utf-8 -*-
"""Intraday quotes -> provisional card (v3.0 MVP).

Primary: Yahoo chart API (stdlib only, no yfinance crumb/rate-limit issues).
Fallback: Tencent qt.gtimg.cn for WTI/Gold/Brent. VIX is required — no fallback.
"""
from __future__ import annotations

import copy
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HEADERS = {"User-Agent": "Mozilla/5.0 (Deep-Risk-OPP alert)"}
SYMBOLS = {
    "CL=F": "wti",
    "GC=F": "gold",
    "BZ=F": "brent",
    "^VIX": "vix",
    "DX-Y.NYB": "dxy",
    "^TNX": "us10y",
}
TENCENT = {"wti": "hf_CL", "gold": "hf_GC", "brent": "hf_BZ"}


def _get(url, timeout=8):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _yahoo(sym):
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/" +
           urllib.parse.quote(sym) + "?interval=5m&range=1d")
    d = json.loads(_get(url).decode("utf-8"))
    res = d["chart"]["result"][0]
    meta = res["meta"]
    price = meta.get("regularMarketPrice")
    if price is None:
        closes = [c for c in res["indicators"]["quote"][0].get("close", []) if c is not None]
        if not closes:
            raise ValueError("no price")
        price = closes[-1]
    ts = meta.get("regularMarketTime")
    when = (datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            if isinstance(ts, (int, float)) else None)
    return {"price": float(price), "time": when, "source": "yahoo"}


def _tencent(sym):
    txt = _get("https://qt.gtimg.cn/q=" + sym).decode("gbk", "replace")
    body = txt.split('"', 2)[1]
    parts = body.split(",")
    price = float(parts[0])
    t = parts[6] if len(parts) > 6 else ""
    d = parts[12] if len(parts) > 12 else ""
    when = (d + " " + t) if d and t else None
    return {"price": price, "time": when, "source": "tencent"}


def quote_age_minutes(q):
    """Age of a quote in minutes; Tencent times are Beijing time."""
    t = (q or {}).get("time")
    if not t:
        return None
    try:
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 60.0
    except Exception:
        try:
            dt = datetime.strptime(t, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone(__import__("datetime").timedelta(hours=8)))
            return (datetime.now(timezone.utc) - dt).total_seconds() / 60.0
        except Exception:
            return None


def _cboe_vix():
    d = json.loads(_get("https://cdn.cboe.com/api/global/delayed_quotes/quotes/_VIX.json").decode("utf-8"))
    price = d["data"]["current_price"]
    when = d.get("timestamp")
    try:
        when = datetime.strptime(when, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc).isoformat()
    except Exception:
        when = None
    return {"price": float(price), "time": when, "source": "cboe-delayed"}


def fetch_quotes():
    out = {}
    for sym, key in SYMBOLS.items():
        for attempt in (1, 2):
            try:
                out[key] = _yahoo(sym)
                break
            except Exception:
                if attempt == 2:
                    break
                time.sleep(1)
    for key, tsym in TENCENT.items():
        if key not in out:
            try:
                out[key] = _tencent(tsym)
            except Exception:
                pass
    if "vix" not in out:
        try:
            out["vix"] = _cboe_vix()
        except Exception:
            pass
    missing = [k for k in ("wti", "gold", "vix") if k not in out]
    if missing:
        raise RuntimeError("missing critical quotes: " + ", ".join(missing))
    return out


def regime_for_gor(gor):
    if gor is None:
        return None
    if gor >= 45:
        return "原油极端低估"
    if gor >= 30:
        return "修复周期"
    if gor >= 20:
        return "估值均衡"
    return "原油泡沫"


def provisional_card(card, quotes):
    """Clone the daily card, override prices, recompute GOR/regime/s2."""
    c = copy.deepcopy(card)
    d = c.setdefault("data", {})

    def put(key, qkey, fallback=None):
        q = quotes.get(qkey)
        if q:
            d.setdefault(key, {})
            d[key]["price"] = q["price"]
            d[key]["change_pct"] = 0.0
        elif fallback is not None:
            d.setdefault(key, {})
            d[key]["price"] = fallback

    put("WTI原油", "wti")
    put("黄金期货", "gold")
    wti = d.get("WTI原油", {}).get("price")
    gold = d.get("黄金期货", {}).get("price")
    brent_q = quotes.get("brent")
    brent = brent_q["price"] if brent_q else (wti * 1.06 if wti else None)
    put("布伦特原油", "brent", brent)
    put("美元指数DXY", "dxy")
    put("10Y美债收益率", "us10y")
    put("VIX恐慌指数", "vix")

    # Never let a synthetic Brent masquerade as a real quote.
    c["brent_source"] = (brent_q or {}).get("source") or ("estimated" if brent else None)
    c["brent_asof"] = (brent_q or {}).get("time")
    dq = c.setdefault("data_quality", {})
    sources = dq.setdefault("sources", {})
    if brent_q:
        sources["布伦特"] = brent_q.get("source") or "yahoo"
        dq["fallbacks"] = {k: v for k, v in (dq.get("fallbacks") or {}).items()
                           if "布伦特" not in k}
    elif brent:
        sources["布伦特"] = "WTI×1.06 合成"
        dq.setdefault("fallbacks", {})["布伦特"] = "WTI×1.06 合成"
        dq["ok"] = False

    if wti and gold:
        c["gor_wti"] = round(gold / wti, 2)
        c["gor_brent"] = round(gold / brent, 2) if brent else c["gor_wti"]
        c["regime"] = regime_for_gor(c["gor_brent"])

    s = c.setdefault("screener", {})
    if quotes.get("vix"):
        s["vix"] = quotes["vix"]["price"]
        thr = s.get("vix_thr")
        if isinstance(thr, (int, float)):
            s["s2"] = bool(s["vix"] >= thr)
    qtimes = [q["time"] for q in quotes.values() if q.get("time")]
    c["updated"] = max(qtimes) if qtimes else datetime.now(timezone.utc).isoformat()
    c["_source"] = "yahoo-intraday"
    c["_mode"] = "intraday"
    return c
