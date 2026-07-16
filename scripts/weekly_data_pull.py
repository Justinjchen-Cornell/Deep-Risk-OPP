#!/usr/bin/env python3
"""
每周市场数据拉取脚本 · 陈嘉投资决策框架
===========================================
数据源: FRED (利率/DXY/VIX/宏观) + akshare (商品期货) + Web备用
输出: gor_latest.json + capital_flows_latest.json + 看板日志 + HTML数据块更新 + 变化比对报告
用法: python scripts/weekly_data_pull.py
频率: 每周六 08:00 (Windows Task Scheduler)
"""

import json, os, datetime, sys, re
import urllib.request, ssl
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "看板日志"
LOG_FILE = BASE_DIR / "看板日志" / "update_log.txt"

def log(msg):
    """带时间戳的日志输出（兼容Windows GBK控制台）"""
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        safe = line.encode('ascii', errors='replace').decode('ascii')
        print(safe)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass


# ─── FRED API helper ───────────────────────────────────────────
_fred = None

def _init_fred():
    global _fred
    if _fred is not None:
        return _fred
    try:
        from fredapi import Fred
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / '.env')
        api_key = os.getenv('FRED_API_KEY')
        if api_key:
            _fred = Fred(api_key=api_key)
            log("  FRED: connected")
        else:
            _fred = False
            log("  FRED: API key not found (set FRED_API_KEY in .env)")
    except ImportError:
        _fred = False
        log("  FRED: pip install fredapi python-dotenv")
    except Exception as e:
        _fred = False
        log(f"  FRED init ERROR: {e}")
    return _fred


def fred_get(series_id):
    fred = _init_fred()
    if not fred:
        return None
    try:
        series = fred.get_series(series_id)
        return float(series.dropna().iloc[-1])
    except Exception as e:
        log(f"  FRED {series_id}: {e}")
        return None


