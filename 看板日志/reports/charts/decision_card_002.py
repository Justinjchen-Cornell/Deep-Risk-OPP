import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)
fig.patch.set_facecolor('#0a0e14')
ax.set_facecolor('#0a0e14')
ax.set_xlim(0, 8)
ax.set_ylim(0, 5.5)
ax.set_xticks([]); ax.set_yticks([])
for spine in ax.spines.values(): spine.set_visible(False)

def box(x, y, w, h, color='#1a2030', lc='#30363d', lw=1.2):
    ax.add_patch(mpatches.FancyBboxPatch((x,y), w, h, boxstyle='round,pad=0.08',
        facecolor=color, edgecolor=lc, linewidth=lw, zorder=2))

def txt(x, y, s, size=8, color='#c9d1d9', bold=False, ha='left', mono=True):
    ax.text(x, y, s, fontsize=size, color=color, fontfamily='monospace' if mono else 'sans-serif',
            fontweight='bold' if bold else 'normal', ha=ha, va='center', zorder=3)

# ─── HEADER ───────────────────────────────────────────────
box(0.3, 4.95, 7.4, 0.45, '#1a2030', '#ffa50044', 1.5)
txt(4.0, 5.33, 'GOR INVESTMENT DECISION CARD', 13, '#fff', True, 'center')
txt(4.0, 5.06, 'July 19, 2026  ·  Weekly Pulse #002', 7, '#ffa500', False, 'center')

# ─── GOR BAR ──────────────────────────────────────────────
box(0.3, 3.55, 7.4, 1.3, '#161b22', '#30363d')
# GOR bar
bar_w = 5.6
bar_h = 0.18
bar_x, bar_y = 1.9, 4.35
ax.add_patch(mpatches.FancyBboxPatch((bar_x, bar_y), bar_w, bar_h, boxstyle='round,pad=0.02',
    facecolor='#21262d', edgecolor='none', zorder=1))
fill_w = bar_w * 49.1 / 80
ax.add_patch(mpatches.FancyBboxPatch((bar_x, bar_y), fill_w, bar_h, boxstyle='round,pad=0.02',
    facecolor='#f85149', edgecolor='none', alpha=0.85, zorder=2))
txt(1.9, 4.62, 'GOR(WTI)', 8, '#8b949e', False, 'left')
txt(7.5, 4.62, '49.1', 12, '#fff', True, 'right')
txt(4.7, 4.62, 'EXTREME OPPORTUNITY  (>=45)', 7, '#f85149', True, 'center')
txt(1.9, 4.15, 'GOR(Brent): 46.3', 7, '#8b949e')
txt(1.9, 3.98, 'vs #001 (57.7): -8.6  |  vs 2020 (69.5): -29%  |  vs ATH (78.0): -37%', 6.5, '#555')
txt(1.9, 3.78, 'vs Historical Mean (15-25): 2.0x overvalued', 6.5, '#555')

# ─── LEFT COLUMN: MARKET ─────────────────────────────────
box(0.3, 1.15, 3.55, 2.3, '#161b22', '#30363d')
txt(2.1, 3.32, 'MARKET SNAPSHOT', 9, '#8b949e', True, 'center')
items = [
    ('Gold', '$4,011', '#ffa500'),
    ('WTI', '$81.72', '#3fb950'),
    ('Brent', '$86.73', '#3fb950'),
    ('DXY', '100.93', '#d2991d'),
    ('10Y', '4.57%', '#d2991d'),
    ('VIX', '18.77', '#f85149'),
    ('Copper', '$6.29/lb', '#8b949e'),
]
for i, (label, val, col) in enumerate(items):
    y = 3.15 - i * 0.28
    txt(0.7, y, label, 7, '#8b949e')
    txt(2.6, y, val, 7, col, True, 'right')

# ─── RIGHT COLUMN: FRAMEWORK ──────────────────────────────
box(4.1, 1.15, 3.6, 2.3, '#161b22', '#30363d')
txt(5.9, 3.32, 'FRAMEWORK SIGNAL', 9, '#8b949e', True, 'center')
fw_items = [
    ('GOR >= 45', '#f85149', True),
    ('Oil deeply undervalued', '#c9d1d9', False),
    ('Mean reversion ACTIVE', '#3fb950', False),
    ('Oil at framework weight', '#c9d1d9', False),
    ('', '#555', False),
    ('HARD STOP: RELEASED', '#3fb950', True),
]
for i, (label, col, b) in enumerate(fw_items):
    y = 3.15 - i * 0.25
    txt(4.4, y, label, 7, col, b)

# ─── BOTTOM: ALLOCATION + TRIGGERS ────────────────────────
box(0.3, 0.15, 7.4, 0.9, '#161b22', '#30363d')
# Allocation bar
alloc = [('Oil', 25, '#f85149'), ('Gold', 20, '#ffa500'), ('A-Shr', 7, '#8b949e'), ('Cash', 48, '#555')]
x_start = 0.6
for label, pct, col in alloc:
    w = pct / 100 * 3.0
    ax.add_patch(mpatches.FancyBboxPatch((x_start, 0.72), w, 0.22, boxstyle='round,pad=0.02',
        facecolor=col, edgecolor='none', alpha=0.7, zorder=2))
    if pct >= 15:
        txt(x_start + w/2, 0.83, f'{label} {pct}%', 6.5, '#fff', True, 'center')
    x_start += w + 0.02

txt(0.6, 0.55, 'TRIGGERS:', 7, '#8b949e', True)
txt(0.6, 0.35, 'VIX>20 => speed ELEVATED  |  WTI>$85 => GOR nearing recovery  |  FOMC => DXY risk  |  SPY/QQQ distribution', 5.5, '#555')

# ─── DISCLAIMER ──────────────────────────────────────────
txt(4.0, 0.05, 'RESEARCH FRAMEWORK ONLY — NOT INVESTMENT ADVICE', 5, '#333', False, 'center')

out = r'c:\Users\Admin\Documents\Justinjchen-资料备份\08.投资决策框架\看板日志\decision_card_002.png'
fig.savefig(out, dpi=150, facecolor='#0a0e14', bbox_inches='tight', pad_inches=0.15)
print(f'Saved: {out}')
