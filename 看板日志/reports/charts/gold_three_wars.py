import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig = plt.figure(figsize=(14, 9), dpi=150, facecolor='#ffffff')
gs = fig.add_gridspec(3, 1, height_ratios=[1.2, 1.5, 1],
    hspace=0.35, left=0.10, right=0.94, top=0.92, bottom=0.06)

# ═══════════════════════════════════════════════════════════════
# PANEL 1: THREE WARS — Force Diagram
# ═══════════════════════════════════════════════════════════════
ax1 = fig.add_subplot(gs[0])
ax1.set_xlim(0, 12); ax1.set_ylim(0, 4)
ax1.set_xticks([]); ax1.set_yticks([])
for s in ax1.spines.values(): s.set_visible(False)
ax1.set_title('THE THREE WARS OF GOLD', fontsize=14, color='#000', fontfamily='monospace',
              fontweight='bold', pad=8, loc='left')

wars = [
    (0.5, 'WAR 1: INTEREST RATE', 'Short-term BEARISH', '#c0392b',
     ['Oil pushes inflation higher','Rates stay elevated (10Y: 4.57%)','Paper gold sold for yield','DXY 100.93 — USD strong'],
     '↓', '#c0392b'),
    (4.2, 'WAR 2: CENTRAL BANK BUYING', 'Long-term BULLISH', '#2e7d32',
     ['PBoC 19-month buying streak','Global CBs: Q1 net 244 tonnes','Buying for monetary SOVEREIGNTY','Not for yield — for independence'],
     '↑', '#2e7d32'),
    (7.9, 'WAR 3: CLEARING & SETTLEMENT', 'Structural BULLISH', '#1565c0',
     ['Eastern markets building clearing channels','Gold pricing power shifting East','De-dollarization infrastructure','Multi-decade structural trend'],
     '↑', '#1565c0'),
]

for x, title, subtitle, color, bullets, arrow, arrow_c in wars:
    # Card
    ax1.add_patch(mpatches.FancyBboxPatch((x, 0.3), 3.5, 3.2, boxstyle='round,pad=8',
        facecolor='#fafafa', edgecolor=color, linewidth=1.5))
    # Title
    ax1.text(x+1.75, 3.15, title, fontsize=10, color='#000', fontfamily='monospace',
             fontweight='bold', ha='center')
    ax1.text(x+1.75, 2.85, subtitle, fontsize=8, color=color, fontfamily='monospace',
             fontweight='bold', ha='center')
    # Arrow
    ax1.text(x+3.2, 2.5, arrow, fontsize=20, color=arrow_c, fontfamily='monospace', ha='center',
             fontweight='bold')
    # Bullets
    for j, b in enumerate(bullets):
        ax1.text(x+0.3, 2.0 - j*0.35, f'— {b}', fontsize=7, color='#555', fontfamily='monospace')

# Time arrow at bottom
ax1.annotate('', xy=(11.5, 0.15), xytext=(0.5, 0.15),
    arrowprops=dict(arrowstyle='->', color='#ccc', lw=2))
ax1.text(0.5, 0.0, 'NOW', fontsize=7, color='#888', fontfamily='monospace', fontweight='bold')
ax1.text(11, 0.0, '2027+', fontsize=7, color='#888', fontfamily='monospace')

# ═══════════════════════════════════════════════════════════════
# PANEL 2: GOLD PRICE PATH — Projection with Crash Zone
# ═══════════════════════════════════════════════════════════════
ax2 = fig.add_subplot(gs[1])
ax2.set_facecolor('#fafafa')
for s in ['top','right']: ax2.spines[s].set_visible(False)
ax2.spines['left'].set_color('#ddd'); ax2.spines['bottom'].set_color('#ddd')

# Historical + projected path
months = ['2020','2021','2022','2023','2024','2025','2026\nH1','2026\nH2','2027\nH1','2027\nH2']
gold_path = [1770, 1800, 1800, 1950, 2400, 3470, 4800, 3800, 3000, 5000]  # projection
x = range(len(months))

# Draw path
for i in range(len(x)-1):
    c = '#333' if i < 6 else ('#888' if i < 7 else '#f85149')
    ls = '-' if i < 6 else '--'
    ax2.plot([x[i], x[i+1]], [gold_path[i], gold_path[i+1]],
             color=c, linewidth=2.5 if i < 6 else 2, linestyle=ls, alpha=0.8)

# Shaded uncertainty zone
ax2.fill_between([6, 7, 8, 9], [3800, 2800, 2500, 4000], [3800, 3200, 3500, 6000],
    color='#f85149', alpha=0.06)

# Crash zone highlight
ax2.axvspan(7.4, 8.6, facecolor='#f85149', alpha=0.08, edgecolor='none')
ax2.text(8, 2100, 'LIQUIDITY\nCRISIS\nCRASH ZONE', fontsize=9, color='#c0392b',
         fontfamily='monospace', fontweight='bold', ha='center', va='top',
         bbox=dict(boxstyle='round,pad=6', facecolor='#fff5f5', edgecolor='#f85149', alpha=0.9, linewidth=1.5))