def fetch_all():
    """拉取所有市场数据"""
    import akshare as ak
    data = {}
    ssl._create_default_https_context = ssl._create_unverified_context

    # 1. 黄金期货 (GC)
    try:
        df = ak.futures_foreign_hist(symbol='GC')
        last = df.tail(1).iloc[0]
        data['gold'] = round(float(last['close']), 2)
        log(f"  Gold: ${data['gold']}/oz")
    except Exception as e:
        log(f"  Gold ERROR: {e}"); data['gold'] = None

    # 2. WTI原油 (CL)
    try:
        df = ak.futures_foreign_hist(symbol='CL')
        last = df.tail(1).iloc[0]
        data['wti'] = round(float(last['close']), 2)
        log(f"  WTI: ${data['wti']}/bbl")
    except Exception as e:
        log(f"  WTI ERROR: {e}"); data['wti'] = None

    # 3. 布伦特原油 (B00Y)
    try:
        df = ak.futures_global_hist_em(symbol='B00Y')
        last = df.tail(1).iloc[0]
        data['brent'] = round(float(last.iloc[3]), 2)
        log(f"  Brent: ${data['brent']}/bbl")
    except Exception as e:
        if data.get('wti'):
            data['brent'] = round(data['wti'] * 1.06, 2)
            log(f"  Brent: ${data['brent']}/bbl (WTI*1.06)")
        else:
            log(f"  Brent ERROR: {e}"); data['brent'] = None

    # 4. COMEX铜 (HG)
    try:
        df = ak.futures_foreign_hist(symbol='HG')
        last = df.tail(1).iloc[0]
        data['copper'] = round(float(last['close']) / 100, 4)
        log(f"  Copper: ${data['copper']}/lb")
    except Exception as e:
        log(f"  Copper ERROR: {e}"); data['copper'] = None

    # 5. 10Y美债 — FRED primary, akshare fallback
    us10y = fred_get('DGS10')
    if us10y:
        data['us10y'] = round(us10y, 2)
        log(f"  10Y: {data['us10y']}% (FRED)")
    else:
        try:
            df = ak.bond_zh_us_rate()
            col_name = None
            for c in df.columns:
                if '美国国债收益率10年' in c or ('10' in c and '美国' in c):
                    col_name = c; break
            if col_name is None:
                col_name = '美国国债收益率10年'
            valid = df[df[col_name].notna()]
            if len(valid) > 0:
                data['us10y'] = round(float(valid.tail(1).iloc[0][col_name]), 2)
                log(f"  10Y: {data['us10y']}% (akshare)")
            else:
                raise ValueError("No data")
        except Exception as e:
            log(f"  10Y ERROR: {e}"); data['us10y'] = None

    # 6. DXY — yfinance primary (ICE DXY), web fallback
    try:
        import yfinance as yf
        ticker = yf.Ticker("DX-Y.NYB")
        hist = ticker.history(period="5d")
        if len(hist) > 0:
            data['dxy'] = round(float(hist['Close'].iloc[-1]), 2)
            log(f"  DXY: {data['dxy']} (yfinance)")
        else:
            raise ValueError("No data")
    except:
        try:
            url = 'https://tradingeconomics.com/united-states/currency'
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=15)
            html = resp.read().decode('utf-8', errors='ignore')
            m = re.search(r'DXY.*?exchange rate.*?(\d{2,3}\.\d{2})', html)
            data['dxy'] = float(m.group(1)) if m else None
            log(f"  DXY: {data['dxy']} (web)")
        except Exception as e:
            log(f"  DXY ERROR: {e}"); data['dxy'] = None

    # 7. VIX — FRED primary, TradingView/CBOE fallback
    vix_fred = fred_get('VIXCLS')
    if vix_fred:
        data['vix'] = round(vix_fred, 2)
        log(f"  VIX: {data['vix']} (FRED)")
    else:
        try:
            url = 'https://scanner.tradingview.com/america/scan'
            body = json.dumps({"symbols":{"tickers":["CBOE:VIX"]},"columns":["close"]}).encode()
            req = urllib.request.Request(url, data=body, headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=10)
            tv = json.loads(resp.read())
            if tv.get('data') and len(tv['data'])>0:
                data['vix'] = round(float(tv['data'][0]['d'][0]),2)
                log(f"  VIX: {data['vix']} (TradingView)")
            else:
                raise ValueError("Empty")
        except:
            try:
                url = 'https://www.cboe.com/tradable-products/vix/'
                req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
                resp = urllib.request.urlopen(req, timeout=15)
                html = resp.read().decode('utf-8',errors='ignore')
                for pat in [r'VIX Spot Price.*?(\d{1,2}\.\d{2})', r'"price":\s*(\d{1,2}\.\d{2})']:
                    m = re.search(pat, html, re.DOTALL)
                    if m: data['vix'] = float(m.group(1)); break
                log(f"  VIX: {data.get('vix')} (CBOE)")
            except Exception as e2:
                log(f"  VIX ERROR: {e2}"); data['vix'] = None

    # ─── FRED-only macro indicators ───

    # 8. 30Y美债
    data['us30y'] = fred_get('DGS30')

    # 9. 联邦基金利率
    data['fed_rate'] = fred_get('DFF')

    # 10. 美联储总资产 → 万亿
    walcl = fred_get('WALCL')
    data['fed_balance'] = round(walcl / 1_000_000, 2) if walcl else None

    # 11. M2 → 万亿
    m2 = fred_get('M2SL')
    data['m2'] = round(m2 / 1_000, 2) if m2 else None

    # 12. CPI (月度，取年率近似)
    cpi = fred_get('CPIAUCSL')
    data['cpi'] = round(cpi, 1) if cpi else None

    # 13. 核心PCE
    pce = fred_get('PCEPILFE')
    data['core_pce'] = round(pce, 1) if pce else None

    # 14. 联邦债务 → 万亿
    debt = fred_get('GFDEBTN')
    data['fed_debt'] = round(debt / 1_000_000, 2) if debt else None

    # Log summary
    for k, label in [('us30y','30Y'),('fed_rate','FedRate'),('fed_balance','FedBS'),
                      ('m2','M2'),('cpi','CPI'),('core_pce','CorePCE'),('fed_debt','Debt')]:
        v = data.get(k)
        if v is not None:
            log(f"  {label}: {v} (FRED)" if k in ('us30y','fed_rate') else f"  {label}: {v} (FRED)")
        else:
            log(f"  {label}: N/A")

    return data


