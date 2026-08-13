import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig = plt.figure(figsize=(20, 5.5), dpi=120, facecolor='#0a0e14')
gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.7], wspace=0.04,
    left=0.04, right=0.98, top=0.86, bottom=0.08)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])
ax3 = fig.add_subplot(gs[2])
fig.patch.set_facecolor('#0a0e14')

for ax in [ax1, ax2, ax3]:
    ax.set_facecolor('#0a0e14')

# ═══════════════════════════════════════════════════════════════
# LEFT PANEL: Sentiment Heatmap
# ═══════════════════════════════════════════════════════════════

tickers = ['NVDA','AMZN','SPY','AAPL','META','MSFT','QQQ','TSLA','GOOGL','GLD','TLT','XLE']
buzz =   [81,  79,  80,  79,  78,  77,  74,  73,  73,  43,  39,  34]
bull_pct=[28,  34,  26,  27,  22,  30,  24,  22,  26,  26,  14,  19]
bear_pct=[17,  18,  24,  18,  28,  23,  24,  28,  22,  23,  36,  12]
signals = ['Mild bullish','Strong bullish','!! DISTRIBUTION','Mild bullish',
           'Mild bearish','!! LATE-STAGE','!! DISTRIBUTION','Mild bearish',
           '!! LATE-STAGE','!! LATE-STAGE','Strong bearish','Mild bullish']

y_pos = range(len(tickers))

# Buzz bars
bars = ax1.barh(y_pos, buzz, height=0.55, color='#2a3a50', alpha=0.6, zorder=2)

# Color bars by signal
colors = []
for s in signals:
    if 'DISTRIBUTION' in s or 'LATE-STAGE' in s: colors.append('#f85149')
    elif 'bearish' in s: colors.append('#d2991d')
    elif 'bullish' in s: colors.append('#3fb950')
    else: colors.append('#30363d')

for bar, c in zip(bars, colors):
    bar.set_color(c)
    bar.set_alpha(0.75)

# Bull/Bear percentages as text
for i, (t, b, bu, be) in enumerate(zip(tickers, buzz, bull_pct, bear_pct)):
    ax1.text(b + 1.5, i, f'{bu}%', va='center', fontsize=7, color='#3fb950', fontfamily='monospace')
    ax1.text(b + 1.5, i-0.2, f'{be}%', va='center', fontsize=7, color='#f85149', fontfamily='monospace')

# Signal labels
for i, (s, c) in enumerate(zip(signals, colors)):
    if s:
        ax1.text(96, i, s, va='center', fontsize=7.5, color=c, fontfamily='monospace', fontweight='bold')

ax1.set_yticks(y_pos)
ax1.set_yticklabels(tickers, fontsize=12, fontfamily='monospace', color='#c9d1d9')
ax1.invert_yaxis()
ax1.set_xlim(0, 128)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_color('#30363d')
ax1.spines['bottom'].set_color('#30363d')
ax1.tick_params(colors='#8b949e', labelsize=9)
ax1.set_xlabel('Reddit Buzz Score', color='#8b949e', fontsize=9, fontfamily='monospace')
ax1.set_title('SENTIMENT HEATMAP', color='#fff', fontsize=15, fontfamily='monospace', fontweight='bold', pad=12)

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#f85149', alpha=0.75, label='Distribution / Late-Stage'),
    Patch(facecolor='#d2991d', alpha=0.75, label='Bearish'),
    Patch(facecolor='#3fb950', alpha=0.75, label='Bullish'),
]
ax1.legend(handles=legend_elements, loc='lower right', fontsize=8,
           facecolor='#161b22', edgecolor='#30363d', labelcolor='#8b949e')

# ═══════════════════════════════════════════════════════════════
# MIDDLE PANEL: 4 Key Signals
# ═══════════════════════════════════════════════════════════════

ax2.set_xlim(0, 10)
ax2.set_ylim(0, 10)
ax2.set_xticks([])
ax2.set_yticks([])
for spine in ax2.spines.values(): spine.set_visible(False)
ax2.set_title('KEY SIGNALS', color='#fff', fontsize=13, fontfamily='monospace', fontweight='bold', pad=10)

