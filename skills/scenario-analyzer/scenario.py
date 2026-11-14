#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""18-month scenario pack generator.

Builds a structured 1st/2nd/3rd-order analysis skeleton from a headline,
pre-filled with the current GOR card, portfolio and credit data. It does not
invent conclusions: the prompts are for the analyst (or Claude) to fill.

Usage:
  python skills/scenario-analyzer/scenario.py --headline "Nvidia CEO resigns"
  python skills/scenario-analyzer/scenario.py --headline "..." --out report.md --json
"""
from __future__ import annotations
import argparse, json, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name, default=None):
    try:
        return json.loads((ROOT / name).read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def price(card, key):
    try:
        return float(card["data"][key]["price"])
    except Exception:
        return None


def fred_bp(series):
    try:
        lines = (ROOT / "看板日志" / "cache" / f"fred_{series}.csv").read_text(encoding="utf-8").splitlines()
        return round(float(lines[-1].split(",")[1]) * 100, 1)
    except Exception:
        return None


def baseline():
    card = load("gor_latest.json")
    mp = load("model_portfolio.json")
    hist = (load("history.json").get("rows") or [])
    last = hist[-1] if hist else {}
    return {
        "as_of": card.get("updated", ""),
        "gor_wti": card.get("gor_wti"),
        "gor_brent": card.get("gor_brent"),
        "gold": price(card, "黄金期货"),
        "wti": price(card, "WTI原油"),
        "brent": price(card, "布伦特原油"),
        "vix": price(card, "VIX恐慌指数"),
        "dxy": price(card, "美元指数DXY"),
        "us10y": price(card, "10Y美债收益率"),
        "regime": card.get("regime"),
        "position": card.get("final_position"),
        "allocation": card.get("allocation"),
        "screener": card.get("screener", {}).get("verdict"),
        "hy_bp": fred_bp("BAMLH0A0HYM2"),
        "ccc_bp": fred_bp("BAMLH0A3HYC"),
        "nav": mp.get("nav"),
        "drawdown_pct": round((mp.get("nav", 0) / max([h.get("nav", 0) for h in mp.get("history", [])] or [1]) - 1) * 100, 1) if mp.get("nav") else None,
        "last_history": last.get("date", ""),
    }


def render(headline, b, months):
    alloc = b.get("allocation") or {}
    alloc_txt = " · ".join(f"{k} {v}%" for k, v in alloc.items())
    return f"""# Scenario Pack — {headline}

*Generated {date.today().isoformat()} · {months}-month horizon · Deep-Risk-OPP research framework, not investment advice*

## Baseline (do not mix vintages)

| Item | Value | Source |
|---|---:|---|
| GOR (WTI / Brent) | {b['gor_wti']} / {b['gor_brent']} | daily card {b['as_of']} |
| Gold / WTI / Brent | ${b['gold']} / ${b['wti']} / ${b['brent']} | daily card |
| VIX / DXY / 10Y | {b['vix']} / {b['dxy']} / {b['us10y']}% | daily card |
| Regime / screener | {b['regime']} / {b['screener']} | daily card |
| HY / CCC OAS | {b['hy_bp']}bp / {b['ccc_bp']}bp | FRED cache |
| Position / allocation | {b['position']}% — {alloc_txt} | daily card |
| Model NAV / drawdown | {b['nav']} / {b['drawdown_pct']}% | model_portfolio |

## 1st order — what moves first (0–3 months)

Prompts:
- Which cash-flow or discount-rate variable does the headline hit first?
- What is the immediate price reaction, and what did the credit market do?
- Is this a **governance**, **financing**, **policy** or **demand** event?

Notes: _[fill]_

## 2nd order — who gets repriced (3–12 months)

| Channel | Question | Evidence to watch | Verdict |
|---|---|---|---|
| Suppliers | Do orders/backlog survive the headline? | capex guidance, backlog, receivables | _[fill]_ |
| Customers | Do they diversify or double down? | custom ASIC, procurement, contracts | _[fill]_ |
| Competitors | Who gains at the margin? | share, pricing, design wins | _[fill]_ |
| Credit | Do spreads widen with equities? | HY/CCC, DC HY, lending terms | _[fill]_ |
| Policy | Does the rule set tighten or loosen? | export controls, hearings, budgets | _[fill]_ |
| Positioning | Who is forced to sell? | flows, options, leverage | _[fill]_ |

## 3rd order — regime change (12–{months} months)

| Channel | Question | Signpost |
|---|---|---|
| Capex regime | Does the marginal dollar move from GPUs to power/grid/deployment? | hyperscaler capex mix |
| Governance | Do founder-led mega-caps get a key-man discount? | board succession, disclosure |
| Asset class | Does compute become infrastructure (lower cost of capital)? | REITs, infrastructure funds |
| Politics | Does AI become a national-security / election issue? | hearings, legislation |
| Geography | Does the AI stack bifurcate (US vs China/sovereign)? | export rules, domestic chips |

## Scenarios ({months} months)

| Scenario | Trigger | Path | Signposts | Probability (qualitative) |
|---|---|---|---|---|
| Base | _[fill]_ | _[fill]_ | _[fill]_ | _[fill]_ |
| Upside | _[fill]_ | _[fill]_ | _[fill]_ | _[fill]_ |
| Downside | _[fill]_ | _[fill]_ | _[fill]_ | _[fill]_ |

## Falsifiers

- What would prove the base case wrong?
- What would force a position change (GOR zone, HY/CCC, VIX, capex)?
- What would make this a **systemic** rather than idiosyncratic event?

## Data and definitions

Prices: daily card. Credit: FRED BAMLH0A0HYM2 / BAMLH0A3HYC. Portfolio: model_portfolio.json.
All headline claims must be sourced; separate **reported** from **confirmed**.
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="18-month scenario pack")
    ap.add_argument("--headline", required=True)
    ap.add_argument("--horizon-months", type=int, default=18)
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    b = baseline()
    if a.json:
        print(json.dumps({"headline": a.headline, "baseline": b}, ensure_ascii=False, indent=1))
        return 0
    text = render(a.headline, b, a.horizon_months)
    out = Path(a.out) if a.out else ROOT / "看板日志" / "reports" / "scenarios" / f"scenario-{date.today().isoformat()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
