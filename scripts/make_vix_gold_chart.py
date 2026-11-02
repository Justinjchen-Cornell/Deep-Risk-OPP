# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path("看板日志/reports/special/linkedin_assets")
OUT.mkdir(parents=True, exist_ok=True)
NAVY="#0B1F33"; GOLD="#C9A227"; COPPER="#B87333"; TEAL="#1F6F78"; RED="#B23A2E"; GRAY="#8A8F98"; GRID="#E8E3D8"
plt.rcParams.update({"font.family":"Segoe UI","axes.unicode_minus":False,"figure.facecolor":"white","axes.facecolor":"white",
    "axes.edgecolor":"#D9D4C7","axes.labelcolor":NAVY,"xtick.color":"#5A6572","ytick.color":"#5A6572","text.color":NAVY,
    "axes.grid":True,"grid.color":GRID,"grid.linewidth":0.8,"axes.spines.top":False,"axes.spines.right":False,"font.size":10})

def style(ax, axis="y"):
    ax.grid(axis=axis, color=GRID, lw=.8); ax.set_axisbelow(True)
    for s in ("top","right"): ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=9)

# VIX data
df = pd.read_csv("看板日志/cache/vix_history.csv") if Path("看板日志/cache/vix_history.csv").exists() else None
# fallback hardcoded from CBOE
rows = [
("10/15",16.46,18.01),("10/16",19.99,22.31),("10/19",18.44,18.93),("10/20",17.31,19.13),
("10/21",16.68,17.58),("10/22",19.03,20.31),("10/23",19.45,20.66),("10/26",18.39,19.84),
("10/27",17.52,18.55),("10/28",16.91,17.77),("10/29",17.20,17.36),("10/30",19.42,23.93)]
dates=[r[0] for r in rows]; closes=[r[1] for r in rows]; highs=[r[2] for r in rows]

fig, (ax1, ax2) = plt.subplots(2,1,figsize=(10,9),gridspec_kw={"height_ratios":[1.15,1]})
x=np.arange(len(dates))
ax1.plot(x, closes, color=NAVY, lw=2.2, marker="o", ms=4)
ax1.plot(x[-1], highs[-1], color=RED, marker="o", ms=8, zorder=5)
ax1.vlines(x[-1], closes[-1], highs[-1], color=RED, lw=2)
ax1.axhline(22.5, color=GRAY, lw=1, ls="--")
ax1.text(0, 23.0, "22.5 panic gate", fontsize=8.5, color=GRAY)
ax1.annotate("Intraday high 23.93", (x[-1], highs[-1]), xytext=(-6,10), textcoords="offset points", ha="right", fontsize=9, color=RED, fontweight="bold")
ax1.annotate("Close 19.42", (x[-1], closes[-1]), xytext=(-6,-16), textcoords="offset points", ha="right", fontsize=9, color=NAVY, fontweight="bold")
ax1.set_xticks(x); ax1.set_xticklabels(dates, fontsize=8.5)
ax1.set_ylim(14,25); ax1.set_ylabel("VIX", fontsize=9.5)
ax1.set_title("INTC -28.6%, VIX 24, Gold -3.6%: one market, three warnings", loc="left", fontsize=15, fontweight="bold", color=NAVY, pad=10)
style(ax1)

# Friday moves
labels=["INTC","SMH","NVDA","Gold","QQQ","SPY","WTI","DXY"]
vals=[-28.6,-6.98,-4.22,-3.63,-3.47,-1.77,0.93,-0.06]
colors=[RED if v<0 else TEAL for v in vals]
y=np.arange(len(labels))[::-1]
bars=ax2.barh(y, vals, color=colors, height=.55)
for yy,v in zip(y,vals):
    ax2.text(v + (0.8 if v>=0 else -0.8), yy, f"{v:+.2f}%", va="center", ha="left" if v>=0 else "right", fontsize=9, color=NAVY, fontweight="bold")
ax2.axvline(0,color=GRAY,lw=.8)
ax2.set_yticks(y); ax2.set_yticklabels(labels, fontsize=9.5)
ax2.set_xlim(-34,5); ax2.set_xlabel("Friday move, %", fontsize=9)
ax2.set_title("AI/tech sold off; gold was sold for liquidity", loc="left", fontsize=12, fontweight="bold", color=NAVY, pad=8)
style(ax2, "x")
fig.text(0.01,-0.02,"Sources: CBOE VIX history (10/30/2026); CNBC quotes (10/30 close). Gold = front-month futures; DXY = dollar index. Not investment advice.",fontsize=7.5,color=GRAY)
fig.tight_layout()
fig.savefig(OUT/"vix_gold_flush.png",dpi=200,bbox_inches="tight",facecolor="white")
print("saved", OUT/"vix_gold_flush.png")
