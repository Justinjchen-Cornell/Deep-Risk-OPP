import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

card = r"""╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║              GOR INVESTMENT DECISION CARD                         ║
║              July 19, 2026  .  Weekly Pulse                       ║
║                                                                  ║
║   ┌──────────────────────────────────────────────────────────┐   ║
║   │                                                          │   ║
║   │     GOR(WTI)     49.1                                    │   ║
║   │                                                          │   ║
║   │     ████████████████████████████████████████░░░░░░░░░░   │   ║
║   │                                                          │   ║
║   │     EXTREME OPPORTUNITY  (>= 45 threshold)               │   ║
║   │                                                          │   ║
║   │     GOR(Brent)    46.3                                   │   ║
║   │                                                          │   ║
║   │     vs. Historical Mean (15-25)  ->  2.0x overvalued     │   ║
║   │     vs. #001 (57.7, Jul 12)      ->  -8.6 compression    │   ║
║   │     vs. 2026 Peak (78.0, Feb)    ->  37% retracement     │   ║
║   │                                                          │   ║
║   └──────────────────────────────────────────────────────────┘   ║
║                                                                  ║
║   ┌─────────────────────┐  ┌─────────────────────────────────┐  ║
║   │  MARKET SNAPSHOT    │  │  FRAMEWORK SIGNAL               │  ║
║   ├─────────────────────┤  ├─────────────────────────────────┤  ║
║   │                     │  │                                 │  ║
║   │  Gold     $4,011    │  │  GOR >= 45                      │  ║
║   │  WTI      $81.72    │  │    -> Oil undervalued           │  ║
║   │  Brent    $86.73    │  │    -> Mean reversion ACTIVE     │  ║
║   │  DXY      100.93    │  │    -> Oil at framework weight   │  ║
║   │  10Y      4.57%     │  │                                 │  ║
║   │  VIX      18.77     │  │  WTI > $75                      │  ║
║   │  Copper   $6.29/lb  │  │    -> HARD STOP RELEASED        │  ║
║   │                     │  │                                 │  ║
║   └─────────────────────┘  └─────────────────────────────────┘  ║
║                                                                  ║
║   ┌──────────────────────────────────────────────────────────┐   ║
║   │  RISK CORRECTION LAYER                                    │   ║
║   │                                                          │   ║
║   │  Base (GOR>=45) ......... 70%                             │   ║
║   │  DXY > 99 ............... -10%                            │   ║
║   │  10Y > 4.3% ............. -10%                            │   ║
║   │  ─────────────────────────────                            │   ║
║   │  Framework Position ...... 50%                             │   ║
║   │                                                          │   ║
║   │  Oil 25%  |  Gold 20%  |  Cash 48%  |  A-Shares 7%       │   ║
║   │  Target:  WTI $95 - $105                                  │   ║
║   └──────────────────────────────────────────────────────────┘   ║
║                                                                  ║
║   ┌──────────────────────────────────────────────────────────┐   ║
║   │  THIS WEEK'S TRIGGERS                                    │   ║
║   │                                                          │   ║
║   │  (1)  VIX 18.77 -> if >20, speed flips to ELEVATED       │   ║
║   │  (2)  WTI approaching $85 -> GOR compressing further     │   ║
║   │  (3)  FOMC minutes -> hawkish surprise, DXY > 101        │   ║
║   │  (4)  SPY/QQQ distribution signal confirm or fade        │   ║
║   └──────────────────────────────────────────────────────────┘   ║
║                                                                  ║
║              RESEARCH FRAMEWORK ONLY                             ║
║              NOT INVESTMENT ADVICE                                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝"""

lines = card.split('\n')
n_lines = len(lines)
fontsize = 9

# Use tight bbox to compute pixel dimensions from text
import io
from matplotlib.font_manager import FontProperties
fp = FontProperties(family='monospace', size=fontsize)

# Render to get actual bounding box
fig, ax = plt.subplots(figsize=(8, n_lines*0.18), dpi=150)
fig.patch.set_facecolor('#ffffff')
ax.set_facecolor('#ffffff')
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)

for i, line in enumerate(lines):
    y = 1 - (i + 0.5) / n_lines
    if not line.strip(): continue

    if 'GOR INVESTMENT DECISION CARD' in line:
        c, w = '#000000', 'bold'
    elif 'July 19' in line:
        c, w = '#555555', 'normal'
    elif 'EXTREME OPPORTUNITY' in line:
        c, w = '#000000', 'bold'
    elif 'HARD STOP RELEASED' in line:
        c, w = '#000000', 'bold'
    elif 'MARKET SNAPSHOT' in line.split('│')[0] if '│' in line else False:
        c, w = '#333333', 'bold'
    elif 'FRAMEWORK SIGNAL' in line:
        c, w = '#333333', 'bold'
    elif 'RISK CORRECTION' in line or "THIS WEEK'S TRIGGERS" in line:
        c, w = '#333333', 'bold'
    elif 'RESEARCH FRAMEWORK' in line:
        c, w = '#aaaaaa', 'normal'
    elif '49.1' in line or '46.3' in line:
        c, w = '#000000', 'bold'
    else:
        c, w = '#444444', 'normal'

    ax.text(0.04, y, line, fontsize=fontsize, color=c, fontfamily='monospace',
            fontweight=w, ha='left', va='center')

out = r'c:\Users\Admin\Documents\Justinjchen-资料备份\08.投资决策框架\看板日志\decision_card_ascii.png'
fig.savefig(out, dpi=150, facecolor='#ffffff', bbox_inches='tight', pad_inches=0.15)
print(f'Saved: {out}')

