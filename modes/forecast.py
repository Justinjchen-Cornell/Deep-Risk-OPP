"""
Deep-Risk-OPP — mode forecast (P1-1 拆分自 run.py)
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modes.common import get_gor_zone, get_gor_blend, check_dynamic_hard_stop, get_allocation

def mode_forecast():
    """18-month forward-looking forecast based on current GOR regime."""
    print("=" * 64)
    print("  Deep-Risk-OPP  |  18-Month Forward Forecast")
    print(f"  {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 64)

    # Load current data
    gor_path = config.GOR_LATEST
    if not os.path.exists(gor_path):
        print("\n  No gor_latest.json. Run python run.py --mode daily first.")
        return
    with open(gor_path, 'r', encoding='utf-8') as f:
        latest = json.load(f)

    wti = latest['data'].get('WTI原油', {}).get('price', 0)
    gold = latest['data'].get('黄金期货', {}).get('price', 0)
    gor_w = latest.get('gor_wti', 0)
    gor_b = latest.get('gor_brent', 0)
    dxy = latest['capital_three_flows'].get('dxy', 100)
    vix = latest['capital_three_flows'].get('vix', 17)
    us10y = latest['capital_three_flows'].get('tenyear', 4.5)
    us30y = latest['capital_three_flows'].get('thirtyyear', 5.0)
    fed_rate = latest['capital_three_flows'].get('fed_rate', 3.6)
    regime = latest.get('regime', 'unknown')

    # ─── 1. Current State ──────────────────────────────────────
    print(f"""
  ┌──────────────────────────────────────────────────────────────┐
  │  NOWCAST                                                      │
  ├──────────────────────────────────────────────────────────────┤
  │  GOR:     {gor_w:.1f} (WTI) / {gor_b:.1f} (Brent)           {'':>30s}│
  │  Regime:  {regime:<50s}│
  │  Gold:    ${gold:,.0f}  |  WTI: ${wti:.2f}  |  DXY: {dxy:.2f}      {'':>18s}│
  │  10Y:     {us10y:.2f}%  |  30Y: {us30y:.2f}%  |  VIX: {vix:.2f}     {'':>17s}│
  │  Fed:     {fed_rate:.2f}%  |  WTI<$75: {'YES — Hard Stop' if wti<75 else 'No'}                         {'':>19s}│
  └──────────────────────────────────────────────────────────────┘""")

    # ─── 2. Three Scenario Paths ────────────────────────────────
    # Path A (Bull): WTI recovers, GOR mean-reverts via oil rally
    # Path B (Base): Grinding sideways, GOR stays elevated
    # Path C (Bear): Liquidity crash, everything sells off, then cheap

    print("""
  ╔══════════════════════════════════════════════════════════════╗
  ║              18-MONTH SCENARIO PATHS                          ║
  ╠══════════════════════════════════════════════════════════════╣""")

    # Path A
    wti_a = wti * 1.50 if wti > 0 else 105
    gold_a = gold * 0.95
    gor_a = gold_a / wti_a
    print(f"""
  ║  [+] PATH A: Mean Reversion Rally  (est. 25% probability)      ║
  ║  ───────────────────────────────────────────────────────────  ║
  ║  Trigger:   WTI reclaims $80+ on supply disruption           ║
  ║             OR Fed signals end of tightening cycle           ║
  ║  WTI:       {wti_a:>6.0f}  (current: ${wti:.0f})                            ║
  ║  Gold:      {gold_a:>6.0f}  (current: ${gold:.0f})                          ║
  ║  GOR:       {gor_a:>6.1f}  -> recovery zone                                 ║
  ║  Implication: Oil allocation normalizes to 20-25%. Gold trim.║""")

    # Path B
    wti_b = wti * 1.15 if wti > 0 else 85
    gold_b = gold * 1.05
    gor_b_path = gold_b / wti_b
    print(f"""
  ║  [~] PATH B: Grinding Sideways  (est. 45% probability)         ║
  ║  ───────────────────────────────────────────────────────────  ║
  ║  Trigger:   Iran peace holds. OPEC+ cheats. No macro shock.  ║
  ║             Warsh maintains hawkish posture through 2027.    ║
  ║  WTI:       {wti_b:>6.0f}  (current: ${wti:.0f})                            ║
  ║  Gold:      {gold_b:>6.0f}  (current: ${gold:.0f})                          ║
  ║  GOR:       {gor_b_path:>6.1f}  -> still extreme opportunity                   ║
  ║  Implication: Oil 5% (hard stop lingers). Cash heavy. Wait.  ║""")

    # Path C
    wti_c = wti * 0.65 if wti > 0 else 50
    gold_c = gold * 1.30
    gor_c = gold_c / wti_c
    print(f"""
  ║  [!] PATH C: Liquidity Crash -> Forced Seller Bonanza (30%)    ║
  ║  ───────────────────────────────────────────────────────────  ║
  ║  Trigger:   BOJ hikes -> carry trade unwind -> global freeze  ║
  ║             OR US 30Y auction fails -> sovereign credit shock ║
  ║             OR AI bubble bursts -> broad risk-off cascade     ║
  ║  WTI:       {wti_c:>6.0f}  (crash)                                          ║
  ║  Gold:      {gold_c:>6.0f}  (flight-to-safety surge)                        ║
  ║  GOR:       {gor_c:>6.1f}  -> all-time extreme                                 ║
  ║  Implication: THE opportunity. Deploy cash at WTI $50-60.   ║
  ╚══════════════════════════════════════════════════════════════╝""")

    # ─── 3. Macro Trigger Watchlist ─────────────────────────────
    print("""
  ┌──────────────────────────────────────────────────────────────┐
  │  MACRO TRIGGER WATCHLIST  (next 18 months)                    │
  ├──────────────────────────────────────────────────────────────┤""")

    triggers = [
        ("USD/JPY > 160", "BOJ forced intervention -> carry unwind", "40%", "RED",
         "Global liquidity freeze. All risk assets sell off. Cash = king."),
        ("US 30Y auction fails", "Bid-to-cover < 2.0 -> sovereign credit event", "20%", "RED",
         "USD crisis. Gold surges. Everything else crashes. The 'big one'."),
        ("WTI reclaims $80", "Supply disruption OR OPEC+ emergency cut", "35%", "GRN",
         "Hard stop releases. Oil allocation resets to framework levels."),
        ("Fed signals cut", "Warsh pivots on growth slowdown -> rate cut 2027H1", "30%", "GRN",
         "DXY weakens. Risk appetite returns. Centripetal collapse reverses."),
        ("AI bubble bursts", "Mag-7 earnings miss -> broad equity selloff", "25%", "YEL",
         "Flight to safety. Gold rips. Oil dips on demand-fear. Cash wins."),
        ("Hormuz closes again", "Iran conflict re-escalates -> 21M bbl/day offline", "15%", "YEL",
         "Oil spikes $20-30 in 48hrs. GOR collapses. Shipping = geopolitical call option."),
    ]

    for trigger, catalyst, prob, icon, implication in triggers:
        print(f"""  │                                                              │
  │  {icon} {trigger:<40s} {prob:>6s}                            │
  │     {catalyst:<60s}│
  │     -> {implication:<58s}│""")

    print("""  └──────────────────────────────────────────────────────────────┘""")

    # ─── 4. Regime Transition History ───────────────────────────
    print("""
  ┌──────────────────────────────────────────────────────────────┐
  │  HISTORICAL GOR MEAN REVERSION  (analog reference)            │
  ├──────────────────────────────────────────────────────────────┤""")

    analogs = [
        ("2020.04", 69.5, "COVID shock", "+167%", "12 months", "WTI $25 -> $67"),
        ("2016.01", 39.0, "Oil price collapse", "+54%", "12 months", "WTI $26 -> $54"),
        ("2008.12", 30.0, "GFC demand shock", "+78%", "12 months", "WTI $37 -> $80"),
    ]
    for date, peak, context, oil_move, duration, detail in analogs:
        print(f"""  │                                                              │
  │  {date}  GOR={peak}  {context:<30s}          │
  │     Oil return: {oil_move:<8s}  Duration: {duration:<12s}               │
  │     {detail:<58s}│""")

    print(f"""  │                                                              │
  │  NOW    GOR={gor_w:.1f}  {"WTI hard stop active" if wti<75 else "Mean reversion in progress":<30s}          │
  │     Current GOR is {'above' if gor_w>45 else 'below'} all three historical analogs.               │
  └──────────────────────────────────────────────────────────────┘""")

    # ─── 5. The Framework's Base Case ──────────────────────────
    if wti < 75:
        base_action = "Hold 5% oil, 20% gold, 68% cash. Wait for WTI > $75."
    else:
        base_action = "Accumulate oil to 27%, gold 15%, cash 50%. Target WTI $95-105."

    print(f"""
  ╔══════════════════════════════════════════════════════════════╗
  ║  FRAMEWORK BASE CASE  (next 6 months)                        ║
  ╠══════════════════════════════════════════════════════════════╣
  ║  {base_action:<60s}║
  ║                                                              ║
  ║  The GOR ratio has NEVER stayed above 45 indefinitely.       ║
  ║  Mean reversion is a statistical certainty. The only         ║
  ║  question is HOW: oil rises, gold falls, or both.            ║
  ║                                                              ║
  ║  Historical mean reversion takes 12-36 months from peak.     ║
  ║  The 2026 peak was Feb (78.0). We are 5 months in.           ║
  ║                                                              ║
  ║  The framework does not predict TIMING. It predicts          ║
  ║  DIRECTION and provides DISCIPLINE for the wait.              ║
  ╚══════════════════════════════════════════════════════════════╝
""")

    # Save forecast
    result = {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "current": {"gor_wti": gor_w, "gor_brent": gor_b, "wti": wti, "gold": gold,
                     "dxy": dxy, "vix": vix, "10y": us10y, "regime": regime},
        "scenarios": {
            "bull": {"wti": wti_a, "gold": gold_a, "gor": gor_a, "prob": 0.25},
            "base": {"wti": wti_b, "gold": gold_b, "gor": gor_b_path, "prob": 0.45},
            "bear": {"wti": wti_c, "gold": gold_c, "gor": gor_c, "prob": 0.30},
        },
        "triggers": [{"trigger": t[0], "probability": t[2]} for t in triggers],
    }
    os.makedirs("看板日志", exist_ok=True)
    out = f"看板日志/forecast_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(f"  Forecast saved: {out}")
    print()