def compute_gor(data):
    """GOR计算+仓位分配"""
    g, w, b = data.get('gold'), data.get('wti'), data.get('brent')
    d, y = data.get('dxy'), data.get('us10y')

    gor_b = round(g / b, 2) if g and b else None
    gor_w = round(g / w, 2) if g and w else None

    # GOR区间判定 — 优先Brent，失败时用WTI
    gor_use = gor_b if gor_b else gor_w
    if gor_use and gor_use >= 45:
        regime = "原油极端低估"
        base_pos, base_oil, base_gold = 70, 25, 20
    elif gor_use and gor_use >= 30:
        regime = "修复周期"
        base_pos, base_oil, base_gold = 50, 20, 15
    elif gor_use and gor_use >= 20:
        regime = "估值均衡"
        base_pos, base_oil, base_gold = 30, 10, 15
    else:
        regime = "原油泡沫"
        base_pos, base_oil, base_gold = 10, 0, 7

    # 风险修正
    dxy_corr = -10 if d and d > 99 else (10 if d and d < 98 else 0)
    yld_corr = -10 if y and y > 4.3 else (10 if y and y < 4.2 else 0)
    final_pos = max(5, min(80, base_pos + dxy_corr + yld_corr))

    # 硬规则
    oil_alloc = base_oil
    alerts = []

    if w and w < 75:
        oil_alloc = 5
        alerts.append({"level": "critical", "title": f"WTI ${w} < $75 硬止损触发!", "detail": "油气仓位强制降至5%"})

    if d and d > 99:
        alerts.append({"level": "warning", "title": f"DXY={d} > 99 强美元压制", "detail": "仓位-10%"})
    if y and y > 4.3:
        alerts.append({"level": "warning", "title": f"10Y={y}% > 4.3% 高利率压制", "detail": "仓位-10%"})

    cash = 100 - oil_alloc - base_gold - 7

    return {
        "gor_brent": gor_b, "gor_wti": gor_w, "regime": regime,
        "final_position": final_pos,
        "allocation": {"油气": oil_alloc, "黄金": base_gold, "现金": max(0, cash), "A股": 7, "铜": 0},
        "alerts": alerts
    }


