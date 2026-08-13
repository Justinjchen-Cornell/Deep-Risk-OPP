import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig = plt.figure(figsize=(18, 10), dpi=150, facecolor='#fff')
gs = fig.add_gridspec(2, 1, height_ratios=[1.2, 1],
    hspace=0.35, left=0.04, right=0.98, top=0.92, bottom=0.05)

# ═══════════════════════════════════════════════════════════
# PANEL 1: DECISION TREE
# ═══════════════════════════════════════════════════════════
ax = fig.add_subplot(gs[0])
ax.set_xlim(0, 16); ax.set_ylim(0, 8)
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)

# Root node
def node(x, y, w, h, text, color='#333', bg='#f8f8f8', bold=True, sz=8):
    ax.add_patch(mpatches.FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle='round,pad=4',
        facecolor=bg, edgecolor=color, linewidth=2 if bold else 1))
    ax.text(x, y, text, fontsize=sz, color=color, fontfamily='monospace',
            fontweight='bold' if bold else 'normal', ha='center', va='center', linespacing=1.2)

# ── Level 0: Root ──
node(8, 7.3, 3.5, 0.9, 'US-IRAN CEASEFIRE\nEffective Duration', '#000', '#f0f0f0', True, 10)

# ── Level 1: Duration branches ──
branches_l1 = [
    (3.5, 'SHORT\n< 20 days\n12.2%', '#c0392b', '#fff5f5'),
    (8.0, 'MEDIUM\n20-40 days\n41.3%', '#e67e22', '#fffaf5'),
    (12.5, 'LONG\n> 40 days\n18.8%', '#2e7d32', '#f5fff5'),
]
for x, label, color, bg in branches_l1:
    ax.plot([8, x], [6.8, 5.5], color='#ccc', lw=1.2, zorder=0)
    node(x, 5.3, 2.2, 1.0, label, color, bg, True, 7.5)

# ── Level 2: Intensity sub-branches ──
# Short branches
ax.plot([3.5, 1.8], [4.8, 3.8], color='#ddd', lw=0.8)
ax.plot([3.5, 3.5], [4.8, 3.8], color='#ddd', lw=0.8)
ax.plot([3.5, 5.2], [4.8, 3.8], color='#ddd', lw=0.8)
# Medium branches
ax.plot([8.0, 6.3], [4.8, 3.8], color='#ddd', lw=0.8)
ax.plot([8.0, 8.0], [4.8, 3.8], color='#ddd', lw=0.8)
ax.plot([8.0, 9.7], [4.8, 3.8], color='#ddd', lw=0.8)
# Long branches
ax.plot([12.5, 10.8], [4.8, 3.8], color='#ddd', lw=0.8)
ax.plot([12.5, 12.5], [4.8, 3.8], color='#ddd', lw=0.8)
ax.plot([12.5, 14.2], [4.8, 3.8], color='#ddd', lw=0.8)

leaves = [
    # Short (<20d)
    (1.8, 3.5, 'LOW\n4.5%', '$79', 'Energy + Refining', '#e74c3c33', '#c0392b'),
    (3.5, 3.5, 'MID\n7.5%', '$92', 'Energy + Refining', '#e74c3c55', '#c0392b'),
    (5.2, 3.5, 'HIGH\n3.0%', '$110', 'ALL-IN Energy + Oil Calls', '#e74c3c88', '#c0392b'),
    # Medium (20-40d)
    (6.3, 3.5, 'LOW\n12.4%', '$86', 'Energy + Gold + TIPS', '#e67e2233', '#e67e22'),
    (8.0, 3.5, 'MID\n20.6%', '$100', 'BASE: 40/20/20/20', '#e67e2255', '#e67e22'),
    (9.7, 3.5, 'HIGH\n8.3%', '$119', 'MAX Energy + Tail Hedge', '#e67e2288', '#e67e22'),
    # Long (>40d)
    (10.8, 3.5, 'LOW\n5.6%', '$99', 'Profit-take + TIPS + Gold', '#2e7d3233', '#2e7d32'),
    (12.5, 3.5, 'MID\n9.4%', '$116', 'Energy + Refining + Gold', '#2e7d3255', '#2e7d32'),
    (14.2, 3.5, 'HIGH\n3.8%', '$138', 'ALL-IN Energy + Tail Hedge', '#2e7d3288', '#2e7d32'),
]

for x, y, label, wti, strategy, bg, color in leaves:
    node(x, y, 1.5, 1.1, label, color, bg, False, 6.5)
    ax.text(x, y-0.72, f'WTI: {wti}', fontsize=5.5, color='#888', fontfamily='monospace', ha='center')
    ax.text(x, y-0.95, strategy, fontsize=5, color='#555', fontfamily='monospace', ha='center')

