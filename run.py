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
    """Run daily macro risk scan."""
    print("=" * 60)
    print("  Deep-Risk-OPP  |  Daily Macro Risk Scan")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

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

    # Output decision card
    print(f"""
  ┌─────────────────────────────────────┐
  │  GOR(WTI):   {gor_wti:.2f}
  │  GOR(Brent): {gor_brent:.2f}
  │  Zone:       {config.GOR_ZONES[zone]['label']}
  │  Gold:       ${gold:,.2f}
  │  WTI:        ${wti:,.2f}
  │  DXY:        {dxy:.2f}
  │  10Y:        {ten_year:.2f}%
  │  VIX:        {vix:.2f}
  ├─────────────────────────────────────┤
  │  Total:      {alloc['total']}%
  │  Oil:        {alloc['oil']}%
  │  Gold:       {alloc['gold']}%
  │  A-Shares:   {alloc['a_shares']}%
  │  Copper:     {alloc.get('copper', 0)}%
  │  Cash:       {alloc['cash']}%
  └─────────────────────────────────────┘
""")

    if adjustments:
        print("  Adjustments:")
        for adj in adjustments:
            print(f"    - {adj}")

    # Alerts
    alerts = []
    if wti < config.WTI_HARD_STOP:
        alerts.append(f"CRITICAL: WTI ${wti:.2f} < ${config.WTI_HARD_STOP} — Hard stop active")
    if dxy > config.DXY_THRESHOLD:
        alerts.append(f"WARNING: DXY {dxy:.2f} > {config.DXY_THRESHOLD} — Strong USD")
    if ten_year > config.YIELD_THRESHOLD:
        alerts.append(f"WARNING: 10Y {ten_year:.2f}% > {config.YIELD_THRESHOLD}% — High rates")
    if vix > config.VIX_PANIC:
        alerts.append(f"CRITICAL: VIX {vix:.2f} > {config.VIX_PANIC} — Panic mode")

    if alerts:
        print("\n  Alerts:")
        for a in alerts:
            print(f"    {a}")

    print()


def mode_weekly():
    """Generate weekly change report."""
    print("Weekly change report — compare with last week's data.")
    print("Run: python run.py --mode weekly --compare last-week")
    # Placeholder for weekly report generation
    pass


def mode_masters():
    """Run master consensus check."""
    print("Master consensus check — loading 6 masters...")
    # Placeholder for master consensus engine
    print("See 08-六大师映射.md for detailed master mappings.")


def mode_backtest():
    """Run historical backtest."""
    print("Historical backtest — GOR regime-switching performance.")
    # Placeholder for backtest engine
    print("See 看板日志/ for live signal track record.")


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

    modes[args.mode]()


if __name__ == "__main__":
    main()