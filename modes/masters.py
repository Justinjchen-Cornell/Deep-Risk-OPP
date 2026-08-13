"""
Deep-Risk-OPP — mode masters (P1-1 拆分自 run.py)
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modes.common import get_gor_zone, get_gor_blend, check_dynamic_hard_stop, get_allocation

def mode_masters():
    """Run 6-master consensus engine on current GOR data."""
    print("=" * 60)
    print("  Six Masters Consensus  |  Deep-Risk-OPP")
    print("=" * 60)

    # Load latest data
    gor_path = "gor_latest.json"
    if not os.path.exists(gor_path):
        print("\n  No gor_latest.json. Run python run.py --mode daily first.")
        return

    with open(gor_path, 'r', encoding='utf-8') as f:
        latest = json.load(f)

    wti = latest['data'].get('WTI原油', {}).get('price', 0)
    gold = latest['data'].get('黄金期货', {}).get('price', 0)
    gor_w = latest.get('gor_wti', 0)
    dxy = latest['capital_three_flows'].get('dxy', 100)
    vix = latest['capital_three_flows'].get('vix', 17)
    us10y = latest['capital_three_flows'].get('tenyear', 4.5)
    regime = latest.get('regime', 'unknown')

    masters = []

    # Buffett: cash-heavy when GOR extreme + high rates
    buffett_def = gor_w >= 45 and us10y > 4.0
    buffett_buy = wti < 75  # likes cheap energy
    masters.append({
        "name": "Buffett", "posture": "DEFENSIVE" if buffett_def else "SELECTIVE",
        "signal": "HOLD CASH" if buffett_def else "WATCH ENERGY",
        "confidence": 85 if buffett_def else 65,
        "quip": f"${397 if buffett_def else 200}B cash. {'Cannot find anything at sensible prices.' if buffett_def else 'Energy is on the watchlist.'}"
    })

    # Burry: bond market screaming = systemic risk
    burry_alert = us10y > 4.3 or (dxy and dxy > 99)
    masters.append({
        "name": "Burry", "posture": "DEFENSIVE",
        "signal": "RED ALERT" if burry_alert else "CAUTIOUS",
        "confidence": 92 if burry_alert else 78,
        "quip": f"10Y at {us10y}%. {'The bond market IS screaming.' if us10y > 4.3 else 'Watching credit spreads.'}"
    })

    # Druckenmiller: liquidity first
    druck_liquidity_tight = dxy and dxy > 99
    masters.append({
        "name": "Druckenmiller", "posture": "DEFENSIVE" if druck_liquidity_tight else "NEUTRAL",
        "signal": "TACTICAL OIL + STRATEGIC CASH",
        "confidence": 88 if druck_liquidity_tight else 70,
        "quip": f"DXY {dxy if dxy else '?'}. {'Three CBs tightening = 1997-level signal.' if druck_liquidity_tight else 'Liquidity neutral for now.'}"
    })

    # Damodaran: valuation-based
    g_val = (gor_w - 35) / 35 if gor_w > 0 else 0  # deviation from fair
    masters.append({
        "name": "Damodaran", "posture": "BULLISH ENERGY" if gor_w >= 45 else "NEUTRAL",
        "signal": f"Oil {abs(g_val)*100:.0f}% {'UNDER' if gor_w>=45 else 'FAIR'}VALUED",
        "confidence": 75,
        "quip": f"GOR={gor_w:.1f}. Energy DCF says {'40% upside' if gor_w>=45 else 'fairly priced'}."
    })

    # Taleb: tail risk / convexity
    tails = sum([1 for t in [wti<75, vix>20 if vix else False, us10y>4.3]])
    masters.append({
        "name": "Taleb", "posture": "HEDGED",
        "signal": f"{tails} TAIL RISKS ACTIVE",
        "confidence": 85,
        "quip": f"Barbell: 90% safe + 10% convex. {'Buy straddles.' if (vix and vix<17) else 'Tails are fat.'}"
    })

    # Li Ka-shing: patience, forced sellers
    masters.append({
        "name": "Li Ka-shing", "posture": "PATIENT",
        "signal": "WAIT FOR FORCED SELLERS" if wti < 75 else "HOLD + WATCH",
        "confidence": 80,
        "quip": f"未买先想卖。{'Direction is right but WTI<' + str(wti) + ' — wait.' if wti<75 else 'Holding pattern.'}"
    })

    # Count votes
    defensive = sum(1 for m in masters if m['posture'] == 'DEFENSIVE')
    bullish = sum(1 for m in masters if 'BULLISH' in m['posture'])

    print(f"""
  {'─'*58}
    Data: Gold=${gold:.0f}  WTI=${wti:.2f}  GOR={gor_w:.1f}  {regime}
  {'─'*58}
    {"Master":<16s} {"Posture":<16s} {"Signal":<25s} {"Confidence":>10s}
  {'─'*58}""")
    for m in masters:
        print(f"    {m['name']:<16s} {m['posture']:<16s} {m['signal']:<25s} {m['confidence']:>8d}%")
    print(f"  {'─'*58}")
    print(f"    CONSENSUS: {defensive}/6 defensive | {bullish}/6 bullish energy")
    print(f"    {'⚠️  Majority defensive — cash is the position' if defensive >= 4 else '🟡 Mixed — selective deployment'}")
    print(f"  {'─'*58}\n")

    for m in masters:
        print(f"    {m['name']}: \"{m['quip']}\"")

    # Save
    result = {"date": datetime.now().strftime('%Y-%m-%d'), "masters": masters,
              "defensive_votes": defensive, "bullish_energy_votes": bullish}
    os.makedirs("看板日志", exist_ok=True)
    out = f"看板日志/masters_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {out}")