cards = [
    (0.2, 5.2, '1. Distribution', 'SPY, QQQ buzz 74-80\nbut sentiment dead flat.\nSilent selling likely.', '#f85149'),
    (0.2, 2.7, '2. Late-Stage', 'MSFT, GOOGL, GLD trend\nfalling but bulls > bears.\nClassic trap pattern.', '#d2991d'),
    (5.2, 5.2, '3. Contrarian', 'TLT: 14% bulls (most hated).\nXLE: 34 buzz (ignored).\nExtremes breed reversals.', '#3fb950'),
    (5.2, 2.7, '4. GOR x Sentiment', 'GOR=50.4 extreme but\nbuzz just 22 (nobody cares).\nComplacency -> repricing.', '#ffa500'),
]

for x, y, title, body, color in cards:
    ax2.add_patch(plt.Rectangle((x, y), 4.6, 2.2, facecolor='#161b22', edgecolor=color+'44', linewidth=1, zorder=2))
    ax2.text(x + 0.2, y + 1.85, title, color=color, fontsize=10, fontfamily='monospace', fontweight='bold')
    ax2.text(x + 0.2, y + 1.2, body, color='#8b949e', fontsize=7.5, fontfamily='monospace', va='top', linespacing=1.4)

# ═══════════════════════════════════════════════════════════════
# RIGHT PANEL: Buzz Collapse + GOR
# ═══════════════════════════════════════════════════════════════

ax3.set_xlim(0, 10)
ax3.set_ylim(0, 10)
ax3.set_xticks([])
ax3.set_yticks([])
for spine in ax3.spines.values(): spine.set_visible(False)
ax3.set_title('BUZZ COLLAPSE', color='#f85149', fontsize=13, fontfamily='monospace', fontweight='bold', pad=10)

# GOR box
ax3.add_patch(plt.Rectangle((3, 7.2), 4, 2.5, facecolor='#161b22', edgecolor='#ffa50044', linewidth=1))
ax3.text(5, 9.2, 'GOR = 50.4', color='#fff', fontsize=16, fontfamily='monospace', fontweight='bold', ha='center')
ax3.text(5, 8.4, 'EXTREME OPPORTUNITY', color='#f85149', fontsize=8, fontfamily='monospace', ha='center')
ax3.text(5, 7.8, 'Oil deeply undervalued vs gold', color='#8b949e', fontsize=7, fontfamily='monospace', ha='center')

# Buzz collapse chart
buzz_x = np.linspace(1, 9, 7)
buzz_y = np.array([50, 49, 47, 50, 50, 42, 22])
ax3.plot(buzz_x, buzz_y, color='#f85149', linewidth=2, alpha=0.9, marker='o', markersize=5, markerfacecolor='#fff')
# Area under
ax3.fill_between(buzz_x, buzz_y, 0, color='#f85149', alpha=0.08)
ax3.text(9.2, 22, '22', color='#f85149', fontsize=16, fontfamily='monospace', fontweight='bold', va='center')
ax3.text(5, 1.5, '7-Day Buzz Trend: 50 -> 49 -> 47 -> 50 -> 50 -> 42 -> 22', color='#8b949e', fontsize=7.5, fontfamily='monospace', ha='center')
ax3.text(5, 0.7, 'Market chatter halved. Historically: low buzz + extreme GOR = repricing soon.', color='#555', fontsize=6.5, fontfamily='monospace', ha='center')

# Bottom insight
for spine in ax3.spines.values(): spine.set_visible(False)
ax3.set_ylim(0, 65)

# ── Footer ──
fig.text(0.5, 0.02, 'Data: Adanos Reddit Sentiment API  |  Deep-Risk-OPP  |  Research Only  |  Not Investment Advice',
         fontsize=6.5, color='#484f58', fontfamily='monospace', ha='center')

# ── Title ──
fig.text(0.5, 0.96, 'DEEP-RISK-OPP  ·  MARKET SENTIMENT SCAN  ·  JULY 19, 2026', fontsize=11,
         color='#8b949e', fontfamily='monospace', fontweight='bold', ha='center')

out = r'c:\Users\Admin\Documents\陈嘉-资料备份\08.投资决策框架\看板日志\sentiment_scan_2026-07-19.png'
fig.savefig(out, dpi=120, facecolor='#0a0e14', bbox_inches='tight', pad_inches=0.3)
print(f'Saved: {out}')
