#!/usr/bin/env python3
"""
Wayfinder — Flow Scanner
=========================
Pull all three capital flow dimensions from FRED + yfinance + akshare.
Output: flows_latest.json
"""

import json, os, datetime, sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── FRED ──────────────────────────────────────────────────────
_fred = None

def _init_fred():
    global _fred
    if _fred is not None: return _fred
    try:
        from fredapi import Fred
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / '.env')
        key = os.getenv('FRED_API_KEY')
        if key: _fred = Fred(api_key=key)
        else: _fred = False
    except: _fred = False
    return _fred

def fred_get(series_id):
    fred = _init_fred()
    if not fred: return None
    try: return float(fred.get_series(series_id).dropna().iloc[-1])
    except: return None

# ─── Scan ──────────────────────────────────────────────────────

def scan():
    """Run full 3-flow scan. Returns dict."""
    today = datetime.date.today().strftime('%Y-%m-%d')
    d = {"date": today}

    # ── TOTAL ────────────────────────────────────────────
    fed_bs = fred_get('WALCL')       # millions
    m2 = fred_get('M2SL')            # billions
    sofr = fred_get('SOFR')          # %
    ecb_bs = fred_get('ECBASSETSW')  # millions EUR
    deficit_m = fred_get('MTSDS')    # millions, monthly surplus/deficit

    # Global CB composite (Fed + ECB, normalized to USD)
    global_cb = None
    if fed_bs and ecb_bs:
        ecb_usd = ecb_bs * 1.08  # EUR->USD approximate
        global_cb = round((fed_bs + ecb_usd) / 1e6, 1)  # Trillion USD

    d['total'] = {
        'fed_balance_trillion': round(fed_bs / 1e6, 2) if fed_bs else None,
        'm2_trillion': round(m2 / 1e3, 2) if m2 else None,
        'sofr': round(sofr, 2) if sofr else None,
        'ecb_balance_trillion_eur': round(ecb_bs / 1e6, 2) if ecb_bs else None,
        'global_cb_trillion_usd': global_cb,
        'us_monthly_deficit_billion': round(abs(deficit_m) / 1e3, 1) if deficit_m and deficit_m < 0 else None,
        'trend': 'CONTRACTING' if (fed_bs and fed_bs < 7.5e6) else 'EXPANDING',
    }

    # ── DIRECTION ─────────────────────────────────────────
    dxy = None
    try:
        import yfinance as yf
        dxy = float(yf.Ticker('DX-Y.NYB').history(period='5d')['Close'].iloc[-1])
    except: pass

    gold_reserve_cn = None
    try:
        import akshare as ak
        gr = ak.macro_china_gold_reserve()
        gold_reserve_cn = float(gr.tail(1).iloc[0, 1]) if len(gr) > 0 else None
    except: pass

    # CNY 10Y for China-US spread
    cny_10y = None
    try:
        import akshare as ak
        cn_bond = ak.bond_china_yield()
        if len(cn_bond) > 0:
            cny_10y = float(cn_bond.tail(1).iloc[0, 1]) if cn_bond.shape[1] > 1 else None
    except: pass

    dgs2 = fred_get('DGS2')
    dgs10 = fred_get('DGS10')
    dgs30 = fred_get('DGS30')
    dff = fred_get('DFF')

    yield_curve = None
    china_us_spread = None
    if dgs10 and dgs2:
        yield_curve = round(dgs10 - dgs2, 2)
    if dgs10 and cny_10y:
        china_us_spread = round(cny_10y - dgs10, 2)

    fed_debt = fred_get('GFDEBTN')
    cpi = fred_get('CPIAUCSL')
    pce = fred_get('PCEPILFE')

    d['direction'] = {
        'dxy': round(dxy, 2) if dxy else None,
        'china_gold_reserve_tonnes': gold_reserve_cn,
        'us10y': dgs10, 'us30y': dgs30, 'us2y': dgs2,
        'fed_rate': dff, 'cpi': cpi, 'core_pce': pce,
        'fed_debt_trillion': round(fed_debt / 1e6, 2) if fed_debt else None,
        'yield_curve_10y2y': yield_curve,
        'china_us_spread': china_us_spread,
        'signal': 'CENTRIPETAL' if (dxy and dxy > 99) else ('CENTRIFUGAL' if (dxy and dxy < 98) else 'NEUTRAL'),
    }

    # ── SPEED ─────────────────────────────────────────────
    hy_spread = fred_get('BAMLH0A0HYM2')
    ig_spread = fred_get('BAMLC0A0CM')
    ted = fred_get('TEDRATE')
    vix = fred_get('VIXCLS')
    em_spread = fred_get('BAMLEMCBPIOAS')

    # Swap basis: SOFR - Fed Funds (positive = dollar funding stress)
    sofr_val = d['total']['sofr']
    fed_rate = d['direction']['fed_rate']
    swap_basis = round(sofr_val - fed_rate, 2) if (sofr_val and fed_rate) else None

    # JPY volatility proxy
    jpy_vol = None
    try:
        import yfinance as yf
        jpy = yf.Ticker('JPY=X')
        jpy_hist = jpy.history(period='1mo')
        if len(jpy_hist) > 5:
            jpy_vol = round(float(jpy_hist['Close'].pct_change().std() * (252 ** 0.5) * 100), 1)
    except: pass

    d['speed'] = {
        'vix': round(vix, 2) if vix else None,
        'hy_spread_bp': round(hy_spread * 100, 0) if hy_spread else None,
        'ig_spread_bp': round(ig_spread * 100, 0) if ig_spread else None,
        'ted_spread': round(ted, 2) if ted else None,
        'em_spread_bp': round(em_spread * 100, 0) if em_spread else None,
        'swap_basis': swap_basis,
        'jpy_vol_annualized': jpy_vol,
        'signal': 'PANIC' if (vix and vix > 25) else ('ELEVATED' if (vix and vix > 20) else ('CALM' if (vix and vix < 17) else 'NORMAL')),
    }

    # ── SYNTHESIS ─────────────────────────────────────────
    total_sig = d['total']['trend']
    dir_sig = d['direction']['signal']
    spd_sig = d['speed']['signal']

    if total_sig == 'CONTRACTING' and dir_sig == 'CENTRIPETAL' and spd_sig in ('PANIC', 'ELEVATED'):
        compass = 'CENTRIPETAL COLLAPSE — Cash is king. All risk assets under pressure.'
    elif total_sig == 'EXPANDING' and dir_sig == 'CENTRIFUGAL':
        compass = 'CENTRIFUGAL DIFFUSION — Risk-on. Capital flowing to EM and commodities.'
    elif total_sig == 'CONTRACTING' and dir_sig == 'CENTRIPETAL':
        compass = 'DRAIN PHASE — USD accumulating. Waiting for release valve.'
    else:
        compass = 'TRANSITION — Mixed signals. Tactical positioning only.'

    d['compass'] = compass

    # ── Save ──────────────────────────────────────────────
    out = BASE_DIR / 'flows_latest.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return d


if __name__ == '__main__':
    print('Wayfinder · Flow Scanner')
    print('=' * 40)
    data = scan()
    for dim in ['total', 'direction', 'speed']:
        print(f"\n  {dim.upper()}:")
        for k, v in data[dim].items():
            if v is not None:
                print(f"    {k}: {v}")
    print(f"\n  COMPASS: {data['compass']}")
    print(f"\n  Saved: flows_latest.json")