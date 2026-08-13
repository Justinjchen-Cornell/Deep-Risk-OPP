import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Match reference image: ~1028x543, dark theme, blue-green-orange-red-purple accents
fig = plt.figure(figsize=(14, 7.5), dpi=100, facecolor='#111827')
gs = fig.add_gridspec(4, 5, height_ratios=[1, 2.5, 2.5, 1],
    hspace=0.35, wspace=0.2, left=0.04, right=0.98, top=0.94, bottom=0.04)

COLORS = {'bg':'#111827','card':'#1a2235','line':'#243044','gold':'#f0b90b',
    'red':'#ef4444','green':'#22c55e','blue':'#3b82f6','purple':'#a855f7',
    'orange':'#f97316','text':'#e5e7eb','muted':'#94a3b8','cyan':'#06b6d4'}

def card(ax, x, y, w, h, color=None, alpha=1.0):
    ax.add_patch(mpatches.FancyBboxPatch((x,y), w, h, boxstyle='round,pad=6',
        facecolor=COLORS['card'], edgecolor=color or COLORS['line'], linewidth=1.5, alpha=alpha))

def txt(ax, x, y, s, size=10, color=None, bold=False, ha='left', va='center', mono=False):
    ax.text(x, y, s, fontsize=size, color=color or COLORS['text'],
        fontfamily='monospace' if mono else 'sans-serif',
        fontweight='bold' if bold else 'normal', ha=ha, va=va)

# ═══════════ ROW 0: HEADER ═══════════
ax_h = fig.add_subplot(gs[0, :])
ax_h.set_xlim(0,14); ax_h.set_ylim(0,1); ax_h.set_xticks([]); ax_h.set_yticks([])
for s in ax_h.spines.values(): s.set_visible(False)
txt(ax_h, 7, 0.7, '向心坍缩 · 建仓日历 v2.0', size=18, color='#f0b90b', bold=True, ha='center', mono=True)
txt(ax_h, 7, 0.3, '五节点 × 七档资产 · A股人民币计价 · 仅限国内投资 · 基准日 2026.07.31 | GOR=47.9 WTI=$85.56 10Y=4.67% DXY=100.12', size=9, color=COLORS['muted'], ha='center')

# ═══════════ ROW 1: FIVE NODE CARDS ═══════════
nodes_data = [
    ('节点一', '预热建仓', '7末-8月', '37→50%', COLORS['orange'], '布伦特95-110\n分批建仓·不追高'),
    ('节点二', '加仓期', '8-9月中', '50→61%', COLORS['blue'], '布伦特100-110\n趋势确认·加码主线'),
    ('节点三', '兑现+对冲', '9中-10初', '61→53%', COLORS['red'], '布伦特120-150\n兑现利润·不追高'),
    ('节点四⭐', '速冻买点', '10-11月', '53→69%', COLORS['purple'], '美元荒·全资产回调\n⭐最佳二次布局'),
    ('节点五', '主升兑现', '12月+', '69→45%', COLORS['green'], '美元放水·主升浪\n收获期·分批兑现'),
]

for i, (tag, title, time, pos, color, desc) in enumerate(nodes_data):
    ax = fig.add_subplot(gs[1, i])
    ax.set_xlim(0,10); ax.set_ylim(0,10)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    card(ax, 0.2, 0.2, 9.6, 9.6, color=color+'66')
    # Tag badge
    ax.add_patch(mpatches.FancyBboxPatch((2.5,8.5), 5, 1.0, boxstyle='round,pad=4',
        facecolor=color+'33', edgecolor=color, linewidth=1))
    txt(ax, 5, 9.0, tag+' · '+title, size=12, color=color, bold=True, ha='center', mono=True)
    txt(ax, 5, 7.8, time, size=9, color=COLORS['muted'], ha='center')
    txt(ax, 5, 7.0, pos, size=14, color=color, bold=True, ha='center', mono=True)
    txt(ax, 5, 4.5, desc, size=10, color=COLORS['muted'], ha='center', va='center', linespacing=1.5)

# ═══════════ ROW 2: ASSET CARDS (7 columns → wrap) ═══════════
assets = [
    ('🛢️ 原油\n华宝油气', '布伦特95-100→3-5%\n布伦特<88减50%', COLORS['red']),
    ('🪨 煤炭\n神华601088', '神华30-32元→5-8%\n神华<28元减仓', COLORS['orange']),
    ('⚙️ 铝\n云铝/天山铝业', '沪铝19500-20000→4-6%\n沪铝<18500减仓', COLORS['cyan']),
    ('🔶 铜\n紫金矿业601899', '紫金19-20元→3-5%\n沪铜<70000减仓', COLORS['blue']),
    ('💎 黄金\nETF 518880', '现货4000-4200$→10-12%\n现货<3850减20%', COLORS['gold']),
    ('🥈 白银\n盛达资源', '现货55-58$→2-3%\n现货<50$离场', COLORS['muted']),
    ('📜 国债\nETF 511260', '10Y 3.2-3.4%→10-12%\n收益率<3%转配置', COLORS['green']),
]

for i, (name, detail, color) in enumerate(assets):
    ax = fig.add_subplot(gs[2, i]) if i < 5 else fig.add_subplot(gs[2, i-5+5]) if i >=5 else None
    # Use first 5 columns for 5 assets, remaining 2 in the last 2 columns of the 5-column grid
    # Actually simpler: use all 5 cols, put 2 assets in separate sub-figures
    col_idx = i if i < 5 else (i-5)  # This won't work cleanly with 7 assets in 5 columns
    # Let me just use the first 5 and stack 2 in one
    pass

# Actually need to handle 7 assets in 5 grid slots. Let me restructure.
# Put rows 2-3 together for the asset grid.
# Simpler: use a 2-row layout for assets in the PNG

# Let me restart with a cleaner approach for the whole figure.
print('Need restructure')