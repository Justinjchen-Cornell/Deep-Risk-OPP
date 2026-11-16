# -*- coding: utf-8 -*-
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE=Path(__file__).resolve().parent.parent
OUT=BASE/"看板日志"/"reports"/"special"/"linkedin_assets"
NAVY="#0B1F33"; GOLD="#C9A227"; COPPER="#B87333"; RED="#B23A2E"; TEAL="#1F6F78"
GRAY="#8A8F98"; MID="#5A6572"; LINE="#E3DED2"
plt.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Segoe UI","Arial"],
    "axes.unicode_minus":False,"figure.facecolor":"white","text.color":NAVY})

fig=plt.figure(figsize=(12,6.75))
gs=fig.add_gridspec(1,2,width_ratios=[1,1.15],wspace=0.28)

ax=fig.add_subplot(gs[0,0])
labels=["Nov 11\nclose","Nov 12\nopen","Nov 12\nclose"]
vals=[4.19,3.64,4.01]
colors=[NAVY,RED,TEAL]
bars=ax.bar(labels,vals,color=colors,width=0.55)
for b,v in zip(bars,vals):
    ax.text(b.get_x()+b.get_width()/2,v+0.05,f"${v:.2f}T",ha="center",fontsize=11,fontweight="bold",color=NAVY)
ax.annotate("$550B gap",xy=(1,3.64),xytext=(0.62,3.35),ha="right",fontsize=10,color=RED,fontweight="bold",
            arrowprops=dict(arrowstyle="->",color=RED,lw=1.2))
ax.annotate("$365B rebound",xy=(2,4.01),xytext=(1.35,4.35),fontsize=10,color=TEAL,fontweight="bold",
            arrowprops=dict(arrowstyle="->",color=TEAL,lw=1.2))
ax.set_ylim(3.0,4.6); ax.set_ylabel("Market cap, $T",fontsize=9.5,color=MID)
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.spines["left"].set_color(LINE); ax.spines["bottom"].set_color(LINE)
ax.grid(axis="y",color="#F0ECE2",lw=0.8); ax.set_axisbelow(True)

bx=fig.add_subplot(gs[0,1])
labels2=["Off-balance\nobligations","Shareholders'\nequity","Cash + ST\ninvestments"]
vals2=[530,157,63]
colors2=[RED,NAVY,TEAL]
y=np.arange(len(labels2))[::-1]
bars2=bx.barh(y,vals2,color=colors2,height=0.5)
for yy,v in zip(y,vals2):
    bx.text(v+8,yy,f"${v}B",va="center",fontsize=11,fontweight="bold",color=NAVY)
bx.set_yticks(y); bx.set_yticklabels(labels2,fontsize=10)
bx.set_xlim(0,620); bx.set_xlabel("$B",fontsize=9,color=MID)
for s in ("top","right","left"): bx.spines[s].set_visible(False)
bx.spines["bottom"].set_color(LINE); bx.grid(axis="x",color="#F0ECE2",lw=0.8); bx.set_axisbelow(True)

fig.text(0.06,0.945,"The 550B gap and the 530B book",fontsize=18,fontweight="bold",color=NAVY)
fig.text(0.06,0.905,"Nvidia market cap, Nov 11–12, 2026 · off-balance obligations vs FY2026 balance sheet",fontsize=10.5,color=MID)
fig.text(0.06,0.035,"Sources: Nasdaq (market cap); FY2026 financials (equity 157B, cash+ST 63B); 10-Q reporting cited in market (~530B). Treat 530B as a magnitude, not a precise liability.",fontsize=7.6,color=GRAY)
fig.subplots_adjust(left=0.07,right=0.97,top=0.86,bottom=0.13)
p=OUT/"nvda_offbalance_gap.png"; fig.savefig(p,dpi=200,facecolor="white"); print(p,p.stat().st_size)
