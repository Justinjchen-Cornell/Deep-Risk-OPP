import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ─── Data ─────────────────────────────────────────────────────
# GOR journey: hard stop story
dates = ['Jun 25','Jul 05','Jul 12','Jul 15','Jul 17','Jul 19']
wti   = [69.87, 68.76, 71.50, 79.49, 79.36, 81.72]
gor   = [53.33, 57.44, 57.74, 50.85, 50.40, 49.10]
oil_pct = [5, 5, 5, 27, 25, 25]
vix   = [19.32, 16.15, 15.03, 16.86, 18.77, 18.77]

# Sentiment data
tickers_s = ['NVDA','AMZN','SPY','AAPL','MSFT','QQQ','GLD','TLT','XLE']
buzz_s   = [81, 79, 80, 79, 77, 74, 43, 39, 34]
bull_s   = [28, 34, 26, 27, 30, 24, 26, 14, 19]
bear_s   = [17, 18, 24, 18, 23, 24, 23, 36, 12]

fig = plt.figure(figsize=(16, 6.5), dpi=120, facecolor='#ffffff')
gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.8], wspace=0.25,
    left=0.05, right=0.97, top=0.88, bottom=0.12)

# ─── PANEL 1: Hard Stop Timeline ──────────────────────────────
ax1 = fig.add_subplot(gs[0])
ax1.set_facecolor('#fafafa')
for s in ['top','right']: ax1.spines[s].set_visible(False)
ax1.spines['left'].set_color('#ddd'); ax1.spines['bottom'].set_color('#ddd')

# WTI line
color_wti = '#f85149' if wti[-1] < 75 else '#3fb950'
ax1.plot(dates, wti, color=color_wti, linewidth=3, marker='o', markersize=8, markerfacecolor='#fff', markeredgewidth=2, markeredgecolor=color_wti, zorder=3)
# Hard stop zone
ax1.axhline(y=75, color='#f85149', linestyle='--', linewidth=1.5, alpha=0.5)
ax1.fill_between(range(len(dates)), 0, 75, color='#f85149', alpha=0.04)
ax1.text(5.3, 76, '$75 Hard Stop', color='#f85149', fontsize=8, fontfamily='monospace', va='bottom')

# Annotations
for i, (d, w) in enumerate(zip(dates, wti)):
    c = '#f85149' if w < 75 else '#3fb950'
    ax1.text(i, w + 2.5, f'${w:.0f}', color=c, fontsize=10, fontfamily='monospace', fontweight='bold', ha='center')
ax1.text(3, 63, 'LOCKDOWN', color='#f85149', fontsize=11, fontfamily='monospace', fontweight='bold', ha='center')
ax1.text(5.3, 63, 'ACTIVE', color='#3fb950', fontsize=11, fontfamily='monospace', fontweight='bold', ha='center')

ax1.set_ylim(50, 95)
ax1.set_xticks(range(len(dates))); ax1.set_xticklabels(dates, fontsize=8, fontfamily='monospace')
ax1.tick_params(colors='#888', labelsize=8)
ax1.set_title('WTI: Hard Stop Released', color='#000', fontsize=13, fontfamily='monospace', fontweight='bold', pad=10)
ax1.set_ylabel('WTI ($/bbl)', color='#888', fontsize=9, fontfamily='monospace')

# ─── PANEL 2: Sentiment Distribution ──────────────────────────
ax2 = fig.add_subplot(gs[1])
ax2.set_facecolor('#fafafa')
for s in ['top','right']: ax2.spines[s].set_visible(False)
ax2.spines['left'].set_color('#ddd'); ax2.spines['bottom'].set_color('#ddd')

y_pos = range(len(tickers_s))
colors_s = []
for bu, be in zip(bull_s, bear_s):
    if bu - be > 8: colors_s.append('#3fb950')
    elif be - bu > 8: colors_s.append('#f85149')
    elif bu > be: colors_s.append('#d2991d')
    else: colors_s.append('#888888')

bars = ax2.barh(y_pos, buzz_s, height=0.5, color=colors_s, alpha=0.75, zorder=2)
for i, (t, bu, be, bz) in enumerate(zip(tickers_s, bull_s, bear_s, buzz_s)):
    ax2.text(bz+1, i, f'{bu}%', va='center', fontsize=7, color='#3fb950', fontfamily='monospace')
    ax2.text(bz+1, i-0.22, f'{be}%', va='center', fontsize=7, color='#f85149', fontfamily='monospace')

