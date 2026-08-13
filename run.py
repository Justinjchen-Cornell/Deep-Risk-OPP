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

(P1-1 重构: 轻量分发器。各模式实现位于 modes/ 包。)
"""

import argparse
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config


def main():
    parser = argparse.ArgumentParser(
        description="Deep-Risk-OPP: Macro early-warning system"
    )
    parser.add_argument(
        "--mode",
        choices=["daily", "weekly", "masters", "backtest", "dashboard", "forecast", "report", "sentiment"],
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

    from modes import (backtest, daily, dashboard, forecast, masters,
                       report, sentiment, weekly)

    handlers = {
        "daily": daily.mode_daily,
        "weekly": weekly.mode_weekly,
        "masters": masters.mode_masters,
        "backtest": backtest.mode_backtest,
        "dashboard": dashboard.mode_dashboard,
        "forecast": forecast.mode_forecast,
        "report": report.mode_report,
        "sentiment": sentiment.mode_sentiment,
    }

    print(f"\n  Deep-Risk-OPP v{config.SKILL_VERSION}")
    print(f"  Mode: {args.mode}")
    print()

    if args.mode == "backtest":
        backtest.mode_backtest(from_date=args.from_date, to_date=args.to_date, chart=args.chart)
    else:
        handlers[args.mode]()


if __name__ == "__main__":
    main()
