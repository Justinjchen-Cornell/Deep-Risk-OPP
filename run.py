#!/usr/bin/env python3
"""
Deep-Risk-OPP — CLI Entry Point
================================
Usage:
    python run.py --mode daily              Daily macro risk scan
    python run.py --mode weekly             Weekly change report
    python run.py --mode masters            Master consensus check
    python run.py --mode backtest           Historical backtest
    python run.py --mode dashboard          Launch interactive dashboard
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config


def get_gor_zone(gor_value):
    """Classify GOR value into zone."""
    for zone_name, zone_info in config.GOR_ZONES.items():
        if zone_info["min"] <= gor_value < zone_info["max"]:
            return zone_name
    return "unknown"


def get_allocation(zone, dxy=None, yield_10y=None, wti=None):
    """Compute allocation with risk corrections."""
    base = config.BASE_ALLOCATION.get(zone, config.BASE_ALLOCATION["fair_value"])
    alloc = dict(base)
    adjustments = []

    # Circuit breaker: WTI hard stop
    if wti is not None and wti < config.WTI_HARD_STOP:
        alloc["oil"] = min(alloc["oil"], 5)
        alloc["cash"] += alloc.get("oil", 0) - 5
        adjustments.append(f"WTI ${wti:.2f} < ${config.WTI_HARD_STOP}: oil <= 5%")

    # DXY correction
    if dxy is not None and dxy > config.DXY_THRESHOLD:
        adj = -10
        alloc["total"] = max(5, alloc["total"] + adj)
        adjustments.append(f"DXY {dxy:.2f} > {config.DXY_THRESHOLD}: total {adj:+d}%")

    # Yield correction
    if yield_10y is not None and yield_10y > config.YIELD_THRESHOLD:
        adj = -10
        alloc["total"] = max(5, alloc["total"] + adj)
        adjustments.append(f"10Y {yield_10y:.2f}% > {config.YIELD_THRESHOLD}%: total {adj:+d}%")

    return alloc, adjustments


def mode_daily():
    """Run daily macro risk scan with rich terminal output."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        from rich import box
        console = Console()
        use_rich = True
    except ImportError:
        use_rich = False

    # Load latest GOR data
    gor_path = config.GOR_LATEST
    if os.path.exists(gor_path):
        with open(gor_path, "r", encoding="utf-8") as f:
            gor_data = json.load(f)
    else:
        print("\n  No GOR data found. Run scripts/gor_daily.py first.")
        return

    gor_wti = gor_data.get("gor_wti", 0)
    gor_brent = gor_data.get("gor_brent", 0)
    gold = gor_data.get("data", {}).get("黄金期货", {}).get("price", 0)
    wti = gor_data.get("data", {}).get("WTI原油", {}).get("price", 0)
    dxy = gor_data.get("data", {}).get("美元指数DXY", {}).get("price", 0)
    ten_year = gor_data.get("data", {}).get("10Y美债收益率", {}).get("price", 0)
    vix = gor_data.get("data", {}).get("VIX恐慌指数", {}).get("price", 0)

    zone = get_gor_zone(gor_wti)
    alloc, adjustments = get_allocation(zone, dxy=dxy, yield_10y=ten_year, wti=wti)
    zone_color = {"extreme": "red", "recovery": "yellow", "fair_value": "green", "oil_bubble": "blue"}.get(zone, "white")

    if use_rich:
        # Header
        title = Text(f"Deep-Risk-OPP  ·  {datetime.now().strftime('%Y-%m-%d %H:%M')}", style="bold white")
        console.print(Panel(title, border_style="bright_black", padding=(0, 2)))
        console.print()

        # Market Data Table
        market = Table(box=box.ROUNDED, show_header=True, header_style="bold", border_style="bright_black")
        market.add_column("Metric", style="dim", width=12)
        market.add_column("Value", justify="right", width=14)
        market.add_column("Signal", width=20)
        market.add_row("GOR (WTI)", f"{gor_wti:.2f}", f"[{zone_color}]{config.GOR_ZONES[zone]['label']}[/{zone_color}]")
        market.add_row("GOR (Brent)", f"{gor_brent:.2f}", "")
        market.add_row("Gold", f"${gold:,.0f}", "")
        market.add_row("WTI", f"${wti:.2f}", f"{'[red]⚠ < $75 HARD STOP' if wti < 75 else ''}")
        market.add_row("DXY", f"{dxy:.2f}", f"{'[yellow]⚠ > 99' if dxy > 99 else ''}")
        market.add_row("10Y", f"{ten_year:.2f}%", f"{'[yellow]⚠ > 4.3%' if ten_year > 4.3 else ''}")
        market.add_row("VIX", f"{vix:.2f}", f"{'[green]✓ < 17 (straddle)' if vix < 17 else ''}{'[red]⚠ > 25' if vix > 25 else ''}")
        console.print(Panel(market, title="Market Data", border_style="bright_black"))

        # Allocation Table
        alloc_table = Table(box=box.ROUNDED, show_header=True, header_style="bold", border_style="bright_black")
        alloc_table.add_column("Asset", width=12)
        alloc_table.add_column("Allocation", justify="right", width=12)
        alloc_table.add_column("Status", width=20)
        alloc_table.add_row("🛢️ Oil", f"[bold]{alloc['oil']}%[/bold]", "[red]HARD STOP" if wti < 75 else "[green]ACTIVE")
        alloc_table.add_row("🥇 Gold", f"{alloc['gold']}%", "[gold3]PBoC floor locked[/gold3]")
        alloc_table.add_row("📈 A-Shares", f"{alloc['a_shares']}%", "dim <10% no hedge")
        alloc_table.add_row("💵 Cash", f"[bold]{alloc['cash']}%[/bold]", "")
        alloc_table.add_row("Total", f"[bold underline]{alloc['total']}%[/bold underline]", f"dim (base {70 if zone=='extreme' else 50 if zone=='recovery' else 30 if zone=='fair_value' else 10}%)")
        console.print(Panel(alloc_table, title="Allocation", border_style="bright_black"))

        # Alerts
        alerts = []
        if wti < 75: alerts.append(("[red]🔴 CRITICAL[/red]", f"WTI ${wti:.2f} < $75 — Hard stop. Oil ≤ 5%"))
        if vix > 25: alerts.append(("[red]🔴 CRITICAL[/red]", f"VIX {vix:.2f} > 25 — Vol explosion"))
        if dxy > 99: alerts.append(("[yellow]🟠 WARNING[/yellow]", f"DXY {dxy:.2f} > 99 — Strong USD"))
        if ten_year > 4.3: alerts.append(("[yellow]🟠 WARNING[/yellow]", f"10Y {ten_year:.2f}% > 4.3% — High rates"))
        if vix < 17: alerts.append(("[green]🟢 SIGNAL[/green]", f"VIX {vix:.2f} < 17 — SPY Straddle window"))
        if gor_wti >= 60: alerts.append(("[red]🔴 EXTREME[/red]", f"GOR {gor_wti:.1f} ≥ 60 — Historic divergence"))
        if adjustments:
            for adj in adjustments:
                alerts.append(("[dim]⚙️ ADJUST[/dim]", adj))

        if alerts:
            alert_table = Table(box=box.SIMPLE, show_header=False, border_style="bright_black")
            alert_table.add_column("Level", width=18)
            alert_table.add_column("Message")
            for level, msg in alerts:
                alert_table.add_row(level, msg)
            console.print(Panel(alert_table, title="Signals", border_style="bright_black"))
        console.print()
    else:
        # Fallback plain text
        print(f"\n  GOR(WTI)={gor_wti:.1f}  GOR(Brent)={gor_brent:.1f}  Gold=${gold:.0f}  WTI=${wti:.2f}")
        print(f"  DXY={dxy:.2f}  10Y={ten_year:.2f}%  VIX={vix:.2f}")
        print(f"  Zone: {config.GOR_ZONES[zone]['label']}  →  Oil={alloc['oil']}% Gold={alloc['gold']}% Cash={alloc['cash']}%")
        if wti < 75: print(f"  🚨 WTI ${wti:.2f} < $75 — HARD STOP ACTIVE")


