"""
Deep-Risk-OPP — mode sentiment (P1-1 拆分自 run.py)
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modes.common import get_gor_zone, get_gor_blend, check_dynamic_hard_stop, get_allocation

def mode_sentiment():
    """Market sentiment scan — Adanos Reddit data + divergence detection."""
    import urllib.request

    api_key = os.getenv('ADANOS_API_KEY')
    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv('ADANOS_API_KEY')
        except: pass

    if not api_key:
        print("  ADANOS_API_KEY not set. Add to .env")
        return

    headers = {'x-api-key': api_key, 'User-Agent': 'Deep-Risk-OPP/2.0'}
    base = 'https://api.adanos.org/reddit/stocks/v1'
    tickers = ['QQQ','NVDA','AAPL','MSFT','SPY','TSLA','META','AMZN','GOOGL','IWM','TLT','GLD','XLE','EEM']

    print("=" * 66)
    print("  Deep-Risk-OPP  |  Market Sentiment Scan  |  Adanos Reddit")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 66)

    # Fetch market-wide
    market = {}
    try:
        req = urllib.request.Request(f'{base}/market-sentiment', headers=headers)
        market = json.loads(urllib.request.urlopen(req, timeout=15).read())
    except Exception as e:
        print(f"  Market sentiment API error: {e}")

    # Fetch individual tickers
    stocks = []
    for t in tickers:
        try:
            req = urllib.request.Request(f'{base}/stock/{t}', headers=headers)
            d = json.loads(urllib.request.urlopen(req, timeout=10).read())
            d['ticker'] = t
            stocks.append(d)
        except: pass

    if not stocks:
        print("  No stock data returned.")
        return

    # ── Sentiment Heatmap ───────────────────────────────────
    print(f"\n  {'Ticker':<8s} {'Buzz':>6s} {'Trend':<10s} {'Bull':>5s} {'Bear':>5s} {'Signal':<20s} {'Heat'}")
    print(f"  {'-'*7:<8s} {'-'*5:>6s} {'-'*9:<10s} {'-'*4:>5s} {'-'*4:>5s} {'-'*19:<20s} {'-'*8}")

    divergences = []
    for s in sorted(stocks, key=lambda x: x.get('buzz_score') or 0, reverse=True):
        buzz = s.get('buzz_score') or 0
        bull = s.get('bullish_pct') or 0
        bear = s.get('bearish_pct') or 0
        trend = s.get('trend') or '?'
        sent = s.get('sentiment_score') or 0

        # Signal interpretation
        spread = bull - bear
        if spread > 15: signal = "Strong bullish"
        elif spread > 5: signal = "Mild bullish"
        elif spread > -5: signal = "Dead even — watch"
        elif spread > -15: signal = "Mild bearish"
        else: signal = "Strong bearish"

        # Divergence detection: buzz high + sentiment flat = distribution
        if buzz > 70 and abs(sent) < 0.02:
            signal = "!! Distribution?"
            divergences.append(f"{s['ticker']}: Buzz={buzz:.0f} but sentiment flat ({sent:+.3f}) - distribution likely")

        # Divergence: trend falling + still bullish = late-stage
        if trend == 'falling' and bull > bear:
            signal = "!! Late-stage?"
            divergences.append(f"{s['ticker']}: Trend falling but still bullish (Bulls {bull}% vs Bears {bear}%)")

        # Heat bar
        bar_len = int(buzz / 5)
        bar = '#' * min(bar_len, 16)
        color = '[+]' if sent > 0.03 else ('[~]' if sent > 0 else '[!]')

        print(f"  {s['ticker']:<8s} {buzz:>5.0f}  {trend:<10s} {bull:>4}% {bear:>4}% {signal:<20s} {color} {bar}")

    # ── Market Overview ─────────────────────────────────────
    if market:
        mkt_buzz = market.get('buzz_score', 0)
        mkt_sent = market.get('sentiment_score', 0)
        mkt_bull = market.get('bullish_pct', 0)
        mkt_bear = market.get('bearish_pct', 0)
        trend_hist = market.get('trend_history', [])
        print(f"\n  Market-wide:  Buzz={mkt_buzz:.0f}  Sentiment={mkt_sent:+.3f}  Bulls={mkt_bull}%  Bears={mkt_bear}%")
        if trend_hist:
            print(f"  Buzz 7-day:  {' → '.join(f'{v:.0f}' for v in trend_hist)}")

    # ── Divergence Alerts ───────────────────────────────────
    if divergences:
        print(f"\n  !! DIVERGENCE SIGNALS:")
        for d in divergences:
            print(f"     {d}")
    else:
        print(f"\n  -- No major divergences detected.")

    # ── Integration with GOR ────────────────────────────────
    gor_path = config.GOR_LATEST
    if os.path.exists(gor_path):
        with open(gor_path, 'r', encoding='utf-8') as f:
            gor_data = json.load(f)
        gor_w = gor_data.get('gor_wti', 0)
        regime = gor_data.get('regime', '?')

        # The key cross-check: sentiment vs macro reality
        if market:
            mkt_buzz = market.get('buzz_score', 0)
            print(f"\n  ── Sentiment × GOR Cross-Check ──")
            if gor_w >= 45 and mkt_buzz < 30:
                print(f"  !! GOR={gor_w:.1f} (extreme) but market buzz is LOW ({mkt_buzz:.0f}).")
                print(f"     Historically, low buzz during extreme GOR = complacency before repricing.")
            elif gor_w >= 45 and mkt_buzz > 60:
                print(f"  ** GOR={gor_w:.1f} (extreme) AND market buzz is HIGH ({mkt_buzz:.0f}).")
                print(f"     This is the 'everyone sees it' phase - the move may already be priced.")
            else:
                print(f"  -- GOR={gor_w:.1f} in {regime}. Sentiment in normal range.")


    # P2: 情绪数据并入主 JSON
    payload = {
        "updated": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "ok": bool(market or stocks),
        "market": {
            "buzz_score": round(float(market.get('buzz_score', 0)), 1),
            "sentiment_score": round(float(market.get('sentiment_score', 0)), 3),
            "bullish_pct": market.get('bullish_pct'),
            "bearish_pct": market.get('bearish_pct'),
        },
        "tickers": [
            {
                "ticker": t.get('ticker'),
                "buzz": round(float(t.get('buzz_score') or 0), 1),
                "sentiment": round(float(t.get('sentiment_score') or 0), 3),
                "bullish_pct": t.get('bullish_pct'),
                "bearish_pct": t.get('bearish_pct'),
                "trend": t.get('trend'),
            } for t in sorted(stocks, key=lambda x: x.get('buzz_score') or 0, reverse=True)[:10]
        ],
        "divergences": divergences,
    }
    try:
        gpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gor_latest.json')
        with open(gpath, 'r', encoding='utf-8') as f:
            gd = json.load(f)
        gd['sentiment'] = payload
        with open(gpath, 'w', encoding='utf-8') as f:
            json.dump(gd, f, ensure_ascii=False, indent=2)
        print(f"  ✅ Sentiment merged into gor_latest.json ({len(payload['tickers'])} tickers, {len(divergences)} divergences)")
    except Exception as e:
        print(f"  !! Sentiment merge failed: {e}")
    print()
