"""
Deep-Risk-OPP — mode report (P1-1 拆分自 run.py)
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modes.common import get_gor_zone, get_gor_blend, check_dynamic_hard_stop, get_allocation

def mode_report():
    """Generate standalone HTML report: forecast + masters + triggers."""
    print("  Generating standalone report...")

    # Load data
    gor_path = config.GOR_LATEST
    if not os.path.exists(gor_path):
        print("  ERROR: No gor_latest.json. Run python run.py --mode daily first.")
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
    fed_bs = latest['capital_three_flows'].get('fed_balance', 7.0)
    m2 = latest['capital_three_flows'].get('m2', 23)
    regime = latest.get('regime', 'unknown')
    alloc = latest.get('allocation', {})

    zone = "extreme" if gor_w >= 45 else ("recovery" if gor_w >= 30 else ("fair_value" if gor_w >= 20 else "oil_bubble"))
    zone_color = {"extreme": "#ff4444", "recovery": "#ffaa00", "fair_value": "#00cc66", "oil_bubble": "#4488ff"}.get(zone, "#888")

    # Scenario paths
    wti_a, gold_a = wti * 1.50, gold * 0.95
    wti_b, gold_b = wti * 1.15, gold * 1.05
    wti_c, gold_c = wti * 0.65, gold * 1.30
    gor_a = gold_a / wti_a; gor_b_p = gold_b / wti_b; gor_c = gold_c / wti_c

    # Masters summary
    masters = [
        ("Buffett", "DEFENSIVE" if gor_w >= 45 else "SELECTIVE", f"${397 if gor_w>=45 else 200}B cash. {'Cannot find anything at sensible prices.' if gor_w>=45 else 'Energy on watchlist.'}"),
        ("Burry", "DEFENSIVE", f"10Y at {us10y}%. {'The bond market is screaming.' if us10y>4.3 else 'Watching credit spreads.'}"),
        ("Druckenmiller", "DEFENSIVE" if dxy>99 else "NEUTRAL", f"DXY {dxy:.1f}. {'Three CBs tightening simultaneously.' if dxy>99 else 'Liquidity neutral.'}"),
        ("Damodaran", "BULLISH ENERGY" if gor_w>=45 else "NEUTRAL", f"GOR={gor_w:.1f}. Energy {gor_w>=45 and '40% undervalued by DCF' or 'fairly priced'}."),
        ("Taleb", "HEDGED", f"Barbell: 90% safe + 10% convex. {'Buy straddles.' if vix<17 else 'Tails are fat.'}"),
        ("Li Ka-shing", "PATIENT", f"{'Direction right but wait for forced sellers.' if wti<75 else 'Holding pattern. 90% on what can go wrong.'}"),
    ]
    defensive = sum(1 for m in masters if m[1] == 'DEFENSIVE')

    # Triggers
    triggers = [
        ("USD/JPY > 160", "BOJ forced intervention, carry trade unwind", "40%", "#ff4444", "Global liquidity freeze. Cash = king."),
        ("WTI reclaims $80", "Supply disruption or OPEC+ emergency cut", "35%", "#00cc66", "Hard stop fully releases. Oil normalizes."),
        ("Fed signals cut", "Warsh pivots on growth slowdown", "30%", "#00cc66", "DXY weakens. Centripetal collapse reverses."),
        ("AI bubble bursts", "Mag-7 earnings miss, broad equity selloff", "25%", "#ffaa00", "Flight to safety. Gold rips. Cash wins."),
        ("US 30Y auction fails", "Bid-to-cover < 2.0, sovereign credit shock", "20%", "#ff4444", "USD crisis. Gold surges. Everything crashes."),
        ("Hormuz closes again", "Iran re-escalation, 21M bbl/day offline", "15%", "#ffaa00", "Oil spikes $20-30 in 48hrs. Shipping = call option."),
    ]

    analogs = [
        ("2020.04", "69.5", "COVID shock", "+167%", "12m", "WTI $25 → $67"),
        ("2016.01", "39.0", "Oil price collapse", "+54%", "12m", "WTI $26 → $54"),
        ("2008.12", "30.0", "GFC demand shock", "+78%", "12m", "WTI $37 → $80"),
    ]

    today = datetime.now().strftime('%Y-%m-%d')
    hardstop = "ACTIVE" if wti < 75 else "Released (WTI > $75)"

    # GOR bar width
    bar_pct = min(gor_w / 80 * 100, 100)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Deep-Risk-OPP Report · {today}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0d1117; color:#c9d1d9; font-family:'Segoe UI',system-ui,sans-serif; padding:40px 20px; max-width:900px; margin:0 auto; }}
  .logo {{ text-align:center; margin-bottom:8px; }}
  .logo svg {{ width:500px; max-width:100%; }}
  .title {{ text-align:center; font-size:28px; font-weight:800; color:#fff; margin:8px 0 4px; font-family:monospace; }}
  .subtitle {{ text-align:center; font-size:13px; color:#8b949e; margin-bottom:32px; }}
  .card {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:24px; margin-bottom:20px; }}
  .card h2 {{ font-size:14px; text-transform:uppercase; letter-spacing:1px; color:#8b949e; margin-bottom:16px; font-family:monospace; }}
  .row {{ display:flex; gap:24px; flex-wrap:wrap; }}
  .metric {{ flex:1; min-width:130px; }}
  .metric .val {{ font-size:24px; font-weight:700; color:#fff; font-family:monospace; }}
  .metric .lbl {{ font-size:11px; color:#8b949e; text-transform:uppercase; letter-spacing:0.5px; margin-top:2px; }}
  .gor-bar {{ height:8px; background:#21262d; border-radius:4px; margin:16px 0; overflow:hidden; }}
  .gor-bar-fill {{ height:100%; background:{zone_color}; border-radius:4px; width:{bar_pct:.0f}%; transition:width 1s; }}
  .zone-tag {{ display:inline-block; padding:2px 10px; border-radius:4px; font-size:11px; font-weight:700; font-family:monospace; background:{zone_color}22; color:{zone_color}; border:1px solid {zone_color}44; }}
  table {{ width:100%; border-collapse:collapse; }}
  th {{ text-align:left; font-size:11px; color:#8b949e; padding:6px 8px; border-bottom:1px solid #21262d; text-transform:uppercase; }}
  td {{ padding:8px; font-size:13px; border-bottom:1px solid #21262d11; }}
  .path {{ border-left:3px solid #30363d; padding:12px 16px; margin:8px 0; }}
  .path.bull {{ border-left-color:#3fb950; }}
  .path.base {{ border-left-color:#d2991d; }}
  .path.bear {{ border-left-color:#f85149; }}
  .path h3 {{ font-size:14px; margin-bottom:4px; }}
  .path .prob {{ font-size:11px; color:#8b949e; }}
  .path .row {{ font-size:12px; color:#8b949e; margin:4px 0; }}
  .trigger {{ display:flex; align-items:flex-start; gap:12px; padding:10px 0; border-bottom:1px solid #21262d22; }}
  .trigger .dot {{ width:10px; height:10px; border-radius:50%; margin-top:4px; flex-shrink:0; }}
  .trigger .info {{ flex:1; }}
  .trigger .info strong {{ font-size:13px; color:#fff; }}
  .trigger .info p {{ font-size:11px; color:#8b949e; margin-top:2px; }}
  .trigger .prob {{ font-size:13px; font-weight:700; font-family:monospace; }}
  .footer {{ text-align:center; font-size:10px; color:#484f58; margin-top:40px; }}
  .footer a {{ color:#484f58; }}
</style>
</head>
<body>

<div class="logo">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 120" width="500">
    <rect width="800" height="120" fill="#0d1117"/>
    <text x="400" y="45" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#fff">DEEP-RISK</text>
    <text x="400" y="68" text-anchor="middle" font-family="monospace" font-size="13" font-weight="bold" fill="#ffa500">OPP</text>
    <text x="400" y="90" text-anchor="middle" font-family="monospace" font-size="8" fill="#555">GOR SEISMOGRAPH · CAPITAL FLOW SCAN · 11 FRAMEWORKS · 6 MASTERS</text>
  </svg>
</div>
<div class="title">18-Month Forward Outlook</div>
<div class="subtitle">{today} · Research Framework · Not Investment Advice</div>

<!-- NOWCAST -->
<div class="card">
  <h2>Nowcast</h2>
  <div class="row">
    <div class="metric"><div class="val">{gor_w:.1f}</div><div class="lbl">GOR (WTI)</div></div>
    <div class="metric"><div class="val">{gor_b:.1f}</div><div class="lbl">GOR (Brent)</div></div>
    <div class="metric"><div class="val">${gold:,.0f}</div><div class="lbl">Gold / oz</div></div>
    <div class="metric"><div class="val">${wti:.2f}</div><div class="lbl">WTI / bbl</div></div>
    <div class="metric"><div class="val">{dxy:.2f}</div><div class="lbl">DXY</div></div>
  </div>
  <div class="gor-bar"><div class="gor-bar-fill"></div></div>
  <div style="display:flex;gap:16px;align-items:center;font-size:12px;">
    <span class="zone-tag">{regime}</span>
    <span style="color:#8b949e;">10Y {us10y:.2f}% · 30Y {us30y:.2f}% · VIX {vix:.2f} · Fed {fed_rate:.2f}% · Fed BS ${fed_bs:.1f}T · M2 ${m2:.1f}T</span>
  </div>
  <div style="margin-top:12px;font-size:12px;">
    Allocation: <b style="color:{zone_color}">Oil {alloc.get('油气',0)}%</b> · Gold {alloc.get('黄金',0)}% · Cash {alloc.get('现金',0)}% · A-Shares {alloc.get('A股',0)}%
    <span style="margin-left:16px;color:{'#f85149' if wti<75 else '#3fb950'};">Hard Stop: {hardstop}</span>
  </div>
</div>

<!-- SIX MASTERS -->
<div class="card">
  <h2>Six Masters · Consensus: {defensive}/6 Defensive</h2>
  <table>
    <tr><th>Master</th><th>Posture</th><th>View</th></tr>
"""
    for name, posture, quip in masters:
        pcolor = "#f85149" if posture == "DEFENSIVE" else ("#3fb950" if "BULLISH" in posture else "#d2991d")
        html += f'    <tr><td style="font-weight:600;">{name}</td><td style="color:{pcolor};font-weight:700;">{posture}</td><td style="font-size:12px;color:#8b949e;">{quip}</td></tr>\n'

    html += """  </table>
</div>

<!-- THREE PATHS -->
<div class="card">
  <h2>Scenario Paths · 18 Months</h2>
"""
    paths = [
        ("bull", "Path A: Mean Reversion Rally", "25%", f"WTI ${wti:.0f} → ${wti_a:.0f} · Gold ${gold:.0f} → ${gold_a:.0f} · GOR {gor_w:.1f} → {gor_a:.1f} (Recovery)", "Oil allocation normalizes to 20-25%. Gold trim. Fed pivots or supply disruption triggers the move."),
        ("base", "Path B: Grinding Sideways", "45%", f"WTI ${wti:.0f} → ${wti_b:.0f} · Gold ${gold:.0f} → ${gold_b:.0f} · GOR {gor_w:.1f} → {gor_b_p:.1f} (Still Extreme)", "Iran peace holds. OPEC+ cheats. Warsh maintains hawkish posture through 2027. Cash heavy, wait."),
        ("bear", "Path C: Liquidity Crash → Forced Seller Bonanza", "30%", f"WTI ${wti:.0f} → ${wti_c:.0f} · Gold ${gold:.0f} → ${gold_c:.0f} · GOR {gor_w:.1f} → {gor_c:.1f} (All-Time Extreme)", "BOJ hike, US auction failure, or AI bubble burst triggers global freeze. THE buying opportunity of the cycle."),
    ]
    for cls, title, prob, nums, desc in paths:
        html += f"""  <div class="path {cls}">
    <h3>{title}</h3>
    <div class="prob">Estimated probability: {prob}</div>
    <div class="row">{nums}</div>
    <p style="font-size:12px;color:#8b949e;margin-top:4px;">{desc}</p>
  </div>
"""

    html += """</div>

<!-- TRIGGER WATCHLIST -->
<div class="card">
  <h2>Macro Trigger Watchlist</h2>
"""
    for trigger, catalyst, prob, color, implication in triggers:
        html += f"""  <div class="trigger">
    <div class="dot" style="background:{color};"></div>
    <div class="info"><strong>{trigger}</strong><p>{catalyst}</p></div>
    <div class="prob" style="color:{color};">{prob}</div>
  </div>
  <div style="font-size:11px;color:#8b949e;margin-left:22px;margin-bottom:8px;">-> {implication}</div>
"""

    html += """</div>

<!-- HISTORICAL ANALOGS -->
<div class="card">
  <h2>Historical Analogs · GOR Extreme -> Oil Recovery</h2>
  <table>
    <tr><th>Date</th><th>GOR Peak</th><th>Context</th><th>Oil Return</th><th>Duration</th><th>Path</th></tr>
"""
    for date, peak, ctx, ret, dur, detail in analogs:
        html += f'    <tr><td style="font-weight:600;">{date}</td><td>{peak}</td><td>{ctx}</td><td style="color:#3fb950;font-weight:700;">{ret}</td><td>{dur}</td><td style="font-size:11px;color:#8b949e;">{detail}</td></tr>\n'

    current_analog = "Current GOR exceeds all three historical analogs. Direction certainty is high — timing is the only unknown."
    html += f"""  </table>
  <p style="margin-top:12px;font-size:12px;color:#8b949e;">{current_analog}</p>
</div>

<!-- BASE CASE -->
<div class="card" style="background:linear-gradient(135deg,{zone_color}08,{zone_color}02);border-color:{zone_color}33;">
  <h2>Framework Base Case · Next 6 Months</h2>
  <p style="font-size:15px;color:#fff;line-height:1.8;">
    GOR at {gor_w:.1f} confirms oil remains deeply undervalued relative to gold.
    The Feb 2026 peak of 78.0 marked the extreme. We are 5 months into a mean reversion
    that historically takes 12-36 months.
  </p>
  <p style="font-size:15px;color:#fff;line-height:1.8;margin-top:8px;">
    <b style="color:{zone_color};">Direction is certain. Timing is not.</b>
    The framework provides the discipline to wait — not a date on the calendar.
    Cash is not cowardice. It's the option to buy when forced sellers appear.
  </p>
</div>

<div class="footer">
  Deep-Risk-OPP v{config.SKILL_VERSION} · Research Framework · <a href="https://github.com/Justinjchen-Cornell/Deep-Risk-OPP">GitHub</a><br>
  Not investment advice. Data: FRED, akshare, yfinance. Generated {today}.
</div>

</body>
</html>"""

    out_path = f"看板日志/report_{today}.html"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Report saved: {out_path}")
    print(f"  Open in browser: file:///{os.path.abspath(out_path)}")