ax2.set_yticks(y_pos); ax2.set_yticklabels(tickers_s, fontsize=10, fontfamily='monospace')
ax2.invert_yaxis(); ax2.set_xlim(0, 105)
ax2.tick_params(colors='#888', labelsize=8)
ax2.set_title('Reddit Buzz: Distribution Detected', color='#000', fontsize=13, fontfamily='monospace', fontweight='bold', pad=10)
ax2.set_xlabel('Buzz Score', color='#888', fontsize=9, fontfamily='monospace')

legend = [mpatches.Patch(color='#3fb950', alpha=0.75, label='Bullish'),
          mpatches.Patch(color='#f85149', alpha=0.75, label='Bearish'),
          mpatches.Patch(color='#d2991d', alpha=0.75, label='Late-Stage'),
          mpatches.Patch(color='#888888', alpha=0.75, label='Dead Even')]
ax2.legend(handles=legend, fontsize=7, loc='lower right', framealpha=0.8, edgecolor='#ddd')

# ─── PANEL 3: Framework Signal ────────────────────────────────
ax3 = fig.add_subplot(gs[2])
ax3.set_facecolor('#fafafa')
ax3.set_xlim(0, 10); ax3.set_ylim(0, 10)
ax3.set_xticks([]); ax3.set_yticks([])
for s in ax3.spines.values(): s.set_visible(False)

dy = 1.4
y = 9
signals = [
    ('GOR', '49.1', 'Compressing via oil rally', '#000'),
    ('WTI', '$81.72', 'Hard stop released', '#3fb950'),
    ('VIX', '18.77', 'Creeping up from 15.6', '#d2991d'),
    ('DXY', '100.93', 'Centripetal active', '#d2991d'),
    ('10Y', '4.57%', 'Rate pressure persists', '#d2991d'),
    ('Oil Alloc', '25%', 'Framework fully active', '#3fb950'),
]
for label, val, note, c in signals:
    ax3.text(0.5, y, label, fontsize=10, color='#888', fontfamily='monospace', va='center')
    ax3.text(3.5, y, val, fontsize=13, color='#000', fontfamily='monospace', fontweight='bold', va='center')
    ax3.text(6.5, y, note, fontsize=8, color=c, fontfamily='monospace', va='center')
    y -= dy

y -= 0.8
ax3.text(5, y, 'The GOR framework emerged', fontsize=8.5, color='#000', fontfamily='monospace', ha='center', fontweight='bold')
y -= 0.5
ax3.text(5, y, 'from defensive lockdown this week.', fontsize=8.5, color='#000', fontfamily='monospace', ha='center', fontweight='bold')
y -= 0.5
ax3.text(5, y, 'WTI broke $75. Oil back to 25%.', fontsize=8.5, color='#000', fontfamily='monospace', ha='center', fontweight='bold')
y -= 0.5
ax3.text(5, y, 'Sentiment shows distribution in tech', fontsize=8.5, color='#888', fontfamily='monospace', ha='center')
y -= 0.5
ax3.text(5, y, 'while energy quietly improves.', fontsize=8.5, color='#888', fontfamily='monospace', ha='center')

ax3.set_title('Framework Status', color='#000', fontsize=13, fontfamily='monospace', fontweight='bold', pad=10)

# ─── Title ────────────────────────────────────────────────────
fig.text(0.5, 0.96, 'DEEP-RISK-OPP  ·  GOR PULSE WEEKLY #002  ·  JULY 19, 2026', fontsize=12,
         color='#000', fontfamily='monospace', fontweight='bold', ha='center')
fig.text(0.5, 0.04, 'Data: Yahoo Finance, FRED, Adanos Reddit Sentiment  |  Research Only  |  Not Investment Advice',
         fontsize=6.5, color='#bbb', fontfamily='monospace', ha='center')

out = r'c:\Users\Admin\Documents\Justinjchen-资料备份\08.投资决策框架\看板日志\weekly_market_heatmap.png'
fig.savefig(out, dpi=120, facecolor='#ffffff', bbox_inches='tight', pad_inches=0.3)
print(f'Saved: {out}')
