# -*- coding: utf-8 -*-
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

BASE=Path(__file__).resolve().parent.parent
OUT=BASE/"看板日志"/"reports"/"special"/"linkedin_assets"
OUT.mkdir(parents=True,exist_ok=True)
NAVY="#0B1F33"; GOLD="#C9A227"; COPPER="#B87333"; RED="#B23A2E"; GRAY="#8A8F98"; MID="#5A6572"; LINE="#E3DED2"
plt.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Segoe UI","Arial","DejaVu Sans"],
    "axes.unicode_minus":False,"figure.facecolor":"white","axes.facecolor":"white",
    "text.color":NAVY,"axes.edgecolor":LINE})

fig, ax = plt.subplots(figsize=(12,6.75))
labels=["Dow","Nasdaq","SOX","Nikkei 225","KOSPI"]
vals=[-3.44,-5.52,-12.25,-5.96,-6.02]
colors=[COPPER,COPPER,COPPER,RED,RED]
y=np.arange(len(labels))[::-1]
bars=ax.barh(y, vals, color=colors, height=0.52)
for yy,v in zip(y,vals):
    ax.text(v-0.25, yy, f"{v:.1f}%", va="center", ha="right", fontsize=13, fontweight="bold", color=NAVY)
ax.axhline(2.5, color=LINE, lw=1)
ax.axvline(0, color="#C9C2B2", lw=0.8)
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=12.5)
for lbl,c in zip(ax.get_yticklabels(), colors): lbl.set_color(c)
ax.set_xlim(-14.2, 1.5)
ax.set_xlabel("% change, close to close", fontsize=10, color=MID)
ax.tick_params(axis="x", labelsize=9, colors=MID)
for s in ("top","right","left"): ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(LINE)
ax.grid(axis="x", color="#F0ECE2", lw=0.8); ax.set_axisbelow(True)
ax.legend(handles=[Patch(color=COPPER,label="US · Thu Nov 5"),Patch(color=RED,label="Asia · Fri Nov 6")], loc="lower right", bbox_to_anchor=(1.0,1.02), ncol=2, frameon=False, fontsize=9.5)
fig.text(0.06, 0.925, "Two sessions, one chain", fontsize=18, fontweight="bold", color=NAVY)
fig.text(0.06, 0.878, "US risk-off → Asia liquidity hit · close-to-close % change, Nov 5–6, 2026", fontsize=10.5, color=MID)
fig.text(0.06, 0.055, "The bid went to Treasuries, not to other risk: 2Y 4.58% → 4.46%, 10Y 4.90% → 4.84%.  KOSPI intraday low –8.8%; circuit breaker, program selling paused.", fontsize=9.2, color=NAVY)
fig.text(0.06, 0.018, "Sources: FRED (DJIA, NASDAQCOM, NIKKEI225), Nasdaq (SOX), KRX/Naver (KOSPI), U.S. Treasury.", fontsize=7.6, color=GRAY)
fig.subplots_adjust(left=0.13, right=0.97, top=0.83, bottom=0.14)
p=OUT/"centripetal_us_asia.png"
fig.savefig(p, dpi=200, facecolor="white")
print(p, p.stat().st_size)
