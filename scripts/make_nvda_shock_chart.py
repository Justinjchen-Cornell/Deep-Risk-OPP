# -*- coding: utf-8 -*-
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE=Path(__file__).resolve().parent.parent
OUT=BASE/"看板日志"/"reports"/"special"/"linkedin_assets"
NAVY="#0B1F33"; GOLD="#C9A227"; COPPER="#B87333"; RED="#B23A2E"; GRAY="#8A8F98"; MID="#5A6572"; LINE="#E3DED2"
plt.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Segoe UI","Arial"],
    "axes.unicode_minus":False,"figure.facecolor":"white","text.color":NAVY})

dates=["Nov 5","Nov 6","Nov 9","Nov 10","Nov 11","Nov 12","Nov 13"]
close=[181.60,186.64,178.67,168.89,173.73,166.19,162.85]
vol=[306.1,180.2,462.7,429.3,339.2,747.7,365.8]

fig=plt.figure(figsize=(12,6.75))
gs=fig.add_gridspec(1,2,width_ratios=[1.5,1],wspace=0.22)
ax=fig.add_subplot(gs[0,0])
x=np.arange(len(dates))
ax.plot(x,close,color=NAVY,lw=2.4,marker="o",ms=5)
ax.scatter([5],[151.005],color=RED,s=55,zorder=5)
ax.annotate("Nov 12 open $151.01\n−13.1% vs prior close",(5,151.0),xytext=(1.2,155),textcoords="data",
            fontsize=9,color=RED,fontweight="bold",
            arrowprops=dict(arrowstyle="->",color=RED,lw=1.2))
ax.axhline(148.80,color=RED,lw=0.9,ls=":")
ax.text(0.05,149.6,"Nov 12 low $148.80",fontsize=8.3,color=RED)
ax.set_xticks(x); ax.set_xticklabels(dates,fontsize=8.6)
ax.set_ylim(144,192); ax.set_ylabel("NVDA close, $",fontsize=9.5,color=MID)
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.spines["left"].set_color(LINE); ax.spines["bottom"].set_color(LINE)
ax.grid(axis="y",color="#F0ECE2",lw=0.8); ax.set_axisbelow(True)
for xi,yi in zip(x,close):
    ax.annotate(f"{yi:.0f}",(xi,yi),textcoords="offset points",xytext=(0,9),ha="center",fontsize=8,color=MID)

bx=fig.add_subplot(gs[0,1])
labels=["NVDA","SOX","Nasdaq"]
vals=[-4.34,-0.54,-0.39]
colors=[RED,COPPER,NAVY]
y=np.arange(len(labels))[::-1]
bars=bx.barh(y,vals,color=colors,height=0.5)
for yy,v in zip(y,vals):
    bx.text(v-0.12,yy,f"{v:.1f}%",va="center",ha="right",fontsize=10,fontweight="bold",color=NAVY)
bx.axvline(0,color="#C9C2B2",lw=0.8)
bx.set_yticks(y); bx.set_yticklabels(labels,fontsize=10)
bx.set_xlim(-5.2,1.2); bx.set_xlabel("% change, Nov 12 close",fontsize=9,color=MID)
bx.set_title("Same day, different market",loc="left",fontsize=12.5,fontweight="bold",color=NAVY,pad=10)
for s in ("top","right","left"): bx.spines[s].set_visible(False)
bx.spines["bottom"].set_color(LINE); bx.grid(axis="x",color="#F0ECE2",lw=0.8); bx.set_axisbelow(True)

fig.text(0.06,0.945,"Nvidia lost its CEO. The Nasdaq fell 0.4%.",fontsize=18,fontweight="bold",color=NAVY)
fig.text(0.06,0.905,"Nov 5–13, 2026 · NVDA daily close and the Nov 12 cross-asset reaction",fontsize=10.5,color=MID)
fig.text(0.06,0.062,"HY 320bp (−10bp) · CCC 1,314bp (−16bp) · VIX 18.7 on Nov 12",fontsize=8.8,color=NAVY)
fig.text(0.06,0.025,"Sources: Nasdaq (NVDA, SOX, Nasdaq Composite), FRED (HY/CCC OAS, VIX). Key-man risk is not systemic risk — until capex changes.",fontsize=7.8,color=GRAY)
fig.subplots_adjust(left=0.07,right=0.97,top=0.86,bottom=0.15)
p=OUT/"nvda_keyman_shock.png"; fig.savefig(p,dpi=200,facecolor="white"); print(p,p.stat().st_size)
