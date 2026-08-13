import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, ax = plt.subplots(figsize=(18, 9), dpi=150, facecolor='#ffffff')
ax.set_facecolor('#fafafa')
ax.set_xlim(0, 18); ax.set_ylim(0, 10)
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)

# ═══════════ TOP: MINING STOCK BREAKOUT SIGNAL ═══════════
ax.add_patch(mpatches.FancyBboxPatch((0.3, 7.3), 17.4, 2.4, boxstyle='round,pad=6',
    facecolor='#f0fdf4', edgecolor='#22c55e', linewidth=2))
ax.text(1, 9.3, 'THE SIGNAL: MINING STOCKS BREAKING 20-YEAR TRENDLINES', fontsize=14,
    color='#166534', fontweight='bold')
ax.text(1, 8.9, 'Same macro signal, five simultaneous confirmations:', fontsize=10, color='#333')

signals = [
    ('XAU/Gold Ratio', 'BREAKING 20Y DOWNTREND', '★★★★★'),
    ('GDX Gold Miners', 'Mid-term trendline broken', '★★★★☆'),
    ('COPX Copper Miners', 'Testing weekly breakout', '★★★★☆'),
    ('Hecla (Silver)', 'Leading silver spot 1-3mo', '★★★★☆'),
    ('SPR + Futures', 'Fundamentals confirm', '★★★★★'),
]
for i, (name, status, stars) in enumerate(signals):
    x = 1 + i * 3.4
    ax.add_patch(mpatches.FancyBboxPatch((x, 7.6), 3.0, 1.6, boxstyle='round,pad=3',
        facecolor='#ffffff', edgecolor='#22c55e44', linewidth=1))
    ax.text(x+1.5, 9.0, name, fontsize=8, ha='center', fontweight='bold', color='#166534')
    ax.text(x+1.5, 8.6, status, fontsize=6.5, ha='center', color='#333')
    ax.text(x+1.5, 8.2, stars, fontsize=7, ha='center', color='#f59e0b')

# ═══════════ MIDDLE: THREE-PHASE STRATEGY ═══════════
phases = [
    ('PHASE 1', 'RALLY ENDGAME', 'Now - Mid Sep', '#f59e0b', '#fff7ed',
     'Oil: 50% → 15% (trim on the way up)\nGold: keep 15% base\nCopper/Silver: EXIT to 0%\nCash: 5% → 70%\nAdd: 5-8% put protection'),
    ('PHASE 2', 'CENTRIPETAL COLLAPSE', 'Mid Sep - Mid Oct', '#ef4444', '#fef2f2',
     'DO NOTHING. WAIT.\n\nNot bottom-fishing. Not averaging down.\nNot panic-selling the base.\n\n5 confirmation signals:\nFed +50bp  |  DXY>108  |  VIX>35\nNorthbound -15B  |  Gold -3%/day'),
    ('PHASE 3', 'WRONG-SELLER SALVAGE', 'Mid Oct - Dec', '#3b82f6', '#eff6ff',
     'Buy in 3 tranches (20/30/20% of cash)\n\nOrder of priority:\nGold first (fastest recovery)\n→ Oil (supply floor intact)\n→ Copper miners (deepest discount)\n→ Silver last (highest beta)'),
]

for i, (tag, title, time, color, bg, content) in enumerate(phases):
    x = 0.3 + i * 5.95
    ax.add_patch(mpatches.FancyBboxPatch((x, 3.8), 5.6, 3.1, boxstyle='round,pad=6',
        facecolor=bg, edgecolor=color, linewidth=2))
    ax.add_patch(mpatches.FancyBboxPatch((x+0.2, 6.55), 1.6, 0.5, boxstyle='round,pad=2',
        facecolor=color, edgecolor='none'))
    ax.text(x+1.0, 6.8, tag, fontsize=9, color='#fff', fontweight='bold', ha='center')
    ax.text(x+0.3, 6.1, title, fontsize=12, color=color, fontweight='bold')
    ax.text(x+0.3, 5.75, time, fontsize=8, color='#666')
    ax.text(x+0.3, 4.0, content, fontsize=8, color='#333', va='top', linespacing=1.4)

# Arrows between phases
for i in range(2):
    x1 = 5.9 + i * 5.95
    ax.annotate('', xy=(x1+0.25, 5.35), xytext=(x1, 5.35),
        arrowprops=dict(arrowstyle='->', color='#999', lw=3))

# ═══════════ BOTTOM: THE KEY NUMBERS ═══════════
ax.add_patch(mpatches.FancyBboxPatch((0.3, 0.3), 17.4, 2.5, boxstyle='round,pad=6',
    facecolor='#0f172a', edgecolor='#334155', linewidth=1))
key_nums = [
    ('70%', 'CASH before collapse', '#fbbf24'),
    ('25%', 'OIL HARD CAP (was 50%)', '#f87171'),
    ('15%', 'GOLD BASE - never sold', '#fbbf24'),
    ('3', 'BUY TRANCHES (20/30/20)', '#34d399'),
    ('5', 'COLLAPSE SIGNALS', '#f87171'),
]
for i, (num, label, color) in enumerate(key_nums):
    x = 1.0 + i * 3.4
    ax.text(x+1.0, 2.3, num, fontsize=28, color=color, fontweight='bold', ha='center')
    ax.text(x+1.0, 1.5, label, fontsize=8, color='#cbd5e1', ha='center')
    if i < 4:
        ax.plot([x+2.2, x+2.35], [2.2, 2.2], color='#334155', lw=1)

# ═══════════ TITLE ═══════════
fig.text(0.5, 0.965, 'SUPERCYCLE CONFIRMED. NOW PLAN THE COLLAPSE.', fontsize=20,
    color='#0f172a', fontweight='bold', ha='center')
fig.text(0.5, 0.94, 'Mining stocks break 20-year trendlines  →  3-phase strategy: Rally → Collapse → Salvage', fontsize=11,
    color='#64748b', ha='center')

fig.text(0.5, 0.015, 'Deep-Risk-OPP  ·  Research Framework  ·  Not Investment Advice', fontsize=8,
    color='#94a3b8', ha='center')

out = r'c:\Users\Admin\Documents\陈嘉-资料备份\08.投资决策框架\看板日志\reports\charts\supercycle_three_phase.png'
fig.savefig(out, dpi=150, facecolor='#ffffff', bbox_inches='tight', pad_inches=0.3)
print('SAVED')
