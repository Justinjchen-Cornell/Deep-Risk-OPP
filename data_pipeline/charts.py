"""
Deep-Risk-OPP — 统一图表生成入口 (P2)
所有图表的唯一生成模块：
  snapshot_chart()      — 每日 GOR 快照图（原 redraw_gor_chart）
  backtest_nav_chart()  — 回测 NAV 对比图
  generate_all()        — 一键生成全部图表（--mode chart）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.common import BASE_DIR, log


def snapshot_chart():
    """每日 GOR 决策卡快照图 → 看板日志/GOR_Daily_Snapshot.png"""
    import json
    from datetime import datetime
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    gor_path = BASE_DIR / "gor_latest.json"
    if not gor_path.exists():
        log("  CHART: No gor_latest.json, skipping")
        return None
    with open(gor_path, encoding='utf-8') as f:
        gd = json.load(f)
    gw = gd.get('gor_wti')
    gb = gd.get('gor_brent')
    gold = (gd.get('data') or {}).get('黄金期货', {}).get('price')
    wti = (gd.get('data') or {}).get('WTI原油', {}).get('price')
    regime = gd.get('regime', '?')

    fig, ax = plt.subplots(figsize=(10, 3), dpi=120)
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117')

    zones = [(45, 100, '#ff4444', 'EXTREME OPP'), (30, 45, '#ffaa00', 'RECOVERY'),
             (20, 30, '#00cc66', 'FAIR VALUE'), (0, 20, '#4488ff', 'BUBBLE')]
    for lo, hi, col, lbl in zones:
        ax.axhspan(lo, hi, facecolor=col, alpha=0.08)
        ax.text(0.98, (lo + hi) / 2, lbl, color=col, fontsize=7, ha='right',
                va='center', family='monospace', alpha=0.6, transform=ax.get_yaxis_transform())

    gor_val = gw or gb or 0
    bar_color = '#ff4444' if gor_val >= 45 else ('#ffaa00' if gor_val >= 30 else ('#00cc66' if gor_val >= 20 else '#4488ff'))
    ax.barh(1, gor_val, height=0.6, color=bar_color, alpha=0.8)
    ax.text(gor_val + 1, 1, f'GOR={gor_val:.1f}', color='#ffffff', fontsize=20, fontweight='bold', family='monospace', va='center')
    ax.text(gor_val + 1, 0.6, f'Gold=${gold:.0f}  WTI=${wti:.2f}  {regime}', color='#aaa', fontsize=9, family='monospace', va='center')

    ax.set_xlim(0, max(gor_val + 15, 85))
    ax.set_ylim(0, 2)
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#333')
    ax.tick_params(colors='#888', labelsize=8)
    ax.set_xlabel('GOR (Gold/Oil Ratio)', color='#888', fontsize=8)
    ax.set_title(f'Deep-Risk-OPP  |  {datetime.now().strftime("%Y-%m-%d")}', color='#666', fontsize=10, family='monospace', loc='left', pad=8)

    chart_path = BASE_DIR / "看板日志" / "GOR_Daily_Snapshot.png"
    fig.savefig(chart_path, dpi=120, facecolor='#0d1117', bbox_inches='tight')
    plt.close(fig)
    return str(chart_path)


def backtest_nav_chart(nav_history, bh_history, from_date, to_date,
                       ann_return=0.0, ann_bh=0.0):
    """回测 NAV 对比图 → 看板日志/backtest_chart_{from}_to_{to}.png"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(14, 6), dpi=120)
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117')

    dates_nav, vals_nav = zip(*nav_history)
    dates_bh, vals_bh = zip(*bh_history)

    ax.plot(dates_nav, vals_nav, color='#ffa500', linewidth=2.0, label=f'GOR Strategy ({ann_return:+.1%}/yr)')
    ax.plot(dates_bh, vals_bh, color='#888888', linewidth=1.2, linestyle='--', label=f'60/40 B&H ({ann_bh:+.1%}/yr)')
    ax.axhline(y=100, color='#ffffff', linewidth=0.5, alpha=0.2)

    ax.set_title(f'Deep-Risk-OPP Backtest  |  {from_date} -> {to_date}', color='#ffffff', fontsize=14, fontfamily='monospace', pad=12)
    ax.legend(loc='upper left', facecolor='#1a1a2e', edgecolor='#333', labelcolor='#ccc', fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333')
    ax.spines['bottom'].set_color('#333')
    ax.tick_params(colors='#888', labelsize=9)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}'))
    ax.grid(True, alpha=0.08, color='#ffffff')
    ax.set_ylabel('NAV (base=100)', color='#aaa', fontsize=10)

    chart_path = BASE_DIR / "看板日志" / f"backtest_chart_{from_date}_to_{to_date}.png"
    fig.savefig(chart_path, dpi=150, facecolor='#0d1117', bbox_inches='tight', pad_inches=0.4)
    plt.close(fig)
    return str(chart_path)


def generate_all():
    """生成全部图表（快照 + 若有缓存数据则回测图）。"""
    out = []
    try:
        p1 = snapshot_chart()
        if p1:
            out.append(p1)
            log(f"  CHART: GOR snapshot saved to {p1}")
    except Exception as e:
        log(f"  CHART error: {e}")
    return out


if __name__ == '__main__':
    for path in generate_all():
        print('generated:', path)