# Buy signal marker
ax2.scatter([7.8], [2500], color='#3fb950', s=200, zorder=10, edgecolors='#fff', linewidth=2)
ax2.annotate('BUY SIGNAL\nGold crushed →\nMaximum fear =\nMaximum opportunity',
    xy=(7.8, 2500), xytext=(6.2, 1800),
    fontsize=8, color='#3fb950', fontfamily='monospace', fontweight='bold',
    arrowprops=dict(arrowstyle='->', color='#3fb950', lw=2),
    bbox=dict(boxstyle='round,pad=4', facecolor='#fff', edgecolor='#3fb950', alpha=0.9))

# "We are here" marker
ax2.scatter([6], [3800], color='#000', s=120, zorder=10)
ax2.annotate('WE ARE\nHERE\n(Jul 2026)', xy=(6, 3800), xytext=(5, 4200),
    fontsize=8, color='#000', fontfamily='monospace', fontweight='bold',
    arrowprops=dict(arrowstyle='->', color='#000', lw=1.5),
    bbox=dict(boxstyle='round,pad=4', facecolor='#fff', edgecolor='#000', alpha=0.9))

# Gold ATH and current
ax2.axhline(y=5586, color='#ccc', linestyle=':', linewidth=1)
ax2.text(9.2, 5650, 'ATH $5,586 (Jan 2026)', fontsize=7, color='#aaa', fontfamily='monospace', ha='right')

ax2.set_xticks(x); ax2.set_xticklabels(months, fontsize=8, fontfamily='monospace')
ax2.tick_params(colors='#888', labelsize=8)
ax2.set_ylim(1200, 6200)
ax2.set_title('GOLD PRICE PATH: Historical + Projected', fontsize=14, color='#000',
              fontfamily='monospace', fontweight='bold', pad=8, loc='left')
ax2.set_ylabel('Gold ($/oz)', color='#888', fontsize=9, fontfamily='monospace')

# Legend
leg = [mpatches.Patch(color='#333', label='Historical'),
       mpatches.Patch(color='#888', label='Projected'),
       mpatches.Patch(color='#f85149', alpha=0.2, label='Crash Zone')]
ax2.legend(handles=leg, fontsize=7, loc='upper left', framealpha=0.8, edgecolor='#ddd')

# ═══════════════════════════════════════════════════════════════
# PANEL 3: TIMING FRAMEWORK — Buy Decision Tree
# ═══════════════════════════════════════════════════════════════
ax3 = fig.add_subplot(gs[2])
ax3.set_xlim(0, 12); ax3.set_ylim(0, 3)
ax3.set_xticks([]); ax3.set_yticks([])
for s in ax3.spines.values(): s.set_visible(False)
ax3.set_title('BUY TIMING FRAMEWORK', fontsize=14, color='#000', fontfamily='monospace',
              fontweight='bold', pad=8, loc='left')

phases = [
    (0.3, 'PHASE 1: NOW', '#888', 'Hold 20% gold (PBoC floor).\n50% cash. Wait. Do not chase.',
     'Rate war suppresses paper gold.\nCB buying supports physical.'),
    (4.2, 'PHASE 2: CRASH', '#f85149', 'Gold plunges on liquidity crisis.\nPanic selling. Margin calls.\nALL assets crushed.',
     'Gold could fall 30-50% from here.\nThis is the signal, not the threat.'),
    (8.1, 'PHASE 3: BUY', '#3fb950', 'Deploy cash. Buy physical gold.\nBuy top-tier tech at distressed\nvaluations. Maximum position.',
     'After every crisis, gold re-launches\nand becomes the best performer.'),
]

for x, title, color, action, context in phases:
    ax3.add_patch(mpatches.FancyBboxPatch((x, 0.2), 3.5, 2.5, boxstyle='round,pad=8',
        facecolor='#fafafa', edgecolor=color, linewidth=1.5))
    ax3.text(x+1.75, 2.4, title, fontsize=11, color=color, fontfamily='monospace',
             fontweight='bold', ha='center')
    ax3.text(x+0.2, 1.8, action, fontsize=7.5, color='#000', fontfamily='monospace', va='top')
    ax3.text(x+0.2, 0.5, context, fontsize=6.5, color='#888', fontfamily='monospace', va='top')

# Arrows between phases
for x1, x2, y in [(3.9, 4.1, 1.5), (7.8, 8.0, 1.5)]:
    ax3.annotate('', xy=(x2, y), xytext=(x1, y),
        arrowprops=dict(arrowstyle='->', color='#bbb', lw=2))

# ─── Footer ────────────────────────────────────────────────────
fig.text(0.5, 0.01, 'Deep-Risk-OPP  |  Research Framework  |  Not Investment Advice  |  Source: "Three Wars of Gold" thesis (Jul 17, 2026)',
         fontsize=6.5, color='#bbb', fontfamily='sans-serif', ha='center')

out = r'c:\Users\Admin\Documents\Justinjchen-资料备份\08.投资决策框架\看板日志\gold_three_wars_chart.png'
fig.savefig(out, dpi=150, facecolor='#ffffff', bbox_inches='tight', pad_inches=0.3)
print(f'Saved: {out}')