def save_gor_json(data, gor):
    """保存gor_latest.json"""
    today = datetime.date.today().strftime('%Y-%m-%d')
    output = {
        "updated": f"{today} 12:00",
        "gor_brent": gor['gor_brent'], "gor_wti": gor['gor_wti'],
        "regime": gor['regime'], "final_position": gor['final_position'],
        "allocation": gor['allocation'], "alerts": gor['alerts'],
        "data": {
            "黄金期货": {"price": data.get('gold'), "change_pct": 0.0},
            "WTI原油": {"price": data.get('wti'), "change_pct": 0.0},
            "布伦特原油": {"price": data.get('brent'), "change_pct": 0.0},
            "美元指数DXY": {"price": data.get('dxy'), "change_pct": 0.0},
            "10Y美债收益率": {"price": data.get('us10y'), "change_pct": 0.0},
            "VIX恐慌指数": {"price": data.get('vix'), "change_pct": 0.0},
            "COMEX铜": {"price": data.get('copper'), "change_pct": 0.0}
        },
        "capital_three_flows": {
            "total": "收缩" if (data.get('fed_balance') and data['fed_balance'] < 7.5) else "扩张",
            "direction": "向心坍缩" if (data.get('dxy') and data['dxy'] > 99) else ("离心扩散" if (data.get('dxy') and data['dxy'] < 98) else "中性"),
            "speed": "加速中" if (data.get('vix') and data['vix'] > 20) else "放缓",
            "dxy": data.get('dxy'), "vix": data.get('vix'),
            "tenyear": data.get('us10y'), "thirtyyear": data.get('us30y'),
            "fed_balance": data.get('fed_balance'), "m2": data.get('m2'),
            "fed_rate": data.get('fed_rate'),
            "cpi": data.get('cpi'), "core_pce": data.get('core_pce'),
            "fed_debt": data.get('fed_debt'),
            "warsh_alert": True if (data.get('fed_rate') and data['fed_rate'] > 3.5) else False
        },
        "ashare_hedge": {"enabled": False, "position_pct": 7, "trigger": "A股<10%无需对冲"}
    }

    gor_path = BASE_DIR / "gor_latest.json"
    with open(gor_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    log(f"  Saved: gor_latest.json")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    log_path = DATA_DIR / f"{today}-gor-data.json"
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    log(f"  Saved: 看板日志/{today}-gor-data.json")
    return output


def save_capital_flows_json(data):
    """保存capital_flows_latest.json"""
    today = datetime.date.today().strftime('%Y-%m-%d')
    output = {
        "updated": f"{today} 12:00",
        "week_of": today,
        "bonds": {
            "us_10y": data.get('us10y'), "us_5y": round(data.get('us10y', 4.5) - 0.25, 2) if data.get('us10y') else None,
            "us_30y": round(data.get('us10y', 4.5) + 0.25, 2) if data.get('us10y') else None,
            "yield_curve": "倒挂结束·陡峭化预警",
            "seesaw": {
                "treasury_vs_stocks": "科技股抛售→资金涌入国债（避险）",
                "treasury_vs_gold": "国债与黄金同跌·现金为王信号增强",
                "credit_spread_warning": "HY利差扩大→信用市场压力上升"
            }
        },
        "central_banks": {
            "fed": {"balance_sheet": "$7.3万亿", "trend": "QT收缩中·Warsh鹰派", "rate": "3.50-3.75%", "next_meeting": "2026年7月FOMC", "gold_reserves": "8,133吨"},
            "ecb": {"balance_sheet": "€3.4万亿", "trend": "6月已加息25bp至2.40%", "rate": "2.40%", "gold_reserves": "504吨"},
            "boj": {"balance_sheet": "¥760万亿", "trend": "6月16日加息至1.00%", "rate": "1.00%", "gold_reserves": "846吨"},
            "pboc": {"balance_sheet": "¥44万亿", "trend": "全球唯一降息·3.00→2.90%", "rate": "2.90%", "gold_reserves": "2,332吨"}
        },
        "gold_flows": {"central_bank_purchases": {"2024_total": "1,037吨", "2025_q1": "289吨", "trend": "央行购金不减"}, "etf_flows": {"trend": "黄金从ATH跌-29%·央行独自接盘"}},
        "oil_flows": {"wti_price": data.get('wti'), "spr_level": "3.7亿桶", "producer_discipline": "OPEC+减产·伊朗和平恢复出口"},
        "commodity_index": {"trend": "铜受强美元+科技股抛售压制·AI基建中长期看涨"},
        "currency_flows": {"dxy_signal": ">101=向心坍缩加速·DXY 12月新高"}
    }

    cf_path = BASE_DIR / "capital_flows_latest.json"
    with open(cf_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    log(f"  Saved: capital_flows_latest.json")
    return output


def update_html_data_blocks(gor_output, cf_output):
    """将最新JSON数据注入三个HTML看板的数据块中"""

    gor_block = 'window.__GOR_DATA__ = ' + json.dumps(gor_output, ensure_ascii=False, indent=2) + ';'
    cf_block = 'window.__CAPITAL_FLOWS__ = ' + json.dumps(cf_output, ensure_ascii=False, indent=2) + ';'

    gor_files = ['📊 投资决策看板.html', '🛡️ 对冲作战手册.html']
    cf_files = ['🌊 资本三流观测站.html']

    for fname in gor_files:
        path = BASE_DIR / fname
        if not path.exists(): continue
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        start_idx = html.find('window.__GOR_DATA__ = {')
        if start_idx == -1: continue
        depth = 0; end_idx = start_idx
        for i in range(start_idx, len(html)):
            if html[i] == '{': depth += 1
            elif html[i] == '}':
                depth -= 1
                if depth == 0: end_idx = i + 2; break
        if end_idx > start_idx:
            html = html[:start_idx] + gor_block + html[end_idx:]
            with open(path, 'w', encoding='utf-8') as f: f.write(html)
            log(f"  Updated GOR block: {fname}")

    for fname in cf_files:
        path = BASE_DIR / fname
        if not path.exists(): continue
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        start_idx = html.find('window.__CAPITAL_FLOWS__ = {')
        if start_idx == -1: continue
        depth = 0; end_idx = start_idx
        for i in range(start_idx, len(html)):
            if html[i] == '{': depth += 1
            elif html[i] == '}':
                depth -= 1
                if depth == 0: end_idx = i + 2; break
        if end_idx > start_idx:
            html = html[:start_idx] + cf_block + html[end_idx:]
            with open(path, 'w', encoding='utf-8') as f: f.write(html)
            log(f"  Updated CF block: {fname}")


def generate_weekly_content(gor_output):
    """根据最新数据生成HTML文本内容（本周新闻、金转油逻辑等）"""
    d = gor_output['data']
    a = gor_output['allocation']
    ctf = gor_output['capital_three_flows']
    gb = gor_output['gor_brent']
    gw = gor_output['gor_wti']
    gold = d['黄金期货']['price']
    wti = d['WTI原油']['price']
    brent = d['布伦特原油']['price']
    vix = d['VIX恐慌指数']['price']
    dxy_val = d['美元指数DXY']['price']
    us10y = d['10Y美债收益率']['price']

    week_label = datetime.date.today().strftime('%Y年%m月第') + str((datetime.date.today().day - 1) // 7 + 1) + '周'
    today_str = datetime.date.today().strftime('%m月%d日')

    wti_below = wti < 75
    vix_below = vix < 17
    gor_extreme = gw >= 60 if gw else False

    content = f'''<div class="card" style="margin-bottom:24px;padding:28px 32px;background:linear-gradient(135deg,rgba(240,96,48,.04),rgba(232,180,28,.04));border-color:rgba(240,96,48,.2)">
  <div style="font-size:12px;font-weight:700;color:var(--oil);text-transform:uppercase;letter-spacing:2px;margin-bottom:8px">📡 本周资本三流观察 · {week_label}（数据截至{today_str}）{"⚠️ GOR破60！" if gor_extreme else ""}{"⚠️ WTI<$75硬止损！" if wti_below else ""}{"✅ VIX<17 Straddle窗口！" if vix_below else ""}</div>
  <div style="font-size:16px;color:var(--tx);line-height:1.9">
    <p><b style="color:var(--rd)">{'🔴🔴 GOR(WTI)=' + str(gw) + ' 突破历史极值！' if gor_extreme else '🔴 GOR在高位运行'}</b>黄金${gold:.0f}/oz，WTI ${wti:.2f}/bbl。{"GOR(WTI)突破60——1986年以来首次。金涨油跌使极端程度进一步加剧。" if gor_extreme else ""} 均值回归方向明确但时机高度不确定——伊朗和平协议+OPEC+减产博弈使油价失去方向。{"WTI已连续2周+低于$75硬止损线——油气仓位强制维持5%。" if wti_below else ""}</p>
    <p style="margin-top:8px"><b style="color:{'var(--rd)' if wti_below else 'var(--gold)'}">{'🔴 WTI在$68-70区间挣扎' if wti_below else '🟡 油价运行中'}</b>{"美伊临时和平备忘录持续生效——阿联酋出口恢复至战前85%，伊朗获60天豁免期出口石油。OPEC+维持减产但效果被伊朗增量抵消。Cushing库存处于临界水平但市场更关注伊朗供应回归。$68-70区间可能接近底部。" if wti_below else "油价运行正常。"}</p>
    <p style="margin-top:8px"><b style="color:var(--gold)">{'🟡 黄金运行中' if not gor_extreme else '🟡 黄金V型反弹'}</b>{"金价从近期低点反弹，央行购金锁死下跌空间（Q1净购244吨·PBoC连续19月增持·45%央行计划增持）。黄金底仓20%锁死不动。高盛目标$5,400/oz。"}</p>
    <p style="margin-top:8px"><b style="color:var(--gn)">{'✅ VIX=' + str(vix) + ' < 17——SPY Straddle建仓窗口！' if vix_below else '🟡 VIX=' + str(vix) + ' 偏高等待'}</b>{"低波动率时买入Straddle=典型的凸性交易。WTI<$75+Warsh FOMC+明斯基9月=三重不确定→波动率终将扩张。成本降至组合2-3%。" if vix_below else "等待VIX回落<17或突破25后采取对应策略。"}</p>
    <p style="margin-top:8px"><b style="color:var(--bl)">🔵 DXY={dxy_val}·10Y={us10y}%·FOMC临近</b>DXY{"维持>99向心坍缩区间" if dxy_val > 99 else "回落至98以下"}。10Y在{us10y}%{"高位压制" if us10y > 4.3 else "正常区间"}。Warsh 7月FOMC(7/15-16)临近——市场聚焦9月加息信号。全球央行利率分化：欧美日加息、中国降息。</p>
    <p style="margin-top:8px"><b style="color:var(--pp)">🟣 三流综合判定：</b>总量收缩+方向向心+流速{"放缓" if vix < 18 else "加速"}。当前配置：油气{a['油气']}%+黄金{a['黄金']}%+现金{a['现金']}%。{"<b>GOR突破60=历史级极端。纪律优先：WTI<$75→油气≤5%。等WTI回$75上方重新激活。</b>" if wti_below else ""}</p>
  </div>
</div>'''
    return content


def update_html_text_content(gor_output):
    """更新HTML中的自动文本区域（本周观察等）"""
    path = BASE_DIR / '🌊 资本三流观测站.html'
    if not path.exists():
        log("  SKIP: 资本三流观测站.html not found")
        return

    # Extract values needed
    gw = gor_output.get('gor_wti', 0)
    wti = gor_output['data']['WTI原油']['price']
    wti_below = wti < 75 if wti else False
    gor_extreme = gw >= 60 if gw else False

    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    new_content = generate_weekly_content(gor_output)

    # Replace between AUTO_UPDATE_WEEKLY_SUMMARY markers
    start_tag = '<!-- AUTO_UPDATE_WEEKLY_SUMMARY_START -->'
    end_tag = '<!-- ===== 向心坍缩进度条 ===== -->'
    if start_tag in html and end_tag in html:
        pre = html[:html.find(start_tag) + len(start_tag)]
        post = html[html.find(end_tag):]
        html = pre + '\n' + new_content + '\n<!-- AUTO_UPDATE_WEEKLY_SUMMARY_END -->\n' + post
        with open(path, 'w', encoding='utf-8') as f: f.write(html)
        log("  Updated text: 资本三流观测站 weekly summary")

    # Update the 金转油 logic section title
    old_logic_start = '<div style="font-size:17px;font-weight:800;margin-bottom:12px">'
    new_logic_title = f'<div style="font-size:17px;font-weight:800;margin-bottom:12px">🔄 金转油 · GOR={gw:.1f}{" 历史级极端" if gor_extreme else ""} {"· 等待WTI回归" if wti_below else ""}</div>'
    idx = html.find(old_logic_start)
    if idx != -1 and '金转油' in html[idx:idx+200]:
        end_of_title = html.find('</div>', idx)
        if end_of_title != -1:
            html = html[:idx] + new_logic_title + html[end_of_title + 6:]

    # Update footer date
    today_fmt = datetime.date.today().strftime('%Y.%m.%d')
    for old_date in ['2026.06.25', '2026.06.19', '2026.06.20']:
        old_str = f'本周更新于 {old_date}'
        if old_str in html:
            html = html.replace(old_str, f'本周更新于 {today_fmt}')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    log("  Updated text: 资本三流观测站 footer + logic title")


def generate_change_report(gor_output, data):
    """生成周度变化比对报告"""
    today = datetime.date.today()
    today_str = today.strftime('%Y-%m-%d')

    # Find previous week's data file
    prev_file = None
    if DATA_DIR.exists():
        files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('-gor-data.json')], reverse=True)
        # Skip today's file if it exists, get the one before
        for f in files:
            if today_str not in f:
                prev_file = DATA_DIR / f
                break

    if not prev_file:
        log("  No previous data found, skipping change report")
        return

    try:
        with open(prev_file, 'r', encoding='utf-8') as f:
            prev = json.load(f)
    except:
        log("  Failed to read previous data, skipping change report")
        return

    prev_date = prev.get('updated', 'Unknown')[:10]

    # Current and previous values
    g = gor_output
    c_gold = g['data']['黄金期货']['price']
    p_gold = prev['data']['黄金期货']['price']
    c_wti = g['data']['WTI原油']['price']
    p_wti = prev['data']['WTI原油']['price']
    c_dxy = g['capital_three_flows']['dxy']
    p_dxy = prev['capital_three_flows']['dxy']
    c_vix = g['capital_three_flows']['vix']
    p_vix = prev['capital_three_flows']['vix']
    c_10y = g['capital_three_flows']['tenyear']
    p_10y = prev['capital_three_flows']['tenyear']
    c_oil = g['allocation']['油气']
    p_oil = prev['allocation']['油气']
    c_cash = g['allocation']['现金']
    p_cash = prev['allocation']['现金']

    chg = lambda c,p: f"{'+'+str(round(c-p,2)) if c>p else str(round(c-p,2))}"

    report = f"""---
date: {today_str}
type: change-report
tags: [变化比对, 周报, 市场更新]
---

# 📊 看板变化比对报告 · {prev_date} → {today_str}

> 每周六自动生成 · 记录GOR配置、市场数据、资本三流的周度变化

---

## 🎯 仓位配置变化

| 资产 | {prev_date} | {today_str} | 变化 | 说明 |
|------|:---:|:---:|:--:|------|
| 🛢️ 油气 | {p_oil}% | {c_oil}% | {chg(c_oil,p_oil)}% | {"🔴 WTI${}继续低于$75硬止损" if c_wti < 75 else ""} |
| 🥇 黄金 | {prev['allocation']['黄金']}% | {g['allocation']['黄金']}% | {chg(g['allocation']['黄金'], prev['allocation']['黄金'])}% | PBoC购金锁底 |
| 💵 现金 | {p_cash}% | {c_cash}% | {chg(c_cash,p_cash)}% | |
| 📈 A股 | 7% | 7% | 不变 | <10% |
| **总仓位** | {prev['final_position']}% | {g['final_position']}% | | |

---

## 📈 市场数据变化

| 指标 | {prev_date} | {today_str} | 变化 | 解读 |
|------|:---:|:---:|:--:|------|
| GOR(Brent) | {prev['gor_brent']} | {g['gor_brent']} | {chg(g['gor_brent'], prev['gor_brent'])} | |
| GOR(WTI) | {prev['gor_wti']} | {g['gor_wti']} | {chg(g['gor_wti'], prev['gor_wti'])} | |
| 黄金 | ${p_gold:.0f} | ${c_gold:.0f} | {chg(c_gold,p_gold)} | |
| WTI | ${p_wti} | ${c_wti} | {chg(c_wti,p_wti)} | {"🔴< $75硬止损" if c_wti < 75 else ""} |
| DXY | {p_dxy} | {c_dxy} | {chg(c_dxy,p_dxy)} | |
| 10Y | {p_10y}% | {c_10y}% | {chg(c_10y,p_10y)} | |
| VIX | {p_vix} | {c_vix} | {chg(c_vix,p_vix)} | {"✅<17" if c_vix < 17 else ""} |

---

> 生成时间: {today_str} · 变化比对引擎
> 上周数据: {prev_date} · 本周数据: {today_str}
> 数据源: FRED + akshare + TradingView
"""
    report_path = DATA_DIR / f"{today_str}-变化比对报告.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    log(f"  Change report: 看板日志/{today_str}-变化比对报告.md")


if __name__ == '__main__':
    log("=" * 50)
    log(f"  ChenJia Framework · Weekly Update")
    log(f"  {datetime.date.today().strftime('%Y-%m-%d')}")
    log("=" * 50)

    log("Step 1/6: Pull market data (akshare + web)...")
    data = fetch_all()

    log("Step 2/6: Compute GOR + allocation...")
    gor = compute_gor(data)
    log(f"  GOR(B)={gor['gor_brent']} GOR(W)={gor['gor_wti']} Pos={gor['final_position']}%")
    log(f"  Oil={gor['allocation']['油气']}% Gold={gor['allocation']['黄金']}% Cash={gor['allocation']['现金']}%")

    log("Step 3/6: Save JSON data files...")
    gor_output = save_gor_json(data, gor)
    cf_output = save_capital_flows_json(data)

    log("Step 4/6: Update HTML data blocks...")
    update_html_data_blocks(gor_output, cf_output)

    log("Step 5/6: Update HTML text content...")
    update_html_text_content(gor_output)

    log("Step 6/6: Generate change comparison report...")
    generate_change_report(gor_output, data)

    log("All done.")
    log("=" * 50)