def mode_weekly():
    """Generate weekly change report."""
    print("Weekly change report — compare with last week's data.")
    print("Run: python run.py --mode weekly --compare last-week")
    # Placeholder for weekly report generation
    pass


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


def mode_backtest(from_date=None, to_date=None, chart=False):
    """Run historical GOR regime-switching backtest."""
    from_date = from_date or "2020-01-01"
    to_date = to_date or datetime.now().strftime('%Y-%m-%d')

    print("=" * 70)
    print(f"  Deep-Risk-OPP Backtest  |  {from_date} → {to_date}")
    print("=" * 70)

    # Pull historical data via akshare (primary) or yfinance (fallback)
    print("\n  Pulling historical data...")
    gold_px = None
    wti_px = None

    # Try akshare first
    try:
        import akshare as ak
        import pandas as pd

        print("  Source: akshare")
        gold_df_raw = ak.futures_foreign_hist(symbol='GC')
        wti_df_raw = ak.futures_foreign_hist(symbol='CL')

        # akshare returns RangeIndex with 'date' and 'close' columns
        gold_df_raw['date'] = pd.to_datetime(gold_df_raw['date'])
        gold_df_raw = gold_df_raw.set_index('date').sort_index()
        wti_df_raw['date'] = pd.to_datetime(wti_df_raw['date'])
        wti_df_raw = wti_df_raw.set_index('date').sort_index()

        gold_px = gold_df_raw['close'].astype(float)
        wti_px = wti_df_raw['close'].astype(float)

        # Filter to date range
        mask_g = (gold_px.index >= from_date) & (gold_px.index <= to_date)
        mask_w = (wti_px.index >= from_date) & (wti_px.index <= to_date)
        gold_px = gold_px[mask_g]
        wti_px = wti_px[mask_w]

        print(f"  Gold: {len(gold_px)} rows, ${gold_px.min():.0f} – ${gold_px.max():.0f}")
        print(f"  WTI:  {len(wti_px)} rows, ${wti_px.min():.0f} – ${wti_px.max():.0f}")
    except Exception as e:
        print(f"  akshare failed: {e}, trying yfinance...")
        gold_px = None

    # Fallback to yfinance
    if gold_px is None or wti_px is None or len(gold_px) < 10:
        try:
            import yfinance as yf
            import time
            print("  Source: yfinance (fallback)")
            time.sleep(1)
            gold_df = yf.download("GC=F", start=from_date, end=to_date, progress=False)
            time.sleep(1)
            wti_df = yf.download("CL=F", start=from_date, end=to_date, progress=False)
            if not gold_df.empty and not wti_df.empty:
                gold_px = gold_df['Close'].squeeze()
                wti_px = wti_df['Close'].squeeze()
        except Exception as e:
            print(f"  yfinance fallback also failed: {e}")

    if gold_px is None or wti_px is None or len(gold_px) < 10:
        print("  ERROR: Could not pull sufficient historical data.")
        return

    # Align data
    common_idx = gold_px.index.intersection(wti_px.index)
    gold_px = gold_px[common_idx]
    wti_px = wti_px[common_idx]

    print(f"  Data points: {len(common_idx)} trading days")
    print(f"  Gold range: ${gold_px.min():.0f} – ${gold_px.max():.0f}")
    print(f"  WTI range:  ${wti_px.min():.0f} – ${wti_px.max():.0f}")

    # ============================================================
    # BACKTEST ENGINE
    # ============================================================
    # Simulate: daily regime check → allocation → P&L with 1-day lag

    regime_counts = {"extreme": 0, "recovery": 0, "fair_value": 0, "oil_bubble": 0}
    signal_changes = []
    pnl_oil = 0.0
    pnl_gold = 0.0
    pnl_cash = 0.0
    cash_return = 0.04 / 252  # ~4% annual cash return, daily

    prev_regime = None
    prev_oil_alloc = 0
    prev_gold_alloc = 0

    # Portfolio NAV simulation
    nav = 100.0
    nav_peak = 100.0
    max_drawdown = 0.0
    nav_history = [(common_idx[0], 100.0)] if chart else None
    bh_nav = 100.0
    bh_history = [(common_idx[0], 100.0)] if chart else None

    for i in range(1, len(common_idx)):
        date = common_idx[i]

        g = float(gold_px.iloc[i])
        w = float(wti_px.iloc[i])
        g_prev = float(gold_px.iloc[i-1])
        w_prev = float(wti_px.iloc[i-1])

        gor = g / w if w > 0 else 50

        # Regime
        if gor >= 45:
            regime = "extreme"
            base_oil, base_gold = 25, 20
        elif gor >= 30:
            regime = "recovery"
            base_oil, base_gold = 20, 15
        elif gor >= 20:
            regime = "fair_value"
            base_oil, base_gold = 10, 15
        else:
            regime = "oil_bubble"
            base_oil, base_gold = 0, 7

        if w < 75:
            base_oil = 5

        regime_counts[regime] += 1

        if regime != prev_regime and prev_regime is not None:
            signal_changes.append({
                "date": date.strftime('%Y-%m-%d'),
                "from": prev_regime, "to": regime,
                "gor": round(gor, 1), "wti": round(w, 1), "gold": round(g, 0),
            })

        # Daily NAV compound
        oil_ret = (w / w_prev - 1) if w_prev > 0 else 0
        gold_ret = (g / g_prev - 1) if g_prev > 0 else 0
        cash_ret = 0.04 / 252
        daily = (prev_oil_alloc * oil_ret + prev_gold_alloc * gold_ret + (100 - prev_oil_alloc - prev_gold_alloc) * cash_ret) / 100
        nav = nav * (1 + daily)

        # 60/40 buy-and-hold benchmark
        bh_daily = (0.6 * oil_ret + 0.4 * gold_ret)
        bh_nav = bh_nav * (1 + bh_daily)

        # Max drawdown tracking
        if nav > nav_peak:
            nav_peak = nav
        dd = (nav - nav_peak) / nav_peak
        if dd < max_drawdown:
            max_drawdown = dd

        if chart:
            nav_history.append((date, nav))
            bh_history.append((date, bh_nav))

        prev_regime = regime
        prev_oil_alloc = base_oil
        prev_gold_alloc = base_gold

    # ============================================================
    # RESULTS
    # ============================================================
    total_return = nav / 100 - 1
    n_years = (common_idx[-1] - common_idx[0]).days / 365.25
    ann_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0

    # Benchmark: 60/40 oil/gold buy-and-hold
    wti_bh = float(wti_px.iloc[-1] / wti_px.iloc[0] - 1)
    gold_bh = float(gold_px.iloc[-1] / gold_px.iloc[0] - 1)
    bh_return = 0.6 * wti_bh + 0.4 * gold_bh
    ann_bh = (1 + bh_return) ** (1 / n_years) - 1 if n_years > 0 else 0

    # Average allocation over the period
    total_days = len(common_idx)
    avg_oil = sum(base_oil for _ in range(total_days)) / total_days if total_days > 0 else 0
    avg_gold = (regime_counts['extreme']*20 + regime_counts['recovery']*15 + regime_counts['fair_value']*15 + regime_counts['oil_bubble']*7) / total_days
    avg_cash = 100 - avg_gold - 10  # ~10% avg oil

    print(f"""
  {'='*64}
                      BACKTEST RESULTS
  {'='*64}
    Period:         {from_date} → {to_date}
    Trading days:   {len(common_idx)}
    Years:          {n_years:.1f}

    GOR Strategy:   {total_return:+.1%} total  |  {ann_return:+.1%}/yr
    60/40 B&H:      {bh_return:+.1%} total  |  {ann_bh:+.1%}/yr
    Alpha:          {total_return - bh_return:+.1%}

    Avg Allocation: {avg_gold:.0f}% Gold | ~{avg_oil:.0f}% Oil | ~{avg_cash:.0f}% Cash
    Max Drawdown:   {max_drawdown:+.1%}
  {'='*64}
    Regime Distribution:
      Extreme:      {regime_counts['extreme']:>5d} days  ({regime_counts['extreme']/total_days*100:5.1f}%)
      Recovery:     {regime_counts['recovery']:>5d} days  ({regime_counts['recovery']/total_days*100:5.1f}%)
      Fair Value:   {regime_counts['fair_value']:>5d} days  ({regime_counts['fair_value']/total_days*100:5.1f}%)
      Oil Bubble:   {regime_counts['oil_bubble']:>5d} days  ({regime_counts['oil_bubble']/total_days*100:5.1f}%)
  {'='*64}
    Signal Changes: {len(signal_changes)}
  {'='*64}
""")

    # Print recent signal changes
    if signal_changes:
        print("  Recent Signal Transitions:")
        for sc in signal_changes[-8:]:
            arrow = "↑" if sc['to'] == 'extreme' else ("↓" if sc['to'] == 'oil_bubble' else "→")
            print(f"    {sc['date']}  {sc['from']:>12s} → {sc['to']:<12s} {arrow}  GOR={sc['gor']}  WTI=${sc['wti']}")

    # ============================================================
    # CHART (if --chart flag)
    # ============================================================
    if chart and nav_history:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        fig, ax = plt.subplots(figsize=(14, 6), dpi=120)
        fig.patch.set_facecolor('#0d1117')
        ax.set_facecolor('#0d1117')

        dates_nav, vals_nav = zip(*nav_history)
        dates_bh, vals_bh = zip(*bh_history)

        ax.plot(dates_nav, vals_nav, color='#ffa500', linewidth=2.0, label=f'GOR Strategy ({ann_return:+.1%}/yr)')
        ax.plot(dates_bh, vals_bh, color='#888888', linewidth=1.2, linestyle='--', label=f'60/40 B&H ({ann_bh:+.1%}/yr)')
        ax.axhline(y=100, color='#ffffff', linewidth=0.5, alpha=0.2)

        # Style
        ax.set_title(f'Deep-Risk-OPP Backtest  |  {from_date} → {to_date}', color='#ffffff', fontsize=14, fontfamily='monospace', pad=12)
        ax.legend(loc='upper left', facecolor='#1a1a2e', edgecolor='#333', labelcolor='#ccc', fontsize=10)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#333')
        ax.spines['bottom'].set_color('#333')
        ax.tick_params(colors='#888', labelsize=9)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}'))
        ax.grid(True, alpha=0.08, color='#ffffff')
        ax.set_ylabel('NAV (base=100)', color='#aaa', fontsize=10)

        chart_path = f"看板日志/backtest_chart_{from_date}_to_{to_date}.png"
        fig.savefig(chart_path, dpi=150, facecolor='#0d1117', bbox_inches='tight', pad_inches=0.4)
        plt.close(fig)
        print(f"  Chart saved: {chart_path}")

    # ============================================================
    # SAVE JSON
    # ============================================================
    result = {
        "from": from_date, "to": to_date,
        "trading_days": len(common_idx), "years": round(n_years, 1),
        "strategy": {"total": round(total_return, 4), "annualized": round(ann_return, 4)},
        "benchmark_6040": {"total": round(bh_return, 4), "annualized": round(ann_bh, 4)},
        "max_drawdown": round(max_drawdown, 4),
        "alpha": round(total_return - bh_return, 4),
        "regime_distribution": regime_counts,
        "signal_changes": signal_changes[-20:],
    }
    out_path = f"看板日志/backtest_{from_date}_to_{to_date}.json"
    os.makedirs("看板日志", exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(f"\n  Saved: {out_path}")


def mode_dashboard():
    """Launch interactive dashboard."""
    print("Interactive dashboard — launching...")
    try:
        import streamlit as st
        print("Streamlit available. Run: streamlit run dashboard.py")
    except ImportError:
        print("Streamlit not installed. pip install streamlit")


def main():
    parser = argparse.ArgumentParser(
        description="Deep-Risk-OPP: Macro early-warning system"
    )
    parser.add_argument(
        "--mode",
        choices=["daily", "weekly", "masters", "backtest", "dashboard"],
        default="daily",
        help="Operating mode (default: daily)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Export decision card as JSON file",
    )
    parser.add_argument(
        "--frameworks",
        type=str,
        default=None,
        help="Comma-separated framework IDs to load (e.g. 01,05,11)",
    )
    parser.add_argument(
        "--compare",
        type=str,
        default=None,
        help="Comparison period for weekly mode",
    )
    parser.add_argument(
        "--from",
        type=str,
        dest="from_date",
        default="2020-01-01",
        help="Backtest start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--to",
        type=str,
        dest="to_date",
        default=None,
        help="Backtest end date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--chart",
        action="store_true",
        default=False,
        help="Generate NAV comparison chart (backtest mode)",
    )

    args = parser.parse_args()

    modes = {
        "daily": mode_daily,
        "weekly": mode_weekly,
        "masters": mode_masters,
        "backtest": mode_backtest,
        "dashboard": mode_dashboard,
    }

    print(f"\n  Deep-Risk-OPP v{config.SKILL_VERSION}")
    print(f"  Mode: {args.mode}")
    print()

    if args.mode == "backtest":
        mode_backtest(from_date=args.from_date, to_date=args.to_date, chart=args.chart)
    else:
        modes[args.mode]()


if __name__ == "__main__":
    main()