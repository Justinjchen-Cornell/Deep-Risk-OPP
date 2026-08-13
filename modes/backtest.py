"""
Deep-Risk-OPP — mode backtest (P1-1 拆分自 run.py)
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modes.common import get_gor_zone, get_gor_blend, check_dynamic_hard_stop, get_allocation

def mode_backtest(from_date=None, to_date=None, chart=False):
    """Run historical GOR regime-switching backtest."""
    from_date = from_date or "2020-01-01"
    to_date = to_date or datetime.now().strftime('%Y-%m-%d')

    print("=" * 70)
    print(f"  Deep-Risk-OPP Backtest  |  {from_date} -> {to_date}")
    print("=" * 70)

    # Pull historical data via akshare (primary) or yfinance (fallback)
    print("\n  Pulling historical data...")
    gold_px = None
    wti_px = None

    # Load cached history if present (avoids API rate limits on re-runs)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CACHE = os.path.join(BASE_DIR, "看板日志", "backtest_cache", "gold_wti_history.csv")
    try:
        import pandas as pd
        if os.path.exists(CACHE):
            c = pd.read_csv(CACHE, parse_dates=['date']).set_index('date')
            g_mask = (c.index >= from_date) & (c.index <= to_date)
            gold_px = c['gold'][g_mask]
            wti_px = c['wti'][g_mask]
            cache_ok = str(c.index[0].date()) <= from_date   # 缓存起点必须早于请求起点
            if len(gold_px) > 100 and cache_ok:
                print(f"  Source: local cache ({os.path.basename(CACHE)}, {c.index[0].date()} -> {c.index[-1].date()})")
                print(f"  Gold: {len(gold_px)} rows | WTI: {len(wti_px)} rows")
    except Exception as e:
        print(f"  Cache load failed: {e}")

    # Try Sina GlobalFutures first -- XAU spot since 2006, CL since 1996
    try:
        import json as _json
        import urllib.request as _ur
        import pandas as pd
        import re as _re
        def _sina(sym):
            url = ("https://stock2.finance.sina.com.cn/futures/api/jsonp.php/"
                   "var%20x=/GlobalFuturesService.getGlobalFuturesDailyKLine?symbol=" + sym)
            req = _ur.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            raw = _ur.urlopen(req, timeout=25).read().decode('utf-8', errors='ignore')
            m = _re.search(r'\((\[.*\])\)', raw)
            rows = _json.loads(m.group(1))
            df = pd.DataFrame(rows)
            df['date'] = pd.to_datetime(df['date'])
            return df.set_index('date')['close'].astype(float).sort_index()
        _g = _sina('XAU')
        _w = _sina('CL')
        if len(_g) > 100:
            mask_g = (_g.index >= from_date) & (_g.index <= to_date)
            mask_w = (_w.index >= from_date) & (_w.index <= to_date)
            gold_px = _g[mask_g]
            wti_px = _w[mask_w]
            print(f"  Source: Sina GlobalFutures (XAU spot + CL)")
            print(f"  Gold: {len(gold_px)} rows, ${gold_px.min():.0f} - ${gold_px.max():.0f} | from {gold_px.index[0].date()}")
            print(f"  WTI:  {len(wti_px)} rows, ${wti_px.min():.0f} - ${wti_px.max():.0f} | from {wti_px.index[0].date()}")
    except Exception as e:
        print(f"  Sina failed: {e}, trying FRED+yfinance...")

    # Try FRED WTI (since 1986) + yfinance GC=F gold (since 2000) -- fallback combo
    if gold_px is None or wti_px is None or len(gold_px) < 100:
        try:
            from data_pipeline.common import _init_fred
            import pandas as pd
            fred = _init_fred()
            wti_s = fred.get_series('DCOILWTICO') if fred else None   # WTI Spot Cushing, daily
            gold_s = None
            try:
                import yfinance as yf
                g = yf.Ticker("GC=F").history(period="max", auto_adjust=False)
                gold_s = g['Close'].astype(float).dropna()
            except Exception as ye:
                print(f"  yfinance GC=F failed: {ye}")
            if wti_s is not None and gold_s is not None and len(gold_s) > 100:
                wti_s = wti_s.astype(float).dropna()
                mask_g = (gold_s.index >= from_date) & (gold_s.index <= to_date)
                mask_w = (wti_s.index >= from_date) & (wti_s.index <= to_date)
                gold_px = gold_s[mask_g]
                wti_px = wti_s[mask_w]
                print("  Source: FRED DCOILWTICO (WTI) + yfinance GC=F (Gold)")
                print(f"  Gold: {len(gold_px)} rows, ${gold_px.min():.0f} - ${gold_px.max():.0f}")
                print(f"  WTI:  {len(wti_px)} rows, ${wti_px.min():.0f} - ${wti_px.max():.0f}")
        except Exception as e:
            print(f"  FRED+yfinance combo failed: {e}, trying akshare...")

    # Try akshare if FRED did not fill
    if gold_px is None or wti_px is None or len(gold_px) < 10:
        try:
            import akshare as ak
            import pandas as pd

            print("  Source: akshare")
            gold_df_raw = ak.futures_foreign_hist(symbol='GC')
            wti_df_raw = ak.futures_foreign_hist(symbol='CL')

            gold_df_raw['date'] = pd.to_datetime(gold_df_raw['date'])
            gold_df_raw = gold_df_raw.set_index('date').sort_index()
            wti_df_raw['date'] = pd.to_datetime(wti_df_raw['date'])
            wti_df_raw = wti_df_raw.set_index('date').sort_index()

            gold_px = gold_df_raw['close'].astype(float)
            wti_px = wti_df_raw['close'].astype(float)

            mask_g = (gold_px.index >= from_date) & (gold_px.index <= to_date)
            mask_w = (wti_px.index >= from_date) & (wti_px.index <= to_date)
            gold_px = gold_px[mask_g]
            wti_px = wti_px[mask_w]

            print(f"  Gold: {len(gold_px)} rows, ${gold_px.min():.0f} - ${gold_px.max():.0f}")
            print(f"  WTI:  {len(wti_px)} rows, ${wti_px.min():.0f} - ${wti_px.max():.0f}")
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

    # Persist cache for future runs (only when fetched fresh, i.e. not from cache)
    try:
        if len(gold_px) > 100:
            import pandas as pd
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            cdf = pd.DataFrame({'gold': gold_px, 'wti': wti_px}).dropna()
            cdf.to_csv(CACHE)
            print(f"  Cache saved: {os.path.basename(CACHE)} ({len(cdf)} rows)")
    except Exception as e:
        print(f"  Cache save failed: {e}")

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
    # Simulate: daily regime check -> allocation -> P&L with 1-day lag

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
    # v3: 日收益序列（夏普/回撤/分段收益）
    daily_rets, bh_rets = [], []
    bh_peak = 100.0
    bh_max_dd = 0.0
    regime_rets = {'extreme': [], 'recovery': [], 'fair_value': [], 'oil_bubble': []}

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

        # Max drawdown tracking (both portfolios)
        if nav > nav_peak:
            nav_peak = nav
        dd = (nav - nav_peak) / nav_peak
        if dd < max_drawdown:
            max_drawdown = dd
        if bh_nav > bh_peak:
            bh_peak = bh_nav
        bh_dd = (bh_nav - bh_peak) / bh_peak
        if bh_dd < bh_max_dd:
            bh_max_dd = bh_dd

        # v3: 收益序列
        daily_rets.append(daily)
        bh_rets.append(bh_daily)
        regime_rets[regime].append(daily)

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

    # v3: 夏普与分段收益
    import statistics as _st
    def _sharpe(rets):
        if len(rets) < 30:
            return 0.0
        mu = _st.mean(rets)
        sd = _st.stdev(rets)
        return (mu / sd * (252 ** 0.5)) if sd > 0 else 0.0
    sharpe = _sharpe(daily_rets)
    sharpe_bh = _sharpe(bh_rets)
    regime_ann = {}
    for k, v in regime_rets.items():
        if len(v) >= 30:
            regime_ann[k] = (1 + _st.mean(v)) ** 252 - 1
        else:
            regime_ann[k] = 0.0

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
    Period:         {from_date} -> {to_date}
    Trading days:   {len(common_idx)}
    Years:          {n_years:.1f}

    GOR Strategy:   {total_return:+.1%} total  |  {ann_return:+.1%}/yr
    60/40 B&H:      {bh_return:+.1%} total  |  {ann_bh:+.1%}/yr
    Alpha:          {total_return - bh_return:+.1%}

    Avg Allocation: {avg_gold:.0f}% Gold | ~{avg_oil:.0f}% Oil | ~{avg_cash:.0f}% Cash
    Max Drawdown:   {max_drawdown:+.1%}  (60/40: {bh_max_dd:+.1%})
    Sharpe:         {sharpe:.2f}  (60/40: {sharpe_bh:.2f})
  {'='*64}
    Per-Regime Annualized (GOR strategy):
      Extreme:      {regime_ann['extreme']:+8.1%}   ({regime_counts['extreme']:>4d} days)
      Recovery:     {regime_ann['recovery']:+8.1%}   ({regime_counts['recovery']:>4d} days)
      Fair Value:   {regime_ann['fair_value']:+8.1%}   ({regime_counts['fair_value']:>4d} days)
      Oil Bubble:   {regime_ann['oil_bubble']:+8.1%}   ({regime_counts['oil_bubble']:>4d} days)
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
            arrow = "↑" if sc['to'] == 'extreme' else ("↓" if sc['to'] == 'oil_bubble' else "->")
            print(f"    {sc['date']}  {sc['from']:>12s} -> {sc['to']:<12s} {arrow}  GOR={sc['gor']}  WTI=${sc['wti']}")

    # ============================================================
    # CHART (if --chart flag)
    # ============================================================
    if chart and nav_history:
        from data_pipeline.charts import backtest_nav_chart
        backtest_nav_chart(nav_history, bh_history, from_date, to_date,
                           ann_return, ann_bh)
        print(f"  Chart saved: 看板日志/backtest_chart_{from_date}_to_{to_date}.png")

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