# No-ceasefire branch
ax.plot([8, 14.5], [6.8, 5.8], color='#000', lw=2, zorder=0)
node(14.5, 5.5, 2.0, 0.9, 'NO DEAL\n25.0%', '#000', '#fff', True, 8)
ax.text(14.5, 4.65, 'WTI: $105', fontsize=7, color='#000', fontfamily='monospace', fontweight='bold', ha='center')
ax.text(14.5, 4.35, 'Long Energy + Short EEM', fontsize=6, color='#555', fontfamily='monospace', ha='center')

# Legend row
ax.text(0.5, 1.8, 'INTENSITY:', fontsize=7, color='#888', fontfamily='monospace')
for i, (label, color) in enumerate([('Low', '#e74c3c33'), ('Mid', '#e74c3c55'), ('High', '#e74c3c88')]):
    x = 3.5 + i*2.5
    ax.add_patch(mpatches.FancyBboxPatch((x, 1.5), 2.0, 0.5, boxstyle='round,pad=2', facecolor=color, edgecolor='#ccc', lw=0.5))
    ax.text(x+1, 1.75, label, fontsize=7, color='#555', fontfamily='monospace', ha='center')

# Title
ax.set_title('DECISION TREE: Ceasefire Duration x Conflict Intensity', fontsize=15,
    color='#000', fontfamily='monospace', fontweight='bold', pad=12, loc='left')

# ═══════════════════════════════════════════════════════════
# PANEL 2: ASSET MATRIX
# ═══════════════════════════════════════════════════════════
ax2 = fig.add_subplot(gs[1])
ax2.set_facecolor('#fafafa')
ax2.set_xlim(0, 100); ax2.set_ylim(-30, 70)
for s in ['top','right']: ax2.spines[s].set_visible(False)
ax2.spines['left'].set_color('#ddd'); ax2.spines['bottom'].set_color('#ddd')

assets = [
    ('VLCC/FRO', 47.3, '#c0392b', '██'),
    ('Shale/DVN', 42.2, '#e74c3c', '██'),
    ('Energy/XLE', 26.5, '#e67e22', '██'),
    ('Chems', 21.9, '#f39c12', '█'),
    ('Gold/GLD', 16.9, '#f1c40f', '█'),
    ('BTC', 14.2, '#2ecc71', '█'),
    ('TIPS', 11.6, '#3498db', '░'),
    ('China Refine', 6.2, '#9b59b6', '░'),
    ('DXY', 5.6, '#95a5a6', '░'),
    ('Refiners/VLO', 1.6, '#bdc3c7', '░'),
    ('Bonds/TLT', -11.0, '#e74c3c', ''),
    ('EM/EEM', -16.5, '#c0392b', ''),
]

y = 60
for name, ret, color, bar in assets:
    ax2.barh(y, ret, height=7, color=color, alpha=0.7 if ret>0 else 0.9, zorder=2)
    ax2.text(ret + (2 if ret>0 else -8), y, f'{ret:+.1f}%', fontsize=8, color='#000' if abs(ret)>10 else '#888',
             fontfamily='monospace', fontweight='bold' if abs(ret)>20 else 'normal', va='center')
    ax2.text(-2, y, name, fontsize=8, color='#555', fontfamily='monospace', ha='right', va='center')
    y -= 8

ax2.axvline(x=0, color='#ccc', lw=1)
ax2.set_ylim(-5, 68)
ax2.set_xlim(-15, 60)
ax2.tick_params(colors='#888', labelsize=7)
ax2.set_xlabel('6-Month Expected Return (%)', color='#888', fontsize=8, fontfamily='monospace')
ax2.set_title('EXPECTED RETURNS: Asset Class Mapping', fontsize=15, color='#000',
    fontfamily='monospace', fontweight='bold', pad=12, loc='left')

# Top winners annotation
ax2.text(48, 64, 'TOP WINNERS', fontsize=7, color='#c0392b', fontfamily='monospace', fontweight='bold')
ax2.text(48, 61, 'Oil tankers + Shale', fontsize=6.5, color='#888', fontfamily='monospace')
ax2.text(-12, 64, 'TOP LOSERS', fontsize=7, color='#c0392b', fontfamily='monospace', fontweight='bold')
ax2.text(-12, 61, 'EM + Long Bonds', fontsize=6.5, color='#888', fontfamily='monospace')

# Footer
fig.text(0.5, 0.01, 'Source: Kimi3 Quantitative Model + Six Masters Consensus  |  Research Framework  |  Not Investment Advice',
    fontsize=6.5, color='#bbb', fontfamily='monospace', ha='center')

out = r'c:\Users\Admin\Documents\陈嘉-资料备份\08.投资决策框架\看板日志\reports\charts\ceasefire_decision_tree.png'
fig.savefig(out, dpi=150, facecolor='#fff', bbox_inches='tight', pad_inches=0.3)
print('SAVED')
