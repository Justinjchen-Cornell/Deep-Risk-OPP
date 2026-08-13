"""
Deep-Risk-OPP — mode daily (P1-1 拆分自 run.py)
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modes.common import get_gor_zone, get_gor_blend, check_dynamic_hard_stop, get_allocation

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

    # Load WTI history for dynamic hard stop
    wti_history = None
    if os.path.exists(config.WTI_HISTORY):
        try:
            with open(config.WTI_HISTORY, "r", encoding="utf-8") as f:
                wti_history = json.load(f)
        except Exception:
            pass

    zone = get_gor_zone(gor_wti)
    alloc, adjustments, hard_stop_active, shock_type = get_allocation(
        zone, dxy=dxy, yield_10y=ten_year, wti=wti, gor=gor_wti, vix=vix, wti_history=wti_history
    )
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
        alloc_table.add_row("🛢️ Oil", f"[bold]{alloc['oil']}%[/bold]",
                            f"[red]HARD STOP: {shock_type}[/red]" if hard_stop_active else
                            (f"[yellow]Supply shock override[/yellow]" if shock_type == "supply_shock" else "[green]ACTIVE[/green]"))
        alloc_table.add_row("🥇 Gold", f"{alloc['gold']}%", "[gold3]PBoC floor locked[/gold3]")
        alloc_table.add_row("📈 A-Shares", f"{alloc['a_shares']}%", "dim <10% no hedge")
        alloc_table.add_row("💵 Cash", f"[bold]{alloc['cash']}%[/bold]", "")
        alloc_table.add_row("Total", f"[bold underline]{alloc['total']}%[/bold underline]", f"dim (base {70 if zone=='extreme' else 50 if zone=='recovery' else 30 if zone=='fair_value' else 10}%)")
        console.print(Panel(alloc_table, title="Allocation", border_style="bright_black"))

        # Alerts
        alerts = []
        if hard_stop_active:
            alerts.append(("[red]🔴 CRITICAL[/red]", f"Dynamic hard stop: {shock_type}"))
        if shock_type == "supply_shock":
            alerts.append(("[yellow]🟡 OVERRIDE[/yellow]", f"Supply shock detected: hard stop overridden. Oil kept at framework level."))
        if wti < config.WTI_ABSOLUTE_FLOOR:
            alerts.append(("[red]🔴 ABSOLUTE FLOOR[/red]", f"WTI ${wti:.2f} < ${config.WTI_ABSOLUTE_FLOOR} — hard stop no exceptions"))
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
        print(f"  Zone: {config.GOR_ZONES[zone]['label']}  ->  Oil={alloc['oil']}% Gold={alloc['gold']}% Cash={alloc['cash']}%")
        if hard_stop_active:
            print(f"  🚨 DYNAMIC HARD STOP ACTIVE ({shock_type}) — Oil ≤ 5%")
        elif shock_type == "supply_shock":
            print(f"  🟡 SUPPLY SHOCK OVERRIDE — Hard stop suppressed, oil kept at framework level")
