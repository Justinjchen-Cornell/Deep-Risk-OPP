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

labels=["IPO price","Open","Day-1\nhigh","Day-1\nclose","Now"]
vals=[83.0,111.50,115.10,97.17,89.305]
colors=[NAVY,GOLD,TEAL,COPPER,RED]
fig,ax=plt.subplots(figsize=(12,6.75))
bars=ax.bar(labels,vals,color=colors,width=0.58)
for b,v in zip(bars,vals):
    ax.text(b.get_x()+b.get_width()/2,v+1.8,f"${v:.2f}",ha="center",fontsize=12,fontweight="bold",color=NAVY)
ax.axhline(83,color=RED,lw=1.0,ls=(0,(4,3)))
ax.text(4,95.2,"−20% from the open",ha="center",fontsize=9.5,color=RED,fontweight="bold")
ax.set_ylim(70,124); ax.set_ylabel("Price per share, $",fontsize=9.5,color=MID)
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.spines["left"].set_color(LINE); ax.spines["bottom"].set_color(LINE)
ax.grid(axis="y",color="#F0ECE2",lw=0.8); ax.set_axisbelow(True)
fig.text(0.06,0.945,"The biggest IPO in history is already back near its issue price",fontsize=17,fontweight="bold",color=NAVY)
fig.text(0.06,0.905,"Anthropic (ANT), Nov 19–20, 2026 · price per share",fontsize=10.5,color=MID)
fig.text(0.06,0.035,"Sources: Nasdaq (ANT quote, Nov 20 9:42 ET), IPO terms reported by ifanr (980M shares at $83; $81.3B). Intraday price can change.",fontsize=7.6,color=GRAY)
fig.subplots_adjust(left=0.08,right=0.97,top=0.86,bottom=0.13)
p=OUT/"anthropic_ipo_break.png"; fig.savefig(p,dpi=200,facecolor="white"); print(p,p.stat().st_size)
