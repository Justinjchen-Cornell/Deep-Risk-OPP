#!/usr/bin/env python3
"""
周报栏目化：每周信号复盘 (P3-11)
从 wti_history.json 取近 N 天，生成"本周 GOR 走势 + 逐日信号 + 对错判定 + 下周关注"复盘。
用法:
    python scripts/weekly_report.py            # 默认最近 7 天
    python scripts/weekly_report.py --days 5
输出: 看板日志/weekly_report_YYYY-MM-DD.md（本地）+ 打印摘要
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "看板日志"


def zone_of(gor):
    if gor is None:
        return "—"
    if gor >= 45:
        return "极端区"
    if gor >= 30:
        return "修复区"
    if gor >= 20:
        return "公允区"
    return "泡沫区"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=7)
    args = ap.parse_args()

    hist = json.loads((BASE_DIR / 'wti_history.json').read_text(encoding='utf-8'))
    if len(hist) < 2:
        print('wti_history 数据不足，无法生成周报')
        sys.exit(1)

    week = hist[-args.days:]
    today = datetime.now().strftime('%Y-%m-%d')

    # 本周走势
    gors = [h.get('gor_wti') for h in week if h.get('gor_wti') is not None]
    wtis = [h.get('wti') for h in week if h.get('wti') is not None]
    first, last = week[0], week[-1]
    gor_start, gor_end = first.get('gor_wti'), last.get('gor_wti')
    wti_start, wti_end = first.get('wti'), last.get('wti')
    wti_chg = (wti_end - wti_start) / wti_start * 100 if wti_start else 0

    lines = [
        f"# 📊 本周信号复盘 · {week[0]['date']} → {week[-1]['date']}",
        "",
        f"> 自动生成于 {today} · 数据来自每日管道",
        "",
        "## 一、本周走势",
        "",
        f"| 指标 | 周一 | 周末 | 变动 |",
        "|---|---:|---:|---:|",
        f"| GOR(WTI) | {gor_start:.1f} | {gor_end:.1f} | {gor_end - gor_start:+.1f} |",
        f"| WTI | ${wti_start:.2f} | ${wti_end:.2f} | {wti_chg:+.1f}% |",
        "",
        f"GOR 区间分布：{zone_of(gor_start)} → {zone_of(gor_end)}",
        "",
        "## 二、逐日信号",
        "",
        "| 日期 | GOR | 区间 | WTI | 信号含义 |",
        "|---|---:|---|---:|---|",
    ]
    for h in week:
        g = h.get('gor_wti')
        w = h.get('wti')
        note = "极端：油便宜" if (g or 0) >= 45 else ("修复：持有" if (g or 0) >= 30 else "常态")
        lines.append(f"| {h['date']} | {g:.1f} | {zone_of(g)} | ${w:.2f} | {note} |")

    # 对错判定（本周信号 vs 周末实际）
    lines += [
        "",
        "## 三、本周判定",
        "",
    ]
    if (gor_start or 0) >= 45:
        verdict = "✅ 看多方向正确" if wti_chg > 0 else "⚠️ 看多方向未兑现（短期，12-24 月窗口未到）"
        lines.append(f"周初 GOR {gor_start:.1f}（极端区）→ 周末 WTI {wti_chg:+.1f}% — {verdict}")
    else:
        lines.append(f"周初 GOR {gor_start:.1f}（{zone_of(gor_start)}）→ 周末 WTI {wti_chg:+.1f}% — 常态观察周，无极端信号判定")
    lines.append("")
    lines.append("> 注：单周涨跌不验证 12-24 月结论；完整验证以 docs/track-record.md 证伪条款为准。")

    # 下周关注（风控日历联动）
    lines += [
        "",
        "## 四、下周关注",
        "",
        "- ⏰ **8 月底**：wti_history 满 30 天 → 动态止损（60日均线×0.85）自动启用",
        "- 🟠 **9 月**：明斯基时刻窗口（向心坍缩 2/3 条件已满足，流速待加速）",
        "- ⛏️ **矿业三信号**：金矿股/黄金比 0.085 站稳 · COPX 周线 >50 · 白银破 $70",
        f"- 📈 **证伪进度**：WTI ${wti_end:.2f}，距 $107.60 目标差 ${107.60 - wti_end:+.2f}",
        "",
        "---",
        "研究框架，不构成投资建议 · Deep-Risk-OPP",
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"weekly_report_{week[-1]['date']}.md"
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(f"周报已生成: {out}")
    print(f"  GOR {gor_start:.1f} → {gor_end:.1f} | WTI {wti_chg:+.1f}%")


if __name__ == '__main__':
    main()
