#!/usr/bin/env python3
"""
Wayfinder — CLI
================
  python run.py --mode scan      Today's flow compass
  python run.py --mode report    Standalone HTML flow report
"""

import argparse, json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))


def mode_scan():
    from scripts.flow_scanner import scan
    data = scan()
    t, d, s = data['total'], data['direction'], data['speed']

    def fmt(v, spec='.1f'):
        if v is None: return 'N/A'
        try: return f'{v:{spec}}'
        except: return str(v)

    print(f"""
  Wayfinder · Flow Compass · {data['date']}
  {'='*56}

  TOTAL VOLUME    {t['trend']}
    Fed BS:         ${fmt(t.get('fed_balance_trillion'),'.1f')}T
    M2:             ${fmt(t.get('m2_trillion'),'.1f')}T
    SOFR:           {fmt(t.get('sofr'),'.2f')}%
    ECB BS:         EUR {fmt(t.get('ecb_balance_trillion_eur'),'.1f')}T
    Global CB:      ${fmt(t.get('global_cb_trillion_usd'),'.1f')}T (Fed+ECB)
    Monthly Deficit: ${fmt(t.get('us_monthly_deficit_billion'),'.0f')}B

  DIRECTION       {d['signal']}
    DXY:            {fmt(d.get('dxy'),'.2f')}
    2Y/10Y/30Y:     {fmt(d.get('us2y'),'.2f')}% / {fmt(d.get('us10y'),'.2f')}% / {fmt(d.get('us30y'),'.2f')}%
    10Y-2Y Spread:  {fmt(d.get('yield_curve_10y2y'),'+.2f')}%
    China-US Spr:   {fmt(d.get('china_us_spread'),'+.2f')}% (CNY10Y-USD10Y)
    Fed Rate:       {fmt(d.get('fed_rate'),'.2f')}%
    Debt:           ${fmt(d.get('fed_debt_trillion'),'.1f')}T
    CN Gold:        {d.get('china_gold_reserve_tonnes') or 'N/A'} tonnes

  SPEED           {s['signal']}
    VIX:            {fmt(s.get('vix'),'.2f')}
    HY Spread:      {fmt(s.get('hy_spread_bp'),'.0f')}bp
    IG Spread:      {fmt(s.get('ig_spread_bp'),'.0f')}bp
    EM Spread:      {fmt(s.get('em_spread_bp'),'.0f')}bp
    TED Spread:     {fmt(s.get('ted_spread'),'.2f')}
    Swap Basis:     {fmt(s.get('swap_basis'),'+.2f')}% (SOFR-FF)
    JPY Vol:        {fmt(s.get('jpy_vol_annualized'),'.1f')}% ann

  {'='*56}
  COMPASS: {data['compass']}
  {'='*56}
""")


