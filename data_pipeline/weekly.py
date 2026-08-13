"""
Deep-Risk-OPP — 周度管道入口 (P1-2 拆分)
"""
import datetime
from data_pipeline.common import (log, fetch_all, compute_gor, save_gor_json,
    save_capital_flows_json, update_html_data_blocks, generate_weekly_content)



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


def run_weekly():
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

if __name__ == '__main__':
    run_weekly()