def mode_report():
    from scripts.flow_scanner import scan
    data = scan()
    t, d, s = data['total'], data['direction'], data['speed']
    today = data['date']

    # Gauge colors
    total_color = "#f85149" if t['trend'] == 'CONTRACTING' else "#3fb950"
    dir_color = "#f85149" if d['signal'] == 'CENTRIPETAL' else ("#3fb950" if d['signal'] == 'CENTRIFUGAL' else "#d2991d")
    spd_color = "#f85149" if s['signal'] == 'PANIC' else ("#d2991d" if s['signal'] == 'ELEVATED' else "#3fb950")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Wayfinder · Flow Compass · {today}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{background:#0d1117;color:#c9d1d9;font-family:system-ui,sans-serif;padding:40px 20px;max-width:800px;margin:0 auto;}}
  .logo{{text-align:center;margin-bottom:24px;}}
  .logo h1{{font-family:monospace;font-size:28px;color:#fff;}}
  .logo p{{font-size:12px;color:#8b949e;}}
  .gauges{{display:flex;gap:20px;margin-bottom:24px;flex-wrap:wrap;}}
  .gauge{{flex:1;min-width:200px;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;text-align:center;}}
  .gauge .label{{font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:#8b949e;margin-bottom:8px;}}
  .gauge .value{{font-size:20px;font-weight:800;font-family:monospace;}}
  .card{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;margin-bottom:16px;}}
  .card h2{{font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#8b949e;margin-bottom:12px;font-family:monospace;}}
  .row{{display:flex;flex-wrap:wrap;gap:12px;}}
  .metric{{flex:1;min-width:100px;}}
  .metric .val{{font-size:16px;font-weight:700;color:#fff;font-family:monospace;}}
  .metric .lbl{{font-size:10px;color:#8b949e;text-transform:uppercase;}}
  .compass{{background:linear-gradient(135deg,{total_color}10,{dir_color}10);border:1px solid;border-color:{total_color}33;border-radius:8px;padding:24px;text-align:center;margin-bottom:16px;}}
  .compass .heading{{font-size:18px;font-weight:800;font-family:monospace;color:#fff;}}
  .compass .sub{{font-size:13px;color:#8b949e;margin-top:4px;}}
  .footer{{text-align:center;font-size:10px;color:#484f58;margin-top:32px;}}
</style>
</head>
<body>
<div class="logo">
  <h1>WAYFINDER</h1>
  <p>Capital Flow Compass · {today} · Not Investment Advice</p>
</div>

<div class="gauges">
  <div class="gauge">
    <div class="label">Total Volume</div>
    <div class="value" style="color:{total_color};">{t['trend']}</div>
  </div>
  <div class="gauge">
    <div class="label">Direction</div>
    <div class="value" style="color:{dir_color};">{d['signal']}</div>
  </div>
  <div class="gauge">
    <div class="label">Speed</div>
    <div class="value" style="color:{spd_color};">{s['signal']}</div>
  </div>
</div>

<div class="compass">
  <div class="heading">{data['compass']}</div>
</div>

<div class="card">
  <h2>Total Volume</h2>
  <div class="row">
    <div class="metric"><div class="val">${t.get('fed_balance_trillion','?'):.1f}T</div><div class="lbl">Fed Balance Sheet</div></div>
    <div class="metric"><div class="val">${t.get('m2_trillion','?'):.1f}T</div><div class="lbl">M2 Money Supply</div></div>
    <div class="metric"><div class="val">{t.get('sofr','?'):.2f}%</div><div class="lbl">SOFR</div></div>
    <div class="metric"><div class="val">EUR {t.get('ecb_balance_trillion_eur','?'):.1f}T</div><div class="lbl">ECB Balance Sheet</div></div>
    <div class="metric"><div class="val">${t.get('us_monthly_deficit_billion','?'):.0f}B</div><div class="lbl">Monthly Deficit</div></div>
  </div>
</div>

<div class="card">
  <h2>Direction</h2>
  <div class="row">
    <div class="metric"><div class="val">{d.get('dxy','?'):.2f}</div><div class="lbl">DXY</div></div>
    <div class="metric"><div class="val">{d.get('us10y','?'):.2f}%</div><div class="lbl">US 10Y</div></div>
    <div class="metric"><div class="val">{d.get('us30y','?'):.2f}%</div><div class="lbl">US 30Y</div></div>
    <div class="metric"><div class="val">{d.get('fed_rate','?'):.2f}%</div><div class="lbl">Fed Funds Rate</div></div>
    <div class="metric"><div class="val">{d.get('china_gold_reserve_tonnes','?')}t</div><div class="lbl">China Gold Reserve</div></div>
    <div class="metric"><div class="val">${d.get('fed_debt_trillion','?'):.1f}T</div><div class="lbl">US Federal Debt</div></div>
  </div>
</div>

<div class="card">
  <h2>Speed</h2>
  <div class="row">
    <div class="metric"><div class="val">{s.get('vix','?'):.2f}</div><div class="lbl">VIX</div></div>
    <div class="metric"><div class="val">{s.get('hy_spread_bp','?'):.0f}bp</div><div class="lbl">HY Spread</div></div>
    <div class="metric"><div class="val">{s.get('ig_spread_bp','?'):.0f}bp</div><div class="lbl">IG Spread</div></div>
    <div class="metric"><div class="val">{s.get('ted_spread','?'):.2f}</div><div class="lbl">TED Spread</div></div>
    <div class="metric"><div class="val">{s.get('em_spread_bp','?'):.0f}bp</div><div class="lbl">EM Spread</div></div>
  </div>
</div>

<div class="footer">
  Wayfinder · Research Framework · <a href="https://github.com/Justinjchen-Cornell/Deep-Risk-OPP" style="color:#484f58;">Deep-Risk-OPP</a><br>
  Not investment advice. Data: FRED, yfinance, akshare.
</div>
</body></html>"""

    out = f"reports/flow_report_{today}.html"
    os.makedirs("reports", exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Report saved: {out}")


def main():
    parser = argparse.ArgumentParser(description="Wayfinder — Capital Flow Compass")
    parser.add_argument("--mode", choices=["scan", "report"], default="scan")
    args = parser.parse_args()

    print(f"\n  Wayfinder · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    {"scan": mode_scan, "report": mode_report}[args.mode]()


if __name__ == "__main__":
    main()